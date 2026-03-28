import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

"""
Data Aggregator

Aggregates data from multiple providers with failover and priority.
"""

from typing import Optional, List, Dict, Any, Type
from datetime import date, datetime
import time

from data.providers.base import BaseDataProvider, QuoteData, MarketType, TimeFrame, DataProviderRegistry
from data.validators import DataValidator
from data.normalizers import DataNormalizer
from exceptions import DataSourceError, DataFetchError
from loggers import get_logger

logger = get_logger(__name__)


class DataAggregator:
    """
    Aggregates data from multiple providers.
    
    Features:
    - Provider priority ordering
    - Automatic failover
    - Data caching
    - Response time tracking
    """
    
    def __init__(
        self,
        providers: Optional[List[str]] = None,
        provider_configs: Optional[Dict[str, Dict[str, Any]]] = None,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
    ):
        """
        Initialize aggregator.
        
        Args:
            providers: List of provider names in priority order
            provider_configs: Configuration for each provider
            cache_enabled: Enable data caching
            cache_ttl: Cache TTL in seconds
        """
        self.providers: List[BaseDataProvider] = []
        self.provider_configs = provider_configs or {}
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Initialize providers
        if providers:
            for provider_name in providers:
                try:
                    config = self.provider_configs.get(provider_name, {})
                    provider = DataProviderRegistry.get_provider(provider_name, config)
                    self.providers.append(provider)
                    logger.debug(f"Added provider: {provider_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize provider {provider_name}: {e}")
        else:
            # Use all registered providers
            for provider_name in DataProviderRegistry.list_providers():
                try:
                    config = self.provider_configs.get(provider_name, {})
                    provider = DataProviderRegistry.get_provider(provider_name, config)
                    self.providers.append(provider)
                except Exception as e:
                    logger.warning(f"Failed to initialize provider {provider_name}: {e}")
        
        # Sort by rate limit (higher = better priority)
        self.providers.sort(
            key=lambda p: p.rate_limit or 0,
            reverse=True,
        )
        
        # Initialize validator and normalizer
        self.validator = DataValidator(strict=False)
        self.normalizer = DataNormalizer()
        
        logger.info(f"DataAggregator initialized with {len(self.providers)} providers")
    
    def get_quote(
        self,
        symbol: str,
        date: Optional[date] = None,
        market: Optional[MarketType] = None,
        use_cache: bool = True,
    ) -> QuoteData:
        """
        Get quote with automatic failover.
        
        Tries providers in priority order until one succeeds.
        
        Args:
            symbol: Stock symbol
            date: Quote date
            market: Market type
            use_cache: Use cached data if available
            
        Returns:
            QuoteData from first successful provider
            
        Raises:
            DataSourceError: If all providers fail
        """
        # Check cache
        cache_key = f"quote_{symbol}_{date}"
        if use_cache and self.cache_enabled and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]['data']
        
        # Try providers in order
        errors = []
        
        for provider in self.providers:
            # Check if provider supports market
            if market and not provider.supports_market(market):
                logger.debug(f"Provider {provider.name} doesn't support market {market}")
                continue
            
            try:
                logger.debug(f"Trying provider: {provider.name}")
                start_time = time.time()
                
                # Get quote
                quote = provider.get_quote(symbol, date)
                
                # Validate
                validation = self.validator.validate_quote(quote.to_dict())
                if not validation['valid']:
                    logger.warning(f"Validation failed for {provider.name}: {validation['errors']}")
                    continue
                
                # Cache result
                self._cache_result(cache_key, quote)
                
                elapsed = time.time() - start_time
                logger.info(f"Successfully fetched {symbol} from {provider.name} in {elapsed:.2f}s")
                
                return quote
                
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                errors.append({
                    'provider': provider.name,
                    'error': str(e),
                })
                continue
        
        # All providers failed
        error_msg = f"All providers failed for {symbol}"
        logger.error(error_msg)
        
        raise DataSourceError(
            message=error_msg,
            attempted_sources=[p.name for p in self.providers],
            details={'errors': errors},
        )
    
    def get_history(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: TimeFrame = TimeFrame.DAILY,
        market: Optional[MarketType] = None,
        use_cache: bool = True,
    ) -> List[QuoteData]:
        """
        Get historical data with automatic failover.
        
        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            timeframe: Data timeframe
            market: Market type
            use_cache: Use cached data
            
        Returns:
            List of QuoteData objects
            
        Raises:
            DataSourceError: If all providers fail
        """
        # Check cache
        cache_key = f"history_{symbol}_{start_date}_{end_date}"
        if use_cache and self.cache_enabled and self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for {cache_key}")
            return self._cache[cache_key]['data']
        
        # Try providers in order
        errors = []
        
        for provider in self.providers:
            if market and not provider.supports_market(market):
                continue
            
            if not provider.supports_timeframe(timeframe):
                continue
            
            try:
                logger.debug(f"Trying provider: {provider.name} for history")
                start_time = time.time()
                
                quotes = provider.get_history(symbol, start_date, end_date, timeframe)
                
                if not quotes:
                    logger.warning(f"No data from {provider.name}")
                    continue
                
                # Validate all quotes
                valid_quotes = []
                for quote in quotes:
                    validation = self.validator.validate_quote(quote.to_dict())
                    if validation['valid']:
                        valid_quotes.append(quote)
                    else:
                        logger.debug(f"Skipped invalid quote: {validation['errors']}")
                
                if not valid_quotes:
                    continue
                
                # Cache result
                self._cache_result(cache_key, valid_quotes)
                
                elapsed = time.time() - start_time
                logger.info(f"Fetched {len(valid_quotes)} records from {provider.name} in {elapsed:.2f}s")
                
                return valid_quotes
                
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                errors.append({
                    'provider': provider.name,
                    'error': str(e),
                })
                continue
        
        # All providers failed
        error_msg = f"All providers failed for {symbol} history"
        logger.error(error_msg)
        
        raise DataSourceError(
            message=error_msg,
            attempted_sources=[p.name for p in self.providers],
            details={'errors': errors},
        )
    
    def get_realtime_quote(
        self,
        symbol: str,
        market: Optional[MarketType] = None,
    ) -> QuoteData:
        """
        Get real-time quote with failover.
        
        Args:
            symbol: Stock symbol
            market: Market type
            
        Returns:
            QuoteData with latest price
            
        Raises:
            DataSourceError: If all providers fail
        """
        # Try providers in order
        errors = []
        
        for provider in self.providers:
            if market and not provider.supports_market(market):
                continue
            
            try:
                logger.debug(f"Trying provider: {provider.name} for realtime")
                quote = provider.get_realtime_quote(symbol)
                
                # Validate
                validation = self.validator.validate_quote(quote.to_dict())
                if not validation['valid']:
                    continue
                
                logger.info(f"Realtime quote from {provider.name}: {quote.close}")
                return quote
                
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                errors.append({
                    'provider': provider.name,
                    'error': str(e),
                })
                continue
        
        # All providers failed
        error_msg = f"All providers failed for {symbol} realtime quote"
        logger.error(error_msg)
        
        raise DataSourceError(
            message=error_msg,
            attempted_sources=[p.name for p in self.providers],
            details={'errors': errors},
        )
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry is valid"""
        if cache_key not in self._cache:
            return False
        
        if cache_key not in self._cache_timestamps:
            return False
        
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        
        return age < self.cache_ttl
    
    def _cache_result(self, cache_key: str, data: Any) -> None:
        """Cache result"""
        if not self.cache_enabled:
            return
        
        self._cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now(),
        }
        self._cache_timestamps[cache_key] = datetime.now()
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Cache cleared")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """
        Get provider statistics.
        
        Returns:
            Dictionary with provider stats
        """
        stats = {
            'providers': [],
            'cache_size': len(self._cache),
            'cache_enabled': self.cache_enabled,
        }
        
        for provider in self.providers:
            stats['providers'].append({
                'name': provider.name,
                'description': provider.description,
                'markets': [m.value if hasattr(m, 'value') else str(m) for m in provider.supported_markets],
                'rate_limit': provider.rate_limit,
            })
        
        return stats
