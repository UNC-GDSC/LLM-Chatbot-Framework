"""Document upload and management endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.config import settings
from app.services.document_service import DocumentService
from app.schemas.documents import DocumentResponse, DocumentSearchRequest
from pydantic import BaseModel

router = APIRouter()


class DocumentSearchResponse(BaseModel):
    """Schema for document search results."""
    results: List[dict]


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    process_now: bool = Query(default=True),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Upload a document for RAG processing."""
    if not settings.ENABLE_FILE_UPLOAD:
        raise HTTPException(status_code=403, detail="File upload disabled")

    doc_service = DocumentService(db)

    try:
        document = await doc_service.upload_document(user_id, file, process_now)
        return DocumentResponse.from_orm(document)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=List[DocumentResponse])
async def get_documents(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> List[DocumentResponse]:
    """Get user's uploaded documents."""
    doc_service = DocumentService(db)
    documents = await doc_service.get_user_documents(user_id, limit, offset)
    return [DocumentResponse.from_orm(doc) for doc in documents]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Get a specific document."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document(document_id, user_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse.from_orm(document)


@router.post("/{document_id}/process", response_model=DocumentResponse)
async def process_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    """Process a document for RAG (if not already processed)."""
    doc_service = DocumentService(db)

    try:
        document = await doc_service.process_document(document_id)
        return DocumentResponse.from_orm(document)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document."""
    doc_service = DocumentService(db)
    deleted = await doc_service.delete_document(document_id, user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")


@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> DocumentSearchResponse:
    """Search in uploaded documents using RAG."""
    if not settings.ENABLE_RAG:
        raise HTTPException(status_code=403, detail="RAG disabled")

    doc_service = DocumentService(db)

    try:
        results = await doc_service.search_in_documents(
            user_id, request.query, request.k
        )
        return DocumentSearchResponse(results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
