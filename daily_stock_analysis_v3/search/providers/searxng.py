"""
SearXNG Provider

Free, privacy-respecting metasearch engine.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import httpx

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from search.base import BaseSearchProvider, SearchResult, SearchRegistry
from exceptions import DataFetchError


class SearXNGProvider(BaseSearchProvider):
    """
    SearXNG metasearch provider.
    
    Free, open-source metasearch engine that aggregates results from multiple sources.
    """
    
    name = "searxng"
    description = "SearXNG metasearch engine (free, privacy-focused)"
    rate_limit = 60  # 60 requests per minute
    max_results = 20
    
    # Public SearXNG instances
    PUBLIC_INSTANCES = [
        "https://searx.be",
        "https://searx.org",
        "https://searx.info",
        "https://searx.xyz",
        "https://searx.tiekoetter.com",
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.base_url = self.config.get('base_url') or self.PUBLIC_INSTANCES[0]
        self.categories = self.config.get('categories', ['news', 'general'])
    
    def _get_client(self) -> httpx.Client:
        """Get HTTP client"""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.base_url,
                timeout=self.timeout,
                headers={'User-Agent': 'DailyStockAnalysis/3.0'},
            )
        return self._client
    
    def search(
        self,
        query: str,
        num_results: int = 10,
        date_range: Optional[tuple] = None,
        **kwargs,
    ) -> List[SearchResult]:
        """Search with SearXNG"""
        try:
            client = self._get_client()
            
            # Build parameters
            params = {
                'q': query,
                'format': 'json',
                'categories': ','.join(self.categories),
                'pageno': 1,
            }
            
            # Add date filter if specified
            if date_range:
                start_date, end_date = date_range
                params['time_range'] = 'year'  # SearXNG limited date filtering
            
            # Make request
            response = client.get('/search', params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            results = []
            for result in data.get('results', [])[:num_results]:
                search_result = SearchResult(
                    title=result.get('title', 'No title'),
                    url=result.get('url', ''),
                    snippet=result.get('content', result.get('snippet', '')),
                    source=result.get('source', 'Unknown'),
                    published_date=self._parse_date(result.get('publishedDate')),
                )
                results.append(search_result)
            
            logger.debug(f"SearXNG returned {len(results)} results for '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"SearXNG search failed: {e}")
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
        query = f"{stock_name} {stock_code} stock news"
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        try:
            results = self.search(
                query=query,
                num_results=kwargs.get('num_results', 10),
                date_range=(start_date, end_date),
                categories=['news'],
            )
            
            logger.info(f"Found {len(results)} news items for {stock_code}")
            return results
            
        except Exception as e:
            logger.error(f"SearXNG news search failed: {e}")
            return []  # Return empty list instead of failing
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string from SearXNG"""
        if not date_str:
            return None
        
        try:
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d",
                "%a, %d %b %Y %H:%M:%S",
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def test_instance(self, instance_url: str) -> bool:
        """Test if SearXNG instance is working"""
        try:
            client = httpx.Client(base_url=instance_url, timeout=10)
            response = client.get('/search', params={'q': 'test', 'format': 'json'})
            return response.status_code == 200
        except Exception:
            return False
    
    @classmethod
    def register(cls):
        """Register provider"""
        SearchRegistry.register(cls)


# Auto-register on import
SearXNGProvider.register()
