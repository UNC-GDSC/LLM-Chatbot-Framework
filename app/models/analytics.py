"""Analytics and usage tracking models."""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class MessageFeedback(Base):
    """Feedback on assistant messages."""

    __tablename__ = "message_feedback"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_type = Column(String, nullable=True)  # helpful, unhelpful, inappropriate
    comment = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UsageStats(Base):
    """Usage statistics for tracking API usage."""

    __tablename__ = "usage_stats"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost = Column(Float, nullable=True)  # Estimated cost
    latency_ms = Column(Integer, nullable=True)  # Response time
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Uploaded documents for RAG."""

    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False)
    collection_name = Column(String, nullable=False)  # Vector DB collection
    chunk_count = Column(Integer, default=0)
    metadata = Column(JSON, nullable=True)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ConversationTemplate(Base):
    """Reusable conversation templates."""

    __tablename__ = "conversation_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # Null for system templates
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    system_prompt = Column(String, nullable=True)
    model_config = Column(JSON, nullable=True)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SharedConversation(Base):
    """Shared conversation links."""

    __tablename__ = "shared_conversations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    share_token = Column(String, unique=True, nullable=False, index=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
