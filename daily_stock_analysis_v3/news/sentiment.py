"""
Sentiment Analyzer

Analyze news sentiment for stocks.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """
    Analyze sentiment of news articles.
    
    Uses keyword-based analysis with LLM enhancement option.
    """
    
    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        'beat', 'exceed', 'surge', 'soar', 'jump', 'rally', 'gain', 'rise',
        'profit', 'growth', 'bullish', 'upgrade', 'outperform', 'buy',
        'record', 'strong', 'positive', 'optimistic', 'breakthrough',
        'approval', 'win', 'success', 'milestone', 'partnership',
    ]
    
    NEGATIVE_KEYWORDS = [
        'miss', 'fall', 'drop', 'plunge', 'crash', 'decline', 'loss',
        'bearish', 'downgrade', 'underperform', 'sell', 'weak', 'negative',
        'pessimistic', 'lawsuit', 'scandal', 'investigation', 'recall',
        'bankruptcy', 'layoff', 'warning', 'risk', 'concern',
    ]
    
    def __init__(self, llm_provider=None):
        """
        Initialize sentiment analyzer.
        
        Args:
            llm_provider: Optional LLM for enhanced analysis
        """
        self.llm = llm_provider
        self.use_llm = llm_provider is not None
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment score (-1.0 to 1.0)
            - Negative: -1.0 to -0.3
            - Neutral: -0.3 to 0.3
            - Positive: 0.3 to 1.0
        """
        if not text:
            return 0.0
        
        # Use LLM if available
        if self.use_llm:
            return self._analyze_with_llm(text)
        
        # Use keyword-based analysis
        return self._analyze_with_keywords(text)
    
    def _analyze_with_keywords(self, text: str) -> float:
        """Keyword-based sentiment analysis"""
        text_lower = text.lower()
        
        # Count positive and negative keywords
        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text_lower)
        
        total = positive_count + negative_count
        
        if total == 0:
            return 0.0  # Neutral
        
        # Calculate score
        score = (positive_count - negative_count) / total
        
        return max(-1.0, min(1.0, score))
    
    def _analyze_with_llm(self, text: str) -> float:
        """LLM-enhanced sentiment analysis"""
        try:
            prompt = f"""Analyze the sentiment of this financial news text.

Text: {text[:1000]}  # Truncate to avoid token limits

Rate sentiment from -1.0 (very negative) to 1.0 (very positive).
Respond with only a number between -1.0 and 1.0."""
            
            response = self.llm.generate(prompt)
            
            # Extract number from response
            numbers = re.findall(r'[-+]?\d*\.?\d+', response)
            if numbers:
                score = float(numbers[0])
                return max(-1.0, min(1.0, score))
            
            return 0.0
            
        except Exception as e:
            logger.error(f"LLM sentiment analysis failed: {e}")
            # Fallback to keyword analysis
            return self._analyze_with_keywords(text)
    
    def analyze_multiple(self, texts: List[str]) -> Dict[str, float]:
        """
        Analyze sentiment of multiple texts.
        
        Args:
            texts: List of texts
            
        Returns:
            Dictionary of sentiment scores
        """
        results = {}
        for i, text in enumerate(texts):
            results[f'text_{i}'] = self.analyze_sentiment(text)
        return results
    
    def calculate_aggregate_sentiment(
        self,
        news_items: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate aggregate sentiment from multiple news items.
        
        Args:
            news_items: List of news items with 'title' and 'snippet' fields
            
        Returns:
            Aggregate sentiment analysis
        """
        if not news_items:
            return {
                'overall_sentiment': 0.0,
                'sentiment_label': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'articles_analyzed': 0,
            }
        
        # Analyze each article
        sentiments = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for item in news_items:
            text = f"{item.get('title', '')} {item.get('snippet', '')}"
            score = self.analyze_sentiment(text)
            sentiments.append(score)
            
            if score > 0.3:
                positive_count += 1
            elif score < -0.3:
                negative_count += 1
            else:
                neutral_count += 1
        
        # Calculate aggregate
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0.0
        
        # Determine label
        if avg_sentiment > 0.3:
            label = 'positive'
        elif avg_sentiment < -0.3:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'overall_sentiment': round(avg_sentiment, 3),
            'sentiment_label': label,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'articles_analyzed': len(news_items),
            'sentiment_distribution': {
                'positive': positive_count / len(news_items) if news_items else 0,
                'negative': negative_count / len(news_items) if news_items else 0,
                'neutral': neutral_count / len(news_items) if news_items else 0,
            },
        }
