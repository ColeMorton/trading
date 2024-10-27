from typing import Dict, Tuple, TypedDict, Optional
import vectorbt as vbt
import polars as pl
import numpy as np
import pandas as pd

class StrategyConfig(TypedDict):
    symbol: str
    short_window: int
    long_window: int
    stop_loss: Optional[float]
    position_size: float
    use_sma: bool

class Config(TypedDict):
    strategies: Dict[str, StrategyConfig]
    start_date: str
    end_date: str
    init_cash: float
    fees: float

def generate_signals(close_data: pl.Series, config: Config) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate MA cross signals for multiple strategies.
    
    Args:
        close_data: Close price data
        config: Configuration containing parameters for each strategy
        
    Returns:
        Tuple containing (entries DataFrame, exits DataFrame)
    """
    # Convert polars Series to pandas for vectorbt
    close_pd: pd.Series = pl.DataFrame({
        "Close": close_data,
        "Date": close_data.index
    }).to_pandas().set_index("Date")["Close"]
    
    # Create DataFrames for entries and exits with strategy names as columns
    entries: pl.DataFrame = pl.DataFrame({"Date": close_data.index})
    exits: pl.DataFrame = pl.DataFrame({"Date": close_data.index})
    
    for strategy_name, strategy_config in config['strategies'].items():
        # Determine whether to use SMA or EMA
        ewm: bool = False if strategy_config.get('use_sma', False) else True
        
        # Calculate fast and slow MAs using vectorbt (requires pandas)
        fast_ma: pd.Series = vbt.MA.run(close_pd, strategy_config['short_window'], ewm=ewm).ma
        slow_ma: pd.Series = vbt.MA.run(close_pd, strategy_config['long_window'], ewm=ewm).ma
        
        # Generate base entry/exit signals from MA cross
        base_entries: np.ndarray = (fast_ma > slow_ma).to_numpy()
        base_exits: np.ndarray = (fast_ma < slow_ma).to_numpy()
        
        if strategy_config.get('stop_loss'):
            # Initialize arrays for tracking positions and stop losses
            position_active: np.ndarray = np.zeros(len(close_data), dtype=bool)
            entry_prices: np.ndarray = np.full(len(close_data), np.nan)
            stop_loss_exits: np.ndarray = np.zeros(len(close_data), dtype=bool)
            
            # Process each day
            close_np: np.ndarray = close_pd.to_numpy()
            for i in range(1, len(close_data)):
                current_price: float = close_np[i]
                
                # Check if we have an entry signal
                if base_entries[i] and not position_active[i-1]:
                    position_active[i] = True
                    entry_prices[i] = current_price

                # Maintain position and entry price if still active
                elif position_active[i-1] and not base_exits[i] and not stop_loss_exits[i-1]:
                    position_active[i] = True
                    entry_prices[i] = entry_prices[i-1]
                
                # Check stop loss if position is active
                if position_active[i] and entry_prices[i] is not np.nan:
                    stop_price: float = entry_prices[i] * (1 - strategy_config['stop_loss']/100)
                    if current_price <= stop_price:
                        stop_loss_exits[i] = True
                        position_active[i] = False
            
            # Final entry/exit signals combining MA cross and stop loss
            entries = entries.with_columns(pl.Series(name=strategy_name, values=base_entries & ~position_active))
            exits = exits.with_columns(pl.Series(name=strategy_name, values=base_exits | stop_loss_exits))
        else:
            # For strategies without stop loss, use base signals
            entries = entries.with_columns(pl.Series(name=strategy_name, values=base_entries))
            exits = exits.with_columns(pl.Series(name=strategy_name, values=base_exits))
    
    # Convert back to pandas for vectorbt
    entries_pd: pd.DataFrame = entries.to_pandas().set_index("Date")
    exits_pd: pd.DataFrame = exits.to_pandas().set_index("Date")
            
    return entries_pd, exits_pd
