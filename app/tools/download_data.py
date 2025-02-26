from typing import Callable, Dict, Any
import polars as pl
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from app.tools.export_csv import export_csv, ExportConfig
from app.tools.data_types import DataConfig

def fetch_latest_data_point(ticker: str, config: DataConfig, log: Callable) -> Dict[str, Any]:
    """
    Fetch the latest data point for a ticker to check if market is open.
    
    Args:
        ticker: Stock ticker symbol
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Dict[str, Any]: Latest data point with timestamp
    """
    try:
        log(f"Fetching latest data point for {ticker}")
        
        # Use 1m interval for most recent data
        interval = '1m'
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)  # Get last day's data
        
        # Download latest data
        latest_data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        
        if len(latest_data) == 0:
            log(f"No recent data available for {ticker}, trying 1h interval")
            # Try hourly data if minute data is not available
            latest_data = yf.download(ticker, start=start_date, end=end_date, interval='1h')
            
            if len(latest_data) == 0:
                log(f"No hourly data available for {ticker}, trying daily interval")
                # Try daily data if hourly data is not available
                latest_data = yf.download(ticker, start=start_date - timedelta(days=5), end=end_date, interval='1d')
        
        if len(latest_data) == 0:
            log(f"No data available for {ticker} in the last 6 days", "warning")
            return {'timestamp': None, 'price': None, 'available': False}
        
        # Get the latest timestamp and price
        latest_timestamp = latest_data.index[-1]
        latest_price = latest_data['Close'].iloc[-1]
        
        log(f"Latest data for {ticker}: {latest_timestamp}, Price: {latest_price}")
        
        return {
            'timestamp': latest_timestamp,
            'price': latest_price,
            'available': True
        }
        
    except Exception as e:
        log(f"Error fetching latest data point for {ticker}: {str(e)}", "error")
        return {'timestamp': None, 'price': None, 'available': False}

def download_complete_dataset(ticker: str, config: DataConfig, log: Callable) -> pl.DataFrame:
    """
    Download the complete historical dataset for a ticker.
    
    Args:
        ticker: Stock ticker symbol
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        pl.DataFrame: Complete historical dataset
    """
    try:
        log(f"Downloading complete dataset for {ticker}")
        
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
        
        # Determine start date based on configuration
        if use_hourly:
            start_date = end_date - timedelta(days=730)  # 2 years of hourly data
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
            log(f"Using {period} period for data download")
            data = yf.download(ticker, period=period, interval=interval)
        
        # Handle empty data
        if len(data) == 0:
            error_msg = f"No data downloaded for {ticker}"
            log(error_msg, "error")
            raise ValueError(error_msg)
        
        log(f"Successfully downloaded {len(data)} records")
        
        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [f"{col[0]}_{col[1]}" if isinstance(col, tuple) else col for col in data.columns]
        
        # Reset index to make the datetime index a column
        data = data.reset_index()
        
        # Convert to Polars DataFrame with explicit schema
        df = pl.DataFrame({
            'Date': pl.Series(data['Datetime'] if use_hourly else data['Date']),
            'Open': pl.Series(data['Open'] if 'Open' in data.columns else data[f'Open_{ticker}'], dtype=pl.Float64),
            'High': pl.Series(data['High'] if 'High' in data.columns else data[f'High_{ticker}'], dtype=pl.Float64),
            'Low': pl.Series(data['Low'] if 'Low' in data.columns else data[f'Low_{ticker}'], dtype=pl.Float64),
            'Close': pl.Series(data['Close'] if 'Close' in data.columns else data[f'Close_{ticker}'], dtype=pl.Float64),
            'Volume': pl.Series(data['Volume'] if 'Volume' in data.columns else data[f'Volume_{ticker}'], dtype=pl.Float64)
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
        log(f"Error in download_complete_dataset for {ticker}: {str(e)}", "error")
        raise

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
    # This function is maintained for backward compatibility
    # It now delegates to download_complete_dataset
    return download_complete_dataset(ticker, config, log)
