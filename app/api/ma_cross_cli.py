#!/usr/bin/env python3
"""
MA Cross API CLI Client

Usage:
    python ma_cross_cli.py analyze --ticker AAPL MSFT --start 2023-01-01 --end 2023-12-31
    python ma_cross_cli.py analyze --ticker BTC-USD --async
    python ma_cross_cli.py status <execution_id>
    python ma_cross_cli.py stream <execution_id>
    python ma_cross_cli.py metrics
    python ma_cross_cli.py health
"""

import argparse
import json

import requests

BASE_URL = "http://127.0.0.1:8000"


def analyze(args):
    """Execute MA Cross analysis."""
    data = {
        "TICKER": args.ticker,
        "START_DATE": args.start,
        "END_DATE": args.end,
        "async_execution": args.async_exec,
    }

    # Add optional parameters
    if args.windows:
        data["WINDOWS"] = args.windows
    if args.direction:
        data["DIRECTION"] = args.direction
    if args.ma_types:
        data["STRATEGY_TYPES"] = args.ma_types
    if args.hourly:
        data["USE_HOURLY"] = args.hourly

    # Add minimum criteria if provided
    min_criteria = {}
    if args.min_trades:
        min_criteria["TRADES"] = args.min_trades
    if args.min_win_rate:
        min_criteria["WIN_RATE"] = args.min_win_rate
    if args.min_profit_factor:
        min_criteria["PROFIT_FACTOR"] = args.min_profit_factor
    if min_criteria:
        data["MIN_CRITERIA"] = min_criteria

    response = requests.post(f"{BASE_URL}/api/ma-cross/analyze", json=data, timeout=30)

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    elif response.status_code == 202:
        result = response.json()
        print("Async analysis started!")
        print(f"Task ID: {result['execution_id']}")
        print(f"Status URL: {result['status_url']}")
        print(f"Stream URL: {result['stream_url']}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def get_status(execution_id: str):
    """Check task status."""
    response = requests.get(
        f"{BASE_URL}/api/ma-cross/status/{execution_id}", timeout=10
    )

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def stream_progress(execution_id: str):
    """Stream task progress."""
    try:
        response = requests.get(
            f"{BASE_URL}/api/ma-cross/stream/{execution_id}", stream=True, timeout=60
        )

        for line in response.iter_lines():
            if line:
                decoded_line = line.decode("utf-8")
                if decoded_line.startswith("data: "):
                    data = json.loads(decoded_line[6:])
                    print(json.dumps(data, indent=2))
    except KeyboardInterrupt:
        print("\nStream interrupted")
    except Exception as e:
        print(f"Error: {e}")


def get_metrics():
    """Get service metrics."""
    response = requests.get(f"{BASE_URL}/api/ma-cross/metrics", timeout=10)

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def health_check():
    """Check service health."""
    response = requests.get(f"{BASE_URL}/api/ma-cross/health", timeout=10)

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"Error: {response.status_code}")
        print(response.text)


def main():
    parser = argparse.ArgumentParser(description="MA Cross API CLI Client")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run MA Cross analysis")
    analyze_parser.add_argument(
        "--ticker", nargs="+", required=True, help="Ticker symbol(s)"
    )
    analyze_parser.add_argument(
        "--start", default="2023-01-01", help="Start date (YYYY-MM-DD)"
    )
    analyze_parser.add_argument(
        "--end", default="2023-12-31", help="End date (YYYY-MM-DD)"
    )
    analyze_parser.add_argument(
        "--async", dest="async_exec", action="store_true", help="Run asynchronously"
    )
    analyze_parser.add_argument("--windows", type=int, help="Maximum window size")
    analyze_parser.add_argument(
        "--direction", choices=["Long", "Short"], help="Trading direction"
    )
    analyze_parser.add_argument(
        "--ma-types", nargs="+", choices=["SMA", "EMA"], help="MA types"
    )
    analyze_parser.add_argument("--hourly", action="store_true", help="Use hourly data")
    analyze_parser.add_argument("--min-trades", type=int, help="Minimum trades filter")
    analyze_parser.add_argument(
        "--min-win-rate", type=float, help="Minimum win rate filter"
    )
    analyze_parser.add_argument(
        "--min-profit-factor", type=float, help="Minimum profit factor filter"
    )

    # Status command
    status_parser = subparsers.add_parser("status", help="Check task status")
    status_parser.add_argument("execution_id", help="Execution ID to check")

    # Stream command
    stream_parser = subparsers.add_parser("stream", help="Stream task progress")
    stream_parser.add_argument("execution_id", help="Execution ID to stream")

    # Metrics command
    metrics_parser = subparsers.add_parser("metrics", help="Get service metrics")

    # Health command
    health_parser = subparsers.add_parser("health", help="Check service health")

    args = parser.parse_args()

    if args.command == "analyze":
        analyze(args)
    elif args.command == "status":
        get_status(args.execution_id)
    elif args.command == "stream":
        stream_progress(args.execution_id)
    elif args.command == "metrics":
        get_metrics()
    elif args.command == "health":
        health_check()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
