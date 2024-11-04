import numpy as np
import matplotlib.pyplot as plt
from typing import TypedDict
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.macd.tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from app.macd.tools.backtest_strategy import backtest_strategy
from app.macd.tools.calculate_expectancy import calculate_expectancy
from app.utils import get_data
from app.tools.get_config import get_config

class Config(TypedDict):
    PERIOD: str
    YEARS: float
    USE_YEARS: bool
    USE_HOURLY: bool
    USE_SYNTHETIC: bool
    TICKER: str
    TICKER_1: str
    TICKER_2: str
    SHORT: bool

# Default Configuration
CONFIG: Config = {
    "YEARS": 4.4,
    "USE_YEARS": True,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'MSTR',
    "USE_SYNTHETIC": True,
    "TICKER_1": 'MSTR',
    "TICKER_2": 'BTC-USD',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "WINDOWS": 55
}

config = get_config(CONFIG)

def plot_3d_scatter(results, expectancy_results):
    """Plot two 3D scatter plots: one for Total Return and one for Expectancy."""
    fig = plt.figure(figsize=(20, 8))
    
    # Total Return plot
    ax1 = fig.add_subplot(121, projection='3d')
    plot_single_3d_scatter(fig, ax1, results, 'Total Return')
    
    # Expectancy plot
    ax2 = fig.add_subplot(122, projection='3d')
    plot_single_3d_scatter(fig, ax2, expectancy_results, 'Expectancy')
    
    plt.tight_layout()
    plt.show()

def plot_single_3d_scatter(fig, ax, data, title):
    """Plot a single 3D scatter plot."""
    short_windows, long_windows, signal_windows = np.array([]), np.array([]), np.array([])
    values = np.array([])
    
    for (short, long), row in data.iterrows():
        for signal, val in row.items():
            short_windows = np.append(short_windows, short)
            long_windows = np.append(long_windows, long)
            signal_windows = np.append(signal_windows, signal)
            values = np.append(values, val)
    
    sc = ax.scatter(short_windows, long_windows, signal_windows, c=values, cmap='viridis')
    ax.set_xlabel('Short Window')
    ax.set_ylabel('Long Window')
    ax.set_zlabel('Signal Window')
    ax.set_title(f'3D Scatter Plot of {title}')
    fig.colorbar(sc, ax=ax, label=title)

def main():
    short_windows = np.linspace(8, 20, 13, dtype=int)  # 13 values from 8 to 20 days
    long_windows = np.linspace(13, 34, 22, dtype=int)  # 22 values from 13 to 34 days
    signal_windows = np.linspace(5, 13, 9, dtype=int)  # 9 values from 5 to 13 days

    data = get_data(config)

    # Perform sensitivity analysis
    results, expectancy_results = parameter_sensitivity_analysis(data, short_windows, long_windows, signal_windows, config["SHORT"])
    
    # Find the best parameter combination for Total Return
    best_params = results.stack().idxmax()
    best_return = results.stack().max()
    short_window, long_window, signal_window = best_params[0], best_params[1], best_params[2]
    
    best_params_expectancy = expectancy_results.stack().idxmax()
    best_expectancy_value = expectancy_results.stack().max()

    short_period_expectancy , long_period_expectancy , signal_period_expectancy = best_params_expectancy[0], best_params_expectancy[1], best_params_expectancy[2]

    # Calculate MACD and generate signals with best parameters
    data = calculate_macd(data, short_window=short_window, long_window=long_window, signal_window=signal_window)
    data = calculate_macd_signals(data, config["SHORT"])
    
    # Backtest the strategy with best parameters
    portfolio = backtest_strategy(data, config["SHORT"])
    
    # Print performance metrics for the best parameter combination
    portfolio_stats = portfolio.stats()
    strategy_type = "Short-only" if config["SHORT"] else "Long-only"
    interval = '1h' if config["USE_HOURLY"] else '1d'
    print(f"Performance metrics for the best parameter combination ({interval} {config["TICKER"]}, {strategy_type}):")
    print(portfolio_stats)
    print(f"Best parameters for {interval} {config["TICKER"]}: Short window: {short_window}, Long window: {long_window}, Signal window: {signal_window}")
    print(f"Best total return: {best_return}")
    print(f"Expectancy for best parameters: {calculate_expectancy(portfolio)}")
    print(f"Best parameters for Expectancy: Short window: {short_period_expectancy}, Long window: {long_period_expectancy}, Signal window: {signal_period_expectancy}")
    print(f"Best expectancy value: {best_expectancy_value}")
    
    # Display 3D scatter plots of the results
    plot_3d_scatter(results, expectancy_results)

if __name__ == "__main__":
    main()
