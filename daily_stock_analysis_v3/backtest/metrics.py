"""
Backtest Metrics

Calculate backtest performance metrics.
"""

from typing import List, Dict, Any
import math
import logging

logger = logging.getLogger(__name__)


class BacktestMetrics:
    """
    Calculate backtest performance metrics.
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize metrics calculator.
        
        Args:
            results: Backtest results from engine
        """
        self.results = results
        self.equity_curve = results.get('equity_curve', [])
        self.trades = results.get('trades', [])
    
    def calculate_all(self) -> Dict[str, Any]:
        """
        Calculate all metrics.
        
        Returns:
            Complete metrics dictionary
        """
        return {
            'returns': self.calculate_returns(),
            'risk': self.calculate_risk(),
            'trades': self.calculate_trade_stats(),
            'drawdown': self.calculate_drawdown(),
        }
    
    def calculate_returns(self) -> Dict[str, float]:
        """Calculate return metrics"""
        if len(self.equity_curve) < 2:
            return {'total_return': 0.0, 'daily_returns': []}
        
        equities = [s['total_equity'] for s in self.equity_curve]
        
        # Total return
        total_return = ((equities[-1] - equities[0]) / equities[0]) * 100
        
        # Daily returns
        daily_returns = []
        for i in range(1, len(equities)):
            ret = (equities[i] - equities[i-1]) / equities[i-1]
            daily_returns.append(ret)
        
        # Annualized return
        days = len(equities)
        years = days / 252
        if years > 0:
            annualized = ((1 + total_return/100) ** (1/years) - 1) * 100
        else:
            annualized = 0.0
        
        return {
            'total_return': round(total_return, 2),
            'annualized_return': round(annualized, 2),
            'daily_returns': daily_returns,
            'avg_daily_return': round(sum(daily_returns) / len(daily_returns) * 100 if daily_returns else 0, 4),
        }
    
    def calculate_risk(self) -> Dict[str, float]:
        """Calculate risk metrics"""
        returns_data = self.calculate_returns()
        daily_returns = returns_data.get('daily_returns', [])
        
        if len(daily_returns) < 2:
            return {'volatility': 0.0, 'sharpe_ratio': 0.0}
        
        # Volatility
        mean_ret = sum(daily_returns) / len(daily_returns)
        variance = sum((r - mean_ret) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        daily_vol = math.sqrt(variance)
        annual_vol = daily_vol * math.sqrt(252) * 100
        
        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free = 0.02 / 252  # Daily
        if daily_vol > 0:
            sharpe = (mean_ret - risk_free) / daily_vol * math.sqrt(252)
        else:
            sharpe = 0.0
        
        return {
            'volatility': round(annual_vol, 2),
            'sharpe_ratio': round(sharpe, 2),
            'daily_volatility': round(daily_vol * 100, 4),
        }
    
    def calculate_trade_stats(self) -> Dict[str, Any]:
        """Calculate trade statistics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
            }
        
        # Calculate P&L for each trade (simplified)
        wins = []
        losses = []
        
        for trade in self.trades:
            # This is simplified - real implementation would track entry/exit prices
            pnl = trade.get('pnl', 0)
            if pnl > 0:
                wins.append(pnl)
            elif pnl < 0:
                losses.append(abs(pnl))
        
        total_trades = len(self.trades)
        winning_trades = len(wins)
        losing_trades = len(losses)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = sum(wins)
        gross_loss = sum(losses)
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
        
        avg_win = (sum(wins) / len(wins)) if wins else 0
        avg_loss = (sum(losses) / len(losses)) if losses else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'inf',
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
        }
    
    def calculate_drawdown(self) -> Dict[str, Any]:
        """Calculate drawdown metrics"""
        if len(self.equity_curve) < 2:
            return {'max_drawdown': 0.0, 'avg_drawdown': 0.0}
        
        equities = [s['total_equity'] for s in self.equity_curve]
        
        peak = equities[0]
        max_dd = 0.0
        drawdowns = []
        
        for equity in equities:
            if equity > peak:
                peak = equity
            
            dd = (peak - equity) / peak if peak > 0 else 0
            drawdowns.append(dd)
            
            if dd > max_dd:
                max_dd = dd
        
        avg_dd = sum(drawdowns) / len(drawdowns) if drawdowns else 0
        
        return {
            'max_drawdown': round(max_dd * 100, 2),
            'avg_drawdown': round(avg_dd * 100, 2),
            'drawdown_series': drawdowns,
        }
