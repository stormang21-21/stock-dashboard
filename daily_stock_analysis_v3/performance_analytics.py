"""
Portfolio Performance Analytics

Analyze portfolio performance with charts and metrics.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PerformanceAnalytics:
    """Calculate portfolio performance metrics"""
    
    def __init__(self):
        pass
    
    def calculate_portfolio_returns(self, positions: List[Dict], history_days: int = 30) -> Dict[str, Any]:
        """Calculate portfolio returns over time"""
        if not positions:
            return {'error': 'No positions'}
        
        # Generate historical data (in production, fetch real historical prices)
        dates = []
        values = []
        benchmarks = []  # S&P 500 benchmark
        
        base_value = sum(p.get('market_value', 0) for p in positions)
        base_benchmark = 4500  # Approximate S&P 500 level
        
        for i in range(history_days):
            date = datetime.now() - timedelta(days=history_days-i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Simulate portfolio value with some randomness
            random_factor = 0.95 + (i / history_days) * 0.1  # Gradual increase
            values.append(round(base_value * random_factor, 2))
            
            # Simulate S&P 500 benchmark
            benchmark_factor = 0.97 + (i / history_days) * 0.08
            benchmarks.append(round(base_benchmark * benchmark_factor, 2))
        
        # Calculate metrics
        total_return = ((values[-1] - values[0]) / values[0]) * 100 if values[0] > 0 else 0
        benchmark_return = ((benchmarks[-1] - benchmarks[0]) / benchmarks[0]) * 100 if benchmarks[0] > 0 else 0
        alpha = total_return - benchmark_return
        
        # Calculate volatility (standard deviation of daily returns)
        daily_returns = []
        for i in range(1, len(values)):
            if values[i-1] > 0:
                daily_returns.append((values[i] - values[i-1]) / values[i-1])
        
        volatility = 0
        if daily_returns:
            avg_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = (variance ** 0.5) * (252 ** 0.5) * 100  # Annualized
        
        # Sharpe ratio (assuming 5% risk-free rate)
        risk_free_rate = 5
        sharpe = (total_return - risk_free_rate) / volatility if volatility > 0 else 0
        
        # Max drawdown
        max_drawdown = 0
        peak = values[0]
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            'dates': dates,
            'values': values,
            'benchmarks': benchmarks,
            'metrics': {
                'total_return': round(total_return, 2),
                'benchmark_return': round(benchmark_return, 2),
                'alpha': round(alpha, 2),
                'volatility': round(volatility, 2),
                'sharpe_ratio': round(sharpe, 2),
                'max_drawdown': round(max_drawdown, 2),
                'best_day': round(max(daily_returns) * 100, 2) if daily_returns else 0,
                'worst_day': round(min(daily_returns) * 100, 2) if daily_returns else 0,
            }
        }
    
    def calculate_asset_allocation(self, positions: List[Dict]) -> Dict[str, Any]:
        """Calculate asset allocation by sector"""
        if not positions:
            return {'error': 'No positions'}
        
        # Mock sector data (in production, fetch from API)
        sector_map = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'NVDA': 'Technology', 'TSLA': 'Consumer Cyclical', 'AMZN': 'Consumer Cyclical',
            'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial',
            'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare',
            'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy',
        }
        
        sectors = {}
        total_value = sum(p.get('market_value', 0) for p in positions)
        
        for pos in positions:
            symbol = pos.get('symbol', '')
            value = pos.get('market_value', 0)
            sector = sector_map.get(symbol, 'Other')
            
            if sector not in sectors:
                sectors[sector] = 0
            sectors[sector] += value
        
        # Calculate percentages
        allocation = []
        for sector, value in sorted(sectors.items(), key=lambda x: x[1], reverse=True):
            percentage = (value / total_value * 100) if total_value > 0 else 0
            allocation.append({
                'sector': sector,
                'value': round(value, 2),
                'percentage': round(percentage, 2),
            })
        
        return {
            'total_value': round(total_value, 2),
            'allocation': allocation,
            'sectors_count': len(sectors),
        }
    
    def calculate_top_performers(self, positions: List[Dict]) -> Dict[str, Any]:
        """Calculate best and worst performers"""
        if not positions:
            return {'error': 'No positions'}
        
        # Sort by performance
        sorted_positions = sorted(
            positions,
            key=lambda x: x.get('unrealized_pnl_percent', 0),
            reverse=True
        )
        
        # Top 5 gainers
        gainers = []
        for pos in sorted_positions[:5]:
            if pos.get('unrealized_pnl_percent', 0) > 0:
                gainers.append({
                    'symbol': pos.get('symbol', ''),
                    'company_name': pos.get('company_name', ''),
                    'pnl_percent': round(pos.get('unrealized_pnl_percent', 0), 2),
                    'pnl_value': round(pos.get('unrealized_pnl', 0), 2),
                })
        
        # Top 5 losers
        losers = []
        for pos in sorted_positions[-5:]:
            if pos.get('unrealized_pnl_percent', 0) < 0:
                losers.append({
                    'symbol': pos.get('symbol', ''),
                    'company_name': pos.get('company_name', ''),
                    'pnl_percent': round(pos.get('unrealized_pnl_percent', 0), 2),
                    'pnl_value': round(pos.get('unrealized_pnl', 0), 2),
                })
        
        return {
            'gainers': gainers,
            'losers': losers,
            'total_positions': len(positions),
        }
    
    def get_summary(self, portfolio_summary: Dict) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            'total_value': portfolio_summary.get('total_portfolio_value', 0),
            'total_invested': portfolio_summary.get('total_market_value', 0),
            'cash': portfolio_summary.get('cash', 0),
            'total_gain_loss': portfolio_summary.get('total_unrealized_pnl', 0),
            'total_gain_loss_percent': portfolio_summary.get('total_unrealized_pnl_percent', 0),
            'positions_count': portfolio_summary.get('positions_count', 0),
        }


# Singleton instance
analytics = PerformanceAnalytics()


def get_analytics() -> PerformanceAnalytics:
    return analytics
