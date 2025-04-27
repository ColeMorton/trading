#!/usr/bin/env python3
"""
Test Script for Hardcoded Strategy Configuration Generator

This script demonstrates how to use the generate_hardcoded_config.py script
with different CSV files and ticker filters.
"""

import os
import subprocess
import sys

def run_generator(csv_path, pine_script_path=None, ticker_filter=None):
    """
    Run the hardcoded strategy configuration generator with the specified parameters.
    
    Args:
        csv_path: Path to the CSV file
        pine_script_path: Optional path to update an existing Pine script
        ticker_filter: Optional ticker filter
    """
    cmd = ["python", "tradingview/generate_hardcoded_config.py", csv_path]
    if pine_script_path:
        cmd.append(pine_script_path)
    if ticker_filter:
        cmd.append(ticker_filter)
    
    print(f"\n{'='*80}")
    print(f"Running hardcoded generator with:")
    print(f"  CSV: {csv_path}")
    if pine_script_path:
        print(f"  Pine script: {pine_script_path}")
    if ticker_filter:
        print(f"  Ticker: {ticker_filter}")
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Generator executed successfully!")
            print(result.stdout)
        else:
            print("Error executing generator:")
            print(result.stderr)
    except Exception as e:
        print(f"Exception: {e}")

def main():
    """Main function to run tests."""
    # Check if the generator script exists
    if not os.path.exists("tradingview/generate_hardcoded_config.py"):
        print("Error: generate_hardcoded_config.py not found in the tradingview directory.")
        sys.exit(1)
    
    # Test 1: Generate a new Pine script from CSV
    run_generator("csv/strategies/BTC_d_20250427.csv")
    
    # Test 2: Update an existing Pine script (create a temporary copy first)
    if os.path.exists("tradingview/strategy_breadth_refactored.pine"):
        temp_pine_path = "tradingview/strategy_breadth_refactored_test.pine"
        with open("tradingview/strategy_breadth_refactored.pine", 'r') as f_in, open(temp_pine_path, 'w') as f_out:
            f_out.write(f_in.read())
        run_generator("csv/strategies/BTC_d_20250427.csv", temp_pine_path)
    
    # Test 3: Filter for BTC-USD with proper output filename
    run_generator("csv/strategies/BTC_d_20250427.csv", "tradingview/strategy_breadth_BTC-USD.pine", "BTC-USD")
    
    # Test 4: Try with a different CSV file if available
    if os.path.exists("csv/strategies/DAILY.csv"):
        run_generator("csv/strategies/DAILY.csv")
    
    # Test 5: Try with a multi-asset CSV file if available
    multi_asset_files = [
        "csv/strategies/MULTI_ASSET.csv",
        "csv/strategies/ALL_ASSETS.csv",
        "csv/strategies/crypto_d_20250427.csv"
    ]
    
    for file_path in multi_asset_files:
        if os.path.exists(file_path):
            run_generator(file_path)
            # Also test with a specific ticker filter
            run_generator(file_path, "tradingview/strategy_breadth_ETH-USD.pine", "ETH-USD")
            break
    
    print("\nTests completed!")
    print("To use the generator with your own CSV file, run:")
    print("python tradingview/generate_hardcoded_config.py path/to/your/csv/file.csv [pine_script_path] [ticker_filter]")

if __name__ == "__main__":
    main()