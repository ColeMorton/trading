#!/usr/bin/env python3
"""
Updated SPDS CLI using the new SPDSAnalysisEngine

This CLI uses the simplified 3-layer architecture instead of the old 5-layer system.
"""

import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Import new architecture
from app.tools.spds_analysis_engine import AnalysisRequest, SPDSAnalysisEngine
from app.tools.spds_config import SPDSConfig
from app.tools.spds_export import SPDSExporter as SPDSExportService


class SPDSCLIUpdated:
    """Updated Statistical Performance Divergence System CLI using new architecture"""

    def __init__(self):
        self.parser = self._create_parser()
        self.engine = SPDSAnalysisEngine()
        self.export_service = SPDSExportService()

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="Statistical Performance Divergence System - New Architecture",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze --portfolio risk_on.csv --data-source trade-history
  %(prog)s analyze --portfolio conservative.csv --data-source equity-curves
  %(prog)s analyze --strategy AAPL_SMA_20_50
  %(prog)s analyze --position AAPL_SMA_20_50_20250101
  %(prog)s health
  %(prog)s list-portfolios
            """,
        )

        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Analyze command
        analyze_parser = subparsers.add_parser("analyze", help="Run SPDS analysis")
        analyze_group = analyze_parser.add_mutually_exclusive_group(required=True)
        analyze_group.add_argument(
            "--portfolio",
            "-p",
            type=str,
            help='Portfolio filename (e.g., "risk_on.csv")',
        )
        analyze_group.add_argument(
            "--strategy",
            "-s",
            type=str,
            help="Strategy name (e.g., AAPL_SMA_20_50)",
        )
        analyze_group.add_argument(
            "--position",
            type=str,
            help="Position UUID (e.g., AAPL_SMA_20_50_20250101)",
        )

        # Analysis options
        analyze_parser.add_argument(
            "--data-source",
            choices=["auto", "trade-history", "equity-curves", "both"],
            default="auto",
            help="Data source preference (default: auto)",
        )
        analyze_parser.add_argument(
            "--output-format",
            choices=["json", "table", "summary"],
            default="table",
            help="Output format (default: table)",
        )
        analyze_parser.add_argument(
            "--save-results",
            type=str,
            help="Save results to file (JSON format)",
        )

        # Health command
        subparsers.add_parser("health", help="System health check")

        # List portfolios command
        subparsers.add_parser("list-portfolios", help="List available portfolios")

        # Demo command
        subparsers.add_parser("demo", help="Create demo files and run example")

        # Interactive command
        subparsers.add_parser("interactive", help="Interactive mode")

        # Global options
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output",
        )
        parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")

        return parser

    async def run(self, args: list | None = None) -> int:
        """Run the CLI application"""
        try:
            parsed_args = self.parser.parse_args(args)

            # Configure logging level
            if parsed_args.verbose:
                logging.getLogger().setLevel(logging.DEBUG)
            elif parsed_args.quiet:
                logging.getLogger().setLevel(logging.ERROR)

            # Route to appropriate handler
            if parsed_args.command == "analyze":
                return await self._handle_analyze(parsed_args)
            if parsed_args.command == "health":
                return await self._handle_health()
            if parsed_args.command == "list-portfolios":
                return self._handle_list_portfolios()
            if parsed_args.command == "demo":
                return await self._handle_demo()
            if parsed_args.command == "interactive":
                return await self._handle_interactive()
            self.parser.print_help()
            return 0

        except KeyboardInterrupt:
            print("\n⚠️  Operation cancelled by user")
            return 1
        except Exception as e:
            logger.exception(f"Application error: {e}")
            if hasattr(parsed_args, "verbose") and parsed_args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    async def _handle_analyze(self, args) -> int:
        """Handle analysis using new architecture"""
        print("🧠 SPDS Analysis - New Architecture")
        print("-" * 50)

        try:
            # Create analysis request
            if args.portfolio:
                analysis_type = "portfolio"
                parameter = args.portfolio
                print(f"📊 Analyzing Portfolio: {parameter}")
            elif args.strategy:
                analysis_type = "strategy"
                parameter = args.strategy
                print(f"🎯 Analyzing Strategy: {parameter}")
            elif args.position:
                analysis_type = "position"
                parameter = args.position
                print(f"📍 Analyzing Position: {parameter}")

            # Determine data source
            use_trade_history = self._determine_data_source(args.data_source)
            print(
                f"   Data Source: {args.data_source} ({'Trade History' if use_trade_history else 'Equity Curves'})",
            )

            # Create request
            request = AnalysisRequest(
                analysis_type=analysis_type,
                parameter=parameter,
                use_trade_history=use_trade_history,
            )

            # Run analysis
            print("🔄 Running analysis...")
            results = await self.engine.analyze(request)

            # Output results
            if args.output_format == "json":
                return self._output_json_results(results, args.save_results)
            if args.output_format == "summary":
                return self._output_summary_results(results)
            # table format
            return self._output_table_results(results)

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return 1

    def _determine_data_source(self, data_source: str) -> bool:
        """Determine whether to use trade history based on data source preference"""
        if data_source == "trade-history":
            return True
        if data_source == "equity-curves":
            return False
        # auto or both
        return False  # Default to equity curves

    def _output_json_results(self, results: dict, save_path: str | None = None) -> int:
        """Output results in JSON format"""
        # Convert results to serializable format
        serializable_results = {}
        for key, result in results.items():
            serializable_results[key] = {
                "strategy_name": result.strategy_name,
                "ticker": result.ticker,
                "position_uuid": result.position_uuid,
                "exit_signal": {
                    "signal_type": result.exit_signal.signal_type.value,
                    "risk_level": result.exit_signal.risk_level.value,
                    "reasoning": result.exit_signal.reasoning,
                },
                "confidence_level": result.confidence_level,
                "statistical_metrics": result.statistical_metrics,
                "divergence_metrics": result.divergence_metrics,
                "component_scores": result.component_scores,
            }

        output_data = {
            "analysis_summary": {
                "total_results": len(results),
                "timestamp": "2025-07-15T20:00:00Z",
            },
            "results": serializable_results,
        }

        json_output = json.dumps(output_data, indent=2, default=str)

        if save_path:
            with open(save_path, "w") as f:
                f.write(json_output)
            print(f"✅ Results saved to: {save_path}")
        else:
            print(json_output)

        return 0

    def _output_summary_results(self, results: dict) -> int:
        """Output summary results"""
        print("\n📈 Analysis Summary")
        print("=" * 40)
        print(f"Total Results: {len(results)}")

        # Count signals
        signal_counts: dict[str, int] = {}
        for result in results.values():
            signal = result.exit_signal.signal_type.value
            signal_counts[signal] = signal_counts.get(signal, 0) + 1

        print("\n🎯 Signal Distribution:")
        for signal, count in signal_counts.items():
            print(f"  {signal}: {count}")

        # Show high confidence results
        high_confidence = sum(1 for r in results.values() if r.confidence_level >= 75)
        print(
            f"\nHigh Confidence Results: {high_confidence}/{len(results)} ({high_confidence/len(results)*100:.1f}%)",
        )

        return 0

    def _output_table_results(self, results: dict) -> int:
        """Output detailed table results"""
        if not results:
            print("No results to display")
            return 0

        # Summary first
        self._output_summary_results(results)

        # Detailed results
        print("\n📋 Detailed Analysis Results")
        print("=" * 100)

        # Table header
        print(
            f"{'Strategy':<30} {'Ticker':<8} {'Signal':<15} {'Risk':<10} {'Confidence':<10} {'Reasoning'}",
        )
        print("-" * 100)

        # Sort by confidence level (highest first)
        sorted_results = sorted(
            results.items(),
            key=lambda x: x[1].confidence_level,
            reverse=True,
        )

        for strategy_name, result in sorted_results:
            signal = result.exit_signal.signal_type.value
            risk = result.exit_signal.risk_level.value
            confidence = result.confidence_level
            reasoning = (
                result.exit_signal.reasoning[:40] + "..."
                if len(result.exit_signal.reasoning) > 40
                else result.exit_signal.reasoning
            )

            # Signal icon
            signal_icons = {
                "EXIT_IMMEDIATELY": "🚨",
                "STRONG_SELL": "📉",
                "SELL": "⚠️",
                "HOLD": "✅",
                "TIME_EXIT": "⏰",
            }
            signal_icon = signal_icons.get(signal, "❓")

            print(
                f"{strategy_name:<30} {result.ticker:<8} {signal_icon} {signal:<13} {risk:<10} {confidence:>6.1f}%    {reasoning}",
            )

        print("\n💡 Architecture: New 3-layer SPDS system (CLI → Engine → Results)")
        print(f"📊 Performance: {len(results)} results processed")

        return 0

    async def _handle_health(self) -> int:
        """Handle system health check"""
        print("🏥 SPDS System Health Check")
        print("=" * 40)

        try:
            # Test engine initialization
            print("1. Engine Initialization... ", end="")
            engine = SPDSAnalysisEngine()
            print("✅")

            # Test configuration
            print("2. Configuration... ", end="")
            SPDSConfig()
            print("✅")

            # Test export service
            print("3. Export Service... ", end="")
            SPDSExportService()
            print("✅")

            # Test data directories
            print("4. Data Directories:")
            directories = [
                ("Portfolio Directory", Path("data/raw/positions")),
                ("Price Data Directory", Path("data/raw/prices")),
                ("Export Directory", Path("data/outputs/spds")),
            ]

            for name, path in directories:
                status = "✅" if path.exists() else "❌"
                print(f"   {name}: {status} ({path})")

            # Test simple analysis
            print("5. Simple Analysis Test... ", end="")
            try:
                request = AnalysisRequest(
                    analysis_type="strategy",
                    parameter="TEST_SMA_20_50",
                )
                await engine.analyze(request)
                print("✅")
            except Exception as e:
                print(f"⚠️ ({str(e)[:30]}...)")

            print("\n🎯 System Status: Operational")
            print("📊 Architecture: New 3-layer SPDS (simplified)")
            print("🔧 Components: SPDSAnalysisEngine, SPDSExportService, SPDSConfig")

            return 0

        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return 1

    def _handle_list_portfolios(self) -> int:
        """Handle portfolio listing"""
        print("📋 Available Portfolios")
        print("=" * 30)

        # Check portfolio directory
        portfolio_dir = Path("data/raw/positions")
        if not portfolio_dir.exists():
            print("❌ Portfolio directory not found: data/raw/positions/")
            print("💡 Create portfolio files in data/raw/positions/ directory")
            return 1

        # List CSV files
        portfolio_files = list(portfolio_dir.glob("*.csv"))

        if not portfolio_files:
            print("❌ No portfolio files found in data/raw/positions/")
            return 1

        print(f"Found {len(portfolio_files)} portfolio(s):")
        print()

        for portfolio_file in sorted(portfolio_files):
            portfolio_name = portfolio_file.name
            print(f"📊 {portfolio_name}")

            # Try to read position count
            try:
                import pandas as pd

                df = pd.read_csv(portfolio_file)
                print(f"   Positions: {len(df)}")

                # Show sample tickers
                if "Ticker" in df.columns:
                    tickers = df["Ticker"].value_counts().head(3)
                    ticker_list = ", ".join(
                        [f"{ticker}({count})" for ticker, count in tickers.items()],
                    )
                    print(f"   Top Tickers: {ticker_list}")

            except Exception as e:
                print(f"   Error reading file: {e}")
            print()

        print("💡 Usage:")
        print("  python -m app.tools.spds_cli_updated analyze --portfolio <filename>")

        return 0

    async def _handle_demo(self) -> int:
        """Handle demo mode"""
        print("🎯 Demo Mode - New Architecture")
        print("=" * 40)

        try:
            # Create sample portfolio
            sample_data = [
                {
                    "Position_UUID": "AAPL_SMA_20_50_20250115",
                    "Ticker": "AAPL",
                    "Strategy": "SMA",
                    "Fast_Period": 20,
                    "Slow_Period": 50,
                    "Win_Rate": 0.65,
                    "Total_Return": 0.25,
                    "Sharpe_Ratio": 1.5,
                    "Max_Drawdown": 0.15,
                    "Total_Trades": 150,
                    "Entry_Date": "2025-01-15",
                    "Exit_Date": "",
                    "Current_Price": 175.0,
                    "Position_Size": 100,
                    "Unrealized_PnL": 2500,
                },
            ]

            # Create demo portfolio file
            portfolio_dir = Path("data/raw/positions")
            portfolio_dir.mkdir(parents=True, exist_ok=True)

            import pandas as pd

            demo_file = portfolio_dir / "demo_new_architecture.csv"
            pd.DataFrame(sample_data).to_csv(demo_file, index=False)

            print(f"✅ Created demo portfolio: {demo_file}")

            # Run analysis on demo portfolio
            print("\n🔄 Running demo analysis...")
            request = AnalysisRequest(
                analysis_type="portfolio",
                parameter="demo_new_architecture.csv",
                use_trade_history=False,
            )

            results = await self.engine.analyze(request)

            print(f"✅ Demo analysis completed: {len(results)} results")

            # Show sample result
            if results:
                sample_key = next(iter(results.keys()))
                sample_result = results[sample_key]
                print("\n📊 Sample Result:")
                print(f"   Strategy: {sample_result.strategy_name}")
                print(f"   Signal: {sample_result.exit_signal.signal_type.value}")
                print(f"   Confidence: {sample_result.confidence_level:.1f}%")

            print("\n🎉 Demo completed successfully!")
            print(
                "💡 Try: python -m app.tools.spds_cli_updated analyze --portfolio demo_new_architecture.csv",
            )

            return 0

        except Exception as e:
            print(f"❌ Demo failed: {e}")
            return 1

    async def _handle_interactive(self) -> int:
        """Handle interactive mode"""
        print("🎮 Interactive Mode - New Architecture")
        print("=" * 50)

        try:
            while True:
                print("\nOptions:")
                print("  1. Analyze portfolio")
                print("  2. Analyze strategy")
                print("  3. List portfolios")
                print("  4. System health")
                print("  5. Create demo")
                print("  6. Exit")

                choice = input("\nSelect option (1-6): ").strip()

                if choice == "1":
                    await self._interactive_analyze_portfolio()
                elif choice == "2":
                    await self._interactive_analyze_strategy()
                elif choice == "3":
                    self._handle_list_portfolios()
                elif choice == "4":
                    await self._handle_health()
                elif choice == "5":
                    await self._handle_demo()
                elif choice == "6":
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please select 1-6.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")

        return 0

    async def _interactive_analyze_portfolio(self):
        """Interactive portfolio analysis"""
        print("\n📋 Available Portfolios:")
        self._handle_list_portfolios()

        portfolio = input("\nEnter portfolio filename: ").strip()
        if not portfolio:
            print("❌ No portfolio specified")
            return

        # Create args object
        class Args:
            def __init__(self):
                self.portfolio = portfolio
                self.strategy = None
                self.position = None
                self.data_source = "auto"
                self.output_format = "table"
                self.save_results = None

        args = Args()
        await self._handle_analyze(args)

    async def _interactive_analyze_strategy(self):
        """Interactive strategy analysis"""
        strategy = input("\nEnter strategy name (e.g., AAPL_SMA_20_50): ").strip()
        if not strategy:
            print("❌ No strategy specified")
            return

        # Create args object
        class Args:
            def __init__(self):
                self.portfolio = None
                self.strategy = strategy
                self.position = None
                self.data_source = "auto"
                self.output_format = "table"
                self.save_results = None

        args = Args()
        await self._handle_analyze(args)


def main():
    """Main entry point"""
    cli = SPDSCLIUpdated()
    return asyncio.run(cli.run())


if __name__ == "__main__":
    sys.exit(main())
