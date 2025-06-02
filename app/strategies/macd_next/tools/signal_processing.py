"""
Signal Processing Module

This module provides utilities for processing trading signals and portfolios
for the MACD cross strategy.
"""

import polars as pl
from typing import Optional, Callable, Dict, Any, List, Tuple, Union
from app.tools.get_data import get_data
from app.macd_next.tools.signal_generation import generate_current_signals
from app.macd_next.tools.sensitivity_analysis import analyze_parameter_combination
from app.macd_next.config_types import PortfolioConfig
from app.macd_next.tools.portfolio_selection import get_best_portfolio

def process_current_signals(ticker: str, config: PortfolioConfig, log: Callable) -> Optional[pl.DataFrame]:
    """Process current signals for a ticker using the MACD cross strategy.
    
    Args:
        ticker (str): The ticker symbol to process
        config (PortfolioConfig): Configuration dictionary
        log: Logging function
        
    Returns:
        Optional[pl.DataFrame]: DataFrame of portfolios or None if processing fails
    """
    config_copy = config.copy()
    config_copy["TICKER"] = ticker
    
    try:
        # Generate and validate current signals
        current_signals = generate_current_signals(config_copy, log)
        if len(current_signals) == 0:
            log(f"No current signals found for {ticker} {config.get('DIRECTION', 'Long')}", "warning")
            return None
            
        log(f"Current signals for {ticker} {config.get('DIRECTION', 'Long')}")
        
        # Get and validate price data
        data = get_data(ticker, config_copy, log)
        if data is None:
            log(f"Failed to get price data for {ticker}", "error")
            return None
        
        # Analyze each parameter combination
        portfolios = []
        for row in current_signals.iter_rows(named=True):
            # Create strategy config for this combination
            strategy_config = config_copy.copy()
            strategy_config.update({
                "short_window": row['Short Window'],
                "long_window": row['Long Window'],
                "signal_window": row['Signal Window']
            })
            
            result = analyze_parameter_combination(
                data=data,
                short_window=row['Short Window'],
                long_window=row['Long Window'],
                signal_window=row['Signal Window'],
                config=strategy_config,
                log=log
            )
            if result is not None:
                portfolios.append(result)
        
        return pl.DataFrame(portfolios) if portfolios else None
        
    except Exception as e:
        log(f"Failed to process current signals: {str(e)}", "error")
        return None

def process_ticker_portfolios(ticker: str, config: PortfolioConfig, log: Callable) -> Optional[pl.DataFrame]:
    """Process portfolios for a single ticker using the MACD cross strategy.
    
    Args:
        ticker (str): The ticker symbol to process
        config (PortfolioConfig): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        Optional[pl.DataFrame]: DataFrame of portfolios or None if processing fails
    """
    try:
        log(f"Processing ticker: {ticker} with {config.get('DIRECTION', 'Long')} direction", "info")
        
        if config.get("USE_CURRENT", False):
            log(f"Using current market data for {ticker}", "info")
            return process_current_signals(ticker, config, log)
        else:
            from app.macd_next.tools.portfolio_processing import process_single_ticker
            
            # Log parameter ranges
            log(f"Parameter ranges for {ticker}:", "info")
            log(f"Short window: {config.get('SHORT_WINDOW_START', 2)} to {config.get('SHORT_WINDOW_END', 18)} with step {config.get('STEP', 2)}", "info")
            log(f"Long window: {config.get('LONG_WINDOW_START', 4)} to {config.get('LONG_WINDOW_END', 36)} with step {config.get('STEP', 2)}", "info")
            log(f"Signal window: {config.get('SIGNAL_WINDOW_START', 2)} to {config.get('SIGNAL_WINDOW_END', 18)} with step {config.get('STEP', 2)}", "info")
            
            portfolios = process_single_ticker(ticker, config, log)
            if portfolios is None:
                log(f"Failed to process {ticker}", "error")
                return None
            
            portfolios_df = pl.DataFrame(portfolios)
            log(f"Generated {len(portfolios_df)} portfolios for {ticker} {config.get('DIRECTION', 'Long')}", "info")
            
            # Enhance portfolios with additional metrics for consistency with ma_cross/strategies
            portfolios_df = enhance_portfolios(portfolios_df, ticker, config, log)
            
            # Log some statistics about the portfolios
            if len(portfolios_df) > 0:
                if "Win Rate [%]" in portfolios_df.columns:
                    avg_win_rate = portfolios_df.select(pl.col("Win Rate [%]")).mean().item()
                    log(f"Average Win Rate: {avg_win_rate:.2f}%", "info")
                
                if "Expectancy per Trade" in portfolios_df.columns:
                    avg_expectancy = portfolios_df.select(pl.col("Expectancy per Trade")).mean().item()
                    log(f"Average Expectancy per Trade: {avg_expectancy:.4f}", "info")
                
                if "Profit Factor" in portfolios_df.columns:
                    avg_profit_factor = portfolios_df.select(pl.col("Profit Factor")).mean().item()
                    log(f"Average Profit Factor: {avg_profit_factor:.4f}", "info")
                
                # Log Signal Count and Position Count if available
                if "Signal Count" in portfolios_df.columns:
                    avg_signal_count = portfolios_df.select(pl.col("Signal Count")).mean().item()
                    log(f"Average Signal Count: {avg_signal_count:.0f}", "info")
                
                if "Position Count" in portfolios_df.columns:
                    avg_position_count = portfolios_df.select(pl.col("Position Count")).mean().item()
                    log(f"Average Position Count: {avg_position_count:.0f}", "info")
            # Always return just the DataFrame - best portfolio selection happens after filtering
            return portfolios_df
            
            
    except Exception as e:
        log(f"Failed to process ticker portfolios: {str(e)}", "error")
        return None

