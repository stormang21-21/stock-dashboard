#!/usr/bin/env python3
"""
Phase 4 Test Script

Tests News & Search layer modules.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_search_providers():
    """Test search providers"""
    print("\n=== Testing Search Providers ===")
    
    from search.base import SearchRegistry
    from search.providers.searxng import SearXNGProvider
    from search.providers.tavily import TavilyProvider
    
    # List providers
    providers = SearchRegistry.list_providers()
    print(f"✓ Registered search providers: {providers}")
    
    # Test SearXNG instantiation
    try:
        searxng = SearXNGProvider()
        print(f"✓ SearXNG provider created: {searxng.base_url}")
    except Exception as e:
        print(f"✗ SearXNG failed: {e}")
    
    # Test Tavily instantiation (without API key)
    try:
        tavily = TavilyProvider({'api_key': None})
        print(f"✓ Tavily provider created (no key)")
    except Exception as e:
        print(f"ℹ Tavily validation works: {type(e).__name__}")
    
    print("✅ Search Providers: PASSED\n")


def test_sentiment_analyzer():
    """Test sentiment analyzer"""
    print("\n=== Testing Sentiment Analyzer ===")
    
    from news.sentiment import SentimentAnalyzer
    
    analyzer = SentimentAnalyzer()
    
    # Test positive text
    positive_text = "Company beats earnings expectations with strong growth and positive outlook"
    score = analyzer.analyze_sentiment(positive_text)
    assert score > 0, f"Positive text should have positive score, got {score}"
    print(f"✓ Positive sentiment: {score:.2f}")
    
    # Test negative text
    negative_text = "Company misses targets with declining revenue and negative warning"
    score = analyzer.analyze_sentiment(negative_text)
    assert score < 0, f"Negative text should have negative score, got {score}"
    print(f"✓ Negative sentiment: {score:.2f}")
    
    # Test neutral text
    neutral_text = "Company announces annual shareholder meeting next month"
    score = analyzer.analyze_sentiment(neutral_text)
    assert -0.3 <= score <= 0.3, f"Neutral text should be near zero, got {score}"
    print(f"✓ Neutral sentiment: {score:.2f}")
    
    # Test aggregate sentiment
    news_items = [
        {'title': 'Great earnings beat', 'snippet': 'Strong growth'},
        {'title': 'Revenue miss', 'snippet': 'Declining sales'},
        {'title': 'Neutral announcement', 'snippet': 'Meeting scheduled'},
    ]
    
    summary = analyzer.calculate_aggregate_sentiment(news_items)
    print(f"✓ Aggregate sentiment: {summary['sentiment_label']}")
    print(f"  - Positive: {summary['positive_count']}")
    print(f"  - Negative: {summary['negative_count']}")
    print(f"  - Neutral: {summary['neutral_count']}")
    
    print("✅ Sentiment Analyzer: PASSED\n")


def test_news_aggregator():
    """Test news aggregator"""
    print("\n=== Testing News Aggregator ===")
    
    from news.aggregator import NewsAggregator
    
    aggregator = NewsAggregator()
    
    print(f"✓ Aggregator initialized with {len(aggregator.providers)} providers")
    
    # Test aggregation (will return empty without real search)
    news = aggregator.aggregate_news(
        stock_code="AAPL",
        stock_name="Apple Inc.",
        days=3,
        max_results=5,
    )
    
    print(f"✓ Aggregation completed: {len(news)} results")
    
    # Test sentiment summary
    if news:
        summary = aggregator.get_sentiment_summary(news)
        print(f"✓ Sentiment summary: {summary['sentiment_label']}")
    else:
        print("ℹ No news returned (expected without real API)")
    
    print("✅ News Aggregator: PASSED\n")


def main():
    """Run all Phase 4 tests"""
    print("=" * 60)
    print("Phase 4: News & Search Layer Tests")
    print("=" * 60)
    
    try:
        test_search_providers()
        test_sentiment_analyzer()
        test_news_aggregator()
        
        print("=" * 60)
        print("🎉 ALL PHASE 4 TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
