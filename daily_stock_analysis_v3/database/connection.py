"""
Database Connection

Engine creation, session factory, and connection management.
"""

from typing import Generator, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool, QueuePool

from config import settings, DatabaseConfig
from ..logging import get_logger

logger = get_logger(__name__)


# Global engine and session factory
_engine: Optional[any] = None
_SessionLocal: Optional[scoped_session] = None


def get_engine(config: Optional[DatabaseConfig] = None) -> any:
    """
    Get or create database engine.
    
    Args:
        config: Database configuration (uses settings if not provided)
        
    Returns:
        SQLAlchemy engine
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    if config is None:
        config = settings.database
    
    logger.info(f"Creating database engine: {config.url}")
    
    # Determine pool class based on database type
    if config.url.startswith("sqlite"):
        # SQLite doesn't work well with connection pooling
        poolclass = StaticPool
        connect_args = {"check_same_thread": False}
    else:
        # PostgreSQL and others use QueuePool
        poolclass = QueuePool
        connect_args = {}
    
    # Create engine
    _engine = create_engine(
        config.url,
        echo=config.echo,
        poolclass=poolclass,
        pool_size=config.pool_size if poolclass == QueuePool else None,
        max_overflow=config.max_overflow if poolclass == QueuePool else None,
        connect_args=connect_args,
        future=True,
    )
    
    # Register event listeners
    @_event.listens_for(_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """Set SQLite pragmas for better performance"""
        if config.url.startswith("sqlite"):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
    
    logger.info("Database engine created successfully")
    return _engine


def get_session_factory() -> scoped_session:
    """
    Get or create session factory.
    
    Returns:
        Scoped session factory
    """
    global _SessionLocal
    
    if _SessionLocal is not None:
        return _SessionLocal
    
    engine = get_engine()
    
    _SessionLocal = scoped_session(
        sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine,
            class_=Session,
            expire_on_commit=False,
        )
    )
    
    logger.debug("Session factory created")
    return _SessionLocal


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        SQLAlchemy session
        
    Yields:
        Session for use in context manager
        
    Example:
        ```python
        with get_session() as session:
            # use session
        ```
    """
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        yield session
    finally:
        session.close()


# Context manager for database sessions
get_db = contextmanager(get_session)


def init_db() -> None:
    """
    Initialize database (create tables).
    
    Call this on application startup.
    """
    from .models import Base
    
    engine = get_engine()
    
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialization complete")


def close_db() -> None:
    """
    Close database connections.
    
    Call this on application shutdown.
    """
    global _engine, _SessionLocal
    
    logger.info("Closing database connections...")
    
    if _SessionLocal is not None:
        _SessionLocal.remove()
        _SessionLocal = None
    
    if _engine is not None:
        _engine.dispose()
        _engine = None
    
    logger.info("Database connections closed")


@contextmanager
def transaction(session: Session):
    """
    Context manager for database transactions.
    
    Automatically commits on success, rolls back on failure.
    
    Args:
        session: Database session
        
    Example:
        ```python
        with get_session() as session:
            with transaction(session):
                # do database operations
        ```
    """
    try:
        yield session
        session.commit()
        logger.debug("Transaction committed")
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction rolled back: {e}")
        raise
    finally:
        session.close()
