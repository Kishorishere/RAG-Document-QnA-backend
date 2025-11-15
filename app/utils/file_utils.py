import os
import uuid
import shutil
from pathlib import Path
from typing import Optional
import logging

from app.core.exceptions import InvalidFileTypeException, FileTooLargeException

logger = logging.getLogger(__name__)


def validate_file_type(filename: str, allowed_types: list) -> bool:
    """
    Validate if file extension is allowed.
    
    Args:
        filename: Name of the file
        allowed_types: List of allowed extensions (without dot)
    
    Returns:
        True if valid, raises exception otherwise
    """
    extension = get_file_extension(filename)
    if extension not in allowed_types:
        raise InvalidFileTypeException(extension, allowed_types)
    return True


def validate_file_size(file_size: int, max_size_bytes: int) -> bool:
    """
    Validate if file size is within limit.
    
    Args:
        file_size: Size of file in bytes
        max_size_bytes: Maximum allowed size in bytes
    
    Returns:
        True if valid, raises exception otherwise
    """
    if file_size > max_size_bytes:
        raise FileTooLargeException(file_size, max_size_bytes)
    return True


def save_uploaded_file(file, upload_dir: str) -> str:
    """
    Save uploaded file with unique filename.
    
    Args:
        file: FastAPI UploadFile object
        upload_dir: Directory to save file
    
    Returns:
        Full path to saved file
    """
    try:
        ensure_directory_exists(upload_dir)
        
        extension = get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}.{extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to save file: {str(e)}")
        raise


def delete_file(file_path: str) -> bool:
    """
    Delete a file from disk.
    
    Args:
        file_path: Path to file
    
    Returns:
        True if deleted successfully
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted: {file_path}")
            return True
        else:
            logger.warning(f"File not found for deletion: {file_path}")
            return False
    except Exception as e:
        logger.error(f"Failed to delete file {file_path}: {str(e)}")
        return False


def get_file_extension(filename: str) -> str:
    """
    Get file extension without dot.
    
    Args:
        filename: Name of the file
    
    Returns:
        Extension in lowercase
    """
    return Path(filename).suffix.lstrip('.').lower()


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
    
    Returns:
        Size in bytes
    """
    try:
        return os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Failed to get file size for {file_path}: {str(e)}")
        return 0


def ensure_directory_exists(directory: str) -> None:
    """
    Create directory if it doesn't exist.
    
    Args:
        directory: Path to directory
    """
    try:
        os.makedirs(directory, exist_ok=True)
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {str(e)}")
        raise


def sanitize_filename(filename: str) -> str:
    """
    Remove dangerous characters from filename.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    return sanitized.strip()


def get_original_filename(file) -> str:
    """
    Get original filename from uploaded file.
    
    Args:
        file: FastAPI UploadFile object
    
    Returns:
        Sanitized original filename
    """
    return sanitize_filename(file.filename)