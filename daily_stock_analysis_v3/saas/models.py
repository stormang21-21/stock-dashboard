"""
SaaS Tenant & Subscription Models

Multi-tenant architecture with modular subscriptions.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Set
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tiers"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ModuleStatus(str, Enum):
    """Module status"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    PENDING = "pending"


@dataclass
class TenantModule:
    """
    Module access for a tenant.
    
    Controls which features/markets a tenant can access.
    """
    module_id: str
    module_name: str
    module_type: str  # market, feature, indicator
    enabled: bool = False
    configured: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    added_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'module_id': self.module_id,
            'module_name': self.module_name,
            'module_type': self.module_type,
            'enabled': self.enabled,
            'configured': self.configured,
            'config': self.config,
            'added_at': self.added_at.isoformat(),
        }


@dataclass
class Subscription:
    """
    Subscription plan for a tenant.
    """
    tier: SubscriptionTier
    start_date: date
    end_date: Optional[date] = None
    auto_renew: bool = True
    max_markets: int = 1
    max_users: int = 1
    max_api_calls_per_day: int = 100
    features: Set[str] = field(default_factory=set)
    
    # Pricing
    price_monthly: float = 0.0
    price_yearly: float = 0.0
    currency: str = "USD"
    
    def __post_init__(self):
        # Set defaults based on tier
        if self.tier == SubscriptionTier.FREE:
            self.max_markets = 1
            self.max_users = 1
            self.max_api_calls_per_day = 10
            self.price_monthly = 0.0
        elif self.tier == SubscriptionTier.BASIC:
            self.max_markets = 2
            self.max_users = 3
            self.max_api_calls_per_day = 1000
            self.price_monthly = 29.0
        elif self.tier == SubscriptionTier.PRO:
            self.max_markets = 6
            self.max_users = 10
            self.max_api_calls_per_day = 10000
            self.price_monthly = 99.0
        elif self.tier == SubscriptionTier.ENTERPRISE:
            self.max_markets = 6
            self.max_users = 100
            self.max_api_calls_per_day = 100000
            self.price_monthly = 499.0
    
    def is_active(self) -> bool:
        """Check if subscription is active"""
        if self.end_date is None:
            return True
        return date.today() <= self.end_date
    
    def can_access_market(self, market_count: int) -> bool:
        """Check if tenant can access additional market"""
        return market_count < self.max_markets
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tier': self.tier.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'auto_renew': self.auto_renew,
            'max_markets': self.max_markets,
            'max_users': self.max_users,
            'max_api_calls_per_day': self.max_api_calls_per_day,
            'features': list(self.features),
            'price_monthly': self.price_monthly,
            'is_active': self.is_active(),
        }


@dataclass
class Tenant:
    """
    Tenant (client) in the SaaS platform.
    
    Each tenant has:
    - Subscription plan
    - Enabled modules (markets, features)
    - API usage tracking
    - Configuration
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    email: str = ""
    company: str = ""
    
    # Subscription
    subscription: Optional[Subscription] = None
    
    # Enabled modules
    modules: Dict[str, TenantModule] = field(default_factory=dict)
    
    # API usage tracking
    api_calls_today: int = 0
    api_calls_total: int = 0
    last_api_call: Optional[datetime] = None
    
    # Account status
    status: str = "active"  # active, suspended, cancelled
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def enable_module(self, module_id: str, module_name: str, module_type: str) -> TenantModule:
        """Enable a module for this tenant"""
        if module_id not in self.modules:
            self.modules[module_id] = TenantModule(
                module_id=module_id,
                module_name=module_name,
                module_type=module_type,
                enabled=True,
                configured=False,
            )
        else:
            self.modules[module_id].enabled = True
        
        self.updated_at = datetime.now()
        return self.modules[module_id]
    
    def disable_module(self, module_id: str) -> None:
        """Disable a module"""
        if module_id in self.modules:
            self.modules[module_id].enabled = False
            self.updated_at = datetime.now()
    
    def is_module_enabled(self, module_id: str) -> bool:
        """Check if module is enabled"""
        if module_id not in self.modules:
            return False
        return self.modules[module_id].enabled
    
    def get_enabled_modules(self, module_type: Optional[str] = None) -> List[TenantModule]:
        """Get all enabled modules, optionally filtered by type"""
        modules = [m for m in self.modules.values() if m.enabled]
        if module_type:
            modules = [m for m in modules if m.module_type == module_type]
        return modules
    
    def can_access_market(self, market: str) -> bool:
        """Check if tenant can access specific market"""
        if not self.subscription or not self.subscription.is_active():
            return False
        
        market_module_id = f"market_{market}"
        return self.is_module_enabled(market_module_id)
    
    def track_api_call(self) -> bool:
        """
        Track API call.
        
        Returns:
            True if call is allowed, False if rate limited
        """
        if not self.subscription:
            return False
        
        # Reset daily counter if new day
        if self.last_api_call:
            last_date = self.last_api_call.date()
            if last_date < date.today():
                self.api_calls_today = 0
        
        # Check rate limit
        if self.api_calls_today >= self.subscription.max_api_calls_per_day:
            return False
        
        # Track call
        self.api_calls_today += 1
        self.api_calls_total += 1
        self.last_api_call = datetime.now()
        
        return True
    
    def get_usage_summary(self) -> Dict[str, Any]:
        """Get API usage summary"""
        limit = self.subscription.max_api_calls_per_day if self.subscription else 0
        
        return {
            'calls_today': self.api_calls_today,
            'calls_total': self.api_calls_total,
            'daily_limit': limit,
            'remaining_today': max(0, limit - self.api_calls_today),
            'usage_percent': (self.api_calls_today / limit * 100) if limit > 0 else 0,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'company': self.company,
            'status': self.status,
            'subscription': self.subscription.to_dict() if self.subscription else None,
            'enabled_modules': [m.to_dict() for m in self.get_enabled_modules()],
            'module_count': len(self.modules),
            'usage': self.get_usage_summary(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
