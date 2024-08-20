import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Constants
TICKER = 'BTC-USD'
USE_PORTFOLIO = False
PORTFOLIO = {'BTC-USD': 0.56, 'SPY': 0.44}

def download_stock_data(ticker, period="1y"):
    """
    Downloads historical stock data for the given ticker or portfolio and period.

    Parameters:
    ticker (str or dict): Stock ticker symbol or dictionary of tickers with weights.
    period (str): Period for which to download data (default: "1y").

    Returns:
    pandas.DataFrame: Stock data with a 'Daily Return' column.
    """
    if isinstance(ticker, dict):
        data = None
        for symbol, weight in ticker.items():
            ticker_data = yf.download(symbol, period=period)['Adj Close']
            weighted_data = ticker_data * weight
            if data is None:
                data = weighted_data
            else:
                data += weighted_data
        data = data.to_frame(name='Adj Close')
    else:
        data = yf.download(ticker, period=period)

    data['Daily Return'] = data['Adj Close'].pct_change()
    return data

def filter_data_by_days(data, days):
    """
    Filters the stock data to include only the last specified number of days.

    Parameters:
    data (pandas.DataFrame): The stock data.
    days (int): Number of days to filter.

    Returns:
    pandas.DataFrame: Filtered stock data.
    """
    return data.tail(days)

def plot_daily_returns(data_dict, ticker):
    """
    Plots daily returns for the specified time periods with horizontal lines on the Y-axis.
    
    Parameters:
    data_dict (dict): A dictionary where keys are period names and values are the corresponding filtered data.
    ticker (str): Stock ticker symbol.
    """
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Daily Returns for {ticker}')

    # Flatten the axes array for easier iteration
    axs = axs.flatten()

    for i, (period, data) in enumerate(data_dict.items()):
        daily_returns = data['Daily Return'].dropna()

        # Plot daily returns
        axs[i].plot(data.index, daily_returns, label='Daily Return')

        # Add horizontal lines: Zero, Mean, Median, Std Dev
        mean = daily_returns.mean()
        median = daily_returns.median()
        std_dev = daily_returns.std()

        axs[i].axhline(y=0, color='black', linestyle='-', linewidth=1, label='Zero Line')
        axs[i].axhline(y=mean, color='blue', linestyle='--', linewidth=1, alpha=0.5, label=f'Mean Line ({mean})')
        axs[i].axhline(y=median, color='green', linestyle='-.', linewidth=1, alpha=0.7, label=f'Median Line ({median})')
        axs[i].axhline(y=mean + std_dev, color='red', linestyle=':', linewidth=1, alpha=0.7, label=f'+1 Std Dev ({mean + std_dev})')
        axs[i].axhline(y=mean - std_dev, color='red', linestyle=':', linewidth=1, alpha=0.7, label=f'-1 Std Dev ({mean - std_dev})')

        axs[i].set_title(f'Last {period} Days')
        axs[i].set_xlabel('Date')
        axs[i].set_ylabel('Daily Return')

        axs[i].legend()

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.show()

def main():
    """
    Main function to download stock data, filter it by different periods, and plot the results.
    """
    ticker = PORTFOLIO if USE_PORTFOLIO else TICKER
    periods = [180, 90, 60, 30]  # Different periods to visualize

    # Download and filter the data
    data = download_stock_data(ticker)
    data_dict = {days: filter_data_by_days(data, days) for days in periods}

    # Plot the daily returns for the different periods
    plot_daily_returns(data_dict, ticker if isinstance(ticker, str) else "Portfolio")

if __name__ == "__main__":
    main()
