#!/usr/bin/env python3
"""
Trade History Close Live Signal Command

Main entry point for generating comprehensive sell signal reports utilizing
all available SPDS statistical data to formulate data-based thesis for
position exit decisions.

Usage:
    python -m app.tools.trade_history_close_live_signal --strategy STRATEGY_NAME
    python -m app.tools.trade_history_close_live_signal --strategy MA_SMA_78_82 --output report.md
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .services.exit_strategy_optimizer import (
    ExitStrategyOptimizer,
    MarketCondition,
    optimize_exit_strategy,
)
from .services.sell_report_generator import generate_sell_report
from .services.signal_data_aggregator import (
    SignalDataAggregator,
    StrategyData,
    get_signal_data_aggregator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TradeHistoryCloseCommand:
    """Main command class for trade history close live signal analysis"""

    def __init__(self, base_path: Optional[Path] = None):
        """Initialize command with optional base path"""
        self.base_path = base_path or Path.cwd()
        self.aggregator = get_signal_data_aggregator(self.base_path)

    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute the command with parsed arguments

        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            # Handle special commands first
            if args.list_strategies:
                return self._list_strategies()

            if args.health_check:
                return self._health_check()

            if args.validate_data:
                return self._validate_data()

            # Require strategy for main analysis
            if not args.strategy:
                logger.error("Strategy name or Position_UUID is required")
                return 1

            # Generate the sell signal report
            return self._generate_report(args)

        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            if args.verbose:
                import traceback

                traceback.print_exc()
            return 1

    def _generate_report(self, args: argparse.Namespace) -> int:
        """Generate comprehensive sell signal report"""
        try:
            logger.info(f"Generating sell signal report for: {args.strategy}")

            # Parse market condition if provided
            market_condition = None
            if args.market_condition:
                try:
                    market_condition = MarketCondition(args.market_condition.lower())
                except ValueError:
                    logger.warning(f"Invalid market condition: {args.market_condition}")

            # Generate the report based on format
            if args.format.lower() == "json":
                report_content = self._generate_json_report(args, market_condition)
            elif args.format.lower() == "html":
                report_content = self._generate_html_report(args, market_condition)
            else:  # markdown (default)
                report_content = self._generate_markdown_report(args, market_condition)

            # Output handling
            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(parents=True, exist_ok=True)

                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(report_content)

                logger.info(f"Report saved to: {output_path}")
                print(f"✅ Report generated successfully: {output_path}")

                # Generate console summary
                self._display_console_summary(args.strategy)
            else:
                # When no output file specified, show brief summary then full report
                print("📋 Analysis Summary:")
                print("=" * 50)
                self._display_brief_summary(args.strategy)
                print("=" * 50)
                print("\n📄 Full Report:")
                print(report_content)

            return 0

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return 1

    def _generate_markdown_report(
        self, args: argparse.Namespace, market_condition: Optional[MarketCondition]
    ) -> str:
        """Generate markdown format report"""
        return generate_sell_report(
            args.strategy, self.base_path, args.include_raw_data
        )

    def _generate_json_report(
        self, args: argparse.Namespace, market_condition: Optional[MarketCondition]
    ) -> str:
        """Generate JSON format report"""
        # Get strategy data
        strategy_data = self.aggregator.get_strategy_data(args.strategy)
        if not strategy_data:
            return json.dumps(
                {"error": f"Strategy '{args.strategy}' not found"}, indent=2
            )

        # Get optimization results
        optimization_result = optimize_exit_strategy(
            strategy_data, args.current_price, market_condition
        )

        # Build comprehensive JSON report
        report = {
            "strategy_analysis": {
                "strategy_name": strategy_data.strategy_name,
                "ticker": strategy_data.ticker,
                "position_uuid": strategy_data.position_uuid,
                "analysis_timestamp": strategy_data.generation_timestamp
                or "2025-07-06T13:50:00",
                "exit_signal": strategy_data.exit_signal,
                "signal_confidence": strategy_data.signal_confidence,
                "statistical_validity": strategy_data.statistical_validity,
            },
            "statistical_foundation": {
                "sample_size": strategy_data.sample_size,
                "sample_size_confidence": strategy_data.sample_size_confidence,
                "p_value": strategy_data.p_value,
                "statistical_significance": strategy_data.statistical_significance,
                "dual_layer_convergence_score": strategy_data.dual_layer_convergence_score,
            },
            "performance_metrics": {
                "current_return": strategy_data.current_return,
                "unrealized_pnl": strategy_data.unrealized_pnl,
                "mfe": strategy_data.mfe,
                "mae": strategy_data.mae,
            },
            "divergence_analysis": {
                "z_score_divergence": strategy_data.z_score_divergence,
                "iqr_divergence": strategy_data.iqr_divergence,
                "rarity_score": strategy_data.rarity_score,
            },
            "exit_strategy": {
                "primary_recommendation": {
                    "scenario": optimization_result.primary_recommendation.scenario.value,
                    "priority": optimization_result.primary_recommendation.priority,
                    "confidence": optimization_result.primary_recommendation.confidence,
                    "expected_return": optimization_result.primary_recommendation.expected_return,
                    "risk_score": optimization_result.primary_recommendation.risk_score,
                    "timing_urgency": optimization_result.primary_recommendation.timing_urgency,
                    "execution_notes": optimization_result.primary_recommendation.execution_notes,
                },
                "alternative_scenarios": [
                    {
                        "scenario": alt.scenario.value,
                        "priority": alt.priority,
                        "confidence": alt.confidence,
                        "expected_return": alt.expected_return,
                        "risk_score": alt.risk_score,
                    }
                    for alt in optimization_result.alternative_scenarios
                ],
                "optimization_confidence": optimization_result.optimization_confidence,
                "expected_outcomes": optimization_result.expected_outcomes,
            },
            "risk_management": {
                "take_profit_pct": strategy_data.take_profit_pct,
                "stop_loss_pct": strategy_data.stop_loss_pct,
                "trailing_stop_pct": strategy_data.trailing_stop_pct,
                "max_holding_days": strategy_data.max_holding_days,
                "min_holding_days": strategy_data.min_holding_days,
                "risk_mitigation_plan": optimization_result.risk_mitigation_plan,
                "monitoring_thresholds": optimization_result.monitoring_thresholds,
            },
            "market_assessment": optimization_result.market_assessment.value,
            "generation_metadata": {
                "command_version": "1.0.0",
                "base_path": str(self.base_path),
                "include_raw_data": args.include_raw_data,
                "current_price": args.current_price,
                "market_condition": market_condition.value
                if market_condition
                else None,
            },
        }

        return json.dumps(report, indent=2)

    def _generate_html_report(
        self, args: argparse.Namespace, market_condition: Optional[MarketCondition]
    ) -> str:
        """Generate HTML format report"""
        # Get markdown report first
        markdown_content = self._generate_markdown_report(args, market_condition)

        # Convert to HTML (basic conversion)
        # Note: For production, consider using a proper markdown-to-HTML converter
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sell Signal Report - {args.strategy}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{ color: #2c3e50; }}
        .highlight {{ background-color: #fff3cd; padding: 10px; border-radius: 4px; }}
        .alert {{ background-color: #f8d7da; padding: 10px; border-radius: 4px; color: #721c24; }}
        .success {{ background-color: #d1edff; padding: 10px; border-radius: 4px; color: #0c5460; }}
        pre {{ background-color: #f8f9fa; padding: 15px; border-radius: 4px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container">
        <pre>{markdown_content}</pre>
    </div>
</body>
</html>"""

        return html_content

    def _display_console_summary(self, strategy_identifier: str) -> None:
        """Display formatted console summary of the analysis"""
        try:
            # Get strategy data for summary
            strategy_data = self.aggregator.get_strategy_data(strategy_identifier)
            if not strategy_data:
                print("\n⚠️  Could not retrieve strategy data for console summary")
                return

            # Generate exit strategy recommendation
            exit_optimizer = ExitStrategyOptimizer()
            optimization_result = exit_optimizer.optimize_exit_strategy(strategy_data)

            print(f"\n{'='*70}")
            print(
                f"📊 {strategy_data.exit_signal} Signal Analysis for {strategy_data.strategy_name} Complete"
            )
            print(f"{'='*70}")

            # Key findings section
            print(f"\n🎯 **Key Findings:**")
            print(
                f"   • Current Signal: {self._format_signal_emoji(strategy_data.exit_signal)} **{strategy_data.exit_signal}**"
            )
            print(f"   • Confidence Level: {strategy_data.signal_confidence:.1f}%")
            print(
                f"   • Current P&L: {strategy_data.current_return*100:.2f}% unrealized gains"
            )
            print(
                f"   • Statistical Significance: {strategy_data.statistical_validity} (p-value: {strategy_data.p_value:.3f})"
            )
            print(f"   • Sample Size: {strategy_data.sample_size:,} observations")
            print(f"   • Risk Level: {self._assess_risk_level(strategy_data)}")

            # MFE/MAE Analysis
            if hasattr(strategy_data, "mfe") and hasattr(strategy_data, "mae"):
                print(f"   • Max Favorable Excursion: {strategy_data.mfe*100:.2f}%")
                print(f"   • Max Adverse Excursion: {strategy_data.mae*100:.2f}%")

            # Primary recommendation
            primary_rec = optimization_result.primary_recommendation
            print(f"\n🎯 **Primary Recommendation:**")
            print(
                f"   • Strategy: {primary_rec.scenario.value.replace('_', ' ').title()}"
            )
            print(f"   • Confidence: {primary_rec.confidence*100:.0f}%")
            print(f"   • Expected Return: {primary_rec.expected_return*100:.2f}%")
            print(f"   • Risk Score: {primary_rec.risk_score:.1f}/10")

            # Action items
            print(f"\n🚀 **Recommended Actions:**")
            if strategy_data.exit_signal == "SELL":
                print(f"   1. Prepare for position exit within 1-3 trading sessions")
                print(
                    f"   2. Set trailing stop at {strategy_data.trailing_stop_pct:.2f}% below peak"
                )
                print(f"   3. Hard stop loss at {strategy_data.stop_loss_pct:.2f}%")
                print(f"   4. Target profit at {strategy_data.take_profit_pct:.2f}%")
            elif strategy_data.exit_signal == "HOLD":
                print(f"   1. Continue monitoring position")
                print(
                    f"   2. Maintain trailing stop at {strategy_data.trailing_stop_pct:.2f}%"
                )
                print(
                    f"   3. Consider partial profit taking at {strategy_data.take_profit_pct*0.8:.2f}%"
                )
                print(f"   4. Review position if confidence drops below 60%")

            # Risk management
            print(f"\n⚠️  **Risk Management:**")
            print(f"   • Take Profit Target: {strategy_data.take_profit_pct:.2f}%")
            print(f"   • Stop Loss Limit: {strategy_data.stop_loss_pct:.2f}%")
            print(f"   • Trailing Stop: {strategy_data.trailing_stop_pct:.2f}%")
            print(f"   • Max Holding Period: {strategy_data.max_holding_days} days")

            # Footer
            print(
                f"\n📋 The comprehensive report includes statistical foundation, technical analysis,"
            )
            print(
                f"    multiple exit scenarios, and risk management framework for this position."
            )
            print(f"\n{'='*70}")

        except Exception as e:
            print(f"\n⚠️  Error displaying console summary: {e}")

    def _display_brief_summary(self, strategy_identifier: str) -> None:
        """Display brief console summary for stdout output"""
        try:
            # Get strategy data for summary
            strategy_data = self.aggregator.get_strategy_data(strategy_identifier)
            if not strategy_data:
                print("⚠️  Could not retrieve strategy data")
                return

            # Generate exit strategy recommendation
            exit_optimizer = ExitStrategyOptimizer()
            optimization_result = exit_optimizer.optimize_exit_strategy(strategy_data)
            primary_rec = optimization_result.primary_recommendation

            print(
                f"🎯 {self._format_signal_emoji(strategy_data.exit_signal)} {strategy_data.exit_signal} Signal: {strategy_data.strategy_name}"
            )
            print(
                f"📊 Confidence: {strategy_data.signal_confidence:.1f}% | P&L: {strategy_data.current_return*100:.2f}% | Risk: {self._assess_risk_level(strategy_data)}"
            )
            print(
                f"🚀 Recommendation: {primary_rec.scenario.value.replace('_', ' ').title()} ({primary_rec.confidence*100:.0f}% confidence)"
            )

            if hasattr(strategy_data, "mfe") and hasattr(strategy_data, "mae"):
                print(
                    f"📈 MFE: {strategy_data.mfe*100:.2f}% | MAE: {strategy_data.mae*100:.2f}%"
                )

        except Exception as e:
            print(f"⚠️  Error displaying brief summary: {e}")

    def _format_signal_emoji(self, signal: str) -> str:
        """Get emoji for signal type"""
        signal_emojis = {
            "SELL": "🚨",
            "STRONG_SELL": "🔴",
            "HOLD": "✅",
            "BUY": "🟢",
            "STRONG_BUY": "💚",
        }
        return signal_emojis.get(signal, "⚠️")

    def _assess_risk_level(self, strategy_data: StrategyData) -> str:
        """Assess overall risk level based on multiple factors"""
        risk_score = 0

        # Signal confidence factor
        if strategy_data.signal_confidence > 80:
            risk_score += 1
        elif strategy_data.signal_confidence < 60:
            risk_score += 3
        else:
            risk_score += 2

        # Statistical validity factor
        if strategy_data.statistical_validity == "HIGH":
            risk_score += 0
        elif strategy_data.statistical_validity == "MEDIUM":
            risk_score += 1
        else:
            risk_score += 2

        # Exit signal factor
        if strategy_data.exit_signal in ["SELL", "STRONG_SELL"]:
            risk_score += 2

        # Current return factor (if negative, add risk)
        if strategy_data.current_return < 0:
            risk_score += 2

        # Risk level assessment
        if risk_score <= 2:
            return "LOW"
        elif risk_score <= 4:
            return "MODERATE"
        else:
            return "HIGH"

    def _list_strategies(self) -> int:
        """List all available strategies"""
        try:
            strategies = self.aggregator.get_all_strategies()

            if not strategies:
                print("❌ No strategies found in live_signals data")
                return 1

            print(f"📊 Available Strategies ({len(strategies)} total):\n")

            # Group by signal type for better organization
            sell_strategies = []
            hold_strategies = []
            other_strategies = []

            for strategy in strategies:
                summary = self.aggregator.get_strategy_summary(strategy)
                if summary:
                    signal = summary.get("exit_signal", "UNKNOWN")
                    if signal == "SELL":
                        sell_strategies.append((strategy, summary))
                    elif signal == "HOLD":
                        hold_strategies.append((strategy, summary))
                    else:
                        other_strategies.append((strategy, summary))

            # Display SELL signals first (higher priority)
            if sell_strategies:
                print("🚨 SELL Signals:")
                for strategy, summary in sell_strategies:
                    confidence = summary.get("signal_confidence", 0)
                    ticker = summary.get("ticker", "UNK")
                    print(f"  ⚠️  {strategy} ({ticker}) - {confidence:.1f}% confidence")
                print()

            # Display HOLD signals
            if hold_strategies:
                print("✅ HOLD Signals:")
                for strategy, summary in hold_strategies:
                    confidence = summary.get("signal_confidence", 0)
                    ticker = summary.get("ticker", "UNK")
                    print(f"  📈 {strategy} ({ticker}) - {confidence:.1f}% confidence")
                print()

            # Display other signals
            if other_strategies:
                print("❓ Other Signals:")
                for strategy, summary in other_strategies:
                    signal = summary.get("exit_signal", "UNKNOWN")
                    ticker = summary.get("ticker", "UNK")
                    print(f"  📊 {strategy} ({ticker}) - {signal}")
                print()

            print(
                f"Total: {len(sell_strategies)} SELL, {len(hold_strategies)} HOLD, {len(other_strategies)} Other"
            )
            return 0

        except Exception as e:
            logger.error(f"Error listing strategies: {e}")
            return 1

    def _health_check(self) -> int:
        """Perform system health check"""
        try:
            print("🔍 Performing system health check...\n")

            issues = []
            warnings = []

            # Check data source files
            print("📁 Checking data sources:")

            required_files = [
                self.aggregator.statistical_csv,
                self.aggregator.statistical_json,
                self.aggregator.backtesting_json,
                self.aggregator.backtesting_csv,
            ]

            for file_path in required_files:
                if file_path.exists():
                    print(f"  ✅ {file_path.name}")
                else:
                    print(f"  ❌ {file_path.name} - MISSING")
                    issues.append(f"Missing required file: {file_path}")

            # Check strategy data integrity
            print(f"\n📊 Checking strategy data:")
            strategies = self.aggregator.get_all_strategies()

            if strategies:
                print(f"  ✅ Found {len(strategies)} strategies")

                # Sample a few strategies for validation
                sample_strategies = strategies[:3]
                valid_count = 0

                for strategy in sample_strategies:
                    data = self.aggregator.get_strategy_data(strategy)
                    if data and data.sample_size > 0:
                        valid_count += 1

                if valid_count == len(sample_strategies):
                    print(
                        f"  ✅ Strategy data validation passed ({valid_count}/{len(sample_strategies)})"
                    )
                else:
                    print(
                        f"  ⚠️  Strategy data validation issues ({valid_count}/{len(sample_strategies)})"
                    )
                    warnings.append("Some strategies have incomplete data")
            else:
                print("  ❌ No strategies found")
                issues.append("No strategies available for analysis")

            # Check system dependencies
            print(f"\n🔧 Checking system dependencies:")

            try:
                import pandas as pd

                print(f"  ✅ pandas {pd.__version__}")
            except ImportError:
                print("  ❌ pandas - NOT AVAILABLE")
                issues.append("pandas library not available")

            try:
                import polars as pl

                print(f"  ✅ polars {pl.__version__}")
            except ImportError:
                print("  ⚠️  polars - NOT AVAILABLE (optional)")
                warnings.append("polars library not available (optional)")

            # Summary
            print(f"\n📋 Health Check Summary:")
            if not issues and not warnings:
                print("  🎉 All systems operational!")
                return 0
            elif issues:
                print(f"  ❌ {len(issues)} critical issues found:")
                for issue in issues:
                    print(f"     • {issue}")
                if warnings:
                    print(f"  ⚠️  {len(warnings)} warnings:")
                    for warning in warnings:
                        print(f"     • {warning}")
                return 1
            else:
                print(f"  ⚠️  {len(warnings)} warnings (system functional):")
                for warning in warnings:
                    print(f"     • {warning}")
                return 0

        except Exception as e:
            logger.error(f"Error during health check: {e}")
            return 1

    def _validate_data(self) -> int:
        """Validate data integrity across all sources"""
        try:
            print("🔍 Validating data integrity...\n")

            # Load and validate each data source
            validation_results = []

            # Validate statistical CSV
            try:
                import pandas as pd

                df = pd.read_csv(self.aggregator.statistical_csv)
                validation_results.append(
                    {
                        "source": "statistical_analysis.csv",
                        "status": "✅ VALID",
                        "rows": len(df),
                        "columns": len(df.columns),
                        "issues": [],
                    }
                )
            except Exception as e:
                validation_results.append(
                    {
                        "source": "statistical_analysis.csv",
                        "status": "❌ INVALID",
                        "error": str(e),
                    }
                )

            # Validate statistical JSON
            try:
                with open(self.aggregator.statistical_json, "r") as f:
                    data = json.load(f)

                results_count = len(data.get("statistical_analysis_results", []))
                validation_results.append(
                    {
                        "source": "statistical_analysis.json",
                        "status": "✅ VALID",
                        "strategies": results_count,
                        "issues": [],
                    }
                )
            except Exception as e:
                validation_results.append(
                    {
                        "source": "statistical_analysis.json",
                        "status": "❌ INVALID",
                        "error": str(e),
                    }
                )

            # Display validation results
            all_valid = True
            for result in validation_results:
                print(f"📊 {result['source']}: {result['status']}")
                if result["status"].startswith("✅"):
                    if "rows" in result:
                        print(
                            f"   📈 {result['rows']} rows, {result['columns']} columns"
                        )
                    elif "strategies" in result:
                        print(f"   📈 {result['strategies']} strategies")
                else:
                    all_valid = False
                    print(f"   ❌ Error: {result.get('error', 'Unknown error')}")
                print()

            if all_valid:
                print("🎉 All data sources validated successfully!")
                return 0
            else:
                print(
                    "❌ Data validation failed. Check export files and regenerate if necessary."
                )
                return 1

        except Exception as e:
            logger.error(f"Error during data validation: {e}")
            return 1


