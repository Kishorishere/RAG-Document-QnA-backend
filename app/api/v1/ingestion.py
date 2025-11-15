from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging

from app.core.config import get_settings
from app.core.dependencies import (
    get_db, get_document_processor, get_embedding_service, 
    get_vector_store, verify_document_exists
)
from app.database import crud
from app.models.schemas import (
    DocumentUploadResponse, DocumentMetadata, DocumentListResponse,
    DocumentChunksResponse, ChunkResponse, SuccessResponse
)
from app.models.enums import ChunkingStrategy
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import QdrantVectorStore
from app.utils.file_utils import (
    validate_file_type, validate_file_size, save_uploaded_file, 
    delete_file, get_file_size, get_original_filename
)
from app.core.exceptions import InvalidFileTypeException, FileTooLargeException

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    chunking_strategy: str = Form(default="recursive"),
    db: Session = Depends(get_db),
    document_processor: DocumentProcessor = Depends(get_document_processor),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    vector_store: QdrantVectorStore = Depends(get_vector_store)
):
    """
    Upload and process a document (PDF or TXT).
    
    - **file**: Document file to upload
    - **chunking_strategy**: 'fixed' or 'recursive' (default: recursive)
    """
    settings = get_settings()
    
    try:
        original_filename = get_original_filename(file)
        
        validate_file_type(original_filename, settings.allowed_file_types_list)
        
        file_content = await file.read()
        file_size = len(file_content)
        validate_file_size(file_size, settings.max_file_size_bytes)
        
        await file.seek(0)
        
        file_path = save_uploaded_file(file, settings.upload_dir)
        
        document_id = str(uuid.uuid4())
        
        try:
            processed = document_processor.process_document(file_path, chunking_strategy)
            
            embeddings = embedding_service.generate_embeddings_batch(processed["chunks"])
            
            document_data = {
                "document_id": document_id,
                "filename": original_filename,
                "file_path": file_path,
                "file_size": file_size,
                "chunk_count": processed["total_chunks"],
                "chunking_strategy": chunking_strategy
            }
            document = crud.create_document(db, document_data)
            
            chunks_data = [
                {"chunk_index": idx, "chunk_text": chunk}
                for idx, chunk in enumerate(processed["chunks"])
            ]
            crud.create_chunks(db, document_id, chunks_data)
            
            metadata = {"filename": original_filename}
            vector_store.add_documents(
                document_id=document_id,
                chunks=processed["chunks"],
                embeddings=embeddings,
                metadata=metadata
            )
            
            logger.info(f"Document uploaded successfully: {document_id}")
            
            return DocumentUploadResponse(
                document_id=document_id,
                filename=original_filename,
                chunks_created=processed["total_chunks"],
                strategy_used=chunking_strategy,
                message="Document processed successfully"
            )
            
        except Exception as e:
            delete_file(file_path)
            logger.error(f"Failed to process document: {str(e)}")
            raise
    
    except (InvalidFileTypeException, FileTooLargeException):
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all uploaded documents with pagination.
    
    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    try:
        documents = crud.get_all_documents(db, skip, limit)
        total = crud.get_document_count(db)
        
        document_list = [
            DocumentMetadata(
                document_id=doc.document_id,
                filename=doc.filename,
                file_size=doc.file_size,
                chunk_count=doc.chunk_count,
                chunking_strategy=doc.chunking_strategy,
                upload_timestamp=doc.upload_timestamp
            )
            for doc in documents
        ]
        
        return DocumentListResponse(
            documents=document_list,
            total=total,
            skip=skip,
            limit=limit
        )
    
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise


@router.get("/documents/{document_id}", response_model=DocumentMetadata)
async def get_document(
    document_id: str = Depends(verify_document_exists),
    db: Session = Depends(get_db)
):
    """
    Get specific document metadata by ID.
    
    - **document_id**: Document identifier
    """
    try:
        document = crud.get_document_by_id(db, document_id)
        
        return DocumentMetadata(
            document_id=document.document_id,
            filename=document.filename,
            file_size=document.file_size,
            chunk_count=document.chunk_count,
            chunking_strategy=document.chunking_strategy,
            upload_timestamp=document.upload_timestamp
        )
    
    except Exception as e:
        logger.error(f"Failed to get document: {str(e)}")
        raise


@router.delete("/documents/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: str = Depends(verify_document_exists),
    db: Session = Depends(get_db),
    vector_store: QdrantVectorStore = Depends(get_vector_store)
):
    """
    Delete a document and all its associated data.
    
    - **document_id**: Document identifier
    """
    try:
        document = crud.get_document_by_id(db, document_id)
        file_path = document.file_path
        
        vector_store.delete_by_document_id(document_id)
        
        crud.delete_document(db, document_id)
        
        delete_file(file_path)
        
        logger.info(f"Document deleted: {document_id}")
        
        return SuccessResponse(
            message=f"Document {document_id} deleted successfully",
            success=True
        )
    
    except Exception as e:
        logger.error(f"Failed to delete document: {str(e)}")
        raise


@router.get("/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
async def get_document_chunks(
    document_id: str = Depends(verify_document_exists),
    db: Session = Depends(get_db)
):
    """
    Get all text chunks for a document.
    
    - **document_id**: Document identifier
    """
    try:
        document = crud.get_document_by_id(db, document_id)
        chunks = crud.get_chunks_by_document(db, document_id)
        
        chunk_list = [
            ChunkResponse(
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                created_at=chunk.created_at
            )
            for chunk in chunks
        ]
        
        return DocumentChunksResponse(
            document_id=document_id,
            filename=document.filename,
            chunks=chunk_list,
            total_chunks=len(chunk_list)
        )
    
    except Exception as e:
        logger.error(f"Failed to get document chunks: {str(e)}")
        raise