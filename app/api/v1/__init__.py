"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1 import auth, chat, documents, analytics, exports, sharing

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
router.include_router(documents.router, prefix="/documents", tags=["Documents & RAG"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Feedback"])
router.include_router(exports.router, prefix="/export", tags=["Export"])
router.include_router(sharing.router, prefix="/sharing", tags=["Sharing"])
