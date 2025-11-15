from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import Any, Dict


class BaseRAGException(Exception):
    """Base exception class for RAG application."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundException(BaseRAGException):
    """Raised when a document is not found."""
    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document with ID '{document_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InvalidFileTypeException(BaseRAGException):
    """Raised when an invalid file type is uploaded."""
    def __init__(self, file_type: str, allowed_types: list):
        super().__init__(
            message=f"File type '{file_type}' not allowed. Allowed types: {', '.join(allowed_types)}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class FileTooLargeException(BaseRAGException):
    """Raised when uploaded file exceeds size limit."""
    def __init__(self, file_size: int, max_size: int):
        super().__init__(
            message=f"File size {file_size} bytes exceeds maximum allowed size of {max_size} bytes",
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )


class ChunkingFailedException(BaseRAGException):
    """Raised when document chunking fails."""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to chunk document: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class EmbeddingGenerationException(BaseRAGException):
    """Raised when embedding generation fails."""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to generate embeddings: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class VectorStoreException(BaseRAGException):
    """Raised when vector store operations fail."""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Vector store operation '{operation}' failed: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class LLMException(BaseRAGException):
    """Raised when LLM API calls fail."""
    def __init__(self, reason: str):
        super().__init__(
            message=f"LLM request failed: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class BookingValidationException(BaseRAGException):
    """Raised when booking validation fails."""
    def __init__(self, errors: list):
        error_messages = "; ".join(errors)
        super().__init__(
            message=f"Booking validation failed: {error_messages}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class SessionNotFoundException(BaseRAGException):
    """Raised when a session is not found."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session with ID '{session_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class BookingNotFoundException(BaseRAGException):
    """Raised when a booking is not found."""
    def __init__(self, booking_id: str):
        super().__init__(
            message=f"Booking with ID '{booking_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class TextExtractionException(BaseRAGException):
    """Raised when text extraction from document fails."""
    def __init__(self, file_path: str, reason: str):
        super().__init__(
            message=f"Failed to extract text from '{file_path}': {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class DatabaseException(BaseRAGException):
    """Raised when database operations fail."""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Database operation '{operation}' failed: {reason}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def base_exception_handler(request: Request, exc: BaseRAGException) -> JSONResponse:
    """Global exception handler for custom RAG exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "path": str(request.url)
        }
    )