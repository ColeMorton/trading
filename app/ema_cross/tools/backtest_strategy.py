import polars as pl
import pandas as pd
import vectorbt as vbt
import logging

def backtest_strategy(data: pl.DataFrame, config: dict) -> vbt.Portfolio:
    """
    Backtest the MA cross strategy.
    
    Args:
        data: Price data with signals
        config: Configuration dictionary
        
    Returns:
        Portfolio object with backtest results
    """
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        if config.get('SHORT', False):
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                short_entries=data_pd['Signal'] == 1,
                short_exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        else:
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                entries=data_pd['Signal'] == 1,
                exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        
        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise
