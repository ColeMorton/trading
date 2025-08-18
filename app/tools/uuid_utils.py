"""
Centralized UUID utilities for trading strategies.

This module provides a single source of truth for generating and parsing
strategy UUIDs/IDs across the entire trading system.

Key Features:
- Consistent UUID format for SMA/EMA (omits signal_period) vs MACD (includes signal_period)
- Backward compatibility for parsing existing UUIDs
- Support for both position UUIDs and strategy IDs
- Validation and error handling
"""

from typing import Any, Dict, Optional, Tuple


def generate_strategy_uuid(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_period: int = 0,
    entry_date: Optional[str] = None,
) -> str:
    """Generate standardized strategy UUID.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD, ATR, etc.)
        fast_period: Fast period parameter
        slow_period: Slow period parameter
        signal_period: Signal period parameter (optional, only used for MACD)
        entry_date: Entry date for position UUIDs (optional)

    Returns:
        str: Formatted strategy UUID

    Raises:
        ValueError: If required parameters are invalid
    """
    # Validate inputs
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")
    if not strategy_type or not isinstance(strategy_type, str):
        raise ValueError("Strategy type must be a non-empty string")
    if not isinstance(fast_period, int) or fast_period <= 0:
        raise ValueError("Fast period must be a positive integer")
    if not isinstance(slow_period, int) or slow_period <= 0:
        raise ValueError("Slow period must be a positive integer")
    if fast_period >= slow_period:
        raise ValueError("Fast period must be less than slow period")

    # Clean entry date to YYYYMMDD format if provided
    if entry_date:
        if isinstance(entry_date, str):
            if " " in entry_date:
                entry_date = entry_date.split(" ")[0]
            # Convert YYYY-MM-DD to YYYYMMDD for consistency
            if "-" in entry_date and len(entry_date) == 10:
                entry_date = entry_date.replace("-", "")

    # Normalize strategy type
    strategy_upper = strategy_type.upper()
    ticker_upper = ticker.upper()

    # Build UUID components
    uuid_parts = [ticker_upper, strategy_upper, str(fast_period), str(slow_period)]

    # For SMA and EMA strategies, omit the signal_period parameter
    # Signal period is only used for MACD strategies
    if strategy_upper not in ["SMA", "EMA"]:
        # For MACD and other strategies that use signal_period
        uuid_parts.append(str(signal_period))

    # Add entry date if provided (for position UUIDs)
    if entry_date:
        uuid_parts.append(entry_date)

    return "_".join(uuid_parts)


def generate_position_uuid(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_period: int,
    entry_date: str,
) -> str:
    """Generate unique position identifier with validation.

    This is a convenience wrapper around generate_strategy_uuid for positions.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD, etc.)
        fast_period: Fast period parameter
        slow_period: Slow period parameter
        signal_period: Signal period parameter (ignored for SMA/EMA)
        entry_date: Position entry date

    Returns:
        str: Unique position UUID

    Raises:
        ValueError: If required parameters are invalid
    """
    if not entry_date:
        raise ValueError("Entry date is required for position UUIDs")

    return generate_strategy_uuid(
        ticker=ticker,
        strategy_type=strategy_type,
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
        entry_date=entry_date,
    )


def generate_strategy_id(
    ticker: str,
    strategy_type: str,
    fast_period: int,
    slow_period: int,
    signal_period: int = 0,
) -> str:
    """Generate standardized strategy ID (without entry date).

    This is a convenience wrapper around generate_strategy_uuid for strategy IDs.

    Args:
        ticker: Stock/asset ticker symbol
        strategy_type: Strategy type (SMA, EMA, MACD, etc.)
        fast_period: Fast period parameter
        slow_period: Slow period parameter
        signal_period: Signal period parameter (ignored for SMA/EMA)

    Returns:
        str: Strategy ID

    Raises:
        ValueError: If required parameters are invalid
    """
    return generate_strategy_uuid(
        ticker=ticker,
        strategy_type=strategy_type,
        fast_period=fast_period,
        slow_period=slow_period,
        signal_period=signal_period,
        entry_date=None,
    )


