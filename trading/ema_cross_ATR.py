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
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'DVA'  # Ticker for X to USD
TICKER_2 = 'QQQ'  # Ticker for Y to USD
EMA_FAST = 10  # Fast EMA period
EMA_SLOW = 17  # Slow EMA period

interval = '1h' if USE_HOURLY_DATA else '1d'

@lru_cache(maxsize=None)
def download_data(ticker, start_date, end_date):
    """Download historical data from Yahoo Finance."""
    return yf.download(ticker, start=start_date, end=end_date, interval=interval)

def calculate_ema(data, short_window, long_window):
    """Calculate short-term and long-term EMAs."""
    data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
    data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()

def calculate_atr(data, length):
    """Calculate Average True Range (ATR)."""
    high_low = data['High'] - data['Low']
    high_close = np.abs(data['High'] - data['Close'].shift())
    low_close = np.abs(data['Low'] - data['Close'].shift())
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    return true_range.rolling(window=length).mean()

def generate_signals(data, short_window, long_window, atr_length, atr_multiplier):
    """Generate trading signals based on EMA cross and ATR Stop."""
    calculate_ema(data, short_window, long_window)
    data['ATR'] = calculate_atr(data, atr_length)
    data['Signal'] = 0
    data['ATR_Stop'] = np.nan

    for i in range(1, len(data)):
        if data['EMA_short'].iloc[i] > data['EMA_long'].iloc[i] and data['EMA_short'].iloc[i-1] <= data['EMA_long'].iloc[i-1]:
            data.loc[data.index[i], 'Signal'] = 1
            data.loc[data.index[i], 'ATR_Stop'] = data['Close'].iloc[i] - (data['ATR'].iloc[i] * atr_multiplier)
        elif data['Signal'].iloc[i-1] == 1:
            if data['Close'].iloc[i] < data['ATR_Stop'].iloc[i-1]:
                data.loc[data.index[i], 'Signal'] = 0
            else:
                data.loc[data.index[i], 'Signal'] = 1
                data.loc[data.index[i], 'ATR_Stop'] = max(data['ATR_Stop'].iloc[i-1], data['Close'].iloc[i] - (data['ATR'].iloc[i] * atr_multiplier))
    
    data['Position'] = data['Signal'].shift()
    return data

def backtest_strategy(data):
    """Backtest the EMA cross strategy with ATR Stop."""
    portfolio = vbt.Portfolio.from_signals(
        close=data['Close'],
        entries=(data['Signal'] == 1) & (data['Signal'].shift() != 1),
        exits=(data['Signal'] == 0) & (data['Signal'].shift() == 1),
        init_cash=1000,
        fees=0.001
    )
    return portfolio

def analyze_params(data, ema_fast, ema_slow, atr_length, atr_multiplier):
    data_with_signals = generate_signals(data.copy(), ema_fast, ema_slow, atr_length, atr_multiplier)
    portfolio = backtest_strategy(data_with_signals)
    return atr_length, atr_multiplier, portfolio.total_return()

def parameter_sensitivity_analysis(data, atr_lengths, atr_multipliers):
    results = pd.DataFrame(index=atr_lengths, columns=atr_multipliers)
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(analyze_params, data, EMA_FAST, EMA_SLOW, length, multiplier) 
                   for length in atr_lengths for multiplier in atr_multipliers]
        for future in as_completed(futures):
            length, multiplier, total_return = future.result()
            results.loc[length, multiplier] = total_return
    return results

def plot_heatmap(results, ticker):
    """Plot heatmap of the results."""
    plt.figure(figsize=(12, 8))
    sns.heatmap(results.astype(float), annot=True, cmap="YlGnBu", fmt='.3f', cbar_kws={'label': 'Total Return'})
    timeframe = "Hourly" if USE_HOURLY_DATA else "Daily"
    plt.title(f'Parameter Sensitivity Analysis - ATR Stop ({timeframe}) for {ticker}')
    plt.xlabel('ATR Multiplier')
    plt.ylabel('ATR Length')
    plt.tight_layout()
    plt.show()

def main():
    end_date = datetime.now()
    years = 1 if USE_HOURLY_DATA else 10
    start_date = end_date - timedelta(days=365 * years)

    atr_lengths = range(2, 13)
    atr_multipliers = np.arange(1, 8.5, 0.5)

    if USE_SYNTHETIC:
        data_ticker_1 = download_data(TICKER_1, start_date, end_date)
        data_ticker_2 = download_data(TICKER_2, start_date, end_date)
        
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        data = pd.DataFrame(index=data_ticker_1.index)
        data['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        data['Open'] = data_ticker_1['Open'] / data_ticker_2['Open']
        data['High'] = data_ticker_1['High'] / data_ticker_2['High']
        data['Low'] = data_ticker_1['Low'] / data_ticker_2['Low']
        data = data.dropna()
        
        base_currency = TICKER_1[:3]
        quote_currency = TICKER_2[:3]
        synthetic_ticker = f"{base_currency}/{quote_currency}"
    else:
        data = download_data(TICKER_1, start_date, end_date)
        synthetic_ticker = TICKER_1

    results = parameter_sensitivity_analysis(data, atr_lengths, atr_multipliers)
    
    best_params = results.stack().idxmax()
    best_return = results.stack().max()
    print(f"Best parameters for {interval} {synthetic_ticker}: ATR Length: {best_params[0]}, ATR Multiplier: {best_params[1]}")
    print(f"Best total return: {best_return:.3f}")
    
    plot_heatmap(results, synthetic_ticker)

if __name__ == "__main__":
    main()
