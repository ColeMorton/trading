"""
Signal Processing Module

This module provides utilities for processing trading signals and portfolios.
"""

import polars as pl
from typing import Optional, Callable
from app.tools.get_data import get_data
from app.mean_reversion.tools.signal_generation import generate_current_signals
from app.mean_reversion.tools.sensitivity_analysis import analyze_parameter_combination
from app.mean_reversion.config_types import PortfolioConfig

def process_current_signals(ticker: str, config: PortfolioConfig, log: Callable) -> Optional[pl.DataFrame]:
    """Process current signals for a ticker.
    
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
                "change_pct": row['Change PCT'],
                "candle_number": row['Candle Number']
            })
            
            result = analyze_parameter_combination(
                data=data,
                change_pct=row['Change PCT'],
                candle_number=row['Candle Number'],
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
    """Process portfolios for a single ticker.
    
    Args:
        ticker (str): The ticker symbol to process
        config (PortfolioConfig): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        Optional[pl.DataFrame]: DataFrame of portfolios or None if processing fails
    """
    try:
        if config.get("USE_CURRENT", False):
            return process_current_signals(ticker, config, log)
        else:
            from app.mean_reversion.tools.portfolio_processing import process_single_ticker
            portfolios = process_single_ticker(ticker, config, log)
            if portfolios is None:
                log(f"Failed to process {ticker}", "error")
                return None
                
            portfolios_df = pl.DataFrame(portfolios)
            log(f"Results for {ticker} {config.get('DIRECTION', 'Long')}")
            return portfolios_df
            
    except Exception as e:
        log(f"Failed to process ticker portfolios: {str(e)}", "error")
        return None
