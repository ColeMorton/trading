import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Define the list of assets
# ASSETS = ['SPY', 'QQQ', 'BTC-USD', 'SOL-USD']

ASSETS = ['CEG', 'VRTX', 'VST', 'SLV', 'ANET', 'HWM']

# ASSETS = ['CEG', 'VRTX', 'VST', 'AMD', 'MPWR', 'URI', 'BTC-USD', 'SPY']

# ASSETS = ['EURSEK=X', 'EURHUF=X', 'EURZAR=X', 'EURPLN=X']

# ASSETS = ['GWW','WAB','TSLA','AMZN','IDXX','LOW','ETN','ANET','MSFT','HD','AVGO','RCL']

# ASSETS = ['PALL', 'SPY', 'SGOL', 'BTC-USD', 'TLT', 'SIVR']

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

def plot_rolling_sortino(rolling_sortino_dict, assets):
    """Plot the rolling annualized Sortino Ratios for different time periods in a single window."""
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Rolling Annualized Sortino Ratios for Different Look-back Periods', fontsize=16)
    
    periods = ['180 Days', '90 Days', '60 Days', '30 Days']
    
    for ax, period in zip(axs.flatten(), periods):
        rolling_sortino = rolling_sortino_dict[period]
        for asset in assets:
            ax.plot(rolling_sortino[asset], label=asset)
        
        ax.set_title(f'{period} Look-back')
        ax.set_xlabel('Date')
        ax.set_ylabel('Sortino Ratio')
        ax.legend()
        ax.grid(True)
        
        # Set x-axis major locator to MonthLocator and formatter to DateFormatter
        ax.xaxis.set_major_locator(mdates.MonthLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
        
        # Rotate date labels for better readability
        ax.tick_params(axis='x', rotation=45)

        # Add a horizontal line at Sortino 0 level with increased thickness
        ax.axhline(y=0, color='black', linestyle='-', linewidth=2)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Adjust subplots to fit the main title
    plt.show()

def main():
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=292)).strftime('%Y-%m-%d')

    # Download historical data
    data = download_data(ASSETS, start_date, end_date)

    # Calculate daily returns
    returns = data.pct_change().dropna()

    # Calculate the rolling annualized Sortino Ratios for different look-back periods
    rolling_sortino_dict = {
        '180 Days': calculate_rolling_sortino(returns, window=180),
        '90 Days': calculate_rolling_sortino(returns, window=90),
        '60 Days': calculate_rolling_sortino(returns, window=60),
        '30 Days': calculate_rolling_sortino(returns, window=30),
    }

    # Plot the rolling Sortino Ratios
    plot_rolling_sortino(rolling_sortino_dict, ASSETS)

if __name__ == "__main__":
    main()
