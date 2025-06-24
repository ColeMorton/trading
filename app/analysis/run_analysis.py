#!/usr/bin/env python3
"""
Quantitative Analysis Runner

This script provides a command-line interface for running comprehensive
quantitative analysis on trading strategy data. It integrates with the
existing concurrency analysis framework.

Usage:
    python app/analysis/run_analysis.py
    python app/analysis/run_analysis.py --export-charts
    python app/analysis/run_analysis.py --monte-carlo-sims 50000
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.analysis.quantitative_analysis import QuantitativeAnalyzer
from app.tools.logging_context import logging_context


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Quantitative Analysis for Trading Strategies"
    )

    parser.add_argument(
        "--base-dir",
        type=str,
        default=None,
        help="Base directory for analysis (defaults to project root)",
    )

    parser.add_argument(
        "--export-charts",
        action="store_true",
        help="Export correlation and performance charts",
    )

    parser.add_argument(
        "--monte-carlo-sims",
        type=int,
        default=10000,
        help="Number of Monte Carlo simulations (default: 10000)",
    )

    parser.add_argument(
        "--output-format",
        choices=["txt", "json", "both"],
        default="both",
        help="Output format for reports (default: both)",
    )

    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def create_charts(analyzer: QuantitativeAnalyzer) -> bool:
    """Create and save analysis charts"""
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns

        # Set style
        try:
            plt.style.use("seaborn-v0_8")
        except:
            plt.style.use("default")
        sns.set_palette("husl")

        charts_dir = analyzer.output_dir / "charts"
        charts_dir.mkdir(exist_ok=True)

        # Correlation heatmap for existing strategies
        if analyzer.trades_data is not None:
            correlation_data = analyzer.analyze_portfolio_correlation(
                analyzer.trades_data
            )

            if not correlation_data.empty:
                plt.figure(figsize=(12, 10))
                sns.heatmap(
                    correlation_data, annot=True, cmap="RdYlBu_r", center=0, fmt=".2f"
                )
                plt.title("Strategy Metrics Correlation Matrix - Existing Portfolio")
                plt.tight_layout()
                plt.savefig(
                    charts_dir / "existing_correlation_matrix.png",
                    dpi=300,
                    bbox_inches="tight",
                )
                plt.close()

                print(
                    f"Correlation matrix saved to: {charts_dir / 'existing_correlation_matrix.png'}"
                )

        # Performance comparison chart
        if analyzer.trades_data is not None and analyzer.incoming_data is not None:
            existing_metrics = analyzer.calculate_strategy_metrics(analyzer.trades_data)
            incoming_metrics = analyzer.calculate_strategy_metrics(
                analyzer.incoming_data
            )

            # Risk-Return scatter plot
            plt.figure(figsize=(14, 8))

            # Existing strategies
            existing_returns = [m.annualized_return * 100 for m in existing_metrics]
            existing_volatility = [
                m.annualized_volatility * 100 for m in existing_metrics
            ]

            plt.scatter(
                existing_volatility,
                existing_returns,
                alpha=0.7,
                s=100,
                label="Existing Strategies",
                color="blue",
            )

            # Incoming strategies
            incoming_returns = [m.annualized_return * 100 for m in incoming_metrics]
            incoming_volatility = [
                m.annualized_volatility * 100 for m in incoming_metrics
            ]

            plt.scatter(
                incoming_volatility,
                incoming_returns,
                alpha=0.7,
                s=100,
                label="Incoming Strategies",
                color="red",
            )

            plt.xlabel("Annualized Volatility (%)")
            plt.ylabel("Annualized Return (%)")
            plt.title("Risk-Return Profile: Existing vs Incoming Strategies")
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(
                charts_dir / "risk_return_comparison.png", dpi=300, bbox_inches="tight"
            )
            plt.close()

            print(
                f"Risk-return comparison saved to: {charts_dir / 'risk_return_comparison.png'}"
            )

        return True

    except ImportError:
        print("Matplotlib/Seaborn not available. Skipping chart creation.")
        return False
    except Exception as e:
        print(f"Error creating charts: {str(e)}")
        return False


def run_comprehensive_analysis(args):
    """Run the comprehensive quantitative analysis"""

    log_level = "DEBUG" if args.verbose else "INFO"

    with logging_context(
        module_name="quantitative_analysis",
        log_file="quantitative_analysis.log",
        level=log_level,
    ) as log:
        log("Starting comprehensive quantitative analysis...", "info")

        try:
            # Initialize analyzer
            analyzer = QuantitativeAnalyzer(base_dir=args.base_dir)
            log("Analyzer initialized successfully", "info")

            # Load data
            log("Loading strategy data...", "info")
            if not analyzer.load_data():
                log("Failed to load required data files", "error")
                return False

            log("Data loaded successfully", "info")

            # Generate comprehensive report
            log("Generating comprehensive analysis report...", "info")
            report = analyzer.generate_comprehensive_report()

            # Save report based on output format
            if args.output_format in ["txt", "both"]:
                report_path = analyzer.save_report(report)
                log(f"Text report saved to: {report_path}", "info")

                # Display report to console
                print("\n" + "=" * 80)
                print("QUANTITATIVE ANALYSIS REPORT")
                print("=" * 80)
                print(report)

            # Export JSON metrics
            if args.output_format in ["json", "both"]:
                metrics_path = analyzer.export_metrics_to_json()
                log(f"JSON metrics exported to: {metrics_path}", "info")

            # Create charts if requested
            if args.export_charts:
                log("Creating analysis charts...", "info")
                if create_charts(analyzer):
                    log("Charts created successfully", "info")
                else:
                    log("Chart creation failed or skipped", "warning")

            # Run Monte Carlo analysis with custom simulation count
            if analyzer.trades_data is not None:
                log(
                    f"Running Monte Carlo analysis with {args.monte_carlo_sims} simulations...",
                    "info",
                )
                existing_metrics = analyzer.calculate_strategy_metrics(
                    analyzer.trades_data
                )
                mc_results = analyzer.run_monte_carlo_analysis(
                    existing_metrics, num_simulations=args.monte_carlo_sims
                )

                if mc_results:
                    log("Monte Carlo analysis completed", "info")
                    print(
                        f"\nMonte Carlo Results ({args.monte_carlo_sims} simulations):"
                    )
                    print(
                        f"Expected Portfolio Value: {mc_results['mean_final_value']:.3f}"
                    )
                    print(f"95% Confidence Interval: {mc_results['var_95']:.3f}")
                    print(
                        f"Probability of Loss: {mc_results['probability_of_loss']*100:.1f}%"
                    )
                else:
                    log("Monte Carlo analysis failed", "warning")

            log("Quantitative analysis completed successfully", "info")
            return True

        except Exception as e:
            log(f"Error in quantitative analysis: {str(e)}", "error")
            return False


def main():
    """Main entry point"""
    args = parse_arguments()

    print("Comprehensive Quantitative Analysis for Trading Strategies")
    print("=" * 60)
    print(f"Monte Carlo Simulations: {args.monte_carlo_sims}")
    print(f"Output Format: {args.output_format}")
    print(f"Export Charts: {args.export_charts}")
    print("=" * 60)

    success = run_comprehensive_analysis(args)

    if success:
        print("\n✓ Analysis completed successfully!")
        print("\nFiles generated:")
        print("- Comprehensive analysis report (TXT)")
        print("- Detailed metrics export (JSON)")
        if args.export_charts:
            print("- Correlation matrices and performance charts (PNG)")
        return 0
    else:
        print("\n✗ Analysis failed. Check logs for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
