#!/usr/bin/env python3
"""
Debug crossover detection logic for Signal Unconfirmed
"""

import polars as pl
from pathlib import Path

def debug_crossover_detection():
    """Check if the issue is with crossover detection vs static MA comparison"""
    
    # Read price data
    price_data_path = Path("data/raw/prices/SOL-USD_D.csv")
    price_data = pl.read_csv(price_data_path)
    
    print("=== CROSSOVER ANALYSIS ===")
    print(f"Total rows: {len(price_data)}")
    
    # Get last 5 rows for analysis
    last_5_rows = price_data.tail(5)
    print("\nLast 5 price points:")
    for row in last_5_rows.select(["Date", "Close"]).to_dicts():
        print(f"  {row['Date']}: {row['Close']:.2f}")
    
    # Calculate SMA 29,30 for last 5 bars
    print("\n=== SMA 29,30 ANALYSIS ===")
    sma_data = price_data.with_columns([
        pl.col("Close").cast(pl.Float64).rolling_mean(window_size=29).alias("MA_FAST"),
        pl.col("Close").cast(pl.Float64).rolling_mean(window_size=30).alias("MA_SLOW"),
    ])
    
    # Get last 5 rows with MAs
    last_5_sma = sma_data.tail(5).select(["Date", "Close", "MA_FAST", "MA_SLOW"])
    print("Last 5 bars with MAs:")
    for row in last_5_sma.to_dicts():
        fast = row['MA_FAST']
        slow = row['MA_SLOW']
        diff = fast - slow if fast and slow else None
        bullish = fast > slow if fast and slow else None
        print(f"  {row['Date']}: Close={row['Close']:.2f}, Fast={fast:.4f}, Slow={slow:.4f}, Diff={diff:.4f}, Bullish={bullish}")
    
    # Check for crossover patterns
    last_2_sma = last_5_sma.tail(2).to_dicts()
    if len(last_2_sma) >= 2:
        prev_bullish = last_2_sma[0]['MA_FAST'] > last_2_sma[0]['MA_SLOW']
        curr_bullish = last_2_sma[1]['MA_FAST'] > last_2_sma[1]['MA_SLOW']
        print(f"\nCrossover check: Previous bullish={prev_bullish}, Current bullish={curr_bullish}")
        if prev_bullish and not curr_bullish:
            print("*** BEARISH CROSSOVER DETECTED (Fast crossed below Slow) ***")
        elif not prev_bullish and curr_bullish:
            print("*** BULLISH CROSSOVER DETECTED (Fast crossed above Slow) ***")
        else:
            print("No crossover detected")
    
    # Calculate MACD 13,19,5 for last 5 bars
    print("\n=== MACD 13,19,5 ANALYSIS ===")
    macd_data = price_data.with_columns([
        pl.col("Close").cast(pl.Float64).ewm_mean(span=13, adjust=False).alias("EMA_FAST"),
        pl.col("Close").cast(pl.Float64).ewm_mean(span=19, adjust=False).alias("EMA_SLOW"),
    ]).with_columns([
        (pl.col("EMA_FAST") - pl.col("EMA_SLOW")).alias("MACD_LINE"),
    ]).with_columns([
        pl.col("MACD_LINE").ewm_mean(span=5, adjust=False).alias("MACD_SIGNAL"),
    ])
    
    # Get last 5 rows with MACD
    last_5_macd = macd_data.tail(5).select(["Date", "Close", "MACD_LINE", "MACD_SIGNAL"])
    print("Last 5 bars with MACD:")
    for row in last_5_macd.to_dicts():
        macd = row['MACD_LINE']
        signal = row['MACD_SIGNAL']
        diff = macd - signal if macd and signal else None
        bullish = macd > signal if macd and signal else None
        print(f"  {row['Date']}: Close={row['Close']:.2f}, MACD={macd:.4f}, Signal={signal:.4f}, Diff={diff:.4f}, Bullish={bullish}")
    
    # Check for crossover patterns
    last_2_macd = last_5_macd.tail(2).to_dicts()
    if len(last_2_macd) >= 2:
        prev_bullish = last_2_macd[0]['MACD_LINE'] > last_2_macd[0]['MACD_SIGNAL']
        curr_bullish = last_2_macd[1]['MACD_LINE'] > last_2_macd[1]['MACD_SIGNAL']
        print(f"\nCrossover check: Previous bullish={prev_bullish}, Current bullish={curr_bullish}")
        if prev_bullish and not curr_bullish:
            print("*** BEARISH CROSSOVER DETECTED (MACD crossed below Signal) ***")
        elif not prev_bullish and curr_bullish:
            print("*** BULLISH CROSSOVER DETECTED (MACD crossed above Signal) ***")
        else:
            print("No crossover detected")
    
    # Test with simulated price drops
    print("\n=== SIMULATED PRICE DROP ANALYSIS ===")
    
    # Test what happens if current close drops significantly
    test_prices = [180.0, 175.0, 170.0, 165.0]
    
    for test_price in test_prices:
        print(f"\n--- Testing with Close = {test_price:.1f} ---")
        
        # Create modified data
        modified_data = price_data.clone()
        last_date = modified_data.tail(1).get_column("Date").item()
        modified_data = modified_data.with_columns(
            pl.when(pl.col("Date") == last_date)
            .then(test_price)
            .otherwise(pl.col("Close"))
            .alias("Close")
        )
        
        # Test SMA
        sma_test = modified_data.with_columns([
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=29).alias("MA_FAST"),
            pl.col("Close").cast(pl.Float64).rolling_mean(window_size=30).alias("MA_SLOW"),
        ])
        
        last_sma = sma_test.tail(1)
        fast_sma = last_sma.get_column("MA_FAST").item()
        slow_sma = last_sma.get_column("MA_SLOW").item()
        sma_exit = fast_sma < slow_sma
        
        print(f"  SMA 29,30: Fast={fast_sma:.4f}, Slow={slow_sma:.4f}, Exit signal={sma_exit}")
        
        # Test MACD
        macd_test = modified_data.with_columns([
            pl.col("Close").cast(pl.Float64).ewm_mean(span=13, adjust=False).alias("EMA_FAST"),
            pl.col("Close").cast(pl.Float64).ewm_mean(span=19, adjust=False).alias("EMA_SLOW"),
        ]).with_columns([
            (pl.col("EMA_FAST") - pl.col("EMA_SLOW")).alias("MACD_LINE"),
        ]).with_columns([
            pl.col("MACD_LINE").ewm_mean(span=5, adjust=False).alias("MACD_SIGNAL"),
        ])
        
        last_macd = macd_test.tail(1)
        macd_line = last_macd.get_column("MACD_LINE").item()
        signal_line = last_macd.get_column("MACD_SIGNAL").item()
        macd_exit = macd_line < signal_line
        
        print(f"  MACD 13,19,5: MACD={macd_line:.4f}, Signal={signal_line:.4f}, Exit signal={macd_exit}")

if __name__ == "__main__":
    debug_crossover_detection()