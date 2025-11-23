"""Document-related schemas."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Response schema for document."""

    id: str
    user_id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    collection_name: str
    chunk_count: int
    processed: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentSearchRequest(BaseModel):
    """Request schema for document search."""

    query: str = Field(..., min_length=1, max_length=1000)
    k: int = Field(default=4, ge=1, le=20, description="Number of results to return")
