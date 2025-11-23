"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1 import auth, chat

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(chat.router, prefix="/chat", tags=["Chat"])
