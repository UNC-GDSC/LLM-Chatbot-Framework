"""Email notification service."""

from typing import Optional, List
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Service for sending email notifications."""

    def __init__(self) -> None:
        """Initialize email service."""
        self.enabled = all([
            settings.SMTP_HOST,
            settings.SMTP_USER,
            settings.SMTP_PASSWORD,
            settings.SMTP_FROM_EMAIL,
        ])

        if not self.enabled:
            logger.warning("Email service not configured")

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """Send an email."""
        if not self.enabled:
            logger.warning("Email service not configured, skipping email")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.SMTP_FROM_EMAIL
            message["To"] = to_email

            # Add text and HTML parts
            if body_text:
                part1 = MIMEText(body_text, "plain")
                message.attach(part1)

            part2 = MIMEText(body_html, "html")
            message.attach(part2)

            # Send email
            async with aiosmtplib.SMTP(
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                start_tls=True,
            ) as smtp:
                await smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                await smtp.send_message(message)

            logger.info(f"Email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    async def send_conversation_shared(
        self,
        to_email: str,
        share_url: str,
        conversation_title: str,
        shared_by: str,
    ) -> bool:
        """Send notification when conversation is shared."""
        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>📢 Conversation Shared With You</h2>
            <p><strong>{{ shared_by }}</strong> has shared a conversation with you:</p>
            <p><strong>Title:</strong> {{ conversation_title }}</p>
            <p><a href="{{ share_url }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Conversation</a></p>
            <p style="color: #666; font-size: 12px;">This link may expire. View it soon!</p>
        </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(
            shared_by=shared_by,
            conversation_title=conversation_title,
            share_url=share_url,
        )

        return await self.send_email(
            to_email,
            f"Conversation shared: {conversation_title}",
            body_html,
        )

    async def send_welcome_email(
        self,
        to_email: str,
        username: str,
    ) -> bool:
        """Send welcome email to new users."""
        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>🎉 Welcome to LLM Chatbot Framework!</h2>
            <p>Hi <strong>{{ username }}</strong>,</p>
            <p>Thank you for joining! You now have access to our powerful AI chatbot platform.</p>
            <h3>What you can do:</h3>
            <ul>
                <li>💬 Chat with multiple AI models (OpenAI, Claude, Ollama)</li>
                <li>📄 Upload documents for AI-powered analysis</li>
                <li>📊 Track your usage and costs</li>
                <li>🔗 Share conversations with others</li>
                <li>📤 Export conversations in multiple formats</li>
            </ul>
            <p>Get started at: <a href="http://localhost:8000/docs">API Documentation</a></p>
            <p>Happy chatting!</p>
        </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(username=username)

        return await self.send_email(
            to_email,
            "Welcome to LLM Chatbot Framework!",
            body_html,
        )

    async def send_usage_report(
        self,
        to_email: str,
        username: str,
        stats: dict,
    ) -> bool:
        """Send weekly usage report."""
        html_template = """
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>📊 Your Weekly Usage Report</h2>
            <p>Hi <strong>{{ username }}</strong>,</p>
            <p>Here's your usage summary for the past week:</p>
            <table style="border-collapse: collapse; width: 100%;">
                <tr style="background-color: #f2f2f2;">
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Metric</strong></td>
                    <td style="border: 1px solid #ddd; padding: 8px;"><strong>Value</strong></td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">Total Requests</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ stats.total_requests }}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">Total Tokens</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">{{ stats.total_tokens }}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #ddd; padding: 8px;">Total Cost</td>
                    <td style="border: 1px solid #ddd; padding: 8px;">${{ stats.total_cost }}</td>
                </tr>
            </table>
            <p>Keep building amazing things!</p>
        </body>
        </html>
        """

        template = Template(html_template)
        body_html = template.render(username=username, stats=stats)

        return await self.send_email(
            to_email,
            "Your Weekly Usage Report",
            body_html,
        )
