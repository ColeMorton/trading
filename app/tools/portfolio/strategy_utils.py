"""
Strategy Utilities Module

This module provides centralized utilities for handling strategy types
and ensuring consistency across the application.
"""

from typing import Any, Callable, Dict, Optional

from app.tools.portfolio.strategy_types import (
    DEFAULT_STRATEGY_TYPE,
    STRATEGY_TYPE_FIELDS,
    VALID_STRATEGY_TYPES,
    StrategyTypeLiteral,
)


def determine_strategy_type(
    row: Dict[str, Any], log: Optional[Callable[[str, str], None]] = None
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
        if field in row and row[field]:
            strategy_type = row[field]
            # Validate strategy type
            if strategy_type in VALID_STRATEGY_TYPES:
                if log:
                    log(
                        f"Using strategy type '{strategy_type}' from field '{field}' for {ticker}",
                        "info",
                    )
                return strategy_type
            else:
                if log:
                    log(
                        f"Invalid strategy type '{strategy_type}' from field '{field}' for {ticker}, defaulting to {DEFAULT_STRATEGY_TYPE}",
                        "warning",
                    )
                return DEFAULT_STRATEGY_TYPE

    # Check if this might be a MACD strategy based on presence of SIGNAL_WINDOW
    if "SIGNAL_WINDOW" in row and row["SIGNAL_WINDOW"] is not None:
        if log:
            log(
                f"Detected MACD strategy for {ticker} based on presence of SIGNAL_WINDOW",
                "info",
            )
        return "MACD"

    # For legacy data: Derive from USE_SMA if no explicit type
    if log:
        log(
            f"No explicit strategy type found for {ticker}. Deriving from USE_SMA.",
            "info",
        )

    use_sma = row.get("USE_SMA", True)
    if isinstance(use_sma, str):
        use_sma = use_sma.lower() in ["true", "yes", "1"]

    derived_type = "SMA" if use_sma else "EMA"
    if log:
        log(
            f"Derived strategy type '{derived_type}' from USE_SMA={use_sma} for {ticker}",
            "info",
        )

    return derived_type


def create_strategy_type_fields(strategy_type: StrategyTypeLiteral) -> Dict[str, Any]:
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
        STRATEGY_TYPE_FIELDS[
            "JSON_OLD"
        ]: strategy_type,  # type (for backward compatibility)
        "USE_SMA": strategy_type == "SMA",  # Derive USE_SMA from strategy_type
    }


def get_strategy_type_for_export(
    df: Dict[str, Any], log: Optional[Callable[[str, str], None]] = None
) -> StrategyTypeLiteral:
    """
    Get the strategy type for export, handling all possible field names.

    Args:
        df: DataFrame or dictionary containing strategy data
        log: Optional logging function

    Returns:
        str: Strategy type (SMA, EMA, or MACD)
    """
    if log:
        log(f"Checking for strategy type fields in: {df.keys()}", "info")

    # Use the same priority order as determine_strategy_type
    field_priority = [
        STRATEGY_TYPE_FIELDS["INTERNAL"],  # STRATEGY_TYPE
        STRATEGY_TYPE_FIELDS["CSV"],  # Strategy Type
        STRATEGY_TYPE_FIELDS["JSON_NEW"],  # strategy_type
        STRATEGY_TYPE_FIELDS["JSON_OLD"],  # type
    ]

    for field in field_priority:
        if log:
            log(
                f"Field '{field}' present: {field in df}, value: {df.get(field)}",
                "info",
            )
        if field in df and df[field] is not None:
            return df[field]

    # Check if this might be a MACD strategy based on presence of SIGNAL_WINDOW
    if "SIGNAL_WINDOW" in df and df["SIGNAL_WINDOW"] is not None:
        if log:
            log("Detected MACD strategy based on presence of SIGNAL_WINDOW", "info")
        return "MACD"

    # If no strategy type field is found, derive from USE_SMA
    if log:
        # Note: USE_SMA is deprecated and only exists for legacy support
        log(
            f"USE_SMA present (legacy field): {
    'USE_SMA' in df}, value: {
        df.get('USE_SMA')}",
            "info",
        )
    if "USE_SMA" in df:
        use_sma = df["USE_SMA"]
        if isinstance(use_sma, str):
            use_sma = use_sma.lower() in ["true", "yes", "1"]
        return "SMA" if use_sma else "EMA"

    # Default to EMA if no information is available
    if log:
        log(
            f"No strategy type information found, defaulting to {DEFAULT_STRATEGY_TYPE}",
            "warning",
        )
    return DEFAULT_STRATEGY_TYPE
