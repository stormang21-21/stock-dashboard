"""
AI/LLM Exceptions

Exceptions specific to AI analysis and LLM operations.
"""

from typing import Optional, Dict, Any, List
from .base import BaseException


class AIError(BaseException):
    """
    Base class for AI-related errors.
    """
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if model:
            details['model'] = model
        if provider:
            details['provider'] = provider
        
        super().__init__(
            message=message,
            code="AI_ERROR",
            details=details,
            **kwargs,
        )


class LLMError(AIError):
    """
    LLM API errors.
    
    Raised when:
    - LLM API call fails
    - Invalid response from LLM
    - Token limit exceeded
    """
    
    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        error_type: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if status_code:
            details['status_code'] = status_code
        if error_type:
            details['error_type'] = error_type
        
        super().__init__(
            message=message,
            model=model,
            provider=provider,
            code="LLM_ERROR",
            details=details,
            **kwargs,
        )


class PromptError(AIError):
    """
    Prompt-related errors.
    
    Raised when:
    - Prompt template not found
    - Prompt rendering fails
    - Invalid prompt variables
    """
    
    def __init__(
        self,
        message: str,
        template_name: Optional[str] = None,
        missing_variables: Optional[List[str]] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if template_name:
            details['template_name'] = template_name
        if missing_variables:
            details['missing_variables'] = missing_variables
        
        super().__init__(
            message=message,
            code="PROMPT_ERROR",
            details=details,
            **kwargs,
        )


class AnalysisError(AIError):
    """
    Stock analysis errors.
    
    Raised when:
    - Analysis fails
    - Invalid analysis result
    - Missing required data for analysis
    """
    
    def __init__(
        self,
        message: str,
        stock_code: Optional[str] = None,
        analysis_type: Optional[str] = None,
        missing_data: Optional[List[str]] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if stock_code:
            details['stock_code'] = stock_code
        if analysis_type:
            details['analysis_type'] = analysis_type
        if missing_data:
            details['missing_data'] = missing_data
        
        super().__init__(
            message=message,
            code="ANALYSIS_ERROR",
            details=details,
            **kwargs,
        )


class StrategyError(AIError):
    """
    Trading strategy errors.
    
    Raised when:
    - Strategy not found
    - Strategy execution fails
    - Invalid strategy configuration
    """
    
    def __init__(
        self,
        message: str,
        strategy_name: Optional[str] = None,
        strategy_id: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        **kwargs,
    ):
        details = kwargs.get('details', {})
        if strategy_name:
            details['strategy_name'] = strategy_name
        if strategy_id:
            details['strategy_id'] = strategy_id
        if validation_errors:
            details['validation_errors'] = validation_errors
        
        super().__init__(
            message=message,
            code="STRATEGY_ERROR",
            details=details,
            **kwargs,
        )
