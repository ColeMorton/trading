from typing import Dict, Tuple
import polars as pl
import pandas as pd
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals

def generate_signals(data_dict: Dict[str, pd.DataFrame], config: Dict) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate entry and exit signals for multiple strategies.
    
    Args:
        data_dict (Dict[str, pd.DataFrame]): Dictionary of price data for each symbol
        config (Dict): Configuration dictionary containing strategy parameters
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame]: Entry and exit signals for each strategy
    """
    # Get a reference index from the first dataframe
    reference_index = next(iter(data_dict.values())).index
    
    # Find common date range across all dataframes
    common_index = reference_index
    for df in data_dict.values():
        common_index = common_index.intersection(df.index)
    
    # Initialize DataFrames for entries and exits
    entries_df = pd.DataFrame(index=common_index)
    exits_df = pd.DataFrame(index=common_index)
    
    # Process each strategy
    for strategy_name, strategy in config['strategies'].items():
        symbol = strategy['symbol']
        df = data_dict[symbol]
        
        # Filter to common date range
        df = df.loc[common_index]
        
        # Create polars Series from Close prices
        close_series = pl.Series('Close', df['Close'].values)
        
        # Create strategy-specific config
        strategy_config = {
            'USE_SMA': strategy.get('use_sma', config.get('USE_SMA', False)),
            'USE_RSI': strategy.get('use_rsi', config.get('USE_RSI', False)),
            'RSI_THRESHOLD': strategy.get('rsi_threshold', config.get('RSI_THRESHOLD', 70)),
            'SHORT': strategy.get('short', config.get('SHORT', False))
        }
        
        # Calculate moving averages and initial signals
        ma_signals = calculate_ma_and_signals(
            close_series,
            strategy['short_window'],
            strategy['long_window'],
            strategy_config
        )
        
        # Convert to numpy for easier manipulation
        close_np = df['Close'].to_numpy()
        entries_np = ma_signals['entries'].to_numpy()
        exits_np = ma_signals['exits'].to_numpy()
        
        # Initialize arrays for tracking position and entry price
        in_position = False
        entry_price = 0.0
        stop_loss_price = 0.0
        
        # Process stop loss
        for i in range(len(close_np)):
            current_price = close_np[i]
            
            if not in_position:
                if entries_np[i]:
                    # Enter position
                    in_position = True
                    entry_price = current_price
                    # Calculate stop loss price
                    stop_loss_price = entry_price * (1 - strategy['stop_loss'] / 100)
            else:
                # Check for stop loss or regular exit
                if current_price <= stop_loss_price or exits_np[i]:
                    # Exit position
                    in_position = False
                    entries_np[i] = False
                    exits_np[i] = True
                    entry_price = 0.0
                    stop_loss_price = 0.0
                else:
                    # Still in position, prevent new entry signals
                    entries_np[i] = False
        
        # Add signals to DataFrames
        entries_df[strategy_name] = entries_np
        exits_df[strategy_name] = exits_np
    
    return entries_df, exits_df
