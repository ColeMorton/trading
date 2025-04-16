"""
Signal Processing Module

This module provides utilities for processing trading signals and portfolios
for the MACD cross strategy.
"""

import polars as pl
from typing import Optional, Callable
from app.tools.get_data import get_data
from app.macd_next.tools.signal_generation import generate_current_signals
from app.macd_next.tools.sensitivity_analysis import analyze_parameter_combination
from app.macd_next.config_types import PortfolioConfig

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
            
            # Log some statistics about the portfolios
            if len(portfolios_df) > 0:
                if "Win Rate [%]" in portfolios_df.columns:
                    avg_win_rate = portfolios_df.select(pl.col("Win Rate [%]")).mean().item()
                    log(f"Average Win Rate: {avg_win_rate:.2f}%", "info")
                
                if "Expectancy Per Trade" in portfolios_df.columns:
                    avg_expectancy = portfolios_df.select(pl.col("Expectancy Per Trade")).mean().item()
                    log(f"Average Expectancy Per Trade: {avg_expectancy:.4f}", "info")
                
                if "Profit Factor" in portfolios_df.columns:
                    avg_profit_factor = portfolios_df.select(pl.col("Profit Factor")).mean().item()
                    log(f"Average Profit Factor: {avg_profit_factor:.4f}", "info")
            
            return portfolios_df
            
    except Exception as e:
        log(f"Failed to process ticker portfolios: {str(e)}", "error")
        return None
