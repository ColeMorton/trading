import polars as pl

def calculate_macd_signals(data, short):
    """Generate trading signals based on MACD cross."""
    if short:
        # Short-only strategy
        data = data.with_columns(pl.lit(0).alias("Signal"))
        data = data.with_columns(
            pl.when(pl.col("MACD") < pl.col("Signal_Line"))
            .then(-1)
            .otherwise(0)
            .alias("Signal")
        )
    else:
        # Long-only strategy
        data = data.with_columns(pl.lit(0).alias("Signal"))
        data = data.with_columns(
            pl.when(pl.col("MACD") > pl.col("Signal_Line"))
            .then(1)
            .otherwise(0)
            .alias("Signal")
        )
    data = data.with_columns(pl.col("Signal").shift(1).alias("Position"))
    return data