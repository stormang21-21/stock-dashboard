"""
Free Tier Strategy

Designed to onboard users, show value, and convert to paid.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class FreeTierLimits:
    """
    Free tier limits - enough to show value, limited enough to convert.
    """
    # Market access
    max_markets: int = 1
    available_markets: List[str] = field(default_factory=lambda: ['market_us'])
    
    # API usage (generous enough to try, limited enough to convert)
    api_calls_per_day: int = 10
    api_calls_per_month: int = 100
    
    # Features (give a taste of premium)
    ai_analyses_per_day: int = 1
    ai_analyses_per_month: int = 5
    
    # Data limitations
    historical_data_days: int = 30  # Only 30 days of history
    real_time_delay_minutes: int = 15  # 15-minute delayed data
    
    # Portfolio
    max_portfolio_positions: int = 5
    max_portfolio_value: float = 100000  # Paper trading limit
    
    # Backtesting
    backtest_enabled: bool = False  # Premium feature
    
    # Support
    support_level: str = "community"  # No priority support
    
    # Watermarking (subtle upgrade prompt)
    show_upgrade_prompt: bool = True
    watermark_reports: bool = True


@dataclass
class TrialPeriod:
    """
    Pro trial to hook users with premium features.
    """
    enabled: bool = True
    duration_days: int = 7
    features_included: List[str] = field(default_factory=lambda: [
        'feature_ai_analysis',
        'feature_backtest',
        'feature_risk',
        'market_crypto',
    ])


class FreeTierManager:
    """
    Manages free tier experience and conversion triggers.
    """
    
    def __init__(self):
        self.limits = FreeTierLimits()
        self.trial = TrialPeriod()
        self.conversion_triggers = []
    
    def check_limit(self, tenant, action: str) -> Dict[str, Any]:
        """
        Check if action is allowed under free tier.
        
        Returns dict with:
        - allowed: bool
        - remaining: int
        - upgrade_prompt: str (if limited)
        """
        if not tenant.subscription or tenant.subscription.tier.value != 'free':
            return {'allowed': True, 'remaining': float('inf')}
        
        # Check API calls
        if action == 'api_call':
            remaining_day = self.limits.api_calls_per_day - tenant.api_calls_today
            remaining_month = self.limits.api_calls_per_month - (tenant.api_calls_total % self.limits.api_calls_per_month)
            
            if remaining_day <= 0:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'upgrade_prompt': 'Daily limit reached! Upgrade to Basic for 1,000 calls/day',
                    'upgrade_cta': 'Upgrade to Basic - $29/mo',
                }
            
            return {
                'allowed': True,
                'remaining': min(remaining_day, remaining_month),
                'limit': self.limits.api_calls_per_day,
            }
        
        # Check AI analyses
        if action == 'ai_analysis':
            # Count AI analyses from usage
            ai_used_today = tenant.config.get('ai_analyses_today', 0)
            
            if ai_used_today >= self.limits.ai_analyses_per_day:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'upgrade_prompt': 'Free tier includes 1 AI analysis/day. Upgrade for unlimited!',
                    'upgrade_cta': 'Upgrade to Basic - $29/mo',
                }
            
            return {
                'allowed': True,
                'remaining': self.limits.ai_analyses_per_day - ai_used_today,
            }
        
        # Check market access
        if action.startswith('market_'):
            if action not in self.limits.available_markets:
                return {
                    'allowed': False,
                    'remaining': 0,
                    'upgrade_prompt': f'{self._market_name(action)} available on Basic tier and above',
                    'upgrade_cta': 'Unlock All Markets - $29/mo',
                }
        
        return {'allowed': True, 'remaining': float('inf')}
    
    def _market_name(self, market_id: str) -> str:
        """Get market display name"""
        names = {
            'market_cn': 'China A-Shares',
            'market_hk': 'Hong Kong',
            'market_sg': 'Singapore',
            'market_jp': 'Japan',
            'market_crypto': 'Cryptocurrency',
        }
        return names.get(market_id, market_id)
    
    def get_upgrade_triggers(self, tenant) -> List[Dict[str, Any]]:
        """
        Get personalized upgrade triggers based on usage.
        
        Returns list of reasons to upgrade.
        """
        triggers = []
        
        # Trigger 1: Approaching API limit
        if tenant.api_calls_today >= self.limits.api_calls_per_day * 0.8:
            triggers.append({
                'type': 'api_limit',
                'severity': 'warning',
                'title': 'Running Low on API Calls',
                'message': f'You\'ve used {tenant.api_calls_today}/{self.limits.api_calls_per_day} API calls today',
                'upgrade_benefit': 'Basic tier includes 1,000 calls/day (100x more!)',
                'cta': 'Upgrade to Basic',
                'price': '$29/mo',
            })
        
        # Trigger 2: Tried to access premium market
        attempted_markets = tenant.config.get('attempted_markets', [])
        premium_markets = [m for m in attempted_markets if m not in self.limits.available_markets]
        if premium_markets:
            triggers.append({
                'type': 'market_access',
                'severity': 'info',
                'title': 'Unlock More Markets',
                'message': f'You\'ve shown interest in {len(premium_markets)} premium market(s)',
                'upgrade_benefit': 'Access all 6 global markets',
                'cta': 'Unlock All Markets',
                'price': '$29/mo',
            })
        
        # Trigger 3: AI analysis limit
        ai_used = tenant.config.get('ai_analyses_today', 0)
        if ai_used >= self.limits.ai_analyses_per_day:
            triggers.append({
                'type': 'ai_limit',
                'severity': 'warning',
                'title': 'AI Analysis Limit Reached',
                'message': 'You\'ve used your free AI analysis for today',
                'upgrade_benefit': 'Unlimited AI-powered analysis',
                'cta': 'Get Unlimited AI',
                'price': '$29/mo',
            })
        
        # Trigger 4: Portfolio limit
        portfolio_count = len(tenant.config.get('portfolio_positions', []))
        if portfolio_count >= self.limits.max_portfolio_positions * 0.8:
            triggers.append({
                'type': 'portfolio_limit',
                'severity': 'info',
                'title': 'Expand Your Portfolio',
                'message': f'You\'re tracking {portfolio_count}/{self.limits.max_portfolio_positions} positions',
                'upgrade_benefit': 'Track unlimited positions',
                'cta': 'Upgrade Portfolio',
                'price': '$29/mo',
            })
        
        # Trigger 5: Backtest interest (if they tried to access)
        if tenant.config.get('tried_backtest', False):
            triggers.append({
                'type': 'backtest',
                'severity': 'info',
                'title': 'Try Backtesting',
                'message': 'Backtesting is available on Pro tier',
                'upgrade_benefit': 'Test strategies on historical data',
                'cta': 'Start Pro Trial',
                'price': '$99/mo (7-day free trial)',
            })
        
        # Trigger 6: Trial expiration (if on trial)
        if tenant.config.get('trial_end_date'):
            trial_end = date.fromisoformat(tenant.config['trial_end_date'])
            days_left = (trial_end - date.today()).days
            
            if days_left <= 3:
                triggers.append({
                    'type': 'trial_expiring',
                    'severity': 'urgent',
                    'title': 'Trial Ending Soon',
                    'message': f'Your Pro trial ends in {days_left} day(s)',
                    'upgrade_benefit': 'Keep all Pro features',
                    'cta': 'Subscribe to Pro',
                    'price': '$99/mo',
                })
        
        return triggers
    
    def start_pro_trial(self, tenant) -> Dict[str, Any]:
        """
        Start 7-day Pro trial for free tier user.
        
        Conversion tactic: Let them experience premium, then convert.
        """
        if tenant.subscription.tier.value != 'free':
            return {'success': False, 'error': 'Only free tier eligible for trial'}
        
        if tenant.config.get('trial_used', False):
            return {'success': False, 'error': 'Trial already used'}
        
        # Enable Pro features for 7 days
        trial_end = date.today() + timedelta(days=7)
        
        tenant.config['trial_end_date'] = trial_end.isoformat()
        tenant.config['trial_used'] = True
        
        # Enable Pro modules temporarily
        pro_features = ['feature_backtest', 'feature_risk', 'market_crypto']
        for feature_id in pro_features:
            # Enable without checking limits
            if feature_id not in tenant.modules:
                tenant.enable_module(feature_id, feature_id, 'feature')
        
        return {
            'success': True,
            'trial_end': trial_end.isoformat(),
            'days_remaining': 7,
            'message': 'Pro trial activated! Enjoy all Pro features for 7 days.',
        }
    
    def get_free_tier_benefits(self) -> List[Dict[str, str]]:
        """Get list of free tier benefits for marketing"""
        return [
            {
                'icon': '🎯',
                'title': '1 Free Market',
                'desc': 'Start with US stocks',
            },
            {
                'icon': '📊',
                'title': '10 API Calls/Day',
                'desc': 'Enough to test the platform',
            },
            {
                'icon': '🤖',
                'title': '1 AI Analysis/Day',
                'desc': 'Experience AI-powered insights',
            },
            {
                'icon': '📈',
                'title': '5 Positions',
                'desc': 'Track your favorite stocks',
            },
            {
                'icon': '📚',
                'title': '30-Day History',
                'desc': 'Analyze recent trends',
            },
            {
                'icon': '🎁',
                'title': '7-Day Pro Trial',
                'desc': 'Try all premium features',
            },
        ]
    
    def get_upgrade_comparison(self) -> Dict[str, Dict[str, Any]]:
        """Get feature comparison table"""
        return {
            'Free': {
                'price': '$0',
                'markets': 1,
                'api_calls_day': 10,
                'ai_analyses_day': 1,
                'portfolio_positions': 5,
                'historical_data': '30 days',
                'backtest': False,
                'risk_analysis': False,
                'support': 'Community',
            },
            'Basic': {
                'price': '$29',
                'markets': 2,
                'api_calls_day': 1000,
                'ai_analyses_day': 'Unlimited',
                'portfolio_positions': 50,
                'historical_data': '1 year',
                'backtest': False,
                'risk_analysis': False,
                'support': 'Email',
                'popular': True,
            },
            'Pro': {
                'price': '$99',
                'markets': 6,
                'api_calls_day': 10000,
                'ai_analyses_day': 'Unlimited',
                'portfolio_positions': 'Unlimited',
                'historical_data': 'All time',
                'backtest': True,
                'risk_analysis': True,
                'support': 'Priority',
            },
            'Enterprise': {
                'price': '$499',
                'markets': 6,
                'api_calls_day': 100000,
                'ai_analyses_day': 'Unlimited',
                'portfolio_positions': 'Unlimited',
                'historical_data': 'All time',
                'backtest': True,
                'risk_analysis': True,
                'support': 'Dedicated',
            },
        }


# Global instance
free_tier_manager = FreeTierManager()


def get_free_tier_manager() -> FreeTierManager:
    """Get free tier manager instance"""
    return free_tier_manager
