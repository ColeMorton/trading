#!/usr/bin/env python3
"""
SPDS Performance Benchmark Script

Creates performance baselines for key SPDS operations to validate whether
memory optimization complexity is justified. Tests analysis time for 1K, 10K,
and 100K position portfolios.

Usage:
    python scripts/spds_performance_benchmark.py
    python scripts/spds_performance_benchmark.py --quick-test
    python scripts/spds_performance_benchmark.py --save-results benchmark_results.json
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import statistics

import pandas as pd
import numpy as np
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID

# Import SPDS components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.tools.portfolio_analyzer import PortfolioStatisticalAnalyzer
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig
from app.tools.models.statistical_analysis_models import StatisticalAnalysisResult

console = Console()

@dataclass
class BenchmarkResult:
    """Individual benchmark result."""
    operation: str
    portfolio_size: int
    execution_time: float
    memory_usage_mb: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class BenchmarkSuite:
    """Complete benchmark suite results."""
    results: List[BenchmarkResult]
    total_time: float
    system_info: Dict[str, Any]
    timestamp: str

class SPDSPerformanceBenchmark:
    """Performance benchmarking for SPDS operations."""
    
    def __init__(self, save_results: Optional[str] = None):
        self.save_results = save_results
        self.results: List[BenchmarkResult] = []
        self.logger = logging.getLogger(__name__)
        
        # Create benchmark portfolios directory
        self.benchmark_dir = Path("benchmark_portfolios")
        self.benchmark_dir.mkdir(exist_ok=True)
        
        # Portfolio sizes to test
        self.portfolio_sizes = [1000, 10000, 100000]
        
    def create_test_portfolio(self, size: int) -> str:
        """Create a test portfolio with specified number of positions."""
        portfolio_path = self.benchmark_dir / f"test_portfolio_{size}.csv"
        
        # Generate realistic portfolio data
        np.random.seed(42)  # For reproducible results
        
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX", "SPY", "QQQ"]
        strategies = ["SMA", "EMA", "MACD", "RSI"]
        
        data = []
        for i in range(size):
            ticker = np.random.choice(tickers)
            strategy = np.random.choice(strategies)
            
            # Generate realistic parameters
            short_window = np.random.randint(5, 50)
            long_window = np.random.randint(50, 200)
            
            # Generate realistic performance metrics
            win_rate = np.random.uniform(0.3, 0.8)
            total_return = np.random.uniform(-0.5, 2.0)
            sharpe_ratio = np.random.uniform(-1.0, 3.0)
            max_drawdown = np.random.uniform(0.05, 0.4)
            trades = np.random.randint(10, 500)
            
            # Create Position_UUID
            position_uuid = f"{ticker}_{strategy}_{short_window}_{long_window}_{20250101 + i:08d}"
            
            data.append({
                "Ticker": ticker,
                "Strategy": strategy,
                "Short_Window": short_window,
                "Long_Window": long_window,
                "Win_Rate": win_rate,
                "Total_Return": total_return,
                "Sharpe_Ratio": sharpe_ratio,
                "Max_Drawdown": max_drawdown,
                "Total_Trades": trades,
                "Position_UUID": position_uuid,
                "Entry_Date": f"2025-01-{(i % 28) + 1:02d}",
                "Exit_Date": "",
                "Current_Price": np.random.uniform(50, 500),
                "Position_Size": np.random.randint(1, 1000),
                "Unrealized_PnL": np.random.uniform(-1000, 5000),
            })
        
        df = pd.DataFrame(data)
        df.to_csv(portfolio_path, index=False)
        
        console.print(f"[green]✅ Created test portfolio with {size} positions: {portfolio_path}[/green]")
        return str(portfolio_path)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    async def benchmark_portfolio_analysis(self, portfolio_path: str, size: int) -> BenchmarkResult:
        """Benchmark portfolio analysis operation."""
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            # Copy the portfolio file to the correct location
            import shutil
            positions_dir = Path("csv/positions")
            positions_dir.mkdir(parents=True, exist_ok=True)
            
            portfolio_filename = Path(portfolio_path).name
            dest_path = positions_dir / portfolio_filename
            shutil.copy2(portfolio_path, dest_path)
            
            # Test with trade history mode using just the filename
            analyzer = PortfolioStatisticalAnalyzer(portfolio_filename, use_trade_history=False)
            results = await analyzer.analyze()
            
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            execution_time = end_time - start_time
            memory_usage = end_memory - start_memory
            
            return BenchmarkResult(
                operation="Portfolio Analysis",
                portfolio_size=size,
                execution_time=execution_time,
                memory_usage_mb=memory_usage,
                success=True
            )
            
        except Exception as e:
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            return BenchmarkResult(
                operation="Portfolio Analysis",
                portfolio_size=size,
                execution_time=end_time - start_time,
                memory_usage_mb=end_memory - start_memory,
                success=False,
                error_message=str(e)
            )
    
    async def benchmark_memory_optimization(self, portfolio_path: str, size: int) -> Tuple[BenchmarkResult, BenchmarkResult]:
        """Benchmark with and without memory optimization."""
        
        # Copy the portfolio file to the correct location
        import shutil
        positions_dir = Path("csv/positions")
        positions_dir.mkdir(parents=True, exist_ok=True)
        
        portfolio_filename = Path(portfolio_path).name
        dest_path = positions_dir / portfolio_filename
        shutil.copy2(portfolio_path, dest_path)
        
        # Test without memory optimization
        start_time = time.time()
        start_memory = self.get_memory_usage()
        
        try:
            # Create analyzer without memory optimization
            analyzer = PortfolioStatisticalAnalyzer(portfolio_filename, use_trade_history=False)
            results = await analyzer.analyze()
            
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            without_optimization = BenchmarkResult(
                operation="Analysis (No Memory Opt)",
                portfolio_size=size,
                execution_time=end_time - start_time,
                memory_usage_mb=end_memory - start_memory,
                success=True
            )
            
        except Exception as e:
            without_optimization = BenchmarkResult(
                operation="Analysis (No Memory Opt)",
                portfolio_size=size,
                execution_time=time.time() - start_time,
                memory_usage_mb=self.get_memory_usage() - start_memory,
                success=False,
                error_message=str(e)
            )
        
        # Test with memory optimization (if available)
        try:
            from app.tools.processing.memory_optimizer import get_memory_optimizer
            
            start_time = time.time()
            start_memory = self.get_memory_usage()
            
            # Enable memory optimization
            optimizer = get_memory_optimizer()
            optimizer.enable_monitoring = True
            
            analyzer = PortfolioStatisticalAnalyzer(portfolio_filename, use_trade_history=False)
            results = await analyzer.analyze()
            
            end_time = time.time()
            end_memory = self.get_memory_usage()
            
            with_optimization = BenchmarkResult(
                operation="Analysis (With Memory Opt)",
                portfolio_size=size,
                execution_time=end_time - start_time,
                memory_usage_mb=end_memory - start_memory,
                success=True
            )
            
        except Exception as e:
            with_optimization = BenchmarkResult(
                operation="Analysis (With Memory Opt)",
                portfolio_size=size,
                execution_time=time.time() - start_time,
                memory_usage_mb=self.get_memory_usage() - start_memory,
                success=False,
                error_message=str(e)
            )
        
        return without_optimization, with_optimization
    
    async def run_benchmark_suite(self, quick_test: bool = False) -> BenchmarkSuite:
        """Run complete benchmark suite."""
        console.print("[bold]🏃‍♂️ Starting SPDS Performance Benchmark Suite[/bold]")
        console.print("-" * 60)
        
        start_time = time.time()
        
        # Use smaller sizes for quick test
        if quick_test:
            self.portfolio_sizes = [100, 1000, 5000]
            console.print("[yellow]ℹ️  Running quick test with smaller portfolio sizes[/yellow]")
        
        with Progress() as progress:
            task = progress.add_task("Benchmarking...", total=len(self.portfolio_sizes) * 3)
            
            for size in self.portfolio_sizes:
                console.print(f"\n[cyan]📊 Testing portfolio size: {size:,} positions[/cyan]")
                
                # Create test portfolio
                portfolio_path = self.create_test_portfolio(size)
                
                # Benchmark basic portfolio analysis
                progress.update(task, advance=1)
                result = await self.benchmark_portfolio_analysis(portfolio_path, size)
                self.results.append(result)
                
                if result.success:
                    console.print(f"[green]✅ Analysis completed in {result.execution_time:.2f}s[/green]")
                else:
                    console.print(f"[red]❌ Analysis failed: {result.error_message}[/red]")
                
                # Benchmark memory optimization comparison
                progress.update(task, advance=1)
                without_opt, with_opt = await self.benchmark_memory_optimization(portfolio_path, size)
                self.results.extend([without_opt, with_opt])
                
                # Show memory optimization impact
                if without_opt.success and with_opt.success:
                    memory_savings = without_opt.memory_usage_mb - with_opt.memory_usage_mb
                    savings_pct = (memory_savings / without_opt.memory_usage_mb) * 100 if without_opt.memory_usage_mb > 0 else 0
                    console.print(f"[dim]Memory savings: {memory_savings:.1f}MB ({savings_pct:.1f}%)[/dim]")
                
                progress.update(task, advance=1)
        
        total_time = time.time() - start_time
        
        # Collect system information
        import platform
        import psutil
        
        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / (1024**3),
            "disk_usage_gb": psutil.disk_usage('/').total / (1024**3),
        }
        
        return BenchmarkSuite(
            results=self.results,
            total_time=total_time,
            system_info=system_info,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    def display_results(self, suite: BenchmarkSuite):
        """Display benchmark results in formatted table."""
        console.print(f"\n[bold]📈 SPDS Performance Benchmark Results[/bold]")
        console.print(f"[dim]Completed: {suite.timestamp} | Total Time: {suite.total_time:.1f}s[/dim]")
        console.print("-" * 80)
        
        # Create results table
        table = Table(title="Performance Benchmarks", show_header=True)
        table.add_column("Operation", style="cyan", no_wrap=True)
        table.add_column("Portfolio Size", style="white", justify="right")
        table.add_column("Execution Time", style="green", justify="right")
        table.add_column("Memory Usage", style="yellow", justify="right")
        table.add_column("Status", style="blue", justify="center")
        
        for result in suite.results:
            status = "✅ Success" if result.success else "❌ Failed"
            table.add_row(
                result.operation,
                f"{result.portfolio_size:,}",
                f"{result.execution_time:.2f}s",
                f"{result.memory_usage_mb:.1f}MB",
                status
            )
        
        console.print(table)
        
        # Performance insights
        console.print("\n[bold]🔍 Performance Insights[/bold]")
        
        # Calculate averages for successful operations
        successful_results = [r for r in suite.results if r.success]
        
        if successful_results:
            avg_time_per_1k = statistics.mean([
                r.execution_time / (r.portfolio_size / 1000) 
                for r in successful_results 
                if r.portfolio_size > 0
            ])
            
            avg_memory_per_1k = statistics.mean([
                r.memory_usage_mb / (r.portfolio_size / 1000) 
                for r in successful_results 
                if r.portfolio_size > 0
            ])
            
            console.print(f"[dim]Average time per 1K positions: {avg_time_per_1k:.3f}s[/dim]")
            console.print(f"[dim]Average memory per 1K positions: {avg_memory_per_1k:.1f}MB[/dim]")
            
            # Memory optimization assessment
            with_opt_results = [r for r in successful_results if "With Memory Opt" in r.operation]
            without_opt_results = [r for r in successful_results if "No Memory Opt" in r.operation]
            
            if with_opt_results and without_opt_results:
                avg_savings = statistics.mean([
                    wo.memory_usage_mb - w.memory_usage_mb 
                    for wo, w in zip(without_opt_results, with_opt_results)
                ])
                
                avg_savings_pct = statistics.mean([
                    ((wo.memory_usage_mb - w.memory_usage_mb) / wo.memory_usage_mb) * 100 
                    for wo, w in zip(without_opt_results, with_opt_results)
                    if wo.memory_usage_mb > 0
                ])
                
                console.print(f"[dim]Memory optimization savings: {avg_savings:.1f}MB ({avg_savings_pct:.1f}%)[/dim]")
                
                # Assessment of memory optimization value
                if avg_savings_pct > 50:
                    console.print("[green]✅ Memory optimization provides significant value[/green]")
                elif avg_savings_pct > 20:
                    console.print("[yellow]⚠️  Memory optimization provides moderate value[/yellow]")
                else:
                    console.print("[red]❌ Memory optimization may not justify complexity[/red]")
        
        # System information
        console.print("\n[bold]💻 System Information[/bold]")
        console.print(f"[dim]Python: {suite.system_info['python_version']}[/dim]")
        console.print(f"[dim]Platform: {suite.system_info['platform']}[/dim]")
        console.print(f"[dim]CPU Cores: {suite.system_info['cpu_count']}[/dim]")
        console.print(f"[dim]Memory: {suite.system_info['memory_gb']:.1f}GB[/dim]")
        
        # Failed operations summary
        failed_results = [r for r in suite.results if not r.success]
        if failed_results:
            console.print(f"\n[red]❌ {len(failed_results)} operations failed[/red]")
            for result in failed_results:
                console.print(f"[red]  • {result.operation} ({result.portfolio_size:,}): {result.error_message}[/red]")
    
    def save_benchmark_results(self, suite: BenchmarkSuite):
        """Save benchmark results to JSON file."""
        if not self.save_results:
            return
            
        # Convert to serializable format
        data = {
            "timestamp": suite.timestamp,
            "total_time": suite.total_time,
            "system_info": suite.system_info,
            "results": [
                {
                    "operation": r.operation,
                    "portfolio_size": r.portfolio_size,
                    "execution_time": r.execution_time,
                    "memory_usage_mb": r.memory_usage_mb,
                    "success": r.success,
                    "error_message": r.error_message
                }
                for r in suite.results
            ]
        }
        
        with open(self.save_results, 'w') as f:
            json.dump(data, f, indent=2)
        
        console.print(f"[green]💾 Results saved to: {self.save_results}[/green]")

async def main():
    """Main benchmark execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SPDS Performance Benchmark")
    parser.add_argument("--quick-test", action="store_true", help="Run quick test with smaller portfolios")
    parser.add_argument("--save-results", type=str, help="Save results to JSON file")
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during benchmarking
    
    # Create and run benchmark
    benchmark = SPDSPerformanceBenchmark(save_results=args.save_results)
    
    try:
        suite = await benchmark.run_benchmark_suite(quick_test=args.quick_test)
        benchmark.display_results(suite)
        
        if args.save_results:
            benchmark.save_benchmark_results(suite)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Benchmark interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Benchmark failed: {e}[/red]")
        raise

if __name__ == "__main__":
    asyncio.run(main())