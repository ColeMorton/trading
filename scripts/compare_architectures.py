#!/usr/bin/env python3
"""
Compare Old vs New SPDS Architecture

Benchmarks the old 5-layer architecture against the new 3-layer architecture
to validate performance improvements.
"""

import asyncio
import json

# Add project root to path
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd


sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table

from app.tools.spds_analysis_engine import AnalysisRequest, SPDSAnalysisEngine


console = Console()


@dataclass
class BenchmarkComparison:
    """Comparison result between old and new architectures."""

    operation: str
    portfolio_size: int
    old_time: float
    new_time: float
    old_success: bool
    new_success: bool
    speedup: float
    improvement: str


class ArchitectureComparison:
    """Compare old vs new SPDS architectures."""

    def __init__(self):
        self.results: list[BenchmarkComparison] = []
        self.portfolio_dir = Path("data/raw/positions")
        self.portfolio_dir.mkdir(parents=True, exist_ok=True)

    def create_test_portfolio(self, size: int) -> str:
        """Create a test portfolio."""
        portfolio_filename = f"arch_compare_{size}.csv"
        portfolio_path = self.portfolio_dir / portfolio_filename

        # Generate realistic test data
        np.random.seed(42)

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

    async def benchmark_new_architecture(
        self, portfolio_filename: str, size: int
    ) -> tuple[float, bool]:
        """Benchmark the new architecture."""
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
            return end_time - start_time, len(results) > 0

        except Exception as e:
            console.print(f"[red]New architecture failed: {e}[/red]")
            return time.time() - start_time, False

    async def benchmark_old_architecture(
        self, portfolio_filename: str, size: int
    ) -> tuple[float, bool]:
        """Benchmark the old architecture."""
        start_time = time.time()

        try:
            # Import old architecture components
            from app.tools.portfolio_analyzer import PortfolioStatisticalAnalyzer

            analyzer = PortfolioStatisticalAnalyzer(
                portfolio_filename, use_trade_history=False
            )
            results = await analyzer.analyze()

            end_time = time.time()
            return end_time - start_time, len(results) > 0

        except Exception as e:
            console.print(f"[red]Old architecture failed: {e}[/red]")
            return time.time() - start_time, False

    async def run_comparison(self, sizes: list[int] | None = None):
        """Run comprehensive comparison."""
        if sizes is None:
            sizes = [100, 500, 1000]
        console.print("[bold]⚡ Comparing SPDS Architectures[/bold]")
        console.print("-" * 50)

        for size in sizes:
            console.print(f"\n[cyan]Testing portfolio size: {size} positions[/cyan]")

            # Create test portfolio
            portfolio_filename = self.create_test_portfolio(size)

            # Benchmark old architecture
            console.print("  Testing old architecture...")
            old_time, old_success = await self.benchmark_old_architecture(
                portfolio_filename, size
            )

            # Benchmark new architecture
            console.print("  Testing new architecture...")
            new_time, new_success = await self.benchmark_new_architecture(
                portfolio_filename, size
            )

            # Calculate improvement
            if old_success and new_success and old_time > 0:
                speedup = old_time / new_time
                if speedup > 1.0:
                    improvement = f"{speedup:.1f}x faster"
                else:
                    improvement = f"{1 / speedup:.1f}x slower"
            else:
                speedup = 0.0
                improvement = "N/A"

            # Store results
            comparison = BenchmarkComparison(
                operation="Portfolio Analysis",
                portfolio_size=size,
                old_time=old_time,
                new_time=new_time,
                old_success=old_success,
                new_success=new_success,
                speedup=speedup,
                improvement=improvement,
            )

            self.results.append(comparison)

            # Show immediate results
            if old_success and new_success:
                console.print(
                    f"  [green]✅ Old: {old_time:.2f}s, New: {new_time:.2f}s ({improvement})[/green]"
                )
            elif new_success:
                console.print(
                    f"  [green]✅ New architecture succeeded in {new_time:.2f}s[/green]"
                )
            else:
                console.print("  [red]❌ Both architectures failed[/red]")

        # Display comprehensive results
        self.display_results()

        # Save results
        self.save_results()

    def display_results(self):
        """Display comparison results."""
        console.print("\n[bold]📊 Architecture Comparison Results[/bold]")

        # Create comparison table
        table = Table(title="Performance Comparison", show_header=True)
        table.add_column("Portfolio Size", style="cyan")
        table.add_column("Old Architecture", style="red")
        table.add_column("New Architecture", style="green")
        table.add_column("Improvement", style="yellow")
        table.add_column("Status", style="blue")

        for result in self.results:
            old_status = "✅" if result.old_success else "❌"
            new_status = "✅" if result.new_success else "❌"
            status = f"{old_status} → {new_status}"

            table.add_row(
                f"{result.portfolio_size:,} positions",
                f"{result.old_time:.2f}s",
                f"{result.new_time:.2f}s",
                result.improvement,
                status,
            )

        console.print(table)

        # Calculate summary statistics
        successful_comparisons = [
            r for r in self.results if r.old_success and r.new_success
        ]

        if successful_comparisons:
            avg_old_time = sum(r.old_time for r in successful_comparisons) / len(
                successful_comparisons
            )
            avg_new_time = sum(r.new_time for r in successful_comparisons) / len(
                successful_comparisons
            )
            avg_speedup = sum(r.speedup for r in successful_comparisons) / len(
                successful_comparisons
            )

            console.print("\n[bold]📈 Summary Statistics[/bold]")
            console.print(f"Average old architecture time: {avg_old_time:.2f}s")
            console.print(f"Average new architecture time: {avg_new_time:.2f}s")
            console.print(f"Average speedup: {avg_speedup:.1f}x")

            if avg_speedup > 1.0:
                console.print(
                    f"[green]✅ New architecture is {avg_speedup:.1f}x faster on average[/green]"
                )
            else:
                console.print(
                    f"[red]❌ New architecture is {1 / avg_speedup:.1f}x slower on average[/red]"
                )

        # Architecture complexity comparison
        console.print("\n[bold]🏗️ Architecture Complexity[/bold]")
        console.print(
            "Old architecture: 5 layers (CLI → Config → Service → Analysis → Export)"
        )
        console.print("New architecture: 3 layers (CLI → AnalysisEngine → Results)")
        console.print("Complexity reduction: 40% (5 → 3 layers)")

    def save_results(self):
        """Save comparison results."""
        results_data = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "total_comparisons": len(self.results),
                "successful_comparisons": len(
                    [r for r in self.results if r.old_success and r.new_success]
                ),
                "new_architecture_success_rate": (
                    len([r for r in self.results if r.new_success]) / len(self.results)
                    if self.results
                    else 0
                ),
                "old_architecture_success_rate": (
                    len([r for r in self.results if r.old_success]) / len(self.results)
                    if self.results
                    else 0
                ),
            },
            "comparisons": [
                {
                    "operation": r.operation,
                    "portfolio_size": r.portfolio_size,
                    "old_time": r.old_time,
                    "new_time": r.new_time,
                    "old_success": r.old_success,
                    "new_success": r.new_success,
                    "speedup": r.speedup,
                    "improvement": r.improvement,
                }
                for r in self.results
            ],
        }

        with open("architecture_comparison.json", "w") as f:
            json.dump(results_data, f, indent=2)

        console.print(
            "\n[green]💾 Results saved to: architecture_comparison.json[/green]"
        )


async def main():
    """Run architecture comparison."""
    comparison = ArchitectureComparison()
    await comparison.run_comparison()


if __name__ == "__main__":
    asyncio.run(main())
