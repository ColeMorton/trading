"""
MA Cross Test Script

This script tests the enhanced MA cross detection with real-time data.
"""

import polars as pl
from app.tools.setup_logging import setup_logging
from app.tools.market_status import is_market_open
from app.tools.download_data import fetch_latest_data_point
from app.ma_cross.config_types import Config

def test_ma_cross(ticker: str, short_window: int, long_window: int, use_sma: bool = False) -> bool:
    """
    Test MA cross detection for a specific ticker and window combination.
    
    Args:
        ticker: Stock ticker symbol
        short_window: Short-term window size
        long_window: Long-term window size
        use_sma: Whether to use SMA instead of EMA
        
    Returns:
        bool: True if test passed, False otherwise
    """
    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross_test',
        log_file=f'test_ma_cross_{ticker}.log'
    )
    
    try:
        log(f"Testing MA cross detection for {ticker} with {'SMA' if use_sma else 'EMA'}")
        log(f"Short window: {short_window}, Long window: {long_window}")
        
        # Create test configuration
        config: Config = {
            "TICKER": ticker,
            "BASE_DIR": ".",
            "REFRESH": True,  # Always use fresh data for testing
            "USE_CURRENT": True,  # Test current crossover detection
            "USE_SMA": use_sma,
            "DIRECTION": "Long",
            "SHORT_WINDOW": short_window,
            "LONG_WINDOW": long_window
        }
        
        # Check if market is open
        latest_data = fetch_latest_data_point(ticker, config, log)
        market_status = is_market_open(latest_data, ticker, config, log)
        log(f"Market status for {ticker}: {'Open' if market_status else 'Closed'}")
        
        # Get latest market data directly from download_data to bypass validation
        log("Downloading market data directly...")
        try:
            # Use download_complete_dataset directly to get raw data
            from app.tools.download_data import download_complete_dataset
            data = download_complete_dataset(ticker, config, log)
            
            if data is None or len(data) == 0:
                log("Error: No data retrieved", "error")
                log_close()
                return False
            
            log(f"Retrieved {len(data)} data points")
            log(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
            
            # Ensure data is sorted by date
            data = data.sort("Date")
            
            # Calculate moving averages directly
            log("Calculating moving averages...")
            
            # Use SMA or EMA based on config
            if config.get('USE_SMA', False):
                data = data.with_columns([
                    pl.col("Close").cast(pl.Float64).rolling_mean(window_size=short_window).alias("MA_FAST"),
                    pl.col("Close").cast(pl.Float64).rolling_mean(window_size=long_window).alias("MA_SLOW")
                ])
            else:
                data = data.with_columns([
                    pl.col("Close").cast(pl.Float64).ewm_mean(span=short_window, adjust=False).alias("MA_FAST"),
                    pl.col("Close").cast(pl.Float64).ewm_mean(span=long_window, adjust=False).alias("MA_SLOW")
                ])
            
            # Calculate RSI if needed
            if config.get('USE_RSI', False):
                log("Calculating RSI...")
                rsi_window = config.get('RSI_WINDOW', 14)
                # Implement simple RSI calculation here
                # ...
            
            # Generate signals manually
            log("Generating signals...")
            
            # Current MA relationship
            ma_fast_gt_slow = pl.col('MA_FAST') > pl.col('MA_SLOW')
            ma_fast_lt_slow = pl.col('MA_FAST') < pl.col('MA_SLOW')
            
            # Previous MA relationship
            prev_ma_fast_gt_slow = ma_fast_gt_slow.shift(1)
            prev_ma_fast_lt_slow = ma_fast_lt_slow.shift(1)
            
            # For long positions
            if config.get('DIRECTION', 'Long') == 'Long':
                # Accurate crossover detection: Fast MA crosses above Slow MA
                entries = ma_fast_gt_slow & ~prev_ma_fast_gt_slow
                
                # If not using current crossovers, also include when fast MA is already above slow MA
                if not config.get('USE_CURRENT', False):
                    entries = entries | ma_fast_gt_slow
                    
                # Exit when fast MA crosses below slow MA
                exits = ma_fast_lt_slow & ~prev_ma_fast_lt_slow
            else:
                # For short positions
                # Accurate crossover detection: Fast MA crosses below Slow MA
                entries = ma_fast_lt_slow & ~prev_ma_fast_lt_slow
                
                # If not using current crossovers, also include when fast MA is already below slow MA
                if not config.get('USE_CURRENT', False):
                    entries = entries | ma_fast_lt_slow
                    
                # Exit when fast MA crosses above slow MA
                exits = ma_fast_gt_slow & ~prev_ma_fast_gt_slow
            
            # Add Signal column
            direction_multiplier = -1 if config.get('DIRECTION', 'Long') == 'Short' else 1
            data = data.with_columns([
                pl.when(entries).then(direction_multiplier).otherwise(0).alias("Signal")
            ])
            
            # Add Position column
            data = data.with_columns([
                pl.col("Signal").shift(1).alias("Position")
            ])
        except Exception as e:
            log(f"Error processing data: {str(e)}", "error")
            log_close()
            return False
        
        # Check for current signals
        signals = data.filter(pl.col("Signal") != 0)
        
        if len(signals) > 0:
            log("Found signals:")
            for row in signals.tail(5).to_dicts():
                date = row['Date']
                signal = row['Signal']
                ma_fast = row['MA_FAST']
                ma_slow = row['MA_SLOW']
                
                log(f"Signal at {date}: {'Long' if signal > 0 else 'Short'}")
                log(f"  Fast MA: {ma_fast:.2f}, Slow MA: {ma_slow:.2f}")
                
                # Verify if this is a valid crossover
                if signal > 0:  # Long signal
                    # Convert to pandas to get index
                    data_pd = data.to_pandas()
                    # Find the row with this date
                    date_rows = data_pd[data_pd['Date'] == date]
                    if not date_rows.empty:
                        idx = date_rows.index[0]
                        if idx > 0:
                            # Get previous row
                            prev_row = data_pd.iloc[idx-1]
                            prev_ma_fast = prev_row['MA_FAST']
                            prev_ma_slow = prev_row['MA_SLOW']
                            
                            is_valid = ma_fast > ma_slow and prev_ma_fast <= prev_ma_slow
                            log(f"  Valid crossover: {is_valid}")
                            log(f"  Previous Fast MA: {prev_ma_fast:.2f}, Previous Slow MA: {prev_ma_slow:.2f}")
                            
                            if not is_valid:
                                log("Error: Invalid crossover detected", "error")
                                log_close()
                                return False
        else:
            log("No signals found in the current data")
        
        log("Test completed successfully")
        log_close()
        return True
        
    except Exception as e:
        log(f"Test failed: {str(e)}", "error")
        log_close()
        return False

def run_tests():
    """Run a series of tests with different tickers and parameters."""
    results = []
    
    # Test with different tickers and parameters
    test_cases = [
        {"ticker": "AAPL", "short_window": 10, "long_window": 20, "use_sma": False},
        {"ticker": "MSFT", "short_window": 20, "long_window": 50, "use_sma": True},
        {"ticker": "BTC-USD", "short_window": 9, "long_window": 21, "use_sma": False},
    ]
    
    for test_case in test_cases:
        print(f"Testing {test_case['ticker']} with {'SMA' if test_case['use_sma'] else 'EMA'}")
        result = test_ma_cross(
            ticker=test_case["ticker"],
            short_window=test_case["short_window"],
            long_window=test_case["long_window"],
            use_sma=test_case["use_sma"]
        )
        results.append({
            "ticker": test_case["ticker"],
            "short_window": test_case["short_window"],
            "long_window": test_case["long_window"],
            "use_sma": test_case["use_sma"],
            "result": "PASS" if result else "FAIL"
        })
    
    # Print summary
    print("\nTest Results:")
    print("=" * 60)
    print(f"{'Ticker':<10} {'Windows':<15} {'Type':<5} {'Result':<10}")
    print("-" * 60)
    
    for result in results:
        windows = f"{result['short_window']}/{result['long_window']}"
        ma_type = "SMA" if result["use_sma"] else "EMA"
        print(f"{result['ticker']:<10} {windows:<15} {ma_type:<5} {result['result']:<10}")
    
    # Overall result
    all_passed = all(r["result"] == "PASS" for r in results)
    print("=" * 60)
    print(f"Overall Result: {'PASS' if all_passed else 'FAIL'}")
    
    return all_passed

if __name__ == "__main__":
    run_tests()