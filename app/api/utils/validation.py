"""
Enhanced validation utilities for API requests.

This module provides additional validation functions beyond basic Pydantic validation
to ensure request data is valid for the MA Cross analysis.
"""

import re
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass

from app.api.models.ma_cross import MACrossRequest


@dataclass
class ValidationError:
    """Represents a validation error with field and message."""
    field: str
    message: str
    value: Any


class RequestValidator:
    """Enhanced validator for MA Cross requests."""
    
    # Valid ticker patterns
    TICKER_PATTERN = re.compile(r'^[A-Z0-9\-\.=]+$')
    CRYPTO_PATTERN = re.compile(r'^[A-Z0-9]+-USD$')
    SYNTHETIC_PATTERN = re.compile(r'^[A-Z0-9]+_[A-Z0-9]+$')
    
    # Known exchanges and suffixes
    VALID_SUFFIXES = ['-USD', '=F', '.TO', '.L', '.HK', '.T']
    
    # Reasonable limits
    MAX_TICKERS = 50
    MAX_YEARS = 20
    MIN_WINDOW = 2
    MAX_WINDOW = 200
    MIN_PERCENTAGE = 0.0
    MAX_PERCENTAGE = 1.0
    
    @classmethod
    def validate_request(cls, request: MACrossRequest) -> List[ValidationError]:
        """
        Perform comprehensive validation of MA Cross request.
        
        Args:
            request: MACrossRequest object to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate tickers
        errors.extend(cls._validate_tickers(request.ticker, request.tickers))
        
        # Validate synthetic pair configuration
        errors.extend(cls._validate_synthetic_pairs(request))
        
        # Validate time periods
        errors.extend(cls._validate_time_periods(request))
        
        # Validate moving average windows
        errors.extend(cls._validate_ma_windows(request))
        
        # Validate percentage fields
        errors.extend(cls._validate_percentages(request))
        
        # Validate minimum criteria
        if request.minimum_criteria:
            errors.extend(cls._validate_minimum_criteria(request.minimum_criteria))
        
        return errors
    
    @classmethod
    def _validate_tickers(cls, primary_ticker: str, additional_tickers: Optional[List[str]]) -> List[ValidationError]:
        """Validate ticker symbols."""
        errors = []
        
        # Collect all tickers
        all_tickers = [primary_ticker]
        if additional_tickers:
            all_tickers.extend(additional_tickers)
        
        # Check total count
        if len(all_tickers) > cls.MAX_TICKERS:
            errors.append(ValidationError(
                field="tickers",
                message=f"Too many tickers ({len(all_tickers)}). Maximum allowed: {cls.MAX_TICKERS}",
                value=len(all_tickers)
            ))
        
        # Validate each ticker
        for i, ticker in enumerate(all_tickers):
            field = "ticker" if i == 0 else f"tickers[{i-1}]"
            errors.extend(cls._validate_single_ticker(ticker, field))
        
        # Check for duplicates
        unique_tickers = set(all_tickers)
        if len(unique_tickers) != len(all_tickers):
            duplicates = [t for t in all_tickers if all_tickers.count(t) > 1]
            errors.append(ValidationError(
                field="tickers",
                message=f"Duplicate tickers found: {list(set(duplicates))}",
                value=duplicates
            ))
        
        return errors
    
    @classmethod
    def _validate_single_ticker(cls, ticker: str, field: str) -> List[ValidationError]:
        """Validate a single ticker symbol."""
        errors = []
        
        if not ticker:
            errors.append(ValidationError(
                field=field,
                message="Ticker cannot be empty",
                value=ticker
            ))
            return errors
        
        if len(ticker) > 20:
            errors.append(ValidationError(
                field=field,
                message=f"Ticker too long ({len(ticker)} chars). Maximum: 20",
                value=ticker
            ))
        
        if not cls.TICKER_PATTERN.match(ticker):
            errors.append(ValidationError(
                field=field,
                message=f"Invalid ticker format: {ticker}. Use uppercase letters, numbers, hyphens, dots, and equals only",
                value=ticker
            ))
        
        # Validate specific patterns
        if '_' in ticker and not cls.SYNTHETIC_PATTERN.match(ticker):
            errors.append(ValidationError(
                field=field,
                message=f"Invalid synthetic pair format: {ticker}. Use format: SYMBOL1_SYMBOL2",
                value=ticker
            ))
        
        return errors
    
    @classmethod
    def _validate_synthetic_pairs(cls, request: MACrossRequest) -> List[ValidationError]:
        """Validate synthetic pair configuration."""
        errors = []
        
        has_synthetic = any('_' in t for t in [request.ticker] + (request.tickers or []))
        has_ticker_1 = bool(request.ticker_1)
        has_ticker_2 = bool(request.ticker_2)
        
        if has_synthetic and (not has_ticker_1 or not has_ticker_2):
            errors.append(ValidationError(
                field="synthetic_pairs",
                message="Synthetic pairs require both TICKER_1 and TICKER_2 to be specified",
                value={"ticker_1": request.ticker_1, "ticker_2": request.ticker_2}
            ))
        
        if (has_ticker_1 or has_ticker_2) and not has_synthetic:
            errors.append(ValidationError(
                field="synthetic_pairs",
                message="TICKER_1 and TICKER_2 can only be used with synthetic pair tickers (containing '_')",
                value={"ticker_1": request.ticker_1, "ticker_2": request.ticker_2}
            ))
        
        # Validate individual synthetic ticker symbols
        if has_ticker_1:
            errors.extend(cls._validate_single_ticker(request.ticker_1, "ticker_1"))
        if has_ticker_2:
            errors.extend(cls._validate_single_ticker(request.ticker_2, "ticker_2"))
        
        return errors
    
    @classmethod
    def _validate_time_periods(cls, request: MACrossRequest) -> List[ValidationError]:
        """Validate time period settings."""
        errors = []
        
        if request.years < 0 or request.years > cls.MAX_YEARS:
            errors.append(ValidationError(
                field="years",
                message=f"Years must be between 0 and {cls.MAX_YEARS}",
                value=request.years
            ))
        
        if request.use_hourly and request.years > 2:
            errors.append(ValidationError(
                field="years",
                message="Hourly data analysis limited to 2 years maximum",
                value=request.years
            ))
        
        return errors
    
    @classmethod
    def _validate_ma_windows(cls, request: MACrossRequest) -> List[ValidationError]:
        """Validate moving average window sizes."""
        errors = []
        
        if request.short_window < cls.MIN_WINDOW or request.short_window > cls.MAX_WINDOW:
            errors.append(ValidationError(
                field="short_window",
                message=f"Short window must be between {cls.MIN_WINDOW} and {cls.MAX_WINDOW}",
                value=request.short_window
            ))
        
        if request.long_window < cls.MIN_WINDOW or request.long_window > cls.MAX_WINDOW:
            errors.append(ValidationError(
                field="long_window",
                message=f"Long window must be between {cls.MIN_WINDOW} and {cls.MAX_WINDOW}",
                value=request.long_window
            ))
        
        if request.short_window >= request.long_window:
            errors.append(ValidationError(
                field="ma_windows",
                message=f"Short window ({request.short_window}) must be less than long window ({request.long_window})",
                value={"short": request.short_window, "long": request.long_window}
            ))
        
        return errors
    
    @classmethod
    def _validate_percentages(cls, request: MACrossRequest) -> List[ValidationError]:
        """Validate percentage fields."""
        errors = []
        
        percentage_fields = [
            ("allocation_pct", request.allocation_pct),
            ("stop_loss_pct", request.stop_loss_pct)
        ]
        
        for field_name, value in percentage_fields:
            if value is not None:
                if value < cls.MIN_PERCENTAGE or value > cls.MAX_PERCENTAGE:
                    errors.append(ValidationError(
                        field=field_name,
                        message=f"{field_name} must be between {cls.MIN_PERCENTAGE} and {cls.MAX_PERCENTAGE}",
                        value=value
                    ))
        
        return errors
    
    @classmethod
    def _validate_minimum_criteria(cls, criteria) -> List[ValidationError]:
        """Validate minimum criteria settings."""
        errors = []
        
        # Validate percentage ranges
        percentage_fields = [
            ("win_rate", criteria.WIN_RATE),
            ("profit_factor", criteria.PROFIT_FACTOR),
            ("sharpe_ratio", criteria.SHARPE_RATIO)
        ]
        
        for field_name, value in percentage_fields:
            if value is not None and field_name == "win_rate":
                if value < 0.0 or value > 1.0:
                    errors.append(ValidationError(
                        field=f"minimum_criteria.{field_name}",
                        message=f"{field_name} must be between 0.0 and 1.0",
                        value=value
                    ))
            elif value is not None and value < 0:
                errors.append(ValidationError(
                    field=f"minimum_criteria.{field_name}",
                    message=f"{field_name} must be non-negative",
                    value=value
                ))
        
        # Validate count fields
        count_fields = [
            ("total_trades", criteria.TOTAL_TRADES),
            ("months", criteria.MONTHS)
        ]
        
        for field_name, value in count_fields:
            if value is not None and value < 0:
                errors.append(ValidationError(
                    field=f"minimum_criteria.{field_name}",
                    message=f"{field_name} must be non-negative",
                    value=value
                ))
        
        return errors


def format_validation_errors(errors: List[ValidationError]) -> Dict[str, Any]:
    """
    Format validation errors for API response.
    
    Args:
        errors: List of validation errors
        
    Returns:
        Formatted error response
    """
    return {
        "error": "validation_failed",
        "message": f"Request validation failed with {len(errors)} error(s)",
        "details": [
            {
                "field": error.field,
                "message": error.message,
                "invalid_value": error.value
            }
            for error in errors
        ]
    }


def validate_ma_cross_request(request: MACrossRequest) -> Optional[Dict[str, Any]]:
    """
    Validate MA Cross request and return formatted errors if any.
    
    Args:
        request: MACrossRequest to validate
        
    Returns:
        None if valid, error dict if invalid
    """
    errors = RequestValidator.validate_request(request)
    
    if errors:
        return format_validation_errors(errors)
    
    return None