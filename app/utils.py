import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Tuple, List
import pandas as pd
import vectorbt as vbt
import logging
import os

def download_data(ticker: str, years: int, use_hourly: bool) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * years)
    
    # Download data using yfinance (returns pandas DataFrame)
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    
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
    
    return df

def get_data(config: dict) -> pl.DataFrame:
    if config.get('USE_SYNTHETIC', False) == False:
        data = download_data(config['TICKER'], config['YEARS'], config['USE_HOURLY'])
    else:
        data, _ = use_synthetic(config['TICKER_1'], config['TICKER_2'], config['USE_HOURLY'])

    return data

def use_synthetic(ticker1: str, ticker2: str, use_hourly: bool) -> Tuple[pl.DataFrame, str]:
    """Create a synthetic pair from two tickers."""
    data_ticker_1 = download_data(ticker1, 30, use_hourly)
    data_ticker_2 = download_data(ticker2, 30, use_hourly)
    
    data_merged = data_ticker_1.join(data_ticker_2, on='Date', how='inner', suffix="_2")
    
    data = pl.DataFrame({
        'Date': data_merged['Date'],
        'Close': (data_merged['Close'] / data_merged['Close_2']).cast(pl.Float64),
        'Open': (data_merged['Open'] / data_merged['Open_2']).cast(pl.Float64),
        'High': (data_merged['High'] / data_merged['High_2']).cast(pl.Float64),
        'Low': (data_merged['Low'] / data_merged['Low_2']).cast(pl.Float64),
        'Volume': data_merged['Volume'].cast(pl.Float64)  # Keep original volume
    })
    
    base_currency = ticker1[:3]
    quote_currency = ticker2[:3]
    synthetic_ticker = f"{base_currency}/{quote_currency}"
    
    return data, synthetic_ticker

def calculate_mas(data: pl.DataFrame, fast_period: int, slow_period: int, use_sma: bool = False) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA)."""
    # Convert to pandas for calculations
    df = data.to_pandas()
    
    # Ensure numeric type for Close column
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    if use_sma:
        df['MA_FAST'] = df['Close'].rolling(window=fast_period).mean()
        df['MA_SLOW'] = df['Close'].rolling(window=slow_period).mean()
    else:
        df['MA_FAST'] = df['Close'].ewm(span=fast_period, adjust=False).mean()
        df['MA_SLOW'] = df['Close'].ewm(span=slow_period, adjust=False).mean()
    
    # Convert back to polars
    return pl.from_pandas(df)

def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    """Calculate RSI."""
    # Convert to pandas for calculations
    df = data.to_pandas()
    
    # Ensure numeric type for Close column
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Convert back to polars
    return pl.from_pandas(df)

def generate_ma_signals(data: pl.DataFrame, config: dict) -> Tuple[pl.Series, pl.Series]:
    """Generate entry and exit signals based on MA crossover."""
    use_rsi = config.get('USE_RSI', False)

    if config['SHORT']:
        entries = (data['MA_FAST'] < data['MA_SLOW'])
        if use_rsi:
            entries = entries & (data['RSI'] <= (100 - config['RSI_THRESHOLD']))
        exits = data['MA_FAST'] > data['MA_SLOW']
    else:
        entries = (data['MA_FAST'] > data['MA_SLOW'])
        if use_rsi:
            entries = entries & (data['RSI'] >= config['RSI_THRESHOLD'])
        exits = data['MA_FAST'] < data['MA_SLOW']
    
    return entries, exits

def calculate_metrics(trades: list, short: bool) -> Tuple[float, float, float]:
    """Calculate performance metrics from a list of trades."""
    if not trades:
        return 0, 0, 0
    
    returns = [(exit_price / entry_price - 1) * (-1 if short else 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(returns)
    
    average_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    average_loss = np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))
    
    return total_return * 100, win_rate * 100, expectancy

def find_prominent_peaks(x: np.ndarray, y: np.ndarray, prominence: float = 1, distance: int = 10) -> np.ndarray:
    """Find prominent peaks in a dataset."""
    from scipy.signal import find_peaks
    peaks, _ = find_peaks(y, prominence=prominence, distance=distance)
    return peaks

def add_peak_labels(ax, x: np.ndarray, y: np.ndarray, peaks: np.ndarray, fmt: str = '.2f'):
    """Add labels to peaks in a plot."""
    for peak in peaks:
        ax.annotate(f'({x[peak]:.2f}, {y[peak]:{fmt}})',
                    (x[peak], y[peak]),
                    xytext=(0, 10),
                    textcoords='offset points',
                    ha='center',
                    va='bottom',
                    bbox=dict(boxstyle='round,pad=0.5', fc='cyan', alpha=0.5),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

# Convert stats to compatible format
def convert_stats(stats):
    converted = {}
    for k, v in stats.items():
        if k == 'Start' or k == 'End':
            converted[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else str(v)
        elif isinstance(v, pd.Timedelta):
            converted[k] = str(v)
        else:
            converted[k] = v
    return converted

def backtest_strategy(data: pl.DataFrame, config: dict) -> vbt.Portfolio:
    """Backtest the MA cross strategy."""
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        if config.get('SHORT', False):
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                short_entries=data_pd['Signal'] == 1,
                short_exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        else:
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                entries=data_pd['Signal'] == 1,
                exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        
        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise

def parameter_sensitivity_analysis(data: pl.DataFrame, short_windows: List[int], long_windows: List[int], config: dict) -> List[pl.DataFrame]:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        portfolios = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(temp_data, short, long, config)
                    portfolio = backtest_strategy(temp_data, config)

                    stats = portfolio.stats()
                    converted_stats = convert_stats(stats)
                    # Add short_window and long_window to the stats
                    converted_stats['short_window'] = short
                    converted_stats['long_window'] = long
                    portfolios.append(converted_stats)

        logging.info("Parameter sensitivity analysis completed successfully")

        portfolios = pl.DataFrame(portfolios)
        
        # Sort portfolios by Total Return [%] in descending order
        portfolios = portfolios.sort("Total Return [%]", descending=True)

        # Export to CSV
        csv_path = os.path.join(config['BASE_DIR'], f'csv/ma_cross/{config["TICKER_1"]}_parameter_portfolios.csv')
        portfolios.write_csv(csv_path)

        print(f"Analysis complete. Portfolios written to {csv_path}")
        print(f"Total rows in output: {len(portfolios)}")

        return portfolios
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise

def get_filename(type: str, config: dict) -> str:
    filename = f'{config["TICKER"]}{"_H" if config.get("USE_HOURLY_DATA", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}{"_GBM" if config.get("USE_GBM", False) else ""}{"_" + datetime.now().strftime("%Y%m%d") if config.get("SHOW_LAST", False) else ""}.{type}'

    return filename

def get_path(type: str, feature1: str, config: dict, feature2: str = "") -> str:
    path = os.path.join(config['BASE_DIR'], f'{type}/{feature1}{"/" + feature2 if feature2 != "" else ""}')

    return path

def save_csv(data: pl.DataFrame, feature1: str, config: dict, feature2: str = "") -> None:
    csv_path = get_path("csv", feature1, config, feature2)
    csv_filename = get_filename("csv", config)
    data.write_csv(csv_path + "/" + csv_filename)

    print(f"{len(data)} rows exported to {csv_path}.csv")
