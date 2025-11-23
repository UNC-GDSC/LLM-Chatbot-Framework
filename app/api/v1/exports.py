"""Conversation export endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.services.chat_service import ChatService
from app.services.export_service import ExportService

router = APIRouter()


@router.get("/{conversation_id}/json")
async def export_json(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export conversation as JSON."""
    if not settings.ENABLE_EXPORTS:
        raise HTTPException(status_code=403, detail="Exports disabled")

    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    export_service = ExportService(db)
    json_content = await export_service.export_to_json(conversation)

    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.json"
        },
    )


@router.get("/{conversation_id}/markdown")
async def export_markdown(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export conversation as Markdown."""
    if not settings.ENABLE_EXPORTS:
        raise HTTPException(status_code=403, detail="Exports disabled")

    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    export_service = ExportService(db)
    md_content = await export_service.export_to_markdown(conversation)

    return Response(
        content=md_content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.md"
        },
    )


@router.get("/{conversation_id}/pdf")
async def export_pdf(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export conversation as PDF."""
    if not settings.ENABLE_EXPORTS:
        raise HTTPException(status_code=403, detail="Exports disabled")

    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    export_service = ExportService(db)

    try:
        pdf_content = await export_service.export_to_pdf(conversation)

        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.pdf"
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/{conversation_id}/text")
async def export_text(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Export conversation as plain text."""
    if not settings.ENABLE_EXPORTS:
        raise HTTPException(status_code=403, detail="Exports disabled")

    chat_service = ChatService(db)
    conversation = await chat_service.get_conversation(conversation_id, user_id)

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    export_service = ExportService(db)
    text_content = await export_service.export_to_text(conversation)

    return Response(
        content=text_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f"attachment; filename=conversation_{conversation_id}.txt"
        },
    )
