"""
API Exceptions

Exceptions specific to API operations.
"""

from typing import Optional, Dict, Any, List
from .base import BaseException


class APIError(BaseException):
    """
    Base class for API-related errors.
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        endpoint: Optional[str] = None,
        method: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if status_code:
            details['status_code'] = status_code
        if endpoint:
            details['endpoint'] = endpoint
        if method:
            details['method'] = method
        
        super().__init__(
            message=message,
            code="API_ERROR",
            details=details,
            **kwargs,
        )
        self.status_code = status_code


class BadRequestError(APIError):
    """
    HTTP 400 Bad Request.
    
    Raised when:
    - Invalid request parameters
    - Missing required fields
    - Malformed request body
    """
    
    def __init__(
        self,
        message: str = "Bad request",
        endpoint: Optional[str] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if validation_errors:
            details['validation_errors'] = validation_errors
        
        super().__init__(
            message=message,
            status_code=400,
            endpoint=endpoint,
            code="BAD_REQUEST",
            details=details,
            **kwargs,
        )


class NotFoundError(APIError):
    """
    HTTP 404 Not Found.
    
    Raised when:
    - Resource not found
    - Endpoint doesn't exist
    """
    
    def __init__(
        self,
        message: str = "Resource not found",
        endpoint: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        super().__init__(
            message=message,
            status_code=404,
            endpoint=endpoint,
            code="NOT_FOUND",
            details=details,
            **kwargs,
        )


class AuthenticationError(APIError):
    """
    HTTP 401 Unauthorized.
    """
    
    def __init__(
        self,
        message: str = "Authentication required",
        **kwargs,
    ):
        super().__init__(
            message=message,
            status_code=401,
            code="UNAUTHORIZED",
            **kwargs,
        )


class AuthorizationError(APIError):
    """
    HTTP 403 Forbidden.
    """
    
    def __init__(
        self,
        message: str = "Access denied",
        required_permission: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if required_permission:
            details['required_permission'] = required_permission
        
        super().__init__(
            message=message,
            status_code=403,
            code="FORBIDDEN",
            details=details,
            **kwargs,
        )


class InternalServerError(APIError):
    """
    HTTP 500 Internal Server Error.
    
    Raised when:
    - Unexpected server error
    - Unhandled exception
    """
    
    def __init__(
        self,
        message: str = "Internal server error",
        endpoint: Optional[str] = None,
        error_id: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if error_id:
            details['error_id'] = error_id
        
        super().__init__(
            message=message,
            status_code=500,
            endpoint=endpoint,
            code="INTERNAL_SERVER_ERROR",
            details=details,
            **kwargs,
        )


class ServiceUnavailableError(APIError):
    """
    HTTP 503 Service Unavailable.
    
    Raised when:
    - Service temporarily unavailable
    - Maintenance mode
    - Dependency service down
    """
    
    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: Optional[int] = None,
        reason: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if retry_after:
            details['retry_after_seconds'] = retry_after
        if reason:
            details['reason'] = reason
        
        super().__init__(
            message=message,
            status_code=503,
            code="SERVICE_UNAVAILABLE",
            details=details,
            **kwargs,
        )
