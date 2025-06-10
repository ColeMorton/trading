from datetime import datetime, timedelta
from typing import Callable
import threading

import polars as pl
import yfinance as yf

from app.tools.data_types import DataConfig
from app.tools.export_csv import ExportConfig, export_csv

# Thread lock for yfinance downloads to prevent concurrent access issues
_yfinance_lock = threading.Lock()


def download_data(ticker: str, config: DataConfig, log: Callable) -> pl.DataFrame:
    """Download historical data from Yahoo Finance and export to CSV.

    Args:
        ticker (str): Stock ticker symbol
        config (DataConfig): Configuration dictionary
        log (Callable): Logging function

    Returns:
        pl.DataFrame: Downloaded price data

    Raises:
        ValueError: If no data is downloaded
    """
    try:
        log(f"Initiating data download for {ticker}")

        use_hourly = config.get("USE_HOURLY", False)
        interval = "1h" if use_hourly else "1d"
        log(f"Using {interval} interval for data download")

        # Calculate date range
        end_date = datetime.now()

        if use_hourly:
            start_date = end_date - timedelta(days=730)
            log(f"Setting date range: {start_date} to {end_date}")
            # Use lock to ensure thread-safe yfinance download
            with _yfinance_lock:
                data = yf.download(
                    ticker, start=start_date, end=end_date, interval=interval
                )
        elif config.get("USE_YEARS", False) and config.get("YEARS", False):
            # Convert years to days for timedelta
            days = config["YEARS"] * 365
            start_date = end_date - timedelta(days=days)
            log(f"Setting date range: {start_date} to {end_date}")
            # Use lock to ensure thread-safe yfinance download
            with _yfinance_lock:
                data = yf.download(
                    ticker, start=start_date, end=end_date, interval=interval
                )
        else:
            period = config.get("PERIOD", "max")
            log("Using maximum available period for data download")
            # Use lock to ensure thread-safe yfinance download
            with _yfinance_lock:
                data = yf.download(
                    ticker, period=period, interval=interval, auto_adjust=False
                )

        # Flatten MultiIndex columns - do this for all data retrieval methods
        data.columns = [
            f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col
            for col in data.columns
        ]

        log(f"Successfully downloaded {len(data)} records")

        if len(data) == 0:
            error_msg = f"No data downloaded for {ticker}"
            log(error_msg, "error")
            raise ValueError(error_msg)

        # Reset index to make the datetime index a column
        data = data.reset_index()

        # Helper function to get column data with fallback
        def get_column_data(col_name: str):
            # Try ticker-specific column first (from MultiIndex flattening)
            ticker_col = f"{col_name}_{ticker}"
            if ticker_col in data.columns:
                return data[ticker_col]
            # Fallback to simple column name
            elif col_name in data.columns:
                return data[col_name]
            else:
                available_cols = list(data.columns)
                raise KeyError(
                    f"Column '{col_name}' not found for {ticker}. Available columns: {available_cols}"
                )

        # Convert to Polars DataFrame with explicit schema
        df = pl.DataFrame(
            {
                "Date": pl.Series(data["Datetime"] if use_hourly else data["Date"]),
                "Open": pl.Series(get_column_data("Open"), dtype=pl.Float64),
                "High": pl.Series(get_column_data("High"), dtype=pl.Float64),
                "Low": pl.Series(get_column_data("Low"), dtype=pl.Float64),
                "Close": pl.Series(get_column_data("Close"), dtype=pl.Float64),
                "Volume": pl.Series(get_column_data("Volume"), dtype=pl.Float64),
            }
        )

        # Log data statistics
        log(f"Data summary for {ticker}:")
        log(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        log(f"Price range: ${df['Close'].min():.2f} to ${df['Close'].max():.2f}")
        log(f"Average volume: {df['Volume'].mean():.0f}")
        log(f"Data frequency: {'Hourly' if use_hourly else 'Daily'}")

        # Export to CSV
        export_config: ExportConfig = {
            "BASE_DIR": config.get("BASE_DIR", "."),
            "TICKER": ticker,
            "USE_HOURLY": use_hourly,
            "USE_MA": False,  # Don't include MA suffix for raw price data
        }

        log("Exporting data to CSV")
        df, export_path = export_csv(
            data=df, feature1="price_data", config=export_config
        )
        log(f"Data exported successfully to {export_path}")

        return df

    except Exception as e:
        log(f"Error in download_data for {ticker}: {str(e)}", "error")
        raise
