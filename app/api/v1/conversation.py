from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging

from app.core.dependencies import get_db, get_rag_service, get_memory_service
from app.database import crud
from app.models.schemas import (
    ChatRequest, ChatResponse, ConversationHistoryResponse,
    ConversationMessage, SuccessResponse, SessionListResponse, SessionInfo
)
from app.services.rag_service import RAGService
from app.services.memory_service import MemoryService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def ask_question(
    request: ChatRequest,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Ask a question and get an answer with RAG.
    
    - **question**: User question
    - **session_id**: Conversation session identifier
    - **document_ids**: Optional list of document IDs to search in
    """
    try:
        result = rag_service.ask(
            question=request.question,
            session_id=request.session_id,
            memory_service=memory_service,
            document_ids=request.document_ids,
            top_k=5
        )
        
        sources = [
            {
                "text": source["text"],
                "document_id": source["document_id"],
                "document_name": source["document_name"],
                "chunk_index": source["chunk_index"],
                "similarity_score": source["similarity_score"]
            }
            for source in result["sources"]
        ]
        
        logger.info(f"Question answered for session {request.session_id}")
        
        return ChatResponse(
            answer=result["answer"],
            sources=sources,
            session_id=request.session_id,
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Chat request failed: {str(e)}")
        raise


@router.get("/chat/history/{session_id}", response_model=ConversationHistoryResponse)
async def get_chat_history(
    session_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Get conversation history for a session.
    
    - **session_id**: Conversation session identifier
    - **limit**: Maximum number of messages to retrieve
    """
    try:
        messages = memory_service.get_conversation_history(session_id, limit)
        
        message_list = [
            ConversationMessage(
                role=msg["role"],
                message=msg["message"],
                timestamp=msg["timestamp"]
            )
            for msg in messages
        ]
        
        return ConversationHistoryResponse(
            session_id=session_id,
            messages=message_list,
            total=len(message_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to get chat history: {str(e)}")
        raise


@router.delete("/chat/history/{session_id}", response_model=SuccessResponse)
async def clear_chat_history(
    session_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    Clear all conversation history for a session.
    
    - **session_id**: Conversation session identifier
    """
    try:
        count = memory_service.clear_session(session_id)
        
        logger.info(f"Cleared history for session {session_id}")
        
        return SuccessResponse(
            message=f"Deleted {count} messages from session {session_id}",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Failed to clear chat history: {str(e)}")
        raise


@router.get("/chat/sessions", response_model=SessionListResponse)
async def list_sessions(
    memory_service: MemoryService = Depends(get_memory_service)
):
    """
    List all active chat sessions.
    """
    try:
        sessions = memory_service.get_all_sessions()
        
        session_list = [
            SessionInfo(
                session_id=session["session_id"],
                message_count=session["message_count"],
                last_activity=session["last_activity"]
            )
            for session in sessions
        ]
        
        return SessionListResponse(
            sessions=session_list,
            total=len(session_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to list sessions: {str(e)}")
        raise