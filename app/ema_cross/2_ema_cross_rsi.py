import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
import json
import logging
import os
from app.utils import download_data, calculate_mas, calculate_rsi, use_synthetic, find_prominent_peaks, add_peak_labels

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up logging to overwrite the file each time
logging.basicConfig(
    filename='logs/ema_rsi.log',
    filemode='w',  # 'w' mode overwrites the file
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("RSI Threshold Sensitivity Analysis - New Execution")

with open('config.json') as f:
    config = json.load(f)

# Configuration
YEARS = 30  # Set timeframe in years for daily data
USE_HOURLY_DATA = False  # Set to False for daily data
USE_SYNTHETIC = False  # Toggle between synthetic and original ticker
TICKER_1 = 'NXPI'  # Ticker for X to USD exchange rate
TICKER_2 = 'BTC-USD'  # Ticker for Y to USD exchange rate
SHORT = False  # Set to True for short-only strategy, False for long-only strategy
USE_SMA = False  # Set to True to use SMAs, False to use EMAs

EMA_FAST = 2
EMA_SLOW = 54
RSI_PERIOD = 14

def backtest(data: pl.DataFrame, rsi_threshold: float) -> List[Tuple[float, float]]:
    logging.info(f"Running backtest with RSI threshold: {rsi_threshold}")
    position, entry_price = 0, 0
    trades = []
    for i in range(1, len(data)):
        ema_fast_prev, ema_slow_prev = data['MA_FAST'][i-1], data['MA_SLOW'][i-1]
        ema_fast_curr, ema_slow_curr = data['MA_FAST'][i], data['MA_SLOW'][i]
        rsi_curr = data['RSI'][i]
        
        # Skip this iteration if any of the required values are None
        if any(v is None for v in [ema_fast_prev, ema_slow_prev, ema_fast_curr, ema_slow_curr, rsi_curr]):
            continue
        
        if position == 0:
            if (ema_fast_curr > ema_slow_curr and
                ema_fast_prev <= ema_slow_prev and
                rsi_curr >= rsi_threshold):
                position, entry_price = 1, data['Close'][i]
                logging.info(f"Entered long position at price: {entry_price}, RSI: {rsi_curr}")
        elif position == 1:
            if (ema_fast_curr < ema_slow_curr and
                ema_fast_prev >= ema_slow_prev):
                position, exit_price = 0, data['Close'][i]
                trades.append((entry_price, exit_price))
                logging.info(f"Exited long position at price: {exit_price}, RSI: {rsi_curr}")
    
    logging.info(f"Total trades: {len(trades)}")
    return trades

def calculate_metrics(trades: List[Tuple[float, float]]) -> Tuple[float, float, float, int]:
    logging.info("Starting metrics calculation")
    if not trades:
        return 0, 0, 0, 0
    returns = [(exit_price / entry_price - 1) for entry_price, exit_price in trades]
    total_return = np.prod([1 + r for r in returns]) - 1
    win_rate = sum(1 for r in returns if r > 0) / len(trades)
    
    average_win = np.mean([r for r in returns if r > 0]) if any(r > 0 for r in returns) else 0
    average_loss = np.mean([r for r in returns if r <= 0]) if any(r <= 0 for r in returns) else 0
    expectancy = (win_rate * average_win) - ((1 - win_rate) * abs(average_loss))
    
    num_positions = len(trades)
    
    logging.info(f"Metrics - Total Return: {total_return * 100}%, Win Rate: {win_rate * 100}%, Expectancy: {expectancy}, Number of Positions: {num_positions}")
    return total_return * 100, win_rate * 100, expectancy, num_positions

def run_sensitivity_analysis(data: pl.DataFrame, rsi_range: np.ndarray) -> pl.DataFrame:
    logging.info("Starting sensitivity analysis")
    results = []
    for rsi_threshold in rsi_range:
        trades = backtest(data, rsi_threshold)
        total_return, win_rate, expectancy, num_positions = calculate_metrics(trades)
        results.append({
            'RSI Threshold': rsi_threshold,
            'Total Return': total_return,
            'Win Rate': win_rate,
            'Expectancy': expectancy,
            'Number of Positions': num_positions
        })
    return pl.DataFrame(results)

def plot_results(ticker: str, results_df: pl.DataFrame):
    logging.info("Plotting results")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)
    
    # Plot returns and win rate
    color1 = 'tab:blue'
    ax1.set_ylabel('Total Return %', color=color1)
    ax1.plot(results_df['RSI Threshold'], results_df['Total Return'], color=color1)
    ax1.tick_params(axis='y', labelcolor=color1)
    
    color2 = 'tab:red'
    ax1_twin = ax1.twinx()
    ax1_twin.set_ylabel('Win Rate %', color=color2)
    ax1_twin.plot(results_df['RSI Threshold'], results_df['Win Rate'], color=color2)
    ax1_twin.tick_params(axis='y', labelcolor=color2)
    
    ax1.set_title(f'Total Return % and Win Rate % vs RSI Threshold: {ticker}')
    
    # Plot expectancy and number of positions
    color3 = 'tab:green'
    ax2.set_xlabel('RSI Threshold')
    ax2.set_ylabel('Expectancy', color=color3)
    ax2.plot(results_df['RSI Threshold'], results_df['Expectancy'], color=color3)
    ax2.tick_params(axis='y', labelcolor=color3)
    
    color4 = 'tab:orange'
    ax2_twin = ax2.twinx()
    ax2_twin.set_ylabel('Number of Positions', color=color4)
    ax2_twin.plot(results_df['RSI Threshold'], results_df['Number of Positions'], color=color4)
    ax2_twin.tick_params(axis='y', labelcolor=color4)
    
    ax2.set_title(f'Expectancy and Number of Positions vs RSI Threshold: {ticker}')
    
    # Add peak labels for all plots
    add_peak_labels(ax1, results_df['RSI Threshold'].to_numpy(), results_df['Total Return'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Total Return'].to_numpy()))
    add_peak_labels(ax1_twin, results_df['RSI Threshold'].to_numpy(), results_df['Win Rate'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Win Rate'].to_numpy()))
    add_peak_labels(ax2, results_df['RSI Threshold'].to_numpy(), results_df['Expectancy'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Expectancy'].to_numpy()))
    add_peak_labels(ax2_twin, results_df['RSI Threshold'].to_numpy(), results_df['Number of Positions'].to_numpy(), 
                    find_prominent_peaks(results_df['RSI Threshold'].to_numpy(), results_df['Number of Positions'].to_numpy()))
    
    fig.tight_layout()

    # Save the plot with the correct filename
    plot_filename = f'png/ema_cross/parameter_sensitivity/{ticker}_ema_cross_rsi.png'
    plt.savefig(plot_filename)
    logging.info(f"Plot saved as {plot_filename}")
    
    plt.show()

def main():
    logging.info("Starting main execution")
    rsi_range = np.arange(29, 79, 1)  # 30 to 80

    if USE_SYNTHETIC:
        # Download historical data for TICKER_1 and TICKER_2
        data, synthetic_ticker = use_synthetic(TICKER_1, TICKER_2, USE_HOURLY_DATA)
    else:
        # Download historical data for TICKER_1 only
        data = download_data(TICKER_1, YEARS, USE_HOURLY_DATA)
        synthetic_ticker = TICKER_1

    data = calculate_mas(data, EMA_FAST, EMA_SLOW, USE_SMA)
    data = calculate_rsi(data, RSI_PERIOD)
    
    # Log some statistics about the data
    logging.info(f"Data statistics: Close price - Min: {data['Close'].min()}, Max: {data['Close'].max()}, Mean: {data['Close'].mean()}")
    logging.info(f"RSI statistics: Min: {data['RSI'].min()}, Max: {data['RSI'].max()}, Mean: {data['RSI'].mean()}")
    
    results_df = run_sensitivity_analysis(data, rsi_range)
    
    pl.Config.set_fmt_str_lengths(20)
    plot_results(synthetic_ticker, results_df)
    logging.info("Main execution completed")

if __name__ == "__main__":
    main()
