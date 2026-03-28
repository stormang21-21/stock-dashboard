"""
TradingView Indicators

Technical indicator calculations (TradingView-style).
"""

from typing import List, Dict, Any, Optional
import math
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Calculate technical indicators (TradingView-style).
    
    Implements popular indicators used in TradingView.
    """
    
    @staticmethod
    def sma(prices: List[float], period: int = 20) -> List[float]:
        """
        Simple Moving Average.
        
        Args:
            prices: List of prices
            period: SMA period
            
        Returns:
            List of SMA values
        """
        if len(prices) < period:
            return []
        
        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i-period+1:i+1]) / period
            sma_values.append(sma)
        
        return sma_values
    
    @staticmethod
    def ema(prices: List[float], period: int = 20) -> List[float]:
        """
        Exponential Moving Average.
        
        Args:
            prices: List of prices
            period: EMA period
            
        Returns:
            List of EMA values
        """
        if len(prices) < period:
            return []
        
        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]  # Start with SMA
        
        for price in prices[period:]:
            ema = (price - ema_values[-1]) * multiplier + ema_values[-1]
            ema_values.append(ema)
        
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """
        Relative Strength Index.
        
        Args:
            prices: List of prices
            period: RSI period
            
        Returns:
            List of RSI values (0-100)
        """
        if len(prices) < period + 1:
            return []
        
        rsi_values = []
        gains = []
        losses = []
        
        # Calculate price changes
        for i in range(1, len(prices)):
            change = prices[i] - prices[i-1]
            gains.append(max(0, change))
            losses.append(max(0, -change))
        
        # Initial average gain/loss
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        # Calculate RSI
        for i in range(period - 1, len(gains)):
            if i > period - 1:
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            
            rsi_values.append(rsi)
        
        return rsi_values
    
    @staticmethod
    def macd(
        prices: List[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Dict[str, List[float]]:
        """
        MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: List of prices
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            signal_period: Signal line period
            
        Returns:
            Dictionary with macd, signal, histogram lists
        """
        if len(prices) < slow_period + signal_period:
            return {'macd': [], 'signal': [], 'histogram': []}
        
        # Calculate EMAs
        fast_ema = TechnicalIndicators.ema(prices, fast_period)
        slow_ema = TechnicalIndicators.ema(prices, slow_period)
        
        # Align lengths
        min_len = min(len(fast_ema), len(slow_ema))
        fast_ema = fast_ema[-min_len:]
        slow_ema = slow_ema[-min_len:]
        
        # MACD line
        macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
        
        # Signal line (EMA of MACD)
        signal_line = TechnicalIndicators.ema(macd_line, signal_period)
        
        # Histogram
        min_len = min(len(macd_line), len(signal_line))
        histogram = [m - s for m, s in zip(macd_line[-min_len:], signal_line[-min_len:])]
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram,
        }
    
    @staticmethod
    def bollinger_bands(
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Dict[str, List[float]]:
        """
        Bollinger Bands.
        
        Args:
            prices: List of prices
            period: SMA period
            std_dev: Standard deviation multiplier
            
        Returns:
            Dictionary with upper, middle, lower band lists
        """
        if len(prices) < period:
            return {'upper': [], 'middle': [], 'lower': []}
        
        sma = TechnicalIndicators.sma(prices, period)
        
        upper = []
        lower = []
        
        for i in range(len(sma)):
            # Calculate standard deviation
            start_idx = i * (len(prices) // len(sma))
            window = prices[start_idx:start_idx + period]
            
            if len(window) == period:
                mean = sum(window) / period
                variance = sum((x - mean) ** 2 for x in window) / period
                std = math.sqrt(variance)
                
                upper.append(sma[i] + (std_dev * std))
                lower.append(sma[i] - (std_dev * std))
            else:
                upper.append(sma[i])
                lower.append(sma[i])
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower,
        }
    
    @staticmethod
    def stochastic(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        k_period: int = 14,
        d_period: int = 3,
    ) -> Dict[str, List[float]]:
        """
        Stochastic Oscillator.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            k_period: %K period
            d_period: %D period
            
        Returns:
            Dictionary with k and d lists
        """
        if len(closes) < k_period:
            return {'k': [], 'd': []}
        
        k_values = []
        
        for i in range(k_period - 1, len(closes)):
            highest_high = max(highs[i-k_period+1:i+1])
            lowest_low = min(lows[i-k_period+1:i+1])
            
            if highest_high == lowest_low:
                k = 50
            else:
                k = ((closes[i] - lowest_low) / (highest_high - lowest_low)) * 100
            
            k_values.append(k)
        
        # %D is SMA of %K
        d_values = TechnicalIndicators.sma(k_values, d_period)
        
        return {
            'k': k_values,
            'd': d_values,
        }
    
    @staticmethod
    def atr(
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> List[float]:
        """
        Average True Range (ATR).
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            period: ATR period
            
        Returns:
            List of ATR values
        """
        if len(closes) < period + 1:
            return []
        
        true_ranges = []
        
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            true_ranges.append(max(tr1, tr2, tr3))
        
        # Initial ATR
        atr_values = [sum(true_ranges[:period]) / period]
        
        # Wilder's smoothing
        for tr in true_ranges[period:]:
            atr = (atr_values[-1] * (period - 1) + tr) / period
            atr_values.append(atr)
        
        return atr_values
    
    @staticmethod
    def ichimoku_cloud(
        highs: List[float],
        lows: List[float],
        closes: List[float],
    ) -> Dict[str, List[float]]:
        """
        Ichimoku Cloud.
        
        Args:
            highs: List of high prices
            lows: List of low prices
            closes: List of close prices
            
        Returns:
            Dictionary with tenkan, kijun, senkou_a, senkou_b, chikou lists
        """
        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        tenkan_period = 9
        tenkan = []
        
        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        kijun_period = 26
        kijun = []
        
        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        senkou_b_period = 52
        senkou_b = []
        
        min_periods = max(tenkan_period, kijun_period, senkou_b_period)
        
        if len(closes) < min_periods:
            return {
                'tenkan': [],
                'kijun': [],
                'senkou_a': [],
                'senkou_b': [],
                'chikou': [],
            }
        
        for i in range(min_periods - 1, len(closes)):
            # Tenkan
            if i >= tenkan_period - 1:
                high_9 = max(highs[i-tenkan_period+1:i+1])
                low_9 = min(lows[i-tenkan_period+1:i+1])
                tenkan.append((high_9 + low_9) / 2)
            
            # Kijun
            if i >= kijun_period - 1:
                high_26 = max(highs[i-kijun_period+1:i+1])
                low_26 = min(lows[i-kijun_period+1:i+1])
                kijun.append((high_26 + low_26) / 2)
            
            # Senkou B
            if i >= senkou_b_period - 1:
                high_52 = max(highs[i-senkou_b_period+1:i+1])
                low_52 = min(lows[i-senkou_b_period+1:i+1])
                senkou_b.append((high_52 + low_52) / 2)
        
        # Senkou Span A: (Tenkan + Kijun)/2
        min_len = min(len(tenkan), len(kijun))
        senkou_a = [(t + k) / 2 for t, k in zip(tenkan[-min_len:], kijun[-min_len:])]
        
        # Chikou Span: Close shifted back 26 periods
        chikou = closes[:-kijun_period] if len(closes) > kijun_period else []
        
        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou,
        }
    
    @staticmethod
    def get_all_indicators(
        prices: List[float],
        highs: Optional[List[float]] = None,
        lows: Optional[List[float]] = None,
        volumes: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Calculate all major indicators.
        
        Args:
            prices: List of close prices
            highs: List of high prices (optional)
            lows: List of low prices (optional)
            volumes: List of volumes (optional)
            
        Returns:
            Dictionary of all calculated indicators
        """
        indicators = {
            'sma_20': TechnicalIndicators.sma(prices, 20),
            'sma_50': TechnicalIndicators.sma(prices, 50),
            'sma_200': TechnicalIndicators.sma(prices, 200),
            'ema_10': TechnicalIndicators.ema(prices, 10),
            'ema_20': TechnicalIndicators.ema(prices, 20),
            'ema_50': TechnicalIndicators.ema(prices, 50),
            'rsi_14': TechnicalIndicators.rsi(prices, 14),
            'macd': TechnicalIndicators.macd(prices),
            'bollinger': TechnicalIndicators.bollinger_bands(prices),
        }
        
        # Indicators requiring OHLC
        if highs and lows:
            indicators['stochastic'] = TechnicalIndicators.stochastic(highs, lows, prices)
            indicators['atr'] = TechnicalIndicators.atr(highs, lows, prices)
            indicators['ichimoku'] = TechnicalIndicators.ichimoku_cloud(highs, lows, prices)
        
        return indicators
