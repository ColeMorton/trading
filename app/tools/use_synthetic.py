import os
from typing import Callable, Tuple

import polars as pl

from app.tools.data_types import DataConfig
from app.tools.download_data import download_data


def use_synthetic(
    ticker1: str, ticker2: str, config: DataConfig, log: Callable
) -> Tuple[pl.DataFrame, str]:
    """Create a synthetic pair from two tickers.

    Args:
        ticker1 (str): First ticker symbol
        ticker2 (str): Second ticker symbol
        config (DataConfig): Configuration dictionary
        log (Callable): Logging function

    Returns:
        Tuple[pl.DataFrame, str]: Synthetic pair data and synthetic ticker name
    """
    try:
        log(f"Creating synthetic pair from {ticker1} and {ticker2}")

        log(f"Downloading data for {ticker1}")
        data_ticker_1 = download_data(ticker1, config, log)

        log(f"Downloading data for {ticker2}")
        data_ticker_2 = download_data(ticker2, config, log)

        log("Merging data from both tickers")

        # Check if we have data to merge
        if len(data_ticker_1) == 0 or len(data_ticker_2) == 0:
            log("One or both datasets are empty", "error")
            return pl.DataFrame(), ""

        # Convert Date column to datetime if it's not already
        if data_ticker_1["Date"].dtype == pl.Utf8:
            data_ticker_1 = data_ticker_1.with_columns(pl.col("Date").str.to_datetime())
        if data_ticker_2["Date"].dtype == pl.Utf8:
            data_ticker_2 = data_ticker_2.with_columns(pl.col("Date").str.to_datetime())

        # Extract date part only (without time) for joining
        data_ticker_1 = data_ticker_1.with_columns(
            pl.col("Date").dt.truncate("1h").alias("DateHour")
        )
        data_ticker_2 = data_ticker_2.with_columns(
            pl.col("Date").dt.truncate("1h").alias("DateHour")
        )

        # Join on DateHour instead of exact timestamp
        data_merged = data_ticker_1.join(
            data_ticker_2, on="DateHour", how="inner", suffix="_2"
        )
        log(f"Merged data contains {len(data_merged)} rows")

        # If merged data is empty, try a more flexible approach
        if len(data_merged) == 0:
            log("No matching timestamps found, trying date-only matching", "warning")

            # Extract date part only (without time) for joining
            data_ticker_1 = data_ticker_1.with_columns(
                pl.col("Date").dt.date().alias("DateOnly")
            )
            data_ticker_2 = data_ticker_2.with_columns(
                pl.col("Date").dt.date().alias("DateOnly")
            )

            # Join on DateOnly
            data_merged = data_ticker_1.join(
                data_ticker_2, on="DateOnly", how="inner", suffix="_2"
            )
            log(f"Date-only merge contains {len(data_merged)} rows")

        log("Calculating synthetic pair ratios")

        # Create a new DataFrame with the expressions evaluated
        data_merged = data_merged.with_columns(
            [
                # Handle Open prices - fill nulls with Close prices
                pl.col("Open").fill_null(pl.col("Close")).alias("Open_clean"),
                pl.col("Open_2").fill_null(pl.col("Close_2")).alias("Open_2_clean"),
            ]
        ).with_columns(
            [
                # Replace zeros with Close prices
                pl.when(pl.col("Open_clean") == 0)
                .then(pl.col("Close"))
                .otherwise(pl.col("Open_clean"))
                .alias("Open_final"),
                pl.when(pl.col("Open_2_clean") == 0)
                .then(pl.col("Close_2"))
                .otherwise(pl.col("Open_2_clean"))
                .alias("Open_2_final"),
            ]
        )

        # Calculate ratios with clean data
        data = pl.DataFrame(
            {
                "Date": data_merged["Date"],
                "Close": (data_merged["Close"] / data_merged["Close_2"]).cast(
                    pl.Float64
                ),
                "Open": (data_merged["Open_final"] / data_merged["Open_2_final"]).cast(
                    pl.Float64
                ),
                "High": (data_merged["High"] / data_merged["High_2"]).cast(pl.Float64),
                "Low": (data_merged["Low"] / data_merged["Low_2"]).cast(pl.Float64),
                "Volume": data_merged["Volume"].cast(
                    pl.Float64
                ),  # Keep original volume
            }
        )

        log("Synthetic pair statistics:")

        # Check if data is empty
        if len(data) == 0:
            log("Synthetic pair data is empty", "error")
            return pl.DataFrame(), ""

        # Safely log statistics with null checks
        date_min = data["Date"].min()
        date_max = data["Date"].max()
        close_min = data["Close"].min()
        close_max = data["Close"].max()

        log(f"Date range: {date_min} to {date_max}")

        # Format only if values are not None
        if close_min is not None and close_max is not None:
            log(f"Ratio range: {close_min:.4f} to {close_max:.4f}")
        else:
            log("Ratio range: Unable to calculate (null values)")

        synthetic_ticker = f"{ticker1}_{ticker2}"

        # Export synthetic pair data directly with custom filename
        export_path = os.path.join(config.get("BASE_DIR", "."), "data", "raw", "prices")
        os.makedirs(export_path, exist_ok=True)

        # Create custom filename in format: {ticker1}_{ticker2}_{timeframe}.csv
        timeframe = "H" if config.get("USE_HOURLY", False) else "D"
        filename = f"{ticker1}_{ticker2}_{timeframe}.csv"
        full_path = os.path.join(export_path, filename)

        log("Exporting synthetic pair data to CSV")
        try:
            # Remove existing file if it exists
            if os.path.exists(full_path):
                os.remove(full_path)

            # Export data
            data.write_csv(full_path, separator=",")
            log(f"Successfully exported results to {full_path}")
            success = True
        except Exception as e:
            log(f"Failed to export synthetic pair data: {str(e)}", "error")
            success = False

        if success:
            log(f"Synthetic pair data exported successfully as {filename}")
        else:
            log("Failed to export synthetic pair data", "error")

        # Return the data and synthetic ticker for further processing
        if success:
            return data, synthetic_ticker
        else:
            log("Failed to create synthetic pair", "error")
            return pl.DataFrame(), ""

    except Exception as e:
        log(f"Error in use_synthetic: {str(e)}", "error")
        raise
