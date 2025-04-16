"""
Signal Generation Module

This module handles the generation of trading signals based on
MACD cross strategy parameters.
"""

import polars as pl
from typing import Dict, Optional, Callable
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.export_csv import export_csv

def calculate_macd(data: pl.DataFrame, short_window: int, long_window: int, signal_window: int) -> pl.DataFrame:
    """Calculate MACD and Signal line values.
    
    Args:
        data: Price data DataFrame
        short_window: Short-term EMA period
        long_window: Long-term EMA period
        signal_window: Signal line EMA period
        
    Returns:
        DataFrame with MACD indicators added
    """
    # Calculate EMAs
    data = data.with_columns([
        pl.col("Close").ewm_mean(span=short_window).alias("EMA_short"),
        pl.col("Close").ewm_mean(span=long_window).alias("EMA_long")
    ])
    
    # Calculate MACD line
    data = data.with_columns([
        (pl.col("EMA_short") - pl.col("EMA_long")).alias("MACD")
    ])
    
    # Calculate Signal line
    data = data.with_columns([
        pl.col("MACD").ewm_mean(span=signal_window).alias("Signal_Line")
    ])
    
    return data

def generate_macd_signals(data: pl.DataFrame, config: Dict) -> Optional[pl.DataFrame]:
    """Generate trading signals based on MACD cross strategy parameters.
    
    Args:
        data: Price data DataFrame
        config: Configuration dictionary with strategy parameters
        
    Returns:
        DataFrame with added signal columns or None if calculation fails
    """
    try:
        if data is None or len(data) == 0:
            return None
            
        short_window = config.get("short_window", 12)
        long_window = config.get("long_window", 26)
        signal_window = config.get("signal_window", 9)
        direction = config.get("DIRECTION", "Long").lower()
        
        # Calculate MACD indicators
        data = calculate_macd(data, short_window, long_window, signal_window)
        
        # Initialize Signal column
        data = data.with_columns([
            pl.lit(0).cast(pl.Int32).alias("Signal")
        ])
        
        # Generate signals based on direction
        if direction == "long":
            # Long: Enter when MACD crosses above Signal Line
            data = data.with_columns([
                pl.when(
                    (pl.col("MACD") > pl.col("Signal_Line")) & 
                    (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1))
                )
                .then(1)  # Enter long
                .when(
                    (pl.col("MACD") < pl.col("Signal_Line")) & 
                    (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1))
                )
                .then(0)  # Exit long
                .otherwise(pl.col("Signal"))
                .alias("Signal")
            ])
        else:
            # Short: Enter when MACD crosses below Signal Line
            data = data.with_columns([
                pl.when(
                    (pl.col("MACD") < pl.col("Signal_Line")) & 
                    (pl.col("MACD").shift(1) >= pl.col("Signal_Line").shift(1))
                )
                .then(-1)  # Enter short
                .when(
                    (pl.col("MACD") > pl.col("Signal_Line")) & 
                    (pl.col("MACD").shift(1) <= pl.col("Signal_Line").shift(1))
                )
                .then(0)  # Exit short
                .otherwise(pl.col("Signal"))
                .alias("Signal")
            ])
        
        # Forward fill signals between crossovers
        data = data.with_columns([
            pl.col("Signal").forward_fill().fill_null(0).alias("Signal")
        ])
        
        return data
        
    except Exception as e:
        print(f"Signal generation error: {str(e)}")
        return None

def get_current_signals(data: pl.DataFrame, config: Dict, log: Callable) -> pl.DataFrame:
    """Get current signals for MACD parameter combinations.
    
    Args:
        data: Price data DataFrame
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        DataFrame containing parameter combinations with current signals
    """
    try:
        signals = []
        
        # Generate parameter combinations with STEP
        step = config.get("STEP", 2)  # Default to 2 if not specified
        
        # Use the specific config parameters with appropriate defaults
        short_window_start = config.get("SHORT_WINDOW_START", 2)
        short_window_end = config.get("SHORT_WINDOW_END", 18)
        long_window_start = config.get("LONG_WINDOW_START", 4)
        long_window_end = config.get("LONG_WINDOW_END", 36)
        signal_window_start = config.get("SIGNAL_WINDOW_START", 2)
        signal_window_end = config.get("SIGNAL_WINDOW_END", 18)
        
        for short_window in range(short_window_start, short_window_end + 1, step):
            for long_window in range(long_window_start, long_window_end + 1, step):
                if long_window <= short_window:
                    continue
                    
                for signal_window in range(signal_window_start, signal_window_end + 1, step):
                    try:
                        temp_config = config.copy()
                        temp_config.update({
                            "short_window": short_window,
                            "long_window": long_window,
                            "signal_window": signal_window
                        })
                        
                        temp_data = generate_macd_signals(data.clone(), temp_config)
                        
                        if temp_data is not None and len(temp_data) > 0:
                            last_signal = temp_data.tail(1).select("Signal").item()
                            if last_signal != 0:  # If there's an active signal
                                signals.append({
                                    "Short Window": short_window,
                                    "Long Window": long_window,
                                    "Signal Window": signal_window,
                                    "Signal": last_signal
                                })
                                
                    except Exception as e:
                        log(f"Failed to process parameters {short_window}/{long_window}/{signal_window}: {str(e)}", "warning")
                        continue
        
        # Create DataFrame with explicit schema
        if signals:
            return pl.DataFrame(signals)
        return pl.DataFrame(schema={
            "Short Window": pl.Int32,
            "Long Window": pl.Int32,
            "Signal Window": pl.Int32,
            "Signal": pl.Int32
        })
        
    except Exception as e:
        log(f"Failed to get current signals: {str(e)}", "error")
        return pl.DataFrame(schema={
            "Short Window": pl.Int32,
            "Long Window": pl.Int32,
            "Signal Window": pl.Int32,
            "Signal": pl.Int32
        })

def generate_current_signals(config: Dict, log: Callable) -> pl.DataFrame:
    """Generate current trading signals based on MACD parameters.
    
    Args:
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        DataFrame containing current signals with parameters
    """
    try:
        config = get_config(config)
        
        data = get_data(config["TICKER"], config, log)
        if data is None:
            log("Failed to get price data", "error")
            return pl.DataFrame(schema={
                "Short Window": pl.Int32,
                "Long Window": pl.Int32,
                "Signal Window": pl.Int32,
                "Signal": pl.Int32
            })

        current_signals = get_current_signals(data, config, log)

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "macd_cross", config, 'current_signals')
            
            if len(current_signals) == 0:
                print("No signals found for today")
        
        return current_signals
        
    except Exception as e:
        log(f"Failed to generate current signals: {str(e)}", "error")
        return pl.DataFrame(schema={
            "Short Window": pl.Int32,
            "Long Window": pl.Int32,
            "Signal Window": pl.Int32,
            "Signal": pl.Int32
        })
