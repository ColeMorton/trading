from typing import Tuple, List
import yfinance as yf
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor, as_completed

# Constants for easy configuration
USE_HOURLY: bool = False  # Set to False for daily data
USE_SYNTHETIC: bool = False  # Toggle between synthetic and original ticker
TICKER_1: str = 'BTC-USD'  # Ticker for X to USD
TICKER_2: str = 'BTC-USD'  # Ticker for Y to USD

USE_EMA: bool = False
EMA_FAST: int = 9  # Fast EMA period
EMA_SLOW: int = 31  # Slow EMA period

interval: str = '1h' if USE_HOURLY else '1d'

@lru_cache(maxsize=None)
def download_data(ticker: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

def calculate_ema(data: pd.DataFrame, short_window: int, long_window: int) -> None:
    """Calculate short-term and long-term EMAs."""
    data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()

def calculate_atr(data: pd.DataFrame, length: int) -> pd.Series:
    """Calculate Average True Range (ATR)."""
    high_low: pd.Series = data['High'] - data['Low']
    high_close: pd.Series = np.abs(data['High'] - data['Close'].shift())
    low_close: pd.Series = np.abs(data['Low'] - data['Close'].shift())
    ranges: pd.DataFrame = pd.concat([high_low, high_close, low_close], axis=1)
    true_range: pd.Series = np.max(ranges, axis=1)
    return true_range.rolling(window=length).mean()

def calculate_atr_trailing_stop(close: float, atr: float, multiplier: float, highest_since_entry: float, previous_stop: float) -> float:
    """Calculate ATR Trailing Stop."""
    potential_stop: float = close - (atr * multiplier)
    if np.isnan(previous_stop):
        return potential_stop
    new_stop: float = highest_since_entry - (atr * multiplier)
    return max(new_stop, previous_stop)

def generate_signals(data: pd.DataFrame, short_window: int, long_window: int, atr_length: int, atr_multiplier: float) -> pd.DataFrame:
    """Generate trading signals based on EMA cross and ATR Trailing Stop."""
    calculate_ema(data, short_window, long_window)
    data['ATR'] = calculate_atr(data, atr_length)
    data['Signal'] = 0
    data['ATR_Trailing_Stop'] = np.nan
    data['Highest_Since_Entry'] = np.nan

    in_position: bool = False
    entry_price: float = 0

    for i in range(1, len(data)):
        current_close: float = data['Close'].iloc[i]
        current_atr: float = data['ATR'].iloc[i]
        
        # Check for entry condition
        ema_cross: bool = data['EMA_short'].iloc[i] > data['EMA_long'].iloc[i] and data['EMA_short'].iloc[i-1] <= data['EMA_long'].iloc[i-1]
        potential_stop: float = calculate_atr_trailing_stop(current_close, current_atr, atr_multiplier, current_close, np.nan)
        price_above_stop: bool = current_close >= potential_stop
        
        # if ema_cross and price_above_stop and not in_position:
        if price_above_stop and not in_position:
            if USE_EMA and ema_cross or USE_EMA == False:
                data.loc[data.index[i], 'Signal'] = 1
                data.loc[data.index[i], 'ATR_Trailing_Stop'] = potential_stop
                data.loc[data.index[i], 'Highest_Since_Entry'] = current_close
                in_position = True
                entry_price = current_close
        elif in_position:
            # Update highest price since entry
            highest_since_entry: float = max(data['Highest_Since_Entry'].iloc[i-1], current_close)
            data.loc[data.index[i], 'Highest_Since_Entry'] = highest_since_entry
            
            # Calculate new trailing stop
            new_stop: float = calculate_atr_trailing_stop(
                current_close,
                current_atr,
                atr_multiplier,
                highest_since_entry,
                data['ATR_Trailing_Stop'].iloc[i-1]
            )
            data.loc[data.index[i], 'ATR_Trailing_Stop'] = new_stop

            if current_close < new_stop:
                data.loc[data.index[i], 'Signal'] = 0
                in_position = False
            else:
                data.loc[data.index[i], 'Signal'] = 1

    data['Position'] = data['Signal'].shift()
    return data

def backtest_strategy(data: pd.DataFrame) -> vbt.Portfolio:
    """Backtest the EMA cross strategy with ATR Trailing Stop."""
    portfolio: vbt.Portfolio = vbt.Portfolio.from_signals(
        close=data['Close'],
        entries=(data['Signal'] == 1) & (data['Signal'].shift() != 1),
        exits=(data['Signal'] == 0) & (data['Signal'].shift() == 1),
        init_cash=1000,
        fees=0.001
    )
    return portfolio

def analyze_params(data: pd.DataFrame, ema_fast: int, ema_slow: int, atr_length: int, atr_multiplier: float) -> Tuple[int, float, float]:
    data_with_signals: pd.DataFrame = generate_signals(data.copy(), ema_fast, ema_slow, atr_length, atr_multiplier)
    portfolio: vbt.Portfolio = backtest_strategy(data_with_signals)
    return atr_length, atr_multiplier, portfolio.total_return()

def parameter_sensitivity_analysis(data: pd.DataFrame, atr_lengths: List[int], atr_multipliers: List[float]) -> pd.DataFrame:
    results: pd.DataFrame = pd.DataFrame(index=atr_lengths, columns=atr_multipliers)
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(analyze_params, data, EMA_FAST, EMA_SLOW, length, multiplier) 
                   for length in atr_lengths for multiplier in atr_multipliers]
        for future in as_completed(futures):
            length, multiplier, total_return = future.result()
            results.loc[length, multiplier] = total_return
    return results

