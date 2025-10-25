"""
COMP Strategy Calculator

Calculates compound signals based on the percentage of component strategies
that are currently in position.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import polars as pl

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals


def load_component_strategies(csv_path: str | Path) -> list[dict[str, Any]]:
    """
    Load component strategies from a CSV file.

    Args:
        csv_path: Path to the strategies CSV file

    Returns:
        List of strategy dictionaries with parameters
    """
    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Strategy CSV file not found: {csv_path}")

    # Read CSV using pandas
    df = pd.read_csv(csv_path)

    strategies = []
    for _, row in df.iterrows():
        strategy = {
            "ticker": row.get("Ticker", ""),
            "strategy_type": row.get("Strategy Type", "SMA"),
            "fast_period": int(row.get("Fast Period", 0)),
            "slow_period": int(row.get("Slow Period", 0)),
        }

        # Add signal period for MACD strategies
        if strategy["strategy_type"].upper() == "MACD":
            strategy["signal_period"] = int(row.get("Signal Period", 9))

        strategies.append(strategy)

    return strategies


def calculate_component_position(
    data: pl.DataFrame,
    strategy: dict[str, Any],
    config: dict,
    log: Callable,
) -> pl.Series | None:
    """
    Calculate position status (0 or 1) for a single component strategy.

    Args:
        data: Price data
        strategy: Strategy parameters dict
        config: Configuration dict
        log: Logging function

    Returns:
        Polars Series with position values (0 or 1) or None if calculation fails
    """
    try:
        strategy_type = strategy["strategy_type"].upper()
        fast_period = strategy["fast_period"]
        slow_period = strategy["slow_period"]

        # Create a copy of data to avoid modifying original
        temp_data = data.clone()

        # Create strategy-specific config (override STRATEGY_TYPE to match component strategy)
        strategy_config = {**config, "STRATEGY_TYPE": strategy_type}

        # Calculate signals based on strategy type
        if strategy_type in ["SMA", "EMA"]:
            temp_data = calculate_ma_and_signals(
                temp_data,
                fast_period,
                slow_period,
                strategy_config,
                log,
                strategy_type=strategy_type,
            )
        elif strategy_type == "MACD":
            signal_period = strategy.get("signal_period", 9)
            temp_data = calculate_macd_and_signals(
                temp_data,
                fast_period,
                slow_period,
                signal_period,
                strategy_config,
                log,
            )
        else:
            log(f"Unsupported strategy type: {strategy_type}", "warning")
            return None

        # Extract position column
        if "Position" in temp_data.columns:
            # Position column exists - use it directly
            position = temp_data["Position"]
        elif "Signal" in temp_data.columns:
            # Fall back to Signal column if Position doesn't exist
            # Convert signal to position (shift by 1 to simulate entry at next bar)
            position = temp_data["Signal"].shift(1).fill_null(0)
        else:
            log(f"No Position or Signal column found for {strategy_type}", "warning")
            return None

        # Ensure position is binary (0 or 1)
        # Handle any potential non-zero values as "in position"
        position = (position != 0).cast(pl.Int32)

        return position

    except Exception as e:
        log(f"Error calculating position for strategy {strategy}: {e}", "error")
        return None


def aggregate_positions(
    data: pl.DataFrame,
    component_positions: list[pl.Series],
    log: Callable,
) -> pl.DataFrame:
    """
    Aggregate component strategy positions and calculate percentage in position.

    Args:
        data: Original price data with Date column
        component_positions: List of position series from component strategies
        log: Logging function

    Returns:
        DataFrame with Date and percentage_in_position columns
    """
    if not component_positions:
        raise ValueError("No component positions to aggregate")

    # Stack all position series into a DataFrame
    positions_df = pl.DataFrame(
        {f"strategy_{i}": pos for i, pos in enumerate(component_positions)}
    )

    # Calculate sum of positions (number of strategies in position)
    # Use select to evaluate the expression first, then extract the column
    sum_df = positions_df.select(pl.sum_horizontal(pl.all()))
    # Get the first (and only) column regardless of its name
    total_in_position = sum_df.to_numpy().flatten()

    # Calculate percentage (0 to 100)
    total_strategies = len(component_positions)
    percentage = (total_in_position / total_strategies) * 100.0

    # Create result DataFrame with Date from original data
    result = pl.DataFrame(
        {
            "Date": data["Date"].to_list(),  # Convert to list to avoid Expr issues
            "percentage_in_position": percentage,
            "num_in_position": total_in_position,
            "total_strategies": [total_strategies] * len(data),  # Repeat for each row
        }
    )

    log(
        f"Aggregated {total_strategies} component strategies. "
        f"Percentage range: {percentage.min():.1f}% to {percentage.max():.1f}%"
    )

    return result


def generate_compound_signals(
    aggregated_data: pl.DataFrame,
    threshold: float = 50.0,
    log: Callable = None,
) -> pl.DataFrame:
    """
    Generate compound entry/exit signals based on percentage threshold crossings.

    Entry: percentage crosses from <50% to >=50%
    Exit: percentage crosses from >=50% to <50%

    Args:
        aggregated_data: DataFrame with percentage_in_position column
        threshold: Percentage threshold for signals (default 50.0)
        log: Optional logging function

    Returns:
        DataFrame with Signal and Position columns added
    """
    # Create a copy to avoid modifying original
    data = aggregated_data.clone()

    # Initialize signal column (0 = no position, 1 = in position)
    percentage = data["percentage_in_position"].to_numpy()
    signals = np.zeros(len(percentage), dtype=np.int32)

    # Track if we're currently in a position
    in_position = False
    entry_count = 0
    exit_count = 0

    for i in range(len(percentage)):
        current_pct = percentage[i]

        if not in_position:
            # Check for entry: percentage >= threshold
            if current_pct >= threshold:
                in_position = True
                signals[i] = 1
                entry_count += 1
            else:
                signals[i] = 0
        # We're in position
        # Check for exit: percentage < threshold
        elif current_pct < threshold:
            in_position = False
            signals[i] = 0
            exit_count += 1
        else:
            # Stay in position
            signals[i] = 1

    # Add Signal and Position columns to DataFrame
    data = data.with_columns(
        [
            pl.Series("Signal", signals),
            pl.Series("Position", signals).shift(1).fill_null(0).cast(pl.Int32),
        ]
    )

    if log:
        log(f"Generated {entry_count} entry signals and {exit_count} exit signals")
        log(
            f"Final position status: {'in position' if in_position else 'not in position'}"
        )

    return data


def calculate_compound_strategy(
    data: pl.DataFrame,
    csv_path: str | Path,
    config: dict,
    log: Callable,
) -> pl.DataFrame | None:
    """
    Main function to calculate compound strategy signals.

    Args:
        data: Price data
        csv_path: Path to component strategies CSV
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame with compound signals or None if calculation fails
    """
    try:
        # Load component strategies from CSV
        log(f"Loading component strategies from {csv_path}")
        component_strategies = load_component_strategies(csv_path)
        log(f"Loaded {len(component_strategies)} component strategies")

        if not component_strategies:
            log("No component strategies found in CSV", "error")
            return None

        # Calculate position for each component strategy
        log("Calculating positions for component strategies...")
        component_positions = []

        for i, strategy in enumerate(component_strategies):
            strategy_name = (
                f"{strategy['strategy_type']} "
                f"{strategy['fast_period']}/{strategy['slow_period']}"
            )
            if strategy["strategy_type"].upper() == "MACD":
                strategy_name += f"/{strategy.get('signal_period', 9)}"

            log(
                f"  [{i+1}/{len(component_strategies)}] Processing {strategy_name}",
                "debug",
            )

            position = calculate_component_position(data, strategy, config, log)

            if position is not None:
                component_positions.append(position)
            else:
                log(f"  Failed to calculate position for {strategy_name}", "warning")

        if not component_positions:
            log("Failed to calculate positions for any component strategy", "error")
            return None

        log(
            f"Successfully calculated positions for {len(component_positions)}/{len(component_strategies)} strategies"
        )

        # Aggregate positions
        log("Aggregating component positions...")
        aggregated = aggregate_positions(data, component_positions, log)

        # Generate compound signals
        log("Generating compound signals...")
        result = generate_compound_signals(aggregated, threshold=50.0, log=log)

        # Add price data columns needed for backtesting
        result = result.with_columns(
            [
                data["Open"],
                data["High"],
                data["Low"],
                data["Close"],
                data["Volume"],
            ]
        )

        return result

    except Exception as e:
        log(f"Error calculating compound strategy: {e}", "error")
        import traceback

        log(traceback.format_exc(), "error")
        return None
