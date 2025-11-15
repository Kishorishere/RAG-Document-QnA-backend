from groq import Groq
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime, date, time
import json
import uuid
import logging

from app.database import crud
from app.core.exceptions import BookingValidationException, LLMException, DatabaseException
from app.utils.validators import validate_email, validate_date_string, validate_time_string, is_future_date, is_business_hours

logger = logging.getLogger(__name__)


class BookingService:
    """Service for managing booking operations with LLM extraction."""
    
    def __init__(self, groq_client: Groq, db: Session, groq_model: str = "llama-3.1-8b-instant"):
        """
        Initialize booking service.
        
        Args:
            groq_client: Groq API client
            db: Database session
            groq_model: Groq model name
        """
        self.groq_client = groq_client
        self.db = db
        self.groq_model = groq_model
    
    def extract_booking_info(self, message: str) -> Dict:
        """
        Extract booking information from natural language message using LLM.
        
        Args:
            message: User message containing booking details
        
        Returns:
            Dictionary with extracted booking info
        """
        try:
            extraction_prompt = f"""Extract booking information from the following message. Return ONLY a JSON object with these fields:
- name: person's full name
- email: email address
- date: date in YYYY-MM-DD format
- time: time in HH:MM format (24-hour)

If any information is missing, use null for that field.

Message: {message}

Return only the JSON, no other text."""

            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=[
                    {"role": "system", "content": "You are a booking information extraction assistant. Extract booking details and return only JSON."},
                    {"role": "user", "content": extraction_prompt}
                ],
                temperature=0.1,
                max_tokens=200
            )
            
            result_text = response.choices[0].message.content.strip()
            
            result_text = result_text.replace("```json", "").replace("```", "").strip()
            
            booking_info = json.loads(result_text)
            
            logger.info("Successfully extracted booking information")
            return booking_info
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            raise LLMException(f"Could not extract booking information: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to extract booking info: {str(e)}")
            raise LLMException(str(e))
    
    def validate_booking_data(self, booking_info: Dict) -> tuple[bool, List[str]]:
        """
        Validate extracted booking data.
        
        Args:
            booking_info: Dictionary with booking information
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not booking_info.get("name"):
            errors.append("Name is required")
        
        email = booking_info.get("email")
        if not email:
            errors.append("Email is required")
        elif not validate_email(email):
            errors.append("Invalid email format")
        
        date_str = booking_info.get("date")
        if not date_str:
            errors.append("Date is required")
        else:
            is_valid, parsed_date = validate_date_string(date_str)
            if not is_valid:
                errors.append("Invalid date format. Use YYYY-MM-DD")
            else:
                booking_date = parsed_date.date()
                if not is_future_date(booking_date):
                    errors.append("Date must be in the future")
        
        time_str = booking_info.get("time")
        if not time_str:
            errors.append("Time is required")
        else:
            is_valid, parsed_time = validate_time_string(time_str)
            if not is_valid:
                errors.append("Invalid time format. Use HH:MM")
            else:
                if not is_business_hours(parsed_time):
                    errors.append("Time must be within business hours (9 AM - 5 PM)")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def create_booking(self, booking_info: Dict, session_id: str) -> Dict:
        """
        Create a new booking in the database.
        
        Args:
            booking_info: Validated booking information
            session_id: Session ID for tracking
        
        Returns:
            Created booking details
        """
        try:
            is_valid, errors = self.validate_booking_data(booking_info)
            if not is_valid:
                raise BookingValidationException(errors)
            
            parsed_date = datetime.strptime(booking_info["date"], "%Y-%m-%d").date()
            parsed_time = datetime.strptime(booking_info["time"], "%H:%M").time()
            
            booking_data = {
                "booking_id": str(uuid.uuid4()),
                "session_id": session_id,
                "name": booking_info["name"],
                "email": booking_info["email"],
                "date": parsed_date,
                "time": parsed_time,
                "status": "pending"
            }
            
            booking = crud.create_booking(self.db, booking_data)
            
            logger.info(f"Created booking: {booking.booking_id}")
            
            return {
                "booking_id": booking.booking_id,
                "status": booking.status,
                "name": booking.name,
                "email": booking.email,
                "date": booking.date,
                "time": booking.time,
                "session_id": booking.session_id,
                "created_at": booking.created_at
            }
            
        except BookingValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to create booking: {str(e)}")
            raise DatabaseException("create_booking", str(e))
    
    def get_booking(self, booking_id: str) -> Optional[Dict]:
        """
        Get booking by ID.
        
        Args:
            booking_id: Booking identifier
        
        Returns:
            Booking details or None
        """
        try:
            booking = crud.get_booking_by_id(self.db, booking_id)
            
            if not booking:
                return None
            
            return {
                "booking_id": booking.booking_id,
                "status": booking.status,
                "name": booking.name,
                "email": booking.email,
                "date": booking.date,
                "time": booking.time,
                "session_id": booking.session_id,
                "created_at": booking.created_at,
                "updated_at": booking.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to get booking: {str(e)}")
            raise DatabaseException("get_booking", str(e))
    
    def update_booking_status(self, booking_id: str, status: str) -> Dict:
        """
        Update booking status.
        
        Args:
            booking_id: Booking identifier
            status: New status
        
        Returns:
            Updated booking details
        """
        try:
            booking = crud.update_booking_status(self.db, booking_id, status)
            
            logger.info(f"Updated booking {booking_id} status to {status}")
            
            return {
                "booking_id": booking.booking_id,
                "status": booking.status,
                "name": booking.name,
                "email": booking.email,
                "date": booking.date,
                "time": booking.time,
                "updated_at": booking.updated_at
            }
            
        except Exception as e:
            logger.error(f"Failed to update booking status: {str(e)}")
            raise DatabaseException("update_booking_status", str(e))
    
    def list_bookings(self, skip: int = 0, limit: int = 100, status_filter: Optional[str] = None) -> List[Dict]:
        """
        List bookings with optional status filter.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            status_filter: Optional status filter
        
        Returns:
            List of bookings
        """
        try:
            bookings = crud.get_all_bookings(self.db, skip, limit, status_filter)
            
            return [
                {
                    "booking_id": b.booking_id,
                    "status": b.status,
                    "name": b.name,
                    "email": b.email,
                    "date": b.date,
                    "time": b.time,
                    "session_id": b.session_id,
                    "created_at": b.created_at
                }
                for b in bookings
            ]
            
        except Exception as e:
            logger.error(f"Failed to list bookings: {str(e)}")
            raise DatabaseException("list_bookings", str(e))
    
    def delete_booking(self, booking_id: str) -> bool:
        """
        Delete a booking.
        
        Args:
            booking_id: Booking identifier
        
        Returns:
            True if deleted successfully
        """
        try:
            result = crud.delete_booking(self.db, booking_id)
            logger.info(f"Deleted booking: {booking_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to delete booking: {str(e)}")
            raise DatabaseException("delete_booking", str(e))
    
    def process_booking_request(self, message: str, session_id: str) -> Dict:
        """
        Main orchestration: extract, validate, and create booking.
        
        Args:
            message: User message with booking details
            session_id: Session ID
        
        Returns:
            Created booking details with message
        """
        try:
            booking_info = self.extract_booking_info(message)
            
            is_valid, errors = self.validate_booking_data(booking_info)
            
            if not is_valid:
                raise BookingValidationException(errors)
            
            booking = self.create_booking(booking_info, session_id)
            
            booking["message"] = "Booking created successfully"
            
            logger.info(f"Processed booking request for session {session_id}")
            return booking
            
        except (BookingValidationException, LLMException):
            raise
        except Exception as e:
            logger.error(f"Failed to process booking request: {str(e)}")
            raise DatabaseException("process_booking_request", str(e))