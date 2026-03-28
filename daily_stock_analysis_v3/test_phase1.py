#!/usr/bin/env python3
"""
Phase 1 Test Script

Tests all foundation modules:
- Config system
- Logging system
- Exceptions
- Database layer
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_config():
    """Test configuration system"""
    print("\n=== Testing Config System ===")
    
    from config import settings, get_settings
    
    # Test settings loaded
    assert settings.app_name == "Daily Stock Analysis"
    assert settings.version == "3.0.0-alpha"
    print(f"✓ App: {settings.app_name} v{settings.version}")
    
    # Test database config
    assert settings.database.url is not None
    print(f"✓ Database: {settings.database.url}")
    
    # Test LLM config
    assert settings.llm.provider is not None
    print(f"✓ LLM: {settings.llm.provider}/{settings.llm.model}")
    
    # Test API config
    assert settings.api.port > 0
    print(f"✓ API: {settings.api.host}:{settings.api.port}")
    
    # Test to_dict
    config_dict = settings.to_dict()
    assert "app" in config_dict
    assert "database" in config_dict
    print("✓ Config serialization works")
    
    print("✅ Config System: PASSED\n")


def test_logging():
    """Test logging system"""
    print("\n=== Testing Logging System ===")
    
    from loggers import get_logger, setup_logging
    
    # Test logger creation
    logger = get_logger("test")
    assert logger is not None
    print("✓ Logger created")
    
    # Test logging
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    print("✓ Logging works")
    
    # Test setup_logging
    setup_logging(level="DEBUG", console=True)
    print("✓ Logging setup works")
    
    print("✅ Logging System: PASSED\n")


def test_exceptions():
    """Test exception hierarchy"""
    print("\n=== Testing Exceptions ===")
    
    from exceptions import (
        BaseException,
        ConfigurationError,
        ValidationError,
        NotFoundError,
        DataFetchError,
        LLMError,
        APIError,
    )
    
    # Test base exception
    try:
        raise BaseException("Test error", code="TEST")
    except BaseException as e:
        assert e.message == "Test error"
        assert e.code == "TEST"
        print("✓ Base exception works")
    
    # Test config error
    try:
        raise ConfigurationError("Missing config", config_key="API_KEY")
    except ConfigurationError as e:
        assert e.details.get("config_key") == "API_KEY"
        print("✓ Configuration error works")
    
    # Test validation error
    try:
        raise ValidationError("Invalid value", field="price", value=-100)
    except ValidationError as e:
        assert e.details.get("field") == "price"
        print("✓ Validation error works")
    
    # Test data fetch error
    try:
        raise DataFetchError("API failed", source="Yahoo", status_code=500)
    except DataFetchError as e:
        assert e.details.get("source") == "Yahoo"
        print("✓ Data fetch error works")
    
    # Test LLM error
    try:
        raise LLMError("Token limit", model="gpt-4", provider="openai")
    except LLMError as e:
        assert e.details.get("model") == "gpt-4"
        print("✓ LLM error works")
    
    # Test API error
    try:
        raise APIError("Server error", status_code=500)
    except APIError as e:
        assert e.status_code == 500
        print("✓ API error works")
    
    print("✅ Exceptions: PASSED\n")


def test_database():
    """Test database layer"""
    print("\n=== Testing Database Layer ===")
    
    from database import get_engine, init_db, close_db, get_db
    from database.models import Base
    
    # Test engine creation
    engine = get_engine()
    assert engine is not None
    print("✓ Engine created")
    
    # Test init_db
    init_db()
    print("✓ Database initialized")
    
    # Test session
    with get_db() as session:
        assert session is not None
        print("✓ Session works")
    
    # Test close
    close_db()
    print("✓ Database closed")
    
    print("✅ Database Layer: PASSED\n")


def main():
    """Run all Phase 1 tests"""
    print("=" * 60)
    print("Phase 1: Foundation Tests")
    print("=" * 60)
    
    try:
        test_config()
        test_logging()
        test_exceptions()
        test_database()
        
        print("=" * 60)
        print("🎉 ALL PHASE 1 TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
