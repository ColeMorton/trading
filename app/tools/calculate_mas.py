from typing import Callable

import polars as pl


def calculate_mas(
    data: pl.DataFrame, fast_window: int, slow_window: int, use_sma: bool, log: Callable
) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA).

    Args:
        data: Price data DataFrame
        fast_window: Fast MA window size
        slow_window: Slow MA window size
        use_sma: If True, use Simple Moving Average, otherwise use Exponential Moving Average

    Returns:
        DataFrame with MA columns added
    """
    log(
        f"Calculating {'SMA' if use_sma else 'EMA'} with windows {fast_window}, {slow_window}"
    )
    log(f"Input data shape: {data.shape}")

    if use_sma:
        result = data.with_columns(
            [
                pl.col("Close")
                .cast(pl.Float64)
                .rolling_mean(window_size=fast_window)
                .alias("MA_FAST"),
                pl.col("Close")
                .cast(pl.Float64)
                .rolling_mean(window_size=slow_window)
                .alias("MA_SLOW"),
            ]
        )
    else:
        result = data.with_columns(
            [
                pl.col("Close")
                .cast(pl.Float64)
                .ewm_mean(span=fast_window, adjust=False)
                .alias("MA_FAST"),
                pl.col("Close")
                .cast(pl.Float64)
                .ewm_mean(span=slow_window, adjust=False)
                .alias("MA_SLOW"),
            ]
        )

    # Count non-null values in MA columns
    valid_fast = result.select(pl.col("MA_FAST").is_not_null()).sum().item()
    valid_slow = result.select(pl.col("MA_SLOW").is_not_null()).sum().item()
    log(f"Valid MA points - Fast: {valid_fast}, Slow: {valid_slow}")

    return result
