"""RAG (Retrieval Augmented Generation) service."""

from typing import List, Optional, Dict, Any
from pathlib import Path
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma, FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredMarkdownLoader,
)
from langchain.schema import Document

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RAGService:
    """Service for RAG operations with vector database."""

    def __init__(self) -> None:
        """Initialize RAG service."""
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def _get_embeddings(self) -> OpenAIEmbeddings:
        """Get embeddings model."""
        if not self.embeddings:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key required for RAG")
            self.embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        return self.embeddings

    def _get_vector_store(self, collection_name: str = "default") -> Any:
        """Get or create vector store."""
        embeddings = self._get_embeddings()

        if settings.VECTOR_DB_TYPE == "chromadb":
            return Chroma(
                collection_name=collection_name,
                embedding_function=embeddings,
                persist_directory=str(Path(settings.VECTOR_DB_PATH) / collection_name),
            )
        elif settings.VECTOR_DB_TYPE == "faiss":
            faiss_path = Path(settings.VECTOR_DB_PATH) / collection_name / "index.faiss"
            if faiss_path.exists():
                return FAISS.load_local(
                    str(faiss_path.parent),
                    embeddings,
                    allow_dangerous_deserialization=True,
                )
            else:
                # Create empty FAISS index
                return FAISS.from_texts([""], embeddings)
        else:
            raise ValueError(f"Unsupported vector DB type: {settings.VECTOR_DB_TYPE}")

    async def load_document(self, file_path: str) -> List[Document]:
        """Load and split document into chunks."""
        ext = Path(file_path).suffix.lower()

        loaders = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".md": UnstructuredMarkdownLoader,
            ".docx": UnstructuredWordDocumentLoader,
        }

        loader_class = loaders.get(ext)
        if not loader_class:
            raise ValueError(f"Unsupported file type: {ext}")

        loader = loader_class(file_path)
        documents = loader.load()

        # Split documents
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Loaded {len(chunks)} chunks from {file_path}")

        return chunks

    async def add_documents(
        self,
        documents: List[Document],
        collection_name: str = "default",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Add documents to vector store."""
        # Add metadata to all documents
        if metadata:
            for doc in documents:
                doc.metadata.update(metadata)

        vector_store = self._get_vector_store(collection_name)

        # Add documents
        ids = vector_store.add_documents(documents)

        # Persist if using FAISS
        if settings.VECTOR_DB_TYPE == "faiss":
            save_path = Path(settings.VECTOR_DB_PATH) / collection_name
            save_path.mkdir(parents=True, exist_ok=True)
            vector_store.save_local(str(save_path))

        logger.info(f"Added {len(ids)} documents to {collection_name}")
        return ids

    async def search(
        self,
        query: str,
        collection_name: str = "default",
        k: int = 4,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Search for similar documents."""
        vector_store = self._get_vector_store(collection_name)

        # Search with optional filtering
        if filter_dict:
            results = vector_store.similarity_search(
                query, k=k, filter=filter_dict
            )
        else:
            results = vector_store.similarity_search(query, k=k)

        logger.info(f"Found {len(results)} results for query in {collection_name}")
        return results

    async def search_with_score(
        self,
        query: str,
        collection_name: str = "default",
        k: int = 4,
    ) -> List[tuple[Document, float]]:
        """Search with similarity scores."""
        vector_store = self._get_vector_store(collection_name)
        results = vector_store.similarity_search_with_score(query, k=k)
        return results

    async def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection."""
        try:
            collection_path = Path(settings.VECTOR_DB_PATH) / collection_name
            if collection_path.exists():
                import shutil
                shutil.rmtree(collection_path)
                logger.info(f"Deleted collection: {collection_name}")
                return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
        return False

    async def get_context_for_query(
        self,
        query: str,
        collection_name: str = "default",
        k: int = 4,
    ) -> str:
        """Get context for a query from vector store."""
        results = await self.search(query, collection_name, k)

        if not results:
            return ""

        # Combine results into context
        context_parts = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(f"[Source {i}: {source}]\n{doc.page_content}\n")

        return "\n".join(context_parts)
