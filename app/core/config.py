from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List,Optional
import os


class Settings(BaseSettings):
    """Application configuration settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Groq API Configuration
    groq_api_key: str
    groq_model: str = "llama-3.1-8b-instant"
    
    # Embedding Model Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384
    
    # Qdrant Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "documents"
    qdrant_api_key: Optional[str] = None
    
    # SQLite Database
    sqlite_url: str = "sqlite:///./storage/sqlite/app.db"
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    default_chunking_strategy: str = "recursive"
    
    # File Upload Settings
    max_file_size_mb: int = 10
    allowed_file_types: str = "pdf,txt"
    upload_dir: str = "./storage/uploads"
    
    # RAG Settings
    top_k_results: int = 5
    max_history_messages: int = 10
    
    # Logging
    log_level: str = "INFO"
    log_dir: str = "./logs"
    
    # API Settings
    api_version: str = "v1"
    api_title: str = "RAG Backend API"
    api_description: str = "Document Q&A and Booking System with RAG"
    cors_origins: str = "*"
    
    # Application Settings
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Return allowed file types as a list."""
        return [ext.strip() for ext in self.allowed_file_types.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Return max file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS origins as a list."""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    def validate_config(self) -> None:
        """Validate that all required configuration is present."""
        if not self.groq_api_key or self.groq_api_key == "your_groq_api_key_here":
            raise ValueError("GROQ_API_KEY must be set in .env file")
        
        # Create necessary directories
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        os.makedirs("./storage/sqlite", exist_ok=True)


# Singleton instance
_settings = None


def get_settings() -> Settings:
    """Get or create settings singleton instance."""
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
            _settings.validate_config()
        except Exception as e:
            raise RuntimeError(f"Failed to load configuration: {str(e)}")
    return _settings