def plot_heatmap(results: pd.DataFrame, ticker: str) -> None:
    """Plot heatmap of the results."""
    plt.figure(figsize=(12, 8))
    sns.heatmap(results.astype(float), annot=True, cmap="YlGnBu", fmt='.3f', cbar_kws={'label': 'Total Return'})
    timeframe: str = "Hourly" if USE_HOURLY else "Daily"
    plt.title(f'Parameter Sensitivity Analysis - ATR Trailing Stop ({timeframe}) for {ticker}')
    plt.xlabel('ATR Multiplier')
    plt.ylabel('ATR Length')
    plt.tight_layout()
    plt.show()

def main() -> None:
    end_date: datetime = datetime.now()
    years: int = 2 if USE_HOURLY else 10
    start_date: datetime = end_date - timedelta(days=365 * years)

    atr_lengths: List[int] = list(range(2, 15))
    atr_multipliers: List[float] = list(np.arange(2.5, 12.5, 0.5))

    if USE_SYNTHETIC:
        data_ticker_1: pd.DataFrame = download_data(TICKER_1, start_date, end_date)
        data_ticker_2: pd.DataFrame = download_data(TICKER_2, start_date, end_date)
        
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        data: pd.DataFrame = pd.DataFrame(index=data_ticker_1.index)
        data['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        data['Open'] = data_ticker_1['Open'] / data_ticker_2['Open']
        data['High'] = data_ticker_1['High'] / data_ticker_2['High']
        data['Low'] = data_ticker_1['Low'] / data_ticker_2['Low']
        data['Volume'] = (data_ticker_1['Volume'] + data_ticker_2['Volume']) / 2
        data = data.dropna()
        
        base_currency: str = TICKER_1[:3]
        quote_currency: str = TICKER_2[:3]
        synthetic_ticker: str = f"{base_currency}/{quote_currency}"
    else:
        data: pd.DataFrame = download_data(TICKER_1, start_date, end_date)
        synthetic_ticker: str = TICKER_1

    results: pd.DataFrame = parameter_sensitivity_analysis(data, atr_lengths, atr_multipliers)
    
    best_params: Tuple[int, float] = results.stack().idxmax()
    best_return: float = results.stack().max()
    print(f"Best parameters for {interval} {synthetic_ticker}: ATR Length: {best_params[0]}, ATR Multiplier: {best_params[1]}")
    print(f"Best total return: {best_return:.3f}")
    
    plot_heatmap(results, synthetic_ticker)

if __name__ == "__main__":
    main()