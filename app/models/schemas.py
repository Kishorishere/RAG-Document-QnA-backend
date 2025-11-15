from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional
from datetime import datetime, date, time
from app.models.enums import ChunkingStrategy, BookingStatus, MessageRole


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""
    document_id: str
    filename: str
    chunks_created: int
    strategy_used: str
    message: str


class DocumentMetadata(BaseModel):
    """Model for document metadata."""
    document_id: str
    filename: str
    file_size: int
    chunk_count: int
    chunking_strategy: str
    upload_timestamp: datetime
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: List[DocumentMetadata]
    total: int
    skip: int
    limit: int


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=255)
    document_ids: Optional[List[str]] = None
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError("Question cannot be empty or whitespace only")
        return v.strip()


class SourceChunk(BaseModel):
    """Model for source chunk information."""
    text: str
    document_id: str
    document_name: str
    chunk_index: int
    similarity_score: float


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: List[SourceChunk]
    session_id: str
    timestamp: datetime


class ConversationMessage(BaseModel):
    """Model for a single conversation message."""
    role: str
    message: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class ConversationHistoryResponse(BaseModel):
    """Response model for conversation history."""
    session_id: str
    messages: List[ConversationMessage]
    total: int


class SessionInfo(BaseModel):
    """Model for session information."""
    session_id: str
    message_count: int
    last_activity: datetime


class SessionListResponse(BaseModel):
    """Response model for listing sessions."""
    sessions: List[SessionInfo]
    total: int


class BookingRequest(BaseModel):
    """Request model for creating a booking."""
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: str = Field(..., min_length=1, max_length=255)


class BookingInfo(BaseModel):
    """Model for booking information."""
    name: str
    email: EmailStr
    date: str
    time: str


class BookingResponse(BaseModel):
    """Response model for booking operations."""
    booking_id: str
    status: str
    name: str
    email: str
    date: date
    time: time
    session_id: str
    message: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookingListResponse(BaseModel):
    """Response model for listing bookings."""
    bookings: List[BookingResponse]
    total: int
    skip: int
    limit: int


class BookingStatusUpdate(BaseModel):
    """Request model for updating booking status."""
    status: BookingStatus
    
    @validator('status')
    def validate_status(cls, v):
        if v not in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED]:
            raise ValueError(f"Invalid status. Must be one of: {', '.join([s.value for s in BookingStatus])}")
        return v


class ErrorResponse(BaseModel):
    """Response model for errors."""
    error: str
    message: str
    timestamp: datetime
    path: Optional[str] = None


class SuccessResponse(BaseModel):
    """Generic success response."""
    message: str
    success: bool = True


class ChunkResponse(BaseModel):
    """Response model for document chunks."""
    chunk_index: int
    chunk_text: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class DocumentChunksResponse(BaseModel):
    """Response model for listing document chunks."""
    document_id: str
    filename: str
    chunks: List[ChunkResponse]
    total_chunks: int


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)