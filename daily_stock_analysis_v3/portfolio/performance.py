"""
Performance Calculator

Calculate portfolio performance metrics.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import math
import logging

logger = logging.getLogger(__name__)


class PerformanceCalculator:
    """
    Calculate portfolio performance metrics.
    
    Metrics:
    - Total return
    - Annualized return
    - Sharpe ratio
    - Sortino ratio
    - Maximum drawdown
    - Win rate
    - Profit factor
    """
    
    def __init__(self, snapshots: List[Dict[str, Any]]):
        """
        Initialize calculator.
        
        Args:
            snapshots: List of portfolio snapshots over time
        """
        self.snapshots = sorted(snapshots, key=lambda x: x['date'])
        self.equity_curve = [s['total_equity'] for s in snapshots]
        self.dates = [s['date'] for s in snapshots]
    
    def total_return(self) -> float:
        """
        Calculate total return.
        
        Returns:
            Total return percentage
        """
        if len(self.equity_curve) < 2:
            return 0.0
        
        start_equity = self.equity_curve[0]
        end_equity = self.equity_curve[-1]
        
        if start_equity == 0:
            return 0.0
        
        return ((end_equity - start_equity) / start_equity) * 100
    
    def annualized_return(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate annualized return.
        
        Args:
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Annualized return percentage
        """
        if len(self.equity_curve) < 2:
            return 0.0
        
        total_ret = self.total_return() / 100
        
        # Calculate time period in years
        if len(self.dates) >= 2:
            start_date = date.fromisoformat(self.dates[0])
            end_date = date.fromisoformat(self.dates[-1])
            days = (end_date - start_date).days
            years = days / 365.25
        else:
            years = 1.0
        
        if years <= 0:
            return 0.0
        
        # Annualized return
        annualized = ((1 + total_ret) ** (1 / years) - 1) * 100
        
        return annualized
    
    def volatility(self, annualize: bool = True) -> float:
        """
        Calculate return volatility.
        
        Args:
            annualize: Whether to annualize volatility
            
        Returns:
            Volatility percentage
        """
        if len(self.equity_curve) < 3:
            return 0.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev = self.equity_curve[i - 1]
            curr = self.equity_curve[i]
            if prev > 0:
                returns.append((curr - prev) / prev)
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        daily_vol = math.sqrt(variance)
        
        # Annualize
        if annualize:
            daily_vol *= math.sqrt(252)  # Trading days
        
        return daily_vol * 100
    
    def sharpe_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe ratio
        """
        annual_ret = self.annualized_return()
        vol = self.volatility(annualize=True)
        
        if vol == 0:
            return 0.0
        
        sharpe = (annual_ret - risk_free_rate) / vol
        return sharpe
    
    def sortino_ratio(self, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sortino ratio (downside deviation).
        
        Args:
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sortino ratio
        """
        if len(self.equity_curve) < 3:
            return 0.0
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(self.equity_curve)):
            prev = self.equity_curve[i - 1]
            curr = self.equity_curve[i]
            if prev > 0:
                returns.append((curr - prev) / prev)
        
        # Calculate downside deviation
        negative_returns = [r for r in returns if r < 0]
        
        if len(negative_returns) < 2:
            return 0.0
        
        downside_variance = sum(r ** 2 for r in negative_returns) / (len(negative_returns) - 1)
        downside_dev = math.sqrt(downside_variance) * math.sqrt(252)  # Annualized
        
        if downside_dev == 0:
            return 0.0
        
        annual_ret = self.annualized_return()
        sortino = (annual_ret - risk_free_rate) / (downside_dev * 100)
        
        return sortino
    
    def max_drawdown(self) -> float:
        """
        Calculate maximum drawdown.
        
        Returns:
            Maximum drawdown percentage
        """
        if len(self.equity_curve) < 2:
            return 0.0
        
        peak = self.equity_curve[0]
        max_dd = 0.0
        
        for equity in self.equity_curve:
            if equity > peak:
                peak = equity
            
            drawdown = (peak - equity) / peak if peak > 0 else 0
            if drawdown > max_dd:
                max_dd = drawdown
        
        return max_dd * 100
    
    def calmar_ratio(self) -> float:
        """
        Calculate Calmar ratio (return / max drawdown).
        
        Returns:
            Calmar ratio
        """
        annual_ret = self.annualized_return()
        max_dd = self.max_drawdown()
        
        if max_dd == 0:
            return 0.0
        
        return annual_ret / max_dd
    
    def win_rate(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate win rate from trades.
        
        Args:
            trades: List of trade records
            
        Returns:
            Win rate percentage
        """
        if not trades:
            return 0.0
        
        # Count winning trades (simplified - assumes trades have pnl field)
        winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
        
        return (len(winning_trades) / len(trades)) * 100
    
    def profit_factor(self, trades: List[Dict[str, Any]]) -> float:
        """
        Calculate profit factor (gross profit / gross loss).
        
        Args:
            trades: List of trade records
            
        Returns:
            Profit factor
        """
        if not trades:
            return 0.0
        
        gross_profit = sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) > 0)
        gross_loss = abs(sum(t.get('pnl', 0) for t in trades if t.get('pnl', 0) < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
        
        return gross_profit / gross_loss
    
    def get_all_metrics(self, trades: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Get all performance metrics.
        
        Args:
            trades: Optional list of trades for trade-based metrics
            
        Returns:
            Dictionary of all metrics
        """
        metrics = {
            'total_return': round(self.total_return(), 2),
            'annualized_return': round(self.annualized_return(), 2),
            'volatility': round(self.volatility(), 2),
            'sharpe_ratio': round(self.sharpe_ratio(), 2),
            'sortino_ratio': round(self.sortino_ratio(), 2),
            'max_drawdown': round(self.max_drawdown(), 2),
            'calmar_ratio': round(self.calmar_ratio(), 2),
            'snapshots': len(self.snapshots),
            'start_date': self.dates[0] if self.dates else None,
            'end_date': self.dates[-1] if self.dates else None,
        }
        
        # Add trade-based metrics if trades provided
        if trades:
            metrics['win_rate'] = round(self.win_rate(trades), 2)
            metrics['profit_factor'] = round(self.profit_factor(trades), 2)
            metrics['total_trades'] = len(trades)
        
        return metrics
