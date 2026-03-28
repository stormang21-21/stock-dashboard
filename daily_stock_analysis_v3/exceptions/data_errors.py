"""
Data Layer Exceptions

Exceptions specific to data fetching and processing.
"""

from typing import Optional, List, Any
from .base import BaseException


class DataError(BaseException):
    """
    Base class for data-related errors.
    """
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if source:
            details['source'] = source
        
        super().__init__(
            message=message,
            code="DATA_ERROR",
            details=details,
            **kwargs,
        )


class DataFetchError(DataError):
    """
    Error fetching data from external sources.
    
    Raised when:
    - API request fails
    - Network error
    - Timeout
    """
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if status_code:
            details['status_code'] = status_code
        if url:
            details['url'] = url
        
        super().__init__(
            message=message,
            source=source,
            code="DATA_FETCH_ERROR",
            details=details,
            **kwargs,
        )


class DataValidationError(DataError):
    """
    Data validation failed.
    
    Raised when:
    - Data doesn't match expected schema
    - Missing required fields
    - Invalid data types
    """
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if field:
            details['field'] = field
        if value is not None:
            details['value'] = str(value)
        
        super().__init__(
            message=message,
            source=source,
            code="DATA_VALIDATION_ERROR",
            details=details,
            **kwargs,
        )


class DataSourceError(DataError):
    """
    Data source configuration or availability error.
    
    Raised when:
    - Data source not configured
    - Data source unavailable
    - All data sources exhausted
    """
    
    def __init__(
        self,
        message: str,
        source: Optional[str] = None,
        attempted_sources: Optional[List[str]] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if attempted_sources:
            details['attempted_sources'] = attempted_sources
        
        super().__init__(
            message=message,
            source=source,
            code="DATA_SOURCE_ERROR",
            details=details,
            **kwargs,
        )


class RateLimitError(DataFetchError):
    """
    Rate limit exceeded.
    
    Raised when:
    - API rate limit hit
    - Quota exceeded
    - Too many requests
    """
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        source: Optional[str] = None,
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset_at: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if retry_after:
            details['retry_after_seconds'] = retry_after
        if limit:
            details['limit'] = limit
        if remaining is not None:
            details['remaining'] = remaining
        if reset_at:
            details['reset_at'] = reset_at
        
        super().__init__(
            message=message,
            source=source,
            code="RATE_LIMIT_ERROR",
            details=details,
            **kwargs,
        )
