"""
Strategy Processing Module.

This module handles the preparation and processing of strategy data for concurrency analysis.
It processes both MACD and MA cross strategies, calculating signals and positions.
"""

from typing import List, Tuple, Callable
import polars as pl
import pandas as pd
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.calculate_macd import calculate_macd
from app.tools.calculate_macd_signals import calculate_macd_signals
from app.concurrency.tools.atr_strategy import process_atr_strategy
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
            # Normalize field names first (handle both uppercase and lowercase)
            field_mapping = {
                "TICKER": ["ticker", "TICKER"],
                "LENGTH": ["length", "LENGTH"],
                "MULTIPLIER": ["multiplier", "MULTIPLIER"],
                "SHORT_WINDOW": ["short_window", "SHORT_WINDOW"],
                "LONG_WINDOW": ["long_window", "LONG_WINDOW"],
                "SIGNAL_WINDOW": ["signal_window", "SIGNAL_WINDOW"],
                "DIRECTION": ["direction", "DIRECTION"],
                "STRATEGY_TYPE": ["type", "STRATEGY_TYPE"]
            }
            
            # Copy values from lowercase to uppercase keys
            for upper_key, possible_keys in field_mapping.items():
                for key in possible_keys:
                    if key in strategy_config and upper_key not in strategy_config:
                        strategy_config[upper_key] = strategy_config[key]
            
            # Determine strategy type after normalization
            strategy_type = strategy_config.get('STRATEGY_TYPE', 'MA')
            
            # Define required fields based on strategy type
            if strategy_type == 'ATR':
                required_fields = ["TICKER", "LENGTH", "MULTIPLIER"]
            elif strategy_type == 'MACD':
                required_fields = ["TICKER", "SHORT_WINDOW", "LONG_WINDOW", "SIGNAL_WINDOW"]
            else:  # Default to MA strategy
                required_fields = ["TICKER", "SHORT_WINDOW", "LONG_WINDOW"]
            
            # Check for missing fields after normalization
            missing_fields = []
            for field in required_fields:
                # For each required field, check if any of its possible variations exist
                field_variants = [field.lower(), field]
                if not any(variant in strategy_config for variant in field_variants):
                    missing_fields.append(field)
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
                # Check if it's a MACD strategy (has SIGNAL_WINDOW > 0 or type is MACD)
                is_macd = ('SIGNAL_WINDOW' in strategy_config and strategy_config['SIGNAL_WINDOW'] > 0) or \
                          (strategy_config.get('STRATEGY_TYPE') == 'MACD') or \
                          (strategy_config.get('type') == 'MACD')
                
                # Check if it's an ATR strategy
                is_atr = (strategy_config.get('STRATEGY_TYPE') == 'ATR') or \
                         (strategy_config.get('type') == 'ATR')
                
                if is_atr:
                    log(f"Processing {direction} ATR Trailing Stop strategy {i}/{len(strategies)}", "info")
                    
                    # Process ATR strategy using the dedicated module
                    data = process_atr_strategy(
                        data,
                        strategy_config,
                        log
                    )
                    log(f"ATR signals calculated for {strategy_config['TICKER']}", "info")
                    
                elif is_macd:
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
                        
                    # The calculate_ma_and_signals function returns a tuple (DataFrame, SignalAudit)
                    # We need to extract the DataFrame from this tuple
                    result = calculate_ma_and_signals(
                        data,
                        strategy_config['SHORT_WINDOW'],
                        strategy_config['LONG_WINDOW'],
                        strategy_config,
                        log
                    )
                    
                    # Extract the DataFrame from the tuple
                    if isinstance(result, tuple) and len(result) == 2:
                        data, signal_audit = result
                        log(f"Successfully extracted DataFrame and SignalAudit from result tuple", "info")
                    else:
                        # If result is not a tuple, assume it's just the DataFrame
                        data = result
                        log(f"Result is not a tuple, assuming it's just the DataFrame", "warning")
                    log(f"MA signals calculated and positions set for {strategy_config['TICKER']}", "info")
                    
                    # Log position statistics for verification
                    positions = data["Position"].to_numpy()
                    position_changes = (positions[1:] != positions[:-1]).sum()
                    log(f"Strategy {i} position changes detected: {position_changes}", "info")
                
                # Store ATR-specific columns before backtesting (they might be lost during backtesting)
                atr_columns = {}
                if strategy_config.get('STRATEGY_TYPE') == 'ATR' or strategy_config.get('type') == 'ATR':
                    log(f"Preserving ATR columns for {strategy_config['TICKER']}", "info")
                    # Check if ATR_Trailing_Stop column exists
                    if 'ATR_Trailing_Stop' in data.columns:
                        atr_columns['ATR_Trailing_Stop'] = data.select(['Date', 'ATR_Trailing_Stop']).to_pandas()
                        log(f"Preserved ATR_Trailing_Stop column with {atr_columns['ATR_Trailing_Stop']['ATR_Trailing_Stop'].notna().sum()} non-null values", "info")
                    else:
                        log(f"WARNING: ATR_Trailing_Stop column not found for {strategy_config['TICKER']} ATR strategy", "warning")
                
                # Calculate expectancy
                log(f"Running backtest for {strategy_config['TICKER']}", "info")
                portfolio = backtest_strategy(data, strategy_config, log)
                stats = convert_stats(portfolio.stats(), log, strategy_config, None)
                
                # Restore ATR-specific columns after backtesting
                if atr_columns and 'ATR_Trailing_Stop' in atr_columns:
                    try:
                        log(f"Restoring ATR columns for {strategy_config['TICKER']}", "info")
                        # Get the data from the portfolio
                        data_pd = portfolio._data_pd
                        
                        # Log data shapes and column info for debugging
                        log(f"Portfolio data shape: {data_pd.shape}, columns: {list(data_pd.columns)}", "info")
                        log(f"ATR data shape: {atr_columns['ATR_Trailing_Stop'].shape}, columns: {list(atr_columns['ATR_Trailing_Stop'].columns)}", "info")
                        
                        # Check if Date columns are compatible
                        log(f"Portfolio Date column type: {data_pd['Date'].dtype}", "info")
                        log(f"ATR Date column type: {atr_columns['ATR_Trailing_Stop']['Date'].dtype}", "info")
                        
                        # Ensure Date columns are the same type
                        if data_pd['Date'].dtype != atr_columns['ATR_Trailing_Stop']['Date'].dtype:
                            log(f"Converting Date columns to compatible types", "info")
                            # Convert both to datetime for safe merging
                            data_pd['Date'] = pd.to_datetime(data_pd['Date'])
                            atr_columns['ATR_Trailing_Stop']['Date'] = pd.to_datetime(atr_columns['ATR_Trailing_Stop']['Date'])
                        
                        # Merge the ATR columns back into the data
                        data_pd = data_pd.merge(atr_columns['ATR_Trailing_Stop'], on='Date', how='left')
                        log(f"Restored ATR_Trailing_Stop column with {data_pd['ATR_Trailing_Stop'].notna().sum()} non-null values", "info")
                        
                        # Update the portfolio's data
                        portfolio._data_pd = data_pd
                        
                        # Convert back to polars and update the strategy data
                        data = pl.from_pandas(data_pd)
                        log(f"Successfully restored ATR data to polars DataFrame", "info")
                    except Exception as e:
                        log(f"Error restoring ATR columns: {str(e)}", "error")
                        # Continue without the ATR columns rather than failing
                        log(f"Continuing without ATR visualization data", "warning")
                
                # Add expectancy to strategy config
                strategy_config['EXPECTANCY_PER_MONTH'] = stats['Expectancy per Month']
                strategy_config['EXPECTANCY'] = stats['Expectancy']
                strategy_config['EXPECTANCY_PER_TRADE'] = stats['Expectancy per Trade']
                
                log(f"Expectancy per month for {strategy_config['TICKER']}: "
                    f"{stats['Expectancy per Month']:.4f}", "info")
                
                # Add all portfolio stats to strategy config
                strategy_config['PORTFOLIO_STATS'] = stats
                log(f"Added portfolio stats to strategy config for {strategy_config['TICKER']}", "info")
                
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
