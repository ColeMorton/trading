"""
Enhanced validation utilities for API requests.

This module provides additional validation functions beyond basic Pydantic validation
to ensure request data is valid for the MA Cross analysis.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.api.models.strategy_analysis import MACrossRequest


@dataclass
class ValidationError:
    """Represents a validation error with field and message."""

    field: str
    message: str
    value: Any


class RequestValidator:
    """Enhanced validator for MA Cross requests."""

    # Valid ticker patterns
    TICKER_PATTERN = re.compile(r"^[A-Z0-9\-\.=]+$")
    CRYPTO_PATTERN = re.compile(r"^[A-Z0-9]+-USD$")
    SYNTHETIC_PATTERN = re.compile(r"^[A-Z0-9]+_[A-Z0-9]+$")

    # Known exchanges and suffixes
    VALID_SUFFIXES = ["-USD", "=F", ".TO", ".L", ".HK", ".T"]

    # Reasonable limits
    MAX_TICKERS = 50
    MAX_YEARS = 20
    MIN_WINDOW = 2
    MAX_WINDOW = 200

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
        additional_tickers = request.tickers if hasattr(request, "tickers") else None
        errors.extend(cls._validate_tickers(request.ticker, additional_tickers))

        # Validate synthetic pair configuration
        errors.extend(cls._validate_synthetic_pairs(request))

        # Validate time periods
        errors.extend(cls._validate_time_periods(request))

        # Validate minimum criteria if provided
        if hasattr(request, "minimums") and request.minimums:
            errors.extend(cls._validate_minimum_criteria(request.minimums))

        return errors

    @classmethod
    def _validate_tickers(
        cls, primary_ticker, additional_tickers: Optional[List[str]]
    ) -> List[ValidationError]:
        """Validate ticker symbols."""
        errors = []

        # Collect all tickers
        all_tickers = []

        # Handle primary_ticker which can be string or list
        if isinstance(primary_ticker, str):
            all_tickers.append(primary_ticker)
        elif isinstance(primary_ticker, list):
            all_tickers.extend(primary_ticker)
        else:
            errors.append(
                ValidationError(
                    field="ticker",
                    message=f"Invalid ticker type: {type(primary_ticker).__name__}. Expected string or list",
                    value=primary_ticker,
                )
            )
            return errors

        if additional_tickers:
            all_tickers.extend(additional_tickers)

        # Check total count
        if len(all_tickers) > cls.MAX_TICKERS:
            errors.append(
                ValidationError(
                    field="tickers",
                    message=f"Too many tickers ({len(all_tickers)}). Maximum allowed: {cls.MAX_TICKERS}",
                    value=len(all_tickers),
                )
            )

        # Validate each ticker
        for i, ticker in enumerate(all_tickers):
            if isinstance(primary_ticker, list) and i < len(primary_ticker):
                field = f"ticker[{i}]"
            elif i == 0:
                field = "ticker"
            else:
                field = f"tickers[{i-1}]"
            errors.extend(cls._validate_single_ticker(ticker, field))

        # Check for duplicates
        unique_tickers = set(all_tickers)
        if len(unique_tickers) != len(all_tickers):
            duplicates = [t for t in all_tickers if all_tickers.count(t) > 1]
            errors.append(
                ValidationError(
                    field="tickers",
                    message=f"Duplicate tickers found: {list(set(duplicates))}",
                    value=duplicates,
                )
            )

        return errors

    @classmethod
    def _validate_single_ticker(cls, ticker: str, field: str) -> List[ValidationError]:
        """Validate a single ticker symbol."""
        errors = []

        if not ticker:
            errors.append(
                ValidationError(
                    field=field, message="Ticker cannot be empty", value=ticker
                )
            )
            return errors

        if len(ticker) > 20:
            errors.append(
                ValidationError(
                    field=field,
                    message=f"Ticker too long ({len(ticker)} chars). Maximum: 20",
                    value=ticker,
                )
            )

        if not cls.TICKER_PATTERN.match(ticker):
            errors.append(
                ValidationError(
                    field=field,
                    message=f"Invalid ticker format: {ticker}. Use uppercase letters, numbers, hyphens, dots, and equals only",
                    value=ticker,
                )
            )

        # Validate specific patterns
        if "_" in ticker and not cls.SYNTHETIC_PATTERN.match(ticker):
            errors.append(
                ValidationError(
                    field=field,
                    message=f"Invalid synthetic pair format: {ticker}. Use format: SYMBOL1_SYMBOL2",
                    value=ticker,
                )
            )

        return errors

    @classmethod
    def _validate_synthetic_pairs(
        cls, request: MACrossRequest
    ) -> List[ValidationError]:
        """Validate synthetic pair configuration."""
        errors = []

        # Collect all tickers to check for synthetic pairs
        all_tickers = []
        if isinstance(request.ticker, str):
            all_tickers.append(request.ticker)
        elif isinstance(request.ticker, list):
            all_tickers.extend(request.ticker)

        if hasattr(request, "tickers") and request.tickers:
            all_tickers.extend(request.tickers)

        has_synthetic = any("_" in t for t in all_tickers)
        has_ticker_1 = bool(request.ticker_1)
        has_ticker_2 = bool(request.ticker_2)
        use_synthetic = getattr(request, "use_synthetic", False)

        # If use_synthetic is True, both ticker_1 and ticker_2 are required
        if use_synthetic and (not has_ticker_1 or not has_ticker_2):
            errors.append(
                ValidationError(
                    field="synthetic_pairs",
                    message="When USE_SYNTHETIC is true, both TICKER_1 and TICKER_2 must be specified",
                    value={
                        "ticker_1": request.ticker_1,
                        "ticker_2": request.ticker_2,
                        "use_synthetic": use_synthetic,
                    },
                )
            )

        # If synthetic tickers in main ticker field, both ticker_1 and ticker_2
        # should be provided
        if has_synthetic and (not has_ticker_1 or not has_ticker_2):
            errors.append(
                ValidationError(
                    field="synthetic_pairs",
                    message="Synthetic pair tickers (containing '_') require both TICKER_1 and TICKER_2 to be specified",
                    value={"ticker_1": request.ticker_1, "ticker_2": request.ticker_2},
                )
            )

        # If ticker_1 or ticker_2 are provided, either use_synthetic should be
        # true OR there should be synthetic tickers
        if (has_ticker_1 or has_ticker_2) and not use_synthetic and not has_synthetic:
            # This is now just a warning - we'll allow it but ignore the
            # ticker_1/ticker_2 fields
            pass  # Don't add an error, just ignore these fields

        # Validate individual synthetic ticker symbols if they're provided
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
            errors.append(
                ValidationError(
                    field="years",
                    message=f"Years must be between 0 and {cls.MAX_YEARS}",
                    value=request.years,
                )
            )

        if request.use_hourly and request.years > 2:
            errors.append(
                ValidationError(
                    field="years",
                    message="Hourly data analysis limited to 2 years maximum",
                    value=request.years,
                )
            )

        return errors

    @classmethod
    def _validate_minimum_criteria(cls, criteria) -> List[ValidationError]:
        """Validate minimum criteria settings."""
        errors = []

        # Validate percentage ranges
        percentage_fields = []
        if hasattr(criteria, "win_rate") and criteria.win_rate is not None:
            percentage_fields.append(("win_rate", criteria.win_rate))
        if hasattr(criteria, "profit_factor") and criteria.profit_factor is not None:
            percentage_fields.append(("profit_factor", criteria.profit_factor))
        if hasattr(criteria, "sortino_ratio") and criteria.sortino_ratio is not None:
            percentage_fields.append(("sortino_ratio", criteria.sortino_ratio))

        for field_name, value in percentage_fields:
            if value is not None and field_name == "win_rate":
                if value < 0.0 or value > 1.0:
                    errors.append(
                        ValidationError(
                            field=f"minimum_criteria.{field_name}",
                            message=f"{field_name} must be between 0.0 and 1.0",
                            value=value,
                        )
                    )
            elif value is not None and value < 0:
                errors.append(
                    ValidationError(
                        field=f"minimum_criteria.{field_name}",
                        message=f"{field_name} must be non-negative",
                        value=value,
                    )
                )

        # Validate count fields
        count_fields = []
        if hasattr(criteria, "trades") and criteria.trades is not None:
            count_fields.append(("trades", criteria.trades))

        for field_name, value in count_fields:
            if value is not None and value < 0:
                errors.append(
                    ValidationError(
                        field=f"minimum_criteria.{field_name}",
                        message=f"{field_name} must be non-negative",
                        value=value,
                    )
                )

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
                "invalid_value": error.value,
            }
            for error in errors
        ],
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
