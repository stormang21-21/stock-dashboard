"""
News Aggregator

Aggregate news from multiple sources with deduplication and ranking.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from search.base import BaseSearchProvider, SearchResult
from search.providers.searxng import SearXNGProvider
from search.providers.tavily import TavilyProvider
from news.sentiment import SentimentAnalyzer


class NewsAggregator:
    """
    Aggregate news from multiple sources.
    
    Features:
    - Multi-source aggregation
    - Deduplication
    - Sentiment analysis
    - Relevance ranking
    """
    
    def __init__(
        self,
        providers: Optional[List[BaseSearchProvider]] = None,
        sentiment_analyzer: Optional[SentimentAnalyzer] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize news aggregator.
        
        Args:
            providers: List of search providers
            sentiment_analyzer: Sentiment analyzer instance
            config: Configuration
        """
        self.config = config or {}
        self.providers = providers or self._create_default_providers()
        self.sentiment_analyzer = sentiment_analyzer or SentimentAnalyzer()
        self.max_results = self.config.get('max_results', 20)
        self.deduplicate = self.config.get('deduplicate', True)
        
        logger.info(f"NewsAggregator initialized with {len(self.providers)} providers")
    
    def _create_default_providers(self) -> List[BaseSearchProvider]:
        """Create default search providers"""
        providers = []
        
        # SearXNG (free, no API key needed)
        try:
            providers.append(SearXNGProvider())
            logger.debug("Added SearXNG provider")
        except Exception as e:
            logger.warning(f"Failed to initialize SearXNG: {e}")
        
        # Tavily (requires API key)
        try:
            tavily_config = {'api_key': self.config.get('tavily_api_key')}
            if tavily_config['api_key']:
                providers.append(TavilyProvider(tavily_config))
                logger.debug("Added Tavily provider")
        except Exception as e:
            logger.debug(f"Tavily not configured: {e}")
        
        return providers
    
    def aggregate_news(
        self,
        stock_code: str,
        stock_name: str,
        days: int = 3,
        max_results: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Aggregate news from all providers.
        
        Args:
            stock_code: Stock symbol
            stock_name: Stock name
            days: Number of days to search back
            max_results: Maximum results to return
            
        Returns:
            List of aggregated news items
        """
        max_results = max_results or self.max_results
        
        all_results = []
        
        # Search with each provider
        for provider in self.providers:
            try:
                logger.debug(f"Searching with {provider.name}")
                results = provider.search_news(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    days=days,
                )
                all_results.extend(results)
                logger.debug(f"{provider.name} returned {len(results)} results")
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                continue
        
        logger.info(f"Aggregated {len(all_results)} total results from {len(self.providers)} providers")
        
        # Deduplicate
        if self.deduplicate:
            all_results = self._deduplicate_results(all_results)
            logger.info(f"After deduplication: {len(all_results)} results")
        
        # Add sentiment analysis
        for result in all_results:
            text = f"{result.title} {result.snippet}"
            result.sentiment = self.sentiment_analyzer.analyze_sentiment(text)
        
        # Sort by relevance (sentiment + recency)
        all_results = self._rank_results(all_results)
        
        # Limit results
        all_results = all_results[:max_results]
        
        # Convert to dict
        return [self._result_to_dict(r) for r in all_results]
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results"""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # Normalize URL for comparison
            url_normalized = result.url.lower().rstrip('/')
            
            if url_normalized not in seen_urls:
                seen_urls.add(url_normalized)
                unique_results.append(result)
        
        return unique_results
    
    def _rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Rank results by relevance.
        
        Ranking factors:
        - Sentiment (absolute value - more extreme = more relevant)
        - Recency (newer = more relevant)
        - Source credibility (future enhancement)
        """
        def score(result: SearchResult) -> float:
            # Sentiment score (0-1)
            sentiment_score = abs(result.sentiment or 0)
            
            # Recency score (0-1)
            if result.published_date:
                age = datetime.now() - result.published_date
                recency_score = max(0, 1 - (age.days / 7))  # Decay over 7 days
            else:
                recency_score = 0.5  # Default for unknown dates
            
            # Combined score
            return sentiment_score * 0.4 + recency_score * 0.6
        
        return sorted(results, key=score, reverse=True)
    
    def _result_to_dict(self, result: SearchResult) -> Dict[str, Any]:
        """Convert SearchResult to dictionary"""
        return {
            'title': result.title,
            'url': result.url,
            'snippet': result.snippet,
            'source': result.source,
            'published_date': result.published_date.isoformat() if result.published_date else None,
            'sentiment': result.sentiment,
            'sentiment_label': self._sentiment_to_label(result.sentiment),
        }
    
    def _sentiment_to_label(self, score: Optional[float]) -> str:
        """Convert sentiment score to label"""
        if score is None:
            return 'neutral'
        elif score > 0.3:
            return 'positive'
        elif score < -0.3:
            return 'negative'
        else:
            return 'neutral'
    
    def get_sentiment_summary(
        self,
        news_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Get sentiment summary for news items.
        
        Args:
            news_items: List of news items
            
        Returns:
            Sentiment summary
        """
        return self.sentiment_analyzer.calculate_aggregate_sentiment(news_items)
