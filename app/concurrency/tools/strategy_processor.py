"""
Strategy Processing Module.

This module handles the preparation and processing of strategy data for concurrency analysis.
It processes both MACD and MA cross strategies, calculating signals and positions.
"""

from typing import List, Tuple, Callable
import polars as pl
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.tools.backtest_strategy import backtest_strategy
from app.tools.file_utils import convert_stats
from app.concurrency.tools.types import StrategyConfig

def process_strategies(
    strategies: List[StrategyConfig], 
    log: Callable[[str, str], None]
) -> Tuple[List[pl.DataFrame], List[StrategyConfig]]:
    """Process multiple trading strategies and prepare their data for concurrency analysis.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations to process
        log: Callable for logging messages

    Returns:
        Tuple[List[pl.DataFrame], List[StrategyConfig]]: Processed data and updated configs

    Raises:
        ValueError: If fewer than two strategies are provided
        Exception: If processing fails for any strategy
    """
    if len(strategies) < 2:
        raise ValueError("At least two strategies are required for concurrency analysis")
        
    log(f"Processing {len(strategies)} strategies")
    for i, strategy_config in enumerate(strategies, 1):
        direction = "Short" if strategy_config.get("DIRECTION", "Long") == "Short" else "Long"
        log(f"Strategy {i} - {strategy_config['TICKER']}: "
            f"{'Hourly' if strategy_config.get('USE_HOURLY', False) else 'Daily'} ({direction})")
    
    strategy_data = []
    for strategy_config in strategies:
        data = get_data(strategy_config["TICKER"], strategy_config, log)
        
        # Determine if this is a short strategy
        is_short = strategy_config.get("DIRECTION", "Long") == "Short"
        direction = "Short" if is_short else "Long"
        
        if 'SIGNAL_PERIOD' in strategy_config:
            log(f"Processing {direction} MACD strategy with periods: "
                f"{strategy_config['SHORT_WINDOW']}/{strategy_config['LONG_WINDOW']}/"
                f"{strategy_config['SIGNAL_PERIOD']}")
            data = calculate_macd(
                data,
                short_window=strategy_config['SHORT_WINDOW'],
                long_window=strategy_config['LONG_WINDOW'],
                signal_window=strategy_config['SIGNAL_PERIOD']
            )
            data = calculate_macd_signals(data, is_short)
            data = data.with_columns([
                pl.col("Signal").shift(1).fill_null(0).alias("Position")
            ])
        else:
            log(f"Processing {direction} MA cross strategy with windows: "
                f"{strategy_config['SHORT_WINDOW']}/{strategy_config['LONG_WINDOW']}")
            data = calculate_ma_and_signals(
                data, 
                strategy_config['SHORT_WINDOW'], 
                strategy_config['LONG_WINDOW'], 
                strategy_config,
                log
            )
        
        # Add expectancy per day to the strategy config
        portfolio = backtest_strategy(data, strategy_config, log)
        stats = convert_stats(portfolio.stats(), strategy_config)
        strategy_config['EXPECTANCY_PER_DAY'] = stats['Expectancy per Day']
        strategy_data.append(data)
    
    return strategy_data, strategies
