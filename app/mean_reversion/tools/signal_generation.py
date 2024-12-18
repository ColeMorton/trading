"""
Signal Generation Module

This module handles the generation of current trading signals based on
mean reversion strategy parameters.
"""

import polars as pl
import numpy as np
from typing import List, Dict, Callable, Optional
from app.tools.get_config import get_config
from app.tools.get_data import get_data
from app.tools.export_csv import export_csv
from app.mean_reversion.tools.signal_types import Config
from app.mean_reversion.tools.signal_utils import is_signal_current, check_signal_match

def calculate_signals(data: pl.DataFrame, config: Dict) -> Optional[pl.DataFrame]:
    """Calculate trading signals based on mean reversion parameters.
    
    Args:
        data: Price data DataFrame
        config: Configuration dictionary with strategy parameters
        
    Returns:
        DataFrame with added signal columns or None if calculation fails
    """
    try:
        if data is None or len(data) == 0:
            return None
            
        change_pct = config.get("change_pct", 2.00)
        candle_number = config.get("candle_number", 1)
        direction = config.get("DIRECTION", "Long").lower()
        
        # Calculate price changes
        data = data.with_columns([
            ((pl.col("Close") - pl.col("Close").shift(1)) / pl.col("Close").shift(1) * 100).alias("price_change")
        ])
        
        # Initialize Signal column with zeros
        data = data.with_columns([
            pl.lit(0).cast(pl.Int32).alias("Signal")
        ])
        
        # Generate entry signals based on price change threshold and direction
        if direction == "long":
            # Long: Enter when price drops by threshold
            data = data.with_columns([
                (pl.col("price_change") <= -change_pct).cast(pl.Int32).alias("Entry")
            ])
        else:
            # Short: Enter when price rises by threshold
            data = data.with_columns([
                (pl.col("price_change") >= change_pct).cast(pl.Int32).alias("Entry")
            ])
        
        # Generate exit signals after specified number of candles
        data = data.with_columns([
            pl.col("Entry").shift(candle_number).fill_null(False).cast(pl.Int32).alias("Exit")
        ])
        
        # Update Signal column for vectorbt (-1 for short, 1 for long, 0 for exit)
        if direction == "long":
            data = data.with_columns([
                pl.when(pl.col("Entry") == 1)
                .then(1)
                .when(pl.col("Exit") == 1)
                .then(0)
                .otherwise(pl.col("Signal"))
                .alias("Signal")
            ])
        else:
            data = data.with_columns([
                pl.when(pl.col("Entry") == 1)
                .then(-1)
                .when(pl.col("Exit") == 1)
                .then(0)
                .otherwise(pl.col("Signal"))
                .alias("Signal")
            ])
        
        return data
        
    except Exception as e:
        print(f"Signal calculation error: {str(e)}")
        return None

def get_current_signals(
    data: pl.DataFrame,
    change_pcts: List[float],
    candle_numbers: List[int],
    config: Dict,
    log: Callable
) -> pl.DataFrame:
    """
    Get current signals for all parameter combinations.
    
    Args:
        data: Price data DataFrame
        change_pcts: List of price change percentages
        candle_numbers: List of candle numbers
        config: Configuration dictionary
        log: Logging function for recording events and errors
    
    Returns:
        DataFrame containing parameter combinations with current signals
    """
    try:
        signals = []
        
        for change_pct in change_pcts:
            for candle_number in candle_numbers:
                try:
                    temp_data = data.clone()
                    temp_config = config.copy()
                    temp_config.update({
                        "change_pct": change_pct,
                        "candle_number": candle_number
                    })
                    
                    temp_data = calculate_signals(temp_data, temp_config)
                    
                    if temp_data is not None and len(temp_data) > 0:
                        current = is_signal_current(temp_data)
                        if current:
                            signals.append({
                                "Change PCT": float(change_pct),
                                "Candle Number": int(candle_number)
                            })
                except Exception as e:
                    log(f"Failed to process parameters {change_pct:.2f}, {candle_number}: {str(e)}", "warning")
                    continue

        # Create DataFrame with explicit schema
        if signals:
            return pl.DataFrame(
                signals,
                schema={
                    "Change PCT": pl.Float64,
                    "Candle Number": pl.Int32
                }
            )
        return pl.DataFrame(
            schema={
                "Change PCT": pl.Float64,
                "Candle Number": pl.Int32
            }
        )
    except Exception as e:
        log(f"Failed to get current signals: {e}", "error")
        return pl.DataFrame(
            schema={
                "Change PCT": pl.Float64,
                "Candle Number": pl.Int32
            }
        )

def generate_current_signals(config: Config, log: Callable) -> pl.DataFrame:
    """Generate current trading signals based on mean reversion parameters.
    
    Args:
        config (Config): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        pl.DataFrame: DataFrame containing current signals with parameters
    """
    try:
        config = get_config(config)
        
        # Generate parameter ranges with proper precision
        start_pct = round(config.get("CHANGE_PCT_START", 2.00), 2)
        end_pct = round(config.get("CHANGE_PCT_END", 15.00), 2)
        step_pct = config.get("CHANGE_PCT_STEP", 0.01)

        # Calculate number of steps to ensure we include end_pct
        num_steps = int(round((end_pct - start_pct) / step_pct)) + 1
        
        # Create parameter arrays with controlled precision
        change_pcts = [round(start_pct + i * step_pct, 2) for i in range(num_steps)]
        max_candles = config.get("MAX_CANDLES", 5)
        candle_numbers = list(range(1, max_candles + 1))

        data = get_data(config["TICKER"], config, log)
        if data is None:
            log("Failed to get price data", "error")
            return pl.DataFrame(
                schema={
                    "Change PCT": pl.Float64,
                    "Candle Number": pl.Int32
                }
            )

        current_signals = get_current_signals(data, change_pcts, candle_numbers, config, log)

        if not config.get("USE_SCANNER", False):
            export_csv(current_signals, "mean_reversion", config, 'current_signals')
            
            if len(current_signals) == 0:
                print("No signals found for today")
        
        return current_signals
        
    except Exception as e:
        log(f"Failed to generate current signals: {str(e)}", "error")
        return pl.DataFrame(
            schema={
                "Change PCT": pl.Float64,
                "Candle Number": pl.Int32
            }
        )

def process_mean_reversion_signals(
    ticker: str,
    config: Config,
    change_pct: float,
    candle_number: int,
    log: Callable
) -> bool:
    """
    Process mean reversion signals for a given ticker and configuration.

    Args:
        ticker: The ticker symbol to process
        config: Configuration dictionary
        change_pct: Price change percentage from scanner
        candle_number: Number of candles from scanner
        log: Logging function for recording events and errors

    Returns:
        bool: True if current signal is found, False otherwise
    """
    mr_config = config.copy()
    mr_config.update({
        "TICKER": ticker
    })
    
    signals = generate_current_signals(mr_config, log)
    
    is_current = check_signal_match(
        signals.to_dicts() if len(signals) > 0 else [],
        change_pct,
        candle_number
    )
    
    return is_current
