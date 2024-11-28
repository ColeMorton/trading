"""
Signal Processing Module

This module provides utilities for processing trading signals and portfolios.
"""

import polars as pl
from typing import Optional
from app.tools.get_data import get_data
from app.ema_cross.tools.signal_generation import generate_current_signals
from app.ema_cross.tools.sensitivity_analysis import analyze_window_combination
from app.ema_cross.config_types import PortfolioConfig

def process_current_signals(ticker: str, config: PortfolioConfig, log) -> Optional[pl.DataFrame]:
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
            log("No current signals found", "warning")
            return None
            
        log(f"Current signals for {ticker} {'SMA' if config.get('USE_SMA', False) else 'EMA'}")
        
        # Get and validate price data
        data = get_data(ticker, config_copy)
        if data is None:
            log(f"Failed to get price data for {ticker}", "error")
            return None
        
        # Analyze each window combination
        portfolios = []
        for row in current_signals.iter_rows(named=True):
            result = analyze_window_combination(
                data,
                row['Short Window'],
                row['Long Window'],
                config_copy,
                log
            )
            if result is not None:
                portfolios.append(result)
        
        return pl.DataFrame(portfolios) if portfolios else None
        
    except Exception as e:
        log(f"Failed to process current signals: {str(e)}", "error")
        return None

def process_ticker_portfolios(ticker: str, config: PortfolioConfig, log) -> Optional[pl.DataFrame]:
    """Process portfolios for a single ticker.
    
    Args:
        ticker (str): The ticker symbol to process
        config (PortfolioConfig): Configuration dictionary
        log: Logging function
        
    Returns:
        Optional[pl.DataFrame]: DataFrame of portfolios or None if processing fails
    """
    try:
        if config.get("USE_CURRENT", False):
            return process_current_signals(ticker, config, log)
        else:
            from app.ema_cross.tools.portfolio_processing import process_single_ticker
            portfolios = process_single_ticker(ticker, config, log)
            if portfolios is None:
                log(f"Failed to process {ticker}", "error")
                return None
                
            portfolios_df = pl.DataFrame(portfolios)
            log(f"Results for {ticker} {'SMA' if config.get('USE_SMA', False) else 'EMA'}")
            return portfolios_df
            
    except Exception as e:
        log(f"Failed to process ticker portfolios: {str(e)}", "error")
        return None
