"""
Stock Analyzer

Core analysis engine using LLM for stock analysis.
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime
import logging
import json

logger = logging.getLogger(__name__)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ai.llm.base import LLMProvider, LLMRegistry
from ai.prompts import PromptManager
from data.providers.base import QuoteData, MarketType
from exceptions import AIError, AnalysisError


class AnalysisResult:
    """Structured analysis result"""
    
    def __init__(
        self,
        stock_code: str,
        stock_name: str,
        analysis_date: date,
        sentiment_score: int,
        trend_prediction: str,
        operation_advice: str,
        decision_type: str,  # buy/hold/sell
        confidence_level: str,  # high/medium/low
        dashboard: Dict[str, Any],
        summary: str,
        model_used: str,
    ):
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.analysis_date = analysis_date
        self.sentiment_score = sentiment_score
        self.trend_prediction = trend_prediction
        self.operation_advice = operation_advice
        self.decision_type = decision_type
        self.confidence_level = confidence_level
        self.dashboard = dashboard
        self.summary = summary
        self.model_used = model_used
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'analysis_date': self.analysis_date.isoformat(),
            'sentiment_score': self.sentiment_score,
            'trend_prediction': self.trend_prediction,
            'operation_advice': self.operation_advice,
            'decision_type': self.decision_type,
            'confidence_level': self.confidence_level,
            'dashboard': self.dashboard,
            'summary': self.summary,
            'model_used': self.model_used,
        }


class StockAnalyzer:
    """
    Main stock analysis engine.
    
    Uses LLM to analyze stock data and generate trading recommendations.
    """
    
    # Analysis schema for JSON output
    DECISION_SCHEMA = {
        "type": "object",
        "properties": {
            "sentiment_score": {"type": "integer", "minimum": 0, "maximum": 100},
            "trend_prediction": {"type": "string", "enum": ["strong_bullish", "bullish", "sideways", "bearish", "strong_bearish"]},
            "operation_advice": {"type": "string"},
            "decision_type": {"type": "string", "enum": ["buy", "hold", "sell"]},
            "confidence_level": {"type": "string", "enum": ["high", "medium", "low"]},
            "dashboard": {
                "type": "object",
                "properties": {
                    "core_conclusion": {"type": "object"},
                    "data_perspective": {"type": "object"},
                    "intelligence": {"type": "object"},
                    "battle_plan": {"type": "object"},
                }
            },
            "summary": {"type": "string"},
        },
        "required": ["sentiment_score", "trend_prediction", "operation_advice", "decision_type", "dashboard"],
    }
    
    def __init__(
        self,
        llm_provider: Optional[LLMProvider] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        language: str = 'en',
    ):
        """
        Initialize analyzer.
        
        Args:
            llm_provider: LLM provider instance
            llm_config: LLM configuration (if creating provider)
            language: Analysis language ('en' or 'zh')
        """
        # Initialize LLM
        if llm_provider:
            self.llm = llm_provider
        elif llm_config:
            provider_name = llm_config.get('provider', 'gemini')
            self.llm = LLMRegistry.get_provider(provider_name, llm_config)
        else:
            raise ValueError("Either llm_provider or llm_config must be provided")
        
        # Initialize prompt manager
        self.prompt_manager = PromptManager(language=language)
        
        self.language = language
        logger.info(f"StockAnalyzer initialized (model={self.llm.model}, language={language})")
    
    def analyze(
        self,
        stock_code: str,
        stock_name: str,
        quotes: List[QuoteData],
        news: Optional[List[Dict[str, Any]]] = None,
        technical_indicators: Optional[Dict[str, Any]] = None,
        analysis_date: Optional[date] = None,
    ) -> AnalysisResult:
        """
        Analyze stock and generate recommendations.
        
        Args:
            stock_code: Stock symbol
            stock_name: Stock name
            quotes: Historical quote data
            news: Related news articles
            technical_indicators: Technical analysis data
            analysis_date: Analysis date
            
        Returns:
            AnalysisResult object
        """
        try:
            # Prepare analysis data
            analysis_date = analysis_date or date.today()
            
            # Build prompt
            prompt = self._build_analysis_prompt(
                stock_code=stock_code,
                stock_name=stock_name,
                quotes=quotes,
                news=news,
                technical_indicators=technical_indicators,
                analysis_date=analysis_date,
            )
            
            # Generate analysis with LLM
            logger.info(f"Analyzing {stock_code} with {self.llm.model}")
            
            result_json = self.llm.generate_json(
                prompt=prompt,
                schema=self.DECISION_SCHEMA,
                system_prompt=self._get_system_prompt(),
            )
            
            # Parse result
            analysis_result = self._parse_result(
                stock_code=stock_code,
                stock_name=stock_name,
                result_json=result_json,
                analysis_date=analysis_date,
            )
            
            logger.info(f"Analysis complete for {stock_code}: {analysis_result.decision_type}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Analysis failed for {stock_code}: {e}")
            raise AnalysisError(
                message=str(e),
                stock_code=stock_code,
                analysis_type='llm_analysis',
            )
    
    def _build_analysis_prompt(
        self,
        stock_code: str,
        stock_name: str,
        quotes: List[QuoteData],
        news: Optional[List[Dict[str, Any]]],
        technical_indicators: Optional[Dict[str, Any]],
        analysis_date: date,
    ) -> str:
        """Build analysis prompt from data"""
        
        # Format price data
        if quotes:
            latest = quotes[-1]
            price_data = f"""