def create_argument_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser"""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive sell signal reports from SPDS data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --strategy MA_SMA_78_82
  %(prog)s --strategy CRWD_EMA_5_21 --output reports/CRWD_analysis.md
  %(prog)s --strategy QCOM_SMA_49_66 --format json --include-raw-data
  %(prog)s --list-strategies
  %(prog)s --health-check
        """,
    )

    # Main operation modes
    operation_group = parser.add_mutually_exclusive_group()
    operation_group.add_argument(
        "--strategy",
        "-s",
        type=str,
        help="Strategy name (e.g., 'MA_SMA_78_82') or Position_UUID to analyze",
    )
    operation_group.add_argument(
        "--list-strategies",
        "-l",
        action="store_true",
        help="List all available strategies",
    )
    operation_group.add_argument(
        "--health-check", action="store_true", help="Perform system health check"
    )
    operation_group.add_argument(
        "--validate-data",
        action="store_true",
        help="Validate data integrity across all sources",
    )

    # Output options
    output_group = parser.add_argument_group("Output Options")
    output_group.add_argument(
        "--output", "-o", type=str, help="Output file path (default: stdout)"
    )
    output_group.add_argument(
        "--format",
        "-f",
        choices=["markdown", "json", "html"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    output_group.add_argument(
        "--include-raw-data",
        action="store_true",
        help="Include raw statistical data in appendices",
    )

    # Analysis options
    analysis_group = parser.add_argument_group("Analysis Options")
    analysis_group.add_argument(
        "--current-price", type=float, help="Current market price for enhanced analysis"
    )
    analysis_group.add_argument(
        "--market-condition",
        choices=["bullish", "bearish", "sideways", "volatile"],
        help="Current market condition assessment",
    )

    # System options
    system_group = parser.add_argument_group("System Options")
    system_group.add_argument(
        "--base-path", type=str, help="Base path to trading system directory"
    )
    system_group.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    return parser


def main() -> int:
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()

    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize command
    base_path = Path(args.base_path) if args.base_path else None
    command = TradeHistoryCloseCommand(base_path)

    # Execute command
    return command.execute(args)


if __name__ == "__main__":
    sys.exit(main())
