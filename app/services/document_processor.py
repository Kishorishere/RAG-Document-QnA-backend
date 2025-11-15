import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import logging

from app.core.exceptions import TextExtractionException, ChunkingFailedException
from app.utils.text_utils import clean_text

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Service for processing documents and chunking text."""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
        
        Returns:
            Extracted text
        """
        try:
            text_content = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_content.append(page_text)
                        logger.debug(f"Extracted text from page {page_num}")
            
            if not text_content:
                raise TextExtractionException(file_path, "No text content found in PDF")
            
            full_text = "\n\n".join(text_content)
            cleaned_text = clean_text(full_text)
            
            logger.info(f"Successfully extracted {len(cleaned_text)} characters from PDF")
            return cleaned_text
            
        except pdfplumber.PDFSyntaxError as e:
            logger.error(f"PDF syntax error: {str(e)}")
            raise TextExtractionException(file_path, f"Invalid PDF format: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {str(e)}")
            raise TextExtractionException(file_path, str(e))
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """
        Extract text from TXT file.
        
        Args:
            file_path: Path to TXT file
        
        Returns:
            Extracted text
        """
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        text = f.read()
                    
                    cleaned_text = clean_text(text)
                    logger.info(f"Successfully read TXT file with {encoding} encoding")
                    return cleaned_text
                    
                except UnicodeDecodeError:
                    continue
            
            raise TextExtractionException(file_path, "Unable to decode file with supported encodings")
            
        except FileNotFoundError:
            raise TextExtractionException(file_path, "File not found")
        except Exception as e:
            logger.error(f"Failed to extract text from TXT: {str(e)}")
            raise TextExtractionException(file_path, str(e))
    
    def chunk_text_fixed(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Chunk text using fixed size strategy.
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (uses instance default if None)
            overlap: Overlap between chunks (uses instance default if None)
        
        Returns:
            List of text chunks
        """
        try:
            chunk_size = chunk_size or self.chunk_size
            overlap = overlap or self.chunk_overlap
            
            if len(text) <= chunk_size:
                return [text]
            
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + chunk_size
                chunk = text[start:end]
                chunks.append(chunk.strip())
                start = end - overlap
            
            logger.info(f"Created {len(chunks)} chunks using fixed strategy")
            return chunks
            
        except Exception as e:
            logger.error(f"Fixed chunking failed: {str(e)}")
            raise ChunkingFailedException(str(e))
    
    def chunk_text_recursive(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Chunk text using recursive strategy (semantic splitting).
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (uses instance default if None)
            overlap: Overlap between chunks (uses instance default if None)
        
        Returns:
            List of text chunks
        """
        try:
            chunk_size = chunk_size or self.chunk_size
            overlap = overlap or self.chunk_overlap
            
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            chunks = text_splitter.split_text(text)
            
            logger.info(f"Created {len(chunks)} chunks using recursive strategy")
            return chunks
            
        except Exception as e:
            logger.error(f"Recursive chunking failed: {str(e)}")
            raise ChunkingFailedException(str(e))
    
    def process_document(self, file_path: str, strategy: str = "recursive") -> Dict:
        """
        Main orchestration function to process document.
        
        Args:
            file_path: Path to document file
            strategy: Chunking strategy ('fixed' or 'recursive')
        
        Returns:
            Dictionary with chunks and metadata
        """
        try:
            file_extension = file_path.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                text = self.extract_text_from_pdf(file_path)
            elif file_extension == 'txt':
                text = self.extract_text_from_txt(file_path)
            else:
                raise TextExtractionException(file_path, f"Unsupported file type: {file_extension}")
            
            if strategy == "fixed":
                chunks = self.chunk_text_fixed(text)
            elif strategy == "recursive":
                chunks = self.chunk_text_recursive(text)
            else:
                raise ChunkingFailedException(f"Unknown chunking strategy: {strategy}")
            
            result = {
                "chunks": chunks,
                "total_chunks": len(chunks),
                "total_characters": len(text),
                "strategy_used": strategy
            }
            
            logger.info(f"Document processed successfully: {result['total_chunks']} chunks created")
            return result
            
        except (TextExtractionException, ChunkingFailedException):
            raise
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise ChunkingFailedException(str(e))