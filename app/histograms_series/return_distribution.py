from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
from scipy.stats import norm, percentileofscore
import pandas as pd
from typing import TypedDict, NotRequired

from app.tools.download_data import download_data
from app.tools.setup_logging import setup_logging

TICKER = 'BNB-USD'

log, log_close, _, _ = setup_logging(
    module_name='return_distribution',
    log_file='return_distribution.log'
)

class DataConfig(TypedDict):
    """Configuration type definition.

    Required Fields:
        PERIOD (str): Data period

    Optional Fields:
        USE_YEARS (NotRequired[bool]): Use years
        YEARS (NotRequired[int]): Number of years
        USE_CURRENT (NotRequired[bool]): Use current
    """
    PERIOD: str
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[int]
    USE_CURRENT: NotRequired[bool]

def load_config(file_path='config.json'):
    """Load configuration settings from a JSON file."""
    log(f"Loading configuration from file: {file_path}")
    with open(file_path, 'r') as file:
        config = json.load(file)
    log("Configuration loaded successfully.")
    return config

def fetch_data(ticker: str) -> pd.DataFrame:
    """Fetch historical price data for a given ticker."""
    log(f"Fetching data for ticker: {ticker}")
    data_config: DataConfig = {
        "PERIOD": "max",
    }
    df = download_data(ticker, data_config, log)
    data = df.to_pandas()
    data.set_index('Date', inplace=True)
    if data.empty:
        log("No data fetched for the given asset and date range.", "error")
        raise ValueError("No data fetched for the given asset and date range.")
    log("Data fetched successfully.")
    return data

def calculate_returns(data, timeframe):
    """Calculate returns based on the specified timeframe."""
    log(f"Calculating returns for timeframe: {timeframe}")
    data.loc[:, 'Return'] = data.Close.pct_change()
    if timeframe == "D":
        returns = data['Return'].dropna()
    elif timeframe == "3D":
        returns = data['Return'].resample('3D').sum().dropna()
    elif timeframe == "W":
        returns = data['Return'].resample('W-MON').sum().dropna()
    elif timeframe == "2W":
        returns = data['Return'].resample('2W-MON').sum().dropna()
    else:
        log(f"Invalid timeframe specified: {timeframe}", "error")
        raise ValueError("Invalid timeframe specified. Use 'D', '3D', 'W', or '2W'.")
    if returns.empty:
        log("No valid returns calculated. Try increasing the date range.", "error")
        raise ValueError("No valid returns calculated. Try increasing the date range.")
    log("Returns calculated successfully.")
    return returns

def calculate_var(returns):
    """Calculate Value at Risk (VaR)"""
    log("Calculating VaR for returns.")
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)
    log("VaR calculated successfully.")
    return var_95, var_99

def plot_return_distribution(returns, var_95, var_99, ticker, timeframe, ax, current_return):
    """Plot the return distribution with VaR lines and additional statistics."""
    log(f"Plotting return distribution for ticker: {ticker}, timeframe: {timeframe}")
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
    # current_return = returns.iloc[-1]  # Use .iloc[-1] instead of [-1]
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
    log("Return distribution plotted successfully.")

def main():
    """Main function to execute the return distribution analysis."""
    log("Starting return distribution analysis.")
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
        # Get the last adjusted close price and the one before the resampled period
        current_close = data.Close.iloc[-1]

        # Standard trading days logic
        if timeframe == '3D':
            previous_close = data.Close.iloc[-4]  # 3 days before (plus 1 to account for pct_change offset)

        # Check if the ticker contains "-USD"
        if "-USD" in TICKER:
            # Use 7 trading days for W and 14 trading days for 2W
            if timeframe == 'W':
                previous_close = data.Close.iloc[-8]  # 7 trading days ago
            elif timeframe == '2W':
                previous_close = data.Close.iloc[-15] # 14 trading days ago
        else:
            if timeframe == 'W':
                previous_close = data.Close.iloc[-6]  # 5 trading days ago
            elif timeframe == '2W':
                previous_close = data.Close.iloc[-11] # 10 trading days ago

        # Calculate the current return
        current_return = (current_close - previous_close) / previous_close

        returns = calculate_returns(data, timeframe)
        var_95, var_99 = calculate_var(returns)
        plot_return_distribution(returns, var_95, var_99, TICKER, timeframe, ax, current_return)
    
    plt.tight_layout()
    plt.show()
    
    # Print some diagnostic information
    print(f"\nTotal days of data: {len(data)}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    log("Return distribution analysis completed.")
    log_close()

if __name__ == "__main__":
    main()
