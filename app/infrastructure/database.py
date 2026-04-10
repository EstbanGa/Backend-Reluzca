"""
Database configuration and session management.
Uses SQLAlchemy 2.0 with synchronous support.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import logging
from fastapi import HTTPException

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create engine (usando URL síncrona para psycopg2)
engine = create_engine(
    settings.DATABASE_URL_SYNC,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

# Create session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except HTTPException:
        # Don't rollback or log HTTPExceptions - they're intentional
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database.
    Creates all tables if they don't exist.
    
    Note: In production, use Alembic migrations instead.
    """
    # Import all models here to ensure they are registered
    from app.models import usuario, reserva, plan, ubicacion
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def close_db() -> None:
    """Close database connections."""
    engine.dispose()
    logger.info("Database connections closed")


# Database utilities
def check_db_connection() -> bool:
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False