def parse_strategy_uuid(strategy_uuid: str) -> Dict[str, Any]:
    """Parse a strategy UUID into its component parts.

    Supports both old and new formats for backward compatibility.

    Args:
        strategy_uuid: Strategy UUID in various formats:
                      - SMA/EMA: {ticker}_{strategy_type}_{fast_period}_{slow_period}[_{entry_date}]
                      - MACD/others: {ticker}_{strategy_type}_{fast_period}_{slow_period}_{signal_period}[_{entry_date}]

    Returns:
        Dict[str, Any]: Dictionary containing the parsed components:
            - ticker: str
            - strategy_type: str
            - fast_period: int
            - slow_period: int or float (for ATR multiplier)
            - signal_period: int
            - entry_date: str or None

    Raises:
        ValueError: If the UUID format is invalid
    """
    if not strategy_uuid or not isinstance(strategy_uuid, str):
        raise ValueError("Strategy UUID must be a non-empty string")

    parts = strategy_uuid.split("_")

    if len(parts) < 4:
        raise ValueError(f"Invalid strategy UUID format: {strategy_uuid}")

    # Handle case where ticker might contain underscores
    # We'll try different positions for strategy_type to find a valid one
    valid_strategies = ["SMA", "EMA", "MACD", "ATR"]

    ticker = None
    strategy_type = None
    remaining_parts = []

    # Try to find strategy type in the parts
    for i, part in enumerate(parts):
        if part in valid_strategies:
            ticker = "_".join(parts[:i]) if i > 0 else parts[0]
            strategy_type = part
            remaining_parts = parts[i + 1 :]
            break

    if strategy_type is None:
        raise ValueError(f"No valid strategy type found in: {strategy_uuid}")

    # Parse remaining parts based on strategy type and length
    if strategy_type in ["SMA", "EMA"]:
        # Handle both new and old formats for SMA/EMA
        if len(remaining_parts) < 2:
            raise ValueError(
                f"Invalid {strategy_type} strategy UUID format: {strategy_uuid}"
            )

        fast_period = remaining_parts[0]
        slow_period = remaining_parts[1]
        signal_period = "0"  # Default for SMA/EMA

        # Check for entry date, handling both old and new formats
        if len(remaining_parts) == 3:
            # Could be [short, long, entry_date] (new format) or [short, long, signal_period] (old format without date)
            third_part = remaining_parts[2]
            if (third_part.count("-") == 2 and len(third_part) == 10) or (
                len(third_part) == 8 and third_part.isdigit()
            ):
                # Looks like YYYY-MM-DD (old format) or YYYYMMDD (new format)
                entry_date = third_part
            elif third_part == "0":  # Old format signal period (should be ignored)
                entry_date = None
            else:
                # Assume it's an entry date in some other format
                entry_date = third_part
        elif len(remaining_parts) == 4:
            # Old format: [short, long, signal_period, entry_date]
            # Ignore the signal period (index 2) and use entry_date (index 3)
            entry_date = remaining_parts[3]
        elif len(remaining_parts) > 4:
            # Handle case where date might be split by underscores: [short, long, signal_period, YYYY, MM, DD]
            if (
                remaining_parts[2] == "0" and len(remaining_parts) >= 6
            ):  # Old format with split date
                date_parts = remaining_parts[
                    3:6
                ]  # Skip signal period, take next 3 parts
                if len(date_parts) == 3:
                    entry_date = "-".join(date_parts)
                else:
                    entry_date = remaining_parts[3]  # Use first date part
            else:
                # Reconstruct full date from all remaining parts after signal period
                date_parts = remaining_parts[2:]
                if len(date_parts) == 3:  # YYYY-MM-DD format
                    entry_date = "-".join(date_parts)
                else:
                    entry_date = remaining_parts[2]  # Use first part as date
        else:
            # No entry date
            entry_date = None

    else:
        # MACD, ATR, or other strategies that may use signal_period
        if len(remaining_parts) < 2:
            raise ValueError(
                f"Invalid {strategy_type} strategy UUID format: {strategy_uuid}"
            )
        elif len(remaining_parts) == 2:
            # Might be old format SMA/EMA with signal_period, or new format for non-SMA/EMA
            fast_period = remaining_parts[0]
            slow_period = remaining_parts[1]
            signal_period = "0"  # Default
            entry_date = None
        elif len(remaining_parts) == 3:
            # Could be: [short, long, signal] or [short, long, entry_date]
            fast_period = remaining_parts[0]
            slow_period = remaining_parts[1]

            # Try to determine if third part is signal_period or entry_date
            third_part = remaining_parts[2]
            if (third_part.count("-") == 2 and len(third_part) == 10) or (
                len(third_part) == 8 and third_part.isdigit()
            ):
                # Looks like YYYY-MM-DD (old format) or YYYYMMDD (new format)
                signal_period = "0"
                entry_date = third_part
            else:
                signal_period = third_part
                entry_date = None
        else:
            # Has signal_period and possibly entry_date
            fast_period = remaining_parts[0]
            slow_period = remaining_parts[1]
            signal_period = remaining_parts[2]

            # Check for entry date
            if len(remaining_parts) >= 4:
                entry_date_parts = remaining_parts[3:]
                if len(entry_date_parts) == 3:  # YYYY-MM-DD split by underscores
                    entry_date = "-".join(entry_date_parts)
                else:
                    entry_date = remaining_parts[3]
            else:
                entry_date = None

    # Convert numeric values to appropriate types
    try:
        # For ATR strategies, slow_period might be a float (multiplier)
        if strategy_type == "ATR":
            short_window_val = int(fast_period)
            long_window_val = float(slow_period)
        else:
            short_window_val = int(fast_period)
            long_window_val = int(slow_period)

        signal_window_val = int(signal_period)
    except ValueError:
        raise ValueError(f"Invalid numeric values in strategy UUID: {strategy_uuid}")

    return {
        "ticker": ticker,
        "strategy_type": strategy_type,
        "fast_period": short_window_val,
        "slow_period": long_window_val,
        "signal_period": signal_window_val,
        "entry_date": entry_date,
    }


