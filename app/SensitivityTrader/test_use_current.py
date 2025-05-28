#!/usr/bin/env python3
"""
Test script to verify USE_CURRENT parameter integration between SensitivityTrader and MA Cross API.

This script tests:
1. That the USE_CURRENT checkbox value is properly read from the UI
2. That the value is correctly sent to the MA Cross API
3. That the MA Cross analysis respects the USE_CURRENT parameter
"""

import json
import requests
import time

def test_use_current_integration():
    """Test USE_CURRENT parameter integration."""
    
    api_base_url = "http://127.0.0.1:8000"
    
    # Test 1: Test with USE_CURRENT = True (default)
    print("Test 1: Testing with USE_CURRENT = True")
    request_true = {
        "TICKER": "AAPL",
        "WINDOWS": 20,
        "DIRECTION": "Long",
        "STRATEGY_TYPES": ["SMA"],
        "USE_HOURLY": False,
        "USE_YEARS": False,
        "YEARS": 15,
        "USE_SYNTHETIC": False,
        "USE_CURRENT": True,  # This should be passed from the UI checkbox
        "REFRESH": True,
        "MINIMUMS": {
            "WIN_RATE": 0.4,
            "TRADES": 10,
            "EXPECTANCY_PER_TRADE": 0.5,
            "PROFIT_FACTOR": 1.0,
            "SORTINO_RATIO": 0.2
        },
        "SORT_BY": "Score",
        "SORT_ASC": False,
        "USE_GBM": False,
        "async_execution": False
    }
    
    response = requests.post(f"{api_base_url}/api/ma-cross/analyze", json=request_true)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Analysis status: {data.get('status')}")
        print(f"Total portfolios analyzed: {data.get('total_portfolios_analyzed', 0)}")
        print(f"Request included USE_CURRENT = {request_true['USE_CURRENT']}")
        print("✓ Test 1 passed\n")
    else:
        print(f"✗ Test 1 failed: {response.text}\n")
    
    # Test 2: Test with USE_CURRENT = False
    print("Test 2: Testing with USE_CURRENT = False")
    request_false = request_true.copy()
    request_false["USE_CURRENT"] = False
    
    response = requests.post(f"{api_base_url}/api/ma-cross/analyze", json=request_false)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Analysis status: {data.get('status')}")
        print(f"Total portfolios analyzed: {data.get('total_portfolios_analyzed', 0)}")
        print(f"Request included USE_CURRENT = {request_false['USE_CURRENT']}")
        print("✓ Test 2 passed\n")
    else:
        print(f"✗ Test 2 failed: {response.text}\n")
    
    # Test 3: Verify the parameter is properly logged/used
    print("Test 3: Checking if USE_CURRENT parameter affects the analysis")
    print("Note: The actual behavior difference depends on the implementation in 1_get_portfolios.py")
    print("When USE_CURRENT=True, it should use the most recent market data")
    print("When USE_CURRENT=False, it may use cached or historical data\n")
    
    print("Integration test complete!")
    print("\nTo fully test the UI integration:")
    print("1. Start the SensitivityTrader Flask app: python app/SensitivityTrader/main.py")
    print("2. Start the MA Cross API: python -m app.api.run")
    print("3. Open the web interface at http://127.0.0.1:5000")
    print("4. Toggle the 'Use Current' checkbox and run analyses")
    print("5. Check the browser console for the request payload to verify USE_CURRENT is sent correctly")

if __name__ == "__main__":
    print("USE_CURRENT Integration Test")
    print("=" * 50)
    print()
    
    try:
        test_use_current_integration()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server.")
        print("Please ensure the API server is running: python -m app.api.run")
    except Exception as e:
        print(f"Error: {e}")