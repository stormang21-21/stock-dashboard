"""
Tavily Provider

AI-powered search API optimized for research and news.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from search.base import BaseSearchProvider, SearchResult, SearchRegistry
from exceptions import DataFetchError


class TavilyProvider(BaseSearchProvider):
    """
    Tavily AI search provider.
    
    Optimized for news and research with AI-powered relevance ranking.
    """
    
    name = "tavily"
    description = "Tavily AI search (optimized for news & research)"
    rate_limit = 100  # 100 requests per minute
    max_results = 10
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = "https://api.tavily.com"
        self.search_depth = self.config.get('search_depth', 'basic')  # basic or advanced
        
        if not self.api_key:
            logger.warning("Tavily API key not configured")
    
    def _get_client(self):
        """Get Tavily client"""
        if self._client is None:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                raise DataFetchError(
                    "Tavily package not installed. Run: pip install tavily-python",
                    source=self.name,
                )
            except Exception as e:
                raise DataFetchError(
                    f"Failed to initialize Tavily client: {e}",
                    source=self.name,
                )
        
        return self._client
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        date_range: Optional[tuple] = None,
        **kwargs,
    ) -> List[SearchResult]:
        """Search with Tavily"""
        try:
            client = self._get_client()
            
            # Search
            response = client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=num_results,
                include_answer=False,
            )
            
            # Parse results
            results = []
            for result in response.get('results', []):
                search_result = SearchResult(
                    title=result.get('title', 'No title'),
                    url=result.get('url', ''),
                    snippet=result.get('content', ''),
                    source=result.get('source', 'Unknown'),
                    published_date=None,  # Tavily doesn't provide dates
                )
                results.append(search_result)
            
            logger.debug(f"Tavily returned {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            raise DataFetchError(
                message=str(e),
                source=self.name,
                details={'query': query},
            )
    
    def search_news(
        self,
        stock_code: str,
        stock_name: str,
        days: int = 3,
        **kwargs,
    ) -> List[SearchResult]:
        """Search for stock news"""
        # Build query
        query = f"{stock_name} {stock_code} stock news analysis"
        
        try:
            client = self._get_client()
            
            # Use Tavily's news search
            response = client.search(
                query=query,
                search_depth=self.search_depth,
                max_results=kwargs.get('num_results', 10),
                topic='news',  # Tavily supports news topic
            )
            
            # Parse results
            results = []
            for result in response.get('results', []):
                search_result = SearchResult(
                    title=result.get('title', 'No title'),
                    url=result.get('url', ''),
                    snippet=result.get('content', ''),
                    source=result.get('source', 'Unknown'),
                    published_date=None,
                )
                results.append(search_result)
            
            logger.info(f"Tavily found {len(results)} news items for {stock_code}")
            return results
            
        except Exception as e:
            logger.error(f"Tavily news search failed: {e}")
            return []
    
    @classmethod
    def register(cls):
        """Register provider"""
        SearchRegistry.register(cls)


# Auto-register on import
TavilyProvider.register()
