from typing import Callable
import polars as pl
import yfinance as yf
from datetime import datetime, timedelta
from app.tools.export_csv import export_csv, ExportConfig
from app.tools.data_types import DataConfig

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

        use_hourly = config.get('USE_HOURLY', False)
        interval = '1h' if use_hourly else '1d'
        log(f"Using {interval} interval for data download")

        # Calculate date range
        end_date = datetime.now()
        if use_hourly or config.get('USE_YEARS', False):
            days = (730 if use_hourly else 365 * config.get("YEARS", 30))
            start_date = end_date - timedelta(days=days)
            log(f"Setting date range: {start_date} to {end_date}")
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        else:
            period = config.get("PERIOD", "max")
            log(f"Using maximum available period for data download")
            data = yf.download(ticker, period=period, interval=interval)

        log(f"Successfully downloaded {len(data)} records")

        if len(data) == 0:
            error_msg = f"No data downloaded for {ticker}"
            log(error_msg, "error")
            raise ValueError(error_msg)

        # Reset index to make the datetime index a column
        data = data.reset_index()

        # Convert to Polars DataFrame with explicit schema
        df = pl.DataFrame({
            'Date': pl.Series(data['Datetime'] if use_hourly else data['Date']),
            'Open': pl.Series(data['Open'], dtype=pl.Float64),
            'High': pl.Series(data['High'], dtype=pl.Float64),
            'Low': pl.Series(data['Low'], dtype=pl.Float64),
            'Close': pl.Series(data['Close'], dtype=pl.Float64),
            'Adj Close': pl.Series(data['Adj Close'], dtype=pl.Float64),
            'Volume': pl.Series(data['Volume'], dtype=pl.Float64)
        })

        # Log data statistics
        log(f"Data summary for {ticker}:")
        log(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        log(f"Price range: ${df['Close'].min():.2f} to ${df['Close'].max():.2f}")
        log(f"Average volume: {df['Volume'].mean():.0f}")
        log(f"Data frequency: {'Hourly' if use_hourly else 'Daily'}")

        # Export to CSV
        export_config: ExportConfig = {
            'BASE_DIR': config.get('BASE_DIR', '.'),
            'TICKER': ticker,
            'USE_HOURLY': use_hourly,
            'USE_MA': False  # Don't include MA suffix for raw price data
        }
        
        log("Exporting data to CSV")
        df, export_path = export_csv(
            data=df,
            feature1='price_data',
            config=export_config
        )
        log(f"Data exported successfully to {export_path}")

        return df

    except Exception as e:
        log(f"Error in download_data for {ticker}: {str(e)}", "error")
        raise