Current Price: {latest.close} {latest.currency}
Open: {latest.open}
High: {latest.high}
Low: {latest.low}
Volume: {latest.volume}
Date: {latest.timestamp.date()}
"""
            if len(quotes) > 1:
                prev = quotes[-2]
                change = ((latest.close - prev.close) / prev.close) * 100
                price_data += f"Change: {change:+.2f}%"
        else:
            price_data = "No price data available"
        
        # Format technical indicators
        tech_data = technical_indicators or {}
        technical_text = json.dumps(tech_data, indent=2) if tech_data else "No technical data"
        
        # Format news
        news_text = "No news"
        if news:
            news_text = "\n".join([f"- {n.get('title', 'No title')}" for n in news[:5]])
        
        # Render prompt
        prompt = self.prompt_manager.render(
            "stock_analysis",
            stock_code=stock_code,
            stock_name=stock_name,
            market=quotes[-1].market.value if quotes else "unknown",
            currency=quotes[-1].currency if quotes else "unknown",
            price_data=price_data,
            technical_indicators=technical_text,
            news_context=news_text,
            analysis_date=analysis_date.isoformat(),
        )
        
        return prompt
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for analysis"""
        if self.language == 'zh':
            return """你是一位专业的股票分析师，专注于趋势交易。

请生成专业的投资决策仪表盘，包括:
1. 核心结论（一句话说明该买/卖/等）
2. 精确的买入/卖出价位
3. 止损和目标价位
4. 检查清单（用✅/⚠️/❌标记）
5. 风险评估

只输出JSON，不要其他内容。"""
        else:
            return """You are a professional stock analyst specializing in trend trading.

Generate a professional investment decision dashboard including:
1. Core conclusion (one sentence: buy/sell/wait)
2. Precise entry/exit price levels
3. Stop loss and take profit targets
4. Action checklist (use ✅/⚠️/❌)
5. Risk assessment

Output JSON only, no other content."""
    
    def _parse_result(
        self,
        stock_code: str,
        stock_name: str,
        result_json: Dict[str, Any],
        analysis_date: date,
    ) -> AnalysisResult:
        """Parse LLM result into AnalysisResult"""
        
        return AnalysisResult(
            stock_code=stock_code,
            stock_name=stock_name,
            analysis_date=analysis_date,
            sentiment_score=result_json.get('sentiment_score', 50),
            trend_prediction=result_json.get('trend_prediction', 'sideways'),
            operation_advice=result_json.get('operation_advice', 'Hold'),
            decision_type=result_json.get('decision_type', 'hold'),
            confidence_level=result_json.get('confidence_level', 'medium'),
            dashboard=result_json.get('dashboard', {}),
            summary=result_json.get('summary', ''),
            model_used=self.llm.model,
        )
