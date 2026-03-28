"""
Admin API

REST API for tenant and subscription management.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from saas import TenantManager, ModuleRegistry, SubscriptionTier
from saas.manager import get_tenant_manager
from saas.modules import get_module_registry


class AdminAPI:
    """
    Admin API for managing tenants and subscriptions.
    """
    
    def __init__(self):
        self.tenant_manager = get_tenant_manager()
        self.module_registry = get_module_registry()
    
    def onboard_tenant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Onboard a new tenant.
        
        Args:
            data: Onboarding data with name, email, tier, markets
            
        Returns:
            Result with API key
        """
        try:
            # Create tenant
            tier = SubscriptionTier(data.get('tier', 'basic'))
            tenant = self.tenant_manager.create_tenant(
                name=data['name'],
                email=data['email'],
                company=data.get('company', ''),
                tier=tier,
            )
            
            # Enable selected markets
            for market_id in data.get('markets', []):
                market = self.module_registry.get_market(market_id)
                if market:
                    self.tenant_manager.enable_module(
                        tenant.id,
                        market_id,
                        market.name,
                        'market',
                    )
            
            # Enable basic features based on tier
            features = self.module_registry.list_features(enabled_only=True)
            for feature in features:
                if self._tier_can_access_feature(tier.value, feature['required_tier']):
                    self.tenant_manager.enable_module(
                        tenant.id,
                        feature['id'],
                        feature['name'],
                        'feature',
                    )
            
            # Get API key
            api_key = [k for k, v in self.tenant_manager.api_keys.items() if v == tenant.id][0]
            
            return {
                'success': True,
                'tenant_id': tenant.id,
                'api_key': api_key,
                'tenant': tenant.to_dict(),
            }
            
        except Exception as e:
            logger.error(f"Onboarding failed: {e}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def _tier_can_access_feature(self, tier: str, required_tier: str) -> bool:
        """Check if tier can access feature"""
        tier_order = ['free', 'basic', 'pro', 'enterprise']
        tier_index = tier_order.index(tier) if tier in tier_order else 0
        required_index = tier_order.index(required_tier) if required_tier in tier_order else 0
        return tier_index >= required_index
    
    def list_tenants(self, status: Optional[str] = None) -> Dict[str, Any]:
        """List all tenants"""
        tenants = self.tenant_manager.list_tenants(status)
        return {
            'success': True,
            'tenants': tenants,
            'count': len(tenants),
        }
    
    def get_tenant(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant details"""
        tenant = self.tenant_manager.get_tenant(tenant_id)
        if not tenant:
            return {
                'success': False,
                'error': 'Tenant not found',
            }
        
        return {
            'success': True,
            'tenant': tenant.to_dict(),
        }
    
    def update_tenant(self, tenant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update tenant"""
        tenant = self.tenant_manager.update_tenant(tenant_id, **updates)
        if not tenant:
            return {
                'success': False,
                'error': 'Tenant not found',
            }
        
        return {
            'success': True,
            'tenant': tenant.to_dict(),
        }
    
    def upgrade_tenant(self, tenant_id: str, new_tier: str) -> Dict[str, Any]:
        """Upgrade tenant subscription"""
        try:
            tier = SubscriptionTier(new_tier)
            tenant = self.tenant_manager.upgrade_subscription(tenant_id, tier)
            
            if not tenant:
                return {
                    'success': False,
                    'error': 'Tenant not found',
                }
            
            return {
                'success': True,
                'tenant': tenant.to_dict(),
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }
    
    def enable_module(self, tenant_id: str, module_id: str, module_name: str, module_type: str) -> Dict[str, Any]:
        """Enable module for tenant"""
        module = self.tenant_manager.enable_module(tenant_id, module_id, module_name, module_type)
        
        if not module:
            return {
                'success': False,
                'error': 'Failed to enable module',
            }
        
        return {
            'success': True,
            'module': module.to_dict(),
        }
    
    def disable_module(self, tenant_id: str, module_id: str) -> Dict[str, Any]:
        """Disable module for tenant"""
        success = self.tenant_manager.disable_module(tenant_id, module_id)
        
        return {
            'success': success,
        }
    
    def get_tenant_modules(self, tenant_id: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """Get tenant's modules"""
        modules = self.tenant_manager.get_tenant_modules(tenant_id, module_type)
        
        return {
            'success': True,
            'modules': modules,
            'count': len(modules),
        }
    
    def get_usage(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant usage report"""
        report = self.tenant_manager.get_usage_report(tenant_id)
        
        if not report:
            return {
                'success': False,
                'error': 'Tenant not found',
            }
        
        return {
            'success': True,
            'usage': report,
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get platform statistics"""
        stats = self.tenant_manager.get_statistics()
        
        # Add module stats
        stats['available_markets'] = len(self.module_registry.list_markets())
        stats['available_features'] = len(self.module_registry.list_features())
        
        return {
            'success': True,
            'statistics': stats,
        }
    
    def list_available_modules(self, tier: Optional[str] = None) -> Dict[str, Any]:
        """List all available modules"""
        if tier:
            modules = self.module_registry.get_available_modules_for_tier(tier)
        else:
            modules = {
                'markets': self.module_registry.list_markets(),
                'features': self.module_registry.list_features(),
            }
        
        return {
            'success': True,
            'modules': modules,
        }


# Global API instance
admin_api = AdminAPI()


def get_admin_api() -> AdminAPI:
    """Get admin API instance"""
    return admin_api
