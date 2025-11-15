import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import get_settings
from app.core.exceptions import base_exception_handler, generic_exception_handler, BaseRAGException
from app.database.connection import init_db, close_db
from app.utils.logger import setup_application_loggers
from app.api.v1 import ingestion, conversation, booking
from app.models.schemas import HealthResponse
from datetime import datetime

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    settings = get_settings()
    
    setup_application_loggers(settings.log_dir, settings.log_level)
    logger.info("Application starting up...")
    
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
    
    logger.info("Application startup complete")
    
    yield
    
    logger.info("Application shutting down...")
    close_db()
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_exception_handler(BaseRAGException, base_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
    
    app.include_router(
        ingestion.router,
        prefix=f"/api/{settings.api_version}",
        tags=["Document Ingestion"]
    )
    
    app.include_router(
        conversation.router,
        prefix=f"/api/{settings.api_version}",
        tags=["Conversation"]
    )
    
    app.include_router(
        booking.router,
        prefix=f"/api/{settings.api_version}",
        tags=["Booking"]
    )
    
    @app.get("/", response_model=HealthResponse)
    async def root():
        """Root endpoint - health check."""
        return HealthResponse(
            status="healthy",
            message="RAG Backend API is running",
            timestamp=datetime.utcnow()
        )
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            message="All systems operational",
            timestamp=datetime.utcnow()
        )
    @app.get("/frontend")
    async def serve_frontend():
        """Serve the frontend HTML."""
        frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend.html")
        return FileResponse(frontend_path)
    
    return app


app = create_app()