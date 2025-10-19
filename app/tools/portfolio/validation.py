"""
Portfolio Validation Module

This module provides functions for validating portfolio data against schemas
and reporting errors.
"""

from collections.abc import Callable
from typing import Any

import polars as pl

from app.tools.portfolio.strategy_utils import get_strategy_type_for_export


def validate_portfolio_schema(
    df: pl.DataFrame,
    log: Callable[[str, str], None],
    required_columns: list[str] | None | None = None,
) -> tuple[bool, list[str]]:
    """
    Validate that a portfolio DataFrame has the required columns.

    Args:
        df: DataFrame containing portfolio data
        log: Logging function
        required_columns: List of required column names (default: ['TICKER'])

    Returns:
        Tuple of (is_valid, error_messages)
    """
    if required_columns is None:
        required_columns = ["TICKER"]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns: {', '.join(missing_columns)}"
        log(error_msg, "error")
        return False, [error_msg]

    return True, []


def validate_strategy_config(
    strategy: dict[str, Any], log: Callable[[str, str], None]
) -> tuple[bool, list[str]]:
    """
    Validate a strategy configuration dictionary.

    Args:
        strategy: Strategy configuration dictionary
        log: Logging function

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    # Check for TICKER which is required for all strategies
    if "TICKER" not in strategy:
        errors.append("Missing required field: TICKER")

    # Get strategy type using the centralized utility function
    strategy_type = get_strategy_type_for_export(strategy)

    # Define required fields based on strategy type
    ticker = strategy.get("TICKER", "Unknown")

    if strategy_type == "ATR":
        # ATR strategy requires length and multiplier (check both lowercase and
        # uppercase)
        required_fields = [("length", "LENGTH"), ("multiplier", "MULTIPLIER")]
        for field_pair in required_fields:
            if field_pair[0] not in strategy and field_pair[1] not in strategy:
                errors.append(
                    f"Missing required field: {field_pair[0]} or {field_pair[1]}"
                )
    elif strategy_type == "MACD":
        # MACD strategies require FAST_PERIOD, SLOW_PERIOD, and SIGNAL_PERIOD
        # (with fallback support for legacy FAST_PERIOD, SLOW_PERIOD, SIGNAL_PERIOD)
        required_field_pairs = [
            (["FAST_PERIOD", "FAST_PERIOD"], "FAST_PERIOD/FAST_PERIOD"),
            (["SLOW_PERIOD", "SLOW_PERIOD"], "SLOW_PERIOD/SLOW_PERIOD"),
            (["SIGNAL_PERIOD", "SIGNAL_PERIOD"], "SIGNAL_PERIOD/SIGNAL_PERIOD"),
        ]

        for field_options, field_name in required_field_pairs:
            field_found = False
            for field in field_options:
                if field in strategy and strategy[field] is not None:
                    field_found = True
                    break

            if not field_found:
                errors.append(
                    f"Missing required field for MACD strategy {ticker}: {field_name}"
                )
            elif any(
                field in strategy and strategy[field] is None for field in field_options
            ):
                errors.append(
                    f"Field {field_name} cannot be null for MACD strategy {ticker}"
                )

        # Validate window relationships for MACD
        # Use new field names first, fallback to legacy names
        fast_period = strategy.get("FAST_PERIOD") or strategy.get("FAST_PERIOD")
        slow_period = strategy.get("SLOW_PERIOD") or strategy.get("SLOW_PERIOD")
        signal_period = strategy.get("SIGNAL_PERIOD") or strategy.get("SIGNAL_PERIOD")

        if all(
            param is not None for param in [fast_period, slow_period, signal_period]
        ):
            if fast_period >= slow_period:
                errors.append(
                    f"FAST_PERIOD ({fast_period}) must be less than SLOW_PERIOD ({slow_period}) for MACD strategy {ticker}"
                )
            if signal_period <= 0:
                errors.append(
                    f"SIGNAL_PERIOD ({signal_period}) must be greater than 0 for MACD strategy {ticker}"
                )
    else:
        # MA strategies require FAST_PERIOD and SLOW_PERIOD
        # (with fallback support for legacy FAST_PERIOD and SLOW_PERIOD)
        required_field_pairs = [
            (["FAST_PERIOD", "FAST_PERIOD"], "FAST_PERIOD/FAST_PERIOD"),
            (["SLOW_PERIOD", "SLOW_PERIOD"], "SLOW_PERIOD/SLOW_PERIOD"),
        ]

        for field_options, field_name in required_field_pairs:
            field_found = any(field in strategy for field in field_options)
            if not field_found:
                errors.append(f"Missing required field: {field_name}")

    if errors:
        for error in errors:
            log(error, "error")
        return False, errors

    # Validate numeric fields
    numeric_fields = {
        # New parameter names
        "FAST_PERIOD": int,
        "SLOW_PERIOD": int,
        "SIGNAL_PERIOD": int,
        # Other fields
        "STOP_LOSS": float,
        "POSITION_SIZE": float,
        "RSI_WINDOW": int,
        "RSI_THRESHOLD": int,
        "length": int,
        "LENGTH": int,
        "multiplier": float,
        "MULTIPLIER": float,
    }

    for field, field_type in numeric_fields.items():
        if field in strategy:
            # Skip None values
            if strategy[field] is None:
                continue

            try:
                # Attempt to convert to the expected type
                strategy[field] = field_type(strategy[field])
            except (ValueError, TypeError):
                errors.append(f"Invalid {field} value: {strategy[field]}")

    # Validate window relationships
    # Use new field names first, fallback to legacy names
    fast_period = strategy.get("FAST_PERIOD") or strategy.get("FAST_PERIOD")
    slow_period = strategy.get("SLOW_PERIOD") or strategy.get("SLOW_PERIOD")

    if fast_period is not None and slow_period is not None:
        if fast_period >= slow_period:
            errors.append(
                f"FAST_PERIOD ({fast_period}) must be less than SLOW_PERIOD ({slow_period})"
            )

    # Validate stop loss range
    if "STOP_LOSS" in strategy and strategy["STOP_LOSS"] is not None:
        stop_loss_float = float(strategy["STOP_LOSS"])
        # Convert percentage (0-100) to decimal (0-1)
        stop_loss_decimal = (
            stop_loss_float / 100 if stop_loss_float > 1 else stop_loss_float
        )
        if stop_loss_decimal <= 0 or stop_loss_decimal > 1:
            errors.append(
                f"Stop loss for {strategy.get('TICKER', 'Unknown')} ({stop_loss_float}%) is outside valid range (0-100%)"
            )
        strategy["STOP_LOSS"] = stop_loss_decimal

    if errors:
        for error in errors:
            log(error, "error")
        return False, errors

    return True, []


def validate_portfolio_configs(
    strategies: list[dict[str, Any]], log: Callable[[str, str], None]
) -> tuple[bool, list[dict[str, Any]]]:
    """
    Validate a list of strategy configurations.

    Args:
        strategies: List of strategy configuration dictionaries
        log: Logging function

    Returns:
        Tuple of (is_valid, valid_strategies)
    """
    valid_strategies = []
    all_valid = True

    for strategy in strategies:
        ticker = strategy.get("TICKER", "Unknown")
        is_valid, errors = validate_strategy_config(strategy, log)
        if is_valid:
            log(f"VALIDATION PASS: {ticker} strategy accepted", "info")
            valid_strategies.append(strategy)
        else:
            log(
                f"VALIDATION FAIL: {ticker} strategy rejected - errors: {errors}",
                "warning",
            )
            all_valid = False

    return all_valid, valid_strategies
