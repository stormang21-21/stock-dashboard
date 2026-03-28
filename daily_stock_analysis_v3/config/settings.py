"""
Settings Manager

Loads configuration from environment variables and .env files.
Provides singleton access to settings throughout the application.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from functools import lru_cache
from dotenv import load_dotenv

from .models import (
    DatabaseConfig,
    CacheConfig,
    LLMConfig,
    LLMProvider,
    APIConfig,
    NotificationConfig,
    AnalysisConfig,
    ReportLanguage,
    LogLevel,
)


class Settings:
    """
    Main settings class that aggregates all configuration.
    
    Loads from:
    1. Environment variables (highest priority)
    2. .env file
    3. Default values (lowest priority)
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize settings.
        
        Args:
            env_file: Path to .env file (default: .env in project root)
        """
        # Load .env file
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in project root
            project_root = Path(__file__).parent.parent
            env_path = project_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)
        
        # Application settings
        self.app_name: str = os.getenv("APP_NAME", "Daily Stock Analysis")
        self.version: str = os.getenv("APP_VERSION", "3.0.0-alpha")
        self.debug: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level: LogLevel = LogLevel(os.getenv("LOG_LEVEL", "INFO"))
        
        # Load sub-configurations
        self.database = self._load_database_config()
        self.cache = self._load_cache_config()
        self.llm = self._load_llm_config()
        self.api = self._load_api_config()
        self.notification = self._load_notification_config()
        self.analysis = self._load_analysis_config()
        
        # Stock list
        self.stock_list: list[str] = self._load_stock_list()
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            url=os.getenv("DATABASE_URL", "sqlite:///./data/stock_analysis.db"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
        )
    
    def _load_cache_config(self) -> CacheConfig:
        """Load cache configuration"""
        return CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            backend=os.getenv("CACHE_BACKEND", "memory"),
            redis_url=os.getenv("REDIS_URL"),
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "300")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "1000")),
        )
    
    def _load_llm_config(self) -> LLMConfig:
        """Load LLM configuration"""
        provider_str = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        # Map provider string to enum
        provider_map = {
            "gemini": LLMProvider.GEMINI,
            "openai": LLMProvider.OPENAI,
            "deepseek": LLMProvider.DEEPSEEK,
            "anthropic": LLMProvider.ANTHROPIC,
            "ollama": LLMProvider.OLLAMA,
            "aihubmix": LLMProvider.AIHUBMIX,
        }
        provider = provider_map.get(provider_str, LLMProvider.GEMINI)
        
        # Get API key from environment or specific provider env
        api_key = (
            os.getenv("GEMINI_API_KEY") or
            os.getenv("OPENAI_API_KEY") or
            os.getenv("DEEPSEEK_API_KEY") or
            os.getenv("ANTHROPIC_API_KEY") or
            os.getenv("AIHUBMIX_KEY")
        )
        
        return LLMConfig(
            provider=provider,
            model=os.getenv("LLM_MODEL", "gemini-2.0-flash"),
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "8192")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("LLM_RETRY_ATTEMPTS", "3")),
        )
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration"""
        cors_origins = os.getenv("API_CORS_ORIGINS", "*")
        return APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8081")),
            debug=self.debug,
            cors_origins=[origin.strip() for origin in cors_origins.split(",")],
            rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT", "60")),
            enable_auth=os.getenv("API_ENABLE_AUTH", "true").lower() == "true",
        )
    
    def _load_notification_config(self) -> NotificationConfig:
        """Load notification configuration"""
        channels_str = os.getenv("NOTIFICATION_CHANNELS", "")
        channels = []
        if channels_str:
            from .models import NotificationChannel
            for channel in channels_str.split(","):
                channel = channel.strip().lower()
                try:
                    channels.append(NotificationChannel(channel))
                except ValueError:
                    pass  # Skip invalid channels
        
        return NotificationConfig(
            enabled=os.getenv("NOTIFICATION_ENABLED", "false").lower() == "true",
            channels=channels,
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            email_smtp_server=os.getenv("EMAIL_SMTP_SERVER"),
            email_smtp_port=int(os.getenv("EMAIL_SMTP_PORT", "587")) if os.getenv("EMAIL_SMTP_PORT") else None,
            email_sender=os.getenv("EMAIL_SENDER"),
            email_password=os.getenv("EMAIL_PASSWORD"),
        )
    
    def _load_analysis_config(self) -> AnalysisConfig:
        """Load analysis configuration"""
        return AnalysisConfig(
            report_language=ReportLanguage(os.getenv("REPORT_LANGUAGE", "en")),
            report_type=os.getenv("REPORT_TYPE", "full"),
            max_workers=int(os.getenv("ANALYSIS_MAX_WORKERS", "3")),
            enable_news=os.getenv("ANALYSIS_ENABLE_NEWS", "true").lower() == "true",
            news_max_age_days=int(os.getenv("ANALYSIS_NEWS_MAX_AGE_DAYS", "3")),
            enable_chip_analysis=os.getenv("ANALYSIS_ENABLE_CHIP", "true").lower() == "true",
            bias_threshold=float(os.getenv("ANALYSIS_BIAS_THRESHOLD", "5.0")),
        )
    
    def _load_stock_list(self) -> list[str]:
        """Load stock list from environment"""
        stock_list_str = os.getenv("STOCK_LIST", "")
        if not stock_list_str:
            return []
        return [stock.strip() for stock in stock_list_str.split(",") if stock.strip()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (for debugging)"""
        return {
            "app": {
                "name": self.app_name,
                "version": self.version,
                "debug": self.debug,
                "log_level": self.log_level.value,
            },
            "database": self.database.dict(),
            "cache": self.cache.dict(),
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "api_key": "***" if self.llm.api_key else None,
                "temperature": self.llm.temperature,
            },
            "api": self.api.dict(),
            "notification": {
                "enabled": self.notification.enabled,
                "channels": [c.value for c in self.notification.channels],
            },
            "analysis": self.analysis.dict(),
            "stock_list": self.stock_list,
        }
    
    def __repr__(self) -> str:
        return f"Settings(app={self.app_name}, version={self.version}, debug={self.debug})"


# Singleton instance
_settings: Optional[Settings] = None


def get_settings(env_file: Optional[str] = None) -> Settings:
    """
    Get settings singleton.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings(env_file=env_file)
    return _settings


# Convenience access
settings: Settings = get_settings()


# For testing - reset singleton
def reset_settings() -> None:
    """Reset settings singleton (for testing)"""
    global _settings
    _settings = None
