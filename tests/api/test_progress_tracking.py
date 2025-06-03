#!/usr/bin/env python3
"""
Test script for MA Cross API progress tracking
"""

import asyncio
import json
import time
from datetime import datetime

import httpx

API_BASE_URL = "http://127.0.0.1:8000"


async def test_async_with_progress():
    """Test async analysis with progress tracking via SSE."""
    print("\n=== Testing Async MA Cross Analysis with Progress Tracking ===")

    # Request payload
    payload = {
        "ticker": ["BTC-USD", "ETH-USD"],
        "windows": 8,
        "strategy_types": ["SMA", "EMA"],
        "async_execution": True,
    }

    async with httpx.AsyncClient() as client:
        # Submit async analysis
        print(f"\nSubmitting async analysis request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = await client.post(
            f"{API_BASE_URL}/api/ma-cross/analyze", json=payload
        )

        if response.status_code == 202:
            data = response.json()
            execution_id = data["execution_id"]
            print(f"\nAnalysis started with execution ID: {execution_id}")

            # Stream progress updates
            print("\nStreaming progress updates...")
            print("-" * 60)

            async with httpx.AsyncClient(timeout=httpx.Timeout(600.0)) as stream_client:
                async with stream_client.stream(
                    "GET", f"{API_BASE_URL}/api/ma-cross/stream/{execution_id}"
                ) as stream_response:
                    async for line in stream_response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                event_data = json.loads(line[6:])

                                # Display progress information
                                status = event_data.get("status", "unknown")
                                progress = event_data.get("progress", "")

                                # Check for detailed progress info
                                progress_details = event_data.get(
                                    "progress_details", {}
                                )
                                if progress_details:
                                    phase = progress_details.get("phase", "")
                                    current_step = progress_details.get(
                                        "current_step", 0
                                    )
                                    total_steps = progress_details.get("total_steps", 0)
                                    progress_pct = progress_details.get(
                                        "progress_percentage"
                                    )
                                    elapsed = progress_details.get("elapsed_time", 0)

                                    if progress_pct is not None:
                                        print(
                                            f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                                            f"Status: {status} | Phase: {phase} | "
                                            f"Progress: {progress} | "
                                            f"Steps: {current_step}/{total_steps} "
                                            f"({progress_pct:.1f}%) | "
                                            f"Elapsed: {elapsed:.1f}s",
                                            end="",
                                            flush=True,
                                        )
                                    else:
                                        print(
                                            f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                                            f"Status: {status} | Phase: {phase} | "
                                            f"Progress: {progress} | "
                                            f"Elapsed: {elapsed:.1f}s",
                                            end="",
                                            flush=True,
                                        )
                                else:
                                    print(
                                        f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                                        f"Status: {status} | Progress: {progress}",
                                        end="",
                                        flush=True,
                                    )

                                # Check if complete
                                if status in ["completed", "failed"]:
                                    print("\n" + "-" * 60)

                                    if status == "completed":
                                        print(f"\nAnalysis completed successfully!")

                                        # Show summary
                                        total_analyzed = event_data.get(
                                            "total_portfolios_analyzed", 0
                                        )
                                        total_filtered = event_data.get(
                                            "total_portfolios_filtered", 0
                                        )
                                        exec_time = event_data.get("execution_time", 0)

                                        print(
                                            f"Total portfolios analyzed: {total_analyzed}"
                                        )
                                        print(
                                            f"Total portfolios filtered: {total_filtered}"
                                        )
                                        print(f"Execution time: {exec_time:.2f}s")

                                        # Show some portfolio results
                                        results = event_data.get("results", [])
                                        if results:
                                            print(f"\nTop 3 portfolios:")
                                            for i, portfolio in enumerate(results[:3]):
                                                print(
                                                    f"{i+1}. {portfolio.get('ticker')} - "
                                                    f"{portfolio.get('strategy_type')} "
                                                    f"({portfolio.get('short_window')}/{portfolio.get('long_window')}) - "
                                                    f"Return: {portfolio.get('total_return', 0):.2f}%"
                                                )
                                    else:
                                        print(
                                            f"\nAnalysis failed: {event_data.get('error', 'Unknown error')}"
                                        )

                                    break

                            except json.JSONDecodeError:
                                print(f"\nFailed to parse event: {line}")
                            except Exception as e:
                                print(f"\nError processing event: {e}")
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)


async def test_sync_analysis():
    """Test synchronous analysis (no SSE progress, but faster for small requests)."""
    print("\n=== Testing Sync MA Cross Analysis ===")

    payload = {
        "ticker": "BTC-USD",
        "windows": 8,
        "strategy_types": ["SMA"],
        "async_execution": False,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        print(f"\nSubmitting sync analysis request...")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        start_time = time.time()
        response = await client.post(
            f"{API_BASE_URL}/api/ma-cross/analyze", json=payload
        )
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            print(f"\nAnalysis completed in {elapsed:.2f}s")
            print(
                f"Total portfolios analyzed: {data.get('total_portfolios_analyzed', 0)}"
            )
            print(
                f"Total portfolios filtered: {data.get('total_portfolios_filtered', 0)}"
            )

            # Show portfolio results
            portfolios = data.get("portfolios", [])
            if portfolios:
                print(f"\nPortfolio results:")
                for portfolio in portfolios:
                    print(
                        f"- {portfolio.get('ticker')} - "
                        f"{portfolio.get('strategy_type')} "
                        f"({portfolio.get('short_window')}/{portfolio.get('long_window')}) - "
                        f"Return: {portfolio.get('total_return', 0):.2f}%"
                    )
        else:
            print(f"\nError: {response.status_code}")
            print(response.text)


async def main():
    """Run all tests."""
    # Test sync first (quick)
    await test_sync_analysis()

    # Test async with progress tracking
    await test_async_with_progress()


if __name__ == "__main__":
    asyncio.run(main())
