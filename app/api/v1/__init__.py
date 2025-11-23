"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1 import (
    auth,
    chat,
    documents,
    analytics,
    exports,
    sharing,
    agents,
    templates,
    admin,
    search,
    webhooks,
    sse,
)

router = APIRouter()

# Core features
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Document & RAG
router.include_router(documents.router, prefix="/documents", tags=["Documents & RAG"])

# Analytics & Feedback
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics & Feedback"])

# Export & Sharing
router.include_router(exports.router, prefix="/export", tags=["Export"])
router.include_router(sharing.router, prefix="/sharing", tags=["Sharing"])

# Advanced features (v3.0)
router.include_router(agents.router, prefix="/agents", tags=["AI Agents & Tools"])
router.include_router(templates.router, prefix="/templates", tags=["Templates"])
router.include_router(admin.router, prefix="/admin", tags=["Admin Dashboard"])
router.include_router(search.router, prefix="/search", tags=["Advanced Search"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
router.include_router(sse.router, prefix="/sse", tags=["SSE Streaming"])
