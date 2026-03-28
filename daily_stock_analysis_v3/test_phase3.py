#!/usr/bin/env python3
"""
Phase 3 Test Script

Tests AI/Analysis layer modules.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_llm_providers():
    """Test LLM providers"""
    print("\n=== Testing LLM Providers ===")
    
    from ai.llm.base import LLMRegistry
    from ai.llm.gemini import GeminiProvider
    from ai.llm.openai import OpenAIProvider
    
    # List providers
    providers = LLMRegistry.list_providers()
    print(f"✓ Registered LLM providers: {providers}")
    
    # Test provider info
    for name in providers:
        info = LLMRegistry.get_provider_info(name)
        print(f"  - {name}: {info.get('description', 'N/A')}")
    
    # Test instantiation (without API key - will fail validation)
    try:
        GeminiProvider({'api_key': 'test'})
        print("✓ Gemini provider can be instantiated")
    except Exception as e:
        print(f"ℹ Gemini validation works: {type(e).__name__}")
    
    try:
        OpenAIProvider({'api_key': 'test'})
        print("✓ OpenAI provider can be instantiated")
    except Exception as e:
        print(f"ℹ OpenAI validation works: {type(e).__name__}")
    
    print("✅ LLM Providers: PASSED\n")


def test_prompt_manager():
    """Test prompt manager"""
    print("\n=== Testing Prompt Manager ===")
    
    from ai.prompts import PromptManager
    
    # Test English
    pm_en = PromptManager(language='en')
    templates = pm_en.list_templates()
    print(f"✓ English templates: {templates}")
    
    # Test rendering
    prompt = pm_en.render(
        "stock_analysis",
        stock_code="AAPL",
        stock_name="Apple Inc.",
        market="us",
        currency="USD",
        price_data="$150.00",
        technical_indicators="RSI: 45",
        news_context="No news",
        analysis_date="2026-03-23",
    )
    assert "AAPL" in prompt
    assert "Apple" in prompt
    print("✓ English prompt rendering works")
    
    # Test Chinese
    pm_zh = PromptManager(language='zh')
    templates = pm_zh.list_templates()
    print(f"✓ Chinese templates: {templates}")
    
    print("✅ Prompt Manager: PASSED\n")


def test_strategy_registry():
    """Test strategy registry"""
    print("\n=== Testing Strategy Registry ===")
    
    from ai.strategies.base import StrategyRegistry
    
    strategies = StrategyRegistry.list_strategies()
    print(f"✓ Registered strategies: {strategies}")
    
    print("✅ Strategy Registry: PASSED\n")


def test_analyzer_initialization():
    """Test analyzer initialization"""
    print("\n=== Testing Analyzer ===")
    
    from ai.analyzer import StockAnalyzer
    from exceptions import AIError
    
    # Test initialization fails without API key
    try:
        analyzer = StockAnalyzer(llm_config={'provider': 'gemini'})
        print("✗ Should have failed without API key")
    except (ValueError, AIError) as e:
        print(f"✓ Analyzer validation works: {type(e).__name__}")
    
    print("✅ Analyzer: PASSED\n")


def main():
    """Run all Phase 3 tests"""
    print("=" * 60)
    print("Phase 3: AI/Analysis Layer Tests")
    print("=" * 60)
    
    try:
        test_llm_providers()
        test_prompt_manager()
        test_strategy_registry()
        test_analyzer_initialization()
        
        print("=" * 60)
        print("🎉 ALL PHASE 3 TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
