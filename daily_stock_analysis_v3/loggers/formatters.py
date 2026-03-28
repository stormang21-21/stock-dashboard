"""
Log Formatters

Different formatters for different output destinations.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any


class ConsoleFormatter(logging.Formatter):
    """Colorized console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m',
    }
    
    FORMAT = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def format(self, record):
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
        result = super().format(record)
        record.levelname = levelname
        return result
    
    def __init__(self):
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


class FileFormatter(logging.Formatter):
    """Detailed file formatter"""
    
    FORMAT = "%(asctime)s - %(levelname)s - %(name)s.%(funcName)s:%(lineno)d - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    def __init__(self):
        super().__init__(fmt=self.FORMAT, datefmt=self.DATE_FORMAT)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
            "module": record.module,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)
