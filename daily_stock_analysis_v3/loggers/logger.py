"""
Logger Setup

Central logging configuration.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, List

from .handlers import (
    get_console_handler,
    get_file_handler,
    get_json_handler,
)
from .formatters import ConsoleFormatter


logger = logging.getLogger("daily_stock_analysis")


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    enable_json: bool = False,
    json_log_file: Optional[str] = None,
    console: bool = True,
) -> logging.Logger:
    """Configure logging"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    
    if console:
        console_handler = get_console_handler(level)
        root_logger.addHandler(console_handler)
    
    if log_file:
        file_handler = get_file_handler(log_file, level)
        root_logger.addHandler(file_handler)
    
    if enable_json and json_log_file:
        json_handler = get_json_handler(json_log_file, level)
        root_logger.addHandler(json_handler)
    
    root_logger.info(f"Logging initialized (level={logging.getLevelName(level)})")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)
