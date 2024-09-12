import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
from scipy.stats import norm, percentileofscore

TICKER = 'SOL-USD'

# Set up logging    
logging.basicConfig(
    filename='logs/return_distribution.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_config(file_path='config.json'):
    """Load configuration settings from a JSON file."""
    logging.info("Loading configuration from file: %s", file_path)
    with open(file_path, 'r') as file:
        config = json.load(file)
    logging.info("Configuration loaded successfully.")
    return config

def fetch_data(ticker):
    """Fetch historical price data for a given ticker."""
    logging.info("Fetching data for ticker: %s", ticker)
    data = yf.download(ticker, period='max', interval='1d')
    if data.empty:
        logging.error("No data fetched for the given asset and date range.")
        raise ValueError("No data fetched for the given asset and date range.")
    logging.info("Data fetched successfully.")
    return data

def calculate_returns(data, timeframe):
    """Calculate returns based on the specified timeframe."""
    logging.info("Calculating returns for timeframe: %s", timeframe)
    data.loc[:, 'Return'] = data['Adj Close'].pct_change()
    if timeframe == "D":
        returns = data['Return'].dropna()
    elif timeframe == "3D":
        returns = data['Return'].resample('3D').sum().dropna()
    elif timeframe == "W":
        returns = data['Return'].resample('W-MON').sum().dropna()
    elif timeframe == "2W":
        returns = data['Return'].resample('2W-MON').sum().dropna()
    else:
        logging.error("Invalid timeframe specified: %s", timeframe)
        raise ValueError("Invalid timeframe specified. Use 'D', '3D', 'W', or '2W'.")
    if returns.empty:
        logging.error("No valid returns calculated. Try increasing the date range.")
        raise ValueError("No valid returns calculated. Try increasing the date range.")
    logging.info("Returns calculated successfully.")
    return returns

def calculate_var(returns):
    """Calculate Value at Risk (VaR)"""
    logging.info("Calculating VaR for returns.")
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)
    logging.info("VaR calculated successfully.")
    return var_95, var_99

def plot_return_distribution(returns, var_95, var_99, ticker, timeframe, ax):
    """Plot the return distribution with VaR lines and additional statistics."""
    logging.info("Plotting return distribution for ticker: %s, timeframe: %s", ticker, timeframe)
    # Calculate additional statistics
    mean = np.mean(returns)
    median = np.median(returns)
    std_dev = returns.std()
    std_pos = mean + std_dev / 2
    std_neg = mean - std_dev / 2
    skewness = returns.skew()
    kurtosis = returns.kurtosis()
    
    sns.histplot(returns, bins=50, kde=True, ax=ax, alpha=0.2)
    ax.axvline(x=std_pos, color='blue', linestyle=':', linewidth=2, label=f'+1 Std Dev = {std_pos:.2%}')
    ax.axvline(x=std_neg, color='blue', linestyle=':', linewidth=2, label=f'-1 Std Dev = {std_neg:.2%}')
    ax.axvline(x=var_95, color='red', linestyle='--', linewidth=1, label=f'95% VaR = {var_95:.2%}')
    ax.axvline(x=var_99, color='red', linestyle='--', linewidth=1, label=f'99% VaR = {var_99:.2%}')
    ax.axvline(x=mean, color='green', linestyle='-', linewidth=1, label=f'Mean = {mean:.2%}')
    ax.axvline(x=median, color='orange', linestyle='-.', linewidth=1, label=f'Median = {median:.2%}')
    ax.axvline(0, color='k', linestyle='-', linewidth=1, label='Zero')
    
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

    ax.axvline(x=current_return, color='purple', linestyle='--', linewidth=2, label=f'Current Return = {current_return:.2%}')
    
    ax.text(0.99, 0.99, f'Std Dev: {std_dev:.2%}\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}\nRarity: {rarity_percentage:.2f}\nPercentile: {percentile:.2f}%',
            transform=ax.transAxes, verticalalignment='top', horizontalalignment='right', fontsize=8)
    
    ax.set_title(f'{timeframe} Return Distribution', fontsize=10)
    ax.set_xlabel(f'{timeframe} Return', fontsize=8)
    ax.set_ylabel('Frequency', fontsize=8)
    ax.legend(fontsize=6)
    ax.grid(True)
    logging.info("Return distribution plotted successfully.")

def main():
    """Main function to execute the return distribution analysis."""
    logging.info("Starting return distribution analysis.")
    config = load_config()
    # TICKER = config['TICKER']
    
    # Fetch asset price data
    data = fetch_data(TICKER)
    
    # Set up the plot
    fig, axs = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{TICKER} Return Distributions', fontsize=16)
    
    # Calculate returns and plot for each timeframe
    timeframes = ['2W', 'W', '3D', 'D']
    for timeframe, ax in zip(timeframes, axs.flatten()):
        returns = calculate_returns(data, timeframe)
        var_95, var_99 = calculate_var(returns)
        plot_return_distribution(returns, var_95, var_99, TICKER, timeframe, ax)
    
    plt.tight_layout()
    plt.show()
    
    # Print some diagnostic information
    print(f"\nTotal days of data: {len(data)}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    logging.info("Return distribution analysis completed.")

if __name__ == "__main__":
    main()