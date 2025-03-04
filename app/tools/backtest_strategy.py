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
            - STOP_LOSS (float, optional): Stop loss as decimal (0-1). If not provided, no stop loss is used.
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
        
        # Handle stop loss configuration
        if "STOP_LOSS" in config and config["STOP_LOSS"] is not None:
            stop_loss = config["STOP_LOSS"]  # Already in decimal form (0-1) from app.tools.portfolio.loader
            if 0 < stop_loss <= 1:  # Validate range
                if config.get('SL_CANDLE_CLOSE', True):
                    # When using candle close, we calculate the stop price based on entry
                    # but execute at the candle's close price
                    params['sl_stop'] = stop_loss
                    log(f"Applied stop loss of {stop_loss*100:.2f}% with exit at candle close", "info")
                else:
                    # For immediate exit, use the actual stop loss price
                    params['sl_stop'] = stop_loss
                    # Use the actual stop loss price for exit
                    params['sl_price'] = data_pd['Close'] * (1 - stop_loss if config.get('DIRECTION', 'Long') == 'Long' else 1 + stop_loss)
                    log(f"Applied stop loss of {stop_loss*100:.2f}% with immediate exit", "info")
            else:
                log(f"Warning: Invalid stop loss value {stop_loss*100:.2f}% - must be between 0% and 100%", "warning")
        else:
            log("No stop loss configured for strategy - running without stop loss protection", "warning")
        
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
