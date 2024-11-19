"""
Protective Stop Loss Analysis Module for EMA Cross Strategy

This module analyzes the effectiveness of protective stop loss (PSL) strategies in
combination with EMA cross signals. It examines how different holding periods affect
the performance of PSL exits, considering both long and short positions.

The PSL strategy differs from regular stop loss by monitoring price action over a
specified holding period, rather than using a fixed percentage threshold.
"""

import os
import vectorbt as vbt
import polars as pl
import numpy as np
import matplotlib.pyplot as plt
from typing import TypedDict, NotRequired, List, Tuple, Callable
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi

class Config(TypedDict):
    """
    Configuration type definition for protective stop loss analysis.

    Required Fields:
        TICKER (str): Ticker symbol to analyze
        SHORT_WINDOW (int): Period for short moving average
        LONG_WINDOW (int): Period for long moving average
        RSI_PERIOD (int): Period for RSI calculation

    Optional Fields:
        USE_RSI (NotRequired[bool]): Whether to enable RSI filtering
        RSI_THRESHOLD (NotRequired[float]): RSI threshold for signal filtering
        SHORT (NotRequired[bool]): Whether to enable short positions
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
    """
    TICKER: str
    SHORT_WINDOW: int
    LONG_WINDOW: int
    RSI_PERIOD: int
    USE_RSI: NotRequired[bool]
    RSI_THRESHOLD: NotRequired[float]
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

# Default Configuration
config: Config = {
    "TICKER": 'EQR',
    "SHORT_WINDOW": 33,
    "LONG_WINDOW": 42,
    "RSI_PERIOD": 14,
    "USE_HOURLY": False,
    "USE_SMA": False,
    "USE_RSI": False,
    "RSI_THRESHOLD": 58
}

