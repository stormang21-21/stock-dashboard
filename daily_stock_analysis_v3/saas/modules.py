"""
Module Registry

Manages available modules (markets, features, indicators).
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MarketModule:
    """
    Market module definition.
    
    Defines a market that tenants can subscribe to.
    """
    id: str
    name: str
    description: str
    market_code: str  # CN, HK, US, SG, JP, CRYPTO
    providers: List[str] = field(default_factory=list)
    icon: str = "📈"
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'market_code': self.market_code,
            'providers': self.providers,
            'icon': self.icon,
            'enabled': self.enabled,
        }


@dataclass
class FeatureModule:
    """
    Feature module definition.
    
    Defines a feature that tenants can enable.
    """
    id: str
    name: str
    description: str
    category: str  # analysis, news, portfolio, backtest
    required_tier: str = "basic"  # free, basic, pro, enterprise
    enabled: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'required_tier': self.required_tier,
            'enabled': self.enabled,
        }


class ModuleRegistry:
    """
    Registry for all available modules.
    
    Manages:
    - Market modules
    - Feature modules
    - Indicator modules
    """
    
    def __init__(self):
        self.market_modules: Dict[str, MarketModule] = {}
        self.feature_modules: Dict[str, FeatureModule] = {}
        self._initialize_default_modules()
        logger.info("ModuleRegistry initialized")
    
    def _initialize_default_modules(self):
        """Initialize default modules"""
        
        # Market modules
        markets = [
            MarketModule(
                id="market_cn",
                name="China A-Shares",
                description="Shanghai and Shenzhen stock exchanges",
                market_code="CN",
                providers=["akshare", "efinance"],
                icon="🇨🇳",
            ),
            MarketModule(
                id="market_hk",
                name="Hong Kong",
                description="Hong Kong Stock Exchange",
                market_code="HK",
                providers=["yfinance"],
                icon="🇭🇰",
            ),
            MarketModule(
                id="market_us",
                name="US Stocks",
                description="NYSE, NASDAQ, AMEX",
                market_code="US",
                providers=["yfinance"],
                icon="🇺🇸",
            ),
            MarketModule(
                id="market_sg",
                name="Singapore",
                description="Singapore Exchange",
                market_code="SG",
                providers=["yahoo_asia"],
                icon="🇸🇬",
            ),
            MarketModule(
                id="market_jp",
                name="Japan",
                description="Tokyo Stock Exchange",
                market_code="JP",
                providers=["yahoo_asia"],
                icon="🇯🇵",
            ),
            MarketModule(
                id="market_crypto",
                name="Cryptocurrency",
                description="Bitcoin, Ethereum, and 1000+ altcoins",
                market_code="CRYPTO",
                providers=["binance", "coingecko", "yahoo_crypto"],
                icon="₿",
            ),
        ]
        
        for market in markets:
            self.register_market(market)
        
        # Feature modules
        features = [
            FeatureModule(
                id="feature_ai_analysis",
                name="AI Analysis",
                description="LLM-powered stock analysis and recommendations",
                category="analysis",
                required_tier="basic",
            ),
            FeatureModule(
                id="feature_news",
                name="News & Sentiment",
                description="Real-time news aggregation and sentiment analysis",
                category="news",
                required_tier="basic",
            ),
            FeatureModule(
                id="feature_portfolio",
                name="Portfolio Tracking",
                description="Track holdings, P&L, and performance metrics",
                category="portfolio",
                required_tier="basic",
            ),
            FeatureModule(
                id="feature_backtest",
                name="Backtesting",
                description="Test strategies on historical data",
                category="backtest",
                required_tier="pro",
            ),
            FeatureModule(
                id="feature_technical",
                name="Technical Indicators",
                description="RSI, MACD, Bollinger Bands, and more",
                category="analysis",
                required_tier="basic",
            ),
            FeatureModule(
                id="feature_risk",
                name="Risk Analysis",
                description="VaR, CVaR, Beta, Alpha calculations",
                category="portfolio",
                required_tier="pro",
            ),
        ]
        
        for feature in features:
            self.register_feature(feature)
    
    def register_market(self, market: MarketModule) -> None:
        """Register a market module"""
        self.market_modules[market.id] = market
        logger.debug(f"Market registered: {market.id}")
    
    def register_feature(self, feature: FeatureModule) -> None:
        """Register a feature module"""
        self.feature_modules[feature.id] = feature
        logger.debug(f"Feature registered: {feature.id}")
    
    def get_market(self, market_id: str) -> Optional[MarketModule]:
        """Get market by ID"""
        return self.market_modules.get(market_id)
    
    def get_feature(self, feature_id: str) -> Optional[FeatureModule]:
        """Get feature by ID"""
        return self.feature_modules.get(feature_id)
    
    def list_markets(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """List all market modules"""
        markets = self.market_modules.values()
        if enabled_only:
            markets = [m for m in markets if m.enabled]
        return [m.to_dict() for m in markets]
    
    def list_features(
        self,
        enabled_only: bool = True,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all feature modules"""
        features = self.feature_modules.values()
        
        if enabled_only:
            features = [f for f in features if f.enabled]
        
        if category:
            features = [f for f in features if f.category == category]
        
        return [f.to_dict() for f in features]
    
    def get_available_modules_for_tier(self, tier: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all modules available for a subscription tier.
        
        Args:
            tier: Subscription tier (free, basic, pro, enterprise)
            
        Returns:
            Dictionary with markets and features lists
        """
        tier_order = ["free", "basic", "pro", "enterprise"]
        tier_index = tier_order.index(tier) if tier in tier_order else 0
        
        # All markets are available from basic tier
        markets = self.list_markets(enabled_only=True)
        
        # Features filtered by tier
        available_features = []
        for feature in self.feature_modules.values():
            if not feature.enabled:
                continue
            
            required_tier_index = tier_order.index(feature.required_tier) if feature.required_tier in tier_order else 0
            
            if required_tier_index <= tier_index:
                available_features.append(feature.to_dict())
        
        return {
            'markets': markets,
            'features': available_features,
        }


# Global registry instance
module_registry = ModuleRegistry()


def get_module_registry() -> ModuleRegistry:
    """Get module registry instance"""
    return module_registry
