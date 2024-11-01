import logging
import polars as pl
from app.utils import calculate_mas
from app.tools.generate_ma_signals import generate_ma_signals

def calculate_ma_and_signals(data: pl.DataFrame, short_window: int, long_window: int, config: dict) -> pl.DataFrame:
    """Calculate MAs and generate trading signals."""
    ma_type = "SMA" if config.get('USE_SMA', False) else "EMA"
    logging.info(f"Calculating {ma_type}s and signals with short window {short_window} and long window {long_window}")
    
    try:
        # Calculate moving averages
        data = calculate_mas(data, short_window, long_window, config.get('USE_SMA', False))
        
        # Generate signals based on MA crossovers
        entries, exits = generate_ma_signals(data, config)
        
        # Add Signal column (1 for entry, 0 for no signal)
        data = data.with_columns([
            pl.when(entries).then(1).otherwise(0).alias("Signal")
        ])
        
        # Add Position column (shifted Signal)
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        return data
        
    except Exception as e:
        logging.error(f"Failed to calculate {ma_type}s and signals: {e}")
        raise
