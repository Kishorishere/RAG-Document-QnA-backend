from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional, Dict
from datetime import datetime, date, timedelta
import logging

from app.database.models import Document, DocumentChunk, Conversation, Booking
from app.core.exceptions import DatabaseException, DocumentNotFoundException, BookingNotFoundException

logger = logging.getLogger(__name__)


# Document Operations
def create_document(db: Session, document_data: dict) -> Document:
    """Create a new document record."""
    try:
        document = Document(**document_data)
        db.add(document)
        db.commit()
        db.refresh(document)
        logger.info(f"Document created: {document.document_id}")
        return document
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create document: {str(e)}")
        raise DatabaseException("create_document", str(e))


def get_document_by_id(db: Session, document_id: str) -> Optional[Document]:
    """Get document by document_id."""
    try:
        return db.query(Document).filter(Document.document_id == document_id).first()
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {str(e)}")
        raise DatabaseException("get_document", str(e))


def get_all_documents(db: Session, skip: int = 0, limit: int = 100) -> List[Document]:
    """Get all documents with pagination."""
    try:
        return db.query(Document).order_by(desc(Document.upload_timestamp)).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Failed to get documents: {str(e)}")
        raise DatabaseException("get_all_documents", str(e))


def delete_document(db: Session, document_id: str) -> bool:
    """Delete a document and its chunks."""
    try:
        document = get_document_by_id(db, document_id)
        if not document:
            raise DocumentNotFoundException(document_id)
        
        db.delete(document)
        db.commit()
        logger.info(f"Document deleted: {document_id}")
        return True
    except DocumentNotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise DatabaseException("delete_document", str(e))


def get_document_count(db: Session) -> int:
    """Get total number of documents."""
    try:
        return db.query(func.count(Document.id)).scalar()
    except Exception as e:
        logger.error(f"Failed to get document count: {str(e)}")
        raise DatabaseException("get_document_count", str(e))


def update_document_chunk_count(db: Session, document_id: str, count: int) -> Document:
    """Update chunk count for a document."""
    try:
        document = get_document_by_id(db, document_id)
        if not document:
            raise DocumentNotFoundException(document_id)
        
        document.chunk_count = count
        db.commit()
        db.refresh(document)
        return document
    except DocumentNotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update chunk count: {str(e)}")
        raise DatabaseException("update_chunk_count", str(e))


# Chunk Operations
def create_chunks(db: Session, document_id: str, chunks: List[dict]) -> List[DocumentChunk]:
    """Bulk insert chunks for a document."""
    try:
        chunk_objects = [DocumentChunk(document_id=document_id, **chunk) for chunk in chunks]
        db.bulk_save_objects(chunk_objects)
        db.commit()
        logger.info(f"Created {len(chunks)} chunks for document {document_id}")
        return chunk_objects
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create chunks: {str(e)}")
        raise DatabaseException("create_chunks", str(e))


def get_chunks_by_document(db: Session, document_id: str) -> List[DocumentChunk]:
    """Get all chunks for a document."""
    try:
        return db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index).all()
    except Exception as e:
        logger.error(f"Failed to get chunks for document {document_id}: {str(e)}")
        raise DatabaseException("get_chunks", str(e))


def delete_chunks_by_document(db: Session, document_id: str) -> int:
    """Delete all chunks for a document."""
    try:
        count = db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.commit()
        logger.info(f"Deleted {count} chunks for document {document_id}")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete chunks: {str(e)}")
        raise DatabaseException("delete_chunks", str(e))


# Conversation Operations
def create_conversation_message(db: Session, session_id: str, role: str, message: str) -> Conversation:
    """Create a new conversation message."""
    try:
        conversation = Conversation(session_id=session_id, role=role, message=message)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create conversation message: {str(e)}")
        raise DatabaseException("create_message", str(e))


def get_conversation_history(db: Session, session_id: str, limit: int = 50) -> List[Conversation]:
    """Get conversation history for a session."""
    try:
        return db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(Conversation.timestamp).limit(limit).all()
    except Exception as e:
        logger.error(f"Failed to get conversation history: {str(e)}")
        raise DatabaseException("get_conversation_history", str(e))


