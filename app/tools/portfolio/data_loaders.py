"""Portfolio data loading utilities.

This module provides functions for loading strategy configurations from CSV files.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import polars as pl

from app.tools.console_logging import ConsoleLogger
from app.tools.portfolio.format import convert_csv_to_strategy_config


if TYPE_CHECKING:
    from app.cli.models.portfolio import ReviewStrategyConfig


def load_strategies_from_raw_csv(
    raw_strategies_name: str, console: ConsoleLogger = None
) -> list["ReviewStrategyConfig"]:
    """
    Load strategy configurations from a CSV file in data/raw/strategies/.

    Args:
        raw_strategies_name: Name of the CSV file (without .csv extension)
        console: Optional console logger for output

    Returns:
        List of ReviewStrategyConfig objects

    Raises:
        ValueError: If CSV file doesn't exist or has invalid data
    """
    # Construct CSV file path
    csv_path = Path("data/raw/strategies") / f"{raw_strategies_name}.csv"

    if not csv_path.exists():
        raise ValueError(f"Raw strategies CSV file does not exist: {csv_path}")

    try:
        # Load CSV using polars
        df = pl.read_csv(str(csv_path))

        # Use console logger if provided, fallback to default
        if console is None:
            console = ConsoleLogger()

        # Simple logging function for the conversion
        def log(message: str, level: str = "info"):
            if level == "error":
                console.error(message)
            elif level == "warning":
                console.warning(message)
            else:
                console.debug(message)

        # Use existing CSV conversion system
        config = {"BASE_DIR": ".", "REFRESH": True, "USE_HOURLY": False}
        strategy_configs = convert_csv_to_strategy_config(df, log, config)

        # Import here to avoid circular import
        from app.cli.models.portfolio import (
            Direction,
            ReviewStrategyConfig,
            StrategyType,
        )

        # Convert to ReviewStrategyConfig objects
        review_strategies = []
        for strategy_config in strategy_configs:
            # Map strategy types
            strategy_type_str = strategy_config.get("STRATEGY_TYPE", "SMA")
            try:
                strategy_type = StrategyType(strategy_type_str)
            except ValueError:
                # Default to SMA if unknown strategy type
                strategy_type = StrategyType.SMA

            # Map direction
            direction_str = strategy_config.get("DIRECTION", "long").lower()
            try:
                direction = Direction(direction_str)
            except ValueError:
                # Default to long if unknown direction
                direction = Direction.LONG

            # Create ReviewStrategyConfig
            review_strategy = ReviewStrategyConfig(
                ticker=strategy_config["TICKER"],
                fast_period=strategy_config.get("FAST_PERIOD", 20),
                slow_period=strategy_config.get("SLOW_PERIOD", 50),
                strategy_type=strategy_type,
                direction=direction,
                stop_loss=strategy_config.get("STOP_LOSS"),
                position_size=strategy_config.get("POSITION_SIZE", 1.0),
                use_hourly=strategy_config.get("USE_HOURLY", False),
                rsi_window=strategy_config.get("RSI_WINDOW"),
                rsi_threshold=strategy_config.get("RSI_THRESHOLD"),
                signal_period=strategy_config.get("SIGNAL_PERIOD", 9),
            )

            review_strategies.append(review_strategy)

        console.success(
            f"Successfully loaded {len(review_strategies)} strategies from {csv_path}"
        )
        return review_strategies

    except Exception as e:
        raise ValueError(f"Failed to load strategies from CSV {csv_path}: {e}")
