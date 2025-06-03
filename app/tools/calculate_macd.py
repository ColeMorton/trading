import logging

import polars as pl


def calculate_macd(
    data: pl.DataFrame, short_window: int, long_window: int, signal_window: int
) -> pl.DataFrame:
    """Calculate MACD and Signal Line using EMA.

    Args:
        data (pl.DataFrame): Price data with Close column
        short_window (int): Short EMA period
        long_window (int): Long EMA period
        signal_window (int): Signal line EMA period (must be >= 1)

    Returns:
        pl.DataFrame: DataFrame with MACD indicators added

    Raises:
        ValueError: If signal_window is less than 1
    """
    # Ensure signal_window is at least 1
    if signal_window < 1:
        logging.warning(
            f"Invalid signal_window value: {signal_window}. Using default value of 9 instead."
        )
        signal_window = 9  # Use a default value of 9 which is common for MACD

    logging.info(
        f"\nCalculating MACD with short period: {short_window}, long period: {long_window}, signal period: {signal_window}"
    )
    try:
        # Calculate EMAs with adjust=True for more accurate exponential weighting
        short_ema = data["Close"].ewm_mean(span=short_window, adjust=True)
        long_ema = data["Close"].ewm_mean(span=long_window, adjust=True)

        # Calculate MACD line (difference between short and long EMAs)
        macd = short_ema - long_ema

        # Calculate Signal line (EMA of MACD)
        signal = macd.ewm_mean(span=signal_window, adjust=True)

        # Calculate MACD histogram
        histogram = macd - signal

        # Add columns to dataframe
        data = data.with_columns(
            [
                macd.alias("MACD"),
                signal.alias("Signal_Line"),
                histogram.alias("MACD_Histogram"),
            ]
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
            ]
        )

        stats_row = stats.row(0, named=True)
        logging.info("\nMACD Statistics:")
        logging.info(
            f"MACD Range: {stats_row['macd_min']:.4f} to {stats_row['macd_max']:.4f}"
        )
        logging.info(
            f"Signal Line Range: {stats_row['signal_min']:.4f} to {stats_row['signal_max']:.4f}"
        )
        logging.info(
            f"Null values - MACD: {stats_row['macd_nulls']}, Signal Line: {stats_row['signal_nulls']}"
        )

        # Count potential crossovers
        crossovers = data.select(
            (
                (pl.col("MACD") > pl.col("Signal_Line"))
                & (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1))
                | (pl.col("MACD") < pl.col("Signal_Line"))
                & (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1))
            ).sum()
        ).item()

        logging.info(f"Potential crossover points: {crossovers}")

        # Log first few rows for verification
        sample = data.head(5)
        logging.info("\nFirst few rows:")
        for row in sample.iter_rows(named=True):
            logging.info(
                f"Date: {row['Date']}, Close: {row['Close']:.2f}, MACD: {row['MACD']:.4f}, Signal: {row['Signal_Line']:.4f}"
            )

        # Fill any null values that might have been created by the shift operations
        data = data.with_columns(
            [
                pl.col("MACD").fill_null(0).alias("MACD"),
                pl.col("Signal_Line").fill_null(0).alias("Signal_Line"),
                pl.col("MACD_Histogram").fill_null(0).alias("MACD_Histogram"),
            ]
        )

        return data

    except Exception as e:
        logging.error(f"Failed to calculate MACD: {e}")
        raise
