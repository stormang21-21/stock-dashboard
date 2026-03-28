"""
Database Models

Base model classes and mixins.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, String, Text
from sqlalchemy.orm import declarative_base, declared_attr

Base = declarative_base()


class TimestampMixin:
    """
    Mixin for created/updated timestamps.
    
    Adds:
    - created_at: When record was created
    - updated_at: When record was last updated
    """
    
    @declared_attr
    def created_at(cls) -> Column:
        """Record creation timestamp"""
        return Column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
            index=True,
        )
    
    @declared_attr
    def updated_at(cls) -> Column:
        """Record update timestamp"""
        return Column(
            DateTime,
            default=datetime.utcnow,
            onupdate=datetime.utcnow,
            nullable=False,
        )
    
    def to_dict(self) -> dict:
        """
        Convert model to dictionary.
        
        Returns:
            Dictionary representation
        """
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', 'N/A')})>"


class BaseModel(Base, TimestampMixin):
    """
    Base model with common functionality.
    
    Provides:
    - Auto-incrementing ID
    - Timestamps
    - to_dict() method
    - __repr__() method
    """
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    def to_dict(self, exclude: list[str] | None = None) -> dict:
        """
        Convert model to dictionary.
        
        Args:
            exclude: List of fields to exclude
            
        Returns:
            Dictionary representation
        """
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                
                # Convert datetime to ISO format
                if isinstance(value, datetime):
                    value = value.isoformat()
                
                result[column.name] = value
        
        return result
    
    def update(self, **kwargs) -> "BaseModel":
        """
        Update model attributes.
        
        Args:
            **kwargs: Attributes to update
            
        Returns:
            Self for chaining
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        return self
