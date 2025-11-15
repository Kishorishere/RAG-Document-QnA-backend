from sqlalchemy.orm import Session
from typing import List, Dict
import logging

from app.database import crud
from app.models.enums import MessageRole
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing conversation memory and history."""
    
    def __init__(self, db: Session):
        """
        Initialize memory service.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def save_message(self, session_id: str, role: str, message: str) -> Dict:
        """
        Save a conversation message.
        
        Args:
            session_id: Conversation session ID
            role: Message role (user/assistant/system)
            message: Message content
        
        Returns:
            Dictionary with saved message info
        """
        try:
            conversation = crud.create_conversation_message(
                db=self.db,
                session_id=session_id,
                role=role,
                message=message
            )
            
            logger.info(f"Saved {role} message for session {session_id}")
            
            return {
                "id": conversation.id,
                "session_id": conversation.session_id,
                "role": conversation.role,
                "message": conversation.message,
                "timestamp": conversation.timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to save message: {str(e)}")
            raise DatabaseException("save_message", str(e))
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Retrieve conversation history for a session.
        
        Args:
            session_id: Conversation session ID
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of conversation messages
        """
        try:
            messages = crud.get_conversation_history(
                db=self.db,
                session_id=session_id,
                limit=limit
            )
            
            history = [
                {
                    "role": msg.role,
                    "message": msg.message,
                    "timestamp": msg.timestamp
                }
                for msg in messages
            ]
            
            logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            raise DatabaseException("get_conversation_history", str(e))
    
    def format_history_for_llm(self, messages: List[Dict]) -> List[Dict]:
        """
        Format conversation history for LLM API.
        
        Args:
            messages: List of conversation messages
        
        Returns:
            Formatted messages for LLM
        """
        try:
            formatted = []
            
            for msg in messages:
                formatted.append({
                    "role": msg["role"],
                    "content": msg["message"]
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Failed to format history: {str(e)}")
            return []
    
    def get_recent_context(self, session_id: str, max_messages: int = 10) -> str:
        """
        Get recent conversation context as a single string.
        
        Args:
            session_id: Conversation session ID
            max_messages: Maximum number of recent messages
        
        Returns:
            Formatted conversation context
        """
        try:
            messages = self.get_conversation_history(session_id, max_messages)
            
            context_parts = []
            for msg in messages:
                role_label = "User" if msg["role"] == MessageRole.USER else "Assistant"
                context_parts.append(f"{role_label}: {msg['message']}")
            
            context = "\n\n".join(context_parts)
            return context
            
        except Exception as e:
            logger.error(f"Failed to get recent context: {str(e)}")
            return ""
    
    def clear_session(self, session_id: str) -> int:
        """
        Delete all messages for a session.
        
        Args:
            session_id: Conversation session ID
        
        Returns:
            Number of messages deleted
        """
        try:
            count = crud.delete_conversation_history(
                db=self.db,
                session_id=session_id
            )
            
            logger.info(f"Cleared {count} messages from session {session_id}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clear session: {str(e)}")
            raise DatabaseException("clear_session", str(e))
    
    def get_all_sessions(self) -> List[Dict]:
        """
        Get all active sessions with metadata.
        
        Returns:
            List of session information
        """
        try:
            sessions = crud.get_all_sessions(self.db)
            
            logger.info(f"Retrieved {len(sessions)} active sessions")
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {str(e)}")
            raise DatabaseException("get_all_sessions", str(e))
    
    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.
        
        Args:
            session_id: Session ID to check
        
        Returns:
            True if session exists
        """
        try:
            exists = crud.session_exists(self.db, session_id)
            return exists
            
        except Exception as e:
            logger.error(f"Failed to check session existence: {str(e)}")
            return False
    
    def get_session_message_count(self, session_id: str) -> int:
        """
        Get count of messages in a session.
        
        Args:
            session_id: Session ID
        
        Returns:
            Number of messages
        """
        try:
            messages = self.get_conversation_history(session_id, limit=10000)
            return len(messages)
            
        except Exception as e:
            logger.error(f"Failed to get message count: {str(e)}")
            return 0
    
    def trim_history(self, messages: List[Dict], max_messages: int) -> List[Dict]:
        """
        Trim conversation history to maximum number of messages.
        
        Args:
            messages: List of messages
            max_messages: Maximum messages to keep
        
        Returns:
            Trimmed list of messages
        """
        if len(messages) <= max_messages:
            return messages
        
        return messages[-max_messages:]