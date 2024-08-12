import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import json
import logging
from scipy.stats import norm

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

def fetch_data(ticker, start_date, end_date):
    """Fetch historical price data for a given ticker."""
    logging.info("Fetching data for ticker: %s, start date: %s, end date: %s", ticker, start_date, end_date)
    data = yf.download(ticker, start=start_date, end=end_date)
    if data.empty:
        logging.error("No data fetched for the given asset and date range.")
        raise ValueError("No data fetched for the given asset and date range.")
    logging.info("Data fetched successfully.")
    return data

def calculate_returns(data, timeframe):
    """Calculate returns based on the specified timeframe."""
    logging.info("Calculating returns for timeframe: %s", timeframe)

    # Use .loc to avoid SettingWithCopyWarning
    data.loc[:, 'Return'] = data['Adj Close'].pct_change()

    if timeframe == "D":
        returns = data['Return'].dropna()
        period = 'Daily'
    elif timeframe == "2W":
        returns = data['Return'].resample('2W-MON').sum().dropna()
        period = 'Fortnightly'
    elif timeframe == "W":
        returns = data['Return'].resample('W-MON').sum().dropna()
        period = 'Weekly'
    elif timeframe == "3D":
        returns = data['Return'].resample('3D').sum().dropna()
        period = '3-Day'
    else:
        logging.error("Invalid timeframe specified: %s", timeframe)
        raise ValueError("Invalid timeframe specified. Use 'D', '2W', 'W', or '3D'.")

    if returns.empty:
        logging.error("No valid returns calculated. Try increasing the date range.")
        raise ValueError("No valid returns calculated. Try increasing the date range.")

    logging.info("Returns calculated successfully.")
    return returns, period

def filter_data_by_timeframe(data, timeframe_of):
    """Filter data based on the specified timeframe."""
    logging.info("Filtering data by timeframe: %s", timeframe_of)
    if timeframe_of == "D":
        current_day_of_year = datetime.now().timetuple().tm_yday
        logging.info("current_day_of_year: %s", current_day_of_year)
        filtered_data = data[data.index.dayofyear == current_day_of_year]
        return filtered_data
    elif timeframe_of == "Day of Week":
        current_day = datetime.now().strftime('%A')
        logging.info("Current day of the week: %s", current_day)
        filtered_data = data[data.index.day_name() == current_day]
        return filtered_data
    # Additional filtering logic can be added here for other timeframes
    return data

def calculate_var(returns):
    """Calculate Value at Risk (VaR)"""
    logging.info("Calculating VaR for returns.")
    var_68 = np.percentile(returns, 32)
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)
    logging.info("VaR calculated successfully.")
    return var_68, var_95, var_99

def plot_return_distribution(returns, var_68, var_95, var_99, ticker, period, use_timeframe_of, timeframe_of):
    """Plot the return distribution with VaR lines and additional statistics."""
    logging.info("Plotting return distribution for ticker: %s, period: %s, use_timeframe_of: %s, timeframe_of: %s", ticker, period, use_timeframe_of, timeframe_of)

    # Calculate additional statistics
    mean = np.mean(returns)
    median = np.median(returns)
    std_dev = np.std(returns)

    plt.figure(figsize=(10, 6))
    sns.histplot(returns, bins=200, alpha=0.5, color='blue', edgecolor='black')
    plt.axvline(x=var_68, color='red', linestyle='--', linewidth=2, label=f'68% VaR = {var_68:.2%}')
    plt.axvline(x=var_95, color='indigo', linestyle='--', linewidth=2, label=f'95% VaR = {var_95:.2%}')
    plt.axvline(x=var_99, color='cyan', linestyle='--', linewidth=2, label=f'99% VaR = {var_99:.2%}')
    plt.axvline(x=mean, color='green', linestyle='--', linewidth=2, label=f'Mean = {mean:.2%}')
    plt.axvline(x=median, color='orange', linestyle='--', linewidth=2, label=f'Median = {median:.2%}')
    plt.axvline(0, color='k', linestyle='-', label='Zero')

    # Calculate the return of the current
    current_return = returns[-1]
    plt.axvline(x=current_return, color='purple', linestyle='--', linewidth=2, label=f'Current Return = {current_return:.2%}')

    # Calculate Rarity based on the sign of the current return
    if current_return < 0:
        # Use only negative returns
        negative_returns = returns[returns < 0]
        rarity = norm.cdf(current_return, loc=np.mean(negative_returns), scale=np.std(negative_returns))
    else:
        # Use only positive returns
        positive_returns = returns[returns > 0]
        rarity = norm.cdf(current_return, loc=np.mean(positive_returns), scale=np.std(positive_returns))

    rarity_percentage = (1 - rarity) * 100  # Convert to percentage

    std_dev = returns.std()
    skewness = returns.skew()
    kurtosis = returns.kurtosis()

    plt.text(0.95, 0.95, f'Std Dev: {std_dev:.2%}\nSkewness: {skewness:.2f}\nKurtosis: {kurtosis:.2f}\nRarity: {rarity_percentage:.2f}%', 
             transform=plt.gca().transAxes, verticalalignment='top', horizontalalignment='right', fontsize=10)

    plt.title(f'{ticker} Return Distribution (VaR, Mean, Median)', fontsize=14)
    xlabel = f'{period} Return' if not use_timeframe_of else f'{period} Return ({timeframe_of})'
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.show()
    logging.info("Return distribution plotted successfully.")

def main():
    """Main function to execute the return distribution analysis."""
    logging.info("Starting return distribution analysis.")
    config = load_config()

    USE_DATES = config['USE_DATES']
    start_date = config['START_DATE']
    end_date = config['END_DATE']
    YEARS = config['YEARS']
    TICKER = config['TICKER']
    timeframe = config['TIMEFRAME']
    USE_TIMEFRAME_OF = config['USE_TIMEFRAME_OF']
    TIMEFRAME_OF = config['TIMEFRAME_OF']

    if not USE_DATES:
        logging.info("Using default date range based on YEARS.")
        end_date = datetime.now()
        start_date = end_date - timedelta(365 * YEARS)
        logging.info("end_date: %s", end_date)
        logging.info("start_date: %s", start_date)

    # Fetch asset price data
    data = fetch_data(TICKER, start_date, end_date)

    # Filter data if TIMEFRAME_OF is true
    if USE_TIMEFRAME_OF:
        data = filter_data_by_timeframe(data, TIMEFRAME_OF)
        logging.info("filter_data_by_timeframe: %s", data)

        if TIMEFRAME_OF == "Day of Week" or TIMEFRAME_OF == "Day of Month":
            timeframe = "D"
        elif TIMEFRAME_OF == "Week of Year":
            timeframe = "W"
        elif TIMEFRAME_OF == "Month of Year":
            timeframe = "M"

    # Calculate returns based on the toggles
    returns, period = calculate_returns(data, timeframe)

    # Calculate Historical Simulation VaR (95% and 99%)
    var_68, var_95, var_99 = calculate_var(returns)

    # Plot Return Distribution
    plot_return_distribution(returns, var_68, var_95, var_99, TICKER, period, USE_TIMEFRAME_OF, TIMEFRAME_OF)

    # Print some diagnostic information
    print(f"\nTotal days of data: {len(data)}")
    print(f"Number of {period.lower()} returns: {len(returns)}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    logging.info("Return distribution analysis completed.")

if __name__ == "__main__":
    main()