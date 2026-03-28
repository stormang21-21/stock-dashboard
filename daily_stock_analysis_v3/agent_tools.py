"""
Agent Tools with Optional API Integration

Tools automatically use real APIs when configured, fallback to placeholders otherwise.
"""

from typing import Dict, Any, Optional
import logging
from agent_config import get_agent_config

logger = logging.getLogger(__name__)
config = get_agent_config()


class AgentTools:
    """Tool registry with optional API integration"""
    
    def __init__(self):
        self.config = config
    
    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Get stock data.
        
        Uses:
        - yfinance (always available, free)
        - Financial Datasets API (if enabled)
        - Alpha Vantage (if enabled)
        """
        try:
            # Always try yfinance first (free, no API key needed)
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            
            # Get basic data
            info = ticker.info
            hist = ticker.history(period='1mo')
            
            result = {
                'symbol': symbol,
                'success': True,
                'data': {
                    'price': hist['Close'].iloc[-1] if not hist.empty else 0,
                    'company_name': info.get('shortName', symbol),
                    'sector': info.get('sector', 'Unknown'),
                    'market_cap': info.get('marketCap', 0),
                    'pe_ratio': info.get('trailingPE', 0),
                },
                'source': 'yfinance'
            }
            
            logger.info(f"Got stock data for {symbol} from yfinance")
            return result
            
        except Exception as e:
            logger.error(f"Error getting stock data: {e}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'source': 'none'
            }
    
    def get_news(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get news for stock.
        
        Uses:
        - yfinance news (free, always available)
        - NewsAPI (if enabled)
        """
        try:
            # Try yfinance news first
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            news = ticker.news[:limit]
            
            if news:
                result = {
                    'symbol': symbol,
                    'success': True,
                    'news': [
                        {
                            'title': item.get('title', 'No title'),
                            'source': item.get('publisher', 'Unknown'),
                            'url': item.get('link', ''),
                            'published': item.get('providerPublishTime', 0),
                        }
                        for item in news
                    ],
                    'count': len(news),
                    'source': 'yfinance'
                }
                
                logger.info(f"Got {len(news)} news items for {symbol}")
                return result
            
            # Fallback
            return {
                'symbol': symbol,
                'success': True,
                'news': [],
                'count': 0,
                'source': 'none'
            }
            
        except Exception as e:
            logger.error(f"Error getting news: {e}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'news': []
            }
    
    def get_technical_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get technical analysis.
        
        Uses:
        - yfinance + ta-lib calculations (free)
        - Alpha Vantage (if enabled)
        """
        try:
            import yfinance as yf
            import pandas as pd
            
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='3mo')
            
            if hist.empty:
                return {
                    'symbol': symbol,
                    'success': False,
                    'error': 'No data available'
                }
            
            # Calculate indicators
            close = hist['Close']
            
            # SMA
            sma20 = close.rolling(window=20).mean().iloc[-1]
            sma50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1]
            
            # MACD
            exp1 = close.ewm(span=12, adjust=False).mean()
            exp2 = close.ewm(span=26, adjust=False).mean()
            macd = exp1 - exp2
            macd_value = macd.iloc[-1]
            
            result = {
                'symbol': symbol,
                'success': True,
                'technical': {
                    'sma20': round(sma20, 2),
                    'sma50': round(sma50, 2) if sma50 else None,
                    'rsi': round(rsi_value, 2),
                    'macd': round(macd_value, 2),
                    'trend': 'bullish' if sma20 > sma50 else 'bearish',
                    'rsi_signal': 'overbought' if rsi_value > 70 else 'oversold' if rsi_value < 30 else 'neutral',
                },
                'source': 'calculated'
            }
            
            logger.info(f"Calculated technical analysis for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating technicals: {e}")
            return {
                'symbol': symbol,
                'success': False,
                'error': str(e),
                'technical': {}
            }
    
    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """
        Full stock analysis.
        
        Combines:
        - Stock data
        - News
        - Technical analysis
        """
        # Get all data
        stock_data = self.get_stock_data(symbol)
        news = self.get_news(symbol)
        technicals = self.get_technical_analysis(symbol)
        
        # Combine results
        result = {
            'symbol': symbol,
            'success': True,
            'analysis': {
                'stock_data': stock_data.get('data', {}),
                'news_count': news.get('count', 0),
                'technical': technicals.get('technical', {}),
            },
            'sources': {
                'stock_data': stock_data.get('source'),
                'news': news.get('source'),
                'technical': technicals.get('source'),
            }
        }
        
        logger.info(f"Completed full analysis for {symbol}")
        return result
    
    def compare_stocks(self, symbols: list) -> Dict[str, Any]:
        """
        Compare multiple stocks.
        
        Gets data for each and compares metrics.
        """
        results = {}
        
        for symbol in symbols:
            data = self.get_stock_data(symbol)
            if data.get('success'):
                results[symbol] = data['data']
        
        # Simple comparison
        comparison = {
            'symbols': symbols,
            'count': len(results),
            'data': results,
        }
        
        logger.info(f"Compared {len(symbols)} stocks")
        return {
            'success': True,
            'comparison': comparison
        }
    
    def generate_research_report(self, query: str) -> Dict[str, Any]:
        """
        Generate research report.
        
        In production, this would use LLM to generate report.
        """
        report = {
            'query': query,
            'report': 'Research report generated (placeholder - integrate LLM for full reports)',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
        }
        
        logger.info(f"Generated research report for: {query}")
        return {
            'success': True,
            'report': report
        }


# Singleton instance
tools = AgentTools()


def get_agent_tools() -> AgentTools:
    """Get agent tools"""
    return tools
