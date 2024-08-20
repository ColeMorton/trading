import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Define the list of assets

# ASSETS = ['BTC-USD', 'QQQ', 'SPY', 'SOL-USD']

# ASSETS = ['BLDR','LLY','BTC-USD', 'SPY', 'MPC', 'EOG']

ASSETS = ['HKDUSD=X', 'AUDHKD=X']

DAYS = 90

def download_data(assets, start_date, end_date):
    """Download historical adjusted close data for the given assets."""
    return yf.download(assets, start=start_date, end=end_date)['Adj Close']

def calculate_rolling_sortino(returns, window=30, risk_free_rate=0):
    """Calculate the rolling annualized Sortino Ratio."""
    def annualized_sortino_ratio(returns, risk_free_rate=0):
        mean_return = returns.mean() * 252
        downside_deviation = np.sqrt((returns[returns < 0] ** 2).mean()) * np.sqrt(252)
        return (mean_return - risk_free_rate) / downside_deviation

    return returns.rolling(window=window).apply(annualized_sortino_ratio, raw=False)

def plot_rolling_sortino(rolling_sortino, assets):
    """Plot the rolling annualized Sortino Ratio."""
    plt.figure(figsize=(14, 7))
    for asset in assets:
        plt.plot(rolling_sortino[asset], label=asset)

    plt.title(f'Rolling Annualized Sortino Ratio ({DAYS}-day look-back)')
    plt.xlabel('Date')
    plt.ylabel('Sortino Ratio')
    plt.legend()
    plt.grid(True)

    # Set x-axis major locator to MonthLocator and formatter to DateFormatter
    ax = plt.gca()
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    # Rotate date labels for better readability
    plt.xticks(rotation=45)
    plt.show()

def main():
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=292)).strftime('%Y-%m-%d')

    # Download historical data
    data = download_data(ASSETS, start_date, end_date)

    # Calculate daily returns
    returns = data.pct_change().dropna()

    # Calculate the rolling annualized Sortino Ratio
    rolling_sortino = calculate_rolling_sortino(returns, DAYS)

    # Plot the rolling Sortino Ratios
    plot_rolling_sortino(rolling_sortino, ASSETS)

if __name__ == "__main__":
    main()
