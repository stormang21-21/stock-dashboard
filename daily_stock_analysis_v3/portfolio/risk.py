"""
Risk Analyzer

Analyze portfolio risk metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
import math
import logging

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Analyze portfolio risk.
    
    Metrics:
    - Value at Risk (VaR)
    - Conditional VaR (CVaR)
    - Beta
    - Alpha
    - Concentration risk
    - Sector exposure
    """
    
    def __init__(self, snapshots: List[Dict[str, Any]], benchmark_returns: Optional[List[float]] = None):
        """
        Initialize analyzer.
        
        Args:
            snapshots: Portfolio snapshots
            benchmark_returns: Optional benchmark returns for beta/alpha
        """
        self.snapshots = sorted(snapshots, key=lambda x: x['date'])
        self.equity_curve = [s['total_equity'] for s in snapshots]
        self.benchmark_returns = benchmark_returns
    
    def calculate_returns(self) -> List[float]:
        """Calculate daily returns"""
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev = self.equity_curve[i - 1]
            curr = self.equity_curve[i]
            if prev > 0:
                returns.append((curr - prev) / prev)
        return returns
    
    def var(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            confidence_level: Confidence level (e.g., 0.95 for 95%)
            
        Returns:
            VaR percentage
        """
        returns = self.calculate_returns()
        
        if len(returns) < 10:
            return 0.0
        
        # Sort returns
        sorted_returns = sorted(returns)
        
        # Get percentile
        index = int((1 - confidence_level) * len(sorted_returns))
        var_value = sorted_returns[index]
        
        return abs(var_value) * 100
    
    def cvar(self, confidence_level: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        
        Args:
            confidence_level: Confidence level
            
        Returns:
            CVaR percentage
        """
        returns = self.calculate_returns()
        
        if len(returns) < 10:
            return 0.0
        
        # Sort returns
        sorted_returns = sorted(returns)
        
        # Get tail
        tail_index = int((1 - confidence_level) * len(sorted_returns))
        tail_returns = sorted_returns[:tail_index]
        
        if not tail_returns:
            return 0.0
        
        # Average of tail losses
        cvar_value = sum(tail_returns) / len(tail_returns)
        
        return abs(cvar_value) * 100
    
    def beta(self) -> float:
        """
        Calculate portfolio beta vs benchmark.
        
        Returns:
            Beta coefficient
        """
        if not self.benchmark_returns or len(self.benchmark_returns) < 10:
            return 1.0  # Default to market beta
        
        portfolio_returns = self.calculate_returns()
        
        if len(portfolio_returns) != len(self.benchmark_returns):
            min_len = min(len(portfolio_returns), len(self.benchmark_returns))
            portfolio_returns = portfolio_returns[:min_len]
            benchmark_returns = self.benchmark_returns[:min_len]
        else:
            benchmark_returns = self.benchmark_returns
        
        # Calculate covariance and variance
        n = len(portfolio_returns)
        mean_port = sum(portfolio_returns) / n
        mean_bench = sum(benchmark_returns) / n
        
        covariance = sum(
            (portfolio_returns[i] - mean_port) * (benchmark_returns[i] - mean_bench)
            for i in range(n)
        ) / (n - 1)
        
        variance_bench = sum((r - mean_bench) ** 2 for r in benchmark_returns) / (n - 1)
        
        if variance_bench == 0:
            return 1.0
        
        beta = covariance / variance_bench
        return beta
    
    def alpha(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate portfolio alpha (excess return).
        
        Args:
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Alpha percentage (annualized)
        """
        if not self.benchmark_returns:
            return 0.0
        
        # Calculate annualized returns
        portfolio_returns = self.calculate_returns()
        
        if len(portfolio_returns) < 10:
            return 0.0
        
        # Simple annualization
        avg_daily_return = sum(portfolio_returns) / len(portfolio_returns)
        annual_portfolio_return = avg_daily_return * 252
        
        avg_bench_return = sum(self.benchmark_returns) / len(self.benchmark_returns)
        annual_bench_return = avg_bench_return * 252
        
        # CAPM alpha
        portfolio_beta = self.beta()
        expected_return = risk_free_rate + portfolio_beta * (annual_bench_return - risk_free_rate)
        
        alpha = annual_portfolio_return - expected_return
        
        return alpha * 100
    
    def concentration_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze concentration risk.
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            Concentration metrics
        """
        if not positions:
            return {
            'herfindahl_index': 0.0,
            'top_5_concentration': 0.0,
            'largest_position': 0.0,
            'position_count': 0,
        }
        
        # Calculate market values
        market_values = [p.get('market_value', 0) for p in positions if p.get('market_value', 0) > 0]
        
        if not market_values:
            return {
            'herfindahl_index': 0.0,
            'top_5_concentration': 0.0,
            'largest_position': 0.0,
            'position_count': 0,
        }
        
        total_value = sum(market_values)
        
        # Calculate weights
        weights = [mv / total_value for mv in market_values]
        
        # Herfindahl-Hirschman Index (HHI)
        hhi = sum(w ** 2 for w in weights)
        
        # Top 5 concentration
        sorted_weights = sorted(weights, reverse=True)
        top_5_concentration = sum(sorted_weights[:5]) * 100
        
        # Largest position
        largest_position = max(weights) * 100
        
        return {
            'herfindahl_index': round(hhi, 4),
            'top_5_concentration': round(top_5_concentration, 2),
            'largest_position': round(largest_position, 2),
            'position_count': len(positions),
            'diversification_score': round(1 - hhi, 4),  # Higher = more diversified
        }
    
    def get_risk_summary(self, positions: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Get comprehensive risk summary.
        
        Args:
            positions: Optional position list for concentration analysis
            
        Returns:
            Risk summary dictionary
        """
        summary = {
            'var_95': round(self.var(0.95), 2),
            'var_99': round(self.var(0.99), 2),
            'cvar_95': round(self.cvar(0.95), 2),
            'beta': round(self.beta(), 2),
            'alpha': round(self.alpha(), 2),
            'snapshots': len(self.snapshots),
        }
        
        # Add concentration risk if positions provided
        if positions:
            concentration = self.concentration_risk(positions)
            summary.update(concentration)
        
        # Risk rating
        if summary['var_95'] > 5:
            summary['risk_rating'] = 'high'
        elif summary['var_95'] > 2:
            summary['risk_rating'] = 'medium'
        else:
            summary['risk_rating'] = 'low'
        
        return summary
