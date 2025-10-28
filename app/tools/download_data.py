from collections.abc import Callable
from datetime import datetime, timedelta
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

        use_2day = config.get("USE_2DAY", False)
        use_4hour = config.get("USE_4HOUR", False)
        use_hourly = config.get("USE_HOURLY", False)

        # For 4-hour data, we need to download 1-hour data first and then convert
        # For 2-day data, we use daily data (default) and then convert
        if use_4hour:
            interval = "1h"
            log(f"Using {interval} interval for 4-hour data conversion")
        elif use_hourly:
            interval = "1h"
            log(f"Using {interval} interval for data download")
        else:
            interval = "1d"
            if use_2day:
                log(f"Using {interval} interval for 2-day data conversion")
            else:
                log(f"Using {interval} interval for data download")

        # Calculate date range with market-aware adjustments
        end_date = datetime.now()

        if use_4hour or use_hourly:
            # Detect market type for date range optimization
            from app.tools.market_hours import MarketType, detect_market_type

            market_type = detect_market_type(ticker)

            # Adjust date range based on market type
            if market_type == MarketType.US_STOCK:
                # For stocks, account for weekends and holidays - need more data
                days_to_fetch = 730 + 150  # Extra buffer for non-trading days
                log(
                    f"Stock market detected - using {days_to_fetch} day range to account for non-trading days"
                )
            else:
                # Crypto trades 24/7, standard range is sufficient
                days_to_fetch = 730
                log(
                    f"Crypto market detected - using {days_to_fetch} day range for 24/7 trading"
                )

            start_date = end_date - timedelta(days=days_to_fetch)
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
            if col_name in data.columns:
                return data[col_name]
            available_cols = list(data.columns)
            raise KeyError(
                f"Column '{col_name}' not found for {ticker}. Available columns: {available_cols}"
            )

        # Convert to Polars DataFrame with explicit schema
        df = pl.DataFrame(
            {
                "Date": pl.Series(
                    data["Datetime"] if (use_hourly or use_4hour) else data["Date"]
                ),
                "Open": pl.Series(get_column_data("Open"), dtype=pl.Float64),
                "High": pl.Series(get_column_data("High"), dtype=pl.Float64),
                "Low": pl.Series(get_column_data("Low"), dtype=pl.Float64),
                "Close": pl.Series(get_column_data("Close"), dtype=pl.Float64),
                "Volume": pl.Series(get_column_data("Volume"), dtype=pl.Float64),
            }
        )

        # Convert 1-hour data to 4-hour data if requested with market-aware logic
        if use_4hour:
            log("Converting 1-hour data to 4-hour bars with market awareness")
            from app.tools.data_processing import convert_hourly_to_4hour
            from app.tools.market_hours import detect_market_type

            # Detect market type for appropriate conversion
            market_type = detect_market_type(ticker)
            log(f"Detected market type: {market_type.value} for ticker {ticker}")

            # Pass ticker for market-aware conversion
            df = convert_hourly_to_4hour(df, ticker=ticker)
            log("Market-aware 4-hour conversion completed")

        # Convert daily data to 2-day data if requested with market-aware logic
        if use_2day:
            log("Converting daily data to 2-day bars with market awareness")
            from app.tools.data_processing import convert_daily_to_2day
            from app.tools.market_hours import detect_market_type

            # Detect market type for appropriate conversion
            market_type = detect_market_type(ticker)
            log(f"Detected market type: {market_type.value} for ticker {ticker}")

            # Pass ticker for market-aware conversion
            df = convert_daily_to_2day(df, ticker=ticker)
            log("Market-aware 2-day conversion completed")

        # Enhanced data summary display using console logger if available
        if hasattr(log, "__self__") and hasattr(log.__self__, "data_summary_table"):
            # Use enhanced console logger display
            data_info = {
                "date_range": f"{df['Date'].min()} to {df['Date'].max()}",
                "price_range": f"${df['Close'].min():.2f} to ${df['Close'].max():.2f}",
                "avg_volume": int(df["Volume"].mean()),
                "frequency": (
                    "2-Day"
                    if use_2day
                    else "4-Hour" if use_4hour else "Hourly" if use_hourly else "Daily"
                ),
                "records_count": len(df),
            }
            log.__self__.data_summary_table(ticker, data_info)
        else:
            # Fallback to basic logging
            log(f"Data summary for {ticker}:")
            log(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
            log(f"Price range: ${df['Close'].min():.2f} to ${df['Close'].max():.2f}")
            log(f"Average volume: {df['Volume'].mean():.0f}")

            # Determine data frequency for logging
            if use_2day:
                frequency = "2-Day"
            elif use_4hour:
                frequency = "4-Hour"
            elif use_hourly:
                frequency = "Hourly"
            else:
                frequency = "Daily"
            log(f"Data frequency: {frequency}")

        # Export to CSV
        export_config: ExportConfig = {
            "BASE_DIR": config.get("BASE_DIR", "."),
            "TICKER": ticker,
            "USE_2DAY": use_2day,  # Add 2-day flag for export config
            "USE_HOURLY": use_hourly,
            "USE_4HOUR": use_4hour,  # Add 4-hour flag for export config
            "USE_MA": False,  # Don't include MA suffix for raw price data
        }

        log("Exporting data to CSV")
        df, export_path = export_csv(data=df, feature1="prices", config=export_config)
        log(f"Data exported successfully to {export_path}")

        return df

    except Exception as e:
        log(f"Error in download_data for {ticker}: {e!s}", "error")
        raise
