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
from app.tools.stats_converter import convert_stats
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
        ValueError: If fewer than two strategies are provided or invalid configuration
        Exception: If processing fails for any strategy
    """
    try:
        # Validate input
        if not strategies:
            log("No strategies provided", "error")
            raise ValueError("Strategies list cannot be empty")
            
        if len(strategies) < 2:
            log("Insufficient number of strategies", "error")
            raise ValueError("At least two strategies are required for concurrency analysis")
        
        log(f"Processing {len(strategies)} strategies", "info")
        
        # Validate strategy configurations
        for i, strategy_config in enumerate(strategies, 1):
            log(f"Validating strategy {i} configuration", "info")
            
            required_fields = ["TICKER", "SHORT_WINDOW", "LONG_WINDOW"]
            missing_fields = [field for field in required_fields if field not in strategy_config]
            if missing_fields:
                log(f"Strategy {i} missing required fields: {missing_fields}", "error")
                raise ValueError(f"Strategy {i} missing required fields: {missing_fields}")
            
            direction = "Short" if strategy_config.get("DIRECTION", "Long") == "Short" else "Long"
            timeframe = "Hourly" if strategy_config.get("USE_HOURLY", False) else "Daily"
            log(f"Strategy {i} - {strategy_config['TICKER']}: {timeframe} ({direction})", "info")
        
        strategy_data = []
        for i, strategy_config in enumerate(strategies, 1):
            try:
                log(f"Fetching data for strategy {i}: {strategy_config['TICKER']}", "info")
                data = get_data(strategy_config["TICKER"], strategy_config, log)
                
                # Determine if this is a short strategy
                is_short = strategy_config.get("DIRECTION", "Long") == "Short"
                direction = "Short" if is_short else "Long"
                
                # Process based on strategy type
                if 'SIGNAL_WINDOW' in strategy_config:
                    log(f"Processing {direction} MACD strategy {i}/{len(strategies)}", "info")
                    log(f"MACD periods: {strategy_config['SHORT_WINDOW']}/"
                        f"{strategy_config['LONG_WINDOW']}/"
                        f"{strategy_config['SIGNAL_WINDOW']}", "info")
                        
                    data = calculate_macd(
                        data,
                        short_window=strategy_config['SHORT_WINDOW'],
                        long_window=strategy_config['LONG_WINDOW'],
                        signal_window=strategy_config['SIGNAL_WINDOW']
                    )
                    data = calculate_macd_signals(data, is_short)
                    data = data.with_columns([
                        pl.col("Signal").shift(1).fill_null(0).alias("Position")
                    ])
                    log(f"MACD signals calculated for {strategy_config['TICKER']}", "info")
                    
                else:
                    log(f"Processing {direction} MA cross strategy {i}/{len(strategies)}", "info")
                    log(f"MA windows: {strategy_config['SHORT_WINDOW']}/"
                        f"{strategy_config['LONG_WINDOW']}", "info")
                        
                    data = calculate_ma_and_signals(
                        data,
                        strategy_config['SHORT_WINDOW'],
                        strategy_config['LONG_WINDOW'],
                        strategy_config,
                        log
                    )
                    # Convert signals to positions and ensure proper position tracking
                    data = data.with_columns([
                        pl.col("Signal").shift(1).fill_null(0).alias("Position")
                    ])
                    log(f"MA signals calculated and positions set for {strategy_config['TICKER']}", "info")
                    
                    # Log position statistics for verification
                    positions = data["Position"].to_numpy()
                    position_changes = (positions[1:] != positions[:-1]).sum()
                    log(f"Strategy {i} position changes detected: {position_changes}", "info")
                
                # Calculate expectancy
                log(f"Running backtest for {strategy_config['TICKER']}", "info")
                portfolio = backtest_strategy(data, strategy_config, log)
                stats = convert_stats(portfolio.stats(), log, strategy_config)
                strategy_config['EXPECTANCY_PER_MONTH'] = stats['Expectancy per Month']
                log(f"Expectancy per month for {strategy_config['TICKER']}: "
                    f"{stats['Expectancy per Month']:.4f}", "info")
                
                strategy_data.append(data)
                log(f"Successfully processed strategy {i}: {strategy_config['TICKER']}", "info")
                
            except Exception as e:
                log(f"Error processing strategy {i} ({strategy_config['TICKER']}): {str(e)}", "error")
                raise
        
        log(f"Successfully processed all {len(strategies)} strategies", "info")
        return strategy_data, strategies
        
    except Exception as e:
        log(f"Error in strategy processing: {str(e)}", "error")
        raise
