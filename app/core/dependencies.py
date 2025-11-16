from fastapi import Depends
from sqlalchemy.orm import Session
from qdrant_client import QdrantClient
from groq import Groq
import redis
from typing import Generator
import logging

from app.core.config import get_settings
from app.database.connection import get_db
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import QdrantVectorStore
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from app.services.memory_service import MemoryService
from app.services.booking_service import BookingService
from app.core.exceptions import DocumentNotFoundException, SessionNotFoundException

logger = logging.getLogger(__name__)

# Global instances (singletons)
_qdrant_client = None
_embedding_service = None
_vector_store = None
_groq_client = None
_redis_client = None


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client instance."""
    global _qdrant_client
    
    if _qdrant_client is None:
        try:
            settings = get_settings()
            
            if settings.qdrant_api_key:
                _qdrant_client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key
                )
            else:
                _qdrant_client = QdrantClient(url=settings.qdrant_url)
            
            logger.info(f"Qdrant client connected to {settings.qdrant_url}")
        except Exception as e:
            logger.error(f"Failed to create Qdrant client: {str(e)}")
            raise
    
    return _qdrant_client


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance."""
    global _embedding_service
    
    if _embedding_service is None:
        try:
            settings = get_settings()
            _embedding_service = EmbeddingService(settings.embedding_model)
            logger.info("Embedding service initialized")
        except Exception as e:
            logger.error(f"Failed to create embedding service: {str(e)}")
            raise
    
    return _embedding_service


def get_vector_store(
    qdrant_client: QdrantClient = Depends(get_qdrant_client),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> QdrantVectorStore:
    """Get or create vector store instance."""
    global _vector_store
    
    if _vector_store is None:
        try:
            settings = get_settings()
            embedding_dim = embedding_service.get_embedding_dimension()
            
            _vector_store = QdrantVectorStore(
                qdrant_client=qdrant_client,
                collection_name=settings.qdrant_collection,
                vector_size=embedding_dim
            )
            logger.info("Vector store initialized")
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            raise
    
    return _vector_store


def get_groq_client() -> Groq:
    """Get or create Groq client instance."""
    global _groq_client
    
    if _groq_client is None:
        try:
            settings = get_settings()
            _groq_client = Groq(api_key=settings.groq_api_key)
            logger.info("Groq client initialized")
        except Exception as e:
            logger.error(f"Failed to create Groq client: {str(e)}")
            raise
    
    return _groq_client

def get_redis_client() -> redis.Redis:
    """Get or create Redis client instance."""
    global _redis_client
    
    if _redis_client is None:
        try:
            settings = get_settings()
            _redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=False,
                socket_connect_timeout=5
            )
            _redis_client.ping()
            logger.info(f"Redis client connected to {settings.redis_url}")
        except Exception as e:
            logger.error(f"Failed to create Redis client: {str(e)}")
            raise
    
    return _redis_client

def get_document_processor() -> DocumentProcessor:
    """Get document processor instance."""
    try:
        settings = get_settings()
        return DocumentProcessor(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )
    except Exception as e:
        logger.error(f"Failed to create document processor: {str(e)}")
        raise


def get_rag_service(
    vector_store: QdrantVectorStore = Depends(get_vector_store),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    groq_client: Groq = Depends(get_groq_client)
) -> RAGService:
    """Get RAG service instance."""
    try:
        settings = get_settings()
        return RAGService(
            vector_store=vector_store,
            embedding_service=embedding_service,
            groq_client=groq_client,
            groq_model=settings.groq_model
        )
    except Exception as e:
        logger.error(f"Failed to create RAG service: {str(e)}")
        raise


def get_memory_service(redis_client: redis.Redis = Depends(get_redis_client)) -> MemoryService:
    """Get memory service instance."""
    try:
        return MemoryService(redis_client=redis_client)
    except Exception as e:
        logger.error(f"Failed to create memory service: {str(e)}")
        raise


def get_booking_service(
    groq_client: Groq = Depends(get_groq_client),
    db: Session = Depends(get_db)
) -> BookingService:
    """Get booking service instance."""
    try:
        settings = get_settings()
        return BookingService(
            groq_client=groq_client,
            db=db,
            groq_model=settings.groq_model
        )
    except Exception as e:
        logger.error(f"Failed to create booking service: {str(e)}")
        raise


def verify_document_exists(document_id: str, db: Session = Depends(get_db)) -> str:
    """
    Verify that a document exists.
    
    Args:
        document_id: Document ID to verify
        db: Database session
    
    Returns:
        document_id if exists
    
    Raises:
        DocumentNotFoundException if not found
    """
    from app.database import crud
    
    document = crud.get_document_by_id(db, document_id)
    if not document:
        raise DocumentNotFoundException(document_id)
    
    return document_id


def verify_session_exists(session_id: str, db: Session = Depends(get_db)) -> str:
    """
    Verify that a session exists.
    
    Args:
        session_id: Session ID to verify
        db: Database session
    
    Returns:
        session_id if exists
    
    Raises:
        SessionNotFoundException if not found
    """
    from app.database import crud
    
    exists = crud.session_exists(db, session_id)
    if not exists:
        raise SessionNotFoundException(session_id)
    
    return session_id