#!/usr/bin/env python3
"""
Phase 5 Test Script

Tests Portfolio & Trading layer modules.
"""

import sys
from pathlib import Path
from datetime import date, timedelta

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_portfolio_models():
    """Test portfolio models"""
    print("\n=== Testing Portfolio Models ===")
    
    from portfolio.models import Portfolio, Position, Trade, CashFlow, TradeType
    
    # Create portfolio
    portfolio = Portfolio(id="port_1", name="Test Portfolio")
    print(f"✓ Portfolio created: {portfolio.name}")
    
    # Add cash
    portfolio.cash_balance = 100000
    print(f"✓ Initial cash: ${portfolio.cash_balance:,.2f}")
    
    # Create position
    position = Position(
        id="pos_AAPL",
        portfolio_id=portfolio.id,
        stock_code="AAPL",
        stock_name="Apple Inc.",
        quantity=100,
        average_cost=150.0,
        current_price=155.0,
    )
    portfolio.add_position(position)
    print(f"✓ Position added: {position.quantity} AAPL @ ${position.average_cost}")
    
    # Check metrics
    assert portfolio.total_market_value == 15500
    assert portfolio.total_cost_basis == 15000
    assert portfolio.total_unrealized_pnl == 500
    print(f"✓ Market value: ${portfolio.total_market_value:,.2f}")
    print(f"✓ Unrealized P&L: ${portfolio.total_unrealized_pnl:,.2f} ({portfolio.total_return_percent:.2f}%)")
    
    print("✅ Portfolio Models: PASSED\n")


def test_portfolio_tracker():
    """Test portfolio tracker"""
    print("\n=== Testing Portfolio Tracker ===")
    
    from portfolio.models import Portfolio
    from portfolio.tracker import PortfolioTracker
    
    # Create portfolio
    portfolio = Portfolio(id="port_2", name="Tracker Test")
    portfolio.cash_balance = 100000
    tracker = PortfolioTracker(portfolio)
    
    # Buy stock
    trade = tracker.buy(
        stock_code="AAPL",
        stock_name="Apple Inc.",
        quantity=100,
        price=150.0,
        commission=1.0,
    )
    print(f"✓ Buy executed: {trade.quantity} {trade.stock_code} @ ${trade.price}")
    
    # Update price
    tracker.update_prices({"AAPL": 155.0})
    print(f"✓ Price updated: AAPL @ $155.00")
    
    # Take snapshot
    snapshot = tracker.take_snapshot()
    print(f"✓ Snapshot taken: equity=${snapshot['total_equity']:,.2f}")
    
    # Get summary
    summary = tracker.get_summary()
    print(f"✓ Summary: {summary['position_count']} positions, {summary['trade_count']} trades")
    
    print("✅ Portfolio Tracker: PASSED\n")


def test_performance_calculator():
    """Test performance calculator"""
    print("\n=== Testing Performance Calculator ===")
    
    from portfolio.performance import PerformanceCalculator
    
    # Create sample snapshots
    snapshots = [
        {'date': '2026-01-01', 'total_equity': 100000},
        {'date': '2026-01-15', 'total_equity': 102000},
        {'date': '2026-02-01', 'total_equity': 98000},
        {'date': '2026-02-15', 'total_equity': 105000},
        {'date': '2026-03-01', 'total_equity': 110000},
    ]
    
    calc = PerformanceCalculator(snapshots)
    
    # Calculate metrics
    total_ret = calc.total_return()
    print(f"✓ Total return: {total_ret:.2f}%")
    assert total_ret == 10.0
    
    ann_ret = calc.annualized_return()
    print(f"✓ Annualized return: {ann_ret:.2f}%")
    
    sharpe = calc.sharpe_ratio()
    print(f"✓ Sharpe ratio: {sharpe:.2f}")
    
    max_dd = calc.max_drawdown()
    print(f"✓ Max drawdown: {max_dd:.2f}%")
    
    # Get all metrics
    metrics = calc.get_all_metrics()
    print(f"✓ All metrics calculated: {len(metrics)} metrics")
    
    print("✅ Performance Calculator: PASSED\n")


def test_risk_analyzer():
    """Test risk analyzer"""
    print("\n=== Testing Risk Analyzer ===")
    
    from portfolio.risk import RiskAnalyzer
    
    # Create sample snapshots
    snapshots = [
        {'date': '2026-01-01', 'total_equity': 100000},
        {'date': '2026-01-15', 'total_equity': 102000},
        {'date': '2026-02-01', 'total_equity': 98000},
        {'date': '2026-02-15', 'total_equity': 105000},
        {'date': '2026-03-01', 'total_equity': 110000},
    ]
    
    analyzer = RiskAnalyzer(snapshots)
    
    # Calculate VaR
    var_95 = analyzer.var(0.95)
    print(f"✓ VaR (95%): {var_95:.2f}%")
    
    # Calculate CVaR
    cvar_95 = analyzer.cvar(0.95)
    print(f"✓ CVaR (95%): {cvar_95:.2f}%")
    
    # Calculate beta
    beta = analyzer.beta()
    print(f"✓ Beta: {beta:.2f}")
    
    # Get risk summary
    positions = [
        {'market_value': 50000},
        {'market_value': 30000},
        {'market_value': 20000},
    ]
    
    summary = analyzer.get_risk_summary(positions)
    print(f"✓ Risk summary: {summary['risk_rating']} risk")
    print(f"  - Top 5 concentration: {summary['top_5_concentration']:.1f}%")
    print(f"  - Diversification score: {summary['diversification_score']:.2f}")
    
    print("✅ Risk Analyzer: PASSED\n")


def main():
    """Run all Phase 5 tests"""
    print("=" * 60)
    print("Phase 5: Portfolio & Trading Layer Tests")
    print("=" * 60)
    
    try:
        test_portfolio_models()
        test_portfolio_tracker()
        test_performance_calculator()
        test_risk_analyzer()
        
        print("=" * 60)
        print("🎉 ALL PHASE 5 TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
