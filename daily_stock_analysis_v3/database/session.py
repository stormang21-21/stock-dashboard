"""
Database Session Manager

Enhanced session management with transaction support.
"""

from typing import Optional, Callable, Any
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ..logging import get_logger
from ..exceptions import BaseException

logger = get_logger(__name__)


class DatabaseSession:
    """
    Database session wrapper with enhanced functionality.
    
    Provides:
    - Automatic transaction management
    - Error handling
    - Logging
    - Query helpers
    """
    
    def __init__(self, session: Session):
        """
        Initialize session wrapper.
        
        Args:
            session: SQLAlchemy session
        """
        self.session = session
        self._transaction_active = False
    
    def __enter__(self) -> "DatabaseSession":
        """Context manager entry"""
        self._transaction_active = True
        logger.debug("Database transaction started")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit"""
        if exc_type is not None:
            # Exception occurred, rollback
            self.rollback()
            logger.error(f"Transaction rolled back: {exc_val}")
        else:
            # No exception, commit
            self.commit()
            logger.debug("Transaction committed")
        
        self._transaction_active = False
        self.session.close()
    
    def commit(self) -> None:
        """Commit transaction"""
        try:
            self.session.commit()
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Commit failed: {e}")
            raise
    
    def rollback(self) -> None:
        """Rollback transaction"""
        self.session.rollback()
    
    def close(self) -> None:
        """Close session"""
        self.session.close()
    
    def add(self, obj: Any) -> "DatabaseSession":
        """
        Add object to session.
        
        Args:
            obj: Model instance to add
            
        Returns:
            Self for chaining
        """
        self.session.add(obj)
        return self
    
    def add_all(self, objs: list[Any]) -> "DatabaseSession":
        """
        Add multiple objects to session.
        
        Args:
            objs: List of model instances
            
        Returns:
            Self for chaining
        """
        self.session.add_all(objs)
        return self
    
    def delete(self, obj: Any) -> "DatabaseSession":
        """
        Delete object from session.
        
        Args:
            obj: Model instance to delete
            
        Returns:
            Self for chaining
        """
        self.session.delete(obj)
        return self
    
    def query(self, *entities):
        """
        Create query.
        
        Args:
            *entities: Entities to query
            
        Returns:
            SQLAlchemy query
        """
        return self.session.query(*entities)
    
    def execute(self, statement):
        """
        Execute SQL statement.
        
        Args:
            statement: SQL statement
            
        Returns:
            Result
        """
        return self.session.execute(statement)
    
    def refresh(self, obj: Any) -> "DatabaseSession":
        """
        Refresh object from database.
        
        Args:
            obj: Model instance to refresh
            
        Returns:
            Self for chaining
        """
        self.session.refresh(obj)
        return self
    
    def flush(self) -> None:
        """Flush pending changes to database"""
        self.session.flush()


class SessionManager:
    """
    Manages database sessions lifecycle.
    
    Provides dependency injection for FastAPI routes.
    """
    
    def __init__(self, session_factory: Callable[[], Session]):
        """
        Initialize session manager.
        
        Args:
            session_factory: Factory function to create sessions
        """
        self.session_factory = session_factory
    
    @contextmanager
    def session(self) -> DatabaseSession:
        """
        Get managed session.
        
        Yields:
            DatabaseSession wrapper
            
        Example:
            ```python
            with session_manager.session() as db:
                user = db.query(User).first()
            ```
        """
        session = self.session_factory()
        db_session = DatabaseSession(session)
        
        try:
            yield db_session
        finally:
            db_session.close()
    
    def with_transaction(self, func: Callable) -> Callable:
        """
        Decorator for automatic transaction management.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
            
        Example:
            ```python
            @session_manager.with_transaction
            def create_user(db: DatabaseSession, name: str):
                user = User(name=name)
                db.add(user)
            ```
        """
        def wrapper(*args, **kwargs):
            with self.session() as db:
                return func(db, *args, **kwargs)
        
        return wrapper


# Global session manager instance
session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get or create session manager.
    
    Returns:
        SessionManager instance
    """
    global session_manager
    
    if session_manager is None:
        from .connection import get_session_factory
        session_manager = SessionManager(lambda: get_session_factory()())
    
    return session_manager
