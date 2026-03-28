"""
Backtest Report Generator

Generate comprehensive backtest reports.
"""

from typing import Dict, Any, List
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class BacktestReport:
    """
    Generate backtest reports.
    """
    
    def __init__(self, results: Dict[str, Any], metrics: Dict[str, Any]):
        """
        Initialize report generator.
        
        Args:
            results: Backtest results
            metrics: Calculated metrics
        """
        self.results = results
        self.metrics = metrics
        self.generated_at = datetime.now()
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate executive summary.
        
        Returns:
            Summary dictionary
        """
        returns = self.metrics.get('returns', {})
        risk = self.metrics.get('risk', {})
        trades = self.metrics.get('trades', {})
        drawdown = self.metrics.get('drawdown', {})
        
        return {
            'report_generated': self.generated_at.isoformat(),
            'period': {
                'start': self.results.get('start_date'),
                'end': self.results.get('end_date'),
                'trading_days': self.results.get('trading_days'),
            },
            'capital': {
                'initial': self.results.get('initial_capital'),
                'final': self.results.get('final_equity'),
                'total_return_pct': returns.get('total_return'),
                'annualized_return_pct': returns.get('annualized_return'),
            },
            'risk': {
                'volatility_pct': risk.get('volatility'),
                'sharpe_ratio': risk.get('sharpe_ratio'),
                'max_drawdown_pct': drawdown.get('max_drawdown'),
            },
            'trades': {
                'total': trades.get('total_trades'),
                'win_rate_pct': trades.get('win_rate'),
                'profit_factor': trades.get('profit_factor'),
            },
            'performance_rating': self._calculate_rating(returns, risk, drawdown),
        }
    
    def _calculate_rating(
        self,
        returns: Dict[str, Any],
        risk: Dict[str, Any],
        drawdown: Dict[str, Any],
    ) -> str:
        """Calculate overall performance rating"""
        score = 0
        
        # Return scoring
        ann_ret = returns.get('annualized_return', 0)
        if ann_ret > 20:
            score += 3
        elif ann_ret > 10:
            score += 2
        elif ann_ret > 0:
            score += 1
        
        # Risk scoring
        sharpe = risk.get('sharpe_ratio', 0)
        if sharpe > 2:
            score += 3
        elif sharpe > 1:
            score += 2
        elif sharpe > 0:
            score += 1
        
        # Drawdown scoring
        max_dd = abs(drawdown.get('max_drawdown', 0))
        if max_dd < 10:
            score += 3
        elif max_dd < 20:
            score += 2
        elif max_dd < 30:
            score += 1
        
        # Rating
        if score >= 8:
            return 'excellent'
        elif score >= 6:
            return 'good'
        elif score >= 4:
            return 'average'
        else:
            return 'poor'
    
    def generate_json(self, indent: int = 2) -> str:
        """
        Generate JSON report.
        
        Args:
            indent: JSON indentation
            
        Returns:
            JSON string
        """
        report = {
            'summary': self.generate_summary(),
            'metrics': self.metrics,
            'results': {
                'config': self.results.get('config'),
                'trades': self.results.get('trades'),
                'equity_curve': self.results.get('equity_curve'),
            },
        }
        
        return json.dumps(report, indent=indent, default=str)
    
    def generate_text(self) -> str:
        """
        Generate text report.
        
        Returns:
            Text report string
        """
        summary = self.generate_summary()
        
        lines = [
            "=" * 60,
            "BACKTEST REPORT",
            "=" * 60,
            "",
            f"Generated: {summary['report_generated']}",
            "",
            "PERIOD",
            "-" * 40,
            f"Start: {summary['period']['start']}",
            f"End: {summary['period']['end']}",
            f"Trading Days: {summary['period']['trading_days']}",
            "",
            "RETURNS",
            "-" * 40,
            f"Initial Capital: ${summary['capital']['initial']:,.2f}",
            f"Final Equity: ${summary['capital']['final']:,.2f}",
            f"Total Return: {summary['capital']['total_return_pct']:.2f}%",
            f"Annualized Return: {summary['capital']['annualized_return_pct']:.2f}%",
            "",
            "RISK",
            "-" * 40,
            f"Volatility: {summary['risk']['volatility_pct']:.2f}%",
            f"Sharpe Ratio: {summary['risk']['sharpe_ratio']:.2f}",
            f"Max Drawdown: {summary['risk']['max_drawdown_pct']:.2f}%",
            "",
            "TRADES",
            "-" * 40,
            f"Total Trades: {summary['trades']['total']}",
            f"Win Rate: {summary['trades']['win_rate_pct']:.2f}%",
            f"Profit Factor: {summary['trades']['profit_factor']}",
            "",
            f"PERFORMANCE RATING: {summary['performance_rating'].upper()}",
            "=" * 60,
        ]
        
        return "\n".join(lines)
    
    def save_json(self, filepath: str) -> None:
        """
        Save JSON report to file.
        
        Args:
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            f.write(self.generate_json())
        logger.info(f"Report saved to {filepath}")
    
    def save_text(self, filepath: str) -> None:
        """
        Save text report to file.
        
        Args:
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            f.write(self.generate_text())
        logger.info(f"Report saved to {filepath}")