def is_valid_strategy_uuid(strategy_uuid: str) -> bool:
    """Check if a string is a valid strategy UUID.

    Args:
        strategy_uuid: String to validate

    Returns:
        bool: True if the string is a valid strategy UUID, False otherwise
    """
    try:
        parse_strategy_uuid(strategy_uuid)
        return True
    except ValueError:
        return False


def extract_strategy_components(
    strategy_config: Dict[str, Any]
) -> Tuple[str, str, int, int, int]:
    """Extract strategy components from a configuration dictionary.

    Args:
        strategy_config: Strategy configuration dictionary

    Returns:
        Tuple[str, str, int, int, int]: (ticker, strategy_type, fast_period, slow_period, signal_period)

    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Extract required fields with appropriate case handling
    ticker = _get_config_value(strategy_config, ["TICKER", "Ticker", "ticker"])

    # Determine strategy type
    strategy_type = _get_strategy_type(strategy_config)

    # Get window parameters based on strategy type
    if strategy_type == "ATR":
        # ATR strategies use length and multiplier instead of windows
        fast_period = _get_config_value(strategy_config, ["LENGTH", "length"])
        slow_period = _get_config_value(strategy_config, ["MULTIPLIER", "multiplier"])
        # ATR doesn't use signal period, default to 0
        signal_period = 0
    else:
        # MA and MACD strategies use short and long windows
        fast_period = _get_config_value(
            strategy_config, ["FAST_PERIOD", "Fast Period", "fast_period"]
        )
        slow_period = _get_config_value(
            strategy_config, ["SLOW_PERIOD", "Slow Period", "slow_period"]
        )
        # Get signal period (default to 0 for MA strategies)
        signal_period = _get_config_value(
            strategy_config,
            ["SIGNAL_PERIOD", "Signal Period", "signal_period"],
            default=0,
        )

    return ticker, strategy_type, fast_period, slow_period, signal_period


def generate_strategy_id_from_config(strategy_config: Dict[str, Any]) -> str:
    """Generate a standardized strategy ID from a strategy configuration.

    Args:
        strategy_config: Strategy configuration dictionary

    Returns:
        str: Standardized strategy ID

    Raises:
        ValueError: If required fields are missing from the strategy configuration
    """
    (
        ticker,
        strategy_type,
        fast_period,
        slow_period,
        signal_period,
    ) = extract_strategy_components(strategy_config)

    return generate_strategy_id(
        ticker, strategy_type, fast_period, slow_period, signal_period
    )


def _get_config_value(
    config: Dict[str, Any], possible_keys: list, default: Any = None
) -> Any:
    """Get a value from a config dictionary, checking multiple possible keys.

    Args:
        config: Configuration dictionary
        possible_keys: List of possible keys to check
        default: Default value if no key is found

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
        config: Strategy configuration dictionary

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
    if "SIGNAL_PERIOD" in config or "signal_period" in config:
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