def setup_logging_for_psl() -> Tuple[Callable, Callable, Callable, object]:
    """
    Set up logging configuration for protective stop loss analysis.

    Returns:
        Tuple[Callable, Callable, Callable, object]: Tuple containing:
            - log function
            - log_close function
            - logger object
            - file handler object
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    return setup_logging('ma_cross', log_dir, '4_review_protective_stop_loss.log')

def psl_exit(price: np.ndarray, entry_price: np.ndarray, holding_period: int, short: bool) -> np.ndarray:
    """
    Generate Price Stop Loss (PSL) exit signals.

    The PSL strategy monitors price action over a specified holding period and
    generates exit signals based on adverse price movements during that period.

    Args:
        price (np.ndarray): Array of price data
        entry_price (np.ndarray): Array of entry prices
        holding_period (int): The holding period for the PSL
        short (bool): True if it's a short trade, False for long trades

    Returns:
        np.ndarray: Array of PSL exit signals (1 for exit, 0 for hold)
    """
    exit_signal = np.zeros_like(price)
    for i in range(len(price)):
        if i >= holding_period:
            if short:
                if np.any(price[i-holding_period:i] >= entry_price[i-holding_period]):
                    exit_signal[i] = 1
            else:
                if np.any(price[i-holding_period:i] <= entry_price[i-holding_period]):
                    exit_signal[i] = 1
    return exit_signal

def run_backtest(data: pl.DataFrame, entries: np.ndarray, exits: np.ndarray, config: dict) -> vbt.Portfolio:
    """
    Run a backtest using the generated signals.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        entries (np.ndarray): Array of entry signals
        exits (np.ndarray): Array of exit signals
        config (dict): The configuration dictionary

    Returns:
        vbt.Portfolio: A vectorbt Portfolio object containing the backtest results
    """
    if config["SHORT"]:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), short_entries=entries, short_exits=exits)
    else:
        return vbt.Portfolio.from_signals(data['Close'].to_numpy(), entries, exits)

def analyze_holding_periods(
    data: pl.DataFrame,
    entries: pl.Series,
    exits_ema: pl.Series,
    config: dict,
    log: Callable
) -> List[Tuple[int, float, int, float]]:
    """
    Analyze different holding periods and their impact on strategy performance.

    Args:
        data (pl.DataFrame): The input DataFrame containing price data
        entries (pl.Series): Series of entry signals
        exits_ema (pl.Series): Series of EMA-based exit signals
        config (dict): The configuration dictionary
        log (Callable): Logging function

    Returns:
        List[Tuple[int, float, int, float]]: List of tuples containing:
            - Holding period
            - Total return
            - Number of positions
            - Expectancy
    """
    # Convert entries to numpy array and ensure boolean type
    entries_np = entries.to_numpy().astype(bool)
    
    entry_price = data.with_columns(
        pl.when(pl.lit(entries_np))
        .then(pl.col('Close'))
        .otherwise(None)
        .forward_fill()
        .alias('entry_price')
    )['entry_price']

    # Calculate longest holding period
    longest_trade = pl.Series((entries_np != np.roll(entries_np, 1)).cumsum())
    longest_holding_period = longest_trade.value_counts().select(pl.col('count').max()).item()
    log(f"Longest holding period: {longest_holding_period}")

    # Convert exits_ema to numpy array and ensure boolean type
    exits_ema_np = exits_ema.to_numpy().astype(bool)

    results = []
    for holding_period in range(longest_holding_period, 0, -1):
        log(f"Processing holding period: {holding_period}")
        exits_psl = psl_exit(data['Close'].to_numpy(), entry_price.to_numpy(), holding_period, short=config.get("SHORT", False))
        # Combine exits using numpy operations
        exits = np.logical_or(exits_ema_np, exits_psl)

        pf = run_backtest(data, entries_np, exits, config)
        total_return = pf.total_return()
        num_positions = pf.positions.count()
        expectancy = pf.trades.expectancy()
        results.append((holding_period, total_return, num_positions, expectancy))

    return results

def plot_results(
    results: List[Tuple[int, float, int, float]],
    ticker: str,
    config: dict,
    log: Callable
) -> None:
    """
    Plot the results of the holding period analysis.

    Args:
        results (List[Tuple[int, float, int, float]]): Results from holding period analysis
        ticker (str): The ticker symbol being analyzed
        config (dict): The configuration dictionary
        log (Callable): Logging function
    """
    holding_periods, returns, num_positions, expectancies = zip(*results)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = 'tab:green'
    ax1.set_xlabel('Holding Period')
    ax1.set_ylabel('Expectancy', color=color)
    ax1.plot(holding_periods, expectancies, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Number of Positions', color=color)
    ax2.plot(holding_periods, num_positions, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    strategy_type = "Short-only" if config.get("SHORT", False) else "Long-only"
    rsi_info = f" with RSI({config['RSI_PERIOD']}) >= {config['RSI_THRESHOLD']}" if config.get("USE_RSI", False) else ""
    plt.title(f'{ticker} Parameter Sensitivity: Holding Period vs Expectancy ({strategy_type} Strategy{rsi_info})')
    plt.grid(True)

    # Save the plot
    plot_filename = f'png/ema_cross/parameter_sensitivity/{ticker}_protective_stop_loss.png'
    plt.savefig(plot_filename)
    log(f"Plot saved as {plot_filename}")

    plt.show()

def run(config: Config = config) -> bool:
    """
    Run the EMA Cross PSL Strategy analysis.

    This function:
    1. Sets up logging
    2. Prepares data with moving averages and RSI (if enabled)
    3. Analyzes different holding periods for PSL strategy
    4. Generates and saves visualization plots

    Args:
        config (Config): Configuration dictionary containing strategy parameters

    Returns:
        bool: True if analysis successful, raises exception otherwise

    Raises:
        Exception: If analysis fails
    """
    log, log_close, _, _ = setup_logging_for_psl()
    
    try:
        config = get_config(config)
        log(f"Starting protective stop loss analysis for {config['TICKER']}")
        
        data = get_data(config["TICKER"], config)
        data = calculate_mas(data, config['SHORT_WINDOW'], config['LONG_WINDOW'], config.get('USE_SMA', False))
        
        if config.get('USE_RSI', False):
            data = calculate_rsi(data, config['RSI_PERIOD'])
            log(f"RSI enabled with period: {config['RSI_PERIOD']}")
            
        entries, exits_ema = calculate_ma_signals(data, config)
        log("Generated entry/exit signals")
        
        results = analyze_holding_periods(data, entries, exits_ema, config, log)
        log("Holding period analysis completed")
        
        plot_results(results, config["TICKER"], config, log)
        log("Results plotted successfully")
        
        log_close()
        return True
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
