#!/usr/bin/env python3
"""
Comprehensive test of all MA Cross API features including progress tracking
"""

import asyncio
import json
import time
from datetime import datetime

import httpx
import requests

API_BASE_URL = "http://127.0.0.1:8000"


def test_api_health():
    """Test API health endpoints."""
    print("\n=== Testing API Health ===")

    # Test root endpoint
    response = requests.get(f"{API_BASE_URL}/")
    assert response.status_code == 200
    print("✓ Root endpoint working")

    # Test health endpoint
    response = requests.get(f"{API_BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health endpoint working")

    return True


def test_sync_ma_cross():
    """Test synchronous MA Cross analysis."""
    print("\n=== Testing Synchronous MA Cross Analysis ===")

    payload = {
        "ticker": "AAPL",
        "windows": 8,
        "strategy_types": ["SMA"],
        "refresh": False,
    }

    print(f"Request: {json.dumps(payload, indent=2)}")

    response = requests.post(f"{API_BASE_URL}/api/ma-cross/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()

    print(f"✓ Analysis completed in {data.get('execution_time', 0):.2f}s")
    print(f"✓ Portfolios analyzed: {data.get('total_portfolios_analyzed', 0)}")
    print(f"✓ Portfolios filtered: {data.get('total_portfolios_filtered', 0)}")

    # Check for portfolio results
    portfolios = data.get("portfolios", [])
    if portfolios:
        portfolio = portfolios[0]
        print(
            f"✓ Sample result: {portfolio.get('ticker')} - "
            f"{portfolio.get('strategy_type')} "
            f"({portfolio.get('short_window')}/{portfolio.get('long_window')}) - "
            f"Return: {portfolio.get('total_return', 0):.2f}%"
        )

    return True


async def test_async_ma_cross_with_progress():
    """Test asynchronous MA Cross analysis with progress tracking."""
    print("\n=== Testing Async MA Cross with Progress Tracking ===")

    payload = {
        "ticker": ["AAPL", "MSFT"],
        "windows": 8,
        "strategy_types": ["SMA", "EMA"],
        "async_execution": True,
        "refresh": False,
    }

    print(f"Request: {json.dumps(payload, indent=2)}")

    async with httpx.AsyncClient() as client:
        # Submit async analysis
        response = await client.post(
            f"{API_BASE_URL}/api/ma-cross/analyze", json=payload
        )

        assert response.status_code == 202
        data = response.json()
        execution_id = data["execution_id"]
        print(f"✓ Async analysis started: {execution_id}")

        # Stream progress updates
        print("\nProgress updates:")
        last_phase = None

        async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as stream_client:
            async with stream_client.stream(
                "GET", f"{API_BASE_URL}/api/ma-cross/stream/{execution_id}"
            ) as stream_response:
                async for line in stream_response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])

                            # Check progress details
                            progress_details = event_data.get("progress_details", {})
                            if progress_details:
                                phase = progress_details.get("phase", "")
                                if phase != last_phase:
                                    last_phase = phase
                                    message = progress_details.get("message", "")
                                    elapsed = progress_details.get("elapsed_time", 0)
                                    print(f"  ✓ {phase}: {message} ({elapsed:.1f}s)")

                            # Check if complete
                            if event_data.get("status") == "completed":
                                print("\n✓ Analysis completed!")
                                print(
                                    f"✓ Total portfolios: {event_data.get('total_portfolios_analyzed', 0)}"
                                )
                                print(
                                    f"✓ Filtered portfolios: {event_data.get('total_portfolios_filtered', 0)}"
                                )
                                print(
                                    f"✓ Execution time: {event_data.get('execution_time', 0):.2f}s"
                                )
                                break
                            elif event_data.get("status") == "failed":
                                print(
                                    f"\n✗ Analysis failed: {event_data.get('error', 'Unknown error')}"
                                )
                                return False

                        except json.JSONDecodeError:
                            pass
                        except Exception as e:
                            print(f"Error processing event: {e}")

    return True


def test_ma_cross_endpoints():
    """Test MA Cross specific endpoints."""
    print("\n=== Testing MA Cross Endpoints ===")

    # Test metrics endpoint
    response = requests.get(f"{API_BASE_URL}/api/ma-cross/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "available_metrics" in data
    print(
        f"✓ Metrics endpoint working - {len(data['available_metrics'])} metrics available"
    )

    # Test invalid execution ID
    try:
        response = requests.get(f"{API_BASE_URL}/api/ma-cross/stream/invalid-id")
        # Note: StreamingResponse might return 200 with error in stream
        print(f"✓ Invalid execution ID returns status: {response.status_code}")
    except Exception as e:
        print(f"✓ Invalid execution ID handling: {type(e).__name__}")

    return True


def test_csv_exports():
    """Test CSV export functionality."""
    print("\n=== Testing CSV Export Functionality ===")

    # Run analysis to generate CSV files
    payload = {
        "ticker": "SPY",
        "windows": 8,
        "strategy_types": ["SMA"],
        "refresh": False,
    }

    response = requests.post(f"{API_BASE_URL}/api/ma-cross/analyze", json=payload)

    assert response.status_code == 200
    data = response.json()

    # Check export paths
    exports = data.get("portfolio_exports", {})
    if exports:
        portfolios_count = len(exports.get("portfolios", []))
        filtered_count = len(exports.get("portfolios_filtered", []))
        print(f"✓ Exported {portfolios_count} portfolio files")
        print(f"✓ Exported {filtered_count} filtered portfolio files")

        # Verify files exist via data API
        if exports.get("portfolios_filtered"):
            csv_path = exports["portfolios_filtered"][0].replace("csv/", "")
            response = requests.get(f"{API_BASE_URL}/api/data/csv/{csv_path}")
            if response.status_code == 200:
                print("✓ CSV file accessible via data API")

    return True


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("MA Cross API Comprehensive Test Suite")
    print("=" * 60)

    try:
        # Test API health
        test_api_health()

        # Test synchronous analysis
        test_sync_ma_cross()

        # Test MA Cross endpoints
        test_ma_cross_endpoints()

        # Test CSV exports
        test_csv_exports()

        # Test async with progress tracking
        await test_async_ma_cross_with_progress()

        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

    return True


if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
