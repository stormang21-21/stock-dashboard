import sys
sys.path.insert(0, '/root/.openclaw/workspace/daily_stock_analysis_v3')

# Test Phase 2 modules
print("Testing Phase 2 imports...")

try:
    from data.providers.base import BaseDataProvider, DataProviderRegistry, MarketType
    print("✓ Base provider imported")
    
    from data.providers.cn.akshare import AkShareProvider
    print("✓ AkShare provider imported")
    
    from data.providers.cn.efinance import EFinanceProvider
    print("✓ EFinance provider imported")
    
    from data.providers.us_hk.yfinance import YFinanceProvider
    print("✓ YFinance provider imported")
    
    from data.validators import DataValidator
    print("✓ Validator imported")
    
    from data.normalizers import DataNormalizer
    print("✓ Normalizer imported")
    
    from data.aggregator import DataAggregator
    print("✓ Aggregator imported")
    
    # Test provider registry
    providers = DataProviderRegistry.list_providers()
    print(f"\n✅ Registered providers: {providers}")
    
    print("\n🎉 Phase 2 imports successful!")
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
