"""Strategy utilities.

This module provides utilities for working with trading strategies.
"""

from typing import Any

from app.concurrency.tools.strategy_id import generate_strategy_id, is_valid_strategy_id


def get_strategy_types(
    config: dict[str, Any],
    log_func=None,
    default_type: str = "SMA",
) -> list[str]:
    """Get strategy types from config with defaults.

    Args:
        config: Configuration dictionary
        log_func: Optional logging function
        default_type: Default strategy type if none specified

    Returns:
        List of strategy types
    """
    strategy_types = config.get("STRATEGY_TYPES", [])

    if not strategy_types:
        if log_func:
            log_func(
                f"No strategy types specified in config, defaulting to {default_type}",
            )
        strategy_types = [default_type]

    if log_func:
        log_func(f"Using strategy types: {strategy_types}")

    return list(strategy_types)


def filter_portfolios_by_signal(
    portfolios: list[dict[str, Any]],
    config: dict[str, Any],
    log_func=None,
    signal_field: str = "Signal Entry",
) -> list[dict[str, Any]]:
    """Filter portfolios based on signal field.

    Args:
        portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        log_func: Optional logging function
        signal_field: Field to filter by (default: "Signal Entry")

    Returns:
        Filtered list of portfolio dictionaries
    """
    if not portfolios:
        return []

    if not config.get("USE_CURRENT", False):
        return portfolios

    original_count = len(portfolios)
    filtered = [p for p in portfolios if str(p.get(signal_field, "")).lower() == "true"]
    filtered_count = original_count - len(filtered)

    if filtered_count > 0 and log_func:
        log_func(
            f"Filtered out {filtered_count} portfolios with {signal_field} = False",
            "debug",
        )
        log_func(f"Remaining portfolios: {len(filtered)}", "debug")

    return filtered


def determine_strategy_type(strategy_config: dict[str, Any], log_func=None) -> str:
    """Determine the strategy type from configuration.

    Args:
        strategy_config: Strategy configuration dictionary
        log_func: Optional logging function

    Returns:
        Strategy type string
    """
    # Check for explicit strategy type
    strategy_type = strategy_config.get("STRATEGY_TYPE", "")
    if not strategy_type:
        strategy_type = strategy_config.get("type", "")

    # If still not found, infer from configuration
    if not strategy_type:
        if (
            "SIGNAL_PERIOD" in strategy_config
            and strategy_config.get("SIGNAL_PERIOD", 0) > 0
        ):
            strategy_type = "MACD"
        elif "LENGTH" in strategy_config and "MULTIPLIER" in strategy_config:
            strategy_type = "ATR"
        else:
            # Default to MA strategy
            strategy_type = "MA"

    if log_func:
        log_func(f"Using strategy type: {strategy_type}")

    return str(strategy_type)


def get_required_fields_for_strategy(strategy_type: str) -> list[str]:
    """Get required fields for a specific strategy type.

    Args:
        strategy_type: Strategy type string

    Returns:
        List of required field names
    """
    if strategy_type == "ATR":
        return ["TICKER", "LENGTH", "MULTIPLIER"]
    if strategy_type == "MACD":
        return ["TICKER", "FAST_PERIOD", "SLOW_PERIOD", "SIGNAL_PERIOD"]
    # Default to MA strategy
    return ["TICKER", "FAST_PERIOD", "SLOW_PERIOD"]


def validate_strategy_config(
    strategy_config: dict[str, Any],
    strategy_index: int = 0,
    log_func=None,
) -> bool:
    """Validate a strategy configuration.

    Args:
        strategy_config: Strategy configuration dictionary
        strategy_index: Index of the strategy (for logging)
        log_func: Optional logging function

    Returns:
        True if valid, False otherwise

    Raises:
        ValueError: If required fields are missing
    """
    # Normalize field names first (handle both uppercase and lowercase)
    field_mapping = {
        "TICKER": ["ticker", "TICKER"],
        "LENGTH": ["length", "LENGTH"],
        "MULTIPLIER": ["multiplier", "MULTIPLIER"],
        "FAST_PERIOD": ["fast_period", "FAST_PERIOD"],
        "SLOW_PERIOD": ["slow_period", "SLOW_PERIOD"],
        "SIGNAL_PERIOD": ["signal_period", "SIGNAL_PERIOD"],
        "DIRECTION": ["direction", "DIRECTION"],
        "STRATEGY_TYPE": ["type", "STRATEGY_TYPE"],
    }

    # Copy values from lowercase to uppercase keys
    for upper_key, possible_keys in field_mapping.items():
        for key in possible_keys:
            if key in strategy_config and upper_key not in strategy_config:
                strategy_config[upper_key] = strategy_config[key]

    # Determine strategy type after normalization
    strategy_type = determine_strategy_type(strategy_config, log_func)

    # Define required fields based on strategy type
    required_fields = get_required_fields_for_strategy(strategy_type)

    # Check for missing fields after normalization
    missing_fields = []
    for field in required_fields:
        # For each required field, check if any of its possible variations exist
        field_variants = [field.lower(), field]
        if not any(variant in strategy_config for variant in field_variants):
            missing_fields.append(field)

    if missing_fields:
        if log_func:
            log_func(
                f"Strategy {strategy_index} missing required fields: {missing_fields}",
                "error",
            )
        msg = f"Strategy {strategy_index} missing required fields: {missing_fields}"
        raise ValueError(
            msg,
        )

    # Log strategy details
    if log_func:
        direction = (
            "Short" if strategy_config.get("DIRECTION", "Long") == "Short" else "Long"
        )
        timeframe = "Hourly" if strategy_config.get("USE_HOURLY", False) else "Daily"
        log_func(
            f"Strategy {strategy_index} - {strategy_config['TICKER']}: {timeframe} ({direction})",
            "info",
        )

    return True


def get_strategy_id(
    strategy_config: dict[str, Any],
    strategy_index: int = 0,
    log_func=None,
) -> str:
    """Get or generate a strategy ID for a strategy configuration.

    Args:
        strategy_config (Dict[str, Any]): Strategy configuration
        strategy_index (int): Index of the strategy (for logging)
        log_func: Optional logging function

    Returns:
        str: Strategy ID
    """
    # Check if strategy ID already exists
    if "strategy_id" in strategy_config:
        strategy_id = strategy_config["strategy_id"]

        # Validate existing strategy ID
        if is_valid_strategy_id(strategy_id):
            if log_func:
                log_func(
                    f"Using existing strategy ID for strategy {strategy_index}: {strategy_id}",
                    "debug",
                )
            return str(strategy_id)
        if log_func:
            log_func(
                f"Invalid existing strategy ID for strategy {strategy_index}: {strategy_id}",
                "warning",
            )

    # Generate new strategy ID
    try:
        strategy_id = generate_strategy_id(strategy_config)
        if log_func:
            log_func(
                f"Generated strategy ID for strategy {strategy_index}: {strategy_id}",
                "debug",
            )
        return strategy_id
    except ValueError as e:
        if log_func:
            log_func(
                f"Could not generate strategy ID for strategy {strategy_index}: {e!s}",
                "warning",
            )

        # Fallback to a simple identifier
        ticker = strategy_config.get(
            "TICKER",
            strategy_config.get("ticker", f"strategy_{strategy_index}"),
        )
        return f"{ticker}_strategy_{strategy_index}"
