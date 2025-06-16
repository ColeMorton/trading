"""Strategy ID utilities for concurrency analysis.

This module provides functions for generating and parsing standardized strategy IDs
used throughout the concurrency analysis system.
"""

from typing import Any, Dict


def generate_strategy_id(strategy_config: Dict[str, Any]) -> str:
    """Generate a standardized strategy ID from a strategy configuration.

    The strategy ID format is: {ticker}_{strategy_type}_{short_window}_{long_window}_{signal_window}

    Args:
        strategy_config (Dict[str, Any]): Strategy configuration dictionary

    Returns:
        str: Standardized strategy ID

    Raises:
        ValueError: If required fields are missing from the strategy configuration
    """
    # Extract required fields with appropriate case handling
    ticker = _get_config_value(strategy_config, ["TICKER", "Ticker", "ticker"])

    # Determine strategy type
    strategy_type = _get_strategy_type(strategy_config)

    # Get window parameters based on strategy type
    if strategy_type == "ATR":
        # ATR strategies use length and multiplier instead of windows
        short_window = _get_config_value(strategy_config, ["LENGTH", "length"])
        long_window = _get_config_value(strategy_config, ["MULTIPLIER", "multiplier"])
        # ATR doesn't use signal window, default to 0
        signal_window = 0
    else:
        # MA and MACD strategies use short and long windows
        short_window = _get_config_value(
            strategy_config, ["SHORT_WINDOW", "Short Window", "short_window"]
        )
        long_window = _get_config_value(
            strategy_config, ["LONG_WINDOW", "Long Window", "long_window"]
        )
        # Get signal window (default to 0 for MA strategies)
        signal_window = _get_config_value(
            strategy_config,
            ["SIGNAL_WINDOW", "Signal Window", "signal_window"],
            default=0,
        )

    # Format the strategy ID
    return f"{ticker}_{strategy_type}_{short_window}_{long_window}_{signal_window}"


def parse_strategy_id(strategy_id: str) -> Dict[str, Any]:
    """Parse a strategy ID into its component parts.

    Args:
        strategy_id (str): Strategy ID in the format {ticker}_{strategy_type}_{short_window}_{long_window}_{signal_window}

    Returns:
        Dict[str, Any]: Dictionary containing the parsed components

    Raises:
        ValueError: If the strategy ID format is invalid
    """
    parts = strategy_id.split("_")

    if len(parts) < 5:
        raise ValueError(f"Invalid strategy ID format: {strategy_id}")

    # Handle case where ticker might contain underscores (e.g., BTC-USD_SMA_80_85_0)
    if len(parts) > 5:
        # Reconstruct ticker with internal underscores
        ticker_parts = parts[:-4]
        ticker = "_".join(ticker_parts)
        # Get the remaining parts
        strategy_type = parts[-4]
        short_window = parts[-3]
        long_window = parts[-2]
        signal_window = parts[-1]
    else:
        ticker = parts[0]
        strategy_type = parts[1]
        short_window = parts[2]
        long_window = parts[3]
        signal_window = parts[4]

    # Convert numeric values to appropriate types
    try:
        # For ATR strategies, long_window might be a float (multiplier)
        if strategy_type == "ATR":
            short_window_val = int(short_window)
            long_window_val = float(long_window)
        else:
            short_window_val = int(short_window)
            long_window_val = int(long_window)

        signal_window_val = int(signal_window)
    except ValueError:
        raise ValueError(f"Invalid numeric values in strategy ID: {strategy_id}")

    return {
        "ticker": ticker,
        "strategy_type": strategy_type,
        "short_window": short_window_val,
        "long_window": long_window_val,
        "signal_window": signal_window_val,
    }


def is_valid_strategy_id(strategy_id: str) -> bool:
    """Check if a string is a valid strategy ID.

    Args:
        strategy_id (str): String to validate

    Returns:
        bool: True if the string is a valid strategy ID, False otherwise
    """
    try:
        parse_strategy_id(strategy_id)
        return True
    except ValueError:
        return False


def _get_config_value(
    config: Dict[str, Any], possible_keys: list, default: Any | None = None
) -> Any:
    """Get a value from a config dictionary, checking multiple possible keys.

    Args:
        config (Dict[str, Any]): Configuration dictionary
        possible_keys (list): List of possible keys to check
        default (Any, optional): Default value if no key is found

    Returns:
        Any: Value from the config, or default if not found

    Raises:
        ValueError: If no key is found and no default is provided
    """
    for key in possible_keys:
        if key in config:
            return config[key]

    if default is not None:
        return default

    raise ValueError(
        f"Required field not found in config. Checked keys: {possible_keys}"
    )


def _get_strategy_type(config: Dict[str, Any]) -> str:
    """Determine the strategy type from a configuration dictionary.

    Args:
        config (Dict[str, Any]): Strategy configuration dictionary

    Returns:
        str: Strategy type (SMA, EMA, MACD, ATR)

    Raises:
        ValueError: If strategy type cannot be determined
    """
    # Check for explicit strategy type
    strategy_type = _get_config_value(
        config,
        ["STRATEGY_TYPE", "Strategy Type", "MA Type", "strategy_type", "TYPE", "type"],
        default=None,
    )

    if strategy_type:
        return str(strategy_type)

    # Infer from configuration
    if "SIGNAL_WINDOW" in config or "signal_window" in config:
        return "MACD"
    elif ("LENGTH" in config or "length" in config) and (
        "MULTIPLIER" in config or "multiplier" in config
    ):
        return "ATR"
    elif "USE_SMA" in config or "Use_SMA" in config:
        use_sma = _get_config_value(config, ["USE_SMA", "Use_SMA"])
        return "SMA" if use_sma else "EMA"
    else:
        # Fail fast - no default strategy type allowed
        raise ValueError(
            "Strategy type cannot be determined. Must be explicitly specified (STRATEGY_TYPE, Strategy Type, or MA Type field required)."
        )
