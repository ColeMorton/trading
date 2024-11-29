import polars as pl
import vectorbt as vbt
from typing import Callable

def backtest_strategy(data: pl.DataFrame, config: dict, log: Callable) -> vbt.Portfolio:
    """
    Backtest the MA cross strategy.
    
    Args:
        data: Price data with signals
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
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
        
        return portfolio
    except Exception as e:
        log(f"Backtest failed: {e}", "error")
        raise
