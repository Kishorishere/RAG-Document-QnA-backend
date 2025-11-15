from enum import Enum


class ChunkingStrategy(str, Enum):
    """Text chunking strategies for document processing."""
    FIXED = "fixed"
    RECURSIVE = "recursive"


class BookingStatus(str, Enum):
    """Status options for booking records."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class MessageRole(str, Enum):
    """Role types for conversation messages."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"