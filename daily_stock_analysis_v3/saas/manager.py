"""
Tenant Manager

Manages tenants, subscriptions, and module access.
"""

from typing import Dict, List, Optional, Any
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from saas.models import Tenant, Subscription, SubscriptionTier, TenantModule


class TenantManager:
    """
    Manages all tenants in the system.
    
    Features:
    - Tenant CRUD
    - Subscription management
    - Module access control
    - Usage tracking
    """
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.api_keys: Dict[str, str] = {}  # api_key -> tenant_id
        logger.info("TenantManager initialized")
    
    def create_tenant(
        self,
        name: str,
        email: str,
        company: str = "",
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            name: Tenant name
            email: Contact email
            company: Company name
            tier: Subscription tier
            
        Returns:
            Created tenant
        """
        tenant = Tenant(
            name=name,
            email=email,
            company=company,
        )
        
        # Create subscription
        tenant.subscription = Subscription(
            tier=tier,
            start_date=date.today(),
        )
        
        # Generate API key
        api_key = f"dsa_{tenant.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.api_keys[api_key] = tenant.id
        
        # Store tenant
        self.tenants[tenant.id] = tenant
        
        logger.info(f"Tenant created: {tenant.id} ({name})")
        
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenants.get(tenant_id)
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key"""
        tenant_id = self.api_keys.get(api_key)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None
    
    def update_tenant(self, tenant_id: str, **kwargs) -> Optional[Tenant]:
        """Update tenant properties"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        
        for key, value in kwargs.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        
        tenant.updated_at = datetime.now()
        logger.info(f"Tenant updated: {tenant_id}")
        
        return tenant
    
    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete tenant"""
        if tenant_id not in self.tenants:
            return False
        
        tenant = self.tenants[tenant_id]
        
        # Remove API keys
        api_keys_to_remove = [k for k, v in self.api_keys.items() if v == tenant_id]
        for key in api_keys_to_remove:
            del self.api_keys[key]
        
        # Remove tenant
        del self.tenants[tenant_id]
        
        logger.info(f"Tenant deleted: {tenant_id}")
        
        return True
    
    def upgrade_subscription(
        self,
        tenant_id: str,
        new_tier: SubscriptionTier,
    ) -> Optional[Tenant]:
        """
        Upgrade tenant subscription.
        
        Args:
            tenant_id: Tenant ID
            new_tier: New subscription tier
            
        Returns:
            Updated tenant
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        
        # Create new subscription
        tenant.subscription = Subscription(
            tier=new_tier,
            start_date=date.today(),
        )
        
        tenant.updated_at = datetime.now()
        
        logger.info(f"Subscription upgraded: {tenant_id} to {new_tier.value}")
        
        return tenant
    
    def enable_module(
        self,
        tenant_id: str,
        module_id: str,
        module_name: str,
        module_type: str,
    ) -> Optional[TenantModule]:
        """
        Enable module for tenant.
        
        Args:
            tenant_id: Tenant ID
            module_id: Module ID
            module_name: Module name
            module_type: Module type (market, feature, indicator)
            
        Returns:
            Enabled module
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        
        # Check subscription limits
        if module_type == "market":
            enabled_markets = len(tenant.get_enabled_modules("market"))
            if not tenant.subscription.can_access_market(enabled_markets):
                logger.warning(f"Tenant {tenant_id} exceeded market limit")
                return None
        
        module = tenant.enable_module(module_id, module_name, module_type)
        logger.info(f"Module enabled: {module_id} for {tenant_id}")
        
        return module
    
    def disable_module(self, tenant_id: str, module_id: str) -> bool:
        """Disable module for tenant"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return False
        
        tenant.disable_module(module_id)
        logger.info(f"Module disabled: {module_id} for {tenant_id}")
        
        return True
    
    def check_api_access(self, api_key: str) -> bool:
        """
        Check if API call is allowed.
        
        Args:
            api_key: API key
            
        Returns:
            True if allowed, False if rate limited or invalid
        """
        tenant = self.get_tenant_by_api_key(api_key)
        
        if not tenant:
            logger.warning(f"Invalid API key: {api_key[:10]}...")
            return False
        
        if tenant.status != "active":
            logger.warning(f"Inactive tenant: {tenant.id}")
            return False
        
        if not tenant.subscription or not tenant.subscription.is_active():
            logger.warning(f"Expired subscription: {tenant.id}")
            return False
        
        # Track API call
        if not tenant.track_api_call():
            logger.warning(f"Rate limit exceeded: {tenant.id}")
            return False
        
        return True
    
    def get_tenant_modules(self, tenant_id: str, module_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get tenant's enabled modules.
        
        Args:
            tenant_id: Tenant ID
            module_type: Optional filter by type
            
        Returns:
            List of module dictionaries
        """
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return []
        
        modules = tenant.get_enabled_modules(module_type)
        return [m.to_dict() for m in modules]
    
    def get_usage_report(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get usage report for tenant"""
        tenant = self.tenants.get(tenant_id)
        if not tenant:
            return None
        
        return {
            'tenant_id': tenant.id,
            'tenant_name': tenant.name,
            'subscription_tier': tenant.subscription.tier.value if tenant.subscription else None,
            'usage': tenant.get_usage_summary(),
            'enabled_modules': len(tenant.modules),
            'markets_enabled': len(tenant.get_enabled_modules("market")),
            'status': tenant.status,
        }
    
    def list_tenants(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all tenants.
        
        Args:
            status: Optional filter by status
            
        Returns:
            List of tenant summaries
        """
        tenants = self.tenants.values()
        
        if status:
            tenants = [t for t in tenants if t.status == status]
        
        return [t.to_dict() for t in tenants]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get platform statistics"""
        total_tenants = len(self.tenants)
        active_tenants = len([t for t in self.tenants.values() if t.status == "active"])
        
        # Count by tier
        tier_counts = {}
        for tenant in self.tenants.values():
            if tenant.subscription:
                tier = tenant.subscription.tier.value
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Total API calls today
        total_api_calls = sum(t.api_calls_today for t in self.tenants.values())
        
        return {
            'total_tenants': total_tenants,
            'active_tenants': active_tenants,
            'tier_distribution': tier_counts,
            'total_api_calls_today': total_api_calls,
            'total_modules_enabled': sum(len(t.modules) for t in self.tenants.values()),
        }


# Global tenant manager instance
tenant_manager = TenantManager()


def get_tenant_manager() -> TenantManager:
    """Get tenant manager instance"""
    return tenant_manager
