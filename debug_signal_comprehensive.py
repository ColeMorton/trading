#!/usr/bin/env python3
"""
Comprehensive debug of Signal Unconfirmed calculations
"""

import polars as pl
from pathlib import Path
import sys

sys.path.append(".")
from app.tools.strategy.signal_utils import calculate_signal_unconfirmed_realtime

def debug_signal_unconfirmed_comprehensive():
    """Comprehensive debug of Signal Unconfirmed logic"""
    
    # Read price data
    price_data_path = Path("data/raw/prices/SOL-USD_D.csv")
    price_data = pl.read_csv(price_data_path)
    
    print("=== CURRENT PRICE DATA ===")
    print(f"Latest row: {price_data.tail(1).select(['Date', 'Close']).to_dicts()[0]}")
    
    # Test different price scenarios
    current_close = price_data.tail(1).get_column("Close").item()
    test_prices = [182.32, 182.60, 180.00, 179.00]  # User's expected price, actual price, and lower prices
    
    for test_price in test_prices:
        print(f"\n=== TESTING WITH CLOSE PRICE: {test_price:.2f} ===")
        
        # Create modified price data with test price
        modified_data = price_data.clone()
        modified_data = modified_data.with_columns(
            pl.when(pl.col("Date") == modified_data.tail(1).get_column("Date").item())
            .then(test_price)
            .otherwise(pl.col("Close"))
            .alias("Close")
        )
        
        # Test SMA 29,30
        print("\n--- SMA 29,30 ---")
        sma_data = modified_data.with_columns([
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=29).alias("MA_FAST"),
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=30).alias("MA_SLOW"),
        ])
        
        last_row_sma = sma_data.tail(1)
        fast_ma_sma = last_row_sma.get_column("MA_FAST").item()
        slow_ma_sma = last_row_sma.get_column("MA_SLOW").item()
        
        print(f"Fast MA (29): {fast_ma_sma:.4f}")
        print(f"Slow MA (30): {slow_ma_sma:.4f}")
        print(f"Fast - Slow: {fast_ma_sma - slow_ma_sma:.4f}")
        print(f"Fast > Slow: {fast_ma_sma > slow_ma_sma}")
        print(f"With position=1, would generate exit signal: {fast_ma_sma < slow_ma_sma}")
        
        # Test MACD 13,19,5
        print("\n--- MACD 13,19,5 ---")
        macd_data = modified_data.with_columns([
            pl.col("Close").cast(pl.Float64).ewm_mean(span=13, adjust=False).alias("EMA_FAST"),
            pl.col("Close").cast(pl.Float64).ewm_mean(span=19, adjust=False).alias("EMA_SLOW"),
        ]).with_columns([
            (pl.col("EMA_FAST") - pl.col("EMA_SLOW")).alias("MACD_LINE"),
        ]).with_columns([
            pl.col("MACD_LINE").ewm_mean(span=5, adjust=False).alias("MACD_SIGNAL"),
        ])
        
        last_row_macd = macd_data.tail(1)
        macd_line = last_row_macd.get_column("MACD_LINE").item()
        signal_line = last_row_macd.get_column("MACD_SIGNAL").item()
        
        print(f"MACD Line: {macd_line:.4f}")
        print(f"Signal Line: {signal_line:.4f}")
        print(f"MACD - Signal: {macd_line - signal_line:.4f}")
        print(f"MACD > Signal: {macd_line > signal_line}")
        print(f"With position=1, would generate exit signal: {macd_line < signal_line}")
    
    # Now test the actual function call
    print("\n=== TESTING ACTUAL FUNCTION CALLS ===")
    
    # Test SMA 29,30
    result_sma = calculate_signal_unconfirmed_realtime(
        ticker="SOL-USD",
        strategy_type="SMA",
        fast_period=29,
        slow_period=30,
        signal_entry=False,
        signal_exit=False,
        total_open_trades=1,
        config=None,
        signal_period=None,
    )
    print(f"\nSMA 29,30 - Signal Unconfirmed: {result_sma}")
    
    # Test MACD 13,19,5
    result_macd = calculate_signal_unconfirmed_realtime(
        ticker="SOL-USD",
        strategy_type="MACD",
        fast_period=13,
        slow_period=19,
        signal_entry=False,
        signal_exit=False,
        total_open_trades=1,
        config=None,
        signal_period=5,
    )
    print(f"MACD 13,19,5 - Signal Unconfirmed: {result_macd}")
    
    # Check what MA values would trigger exit signals
    print("\n=== MA VALUES THAT WOULD TRIGGER EXIT ===")
    print("For SMA 29,30 to generate exit: Fast MA must be < Slow MA")
    print(f"Current: Fast={fast_ma_sma:.4f}, Slow={slow_ma_sma:.4f}")
    print(f"Need Fast MA to drop below {slow_ma_sma:.4f}")
    
    print("\nFor MACD 13,19,5 to generate exit: MACD Line must be < Signal Line")
    print(f"Current: MACD={macd_line:.4f}, Signal={signal_line:.4f}")
    print(f"Need MACD Line to drop below {signal_line:.4f}")

if __name__ == "__main__":
    debug_signal_unconfirmed_comprehensive()