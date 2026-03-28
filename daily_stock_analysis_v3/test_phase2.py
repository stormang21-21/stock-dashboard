#!/usr/bin/env python3
"""
Phase 2 Test Script

Tests data layer modules:
- Data providers
- Validators
- Normalizers
- Aggregator
"""

import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_providers():
    """Test data providers"""
    print("\n=== Testing Data Providers ===")
    
    from data.providers import DataProviderRegistry
    from data.providers.base import MarketType
    
    # List providers
    providers = DataProviderRegistry.list_providers()
    print(f"✓ Registered providers: {providers}")
    
    # Check CN providers
    cn_providers = DataProviderRegistry.get_providers_for_market(MarketType.CN)
    print(f"✓ CN market providers: {cn_providers}")
    
    # Check US providers
    us_providers = DataProviderRegistry.get_providers_for_market(MarketType.US)
    print(f"✓ US market providers: {us_providers}")
    
    # Test provider instantiation
    if 'akshare' in providers:
        provider = DataProviderRegistry.get_provider('akshare')
        assert provider is not None
        print(f"✓ AkShare provider created: {provider}")
    
    if 'efinance' in providers:
        provider = DataProviderRegistry.get_provider('efinance')
        assert provider is not None
        print(f"✓ Efinance provider created: {provider}")
    
    if 'yfinance' in providers:
        provider = DataProviderRegistry.get_provider('yfinance')
        assert provider is not None
        print(f"✓ YFinance provider created: {provider}")
    
    print("✅ Data Providers: PASSED\n")


def test_validator():
    """Test data validator"""
    print("\n=== Testing Data Validator ===")
    
    from data.validators import DataValidator
    
    validator = DataValidator(strict=False)
    
    # Test valid data
    valid_data = {
        'symbol': '600519',
        'name': 'Kweichow Moutai',
        'market': 'cn',
        'currency': 'CNY',
        'timestamp': date.today(),
        'open': 1400.0,
        'high': 1420.0,
        'low': 1390.0,
        'close': 1410.0,
        'volume': 1000000,
    }
    
    result = validator.validate_quote(valid_data)
    assert result['valid'], f"Valid data failed validation: {result['errors']}"
    print("✓ Valid data passes validation")
    
    # Test missing field
    invalid_data = valid_data.copy()
    del invalid_data['close']
    
    result = validator.validate_quote(invalid_data)
    assert not result['valid'], "Missing field should fail validation"
    print("✓ Missing field detected")
    
    # Test invalid OHLC
    invalid_ohlc = valid_data.copy()
    invalid_ohlc['high'] = 1300.0  # High < Low
    
    result = validator.validate_quote(invalid_ohlc)
    assert not result['valid'], "Invalid OHLC should fail validation"
    print("✓ OHLC validation works")
    
    # Test batch validation
    batch_result = validator.validate_batch([valid_data, invalid_data])
    assert batch_result['valid'] == 1
    assert batch_result['invalid'] == 1
    print(f"✓ Batch validation: {batch_result['valid']}/{batch_result['total']} valid")
    
    print("✅ Data Validator: PASSED\n")


def test_normalizer():
    """Test data normalizer"""
    print("\n=== Testing Data Normalizer ===")
    
    from data.normalizers import DataNormalizer
    
    normalizer = DataNormalizer(target_currency='CNY')
    
    # Test AkShare data normalization
    akshare_data = {
        '日期': '2026-03-23',
        '开盘': 1400.0,
        '最高': 1420.0,
        '最低': 1390.0,
        '收盘': 1410.0,
        '成交量': 1000000,
        '成交额': 1410000000.0,
    }
    
    normalized = normalizer.normalize_quote(akshare_data, source='akshare_cn')
    
    assert 'timestamp' in normalized
    assert 'open' in normalized
    assert 'close' in normalized
    assert normalized['open'] == 1400.0
    assert normalized['close'] == 1410.0
    print("✓ AkShare data normalized correctly")
    
    # Test YFinance data normalization
    yf_data = {
        'Open': 250.0,
        'High': 255.0,
        'Low': 248.0,
        'Close': 252.0,
        'Volume': 5000000,
    }
    
    normalized = normalizer.normalize_quote(yf_data, source='yfinance')
    
    assert normalized['open'] == 250.0
    assert normalized['close'] == 252.0
    print("✓ YFinance data normalized correctly")
    
    print("✅ Data Normalizer: PASSED\n")


def test_aggregator():
    """Test data aggregator"""
    print("\n=== Testing Data Aggregator ===")
    
    from data.aggregator import DataAggregator
    from data.providers.base import MarketType
    
    # Create aggregator
    aggregator = DataAggregator(
        providers=['akshare', 'efinance', 'yfinance'],
        cache_enabled=True,
        cache_ttl=300,
    )
    
    # Get provider stats
    stats = aggregator.get_provider_stats()
    print(f"✓ Aggregator initialized with {len(stats['providers'])} providers")
    print(f"✓ Cache enabled: {stats['cache_enabled']}")
    
    # Test provider priority
    provider_names = [p['name'] for p in stats['providers']]
    print(f"✓ Provider order: {provider_names}")
    
    # Note: Actual data fetching tests require network access and installed packages
    # These would be integration tests
    print("ℹ️  Note: Live data fetching requires installed packages and network")
    
    print("✅ Data Aggregator: PASSED\n")


def main():
    """Run all Phase 2 tests"""
    print("=" * 60)
    print("Phase 2: Data Layer Tests")
    print("=" * 60)
    
    try:
        test_providers()
        test_validator()
        test_normalizer()
        test_aggregator()
        
        print("=" * 60)
        print("🎉 ALL PHASE 2 TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
