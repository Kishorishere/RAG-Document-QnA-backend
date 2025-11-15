from groq import Groq
from typing import List, Dict, Optional
import logging

from app.services.vector_store import QdrantVectorStore
from app.services.embedding_service import EmbeddingService
from app.services.memory_service import MemoryService
from app.core.exceptions import LLMException
from app.models.enums import MessageRole

logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation pipeline."""
    
    def __init__(
        self, 
        vector_store: QdrantVectorStore, 
        embedding_service: EmbeddingService,
        groq_client: Groq,
        groq_model: str = "llama-3.1-8b-instant"
    ):
        """
        Initialize RAG service.
        
        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
            groq_client: Groq API client
            groq_model: Groq model name
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.groq_client = groq_client
        self.groq_model = groq_model
    
    def retrieve_context(
        self, 
        question: str, 
        document_ids: Optional[List[str]] = None, 
        top_k: int = 5
    ) -> List[Dict]:
        """
        Retrieve relevant context chunks for a question.
        
        Args:
            question: User question
            document_ids: Optional list of document IDs to filter
            top_k: Number of chunks to retrieve
        
        Returns:
            List of relevant chunks with metadata
        """
        try:
            query_embedding = self.embedding_service.encode_query(question)
            
            results = self.vector_store.similarity_search(
                query_embedding=query_embedding.tolist(),
                limit=top_k,
                document_ids=document_ids
            )
            
            logger.info(f"Retrieved {len(results)} context chunks for question")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {str(e)}")
            return []
    
    def build_prompt(
        self, 
        question: str, 
        context_chunks: List[Dict], 
        conversation_history: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """
        Build prompt with context and history for LLM.
        
        Args:
            question: User question
            context_chunks: Retrieved context chunks
            conversation_history: Previous conversation messages
        
        Returns:
            Formatted messages for LLM API
        """
        try:
            messages = []
            
            system_message = """You are a helpful AI assistant that answers questions based on provided context.
Rules:
- Answer based on the provided context
- If the context doesn't contain relevant information, say so
- Be concise and accurate
- Cite sources when appropriate
- If you're unsure, acknowledge it"""
            
            messages.append({
                "role": "system",
                "content": system_message
            })
            
            if conversation_history:
                history_limit = min(len(conversation_history), 5)
                messages.extend(conversation_history[-history_limit:])
            
            context_text = self._format_context(context_chunks)
            
            user_prompt = f"""Context:
{context_text}

Question: {question}

Please answer the question based on the context provided above."""
            
            messages.append({
                "role": "user",
                "content": user_prompt
            })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to build prompt: {str(e)}")
            raise
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format context chunks into a single string.
        
        Args:
            chunks: List of context chunks
        
        Returns:
            Formatted context string
        """
        if not chunks:
            return "No relevant context found."
        
        context_parts = []
        for idx, chunk in enumerate(chunks, 1):
            doc_name = chunk.get("document_name", "Unknown")
            text = chunk.get("chunk_text", "")
            score = chunk.get("score", 0.0)
            
            context_parts.append(f"[Source {idx} - {doc_name} (relevance: {score:.2f})]:\n{text}")
        
        return "\n\n".join(context_parts)
    
    def generate_answer(self, messages: List[Dict]) -> str:
        """
        Generate answer using Groq LLM.
        
        Args:
            messages: Formatted messages for LLM
        
        Returns:
            Generated answer text
        """
        try:
            response = self.groq_client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=1,
                stream=False
            )
            
            answer = response.choices[0].message.content
            
            logger.info("Generated answer from LLM")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to generate answer: {str(e)}")
            raise LLMException(str(e))
    
    def ask(
        self, 
        question: str, 
        session_id: str, 
        memory_service: MemoryService,
        document_ids: Optional[List[str]] = None,
        top_k: int = 5
    ) -> Dict:
        """
        Main RAG pipeline: retrieve, build prompt, generate answer.
        
        Args:
            question: User question
            session_id: Conversation session ID
            memory_service: Memory service instance
            document_ids: Optional document IDs to filter
            top_k: Number of context chunks to retrieve
        
        Returns:
            Dictionary with answer and sources
        """
        try:
            memory_service.save_message(session_id, MessageRole.USER, question)
            
            context_chunks = self.retrieve_context(question, document_ids, top_k)
            
            conversation_history = memory_service.get_conversation_history(session_id, limit=10)
            formatted_history = memory_service.format_history_for_llm(conversation_history[:-1])
            
            messages = self.build_prompt(question, context_chunks, formatted_history)
            
            answer = self.generate_answer(messages)
            
            memory_service.save_message(session_id, MessageRole.ASSISTANT, answer)
            
            sources = self.format_sources(context_chunks)
            
            result = {
                "answer": answer,
                "sources": sources,
                "session_id": session_id
            }
            
            logger.info(f"RAG pipeline completed for session {session_id}")
            return result
            
        except LLMException:
            raise
        except Exception as e:
            logger.error(f"RAG pipeline failed: {str(e)}")
            raise LLMException(f"RAG pipeline error: {str(e)}")
    
    def format_sources(self, chunks: List[Dict]) -> List[Dict]:
        """
        Format source chunks for response.
        
        Args:
            chunks: List of context chunks
        
        Returns:
            Formatted source information
        """
        sources = []
        
        for chunk in chunks:
            source = {
                "text": chunk.get("chunk_text", ""),
                "document_id": chunk.get("document_id", ""),
                "document_name": chunk.get("document_name", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "similarity_score": chunk.get("score", 0.0)
            }
            sources.append(source)
        
        return sources
    
    def validate_answer_quality(self, answer: str, context_chunks: List[Dict]) -> bool:
        """
        Basic validation of answer quality.
        
        Args:
            answer: Generated answer
            context_chunks: Context chunks used
        
        Returns:
            True if answer seems valid
        """
        if not answer or len(answer.strip()) < 10:
            return False
        
        fallback_phrases = [
            "i don't know",
            "i cannot answer",
            "no information",
            "not provided",
            "unable to answer"
        ]
        
        answer_lower = answer.lower()
        if any(phrase in answer_lower for phrase in fallback_phrases):
            if not context_chunks:
                return True
            return False
        
        return True