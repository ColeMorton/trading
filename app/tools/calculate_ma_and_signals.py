from collections.abc import Callable

import polars as pl

from app.tools.strategy.factory import factory


def calculate_ma_and_signals(
    data: pl.DataFrame,
    fast_period: int,
    slow_period: int,
    config: dict,
    log: Callable,
    strategy_type: str = "EMA",
) -> pl.DataFrame:
    """
    Calculate MAs and generate trading signals using the strategy factory.

    This function now uses the factory pattern to create and execute strategies,
    making it easier to add new strategy types in the future.

    Args:
        data (pl.DataFrame): Input price data
        fast_period (int): Fast moving average period
        slow_period (int): Slow moving average period
        config (dict): Configuration dictionary
        log (Callable): Logging function
        strategy_type (str, optional): Strategy type to use (SMA or EMA). Defaults to "EMA".

    Returns:
        pl.DataFrame: Data with moving averages, signals, and positions
    """
    # Use strategy type from config if available, otherwise use the provided parameter
    strategy_type = config.get("STRATEGY_TYPE", strategy_type)

    try:
        # Create strategy instance using factory
        strategy = factory.create_strategy(strategy_type)

        # Execute strategy calculation
        result = strategy.calculate(data, fast_period, slow_period, config, log)

        return result

    except Exception as e:
        # Log error with context
        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Failed to calculate {direction} {strategy_type}s and signals: {e}",
            "error",
        )
        raise
