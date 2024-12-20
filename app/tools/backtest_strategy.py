import polars as pl
import vectorbt as vbt
from typing import Callable, Dict, Any

def backtest_strategy(data: pl.DataFrame, config: dict, log: Callable) -> vbt.Portfolio:
    """
    Backtest the MA cross strategy.
    
    Args:
        data: Price data with signals
        config: Configuration dictionary containing:
            - USE_HOURLY (bool): Whether to use hourly data
            - DIRECTION (str): 'Long' or 'Short' for position direction
            - STOP_LOSS (float, optional): Stop loss percentage (0-100). If not provided, no stop loss is used.
            - short_window (int, optional): Short-term window size
            - long_window (int, optional): Long-term window size
            - signal_window (int, optional): Signal line window size
        log: Logging function for recording events and errors
        
    Returns:
        Portfolio object with backtest results
    """
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        # Portfolio parameters
        params = {
            'close': data_pd['Close'],
            'init_cash': 1000,
            'fees': 0.001,
            'freq': freq
        }
        
        # Add stop loss only if explicitly set
        if "STOP_LOSS" in config and config["STOP_LOSS"] is not None:
            params['sl_stop'] = config["STOP_LOSS"] / 100  # Convert percentage to fraction
        
        if config.get('DIRECTION', 'Long').lower() == 'short':
            # For short positions, enter when Signal is -1 (fast MA crosses below slow MA)
            params['short_entries'] = data_pd['Signal'] == -1
            params['short_exits'] = data_pd['Signal'] == 0
        else:
            # For long positions, enter when Signal is 1 (fast MA crosses above slow MA)
            params['entries'] = data_pd['Signal'] == 1
            params['exits'] = data_pd['Signal'] == 0
        
        portfolio = vbt.Portfolio.from_signals(**params)
        
        # Create a custom stats method that includes window parameters
        def stats(self) -> Dict[str, Any]:
            original_stats = super(type(portfolio), self).stats()
            stats_dict = {k: v for k, v in original_stats.items()}
            
            # Add window parameters
            stats_dict['Short Window'] = config.get('short_window', 0)
            stats_dict['Long Window'] = config.get('long_window', 0)
            stats_dict['Signal Window'] = config.get('signal_window', 0)
            
            return stats_dict
        
        # Attach the custom stats method to the portfolio instance
        portfolio.stats = stats.__get__(portfolio)
        
        return portfolio
        
    except Exception as e:
        log(f"Backtest failed: {e}", "error")
        raise
