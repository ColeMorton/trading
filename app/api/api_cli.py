#!/usr/bin/env python3
"""
Trading API CLI Client

A comprehensive CLI for interacting with all Trading API endpoints.

Usage:
    # MA Cross Analysis
    python api_cli.py ma-cross analyze --ticker AAPL MSFT --start 2023-01-01 --end 2023-12-31
    python api_cli.py ma-cross status <execution_id>
    python api_cli.py ma-cross stream <execution_id>
    python api_cli.py ma-cross metrics
    python api_cli.py ma-cross health

    # Script Execution
    python api_cli.py scripts list
    python api_cli.py scripts execute app/ma_cross/1_get_portfolios.py --params TICKER=AAPL
    python api_cli.py scripts status <execution_id>
    python api_cli.py scripts stream <execution_id>

    # Data Access
    python api_cli.py data list csv/strategies
    python api_cli.py data csv strategies/DAILY.csv
    python api_cli.py data json concurrency/BTC_d.json

    # General
    python api_cli.py health
"""

import argparse
import json
import sys
from typing import Any, Dict, Optional

import requests


class TradingAPIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        try:
            if response.status_code in [200, 201, 202]:
                return response.json()
            else:
                print(f"Error: {response.status_code}")
                try:
                    error_data = response.json()
                    print(json.dumps(error_data, indent=2))
                except (json.JSONDecodeError, ValueError):
                    print(response.text)
                sys.exit(1)
        except Exception as e:
            print(f"Request failed: {e}")
            sys.exit(1)

    # MA Cross Methods
    def ma_cross_analyze(self, args):
        """Execute MA Cross analysis."""
        data = {
            "TICKER": args.ticker,
            "START_DATE": args.start,
            "END_DATE": args.end,
            "async_execution": args.async_exec,
        }

        # Add optional parameters
        optional_params = [
            ("windows", "WINDOWS"),
            ("direction", "DIRECTION"),
            ("ma_types", "STRATEGY_TYPES"),
            ("hourly", "USE_HOURLY"),
        ]

        for arg_name, api_name in optional_params:
            value = getattr(args, arg_name, None)
            if value is not None:
                data[api_name] = value

        # Add minimum criteria
        min_criteria = {}
        criteria_params = [
            ("min_trades", "TRADES"),
            ("min_win_rate", "WIN_RATE"),
            ("min_profit_factor", "PROFIT_FACTOR"),
            ("min_score", "SCORE"),
            ("min_sortino", "SORTINO_RATIO"),
            ("min_beats_bnh", "BEATS_BNH"),
        ]

        for arg_name, api_name in criteria_params:
            value = getattr(args, arg_name, None)
            if value is not None:
                min_criteria[api_name] = value

        if min_criteria:
            data["MIN_CRITERIA"] = min_criteria

        response = self.session.post(f"{self.base_url}/api/ma-cross/analyze", json=data)
        result = self._handle_response(response)

        if response.status_code == 202:
            print("🚀 Async analysis started!")
            print(f"Task ID: {result['execution_id']}")
            print(
                f"\nCheck status: python api_cli.py ma-cross status {result['execution_id']}"
            )
            print(
                f"Stream progress: python api_cli.py ma-cross stream {result['execution_id']}"
            )
        else:
            self._print_analysis_results(result)

    def _print_analysis_results(self, result: Dict[str, Any]):
        """Pretty print analysis results."""
        print("\n📊 MA Cross Analysis Results")
        print(f"{'='*60}")
        print(f"Status: {result['status']}")
        print(f"Tickers: {result['ticker']}")
        print(f"Portfolios analyzed: {result['total_portfolios']}")
        print(f"Portfolios after filtering: {result['filtered_portfolios']}")
        print(f"Execution time: {result['execution_time']:.2f}s")

        if result["portfolios"]:
            print("\n📈 Top Portfolios:")
            print(f"{'='*60}")
            for i, portfolio in enumerate(result["portfolios"][:5]):
                print(
                    f"\n{i+1}. {portfolio['ticker']} - {portfolio['strategy_type']} ({portfolio['short_window']}/{portfolio['long_window']})"
                )
                print(f"   Total Return: {portfolio['total_return']:.2%}")
                print(f"   Sharpe Ratio: {portfolio['sharpe_ratio']:.2f}")
                print(f"   Win Rate: {portfolio['win_rate']:.2%}")
                print(f"   Max Drawdown: {portfolio['max_drawdown']:.2%}")
                print(f"   Score: {portfolio['score']:.2f}")

    def ma_cross_status(self, execution_id: str):
        """Check MA Cross task status."""
        response = self.session.get(
            f"{self.base_url}/api/ma-cross/status/{execution_id}"
        )
        result = self._handle_response(response)

        print(f"\n📊 Task Status: {result['status']}")
        print(f"Progress: {result['progress']}%")
        if result.get("message"):
            print(f"Message: {result['message']}")

        if result["status"] == "completed" and result.get("result"):
            self._print_analysis_results(result["result"])
        elif result["status"] == "failed" and result.get("error"):
            print(f"❌ Error: {result['error']}")

    def ma_cross_stream(self, execution_id: str):
        """Stream MA Cross analysis progress."""
        print(f"📡 Streaming progress for execution {execution_id}...")
        print("Press Ctrl+C to stop\n")

        try:
            response = self.session.get(
                f"{self.base_url}/api/ma-cross/stream/{execution_id}", stream=True
            )

            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode("utf-8")
                    if decoded_line.startswith("data: "):
                        data = json.loads(decoded_line[6:])
                        if "progress" in data:
                            print(f"[{data['progress']:3d}%] {data.get('message', '')}")
                        if "result" in data:
                            print("\n✅ Analysis complete!")
                            self._print_analysis_results(data["result"])
                            break
        except KeyboardInterrupt:
            print("\n\nStream interrupted")

    def ma_cross_metrics(self):
        """Get MA Cross service metrics."""
        response = self.session.get(f"{self.base_url}/api/ma-cross/metrics")
        result = self._handle_response(response)

        print("\n📊 MA Cross Service Metrics")
        print(f"{'='*40}")
        print(f"Total Requests: {result['requests_total']}")
        print(
            f"Success Rate: {result['requests_success']/result['requests_total']*100:.1f}%"
        )
        print(f"Avg Response Time: {result['avg_response_time']:.2f}s")
        print(f"Cache Hit Rate: {result['cache_hit_rate']:.1%}")
        print(f"Active Tasks: {result['active_tasks']}")
        print(f"Completed Tasks: {result['completed_tasks']}")
        print(f"Failed Tasks: {result['failed_tasks']}")

    def ma_cross_health(self):
        """Check MA Cross service health."""
        response = self.session.get(f"{self.base_url}/api/ma-cross/health")
        result = self._handle_response(response)

        status_emoji = "✅" if result["status"] == "healthy" else "❌"
        print(f"\n{status_emoji} MA Cross Service Health: {result['status']}")
        print(f"Version: {result['version']}")
        print("Dependencies:")
        for dep, status in result["dependencies"].items():
            emoji = "✅" if status == "healthy" else "❌"
            print(f"  {emoji} {dep}: {status}")

    # Script Methods
    def scripts_list(self):
        """List available scripts."""
        response = self.session.get(f"{self.base_url}/api/scripts/list")
        result = self._handle_response(response)

        print(f"\n📜 Available Scripts ({len(result['scripts'])})")
        print(f"{'='*60}")
        for script in result["scripts"]:
            print(f"\n{script['path']}")
            if script.get("description"):
                print(f"  {script['description']}")
            if script.get("parameters"):
                print(f"  Parameters: {', '.join(script['parameters'].keys())}")

    def scripts_execute(
        self, script_path: str, params: Dict[str, str], async_exec: bool
    ):
        """Execute a script."""
        data = {
            "script_path": script_path,
            "parameters": params,
            "async_execution": async_exec,
        }

        response = self.session.post(f"{self.base_url}/api/scripts/execute", json=data)
        result = self._handle_response(response)

        if async_exec:
            print("🚀 Script execution started!")
            print(f"Execution ID: {result['execution_id']}")
            print(
                f"\nCheck status: python api_cli.py scripts status {result['execution_id']}"
            )
            print(
                f"Stream output: python api_cli.py scripts stream {result['execution_id']}"
            )
        else:
            print(f"✅ Script completed in {result['execution_time']:.2f}s")
            print(f"\nOutput:\n{result['output']}")
            if result.get("error"):
                print(f"\n❌ Error:\n{result['error']}")

    # Data Methods
    def data_list(self, directory: Optional[str] = None):
        """List files in a directory."""
        endpoint = f"{self.base_url}/api/data/list"
        if directory:
            endpoint = f"{endpoint}/{directory}"

        response = self.session.get(endpoint)
        result = self._handle_response(response)

        print(f"\n📁 Directory: {result['directory']}")
        print(f"Files: {len(result['files'])}")
        print(f"{'='*60}")

        for file in result["files"]:
            if file["type"] == "directory":
                print(f"📁 {file['name']}/")
            else:
                size = f"{file['size']:,}" if file["size"] else "0"
                print(f"📄 {file['name']} ({size} bytes)")

    def data_csv(self, file_path: str):
        """Get CSV data."""
        response = self.session.get(f"{self.base_url}/api/data/csv/{file_path}")
        result = self._handle_response(response)

        print(f"\n📊 CSV Data: {file_path}")
        print(f"Format: {result['format']}")

        if result["format"] == "pandas" and "data" in result["data"]:
            data = result["data"]["data"]
            columns = result["data"]["columns"]

            print(f"Rows: {len(data)}")
            print(f"Columns: {', '.join(columns)}")

            # Show first few rows
            print("\nFirst 5 rows:")
            print(f"{'='*60}")
            for i, row in enumerate(data[:5]):
                print(f"Row {i}: {json.dumps(row, indent=2)}")

    def health(self):
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        result = self._handle_response(response)
        print(f"✅ API Status: {result['status']}")


