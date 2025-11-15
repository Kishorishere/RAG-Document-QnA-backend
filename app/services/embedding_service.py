from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import logging

from app.core.exceptions import EmbeddingGenerationException

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating embeddings using sentence-transformers."""
    
    _instance = None
    _model = None
    
    def __new__(cls, model_name: str = "all-MiniLM-L6-v2"):
        """Singleton pattern to ensure only one model instance."""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize(model_name)
        return cls._instance
    
    def _initialize(self, model_name: str):
        """
        Initialize the embedding model.
        
        Args:
            model_name: Name of the sentence-transformers model
        """
        try:
            logger.info(f"Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            self._model_name = model_name
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"Embedding model loaded successfully. Dimension: {self._embedding_dim}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise EmbeddingGenerationException(f"Model initialization failed: {str(e)}")
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            Numpy array of embedding vector
        """
        try:
            if not text or not text.strip():
                raise EmbeddingGenerationException("Cannot generate embedding for empty text")
            
            embedding = self._model.encode(text, convert_to_numpy=True)
            
            logger.debug(f"Generated embedding with shape: {embedding.shape}")
            return embedding
            
        except EmbeddingGenerationException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise EmbeddingGenerationException(str(e))
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
        
        Returns:
            List of embedding vectors
        """
        try:
            if not texts:
                raise EmbeddingGenerationException("Cannot generate embeddings for empty list")
            
            valid_texts = [text for text in texts if text and text.strip()]
            
            if not valid_texts:
                raise EmbeddingGenerationException("All texts are empty")
            
            embeddings = self._model.encode(
                valid_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            logger.info(f"Generated {len(embeddings)} embeddings in batch")
            return embeddings.tolist()
            
        except EmbeddingGenerationException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            raise EmbeddingGenerationException(str(e))
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embedding vectors.
        
        Returns:
            Embedding dimension
        """
        return self._embedding_dim
    
    def encode_query(self, query: str) -> np.ndarray:
        """
        Encode a query text optimized for retrieval.
        
        Args:
            query: Query text
        
        Returns:
            Normalized embedding vector
        """
        try:
            embedding = self.generate_embedding(query)
            
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            
            return embedding
            
        except Exception as e:
            logger.error(f"Failed to encode query: {str(e)}")
            raise EmbeddingGenerationException(str(e))
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score (0 to 1)
        """
        try:
            embedding1 = np.array(embedding1)
            embedding2 = np.array(embedding2)
            
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Failed to compute similarity: {str(e)}")
            return 0.0
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self._model_name,
            "embedding_dimension": self._embedding_dim,
            "max_sequence_length": self._model.max_seq_length
        }