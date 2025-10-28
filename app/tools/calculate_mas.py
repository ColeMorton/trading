from collections.abc import Callable

import polars as pl


def calculate_mas(
    data: pl.DataFrame,
    fast_period: int,
    slow_period: int,
    use_sma: bool,
    log: Callable,
) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA).

    Args:
        data: Price data DataFrame
        fast_period: Fast MA period
        slow_period: Slow MA period
        use_sma: If True, use Simple Moving Average, otherwise use Exponential Moving Average

    Returns:
        DataFrame with MA columns added
    """
    log(
        f"Calculating {'SMA' if use_sma else 'EMA'} with periods {fast_period}, {slow_period}",
        "debug",
    )
    log(f"Input data shape: {data.shape}", "debug")

    if use_sma:
        result = data.with_columns(
            [
                pl.col("Close")
                .cast(pl.Float64)
                .rolling_mean(window_size=fast_period)
                .alias("MA_FAST"),
                pl.col("Close")
                .cast(pl.Float64)
                .rolling_mean(window_size=slow_period)
                .alias("MA_SLOW"),
            ],
        )
    else:
        result = data.with_columns(
            [
                pl.col("Close")
                .cast(pl.Float64)
                .ewm_mean(span=fast_period, adjust=False)
                .alias("MA_FAST"),
                pl.col("Close")
                .cast(pl.Float64)
                .ewm_mean(span=slow_period, adjust=False)
                .alias("MA_SLOW"),
            ],
        )

    # Count non-null values in MA columns
    valid_fast = result.select(pl.col("MA_FAST").is_not_null()).sum().item()
    valid_slow = result.select(pl.col("MA_SLOW").is_not_null()).sum().item()
    log(f"Valid MA points - Fast: {valid_fast}, Slow: {valid_slow}", "debug")

    return result
