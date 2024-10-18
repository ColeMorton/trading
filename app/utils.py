import yfinance as yf
import polars as pl
from datetime import datetime, timedelta
import json
import random
import vectorbt as vbt
import polars as pl
import numpy as np
from typing import Tuple

def download_data(ticker: str, use_hourly: bool = False, years: int = 30) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * years)
    
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        data.reset_index(inplace=True)  # Reset index to make 'Date' a column
        return pl.DataFrame(data)
    except Exception as e:
        raise

def calculate_mas(data: pl.DataFrame, short_window: int, long_window: int, use_sma: bool = False) -> pl.DataFrame:
    try:
        if use_sma:
            return data.with_columns([
                pl.col('Close').rolling_mean(window_size=short_window).fill_null(strategy='forward').alias('MA_FAST'),
                pl.col('Close').rolling_mean(window_size=long_window).fill_null(strategy='forward').alias('MA_SLOW')
            ])
        else:
            return data.with_columns([
                pl.col('Close').ewm_mean(span=short_window).fill_null(strategy='forward').alias('MA_FAST'),
                pl.col('Close').ewm_mean(span=long_window).fill_null(strategy='forward').alias('MA_SLOW')
            ])
    except Exception as e:
        raise

def generate_ma_signals(data: pl.DataFrame, config: dict) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate entry and exit signals based on the strategy configuration.

    Args:
        data (pl.DataFrame): The input DataFrame containing price and indicator data.
        config (dict): The configuration dictionary.

    Returns:
        Tuple[np.ndarray, np.ndarray]: A tuple containing entry and exit signals as NumPy arrays.
    """
    if config["SHORT"]:
        entries = (data['MA_FAST'] < data['MA_SLOW'])
        if config["USE_RSI"]:
            entries = entries & (data['RSI'] <= (100 - config["RSI_THRESHOLD"]))
        exits_ema = data['MA_FAST'] > data['MA_SLOW']
    else:
        entries = (data['MA_FAST'] > data['MA_SLOW'])
        if config["USE_RSI"]:
            entries = entries & (data['RSI'] >= config["RSI_THRESHOLD"])
        exits_ema = data['MA_FAST'] < data['MA_SLOW']

    return entries, exits_ema

def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    """
    Calculate the Relative Strength Index (RSI) for the given data.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data.
        period (int): The period over which to calculate the RSI.

    Returns:
        pl.DataFrame: The input DataFrame with an additional 'RSI' column.

    Raises:
        Exception: If there's an error calculating the RSI.
    """
    try:
        delta = data['Close'].diff()
        gain = (delta.fill_null(0) > 0) * delta.fill_null(0)
        loss = (delta.fill_null(0) < 0) * -delta.fill_null(0)
        avg_gain = gain.rolling_mean(window_size=period)
        avg_loss = loss.rolling_mean(window_size=period)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return data.with_columns([rsi.alias('RSI')])
    except Exception as e:
        raise Exception(f"Error calculating RSI: {str(e)}")
    
def use_synthetic(ticker_1: str, ticker_2: str, use_hourly: bool = False, years: int = 30):
    # Download historical data for TICKER_1 and TICKER_2
    data_ticker_1 = download_data(ticker_1, use_hourly, years)
    data_ticker_2 = download_data(ticker_2, use_hourly, years)

    # Perform an inner join on 'Date' to ensure both have matching rows
    data_merged = data_ticker_1.join(data_ticker_2, on='Date', how='inner', suffix="_2")

    # Now calculate the ratio of 'Close' columns
    data = pl.DataFrame({
        'Date': data_merged['Date'],
        'Close': data_merged['Close'] / data_merged['Close_2'],
        'Open': data_merged['Open'] / data_merged['Open_2'],
        'High': data_merged['High'] / data_merged['High_2'],
        'Low': data_merged['Low'] / data_merged['Low_2'],
        'Volume': data_merged['Volume']  # Keep original volume
    })
    
    # Extracting base and quote currencies from tickers
    base_currency = ticker_1[:3]  # X
    quote_currency = ticker_2[:3]  # Y
    synthetic_ticker = f"{base_currency}/{quote_currency}"
    return data, synthetic_ticker

def load_monte_carlo_median_data(ticker: str) -> pl.DataFrame:
    """Load Monte Carlo data from CSV file."""
    try:
        data = pl.read_csv(f"csv/{ticker}_monte_carlo_median.csv")
        data = data.with_columns([
            pl.col("Date").str.to_datetime("%Y-%m-%d"),
            pl.col("Open").cast(pl.Float64),
            pl.col("High").cast(pl.Float64),
            pl.col("Low").cast(pl.Float64),
            pl.col("Close").cast(pl.Float64),
            pl.col("Adj Close").cast(pl.Float64),
            pl.col("Volume").cast(pl.Int64)
        ])
        return data
    except Exception as e:
        raise

def get_random_simulation(ticker_1: str):
    """
    Import the JSON file, select a random simulation, and return it as a DataFrame.
    
    Returns:
        pl.DataFrame: A randomly selected simulation in the specified format.
    """
    try:
        with open(f'json/{ticker_1}_monte_carlo_simulations.json', 'r') as file:
            data = json.load(file)
        
        simulations = data['simulations']
        random_simulation = random.choice(simulations)
        
        # Generate dates starting from tomorrow
        start_date = datetime.now().date() + timedelta(days=1)
        dates = [start_date + timedelta(days=i) for i in range(len(random_simulation))]
        
        # Create DataFrame
        simulation = pl.DataFrame({
            'Date': dates,
            'Open': random_simulation,
            'High': random_simulation,
            'Low': random_simulation,
            'Close': random_simulation,
            'Adj Close': random_simulation,
            'Volume': [0] * len(random_simulation)
        })
        
        return simulation
    except Exception as e:
        raise Exception(f"Error getting random simulation: {str(e)}")

def run_backtest(data: pl.DataFrame, entries: np.ndarray, exits: np.ndarray, config: dict) -> vbt.Portfolio:
    """
    Run a backtest using the generated signals.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data.
        entries (np.ndarray): Array of entry signals.
        exits (np.ndarray): Array of exit signals.
        config (dict): The configuration dictionary.

    Returns:
        vbt.Portfolio: A vectorbt Portfolio object containing the backtest results.
    """
    if config["SHORT"]:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), short_entries=entries, short_exits=exits)
    else:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), entries, exits)
