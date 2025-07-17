#!/usr/bin/env python3
"""Test script to verify improved error handling for missing price data files."""

import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from contexts.portfolio.services.trade_history_service import TradeHistoryService

def test_error_handling():
    """Test the improved error handling with specific scenarios."""
    
    print("Testing improved error handling for missing price data files...\n")
    
    # Initialize service
    service = TradeHistoryService()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Missing file",
            "ticker": "NONEXISTENT",
            "expected_error": "Price data file not found"
        },
        {
            "name": "Existing file (should work)",
            "ticker": "AAPL",
            "expected_error": None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing {test_case['name']} - Ticker: {test_case['ticker']}")
        
        try:
            df, error_msg = service._read_price_data(test_case['ticker'])
            
            if df is not None:
                print(f"   ✅ Success: Read {len(df)} price records")
                print(f"   📊 Data range: {df.index.min()} to {df.index.max()}")
            else:
                print(f"   ❌ Error: {error_msg}")
                
                if test_case['expected_error']:
                    if test_case['expected_error'] in error_msg:
                        print(f"   ✅ Expected error message format detected")
                    else:
                        print(f"   ⚠️  Unexpected error format")
                        
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
        
        print()
    
    print("Testing complete!\n")
    print("Next: Run 'python -m app.cli trade-history update --portfolio live_signals --verbose' to see improved error messages in action")

if __name__ == "__main__":
    test_error_handling()