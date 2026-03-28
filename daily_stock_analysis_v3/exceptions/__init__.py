"""
Exception Hierarchy

Custom exceptions for better error handling and debugging.
"""

from .base import (
    BaseException,
    ConfigurationError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
)
from .data_errors import (
    DataError,
    DataFetchError,
    DataValidationError,
    DataSourceError,
    RateLimitError,
)
from .ai_errors import (
    AIError,
    LLMError,
    PromptError,
    AnalysisError,
    StrategyError,
)
from .api_errors import (
    APIError,
    BadRequestError,
    InternalServerError,
    ServiceUnavailableError,
)

__all__ = [
    # Base
    "BaseException",
    "ConfigurationError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "AuthorizationError",
    
    # Data
    "DataError",
    "DataFetchError",
    "DataValidationError",
    "DataSourceError",
    "RateLimitError",
    
    # AI
    "AIError",
    "LLMError",
    "PromptError",
    "AnalysisError",
    "StrategyError",
    
    # API
    "APIError",
    "BadRequestError",
    "InternalServerError",
    "ServiceUnavailableError",
]
