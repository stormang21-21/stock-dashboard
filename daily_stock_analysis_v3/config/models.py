"""
Configuration Models

Pydantic models for type-safe configuration validation.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, HttpUrl, SecretStr
from enum import Enum


class LogLevel(str, Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """Database configuration"""
    
    url: str = Field(
        default="sqlite:///./data/stock_analysis.db",
        description="Database connection URL"
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL statements for debugging"
    )
    pool_size: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Database connection pool size"
    )
    max_overflow: int = Field(
        default=10,
        ge=0,
        le=20,
        description="Max overflow connections"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "url": "sqlite:///./data/stock_analysis.db",
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10
            }
        }


class CacheConfig(BaseModel):
    """Cache configuration"""
    
    enabled: bool = Field(
        default=True,
        description="Enable caching"
    )
    backend: str = Field(
        default="memory",
        description="Cache backend: memory or redis"
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL (if using redis backend)"
    )
    default_ttl: int = Field(
        default=300,
        ge=0,
        description="Default TTL in seconds"
    )
    max_size: int = Field(
        default=1000,
        ge=100,
        description="Max cache entries (memory backend)"
    )
    
    @validator('backend')
    def validate_backend(cls, v):
        if v not in ['memory', 'redis']:
            raise ValueError("Backend must be 'memory' or 'redis'")
        return v


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AIHUBMIX = "aihubmix"


class LLMConfig(BaseModel):
    """LLM/AI configuration"""
    
    provider: LLMProvider = Field(
        default=LLMProvider.GEMINI,
        description="LLM provider"
    )
    model: str = Field(
        default="gemini-2.0-flash",
        description="Model name"
    )
    api_key: Optional[SecretStr] = Field(
        default=None,
        description="API key (secret)"
    )
    base_url: Optional[HttpUrl] = Field(
        default=None,
        description="Custom API base URL"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=8192,
        ge=100,
        le=32000,
        description="Max tokens in response"
    )
    timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Request timeout in seconds"
    )
    retry_attempts: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Number of retry attempts"
    )
    
    class Config:
        use_enum_values = True


class APIConfig(BaseModel):
    """API server configuration"""
    
    host: str = Field(
        default="0.0.0.0",
        description="Server host"
    )
    port: int = Field(
        default=8081,
        ge=1,
        le=65535,
        description="Server port"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="API rate limit per minute"
    )
    enable_auth: bool = Field(
        default=True,
        description="Enable authentication"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "host": "0.0.0.0",
                "port": 8081,
                "debug": False,
                "cors_origins": ["*"],
                "rate_limit_per_minute": 60,
                "enable_auth": True
            }
        }


class NotificationChannel(str, Enum):
    """Notification channels"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationConfig(BaseModel):
    """Notification configuration"""
    
    enabled: bool = Field(
        default=False,
        description="Enable notifications"
    )
    channels: List[NotificationChannel] = Field(
        default=[],
        description="Enabled notification channels"
    )
    telegram_bot_token: Optional[SecretStr] = Field(
        default=None,
        description="Telegram bot token"
    )
    telegram_chat_id: Optional[str] = Field(
        default=None,
        description="Telegram chat ID"
    )
    discord_webhook_url: Optional[HttpUrl] = Field(
        default=None,
        description="Discord webhook URL"
    )
    email_smtp_server: Optional[str] = Field(
        default=None,
        description="SMTP server"
    )
    email_smtp_port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
        description="SMTP port"
    )
    email_sender: Optional[str] = Field(
        default=None,
        description="Sender email address"
    )
    email_password: Optional[SecretStr] = Field(
        default=None,
        description="Email password/app password"
    )
    
    @validator('channels')
    def validate_channels(cls, v, values):
        if v and not values.get('enabled'):
            raise ValueError("Cannot have channels when notifications are disabled")
        return v


class ReportLanguage(str, Enum):
    """Report output languages"""
    ZH = "zh"
    EN = "en"


class AnalysisConfig(BaseModel):
    """Analysis configuration"""
    
    report_language: ReportLanguage = Field(
        default=ReportLanguage.EN,
        description="Report output language"
    )
    report_type: str = Field(
        default="full",
        description="Report type: simple, full, brief"
    )
    max_workers: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Max concurrent analysis workers"
    )
    enable_news: bool = Field(
        default=True,
        description="Enable news search"
    )
    news_max_age_days: int = Field(
        default=3,
        ge=1,
        le=30,
        description="Max news age in days"
    )
    enable_chip_analysis: bool = Field(
        default=True,
        description="Enable chip distribution analysis"
    )
    bias_threshold: float = Field(
        default=5.0,
        ge=1.0,
        le=20.0,
        description="Bias ratio threshold (%)"
    )