def get_all_sessions(db: Session) -> List[Dict]:
    """Get all unique session IDs with metadata."""
    try:
        sessions = db.query(
            Conversation.session_id,
            func.count(Conversation.id).label('message_count'),
            func.max(Conversation.timestamp).label('last_activity')
        ).group_by(Conversation.session_id).all()
        
        return [
            {
                "session_id": session.session_id,
                "message_count": session.message_count,
                "last_activity": session.last_activity
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Failed to get sessions: {str(e)}")
        raise DatabaseException("get_sessions", str(e))


def delete_conversation_history(db: Session, session_id: str) -> int:
    """Delete all messages for a session."""
    try:
        count = db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).delete()
        db.commit()
        logger.info(f"Deleted {count} messages for session {session_id}")
        return count
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete conversation history: {str(e)}")
        raise DatabaseException("delete_conversation", str(e))


def session_exists(db: Session, session_id: str) -> bool:
    """Check if a session exists."""
    try:
        return db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).first() is not None
    except Exception as e:
        logger.error(f"Failed to check session existence: {str(e)}")
        raise DatabaseException("session_exists", str(e))


# Booking Operations
def create_booking(db: Session, booking_data: dict) -> Booking:
    """Create a new booking."""
    try:
        booking = Booking(**booking_data)
        db.add(booking)
        db.commit()
        db.refresh(booking)
        logger.info(f"Booking created: {booking.booking_id}")
        return booking
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create booking: {str(e)}")
        raise DatabaseException("create_booking", str(e))


def get_booking_by_id(db: Session, booking_id: str) -> Optional[Booking]:
    """Get booking by booking_id."""
    try:
        return db.query(Booking).filter(Booking.booking_id == booking_id).first()
    except Exception as e:
        logger.error(f"Failed to get booking {booking_id}: {str(e)}")
        raise DatabaseException("get_booking", str(e))


def get_all_bookings(db: Session, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> List[Booking]:
    """Get all bookings with optional status filter."""
    try:
        query = db.query(Booking)
        
        if status_filter:
            query = query.filter(Booking.status == status_filter)
        
        return query.order_by(Booking.date, Booking.time).offset(skip).limit(limit).all()
    except Exception as e:
        logger.error(f"Failed to get bookings: {str(e)}")
        raise DatabaseException("get_bookings", str(e))


def get_bookings_by_session(db: Session, session_id: str) -> List[Booking]:
    """Get all bookings for a session."""
    try:
        return db.query(Booking).filter(
            Booking.session_id == session_id
        ).order_by(desc(Booking.created_at)).all()
    except Exception as e:
        logger.error(f"Failed to get bookings for session {session_id}: {str(e)}")
        raise DatabaseException("get_session_bookings", str(e))


def update_booking_status(db: Session, booking_id: str, status: str) -> Booking:
    """Update booking status."""
    try:
        booking = get_booking_by_id(db, booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        booking.status = status
        booking.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(booking)
        logger.info(f"Booking {booking_id} status updated to {status}")
        return booking
    except BookingNotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update booking status: {str(e)}")
        raise DatabaseException("update_booking_status", str(e))


def delete_booking(db: Session, booking_id: str) -> bool:
    """Delete a booking."""
    try:
        booking = get_booking_by_id(db, booking_id)
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        db.delete(booking)
        db.commit()
        logger.info(f"Booking deleted: {booking_id}")
        return True
    except BookingNotFoundException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete booking {booking_id}: {str(e)}")
        raise DatabaseException("delete_booking", str(e))


def get_upcoming_bookings(db: Session, days: int = 7) -> List[Booking]:
    """Get upcoming bookings in next N days."""
    try:
        today = date.today()
        future_date = today + timedelta(days=days)
        
        return db.query(Booking).filter(
            Booking.date >= today,
            Booking.date <= future_date,
            Booking.status != "cancelled"
        ).order_by(Booking.date, Booking.time).all()
    except Exception as e:
        logger.error(f"Failed to get upcoming bookings: {str(e)}")
        raise DatabaseException("get_upcoming_bookings", str(e))


def get_booking_count_by_status(db: Session) -> Dict[str, int]:
    """Get booking counts grouped by status."""
    try:
        results = db.query(
            Booking.status,
            func.count(Booking.id).label('count')
        ).group_by(Booking.status).all()
        
        return {result.status: result.count for result in results}
    except Exception as e:
        logger.error(f"Failed to get booking counts: {str(e)}")
        raise DatabaseException("get_booking_counts", str(e))