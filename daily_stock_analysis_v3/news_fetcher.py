"""
Real-Time News Fetcher

Fetches real-time news for stocks from multiple sources.
"""

from typing import List, Dict, Any
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch real-time stock news"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_news(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch news for a stock symbol"""
        news_articles = []
        
        # Try Yahoo Finance first
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            if news:
                for item in news[:limit]:
                    title = item.get('title', '')
                    if title and title != 'No title':
                        article = {
                            'title': title,
                            'source': 'Yahoo Finance',
                            'url': item.get('link', ''),
                            'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)).strftime('%Y-%m-%d %H:%M') if item.get('providerPublishTime') else datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'thumbnail': '',
                        }
                        news_articles.append(article)
        except Exception as e:
            logger.debug(f"Yahoo Finance news failed: {e}")
        
        # If Yahoo failed, try Google News RSS
        if not news_articles:
            try:
                rss_url = f'https://news.google.com/rss/search?q={symbol}+stock+OR+{symbol}+stock+news&hl=en-US&gl=US&ceid=US:en'
                response = self.session.get(rss_url, timeout=5)
                
                if response.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    
                    for item in root.findall('.//item')[:limit]:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        pubdate_elem = item.find('pubDate')
                        
                        if title_elem is not None:
                            article = {
                                'title': title_elem.text or 'No title',
                                'source': 'Google News',
                                'url': link_elem.text if link_elem is not None else '',
                                'published': pubdate_elem.text if pubdate_elem is not None else datetime.now().strftime('%Y-%m-%d %H:%M'),
                                'thumbnail': '',
                            }
                            news_articles.append(article)
            except Exception as e:
                logger.debug(f"Google News failed: {e}")
        
        # Fallback if no news found
        if not news_articles:
            news_articles = [{
                'title': f'No recent news available for {symbol}. Check financial news sources for latest updates.',
                'source': 'System',
                'url': f'https://finance.yahoo.com/quote/{symbol}',
                'published': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'thumbnail': '',
            }]
        
        return news_articles[:limit]
    
    def analyze_sentiment(self, title: str) -> str:
        """Simple sentiment analysis"""
        if not title:
            return 'neutral'
            
        title_lower = title.lower()
        
        positive_words = ['beat', 'surge', 'soar', 'jump', 'rally', 'gain', 'rise', 'profit', 'growth', 'bullish', 'upgrade', 'outperform', 'record', 'strong', 'positive', 'optimistic', 'breakthrough', 'win', 'success', 'hits', 'high', 'new']
        negative_words = ['miss', 'fall', 'drop', 'plunge', 'crash', 'decline', 'loss', 'bearish', 'downgrade', 'underperform', 'sell', 'weak', 'negative', 'pessimistic', 'lawsuit', 'scandal', 'investigation', 'bankruptcy', 'layoff', 'warning', 'risk', 'concern', 'fail', 'cuts', 'low']
        
        positive_count = sum(1 for word in positive_words if word in title_lower)
        negative_count = sum(1 for word in negative_words if word in title_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'


news_fetcher = NewsFetcher()


def get_stock_news(symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Get news for a stock symbol with sentiment"""
    articles = news_fetcher.fetch_news(symbol, limit)
    for article in articles:
        article['sentiment'] = news_fetcher.analyze_sentiment(article['title'])
    return articles


if __name__ == "__main__":
    # Test
    print("Testing AAPL news...")
    news = get_stock_news("AAPL", 3)
    for article in news:
        print(f"• {article['title'][:60]}... ({article['sentiment']}) - {article['source']}")
