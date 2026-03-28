"""
Base LLM Provider - Abstract base class for all LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Type
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    name = "base"
    description = "Base LLM provider"
    supports_streaming = False
    supports_vision = False
    max_tokens = 8192
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize LLM provider.
        
        Args:
            config: Provider configuration (api_key, model, etc.)
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.model = self.config.get('model', 'default')
        self.base_url = self.config.get('base_url')
        self.temperature = self.config.get('temperature', 0.7)
        self.max_tokens = self.config.get('max_tokens', self.max_tokens)
        self.timeout = self.config.get('timeout', 30)
        self._client = None
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            temperature: Sampling temperature
            max_tokens: Max tokens in response
            
        Returns:
            Generated text
        """
        pass
    
    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.
        
        Args:
            prompt: User prompt
            schema: JSON schema for output
            system_prompt: System instruction
            
        Returns:
            Parsed JSON object
        """
        pass
    
    def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ):
        """
        Generate text with streaming.
        
        Args:
            prompt: User prompt
            system_prompt: System instruction
            
        Yields:
            Text chunks
        """
        if not self.supports_streaming:
            raise NotImplementedError(f"{self.name} does not support streaming")
        
        # To be implemented by providers that support streaming
        pass
    
    def _validate_config(self) -> None:
        """Validate provider configuration"""
        if not self.api_key:
            raise ValueError(f"API key required for {self.name}")
    
    def _get_client(self):
        """Get or create API client (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _get_client")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model})"


class LLMRegistry:
    """Registry for LLM providers"""
    
    _providers: Dict[str, Type[LLMProvider]] = {}
    
    @classmethod
    def register(cls, provider_class: Type[LLMProvider]) -> Type[LLMProvider]:
        """Register a provider class"""
        if not issubclass(provider_class, LLMProvider):
            raise TypeError("Must inherit from LLMProvider")
        
        cls._providers[provider_class.name] = provider_class
        logger.debug(f"Registered LLM provider: {provider_class.name}")
        
        return provider_class
    
    @classmethod
    def get_provider(cls, name: str, config: Optional[Dict[str, Any]] = None) -> LLMProvider:
        """Get provider instance by name"""
        if name not in cls._providers:
            available = list(cls._providers.keys())
            raise Exception(f"LLM provider '{name}' not found. Available: {available}")
        
        provider_class = cls._providers[name]
        return provider_class(config=config)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """List all registered providers"""
        return list(cls._providers.keys())
    
    @classmethod
    def get_provider_info(cls, name: str) -> Dict[str, Any]:
        """Get provider information"""
        if name not in cls._providers:
            return {}
        
        provider_class = cls._providers[name]
        return {
            'name': provider_class.name,
            'description': provider_class.description,
            'supports_streaming': provider_class.supports_streaming,
            'supports_vision': provider_class.supports_vision,
            'max_tokens': provider_class.max_tokens,
        }
