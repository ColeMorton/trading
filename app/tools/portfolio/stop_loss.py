"""Stop loss utility module for portfolio management.

This module provides utility functions for working with stop loss values
in portfolio data. It handles validation, processing, and calculation of
stop loss levels based on price data.

The module implements functionality for:
1. Validating stop loss values in portfolio data
2. Calculating stop loss levels based on entry prices
3. Applying stop loss rules to trading strategies
"""

from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, TypeVar


# Type variable for generic portfolio data
T = TypeVar("T", dict[str, Any], dict[str, str | float | int | None])


def get_stop_loss_field_name(row: dict[str, Any]) -> str:
    """Get the stop loss field name from a row.

    Handles different variations of the stop loss field name.

    Args:
        row: Dictionary representing a row in portfolio data

    Returns:
        str: The stop loss field name
    """
    # Check for different variations of the stop loss field name
    for field in ["Stop Loss [%]", "Stop Loss", "Stop_Loss"]:
        if field in row:
            return field

    # Default field name if not found
    return "Stop Loss [%]"


def validate_stop_loss(
    portfolio_data: list[T], log: Callable[[str, str | None], None] | None = None,
) -> list[dict[str, Any]]:
    """Validate stop loss values in portfolio data.

    Checks that stop loss values are valid numbers between 0 and 100.

    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function

    Returns:
        List of dictionaries with validated stop loss values
    """
    if not portfolio_data:
        return []

    validated_data = []

    for row in portfolio_data:
        validated_row = dict(row)
        stop_loss_field = get_stop_loss_field_name(row)

        # Validate stop loss value if present
        if stop_loss_field in row and row[stop_loss_field] not in (None, "", "None"):
            try:
                # Convert to float and validate range
                stop_loss_value = float(row[stop_loss_field])
                if stop_loss_value < 0 or stop_loss_value > 100:
                    if log:
                        log(
                            f"Invalid stop loss value {stop_loss_value} for {row.get('Ticker', 'Unknown')}: "
                            "must be between 0 and 100. Setting to None.",
                            "warning",
                        )
                    validated_row[stop_loss_field] = None
                else:
                    validated_row[stop_loss_field] = stop_loss_value
            except (ValueError, TypeError):
                if log:
                    log(
                        f"Invalid stop loss value {row[stop_loss_field]} for {row.get('Ticker', 'Unknown')}: "
                        "must be a number. Setting to None.",
                        "warning",
                    )
                validated_row[stop_loss_field] = None

        validated_data.append(validated_row)

    return validated_data


def normalize_stop_loss(
    portfolio_data: list[T], log: Callable[[str, str | None], None] | None = None,
) -> list[dict[str, Any]]:
    """Normalize stop loss values in portfolio data.

    Ensures all rows have a stop loss field with proper formatting.

    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function

    Returns:
        List of dictionaries with normalized stop loss values
    """
    if not portfolio_data:
        return []

    normalized_data = []
    standard_stop_loss_field = "Stop Loss [%]"

    for row in portfolio_data:
        normalized_row = dict(row)

        # Find the stop loss field if it exists with any variation
        stop_loss_field = None
        stop_loss_value = None

        for field in ["Stop Loss [%]", "Stop Loss", "Stop_Loss"]:
            if field in row:
                stop_loss_field = field
                stop_loss_value = row[field]
                break

        # Normalize the field name to the standard format
        if stop_loss_field and stop_loss_field != standard_stop_loss_field:
            normalized_row[standard_stop_loss_field] = stop_loss_value
            del normalized_row[stop_loss_field]
        elif standard_stop_loss_field not in normalized_row:
            normalized_row[standard_stop_loss_field] = None

        normalized_data.append(normalized_row)

    return normalized_data


def calculate_stop_loss_levels(
    portfolio_data: list[T],
    entry_prices: dict[str, float],
    log: Callable[[str, str | None], None] | None = None,
) -> list[dict[str, Any]]:
    """Calculate stop loss levels based on entry prices.

    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        entry_prices: Dictionary mapping tickers to entry prices
        log: Optional logging function

    Returns:
        List of dictionaries with stop loss levels added
    """
    if not portfolio_data or not entry_prices:
        return portfolio_data

    # First ensure stop loss values are valid
    validated_data = validate_stop_loss(portfolio_data, log)
    stop_loss_field = "Stop Loss [%]"

    # Add stop loss level to each row
    for row in validated_data:
        ticker = row.get("Ticker")
        if not ticker:
            continue

        stop_loss = row.get(stop_loss_field)
        entry_price = entry_prices.get(ticker)

        if (
            stop_loss is not None
            and stop_loss not in ("", "None")
            and entry_price is not None
        ):
            try:
                # Convert percentage to decimal
                stop_loss_decimal = float(stop_loss) / 100.0

                # Calculate stop loss level based on direction
                direction = row.get("direction", "LONG")
                if direction.upper() == "LONG":
                    # For long positions, stop loss is below entry price
                    stop_level = entry_price * (1 - stop_loss_decimal)
                else:
                    # For short positions, stop loss is above entry price
                    stop_level = entry_price * (1 + stop_loss_decimal)

                # Round to appropriate decimal places based on price magnitude
                if entry_price < 1:
                    # For low-priced assets, use more decimal places
                    decimal_places = 6
                elif entry_price < 10:
                    decimal_places = 4
                elif entry_price < 100:
                    decimal_places = 3
                elif entry_price < 1000:
                    decimal_places = 2
                else:
                    decimal_places = 2

                # Format the stop level with appropriate precision
                stop_level_decimal = Decimal(str(stop_level)).quantize(
                    Decimal("0." + "0" * decimal_places), rounding=ROUND_HALF_UP,
                )
                row["Stop Level"] = float(stop_level_decimal)
            except (ValueError, TypeError):
                if log:
                    log(
                        f"Could not calculate stop loss level for {ticker}: "
                        f"invalid stop loss value {stop_loss} or entry price {entry_price}",
                        "warning",
                    )
                row["Stop Level"] = None
        else:
            row["Stop Level"] = None

    return validated_data


