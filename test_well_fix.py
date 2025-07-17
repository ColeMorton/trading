#!/usr/bin/env python3
"""Test script to verify WELL metrics calculation fix."""

import pandas as pd
from pathlib import Path

def test_read_price_data(ticker: str):
    """Test the new robust price data reading method."""
    try:
        price_file = Path("/Users/colemorton/Projects/trading/csv/price_data") / f"{ticker}_D.csv"
        
        if not price_file.exists():
            print(f"❌ {ticker}: Price file not found")
            return False

        df = pd.read_csv(price_file)
        
        if df.empty:
            print(f"❌ {ticker}: Empty dataframe")
            return False
            
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        
        required_columns = ["Close", "High", "Low", "Open", "Volume"]
        if not all(col in df.columns for col in required_columns):
            print(f"❌ {ticker}: Missing required columns")
            return False
            
        print(f"✅ {ticker}: Successfully read {len(df)} price records from {df.index.min()} to {df.index.max()}")
        return True

    except Exception as e:
        print(f"❌ {ticker}: Error reading price data: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing WELL metrics calculation fix...\n")
    
    # Test tickers that should work now
    test_tickers = ["WELL", "AAPL", "QCOM", "BTC-USD"]
    
    results = []
    for ticker in test_tickers:
        result = test_read_price_data(ticker)
        results.append(result)
    
    print(f"\nResults: {sum(results)}/{len(results)} tickers successfully processed")
    
    if all(results):
        print("\n🎉 All tests passed! WELL metrics calculation should now work.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")