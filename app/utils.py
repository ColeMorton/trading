import polars as pl
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Tuple, List
import pandas as pd
import vectorbt as vbt
import logging
import os
from app.geometric_brownian_motion.get_median import get_median

def download_data(ticker: str, years: int, use_hourly: bool) -> pl.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * years)
    
    data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
    return pl.from_pandas(data.reset_index())

def get_data(config: dict) -> pl.DataFrame:
    if config.get('USE_GBM', False) == True:
        return get_median(config)

    if config['PERIOD'] == 'max' and config['USE_SYNTHETIC'] == False:
        """Download historical data from Yahoo Finance."""
        interval = '1h' if config['USE_HOURLY'] else '1d'

        data = yf.download(config['TICKER_1'], period=config['PERIOD'], interval=interval)
        return pl.from_pandas(data.reset_index())

def use_synthetic(ticker1: str, ticker2: str, use_hourly: bool) -> Tuple[pl.DataFrame, str]:
    """Create a synthetic pair from two tickers."""
    data_ticker_1 = download_data(ticker1, 30, use_hourly)
    data_ticker_2 = download_data(ticker2, 30, use_hourly)
    
    data_merged = data_ticker_1.join(data_ticker_2, on='Date', how='inner', suffix="_2")
    
    data = pl.DataFrame({
        'Date': data_merged['Date'],
        'Close': data_merged['Close'] / data_merged['Close_2'],
        'Open': data_merged['Open'] / data_merged['Open_2'],
        'High': data_merged['High'] / data_merged['High_2'],
        'Low': data_merged['Low'] / data_merged['Low_2'],
        'Volume': data_merged['Volume']  # Keep original volume
    })
    
    base_currency = ticker1[:3]
    quote_currency = ticker2[:3]
    synthetic_ticker = f"{base_currency}/{quote_currency}"
    
    return data, synthetic_ticker

def calculate_mas(data: pl.DataFrame, fast_period: int, slow_period: int, use_sma: bool = False) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA)."""
    if use_sma:
        data = data.with_columns([
            pl.col('Close').rolling_mean(window_size=fast_period).alias('MA_FAST'),
            pl.col('Close').rolling_mean(window_size=slow_period).alias('MA_SLOW')
        ])
    else:
        data = data.with_columns([
            pl.col('Close').ewm_mean(span=fast_period, adjust=False).alias('MA_FAST'),
            pl.col('Close').ewm_mean(span=slow_period, adjust=False).alias('MA_SLOW')
        ])
    return data

def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    """Calculate RSI."""
    print("Data type before calculation:", type(data))
    delta = data['Close'].diff()
    gain = np.maximum(delta, 0)  # Corrected line
    loss = -np.minimum(delta, 0)
    
    avg_gain = gain.rolling_mean(window_size=period)
    avg_loss = loss.rolling_mean(window_size=period)
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    print("RSI type:", type(rsi))
    print("RSI value:", rsi)
    print("Data type before return:", type(data))
    
    return data.with_columns([rsi.alias('RSI')])  # Updated to use with_columns

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

def calculate_ma_and_signals(data: pl.DataFrame, short_window: int, long_window: int, config: dict) -> pl.DataFrame:
    """Calculate MAs and generate trading signals."""
    ma_type = "SMA" if config.get('USE_SMA', False) else "EMA"
    logging.info(f"Calculating {ma_type}s and signals with short window {short_window} and long window {long_window}")
    try:
        data = calculate_mas(data, short_window, long_window, config.get('USE_SMA', False))
        entries, exits = generate_ma_signals(data, config)
        
        data = data.with_columns([
            pl.when(entries).then(1).otherwise(0).alias("Signal")
        ])
        
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        logging.info(f"{ma_type}s and signals calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate {ma_type}s and signals: {e}")
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
        csv_path = os.path.join(config['BASE_DIR'], f'csv/ma_cross/{config['TICKER_1']}_parameter_portfolios.csv')
        portfolios.write_csv(csv_path)

        print(f"Analysis complete. Portfolios written to {csv_path}")
        print(f"Total rows in output: {len(portfolios)}")

        return portfolios
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise

def getFilename(ticker: str, config: dict) -> str:
    filename = f'images/ema_cross/parameter_sensitivity/{ticker}{"_H" if config.get("USE_HOURLY_DATA", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}{"_" + datetime.now().strftime("%Y%m%d") if config.get("SHOW_LAST", True) else ""}.png'

    return filename

def getPath(type: str, feature1: str, config: dict, feature2: str = "") -> str:
    path = os.path.join(config['BASE_DIR'], f'{type}/{feature1}{"/" + feature2 if feature2 != "" else ""}')

    return path
