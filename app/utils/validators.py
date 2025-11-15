import re
from datetime import datetime, date, time
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    Validate email format using regex.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid email format
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_date_string(date_str: str, date_format: str = "%Y-%m-%d") -> Tuple[bool, datetime]:
    """
    Parse and validate date string.
    
    Args:
        date_str: Date string to parse
        date_format: Expected date format
    
    Returns:
        Tuple of (is_valid, parsed_date)
    """
    try:
        parsed_date = datetime.strptime(date_str, date_format)
        return True, parsed_date
    except ValueError as e:
        logger.warning(f"Invalid date format: {date_str}, error: {str(e)}")
        return False, None


def validate_time_string(time_str: str) -> Tuple[bool, time]:
    """
    Parse and validate time string (supports multiple formats).
    
    Args:
        time_str: Time string to parse (e.g., "2pm", "14:00", "2:00 PM")
    
    Returns:
        Tuple of (is_valid, parsed_time)
    """
    time_str = time_str.strip().upper()
    
    formats = [
        "%H:%M",
        "%I:%M %p",
        "%I%p",
        "%H:%M:%S"
    ]
    
    for fmt in formats:
        try:
            parsed_time = datetime.strptime(time_str, fmt).time()
            return True, parsed_time
        except ValueError:
            continue
    
    logger.warning(f"Invalid time format: {time_str}")
    return False, None


def is_future_date(check_date: date) -> bool:
    """
    Check if date is in the future.
    
    Args:
        check_date: Date to check
    
    Returns:
        True if date is after today
    """
    today = date.today()
    return check_date > today


def is_business_hours(check_time: time, start_hour: int = 9, end_hour: int = 17) -> bool:
    """
    Check if time is within business hours.
    
    Args:
        check_time: Time to check
        start_hour: Business start hour (default 9 AM)
        end_hour: Business end hour (default 5 PM)
    
    Returns:
        True if within business hours
    """
    return start_hour <= check_time.hour < end_hour


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID to validate
    
    Returns:
        True if valid format
    """
    if not session_id or len(session_id) < 1 or len(session_id) > 255:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, session_id))


def validate_document_id(document_id: str) -> bool:
    """
    Validate document ID format (UUID).
    
    Args:
        document_id: Document ID to validate
    
    Returns:
        True if valid UUID format
    """
    uuid_pattern = r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$'
    return bool(re.match(uuid_pattern, document_id.lower()))


def validate_chunking_strategy(strategy: str) -> bool:
    """
    Validate chunking strategy.
    
    Args:
        strategy: Strategy name
    
    Returns:
        True if valid strategy
    """
    valid_strategies = ['fixed', 'recursive']
    return strategy.lower() in valid_strategies


def validate_booking_status(status: str) -> bool:
    """
    Validate booking status.
    
    Args:
        status: Status value
    
    Returns:
        True if valid status
    """
    valid_statuses = ['pending', 'confirmed', 'cancelled']
    return status.lower() in valid_statuses


def validate_positive_integer(value: int, max_value: int = None) -> bool:
    """
    Validate positive integer with optional max value.
    
    Args:
        value: Integer to validate
        max_value: Maximum allowed value (optional)
    
    Returns:
        True if valid
    """
    if value < 0:
        return False
    
    if max_value is not None and value > max_value:
        return False
    
    return True


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """
    Sanitize user input by removing dangerous characters.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    text = text[:max_length]
    
    dangerous_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'onerror=',
        r'onclick=',
    ]
    
    for pattern in dangerous_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    return text.strip()