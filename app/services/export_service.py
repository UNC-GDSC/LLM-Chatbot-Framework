"""Conversation export service."""

from typing import Optional
from datetime import datetime
import json
from pathlib import Path
import tempfile

from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT

from app.models.conversation import Conversation
from app.core.logging import get_logger

logger = get_logger(__name__)


class ExportService:
    """Service for exporting conversations in various formats."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize export service."""
        self.db = db

    async def export_to_json(self, conversation: Conversation) -> str:
        """Export conversation to JSON format."""
        data = {
            "conversation_id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in conversation.messages
            ],
        }

        return json.dumps(data, indent=2)

    async def export_to_markdown(self, conversation: Conversation) -> str:
        """Export conversation to Markdown format."""
        lines = [
            f"# {conversation.title}",
            "",
            f"**Created:** {conversation.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Updated:** {conversation.updated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            "",
        ]

        for msg in conversation.messages:
            role = "**You**" if msg.role == "user" else "**Assistant**"
            timestamp = msg.created_at.strftime("%H:%M")

            lines.append(f"### {role} - {timestamp}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    async def export_to_pdf(self, conversation: Conversation) -> bytes:
        """Export conversation to PDF format."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            doc = SimpleDocTemplate(tmp.name, pagesize=letter)
            story = []

            # Styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor='#333333',
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=14,
                textColor='#666666',
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=11,
                alignment=TA_LEFT,
            )

            # Title
            story.append(Paragraph(conversation.title, title_style))
            story.append(Spacer(1, 0.2 * inch))

            # Metadata
            meta_text = f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')} | " \
                       f"Updated: {conversation.updated_at.strftime('%Y-%m-%d %H:%M')}"
            story.append(Paragraph(meta_text, normal_style))
            story.append(Spacer(1, 0.3 * inch))

            # Messages
            for msg in conversation.messages:
                role_text = "You" if msg.role == "user" else "Assistant"
                timestamp = msg.created_at.strftime("%H:%M")

                # Message header
                header_text = f"<b>{role_text}</b> - {timestamp}"
                story.append(Paragraph(header_text, heading_style))
                story.append(Spacer(1, 0.1 * inch))

                # Message content
                content = msg.content.replace('\n', '<br/>')
                story.append(Paragraph(content, normal_style))
                story.append(Spacer(1, 0.3 * inch))

            # Build PDF
            doc.build(story)

            # Read file content
            with open(tmp.name, 'rb') as f:
                pdf_content = f.read()

            # Clean up
            Path(tmp.name).unlink()

            return pdf_content

    async def export_to_text(self, conversation: Conversation) -> str:
        """Export conversation to plain text format."""
        lines = [
            f"{conversation.title}",
            f"{'=' * len(conversation.title)}",
            "",
            f"Created: {conversation.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"Updated: {conversation.updated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
            "-" * 70,
            "",
        ]

        for msg in conversation.messages:
            role = "You" if msg.role == "user" else "Assistant"
            timestamp = msg.created_at.strftime("%H:%M")

            lines.append(f"{role} [{timestamp}]:")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("-" * 70)
            lines.append("")

        return "\n".join(lines)
