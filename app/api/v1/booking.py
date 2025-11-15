from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.dependencies import get_db, get_booking_service
from app.database import crud
from app.models.schemas import (
    BookingRequest, BookingResponse, BookingListResponse,
    BookingStatusUpdate, SuccessResponse
)
from app.services.booking_service import BookingService
from app.core.exceptions import BookingNotFoundException

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/booking", response_model=BookingResponse)
async def create_booking(
    request: BookingRequest,
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Create a booking by extracting information from natural language message.
    
    - **message**: Natural language message containing booking details
    - **session_id**: Session identifier for tracking
    
    Example message: "I'd like to book an appointment for John Doe on 2024-12-25 at 14:00. Email: john@example.com"
    """
    try:
        result = booking_service.process_booking_request(
            message=request.message,
            session_id=request.session_id
        )
        
        logger.info(f"Booking created: {result['booking_id']}")
        
        return BookingResponse(
            booking_id=result["booking_id"],
            status=result["status"],
            name=result["name"],
            email=result["email"],
            date=result["date"],
            time=result["time"],
            session_id=result["session_id"],
            message=result["message"],
            created_at=result["created_at"]
        )
    
    except Exception as e:
        logger.error(f"Failed to create booking: {str(e)}")
        raise


@router.get("/booking", response_model=BookingListResponse)
async def list_bookings(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status: Optional[str] = Query(default=None),
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    List all bookings with optional status filter.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    - **status**: Optional status filter (pending/confirmed/cancelled)
    """
    try:
        bookings = booking_service.list_bookings(skip, limit, status)
        
        booking_list = [
            BookingResponse(
                booking_id=b["booking_id"],
                status=b["status"],
                name=b["name"],
                email=b["email"],
                date=b["date"],
                time=b["time"],
                session_id=b["session_id"],
                message="",
                created_at=b["created_at"]
            )
            for b in bookings
        ]
        
        from app.database import crud
        total = len(crud.get_all_bookings(booking_service.db, 0, 10000, status))
        
        return BookingListResponse(
            bookings=booking_list,
            total=total,
            skip=skip,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"Failed to list bookings: {str(e)}")
        raise


@router.get("/booking/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Get specific booking details by ID.
    
    - **booking_id**: Booking identifier
    """
    try:
        booking = booking_service.get_booking(booking_id)
        
        if not booking:
            raise BookingNotFoundException(booking_id)
        
        return BookingResponse(
            booking_id=booking["booking_id"],
            status=booking["status"],
            name=booking["name"],
            email=booking["email"],
            date=booking["date"],
            time=booking["time"],
            session_id=booking["session_id"],
            message="",
            created_at=booking["created_at"]
        )
    
    except Exception as e:
        logger.error(f"Failed to get booking: {str(e)}")
        raise


@router.patch("/booking/{booking_id}", response_model=BookingResponse)
async def update_booking_status(
    booking_id: str,
    status_update: BookingStatusUpdate,
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Update booking status.
    
    - **booking_id**: Booking identifier
    - **status**: New status (pending/confirmed/cancelled)
    """
    try:
        booking = booking_service.update_booking_status(
            booking_id=booking_id,
            status=status_update.status.value
        )
        
        logger.info(f"Booking {booking_id} status updated to {status_update.status.value}")
        
        return BookingResponse(
            booking_id=booking["booking_id"],
            status=booking["status"],
            name=booking["name"],
            email=booking["email"],
            date=booking["date"],
            time=booking["time"],
            session_id="",
            message=f"Status updated to {status_update.status.value}",
            created_at=booking["updated_at"]
        )
    
    except Exception as e:
        logger.error(f"Failed to update booking status: {str(e)}")
        raise


@router.delete("/booking/{booking_id}", response_model=SuccessResponse)
async def delete_booking(
    booking_id: str,
    booking_service: BookingService = Depends(get_booking_service)
):
    """
    Delete a booking.
    
    - **booking_id**: Booking identifier
    """
    try:
        result = booking_service.delete_booking(booking_id)
        
        if result:
            logger.info(f"Booking deleted: {booking_id}")
            return SuccessResponse(
                message=f"Booking {booking_id} deleted successfully",
                success=True
            )
        else:
            raise BookingNotFoundException(booking_id)
    
    except Exception as e:
        logger.error(f"Failed to delete booking: {str(e)}")
        raise


@router.get("/booking/session/{session_id}", response_model=BookingListResponse)
async def get_session_bookings(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all bookings for a specific session.
    
    - **session_id**: Session identifier
    """
    try:
        bookings = crud.get_bookings_by_session(db, session_id)
        
        booking_list = [
            BookingResponse(
                booking_id=b.booking_id,
                status=b.status,
                name=b.name,
                email=b.email,
                date=b.date,
                time=b.time,
                session_id=b.session_id,
                message="",
                created_at=b.created_at
            )
            for b in bookings
        ]
        
        return BookingListResponse(
            bookings=booking_list,
            total=len(booking_list),
            skip=0,
            limit=len(booking_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to get session bookings: {str(e)}")
        raise