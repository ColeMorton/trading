"""
Runner Module for Concurrency Analysis.

This module contains the main execution logic for running concurrency analysis
across multiple trading strategies.
"""

import json
from pathlib import Path
from typing import Any, Callable, Dict, List

import numpy as np

from app.concurrency.tools.analysis import analyze_concurrency
from app.concurrency.tools.optimization_report import (
    generate_optimization_report,
    save_optimization_report,
)
from app.concurrency.tools.permutation import find_optimal_permutation
from app.concurrency.tools.report import generate_json_report
from app.concurrency.tools.strategy_id import generate_strategy_id
from app.concurrency.tools.strategy_processor import process_strategies
from app.concurrency.tools.types import ConcurrencyConfig
from app.concurrency.tools.visualization import plot_concurrency
from app.tools.portfolio import StrategyConfig, load_portfolio
from app.tools.setup_logging import setup_logging


# Custom JSON encoder to handle NumPy types and None values
class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy data types and None values."""

    def default(self, obj):
        if obj is None:
            return 1  # Convert None to 1 for best_horizon (default horizon)
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


def get_portfolio_path(config: ConcurrencyConfig) -> Path:
    """Get the full path to the portfolio file.

    Args:
        config (ConcurrencyConfig): Configuration dictionary containing PORTFOLIO path

    Returns:
        Path: Full path to the portfolio file (.json or .csv)
    """
    # Check if the path is already resolved (contains directory separators)
    if "/" in config["PORTFOLIO"] or "\\" in config["PORTFOLIO"]:
        return Path(config["PORTFOLIO"])

    # Otherwise resolve it
    from app.tools.portfolio.paths import resolve_portfolio_path

    return resolve_portfolio_path(config["PORTFOLIO"], config.get("BASE_DIR"))


def save_json_report(
    report: Dict[str, Any], config: ConcurrencyConfig, log: Callable[[str, str], None]
) -> Path:
    """Save JSON report to file.

    Args:
        report (Dict[str, Any]): Report data to save
        config (ConcurrencyConfig): Configuration dictionary
        log (Callable[[str, str], None]): Logging function

    Returns:
        Path: Path where report was saved

    Raises:
        IOError: If saving fails
    """
    try:
        # Ensure the json/concurrency directory exists
        json_dir = Path("json/concurrency")
        json_dir.mkdir(parents=True, exist_ok=True)

        # Get the portfolio filename without extension
        portfolio_filename = Path(config["PORTFOLIO"]).stem
        report_filename = f"{portfolio_filename}.json"

        # Save the report
        report_path = json_dir / report_filename
        log(f"Saving JSON report to {report_path}", "info")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=4, cls=NumpyEncoder)

        log(f"JSON report saved to {report_path}", "info")
        return report_path

    except Exception as e:
        log(f"Error saving JSON report: {str(e)}", "error")
        raise IOError(f"Failed to save report: {str(e)}")


def run_analysis(
    strategies: List[StrategyConfig],
    log: Callable[[str, str], None],
    config: ConcurrencyConfig,
) -> bool:
    """Run concurrency analysis across multiple strategies.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations to analyze
        log: Callable for logging messages
        config: Configuration dictionary

    Returns:
        bool: True if analysis successful

    Raises:
        Exception: If analysis fails at any stage
    """
    try:
        # Check if optimization is enabled
        optimize = config.get("OPTIMIZE", False)
        optimize_min_strategies = config.get("OPTIMIZE_MIN_STRATEGIES", 3)
        optimize_max_permutations = config.get("OPTIMIZE_MAX_PERMUTATIONS", None)

        # Allocation feature is deprecated
        log("Allocation scores feature is deprecated", "info")

        # Ensure all strategies have strategy_id
        updated_strategies = []
        for i, strategy in enumerate(strategies):
            # Create a copy to avoid modifying the original
            updated_strategy = strategy.copy()

            # Generate and assign strategy ID if not already present
            if "strategy_id" not in updated_strategy:
                try:
                    strategy_id = generate_strategy_id(updated_strategy)
                    updated_strategy["strategy_id"] = strategy_id
                    log(
                        f"Generated strategy ID for strategy {i+1}: {strategy_id}",
                        "debug",
                    )
                except ValueError as e:
                    log(
                        f"Could not generate strategy ID for strategy {i+1}: {str(e)}",
                        "warning",
                    )
                    # Use a fallback ID based on index
                    updated_strategy["strategy_id"] = f"strategy_{i+1}"

            updated_strategies.append(updated_strategy)

        # Process strategies and get data for all strategies
        log("Processing strategy data for all strategies", "info")
        strategy_data, updated_strategies = process_strategies(updated_strategies, log)

        # Analyze concurrency for all strategies
        log("Running concurrency analysis for all strategies", "info")

        # Pass the ALLOCATION flag to each strategy's config
        for strategy in updated_strategies:
            if "GLOBAL_CONFIG" not in strategy:
                strategy["GLOBAL_CONFIG"] = {}
            if "REPORT_INCLUDES" not in strategy["GLOBAL_CONFIG"]:
                strategy["GLOBAL_CONFIG"]["REPORT_INCLUDES"] = {}
            # Allocation flag is no longer needed

        all_stats, all_aligned_data = analyze_concurrency(
            strategy_data, updated_strategies, log
        )

        # Log statistics for all strategies
        log("Logging analysis statistics for all strategies", "info")
        log(f"Overall concurrency statistics:")
        log(f"Total concurrent periods: {all_stats['total_concurrent_periods']}")
        log(f"Concurrency Ratio: {all_stats['concurrency_ratio']:.2f}")
        log(f"Exclusive Ratio: {all_stats['exclusive_ratio']:.2f}")
        log(f"Inactive Ratio: {all_stats['inactive_ratio']:.2f}")
        log(
            f"Average concurrent strategies: {all_stats['avg_concurrent_strategies']:.2f}"
        )
        log(f"Max concurrent strategies: {all_stats['max_concurrent_strategies']}")
        log(f"Risk Concentration Index: {all_stats['risk_concentration_index']}")
        log(f"Risk-Adjusted Efficiency Score: {all_stats['efficiency_score']:.2f}")

        # Log risk metrics
        log(f"\nRisk Metrics:")
        for key, value in all_stats["risk_metrics"].items():
            if isinstance(value, float):
                log(f"{key}: {value:.4f}")
            else:
                log(f"{key}: {value}")

        # Generate and save JSON report for all strategies
        log("Generating JSON report for all strategies", "info")
        all_report = generate_json_report(updated_strategies, all_stats, log, config)
        save_json_report(all_report, config, log)

        # If optimization is enabled, run permutation analysis
        if optimize:
            log("OPTIMIZE flag is TRUE - Running permutation analysis", "info")
            log(
                "Note: Optimization uses risk-adjusted efficiency score that includes both structural components and performance metrics",
                "info",
            )
            log(
                "Using equal allocations for all strategies in each permutation to ensure fair comparison",
                "info",
            )

            if optimize_min_strategies:
                log(
                    f"Minimum strategies per permutation: {optimize_min_strategies}",
                    "info",
                )
            if optimize_max_permutations:
                log(
                    f"Maximum permutations to analyze: {optimize_max_permutations}",
                    "info",
                )

            try:
                # Find optimal permutation
                (
                    optimal_strategies,
                    optimal_stats,
                    optimal_aligned_data,
                ) = find_optimal_permutation(
                    updated_strategies,
                    process_strategies,
                    analyze_concurrency,
                    log,
                    min_strategies=optimize_min_strategies,
                    max_permutations=optimize_max_permutations,
                )

                # Log optimal strategies
                log("Optimal strategy combination found:", "info")
                for i, strategy in enumerate(optimal_strategies):
                    strategy_id = strategy.get("strategy_id", None)
                    ticker = strategy.get("TICKER", "unknown")
                    if strategy_id:
                        log(f"  {i+1}. {ticker} (ID: {strategy_id})", "info")
                    else:
                        log(f"  {i+1}. {ticker}", "info")

                # Log comparison
                log("Comparison of optimal vs. all strategies:", "info")
                log(
                    f"  All strategies risk-adjusted efficiency: {all_stats['efficiency_score']:.4f}",
                    "info",
                )
                log(
                    f"  Optimal combination risk-adjusted efficiency: {optimal_stats['efficiency_score']:.4f}",
                    "info",
                )
                improvement = (
                    (optimal_stats["efficiency_score"] - all_stats["efficiency_score"])
                    / all_stats["efficiency_score"]
                    * 100
                )
                log(f"  Improvement: {improvement:.2f}%", "info")

                # Generate optimization report
                optimization_report = generate_optimization_report(
                    updated_strategies,
                    all_stats,
                    optimal_strategies,
                    optimal_stats,
                    config,
                    log,
                )

                # Save optimization report
                save_optimization_report(optimization_report, config, log)

                # Generate and save JSON report for optimal strategies
                log("Generating JSON report for optimal strategy combination", "info")
                optimal_report = generate_json_report(
                    optimal_strategies, optimal_stats, log, config
                )

                # Save report with "optimal" suffix
                portfolio_filename = Path(config["PORTFOLIO"]).stem
                optimal_report_filename = f"{portfolio_filename}_optimal.json"
                json_dir = Path("json/concurrency")
                json_dir.mkdir(parents=True, exist_ok=True)
                optimal_report_path = json_dir / optimal_report_filename
                with open(optimal_report_path, "w") as f:
                    json.dump(optimal_report, f, indent=4, cls=NumpyEncoder)

                log(f"Optimization complete. Reports saved.", "info")

            except Exception as e:
                log(f"Error during optimization: {str(e)}", "error")
                log("Continuing with standard analysis results", "info")

        # Create visualization if enabled (using all strategies results)
        if config["VISUALIZATION"]:
            log("Creating visualization", "info")
            fig = plot_concurrency(all_aligned_data, all_stats, updated_strategies, log)
            fig.show()
            log("Visualization displayed", "info")

        log("Unified concurrency analysis completed successfully", "info")
        return True

    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        raise


def main(config: ConcurrencyConfig) -> bool:
    """Main entry point for concurrency analysis.

    Args:
        config (ConcurrencyConfig): Configuration dictionary containing PORTFOLIO path
            (supports both .json and .csv files)

    Returns:
        bool: True if analysis successful
    """
    try:
        log, log_close, _, _ = setup_logging(
            module_name="concurrency", log_file="concurrency_analysis.log"
        )

        log("Starting concurrency analysis", "info")

        # Load portfolio from JSON or CSV
        log("Loading portfolio configuration", "info")

        # Resolve the portfolio path
        portfolio_path = get_portfolio_path(config)
        portfolio_filename = portfolio_path.name

        # Load the portfolio using the filename
        log(f"Loading portfolio from: {portfolio_filename}", "info")
        strategies = load_portfolio(portfolio_filename, log, config)

        # Run analysis
        log("Running analysis", "info")
        result = run_analysis(strategies, log, config)

        log("Analysis completed", "info")
        log_close()
        return result

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
