from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Document(Base):
    """SQLAlchemy model for documents."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_size = Column(Integer, nullable=False)
    chunk_count = Column(Integer, default=0)
    chunking_strategy = Column(String(50), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(document_id='{self.document_id}', filename='{self.filename}')>"


class DocumentChunk(Base):
    """SQLAlchemy model for document chunks."""
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(255), ForeignKey("documents.document_id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Composite index for faster queries
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
    )
    
    def __repr__(self):
        return f"<DocumentChunk(document_id='{self.document_id}', chunk_index={self.chunk_index})>"


class Conversation(Base):
    """SQLAlchemy model for conversation messages."""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), index=True, nullable=False)
    role = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Composite index for session queries
    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<Conversation(session_id='{self.session_id}', role='{self.role}')>"


class Booking(Base):
    """SQLAlchemy model for bookings."""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(String(255), unique=True, index=True, nullable=False)
    session_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Composite index for booking queries
    __table_args__ = (
        Index('idx_status_date', 'status', 'date'),
    )
    
    def __repr__(self):
        return f"<Booking(booking_id='{self.booking_id}', name='{self.name}', status='{self.status}')>"