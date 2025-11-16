import redis
import json
from typing import List, Dict
from datetime import datetime
import logging

from app.models.enums import MessageRole
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class MemoryService:
    """Service for managing conversation memory using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        """
        Initialize memory service with Redis client.
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
    
    def save_message(self, session_id: str, role: str, message: str) -> Dict:
        """
        Save a conversation message to Redis.
        
        Args:
            session_id: Conversation session ID
            role: Message role (user/assistant/system)
            message: Message content
        
        Returns:
            Dictionary with saved message info
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            message_data = {
                "role": role,
                "message": message,
                "timestamp": timestamp
            }
            
            key = f"session:{session_id}:messages"
            self.redis.rpush(key, json.dumps(message_data))
            
            self.redis.hset(f"session:{session_id}:meta", "last_activity", timestamp)
            
            logger.info(f"Saved {role} message for session {session_id}")
            
            return {
                "session_id": session_id,
                "role": role,
                "message": message,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to save message to Redis: {str(e)}")
            raise DatabaseException("save_message", str(e))
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """
        Retrieve conversation history for a session from Redis.
        
        Args:
            session_id: Conversation session ID
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of conversation messages
        """
        try:
            key = f"session:{session_id}:messages"
            
            messages_raw = self.redis.lrange(key, -limit, -1)
            
            history = []
            for msg_json in messages_raw:
                msg = json.loads(msg_json)
                history.append({
                    "role": msg["role"],
                    "message": msg["message"],
                    "timestamp": msg["timestamp"]
                })
            
            logger.info(f"Retrieved {len(history)} messages for session {session_id}")
            return history
            
        except Exception as e:
            logger.error(f"Failed to get conversation history from Redis: {str(e)}")
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
            key = f"session:{session_id}:messages"
            meta_key = f"session:{session_id}:meta"
            
            count = self.redis.llen(key)
            
            self.redis.delete(key)
            self.redis.delete(meta_key)
            
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
            pattern = "session:*:messages"
            sessions = []
            
            for key in self.redis.scan_iter(match=pattern):
                session_id = key.decode().split(":")[1]
                
                message_count = self.redis.llen(key)
                
                meta_key = f"session:{session_id}:meta"
                last_activity = self.redis.hget(meta_key, "last_activity")
                
                sessions.append({
                    "session_id": session_id,
                    "message_count": message_count,
                    "last_activity": last_activity.decode() if last_activity else None
                })
            
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
            key = f"session:{session_id}:messages"
            return self.redis.exists(key) > 0
            
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
            key = f"session:{session_id}:messages"
            return self.redis.llen(key)
            
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