def enhance_portfolios(df: pl.DataFrame, ticker: str, config: Dict[str, Any], log: Callable) -> pl.DataFrame:
    """Enhance portfolios with additional metrics for consistency with ma_cross/strategies.
    
    Args:
        df (pl.DataFrame): DataFrame of portfolios
        ticker (str): Ticker symbol
        config (Dict[str, Any]): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        pl.DataFrame: Enhanced DataFrame
    """
    try:
        if len(df) == 0:
            return df
            
        # Add Ticker column if missing
        if "Ticker" not in df.columns:
            df = df.with_columns(pl.lit(ticker).alias("Ticker"))
        
        # Add Strategy Type column if missing
        if "Strategy Type" not in df.columns:
            df = df.with_columns(pl.lit("MACD").alias("Strategy Type"))
        
        # Add Signal Entry and Signal Exit columns if missing
        # For MACD, we'll set these based on the current signal state
        # This is a simplification - in a real implementation, you'd want to check the actual signal state
        if "Signal Entry" not in df.columns:
            # Default to false, will be updated in a real implementation
            df = df.with_columns(pl.lit(False).alias("Signal Entry"))
        
        if "Signal Exit" not in df.columns:
            # Default to false, will be updated in a real implementation
            df = df.with_columns(pl.lit(False).alias("Signal Exit"))
        
        # Add Total Open Trades if missing
        if "Total Open Trades" not in df.columns:
            df = df.with_columns(pl.lit(0).alias("Total Open Trades"))
        
        # Add Signal Count and Position Count if missing
        # These would typically come from the backtest results
        if "Signal Count" not in df.columns and "Total Trades" in df.columns:
            # Estimate Signal Count as 2x Total Trades (entry + exit signals)
            df = df.with_columns((pl.col("Total Trades") * 2).alias("Signal Count"))
        
        if "Position Count" not in df.columns and "Total Trades" in df.columns:
            # Position Count is typically the same as Total Trades
            df = df.with_columns(pl.col("Total Trades").alias("Position Count"))
        
        # Ensure column naming consistency
        # Some columns might have slightly different names between ma_cross and macd_next
        column_mapping = {
            "Expectancy Per Trade": "Expectancy per Trade",
            "Expectancy": "Expectancy per Trade",
            "Win Rate": "Win Rate [%]"
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns and new_name not in df.columns:
                df = df.with_columns(pl.col(old_name).alias(new_name))
                df = df.drop(old_name)
        
        # Calculate Score if missing (used for sorting in ma_cross/strategies)
        if "Score" not in df.columns:
            # Score is typically a weighted combination of key metrics
            # This is a simplified version - adjust weights as needed
            expressions = []
            
            if "Win Rate [%]" in df.columns:
                expressions.append(pl.col("Win Rate [%]") * 0.3)
                
            if "Profit Factor" in df.columns:
                expressions.append(pl.col("Profit Factor") * 0.3)
                
            if "Expectancy per Trade" in df.columns:
                expressions.append(pl.col("Expectancy per Trade") * 0.2)
                
            if "Sortino Ratio" in df.columns:
                expressions.append(pl.col("Sortino Ratio") * 0.2)
                
            if expressions:
                df = df.with_columns(pl.sum_horizontal(expressions).alias("Score"))
            
        return df
        
    except Exception as e:
        log(f"Failed to enhance portfolios: {str(e)}", "error")
        return df
