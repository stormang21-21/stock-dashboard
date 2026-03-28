"""
Prompt Manager

Template management, variable substitution, and localization.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class PromptTemplate:
    """Prompt template with variables"""
    
    def __init__(self, name: str, template: str, variables: Optional[List[str]] = None):
        self.name = name
        self.template = template
        self.variables = variables or []
    
    def render(self, **kwargs) -> str:
        """Render template with variables"""
        result = self.template
        
        # Replace variables
        for var in self.variables:
            value = kwargs.get(var, f"{{{var}}}")
            result = result.replace(f"{{{var}}}", str(value))
        
        return result


class PromptManager:
    """
    Manages prompt templates for stock analysis.
    
    Features:
    - Template storage and retrieval
    - Variable substitution
    - Multi-language support
    - Version control
    """
    
    def __init__(self, language: str = 'en'):
        """
        Initialize prompt manager.
        
        Args:
            language: Default language ('en' or 'zh')
        """
        self.language = language
        self.templates: Dict[str, PromptTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self) -> None:
        """Load default analysis templates"""
        
        # Stock Analysis Prompt
        self.register_template(
            name="stock_analysis",
            template=self._get_stock_analysis_template(),
            variables=[
                "stock_code", "stock_name", "market", "currency",
                "price_data", "technical_indicators", "news_context",
                "analysis_date",
            ],
        )
        
        # Decision Dashboard Prompt
        self.register_template(
            name="decision_dashboard",
            template=self._get_decision_dashboard_template(),
            variables=[
                "stock_info", "technical_data", "news_summary",
                "risk_factors", "language",
            ],
        )
        
        # Strategy Selection Prompt
        self.register_template(
            name="strategy_selection",
            template=self._get_strategy_template(),
            variables=["stock_data", "market_condition", "available_strategies"],
        )
    
    def _get_stock_analysis_template(self) -> str:
        """Get stock analysis prompt template"""
        if self.language == 'zh':
            return """分析股票 {stock_code} ({stock_name})

## 基础信息
- 代码：{stock_code}
- 名称：{stock_name}
- 市场：{market}
- 货币：{currency}
- 日期：{analysis_date}

## 技术数据
{technical_indicators}

## 价格数据
{price_data}

## 相关资讯
{news_context}

请提供详细的分析报告，包括趋势判断、操作建议和风险提示。"""
        else:
            return """Analyze stock {stock_code} ({stock_name})

## Basic Information
- Code: {stock_code}
- Name: {stock_name}
- Market: {market}
- Currency: {currency}
- Date: {analysis_date}

## Technical Data
{technical_indicators}

## Price Data
{price_data}

## Related News
{news_context}

Please provide a detailed analysis report including trend judgment, action recommendations, and risk warnings."""
    
    def _get_decision_dashboard_template(self) -> str:
        """Get decision dashboard prompt"""
        return """You are a professional stock analyst. Generate a decision dashboard in JSON format.

## Input Data
{stock_info}

## Technical Indicators
{technical_data}

## News Summary
{news_summary}

## Risk Factors
{risk_factors}

## Output Requirements
- Language: {language}
- Format: JSON
- Include: core conclusion, action levels, stop loss, take profit targets
- Be specific with price points
- Use ✅/⚠️/❌ for checklist items

Respond with JSON only."""
    
    def _get_strategy_template(self) -> str:
        """Get strategy selection prompt"""
        return """Select the best trading strategy for this market condition.

## Stock Data
{stock_data}

## Market Condition
{market_condition}

## Available Strategies
{available_strategies}

Choose the most appropriate strategy and explain why."""
    
    def register_template(self, name: str, template: str, variables: Optional[List[str]] = None) -> None:
        """
        Register a prompt template.
        
        Args:
            name: Template name
            template: Template string with {variables}
            variables: List of variable names
        """
        self.templates[name] = PromptTemplate(name, template, variables)
        logger.debug(f"Registered template: {name}")
    
    def get_template(self, name: str) -> PromptTemplate:
        """
        Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            PromptTemplate
            
        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            available = list(self.templates.keys())
            raise KeyError(f"Template '{name}' not found. Available: {available}")
        
        return self.templates[name]
    
    def render(self, name: str, **kwargs) -> str:
        """
        Render template with variables.
        
        Args:
            name: Template name
            **kwargs: Variable values
            
        Returns:
            Rendered prompt
        """
        template = self.get_template(name)
        return template.render(**kwargs)
    
    def set_language(self, language: str) -> None:
        """
        Set prompt language.
        
        Args:
            language: Language code ('en' or 'zh')
        """
        self.language = language
        logger.info(f"Prompt language set to: {language}")
        self._load_default_templates()  # Reload templates in new language
    
    def list_templates(self) -> List[str]:
        """List all registered templates"""
        return list(self.templates.keys())
