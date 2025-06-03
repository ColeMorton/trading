#!/usr/bin/env python3
"""
Test script for MA Cross API integration.
Tests the full portfolio analysis functionality.
"""

import json
import time

import requests

# API base URL
BASE_URL = "http://127.0.0.1:8000"


def test_ma_cross_analysis():
    """Test synchronous MA Cross analysis with portfolio functionality."""

    print("Testing MA Cross Portfolio Analysis API...")
    print("-" * 50)

    # Test request with single ticker
    request_data = {
        "ticker": "BTC-USD",
        "windows": 8,  # Very small window for faster testing
        "strategy_types": ["SMA", "EMA"],
        "direction": "Long",
        "use_hourly": False,
        "refresh": False,  # Use cached data
        "minimums": {
            "trades": 5,  # Lower minimum for small window
            "win_rate": 0.3,
            "profit_factor": 0.8,
        },
    }

    print(f"Request data: {json.dumps(request_data, indent=2)}")
    print("\nSending request to API...")

    try:
        # Send POST request
        response = requests.post(
            f"{BASE_URL}/api/ma-cross/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        # Check response
        print(f"\nResponse status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\nResponse summary:")
            print(f"- Status: {result.get('status')}")
            print(f"- Request ID: {result.get('request_id')}")
            print(f"- Execution time: {result.get('execution_time', 0):.2f} seconds")
            print(
                f"- Total portfolios analyzed: {result.get('total_portfolios_analyzed', 0)}"
            )
            print(
                f"- Total portfolios filtered: {result.get('total_portfolios_filtered', 0)}"
            )

            # Show portfolio exports
            exports = result.get("portfolio_exports", {})
            if exports:
                print("\nExported files:")
                for export_type, files in exports.items():
                    print(f"\n  {export_type}:")
                    for file in files[:3]:  # Show first 3 files
                        print(f"    - {file}")
                    if len(files) > 3:
                        print(f"    ... and {len(files) - 3} more")

            # Show sample portfolio results
            portfolios = result.get("portfolios", [])
            if portfolios:
                print("\nSample portfolio results (showing first 3):")
                for i, portfolio in enumerate(portfolios[:3]):
                    print(f"\n  Portfolio {i+1}:")
                    print(f"    - Ticker: {portfolio.get('ticker')}")
                    print(f"    - Strategy: {portfolio.get('strategy_type')}")
                    print(
                        f"    - Windows: {portfolio.get('short_window')}/{portfolio.get('long_window')}"
                    )
                    print(
                        f"    - Total Return: {portfolio.get('total_return', 0):.2f}%"
                    )
                    print(f"    - Sharpe Ratio: {portfolio.get('sharpe_ratio', 0):.2f}")
                    print(f"    - Win Rate: {portfolio.get('win_rate', 0)*100:.1f}%")
                    print(f"    - Score: {portfolio.get('score', 0):.2f}")
        else:
            print(f"\nError response: {response.text}")

    except Exception as e:
        print(f"\nError during test: {str(e)}")
        print(f"Error type: {type(e).__name__}")


def test_async_ma_cross_analysis():
    """Test asynchronous MA Cross analysis."""

    print("\n\nTesting Async MA Cross Analysis...")
    print("-" * 50)

    # Test request
    request_data = {
        "ticker": ["BTC-USD", "ETH-USD"],
        "windows": 8,  # Small window for faster testing
        "strategy_types": ["SMA"],
        "async_execution": True,
        "refresh": False,  # Use cached data
    }

    print(f"Request data: {json.dumps(request_data, indent=2)}")

    try:
        # Start async analysis
        response = requests.post(
            f"{BASE_URL}/api/ma-cross/analyze",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 202:  # Accepted
            result = response.json()
            execution_id = result.get("execution_id")
            print("\nAsync analysis started:")
            print(f"- Execution ID: {execution_id}")
            print(f"- Status: {result.get('status')}")

            # Poll for status
            print("\nPolling for results...")
            for i in range(30):  # Poll for up to 30 seconds
                time.sleep(1)
                status_response = requests.get(
                    f"{BASE_URL}/api/ma-cross/status/{execution_id}"
                )

                if status_response.status_code == 200:
                    status = status_response.json()
                    print(
                        f"\r[{i+1}s] Status: {status.get('status')} - {status.get('progress')}",
                        end="",
                    )

                    if status.get("status") == "completed":
                        print("\n\nAnalysis completed!")
                        print(
                            f"- Total portfolios: {status.get('total_portfolios_analyzed', 0)}"
                        )
                        print(
                            f"- Filtered portfolios: {status.get('total_portfolios_filtered', 0)}"
                        )
                        break
                    elif status.get("status") == "failed":
                        print(f"\n\nAnalysis failed: {status.get('error')}")
                        break
        else:
            print(f"\nError starting async analysis: {response.text}")

    except Exception as e:
        print(f"\nError during async test: {str(e)}")


if __name__ == "__main__":
    # Check if API is running
    try:
        health_response = requests.get(f"{BASE_URL}/health")
        if health_response.status_code != 200:
            print(
                "API server is not running. Please start it with: python -m app.api.run"
            )
            exit(1)
    except requests.ConnectionError:
        print(
            "Cannot connect to API server. Please start it with: python -m app.api.run"
        )
        exit(1)

    # Run tests
    test_ma_cross_analysis()
    test_async_ma_cross_analysis()

    print("\n\nAll tests completed!")
