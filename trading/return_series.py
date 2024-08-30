import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
from scipy.stats import norm, percentileofscore

# Constants
TICKER = 'CDW'
USE_PORTFOLIO = False
PORTFOLIO = {'BTC-USD': 0.56, 'SPY': 0.44}
# PORTFOLIO = {'LLY': 0.25, 'BLDR': 0.25, 'MPO': 0.25, 'EOG': 0.25}

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
        returns = data['Daily Return'].dropna() * 100

        returns = returns.dropna()

        # Plot daily returns
        axs[i].plot(data.index, returns, label='Daily Return')

        # Add horizontal lines: Zero, Mean, Median, Std Dev
        mean = returns.mean()
        median = returns.median()
        std_dev = returns.std()
        skewness = returns.skew()
        kurtosis = returns.kurtosis()

        axs[i].axhline(y=0, color='black', linestyle='-', linewidth=1, label='Zero Line')
        axs[i].axhline(y=mean, color='green', linestyle='--', linewidth=1, alpha=1, label=f'Mean Line {mean:.2f}%')
        axs[i].axhline(y=median, color='orange', linestyle='-.', linewidth=1, alpha=1, label=f'Median Line {median:.2f}%')
        axs[i].axhline(y=mean + std_dev, color='blue', linestyle=':', linewidth=1, alpha=1, label=f'+1 Std Dev {mean + std_dev:.2f}%')
        axs[i].axhline(y=mean - std_dev, color='blue', linestyle=':', linewidth=1, alpha=1, label=f'-1 Std Dev {mean - std_dev:.2f}%')

        # Calculate Rarity based on the sign of the current return
        current_return = returns.iloc[-1]  # Use .iloc[-1] instead of [-1]
        if current_return < 0:
            negative_returns = returns[returns < 0]
            rarity = norm.cdf(current_return, loc=np.mean(negative_returns), scale=np.std(negative_returns))
        else:
            positive_returns = returns[returns > 0]
            rarity = norm.cdf(current_return, loc=np.mean(positive_returns), scale=np.std(positive_returns))
        rarity_percentage = (1 - rarity) * 100  # Convert to percentage

        # Calculate Rarity based on the sign of the current return
        if current_return < 0:
            negative_returns = returns[returns < 0]
            percentile = percentileofscore(negative_returns, current_return, kind='rank')
        else:
            positive_returns = returns[returns > 0]
            percentile = percentileofscore(positive_returns, current_return, kind='rank')

        axs[i].text(0.99, 0.99, f'Std Dev: {std_dev:.2%}\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}\nRarity: {rarity_percentage:.2f}\nPercentile: {percentile:.2f}%',
            transform=axs[i].transAxes, verticalalignment='top', horizontalalignment='right', fontsize=8)

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
