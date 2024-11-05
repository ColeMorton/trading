import polars as pl

def calculate_mas(data: pl.DataFrame, fast_window: int, slow_window: int, use_sma: bool = False) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA)."""
    if use_sma:
        return data.with_columns([
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=fast_window).alias("MA_FAST"),
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=slow_window).alias("MA_SLOW")
        ])
    else:
        return data.with_columns([
            pl.col("Close").cast(pl.Float64).ewm_mean(span=fast_window, adjust=False).alias("MA_FAST"),
            pl.col("Close").cast(pl.Float64).ewm_mean(span=slow_window, adjust=False).alias("MA_SLOW")
        ])
