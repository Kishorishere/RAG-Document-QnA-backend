from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from app.database.models import Base
from app.core.config import get_settings
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine."""
    global _engine
    if _engine is None:
        try:
            settings = get_settings()
            
            # SQLite specific configuration
            connect_args = {"check_same_thread": False}
            
            _engine = create_engine(
                settings.sqlite_url,
                connect_args=connect_args,
                poolclass=StaticPool,
                echo=settings.debug
            )
            
            logger.info(f"Database engine created: {settings.sqlite_url}")
        except Exception as e:
            logger.error(f"Failed to create database engine: {str(e)}")
            raise DatabaseException("engine_creation", str(e))
    
    return _engine


def get_session_local():
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        logger.info("Session factory created")
    
    return _SessionLocal


def init_db():
    """Initialize database by creating all tables."""
    try:
        engine = get_engine()
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise DatabaseException("initialization", str(e))


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that yields database session.
    Automatically closes session after use.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()


def close_db():
    """Close database connections."""
    global _engine
    if _engine is not None:
        try:
            _engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {str(e)}")