"""
Strategy Utilities Module

This module provides centralized utilities for handling strategy types
and ensuring consistency across the application.
"""

from collections.abc import Callable
from typing import Any

from app.tools.portfolio.strategy_types import (
    DEFAULT_STRATEGY_TYPE,
    STRATEGY_TYPE_FIELDS,
    VALID_STRATEGY_TYPES,
    StrategyTypeLiteral,
)


def determine_strategy_type(
    row: dict[str, Any], log: Callable[[str, str], None] | None = None,
) -> StrategyTypeLiteral:
    """
    Determine strategy type from row data with consistent priority.

    Priority order:
    1. STRATEGY_TYPE column (internal representation)
    2. Strategy Type column (CSV representation)
    3. strategy_type column (new JSON field name)
    4. type column (old JSON field name)
    5. Derived from USE_SMA

    Args:
        row: Row data dictionary
        log: Optional logging function

    Returns:
        str: Strategy type (SMA, EMA, or MACD)
    """
    ticker = row.get("TICKER", "Unknown")

    # Check for explicit type fields in priority order
    field_priority = [
        STRATEGY_TYPE_FIELDS["INTERNAL"],  # STRATEGY_TYPE
        STRATEGY_TYPE_FIELDS["CSV"],  # Strategy Type
        STRATEGY_TYPE_FIELDS["JSON_NEW"],  # strategy_type
        STRATEGY_TYPE_FIELDS["JSON_OLD"],  # type
    ]

    for field in field_priority:
        if row.get(field):
            strategy_type = row[field]
            # Validate strategy type
            if strategy_type in VALID_STRATEGY_TYPES:
                if log:
                    log(
                        f"Using strategy type '{strategy_type}' from field '{field}' for {ticker}",
                        "info",
                    )
                return strategy_type  # type: ignore
            if log:
                log(
                    f"Invalid strategy type '{strategy_type}' from field '{field}' for {ticker}, defaulting to {DEFAULT_STRATEGY_TYPE}",
                    "warning",
                )
            return "SMA"  # DEFAULT_STRATEGY_TYPE

    # Check if this might be a MACD strategy based on presence of SIGNAL_PERIOD
    if "SIGNAL_PERIOD" in row and row["SIGNAL_PERIOD"] is not None:
        if log:
            log(
                f"Detected MACD strategy for {ticker} based on presence of SIGNAL_PERIOD",
                "info",
            )
        return "MACD"

    # Default fallback (fail-fast approach)
    if log:
        log(
            f"No explicit strategy type found for {ticker}, defaulting to {DEFAULT_STRATEGY_TYPE}",
            "warning",
        )

    return DEFAULT_STRATEGY_TYPE


def create_strategy_type_fields(strategy_type: StrategyTypeLiteral) -> dict[str, Any]:
    """
    Create a dictionary with all strategy type field representations.

    Args:
        strategy_type: The strategy type (SMA, EMA, MACD)

    Returns:
        Dict[str, Any]: Dictionary with all strategy type field representations
    """
    return {
        STRATEGY_TYPE_FIELDS["INTERNAL"]: strategy_type,  # STRATEGY_TYPE
        STRATEGY_TYPE_FIELDS["JSON_NEW"]: strategy_type,  # strategy_type
        STRATEGY_TYPE_FIELDS["JSON_OLD"]: strategy_type,  # type
    }


def get_strategy_type_for_export(
    df: dict[str, Any], log: Callable[[str, str], None] | None = None,
) -> StrategyTypeLiteral:
    """
    Get the strategy type for export, handling all possible field names.

    Args:
        df: DataFrame or dictionary containing strategy data
        log: Optional logging function

    Returns:
        str: Strategy type (SMA, EMA, MACD, or ATR)
    """
    # Use the same priority order as determine_strategy_type
    field_priority = [
        STRATEGY_TYPE_FIELDS["INTERNAL"],  # STRATEGY_TYPE
        STRATEGY_TYPE_FIELDS["CSV"],  # Strategy Type
        STRATEGY_TYPE_FIELDS["JSON_NEW"],  # strategy_type
        STRATEGY_TYPE_FIELDS["JSON_OLD"],  # type
    ]

    for field in field_priority:
        if field in df and df[field] is not None:
            return df[field]

    # Check if this might be a MACD strategy based on presence of SIGNAL_PERIOD
    if "SIGNAL_PERIOD" in df and df["SIGNAL_PERIOD"] is not None:
        if log:
            log("Detected MACD strategy based on presence of SIGNAL_PERIOD", "info")
        return "MACD"

    # Default to DEFAULT_STRATEGY_TYPE if no strategy type information is available (fail-fast approach)
    if log:
        log(
            f"No explicit strategy type found, defaulting to {DEFAULT_STRATEGY_TYPE}",
            "warning",
        )
    return DEFAULT_STRATEGY_TYPE
