"""
Log Handlers

Handlers for different output destinations.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler as StdRotatingFileHandler
from logging.handlers import TimedRotatingFileHandler as StdTimedRotatingFileHandler
from typing import Optional

from .formatters import ConsoleFormatter, FileFormatter, JSONFormatter


def get_console_handler(
    level: int = logging.INFO,
) -> logging.StreamHandler:
    """
    Create a console handler with colorized output.
    
    Args:
        level: Minimum log level
        
    Returns:
        Configured StreamHandler
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(ConsoleFormatter())
    return handler


def get_file_handler(
    log_file: str,
    level: int = logging.DEBUG,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> StdRotatingFileHandler:
    """
    Create a rotating file handler.
    
    Args:
        log_file: Path to log file
        level: Minimum log level
        max_bytes: Max file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured RotatingFileHandler
    """
    # Ensure directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    handler = StdRotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
    )
    handler.setLevel(level)
    handler.setFormatter(FileFormatter())
    return handler


def get_json_handler(
    log_file: str,
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> StdRotatingFileHandler:
    """
    Create a JSON file handler for structured logging.
    
    Args:
        log_file: Path to log file
        level: Minimum log level
        max_bytes: Max file size before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Configured RotatingFileHandler with JSON formatter
    """
    # Ensure directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    handler = StdRotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8',
    )
    handler.setLevel(level)
    handler.setFormatter(JSONFormatter())
    return handler


def get_timed_file_handler(
    log_file: str,
    level: int = logging.DEBUG,
    when: str = 'midnight',
    interval: int = 1,
    backup_count: int = 7,
) -> StdTimedRotatingFileHandler:
    """
    Create a time-based rotating file handler.
    
    Args:
        log_file: Path to log file
        level: Minimum log level
        when: When to rotate ('midnight', 'h', 'm', 's', 'w0'-'w6')
        interval: Rotation interval
        backup_count: Number of backup files to keep
        
    Returns:
        Configured TimedRotatingFileHandler
    """
    # Ensure directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    handler = StdTimedRotatingFileHandler(
        log_file,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding='utf-8',
    )
    handler.setLevel(level)
    handler.setFormatter(FileFormatter())
    handler.suffix = "%Y-%m-%d"
    return handler
