import logging

import polars as pl


def calculate_macd(
    data: pl.DataFrame,
    fast_period: int,
    slow_period: int,
    signal_period: int,
) -> pl.DataFrame:
    """Calculate MACD and Signal Line using EMA.

    Args:
        data (pl.DataFrame): Price data with Close column
        fast_period (int): Fast EMA period
        slow_period (int): Slow EMA period
        signal_period (int): Signal line EMA period (must be >= 1)

    Returns:
        pl.DataFrame: DataFrame with MACD indicators added

    Raises:
        ValueError: If signal_period is less than 1
    """
    # Ensure signal_period is at least 1
    if signal_period < 1:
        logging.warning(
            f"Invalid signal_period value: {signal_period}. Using default value of 9 instead.",
        )
        signal_period = 9  # Use a default value of 9 which is common for MACD

    logging.info(
        f"\nCalculating MACD with fast period: {fast_period}, slow period: {slow_period}, signal period: {signal_period}",
    )
    try:
        # Calculate EMAs with adjust=True for more accurate exponential weighting
        fast_ema = data["Close"].ewm_mean(span=fast_period, adjust=True)
        slow_ema = data["Close"].ewm_mean(span=slow_period, adjust=True)

        # Calculate MACD line (difference between fast and slow EMAs)
        macd = fast_ema - slow_ema

        # Calculate Signal line (EMA of MACD)
        signal = macd.ewm_mean(span=signal_period, adjust=True)

        # Calculate MACD histogram
        histogram = macd - signal

        # Add columns to dataframe
        data = data.with_columns(
            [
                macd.alias("MACD"),
                signal.alias("Signal_Line"),
                histogram.alias("MACD_Histogram"),
            ],
        )

        # Calculate and log statistics
        stats = data.select(
            [
                pl.col("MACD").min().alias("macd_min"),
                pl.col("MACD").max().alias("macd_max"),
                pl.col("Signal_Line").min().alias("signal_min"),
                pl.col("Signal_Line").max().alias("signal_max"),
                pl.col("MACD").is_null().sum().alias("macd_nulls"),
                pl.col("Signal_Line").is_null().sum().alias("signal_nulls"),
            ],
        )

        stats_row = stats.row(0, named=True)
        logging.info("\nMACD Statistics:")
        logging.info(
            f"MACD Range: {stats_row['macd_min']:.4f} to {stats_row['macd_max']:.4f}",
        )
        logging.info(
            f"Signal Line Range: {stats_row['signal_min']:.4f} to {stats_row['signal_max']:.4f}",
        )
        logging.info(
            f"Null values - MACD: {stats_row['macd_nulls']}, Signal Line: {stats_row['signal_nulls']}",
        )

        # Count potential crossovers
        crossovers = data.select(
            (
                (pl.col("MACD") > pl.col("Signal_Line"))
                & (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1))
                | (pl.col("MACD") < pl.col("Signal_Line"))
                & (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1))
            ).sum(),
        ).item()

        logging.info(f"Potential crossover points: {crossovers}")

        # Log first few rows for verification
        sample = data.head(5)
        logging.info("\nFirst few rows:")
        for row in sample.iter_rows(named=True):
            logging.info(
                f"Date: {row['Date']}, Close: {row['Close']:.2f}, MACD: {row['MACD']:.4f}, Signal: {row['Signal_Line']:.4f}",
            )

        # Fill any null values that might have been created by the shift operations
        return data.with_columns(
            [
                pl.col("MACD").fill_null(0).alias("MACD"),
                pl.col("Signal_Line").fill_null(0).alias("Signal_Line"),
                pl.col("MACD_Histogram").fill_null(0).alias("MACD_Histogram"),
            ],
        )

    except Exception as e:
        logging.exception(f"Failed to calculate MACD: {e}")
        raise
