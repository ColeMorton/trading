import logging

import polars as pl


def calculate_macd_signals(data, short):
    """Generate trading signals based on MACD cross."""
    try:
        # Create crossover signals
        if short:
            # Short-only strategy
            data = data.with_columns(
                [
                    # Generate signal when MACD crosses Signal Line
                    pl.when(
                        (pl.col("MACD") < pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1)),
                    )
                    .then(-1)  # Enter short
                    .when(
                        (pl.col("MACD") > pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1)),
                    )
                    .then(0)  # Exit short
                    .otherwise(pl.lit(None))  # No signal
                    .alias("Signal"),
                ],
            )
        else:
            # Long-only strategy
            data = data.with_columns(
                [
                    # Generate signal when MACD crosses Signal Line
                    pl.when(
                        (pl.col("MACD") > pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1)),
                    )
                    .then(1)  # Enter long
                    .when(
                        (pl.col("MACD") < pl.col("Signal_Line"))
                        & (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1)),
                    )
                    .then(0)  # Exit long
                    .otherwise(pl.lit(None))  # No signal
                    .alias("Signal"),
                ],
            )

        # Forward fill signals between crossovers
        data = data.with_columns(
            [pl.col("Signal").forward_fill().fill_null(0).alias("Signal")],
        )

        # Log signal statistics
        signal_counts = (
            data.group_by("Signal")
            .agg([pl.count("Signal").alias("count")])
            .sort("Signal")
        )
        logging.info("\nSignal distribution:")
        logging.info(signal_counts)

        # Log crossover points for verification
        crossovers = data.filter(
            pl.col("Signal").is_not_null() & (pl.col("Signal") != 0),
        )
        if len(crossovers) > 0:
            logging.info("\nFirst few crossover points:")
            sample = crossovers.head(5)
            for row in sample.iter_rows(named=True):
                logging.info(
                    f"Date: {row['Date']}, MACD: {row['MACD']:.4f}, Signal Line: {row['Signal_Line']:.4f}, Signal: {row['Signal']}",
                )

        return data

    except Exception as e:
        logging.exception(f"Failed to calculate signals: {e}")
        raise
