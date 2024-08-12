import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import json
import logging

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
    data['Return'] = data['Adj Close'].pct_change()
    
    if timeframe == "D":
        returns = data['Return'].dropna()
        period = 'Daily'
    elif timeframe == "2W":
        returns = data['Return'].resample('2W-MON').sum().dropna()
        period = 'Fortnightly'
    elif timeframe == "W":
        returns = data['Return'].resample('W-MON').sum().dropna()
        period = 'Weekly'
    else:
        logging.error("Invalid timeframe specified: %s", timeframe)
        raise ValueError("Invalid timeframe specified. Use 'D', '2W', or 'W'.")
    
    if returns.empty:
        logging.error("No valid returns calculated. Try increasing the date range.")
        raise ValueError("No valid returns calculated. Try increasing the date range.")
    
    logging.info("Returns calculated successfully.")
    return returns, period

def calculate_var(returns):
    """Calculate Value at Risk (VaR) at 95% and 99% confidence levels."""
    logging.info("Calculating VaR for returns.")
    var_95 = np.percentile(returns, 5)
    var_99 = np.percentile(returns, 1)
    logging.info("VaR calculated successfully.")
    return var_95, var_99

def plot_return_distribution(returns, var_95, var_99, ticker, period):
    """Plot the return distribution with VaR lines."""
    logging.info("Plotting return distribution for ticker: %s, period: %s", ticker, period)
    plt.figure(figsize=(10, 6))
    plt.hist(returns, bins=50, alpha=0.6, color='blue', edgecolor='black')
    plt.axvline(x=var_95, color='indigo', linestyle='--', linewidth=2, label=f'95% VaR = {var_95:.2%}')
    plt.axvline(x=var_99, color='cyan', linestyle='--', linewidth=2, label=f'99% VaR = {var_99:.2%}')
    plt.title(f'{ticker} Return Distribution (95% and 99%)', fontsize=14)
    plt.xlabel(f'{period} Return', fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    plt.legend()
    plt.grid(True)
    plt.show()
    logging.info("Return distribution plotted successfully.")

def main():
    """Main function to execute the return distribution analysis."""
    logging.info("Starting return distribution analysis.")
    
    # Load constants from config.json
    config = load_config()
    
    # Constants
    USE_DATES = config['USE_DATES']
    start_date = config['START_DATE']
    end_date = config['END_DATE']
    YEARS = config['YEARS']
    TICKER = config['TICKER']
    TIMEFRAME = config['TIMEFRAME']
    
    if not USE_DATES:
        logging.info("Using default date range based on YEARS.")
        end_date = datetime.now()
        start_date = end_date - timedelta(365 * YEARS)

    # Fetch asset price data
    data = fetch_data(TICKER, start_date, end_date)

    # Calculate returns based on the toggles
    returns, period = calculate_returns(data, TIMEFRAME)

    # Calculate Historical Simulation VaR (95% and 99%)
    var_95, var_99 = calculate_var(returns)

    # Plot Return Distribution
    plot_return_distribution(returns, var_95, var_99, TICKER, period)

    # Print some diagnostic information
    print(f"\nTotal days of data: {len(data)}")
    print(f"Number of {period.lower()} returns: {len(returns)}")
    print(f"Date range: {data.index[0]} to {data.index[-1]}")
    
    logging.info("Return distribution analysis completed.")

if __name__ == "__main__":
    main()
