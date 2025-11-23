"""Document upload and processing service."""

from typing import Optional, List
from pathlib import Path
import os
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from fastapi import UploadFile
import aiofiles

from app.models.analytics import Document
from app.services.rag.rag_service import RAGService
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Service for managing document uploads and processing."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize document service."""
        self.db = db
        self.rag_service = RAGService()
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def upload_document(
        self,
        user_id: str,
        file: UploadFile,
        process_now: bool = True,
    ) -> Document:
        """Upload and optionally process a document."""
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise ValueError(f"File type {file_ext} not allowed")

        # Check file size
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE:
            raise ValueError(f"File size exceeds {settings.MAX_UPLOAD_SIZE} bytes")

        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = self.upload_dir / user_id
        file_path.mkdir(parents=True, exist_ok=True)
        full_path = file_path / filename

        # Save file
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(content)

        # Create document record
        doc = Document(
            user_id=user_id,
            filename=filename,
            original_filename=file.filename,
            file_type=file_ext,
            file_size=len(content),
            file_path=str(full_path),
            collection_name=f"user_{user_id}",
            processed=False,
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # Process document if requested
        if process_now and settings.ENABLE_RAG:
            try:
                await self.process_document(doc.id)
            except Exception as e:
                logger.error(f"Error processing document: {e}")

        logger.info(f"Uploaded document: {doc.original_filename}")
        return doc

    async def process_document(self, document_id: str) -> Document:
        """Process a document for RAG."""
        # Get document
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise ValueError("Document not found")

        # Load and chunk document
        chunks = await self.rag_service.load_document(doc.file_path)

        # Add to vector database
        metadata = {
            "document_id": doc.id,
            "user_id": doc.user_id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
        }

        await self.rag_service.add_documents(
            chunks,
            collection_name=doc.collection_name,
            metadata=metadata,
        )

        # Update document
        doc.chunk_count = len(chunks)
        doc.processed = True
        doc.metadata = metadata
        await self.db.commit()

        logger.info(f"Processed document {doc.original_filename}: {len(chunks)} chunks")
        return doc

    async def get_user_documents(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Document]:
        """Get user's documents."""
        result = await self.db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_document(self, document_id: str, user_id: str) -> Optional[Document]:
        """Get a specific document."""
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document."""
        doc = await self.get_document(document_id, user_id)
        if not doc:
            return False

        # Delete file
        try:
            if os.path.exists(doc.file_path):
                os.remove(doc.file_path)
        except Exception as e:
            logger.error(f"Error deleting file: {e}")

        # Delete from database
        await self.db.delete(doc)
        await self.db.commit()

        logger.info(f"Deleted document: {doc.original_filename}")
        return True

    async def search_in_documents(
        self,
        user_id: str,
        query: str,
        k: int = 4,
    ) -> List[dict]:
        """Search in user's documents using RAG."""
        collection_name = f"user_{user_id}"

        results = await self.rag_service.search_with_score(
            query,
            collection_name=collection_name,
            k=k,
        )

        # Format results
        formatted = []
        for doc, score in results:
            formatted.append({
                "content": doc.page_content,
                "score": float(score),
                "metadata": doc.metadata,
            })

        return formatted
