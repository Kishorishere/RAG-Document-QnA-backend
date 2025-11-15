from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue, MatchAny
from typing import List, Dict, Optional
import uuid
import logging

from app.core.exceptions import VectorStoreException

logger = logging.getLogger(__name__)


class QdrantVectorStore:
    """Service for managing Qdrant vector store operations."""
    
    def __init__(self, qdrant_client: QdrantClient, collection_name: str, vector_size: int = 384):
        """
        Initialize Qdrant vector store.
        
        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of the collection
            vector_size: Dimension of embedding vectors
        """
        self.client = qdrant_client
        self.collection_name = collection_name
        self.vector_size = vector_size
        
        try:
            self._ensure_collection_exists()
            logger.info(f"Vector store initialized with collection: {collection_name}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise VectorStoreException("initialization", str(e))
    
    def _ensure_collection_exists(self):
        """Create collection if it doesn't exist."""
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name not in collection_names:
                self.create_collection()
                logger.info(f"Collection '{self.collection_name}' created")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            logger.error(f"Failed to check collection existence: {str(e)}")
            raise VectorStoreException("check_collection", str(e))
    
    def create_collection(self):
        """Create a new Qdrant collection."""
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {str(e)}")
            raise VectorStoreException("create_collection", str(e))
    
    def add_documents(
        self, 
        document_id: str, 
        chunks: List[str], 
        embeddings: List[List[float]], 
        metadata: Optional[Dict] = None
    ) -> int:
        """
        Add document chunks with embeddings to vector store.
        
        Args:
            document_id: Unique document identifier
            chunks: List of text chunks
            embeddings: List of embedding vectors
            metadata: Additional metadata
        
        Returns:
            Number of vectors added
        """
        try:
            if len(chunks) != len(embeddings):
                raise VectorStoreException(
                    "add_documents", 
                    f"Chunks count ({len(chunks)}) doesn't match embeddings count ({len(embeddings)})"
                )
            
            points = []
            for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point_id = str(uuid.uuid4())
                
                payload = {
                    "document_id": document_id,
                    "chunk_index": idx,
                    "chunk_text": chunk,
                    "document_name": metadata.get("filename", "") if metadata else ""
                }
                
                if metadata:
                    payload.update(metadata)
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            logger.info(f"Added {len(points)} vectors for document {document_id}")
            return len(points)
            
        except VectorStoreException:
            raise
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise VectorStoreException("add_documents", str(e))
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        limit: int = 5, 
        document_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search for similar vectors in the store.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results
            document_ids: Optional list of document IDs to filter by
        
        Returns:
            List of search results with scores
        """
        try:
            query_filter = None
            
            if document_ids:
                from qdrant_client.models import MatchAny
                
                query_filter = Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchAny(any=document_ids) 
                        )
                    ]
                )
            
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter
            )
            
            results = []
            for hit in search_result:
                result = {
                    "id": hit.id,
                    "score": hit.score,
                    "document_id": hit.payload.get("document_id"),
                    "chunk_index": hit.payload.get("chunk_index"),
                    "chunk_text": hit.payload.get("chunk_text"),
                    "document_name": hit.payload.get("document_name", ""),
                    "payload": hit.payload
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} similar vectors")
            return results
            
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {str(e)}")
            raise VectorStoreException("similarity_search", str(e))
    
    def delete_by_document_id(self, document_id: str) -> int:
        """
        Delete all vectors associated with a document.
        
        Args:
            document_id: Document identifier
        
        Returns:
            Number of vectors deleted
        """
        try:
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id)
                    )
                ]
            )
            
            points = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=filter_condition,
                limit=10000
            )[0]
            
            point_ids = [point.id for point in points]
            
            if point_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=point_ids
                )
            
            logger.info(f"Deleted {len(point_ids)} vectors for document {document_id}")
            return len(point_ids)
            
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise VectorStoreException("delete_vectors", str(e))
    
    def get_collection_info(self) -> Dict:
        """
        Get information about the collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            info = self.client.get_collection(self.collection_name)
            
            return {
                "collection_name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {str(e)}")
            raise VectorStoreException("get_collection_info", str(e))
    
    def check_collection_exists(self) -> bool:
        """
        Check if collection exists.
        
        Returns:
            True if collection exists
        """
        try:
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            return self.collection_name in collection_names
            
        except Exception as e:
            logger.error(f"Failed to check collection: {str(e)}")
            return False
    
    def delete_collection(self):
        """Delete the entire collection."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' deleted")
            
        except Exception as e:
            logger.error(f"Failed to delete collection: {str(e)}")
            raise VectorStoreException("delete_collection", str(e))