def apply_stop_loss_rules(
    strategy: dict[str, Any],
    prices: dict[str, list[dict[str, Any]]],
    use_candle_close: bool = True,
    log: Callable[[str, str | None], None] | None = None,
) -> dict[str, Any]:
    """Apply stop loss rules to a strategy based on price data.

    Args:
        strategy: Dictionary representing a trading strategy
        prices: Dictionary mapping tickers to price data
        use_candle_close: Whether to use candle close for stop loss (vs. intracandle)
        log: Optional logging function

    Returns:
        Updated strategy dictionary with stop loss information
    """
    ticker = strategy.get("ticker") or strategy.get("Ticker")
    if not ticker or ticker not in prices:
        return strategy

    # Get stop loss percentage
    stop_loss_percent = None
    for field in ["stop_loss", "Stop Loss [%]", "Stop Loss", "Stop_Loss"]:
        if field in strategy and strategy[field] not in (None, "", "None"):
            try:
                stop_loss_percent = float(strategy[field])
                break
            except (ValueError, TypeError):
                pass

    if stop_loss_percent is None or stop_loss_percent <= 0:
        return strategy

    # Create a copy of the strategy to avoid modifying the original
    updated_strategy = dict(strategy)

    # Get direction (default to LONG if not specified)
    direction = (strategy.get("direction") or "LONG").upper()

    # Get price data for the ticker
    ticker_prices = prices[ticker]
    if not ticker_prices:
        return updated_strategy

    # Find entry point (first signal)
    entry_index = None
    entry_price = None

    for i, candle in enumerate(ticker_prices):
        if candle.get("signal") == 1:  # Entry signal
            entry_index = i
            entry_price = candle.get("close")
            break

    if entry_index is None or entry_price is None:
        return updated_strategy

    # Calculate stop loss level
    stop_loss_decimal = stop_loss_percent / 100.0
    if direction == "LONG":
        stop_level = entry_price * (1 - stop_loss_decimal)
    else:
        stop_level = entry_price * (1 + stop_loss_decimal)

    # Add stop loss information to strategy
    updated_strategy["stop_level"] = stop_level
    updated_strategy["entry_price"] = entry_price

    # Check if stop loss was triggered
    stop_triggered = False
    stop_price = None
    stop_date = None

    for i in range(entry_index + 1, len(ticker_prices)):
        candle = ticker_prices[i]

        if use_candle_close:
            # Only check close price
            if (direction == "LONG" and candle.get("close") <= stop_level) or (
                direction == "SHORT" and candle.get("close") >= stop_level
            ):
                stop_triggered = True
                stop_price = candle.get("close")
                stop_date = candle.get("date")
                break
        # Check intracandle (high/low)
        elif (direction == "LONG" and candle.get("low") <= stop_level) or (
            direction == "SHORT" and candle.get("high") >= stop_level
        ):
            stop_triggered = True
            stop_price = stop_level
            stop_date = candle.get("date")
            break

    if stop_triggered:
        updated_strategy["stop_triggered"] = True
        updated_strategy["stop_price"] = stop_price
        updated_strategy["stop_date"] = stop_date
    else:
        updated_strategy["stop_triggered"] = False

    return updated_strategy


def get_stop_loss_summary(
    portfolio_data: list[T], log: Callable[[str, str | None], None] | None = None,
) -> dict[str, Any]:
    """Get a summary of stop loss statistics for the portfolio.

    Args:
        portfolio_data: List of dictionaries representing portfolio rows
        log: Optional logging function

    Returns:
        Dictionary with stop loss summary statistics
    """
    if not portfolio_data:
        return {
            "strategies_with_stop_loss": 0,
            "strategies_without_stop_loss": 0,
            "total_strategies": 0,
            "average_stop_loss": None,
            "min_stop_loss": None,
            "max_stop_loss": None,
        }

    stop_loss_field = "Stop Loss [%]"
    strategies_with_stop_loss = 0
    strategies_without_stop_loss = 0
    stop_loss_values = []

    for row in portfolio_data:
        if stop_loss_field in row and row[stop_loss_field] not in (None, "", "None"):
            try:
                stop_loss = float(row[stop_loss_field])
                stop_loss_values.append(stop_loss)
                strategies_with_stop_loss += 1
            except (ValueError, TypeError):
                strategies_without_stop_loss += 1
        else:
            strategies_without_stop_loss += 1

    total_strategies = strategies_with_stop_loss + strategies_without_stop_loss

    # Calculate statistics
    average_stop_loss = (
        sum(stop_loss_values) / len(stop_loss_values) if stop_loss_values else None
    )
    min_stop_loss = min(stop_loss_values) if stop_loss_values else None
    max_stop_loss = max(stop_loss_values) if stop_loss_values else None

    return {
        "strategies_with_stop_loss": strategies_with_stop_loss,
        "strategies_without_stop_loss": strategies_without_stop_loss,
        "total_strategies": total_strategies,
        "average_stop_loss": average_stop_loss,
        "min_stop_loss": min_stop_loss,
        "max_stop_loss": max_stop_loss,
    }
