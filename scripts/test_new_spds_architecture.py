#!/usr/bin/env python3
"""
Test New SPDS Architecture

Tests the new simplified SPDS architecture to validate performance
and functionality compared to the existing system.
"""

import asyncio
import json

# Add project root to path
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table


sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.spds_analysis_engine import AnalysisRequest, SPDSAnalysisEngine


console = Console()


class NewArchitectureTest:
    """Test the new SPDS architecture."""

    def __init__(self):
        self.test_results = []
        self.portfolio_dir = Path("data/raw/positions")
        self.portfolio_dir.mkdir(parents=True, exist_ok=True)

    def create_test_portfolio(self, size: int) -> str:
        """Create a test portfolio for the new architecture."""
        portfolio_filename = f"test_new_arch_{size}.csv"
        portfolio_path = self.portfolio_dir / portfolio_filename

        # Generate test data
        np.random.seed(42)  # For reproducible results

        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        strategies = ["SMA", "EMA", "MACD"]

        data = []
        for i in range(size):
            ticker = np.random.choice(tickers)
            strategy = np.random.choice(strategies)

            fast_period = np.random.randint(5, 50)
            slow_period = np.random.randint(50, 200)

            data.append(
                {
                    "Position_UUID": f"{ticker}_{strategy}_{fast_period}_{slow_period}_{20250101 + i:08d}",
                    "Ticker": ticker,
                    "Strategy": strategy,
                    "Fast_Period": fast_period,
                    "Slow_Period": slow_period,
                    "Win_Rate": np.random.uniform(0.3, 0.8),
                    "Total_Return": np.random.uniform(-0.5, 2.0),
                    "Sharpe_Ratio": np.random.uniform(-1.0, 3.0),
                    "Max_Drawdown": np.random.uniform(0.05, 0.4),
                    "Total_Trades": np.random.randint(10, 500),
                    "Entry_Date": f"2025-01-{(i % 28) + 1:02d}",
                    "Exit_Date": "",
                    "Current_Price": np.random.uniform(50, 500),
                    "Position_Size": np.random.randint(1, 1000),
                    "Unrealized_PnL": np.random.uniform(-1000, 5000),
                }
            )

        df = pd.DataFrame(data)
        df.to_csv(portfolio_path, index=False)

        return portfolio_filename

    async def test_portfolio_analysis(self, portfolio_size: int) -> dict[str, Any]:
        """Test portfolio analysis with new architecture."""
        console.print(
            f"[cyan]Testing portfolio analysis ({portfolio_size} positions)[/cyan]"
        )

        # Create test portfolio
        portfolio_filename = self.create_test_portfolio(portfolio_size)

        # Test new architecture
        start_time = time.time()

        try:
            engine = SPDSAnalysisEngine()
            request = AnalysisRequest(
                analysis_type="portfolio",
                parameter=portfolio_filename,
                use_trade_history=False,
            )

            results = await engine.analyze(request)

            end_time = time.time()
            execution_time = end_time - start_time

            return {
                "portfolio_size": portfolio_size,
                "execution_time": execution_time,
                "results_count": len(results),
                "success": True,
                "error": None,
                "sample_result": (
                    list(results.values())[0].to_dict() if results else None
                ),
            }

        except Exception as e:
            return {
                "portfolio_size": portfolio_size,
                "execution_time": time.time() - start_time,
                "results_count": 0,
                "success": False,
                "error": str(e),
                "sample_result": None,
            }

    async def test_strategy_analysis(self) -> dict[str, Any]:
        """Test strategy analysis with new architecture."""
        console.print("[cyan]Testing strategy analysis[/cyan]")

        start_time = time.time()

        try:
            engine = SPDSAnalysisEngine()
            request = AnalysisRequest(
                analysis_type="strategy", parameter="AAPL_SMA_20_50"
            )

            results = await engine.analyze(request)

            end_time = time.time()
            execution_time = end_time - start_time

            return {
                "execution_time": execution_time,
                "results_count": len(results),
                "success": True,
                "error": None,
                "sample_result": (
                    list(results.values())[0].to_dict() if results else None
                ),
            }

        except Exception as e:
            return {
                "execution_time": time.time() - start_time,
                "results_count": 0,
                "success": False,
                "error": str(e),
                "sample_result": None,
            }

    async def test_position_analysis(self) -> dict[str, Any]:
        """Test position analysis with new architecture."""
        console.print("[cyan]Testing position analysis[/cyan]")

        # First create a small portfolio to have positions to analyze
        portfolio_filename = self.create_test_portfolio(10)

        start_time = time.time()

        try:
            engine = SPDSAnalysisEngine()
            request = AnalysisRequest(
                analysis_type="position", parameter="AAPL_SMA_20_50_20250101"
            )

            results = await engine.analyze(request)

            end_time = time.time()
            execution_time = end_time - start_time

            return {
                "execution_time": execution_time,
                "results_count": len(results),
                "success": True,
                "error": None,
                "sample_result": (
                    list(results.values())[0].to_dict() if results else None
                ),
            }

        except Exception as e:
            return {
                "execution_time": time.time() - start_time,
                "results_count": 0,
                "success": False,
                "error": str(e),
                "sample_result": None,
            }

    async def run_comprehensive_test(self):
        """Run comprehensive test of new architecture."""
        console.print("[bold]🧪 Testing New SPDS Architecture[/bold]")
        console.print("-" * 50)

        # Test different portfolio sizes
        portfolio_sizes = [100, 1000, 5000]

        for size in portfolio_sizes:
            result = await self.test_portfolio_analysis(size)
            self.test_results.append(result)

        # Test strategy analysis
        strategy_result = await self.test_strategy_analysis()
        self.test_results.append(strategy_result)

        # Test position analysis
        position_result = await self.test_position_analysis()
        self.test_results.append(position_result)

        # Display results
        self.display_results()

        # Save results
        self.save_results()

    def display_results(self):
        """Display test results."""
        console.print("\n[bold]📊 New Architecture Test Results[/bold]")

        # Create results table
        table = Table(title="Performance Test Results", show_header=True)
        table.add_column("Test Type", style="cyan")
        table.add_column("Size/Parameter", style="white")
        table.add_column("Execution Time", style="green")
        table.add_column("Results Count", style="yellow")
        table.add_column("Status", style="blue")

        for result in self.test_results:
            if "portfolio_size" in result:
                test_type = "Portfolio Analysis"
                size_param = f"{result['portfolio_size']:,} positions"
            elif "sample_result" in result and result.get("sample_result", {}).get(
                "strategy_name"
            ):
                test_type = "Strategy Analysis"
                size_param = "AAPL_SMA_20_50"
            else:
                test_type = "Position Analysis"
                size_param = "AAPL_SMA_20_50_20250101"

            status = "✅ Success" if result["success"] else "❌ Failed"

            table.add_row(
                test_type,
                size_param,
                f"{result['execution_time']:.3f}s",
                str(result["results_count"]),
                status,
            )

        console.print(table)

        # Show any errors
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            console.print("\n[red]❌ Failed Tests:[/red]")
            for test in failed_tests:
                console.print(f"[red]  • {test.get('error', 'Unknown error')}[/red]")

        # Performance summary
        successful_tests = [r for r in self.test_results if r["success"]]
        if successful_tests:
            avg_time = sum(r["execution_time"] for r in successful_tests) / len(
                successful_tests
            )
            console.print(
                f"\n[green]✅ Average execution time: {avg_time:.3f}s[/green]"
            )

            # Show sample result structure
            sample_result = next(
                (r["sample_result"] for r in successful_tests if r["sample_result"]),
                None,
            )
            if sample_result:
                console.print(
                    f"\n[dim]Sample result keys: {list(sample_result.keys())}[/dim]"
                )

    def save_results(self):
        """Save test results to file."""
        results_file = Path("new_architecture_test_results.json")

        with open(results_file, "w") as f:
            json.dump(self.test_results, f, indent=2)

        console.print(f"\n[green]💾 Results saved to: {results_file}[/green]")


async def main():
    """Run the new architecture test."""
    tester = NewArchitectureTest()
    await tester.run_comprehensive_test()


if __name__ == "__main__":
    asyncio.run(main())
