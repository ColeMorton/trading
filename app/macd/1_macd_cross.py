import numpy as np
import matplotlib.pyplot as plt
from app.tools.setup_logging import setup_logging
from app.macd.tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from app.tools.get_data import get_data
from typing import TypedDict
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
    USE_GBM: bool
    USE_SMA: bool
    SHORT_PERIOD: bool
    LONG_WINDOW: bool
    SIGNAL_WINDOW: bool
    RSI_PERIOD: bool
    RSI_THRESHOLD: int
    USE_RSI: bool

# Default Configuration
CONFIG: Config = {
    "TICKER": 'SPY',
    "YEARS": 2,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": True,
    "USE_SYNTHETIC": False,
    "TICKER_1": 'MSTR',
    "TICKER_2": 'BTC-USD',
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "SHORT_PERIOD": 19,
    "LONG_WINDOW": 33,
    "SIGNAL_WINDOW": 13,
    "RSI_PERIOD": 14,
    "RSI_THRESHOLD": 46,  # Already an integer value
    "USE_RSI": False
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

def main(config = config):
    log, log_close, _, _ = setup_logging(
        module_name='macd_cross',
        log_file='1_macd_cross.log'
    )

    short_windows = np.linspace(8, 20, 13, dtype=int)  # 13 values from 8 to 20 days
    long_windows = np.linspace(13, 34, 22, dtype=int)  # 22 values from 13 to 34 days
    signal_windows = np.linspace(5, 13, 9, dtype=int)  # 9 values from 5 to 13 days

    data = get_data(config["TICKER"], config, log)

    # Perform sensitivity analysis
    (results, expectancy_results, sharpe_results, sortino_results, calmar_results,
     best_params, best_expectancy_params, best_sharpe_params, best_sortino_params, best_calmar_params,
     best_return, best_expectancy, best_sharpe, best_sortino, best_calmar) = parameter_sensitivity_analysis(
        data, short_windows, long_windows, signal_windows, config)
    
    # Print performance metrics for all parameter combinations
    interval = '1h' if config["USE_HOURLY"] else '1d'
    print(f"\nBest parameters for {interval} {config['TICKER']}:")
    
    print(f"\nTotal Return:")
    print(f"Short window: {best_params[0]}, Long window: {best_params[1]}, Signal window: {best_params[2]}")
    print(f"Best total return: {best_return:.2%}")
    
    print(f"\nExpectancy:")
    print(f"Short window: {best_expectancy_params[0]}, Long window: {best_expectancy_params[1]}, Signal window: {best_expectancy_params[2]}")
    print(f"Best expectancy value: {best_expectancy:.4f}")
    
    print(f"\nSharpe Ratio:")
    print(f"Short window: {best_sharpe_params[0]}, Long window: {best_sharpe_params[1]}, Signal window: {best_sharpe_params[2]}")
    print(f"Best Sharpe ratio: {best_sharpe:.4f}")
    
    print(f"\nSortino Ratio:")
    print(f"Short window: {best_sortino_params[0]}, Long window: {best_sortino_params[1]}, Signal window: {best_sortino_params[2]}")
    print(f"Best Sortino ratio: {best_sortino:.4f}")
    
    print(f"\nCalmar Ratio:")
    print(f"Short window: {best_calmar_params[0]}, Long window: {best_calmar_params[1]}, Signal window: {best_calmar_params[2]}")
    print(f"Best Calmar ratio: {best_calmar:.4f}")
    
    # Display 3D scatter plots of the results
    plot_3d_scatter(results, expectancy_results)

if __name__ == "__main__":
    main(config)
