"""
Base Exceptions

Foundation exception classes for the application.
"""

from typing import Optional, Dict, Any, List


class BaseException(Exception):
    """
    Base exception class for all custom exceptions.
    
    Attributes:
        message: Error message
        code: Error code for programmatic handling
        details: Additional error details
        context: Context information for debugging
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.context = context or {}
        
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details,
            "context": self.context,
        }
    
    def __str__(self) -> str:
        if self.details:
            return f"{self.message} ({self.details})"
        return self.message
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, code={self.code!r})"


class ConfigurationError(BaseException):
    """
    Configuration-related errors.
    
    Raised when:
    - Invalid configuration values
    - Missing required configuration
    - Configuration validation fails
    """
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            details=details,
            **kwargs,
        )


class ValidationError(BaseException):
    """
    Data validation errors.
    
    Raised when:
    - Input validation fails
    - Data doesn't match expected schema
    - Business rule validation fails
    """
    
    def __init__(
        self,
        message: str,
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
            code="VALIDATION_ERROR",
            details=details,
            **kwargs,
        )


class NotFoundError(BaseException):
    """
    Resource not found errors.
    
    Raised when:
    - Requested resource doesn't exist
    - Database record not found
    - File or path doesn't exist
    """
    
    def __init__(
        self,
        message: str,
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
            code="NOT_FOUND",
            details=details,
            **kwargs,
        )


class AuthenticationError(BaseException):
    """
    Authentication failures.
    
    Raised when:
    - Invalid credentials
    - Missing authentication token
    - Token expired
    """
    
    def __init__(
        self,
        message: str = "Authentication failed",
        **kwargs,
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            **kwargs,
        )


class AuthorizationError(BaseException):
    """
    Authorization failures.
    
    Raised when:
    - Insufficient permissions
    - Access denied to resource
    - Role-based access check fails
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
            code="AUTHORIZATION_ERROR",
            details=details,
            **kwargs,
        )
