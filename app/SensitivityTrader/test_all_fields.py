#!/usr/bin/env python3
"""
Test script to verify all field connections between SensitivityTrader UI and MA Cross API.

This script tests that all configuration fields are properly passed from the UI through
the API to the backend MA Cross analysis module.
"""

import requests
import json
from typing import Dict, Any, List, Union

API_URL = "http://127.0.0.1:8000/api/ma-cross/analyze"

def test_field_connection(field_name: str, test_value: Any, expected_type: type) -> Dict[str, Any]:
    """Test a single field connection."""
    # Build a minimal valid request with the test field
    request_data = {
        "TICKER": "BTC-USD",
        "WINDOWS": 89,
        "DIRECTION": "Long",
        "STRATEGY_TYPES": ["SMA", "EMA"],
        "USE_HOURLY": False,
        "USE_YEARS": False,
        "YEARS": 15,
        "USE_SYNTHETIC": False,
        "USE_CURRENT": True,
        "USE_SCANNER": False,
        "REFRESH": True,
        "MINIMUMS": {
            "WIN_RATE": 0.44,
            "TRADES": 54,
            "EXPECTANCY_PER_TRADE": 1,
            "PROFIT_FACTOR": 1,
            "SORTINO_RATIO": 0.4,
        },
        "SORT_BY": "Score",
        "SORT_ASC": False,
        "USE_GBM": False,
        "async_execution": False
    }
    
    # Override with test value
    if field_name == "MINIMUMS":
        # Special handling for nested minimums
        request_data["MINIMUMS"] = test_value
    else:
        request_data[field_name] = test_value
    
    # Special handling for synthetic pairs
    if field_name == "USE_SYNTHETIC" and test_value:
        request_data["TICKER_2"] = "MSTR"
    
    try:
        # Make the API request
        response = requests.post(API_URL, json=request_data, timeout=10)
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            return {
                "field": field_name,
                "test_value": test_value,
                "status": "PASS",
                "message": "Field accepted by API",
                "response_status": result.get("status", "unknown")
            }
        else:
            return {
                "field": field_name,
                "test_value": test_value,
                "status": "FAIL",
                "message": f"HTTP {response.status_code}: {response.text[:200]}",
                "response_status": "error"
            }
    except Exception as e:
        return {
            "field": field_name,
            "test_value": test_value,
            "status": "ERROR",
            "message": str(e),
            "response_status": "error"
        }

def main():
    """Run all field connection tests."""
    print("Testing all field connections from SensitivityTrader to MA Cross API\n")
    print("=" * 80)
    
    # Define all fields to test
    test_cases = [
        # Field name, test value, expected type
        ("TICKER", "AAPL", str),
        ("TICKER", ["AAPL", "MSFT", "GOOG"], list),
        ("WINDOWS", 55, int),
        ("DIRECTION", "Short", str),
        ("STRATEGY_TYPES", ["EMA"], list),
        ("USE_HOURLY", True, bool),
        ("USE_YEARS", True, bool),
        ("YEARS", 10, int),
        ("USE_SYNTHETIC", True, bool),
        ("TICKER_2", "MSTR", str),
        ("USE_SCANNER", True, bool),
        ("REFRESH", False, bool),
        ("USE_CURRENT", False, bool),
        ("MINIMUMS", {
            "WIN_RATE": 0.5,
            "TRADES": 100,
            "EXPECTANCY_PER_TRADE": 2,
            "PROFIT_FACTOR": 1.5,
            "SORTINO_RATIO": 0.8,
        }, dict),
        ("SORT_BY", "Win Rate [%]", str),
        ("SORT_ASC", True, bool),
        ("USE_GBM", True, bool),
    ]
    
    results = []
    
    # Test each field
    for field_name, test_value, expected_type in test_cases:
        print(f"\nTesting {field_name} with value: {test_value}")
        result = test_field_connection(field_name, test_value, expected_type)
        results.append(result)
        
        if result["status"] == "PASS":
            print(f"✅ {field_name}: {result['message']}")
        elif result["status"] == "FAIL":
            print(f"❌ {field_name}: {result['message']}")
        else:
            print(f"⚠️  {field_name}: {result['message']}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    
    if failed > 0 or errors > 0:
        print("\nFailed/Error tests:")
        for result in results:
            if result["status"] in ["FAIL", "ERROR"]:
                print(f"  - {result['field']}: {result['message']}")
    
    # Test specific field combinations
    print("\n" + "=" * 80)
    print("TESTING FIELD COMBINATIONS")
    print("=" * 80)
    
    # Test synthetic pair configuration
    print("\nTesting synthetic pair configuration...")
    synthetic_request = {
        "TICKER": "BTC-USD",
        "USE_SYNTHETIC": True,
        "TICKER_2": "ETH-USD",
        "WINDOWS": 89,
        "DIRECTION": "Long",
        "STRATEGY_TYPES": ["SMA"],
        "async_execution": False
    }
    
    try:
        response = requests.post(API_URL, json=synthetic_request, timeout=10)
        if response.status_code == 200:
            print("✅ Synthetic pair configuration accepted")
        else:
            print(f"❌ Synthetic pair configuration failed: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Synthetic pair configuration error: {e}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    # Note: Make sure the API server is running at http://127.0.0.1:8000
    print("Note: This test requires the MA Cross API server to be running.")
    print("Start it with: python -m app.api.run\n")
    
    try:
        # Test if API is accessible
        test_response = requests.get("http://127.0.0.1:8000/api/health", timeout=5)
        if test_response.status_code == 200:
            print("✅ API server is running\n")
            main()
        else:
            print("❌ API server returned unexpected status")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server at http://127.0.0.1:8000")
        print("Please start the server with: python -m app.api.run")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")