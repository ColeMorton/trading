#!/usr/bin/env python3
"""
Test Script for Strategy Configuration Generator

This script demonstrates how to use the generate_strategy_config.py script
with different CSV files and ticker filters.
"""

import os
import subprocess
import sys

def run_generator(csv_path, ticker_filter=None):
    """
    Run the strategy configuration generator with the specified parameters.
    
    Args:
        csv_path: Path to the CSV file
        ticker_filter: Optional ticker filter
    """
    cmd = ["python", "tradingview/generate_strategy_config.py", csv_path]
    if ticker_filter:
        cmd.append(ticker_filter)
    
    print(f"\n{'='*80}")
    print(f"Running generator with CSV: {csv_path}" + (f", Ticker: {ticker_filter}" if ticker_filter else ""))
    print(f"{'='*80}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Generator executed successfully!")
            print(f"Output file: {os.path.basename(result.stdout.strip().split('Configuration saved to ')[-1].split('\n')[0])}")
            
            # Extract and print strategy counts
            for line in result.stdout.strip().split('\n'):
                if "Total strategies:" in line or "Strategies for" in line:
                    print(line.strip())
        else:
            print("Error executing generator:")
            print(result.stderr)
    except Exception as e:
        print(f"Exception: {e}")

def main():
    """Main function to run tests."""
    # Check if the generator script exists
    if not os.path.exists("tradingview/generate_strategy_config.py"):
        print("Error: generate_strategy_config.py not found in the tradingview directory.")
        sys.exit(1)
    
    # Test 1: Basic test with BTC_d_20250427.csv
    run_generator("csv/strategies/BTC_d_20250427.csv")
    
    # Test 2: Filter for BTC-USD
    run_generator("csv/strategies/BTC_d_20250427.csv", "BTC-USD")
    
    # Test 3: Try with a different CSV file if available
    if os.path.exists("csv/strategies/DAILY.csv"):
        run_generator("csv/strategies/DAILY.csv")
    
    # Test 4: Try with a multi-asset CSV file if available
    multi_asset_files = [
        "csv/strategies/MULTI_ASSET.csv",
        "csv/strategies/ALL_ASSETS.csv",
        "csv/strategies/CRYPTO_ASSETS.csv"
    ]
    
    for file_path in multi_asset_files:
        if os.path.exists(file_path):
            run_generator(file_path)
            # Also test with a specific ticker filter
            run_generator(file_path, "ETH-USD")
            break
    
    print("\nTests completed!")
    print("To use the generator with your own CSV file, run:")
    print("python tradingview/generate_strategy_config.py path/to/your/csv/file.csv [ticker_filter]")

if __name__ == "__main__":
    main()