from typing import Tuple
import polars as pl
import yfinance as yf
import logging
from typing import TypedDict, NotRequired
from datetime import datetime, timedelta
from app.geometric_brownian_motion.get_median import get_median

class Config(TypedDict):
    TICKER: str
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

def download_data(ticker: str, config: Config = {}) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    logging.info(f"\nDownloading data for {ticker}")

    use_hourly = config.get('USE_HOURLY', False)
    interval = '1h' if use_hourly else '1d'
    logging.info(f"Using interval: {interval}")

    # Calculate date range
    end_date = datetime.now()
    if use_hourly or config.get('USE_YEARS', False):
        days = (730 if use_hourly else 365 * config.get("YEARS", 30))
        start_date = end_date - timedelta(days=days)
        logging.info(f"Using date range: {start_date} to {end_date}")
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    else:
        period = config.get("PERIOD", "max")
        logging.info(f"Using period: {period}")
        data = yf.download(ticker, period=period, interval=interval)

    logging.info(f"Downloaded {len(data)} records")

    if len(data) == 0:
        raise ValueError(f"No data downloaded for {ticker}")

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
    logging.info(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
    logging.info(f"Price range: {df['Close'].min():.2f} to {df['Close'].max():.2f}")
    logging.info(f"Data frequency: {'Hourly' if use_hourly else 'Daily'}")

    return df


def use_synthetic(ticker1: str, ticker2: str, config: Config) -> pl.DataFrame:
    """Create a synthetic pair from two tickers."""
    data_ticker_1 = download_data(ticker1, config)
    data_ticker_2 = download_data(ticker2, config)

    data_merged = data_ticker_1.join(data_ticker_2, on='Date', how='inner', suffix="_2")

    data = pl.DataFrame({
        'Date': data_merged['Date'],
        'Close': (data_merged['Close'] / data_merged['Close_2']).cast(pl.Float64),
        'Open': (data_merged['Open'] / data_merged['Open_2']).cast(pl.Float64),
        'High': (data_merged['High'] / data_merged['High_2']).cast(pl.Float64),
        'Low': (data_merged['Low'] / data_merged['Low_2']).cast(pl.Float64),
        'Volume': data_merged['Volume'].cast(pl.Float64)  # Keep original volume
    })

    return data


def get_data(ticker: str, config: Config) -> pl.DataFrame:
    if config.get('USE_GBM', False):
        data = get_median(config)

    if config.get('USE_SYNTHETIC', False):
        data = use_synthetic(config['TICKER_1'], config['TICKER_2'], config)
    else:
        data = download_data(ticker, config)

    return data
