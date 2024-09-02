import logging
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from datetime import datetime, timedelta
import json

# Set up logging
logging.basicConfig(
    filename='logs/ema_cross.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info('EMA Cross Strategy Visualization with 60-Day View Option')

# Load constants from config.json
with open('config.json', 'r') as file:
    config = json.load(file)

YEARS = config['YEARS']
USE_HOURLY_DATA = config['USE_HOURLY_DATA']
USE_SYNTHETIC = config['USE_SYNTHETIC']
TICKER = config['TICKER']
TICKER_1 = config['TICKER_1']
TICKER_2 = config['TICKER_2']
EMA_FAST = config['EMA_FAST']
EMA_SLOW = config['EMA_SLOW']

# New constant for 60-day view
SHOW_60 = True
USE_HOURLY_DATA = True
TICKER = 'BTC-USD'
EMA_FAST = 9
EMA_SLOW = 31

def download_data(ticker: str, use_hourly: bool) -> pd.DataFrame:
    """Download historical data from Yahoo Finance."""
    interval = '1h' if use_hourly else '1d'
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730 if use_hourly else 365 * YEARS)

    logging.info(f"Downloading data for {ticker}")
    try:
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        logging.info(f"Data download for {ticker} completed successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to download data for {ticker}: {e}")
        raise

def calculate_ema(data: pd.DataFrame, short_window: int, long_window: int) -> pd.DataFrame:
    """Calculate short-term and long-term EMAs."""
    logging.info(f"Calculating EMAs with short window {short_window} and long window {long_window}")
    try:
        data['EMA_short'] = data['Close'].ewm(span=short_window, adjust=False).mean()
        data['EMA_long'] = data['Close'].ewm(span=long_window, adjust=False).mean()
        logging.info(f"EMAs calculated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to calculate EMAs: {e}")
        raise

def generate_signals(data: pd.DataFrame) -> pd.DataFrame:
    """Generate trading signals based on EMA cross."""
    logging.info("Generating trading signals")
    try:
        data['Signal'] = 0
        data['Position'] = 0
        
        # Generate crossover signals
        data['Crossover'] = np.where(data['EMA_short'] > data['EMA_long'], 1, -1)
        
        # Detect changes in crossover (indicating a new cross)
        data['CrossoverChange'] = data['Crossover'].diff()
        
        # Set buy signals (1) the day after a positive crossover
        data.loc[data['CrossoverChange'] == 2, 'Signal'] = 1
        
        # Set sell signals (-1) the day after a negative crossover
        data.loc[data['CrossoverChange'] == -2, 'Signal'] = -1
        
        # Shift the signal to represent the position taken the next day
        data['Position'] = data['Signal'].shift(1)
        
        logging.info("Trading signals generated successfully")
        return data
    except Exception as e:
        logging.error(f"Failed to generate trading signals: {e}")
        raise

def create_synthetic_data() -> pd.DataFrame:
    """Create synthetic ticker data."""
    logging.info("Creating synthetic data")
    try:
        data_ticker_1 = download_data(TICKER_1, USE_HOURLY_DATA)
        data_ticker_2 = download_data(TICKER_2, USE_HOURLY_DATA)
        data_ticker_1['Close'] = data_ticker_1['Close'].fillna(method='ffill')
        data_ticker_2['Close'] = data_ticker_2['Close'].fillna(method='ffill')
        data_ticker_3 = pd.DataFrame(index=data_ticker_1.index)
        data_ticker_3['Close'] = data_ticker_1['Close'] / data_ticker_2['Close']
        logging.info("Synthetic data created successfully")
        return data_ticker_3.dropna()
    except Exception as e:
        logging.error(f"Failed to create synthetic data: {e}")
        raise

def plot_price_and_signals(data: pd.DataFrame, ticker: str, use_hourly: bool) -> None:
    """Plot price history with entry and exit markers, including zoom and pan functionality."""
    logging.info("Plotting price history with entry and exit markers, zoom, and pan")
    try:
        fig, ax = plt.subplots(figsize=(16, 10))
        plt.subplots_adjust(bottom=0.2)  # Make room for the slider

        # Apply 60-day filter if SHOW_60 is True
        if SHOW_60:
            data = data.iloc[-60:]

        lines = []
        lines.append(ax.plot(data.index, data['Close'], label='Close Price')[0])
        lines.append(ax.plot(data.index, data['EMA_short'], label=f'EMA {EMA_FAST}', alpha=0.7)[0])
        lines.append(ax.plot(data.index, data['EMA_long'], label=f'EMA {EMA_SLOW}', alpha=0.7)[0])
        
        # Plot buy signals
        buy_signals = data[data['Signal'] == 1]
        ax.scatter(buy_signals.index, buy_signals['Close'], 
                   marker='^', color='g', label='Buy Signal', s=100)
        
        # Plot sell signals
        sell_signals = data[data['Signal'] == -1]
        ax.scatter(sell_signals.index, sell_signals['Close'], 
                   marker='v', color='r', label='Sell Signal', s=100)
        
        timeframe = "Hourly" if use_hourly else "Daily"
        view_period = "Last 60 Days" if SHOW_60 else "Full Period"
        ax.set_title(f'EMA Cross Strategy ({timeframe}) for {ticker} - {view_period}')
        ax.set_xlabel('Date')
        ax.set_ylabel('Price')
        ax.legend()
        ax.grid(True)

        # Enable zooming and panning
        plt.gcf().canvas.toolbar.pan()
        plt.gcf().canvas.toolbar.zoom()

        # Add a slider for quick navigation
        ax_slider = plt.axes([0.2, 0.02, 0.6, 0.03])
        slider = Slider(ax_slider, 'Time', 0, len(data) - 1, valinit=0, valstep=1)

        def update(val):
            idx = int(slider.val)
            ax.set_xlim(data.index[max(0, idx-30)], data.index[min(len(data)-1, idx+30)])
            fig.canvas.draw_idle()

        slider.on_changed(update)

        # Add reset button
        ax_reset = plt.axes([0.8, 0.02, 0.1, 0.04])
        button_reset = Button(ax_reset, 'Reset')

        def reset(event):
            slider.reset()
            ax.set_xlim(data.index[0], data.index[-1])
            ax.set_ylim(data['Close'].min(), data['Close'].max())
            fig.canvas.draw_idle()

        button_reset.on_clicked(reset)

        plt.show()
        logging.info("Interactive price history plot created successfully")
    except Exception as e:
        logging.error(f"Failed to plot interactive price history: {e}")
        raise

def run() -> None:
    """Main execution method."""
    logging.info("Execution started")
    try:
        if USE_SYNTHETIC:
            data = create_synthetic_data()
            synthetic_ticker = f"{TICKER_1[:3]}{TICKER_2[:3]}"
        else:
            data = download_data(TICKER, USE_HOURLY_DATA)
            synthetic_ticker = TICKER

        data = calculate_ema(data, EMA_FAST, EMA_SLOW)
        data = generate_signals(data)
        plot_price_and_signals(data, synthetic_ticker, USE_HOURLY_DATA)

        logging.info("Execution finished successfully")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise

if __name__ == "__main__":
    run()