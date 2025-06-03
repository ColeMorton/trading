#!/usr/bin/env python3
"""Quick test for debugging."""
import json

import requests

BASE_URL = "http://127.0.0.1:8000"

# Simple test with minimal parameters
request_data = {
    "ticker": "BTC-USD",
    "windows": 8,  # Very small window for quick test
    "strategy_types": ["EMA"],  # Use EMA to match what's being returned
    "refresh": False,  # Use cached data if available
}

print(f"Request: {json.dumps(request_data, indent=2)}")

try:
    response = requests.post(
        f"{BASE_URL}/api/ma-cross/analyze", json=request_data, timeout=30
    )

    print(f"\nStatus: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Portfolios analyzed: {result.get('total_portfolios_analyzed', 0)}")
        print(f"Execution time: {result.get('execution_time', 0):.2f}s")

        # Show first portfolio if available
        portfolios = result.get("portfolios", [])
        if portfolios:
            p = portfolios[0]
            print("\nFirst portfolio:")
            print(f"  Ticker: {p.get('ticker')}")
            print(f"  Windows: {p.get('short_window')}/{p.get('long_window')}")
            print(f"  Score: {p.get('score', 0):.2f}")
    else:
        print(f"Error: {response.text[:200]}")

except Exception as e:
    print(f"Error: {str(e)}")