def main():
    parser = argparse.ArgumentParser(
        description="Trading API CLI Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    client = TradingAPIClient()

    subparsers = parser.add_subparsers(dest="service", help="API services")

    # MA Cross subcommands
    ma_cross = subparsers.add_parser("ma-cross", help="MA Cross analysis")
    ma_cross_sub = ma_cross.add_subparsers(dest="command")

    # MA Cross analyze
    analyze = ma_cross_sub.add_parser("analyze", help="Run analysis")
    analyze.add_argument("--ticker", nargs="+", required=True, help="Ticker(s)")
    analyze.add_argument("--start", default="2023-01-01", help="Start date")
    analyze.add_argument("--end", default="2023-12-31", help="End date")
    analyze.add_argument(
        "--async", dest="async_exec", action="store_true", help="Async execution"
    )
    analyze.add_argument("--windows", type=int, help="Max window size")
    analyze.add_argument("--direction", choices=["Long", "Short"])
    analyze.add_argument(
        "--ma-types", dest="ma_types", nargs="+", choices=["SMA", "EMA"]
    )
    analyze.add_argument("--hourly", action="store_true")
    analyze.add_argument("--min-trades", dest="min_trades", type=int)
    analyze.add_argument("--min-win-rate", dest="min_win_rate", type=float)
    analyze.add_argument("--min-profit-factor", dest="min_profit_factor", type=float)
    analyze.add_argument("--min-score", dest="min_score", type=float)
    analyze.add_argument("--min-sortino", dest="min_sortino", type=float)
    analyze.add_argument("--min-beats-bnh", dest="min_beats_bnh", type=float)

    # Other MA Cross commands
    ma_cross_sub.add_parser("metrics", help="Get metrics")
    ma_cross_sub.add_parser("health", help="Health check")

    status = ma_cross_sub.add_parser("status", help="Check task status")
    status.add_argument("execution_id", help="Execution ID")

    stream = ma_cross_sub.add_parser("stream", help="Stream progress")
    stream.add_argument("execution_id", help="Execution ID")

    # Script subcommands
    scripts = subparsers.add_parser("scripts", help="Script execution")
    scripts_sub = scripts.add_subparsers(dest="command")

    scripts_sub.add_parser("list", help="List scripts")

    execute = scripts_sub.add_parser("execute", help="Execute script")
    execute.add_argument("script_path", help="Script path")
    execute.add_argument("--params", nargs="*", help="Parameters as KEY=VALUE")
    execute.add_argument("--async", dest="async_exec", action="store_true")

    # Data subcommands
    data = subparsers.add_parser("data", help="Data access")
    data_sub = data.add_subparsers(dest="command")

    list_cmd = data_sub.add_parser("list", help="List files")
    list_cmd.add_argument("directory", nargs="?", help="Directory path")

    csv_cmd = data_sub.add_parser("csv", help="Get CSV data")
    csv_cmd.add_argument("file_path", help="CSV file path")

    json_cmd = data_sub.add_parser("json", help="Get JSON data")
    json_cmd.add_argument("file_path", help="JSON file path")

    # General commands
    subparsers.add_parser("health", help="API health check")

    args = parser.parse_args()

    # Route to appropriate handler
    if args.service == "ma-cross":
        if args.command == "analyze":
            client.ma_cross_analyze(args)
        elif args.command == "status":
            client.ma_cross_status(args.execution_id)
        elif args.command == "stream":
            client.ma_cross_stream(args.execution_id)
        elif args.command == "metrics":
            client.ma_cross_metrics()
        elif args.command == "health":
            client.ma_cross_health()
    elif args.service == "scripts":
        if args.command == "list":
            client.scripts_list()
        elif args.command == "execute":
            params = {}
            if args.params:
                for param in args.params:
                    key, value = param.split("=", 1)
                    params[key] = value
            client.scripts_execute(args.script_path, params, args.async_exec)
    elif args.service == "data":
        if args.command == "list":
            client.data_list(args.directory)
        elif args.command == "csv":
            client.data_csv(args.file_path)
    elif args.service == "health":
        client.health()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
