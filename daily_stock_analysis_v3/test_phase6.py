#!/usr/bin/env python3
"""
Phase 6 Test Script

Tests Backtesting layer modules.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_backtest_engine():
    """Test backtest engine"""
    print("\n=== Testing Backtest Engine ===")
    
    from backtest.engine import BacktestEngine, BacktestConfig
    from data.providers.base import QuoteData, MarketType
    
    # Create engine
    config = BacktestConfig(
        initial_capital=100000,
        commission_rate=0.001,
        position_size_pct=0.2,
    )
    engine = BacktestEngine(config)
    print(f"✓ Backtest engine created")
    
    # Initialize
    start_date = date.today() - timedelta(days=30)
    engine.initialize(start_date, initial_capital=100000)
    print(f"✓ Backtest initialized with ${engine.portfolio.cash_balance:,.2f}")
    
    # Create sample quotes
    quotes = [
        QuoteData(
            symbol="AAPL",
            name="Apple Inc.",
            market=MarketType.US,
            currency="USD",
            timestamp=start_date,
            open=150.0,
            high=152.0,
            low=149.0,
            close=151.0,
            volume=1000000,
        )
    ]
    
    # Process day
    result = engine.process_day(start_date, quotes, [])
    print(f"✓ Day processed: equity=${result['equity']:,.2f}")
    
    # Get results
    results = engine.get_results()
    print(f"✓ Results: {results['trading_days']} days, ${results['final_equity']:,.2f} equity")
    
    print("✅ Backtest Engine: PASSED\n")


def test_backtest_metrics():
    """Test backtest metrics"""
    print("\n=== Testing Backtest Metrics ===")
    
    from backtest.metrics import BacktestMetrics
    
    # Sample results
    results = {
        'equity_curve': [
            {'date': '2026-01-01', 'total_equity': 100000},
            {'date': '2026-01-15', 'total_equity': 102000},
            {'date': '2026-02-01', 'total_equity': 98000},
            {'date': '2026-02-15', 'total_equity': 105000},
            {'date': '2026-03-01', 'total_equity': 110000},
        ],
        'trades': [
            {'pnl': 500},
            {'pnl': -200},
            {'pnl': 800},
            {'pnl': 300},
        ],
    }
    
    metrics_calc = BacktestMetrics(results)
    metrics = metrics_calc.calculate_all()
    
    print(f"✓ Returns calculated: {metrics['returns']['total_return']:.2f}%")
    print(f"✓ Risk calculated: Sharpe={metrics['risk']['sharpe_ratio']:.2f}")
    print(f"✓ Trades calculated: {metrics['trades']['total_trades']} trades")
    print(f"✓ Drawdown calculated: {metrics['drawdown']['max_drawdown']:.2f}%")
    
    print("✅ Backtest Metrics: PASSED\n")


def test_backtest_report():
    """Test backtest report"""
    print("\n=== Testing Backtest Report ===")
    
    from backtest.metrics import BacktestMetrics
    from backtest.report import BacktestReport
    
    # Sample data
    results = {
        'start_date': '2026-01-01',
        'end_date': '2026-03-01',
        'trading_days': 60,
        'initial_capital': 100000,
        'final_equity': 110000,
        'total_trades': 20,
        'equity_curve': [],
        'trades': [],
        'config': {'initial_capital': 100000},
    }
    
    metrics = {
        'returns': {'total_return': 10.0, 'annualized_return': 45.0},
        'risk': {'volatility': 15.0, 'sharpe_ratio': 1.5},
        'trades': {'total_trades': 20, 'win_rate': 60.0, 'profit_factor': 2.0},
        'drawdown': {'max_drawdown': 8.0},
    }
    
    # Generate report
    report = BacktestReport(results, metrics)
    
    # Text report
    text_report = report.generate_text()
    assert "BACKTEST REPORT" in text_report
    print("✓ Text report generated")
    
    # JSON report
    json_report = report.generate_json()
    assert "summary" in json_report
    print("✓ JSON report generated")
    
    # Summary
    summary = report.generate_summary()
    print(f"✓ Summary: {summary['performance_rating']} rating")
    
    print("✅ Backtest Report: PASSED\n")


def main():
    """Run all Phase 6 tests"""
    print("=" * 60)
    print("Phase 6: Backtesting Layer Tests")
    print("=" * 60)
    
    try:
        test_backtest_engine()
        test_backtest_metrics()
        test_backtest_report()
        
        print("=" * 60)
        print("🎉 ALL PHASE 6 TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
