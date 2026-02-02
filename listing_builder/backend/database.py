# /Users/shawn/Projects/ListingBuilderPro/listing_builder/backend/database.py
# Purpose: Database connection and session management (Supabase PostgreSQL)
# NOT for: Models or business logic

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from supabase import create_client, Client
from config import settings
from typing import Generator
import structlog

logger = structlog.get_logger()

# SQLAlchemy setup for direct PostgreSQL access
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()


# Supabase client for auth and realtime features
# Lazy init — gotrue has a 'proxy' kwarg incompatibility with current httpx version
_supabase: Client = None


def get_supabase() -> Client:
    """Lazy-init Supabase client. Returns None if client can't be created."""
    global _supabase
    if _supabase is None:
        try:
            _supabase = create_client(
                settings.supabase_url,
                settings.supabase_service_key,
            )
        except TypeError as e:
            logger.warning("supabase_client_init_failed", error=str(e))
    return _supabase


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    Yields a SQLAlchemy session and closes it after request.

    Usage in routes:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Product).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("database_error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    Run this once during deployment or in main.py startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        raise


def check_db_connection() -> bool:
    """
    Health check for database connection.
    Returns True if database is accessible.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))
        return False
