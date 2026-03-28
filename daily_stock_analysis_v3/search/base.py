"""
Base Search Provider - Abstract base class for search providers.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SearchResult:
    """Search result item"""
    
    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str,
        published_date: Optional[datetime] = None,
        sentiment: Optional[float] = None,
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.published_date = published_date
        self.sentiment = sentiment
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'snippet': self.snippet,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'sentiment': self.sentiment,
        }
    
    def __repr__(self) -> str:
        return f"SearchResult(title={self.title[:50]}, source={self.source})"


class BaseSearchProvider(ABC):
    """Abstract base class for search providers"""
    
    name = "base"
    description = "Base search provider"
    rate_limit: Optional[int] = None  # requests per minute
    max_results: int = 10
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url')
        self.timeout = self.config.get('timeout', 30)
        self._client = None
    
    @abstractmethod
    def search(
        self,
        query: str,
        num_results: int = 10,
        date_range: Optional[tuple] = None,
        **kwargs,
    ) -> List[SearchResult]:
        """
        Search for news/articles.
        
        Args:
            query: Search query
            num_results: Number of results
            date_range: (start_date, end_date) tuple
            **kwargs: Provider-specific params
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    @abstractmethod
    def search_news(
        self,
        stock_code: str,
        stock_name: str,
        days: int = 3,
        **kwargs,
    ) -> List[SearchResult]:
        """
        Search specifically for stock news.
        
        Args:
            stock_code: Stock symbol
            stock_name: Stock name
            days: Number of days to search back
            **kwargs: Provider-specific params
            
        Returns:
            List of SearchResult objects
        """
        pass
    
    def _validate_config(self) -> None:
        """Validate provider configuration"""
        pass
    
    def _get_client(self):
        """Get or create API client"""
        raise NotImplementedError("Subclasses must implement _get_client")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"


class SearchRegistry:
    """Registry for search providers"""
    
    _providers: Dict[str, Type[BaseSearchProvider]] = {}
    
    @classmethod
    def register(cls, provider_class: Type[BaseSearchProvider]) -> Type[BaseSearchProvider]:
        """Register a provider class"""
        if not issubclass(provider_class, BaseSearchProvider):
            raise TypeError("Must inherit from BaseSearchProvider")
        
        cls._providers[provider_class.name] = provider_class
        logger.debug(f"Registered search provider: {provider_class.name}")
        
        return provider_class
    
    @classmethod
    def get_provider(cls, name: str, config: Optional[Dict[str, Any]] = None) -> BaseSearchProvider:
        """Get provider instance"""
        if name not in cls._providers:
            available = list(cls._providers.keys())
            raise Exception(f"Search provider '{name}' not found. Available: {available}")
        
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
            'rate_limit': provider_class.rate_limit,
            'max_results': provider_class.max_results,
        }
