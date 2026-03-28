import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

"""
Data Validators

Validate stock data for correctness and completeness.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, date
import re

from exceptions import DataValidationError
from loggers import get_logger

logger = get_logger(__name__)


class DataValidator:
    """
    Validates stock data.
    
    Checks:
    - Required fields present
    - Data types correct
    - Values in valid ranges
    - Symbol format valid
    """
    
    # Required fields for quote data
    REQUIRED_FIELDS = [
        'symbol',
        'name',
        'market',
        'currency',
        'timestamp',
        'open',
        'high',
        'low',
        'close',
        'volume',
    ]
    
    # Numeric fields that must be non-negative
    NON_NEGATIVE_FIELDS = [
        'open',
        'high',
        'low',
        'close',
        'volume',
        'amount',
    ]
    
    # Symbol patterns by market
    SYMBOL_PATTERNS = {
        'cn': r'^\d{6}$',  # 6 digits for A-shares
        'hk': r'^\d{4,5}$',  # 4-5 digits for HK
        'us': r'^[A-Z]{1,5}(\.[A-Z])?$',  # 1-5 letters for US
    }
    
    def __init__(self, strict: bool = False):
        """
        Initialize validator.
        
        Args:
            strict: If True, raise exceptions. If False, return validation results.
        """
        self.strict = strict
    
    def validate_quote(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate quote data.
        
        Args:
            data: Quote data dictionary
            
        Returns:
            Validation result with errors list
            
        Raises:
            DataValidationError: If strict mode and validation fails
        """
        errors = []
        
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # If missing required fields, return early
        if errors:
            if self.strict:
                raise DataValidationError(
                    message="Missing required fields",
                    field="multiple",
                    details={"missing_fields": errors},
                )
            return {"valid": False, "errors": errors}
        
        # Validate field types
        type_errors = self._validate_types(data)
        errors.extend(type_errors)
        
        # Validate numeric ranges
        range_errors = self._validate_ranges(data)
        errors.extend(range_errors)
        
        # Validate OHLC consistency
        ohlc_errors = self._validate_ohlc(data)
        errors.extend(ohlc_errors)
        
        # Validate symbol format
        symbol_errors = self._validate_symbol(data)
        errors.extend(symbol_errors)
        
        # Validate timestamp
        timestamp_errors = self._validate_timestamp(data)
        errors.extend(timestamp_errors)
        
        if errors:
            if self.strict:
                raise DataValidationError(
                    message="Data validation failed",
                    field="multiple",
                    details={"errors": errors},
                )
            return {"valid": False, "errors": errors}
        
        return {"valid": True, "errors": []}
    
    def _validate_types(self, data: Dict[str, Any]) -> List[str]:
        """Validate field types"""
        errors = []
        
        # String fields
        string_fields = ['symbol', 'name', 'currency', 'market']
        for field in string_fields:
            if field in data and not isinstance(data[field], str):
                errors.append(f"Field '{field}' must be string, got {type(data[field])}")
        
        # Numeric fields
        numeric_fields = ['open', 'high', 'low', 'close', 'volume']
        for field in numeric_fields:
            if field in data and not isinstance(data[field], (int, float)):
                errors.append(f"Field '{field}' must be numeric, got {type(data[field])}")
        
        # Timestamp
        if 'timestamp' in data:
            if not isinstance(data['timestamp'], (datetime, date)):
                errors.append(f"Field 'timestamp' must be datetime or date, got {type(data['timestamp'])}")
        
        return errors
    
    def _validate_ranges(self, data: Dict[str, Any]) -> List[str]:
        """Validate numeric ranges"""
        errors = []
        
        for field in self.NON_NEGATIVE_FIELDS:
            if field in data:
                value = data[field]
                if value is not None and value < 0:
                    errors.append(f"Field '{field}' must be non-negative, got {value}")
        
        return errors
    
    def _validate_ohlc(self, data: Dict[str, Any]) -> List[str]:
        """Validate OHLC consistency"""
        errors = []
        
        # High must be >= Low
        if 'high' in data and 'low' in data:
            if data['high'] < data['low']:
                errors.append(f"High ({data['high']}) must be >= Low ({data['low']})")
        
        # High must be >= Open and Close
        if 'high' in data and 'open' in data:
            if data['high'] < data['open']:
                errors.append(f"High ({data['high']}) must be >= Open ({data['open']})")
        
        if 'high' in data and 'close' in data:
            if data['high'] < data['close']:
                errors.append(f"High ({data['high']}) must be >= Close ({data['close']})")
        
        # Low must be <= Open and Close
        if 'low' in data and 'open' in data:
            if data['low'] > data['open']:
                errors.append(f"Low ({data['low']}) must be <= Open ({data['open']})")
        
        if 'low' in data and 'close' in data:
            if data['low'] > data['close']:
                errors.append(f"Low ({data['low']}) must be <= Close ({data['close']})")
        
        return errors
    
    def _validate_symbol(self, data: Dict[str, Any]) -> List[str]:
        """Validate symbol format"""
        errors = []
        
        if 'symbol' not in data:
            return errors
        
        symbol = data['symbol'].strip()
        market = data.get('market', '').lower()
        
        # Determine which pattern to use
        if 'cn' in market or 'a' in market:
            pattern = self.SYMBOL_PATTERNS['cn']
        elif 'hk' in market or 'hong' in market:
            pattern = self.SYMBOL_PATTERNS['hk']
        elif 'us' in market or 'usa' in market:
            pattern = self.SYMBOL_PATTERNS['us']
        else:
            # Try all patterns
            if not any(re.match(p, symbol) for p in self.SYMBOL_PATTERNS.values()):
                errors.append(f"Invalid symbol format: {symbol}")
            return errors
        
        if not re.match(pattern, symbol):
            errors.append(f"Symbol '{symbol}' doesn't match pattern for market '{market}'")
        
        return errors
    
    def _validate_timestamp(self, data: Dict[str, Any]) -> List[str]:
        """Validate timestamp"""
        errors = []
        
        if 'timestamp' not in data:
            return errors
        
        timestamp = data['timestamp']
        
        # Check if timestamp is not in the future
        now = datetime.now()
        if isinstance(timestamp, datetime) and timestamp > now:
            errors.append(f"Timestamp {timestamp} is in the future")
        
        # Check if timestamp is not too old (before 1990)
        if isinstance(timestamp, datetime) and timestamp.year < 1990:
            errors.append(f"Timestamp {timestamp} is too old")
        
        return errors
    
    def validate_batch(self, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate batch of data.
        
        Args:
            data_list: List of data dictionaries
            
        Returns:
            Validation summary
        """
        results = {
            "total": len(data_list),
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }
        
        for i, data in enumerate(data_list):
            result = self.validate_quote(data)
            
            if result["valid"]:
                results["valid"] += 1
            else:
                results["invalid"] += 1
                results["errors"].append({
                    "index": i,
                    "symbol": data.get('symbol', 'unknown'),
                    "errors": result["errors"],
                })
        
        results["success_rate"] = results["valid"] / results["total"] if results["total"] > 0 else 0
        
        return results
