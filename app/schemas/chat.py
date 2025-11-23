"""Chat-related schemas."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """LLM model configuration."""

    provider: str = Field(default="openai", description="LLM provider (openai, anthropic, ollama)")
    model: str = Field(default="gpt-4", description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, ge=1, le=8000)
    stream: bool = Field(default=False, description="Enable streaming responses")


class ChatRequest(BaseModel):
    """Request schema for chat messages."""

    message: str = Field(..., min_length=1, max_length=10000)
    conversation_id: Optional[str] = None
    model_config: Optional[ModelConfig] = None


class MessageResponse(BaseModel):
    """Response schema for a single message."""

    id: str
    role: str
    content: str
    tokens: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """Response schema for chat completion."""

    conversation_id: str
    message: MessageResponse
    model_config: ModelConfig


class ConversationResponse(BaseModel):
    """Response schema for conversation."""

    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""

    title: Optional[str] = "New Conversation"
    model_config: Optional[ModelConfig] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response schema."""

    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
