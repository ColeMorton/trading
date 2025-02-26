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
        
        # For current signals, check if yesterday was a trading holiday
        if config.get("USE_CURRENT", False):
            # Download data including yesterday and day before
            temp_start = end_date - timedelta(days=3)  # Get 3 days to ensure we have enough data
            temp_data = yf.download(ticker, start=temp_start, end=end_date, interval=interval)
            
            if len(temp_data) > 0:
                # Get the last trading day's date
                last_trading_day = temp_data.index[-1].date()
                today = end_date.date()
                
                # If last trading day was before yesterday, adjust end_date
                if (today - last_trading_day).days > 1:
                    log(f"Detected trading holiday. Using data from {last_trading_day}")
                    # Set end_date to the day after last trading day to ensure we get that day's data
                    end_date = datetime.combine(last_trading_day + timedelta(days=1), datetime.min.time())
        
        if use_hourly:
            start_date = end_date - timedelta(days=730)
            log(f"Setting date range: {start_date} to {end_date}")
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        elif config.get('USE_YEARS', False) and config.get("YEARS", False):
            # Convert years to days for timedelta
            days = config["YEARS"] * 365
            start_date = end_date - timedelta(days=days)
            log(f"Setting date range: {start_date} to {end_date}")
            data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        else:
            period = config.get("PERIOD", "max")
            log(f"Using maximum available period for data download")
            data = yf.download(ticker, period=period, interval=interval)
        
        # Flatten MultiIndex columns - do this for all data retrieval methods
        data.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in data.columns]

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
            'Open': pl.Series(data[f'Open_{ticker}'], dtype=pl.Float64),
            'High': pl.Series(data[f'High_{ticker}'], dtype=pl.Float64),
            'Low': pl.Series(data[f'Low_{ticker}'], dtype=pl.Float64),
            'Close': pl.Series(data[f'Close_{ticker}'], dtype=pl.Float64),
            'Volume': pl.Series(data[f'Volume_{ticker}'], dtype=pl.Float64)
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
