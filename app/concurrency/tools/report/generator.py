"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from typing import Any, Callable, Dict, List

from app.concurrency.tools.report.metrics import (
    calculate_ticker_metrics,
    create_portfolio_metrics,
)

# Import from local modules
from app.concurrency.tools.report.strategy import create_strategy_object
from app.concurrency.tools.strategy_id import generate_strategy_id

# Import types from the parent module
from app.concurrency.tools.types import ConcurrencyReport


def generate_json_report(
    strategies: List[Dict[str, Any]],
    stats: Dict[str, Any],
    log: Callable[[str, str], None],
    config: Dict[str, Any],
    monte_carlo_results: Dict[str, Any] = None,
) -> ConcurrencyReport:
    """Generate a comprehensive JSON report of the concurrency analysis.

    Args:
        strategies (List[Dict[str, Any]]): List of strategy configurations
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        log (Callable[[str, str], None]): Logging function
        config (Dict[str, Any]): Configuration dictionary containing RATIO_BASED_ALLOCATION
        monte_carlo_results (Dict[str, Any], optional): Monte Carlo analysis results

    Returns:
        ConcurrencyReport: Complete report containing:
            - strategies: List of strategy details and parameters
            - portfolio_metrics: Dictionary of concurrency, efficiency, risk and signal metrics
                - monte_carlo: Monte Carlo parameter robustness results (if enabled)

    Raises:
        ValueError: If input data is invalid or missing required fields
        KeyError: If required statistics are missing
    """
    try:
        # Validate inputs
        if not strategies:
            log("No strategies provided", "error")
            raise ValueError("Strategies list cannot be empty")

        if not stats:
            log("No statistics provided", "error")
            raise ValueError("Statistics dictionary cannot be empty")

        log(f"Starting JSON report generation for {len(strategies)} strategies", "info")

        # Allocation scores feature has been removed
        log("Allocation scores feature has been removed", "info")

        # Ensure include_allocation is set to false
        stats["include_allocation"] = False

        # Validate required statistics
        required_stats = [
            "total_concurrent_periods",
            "concurrency_ratio",
            "exclusive_ratio",
            "inactive_ratio",
            "avg_concurrent_strategies",
            "max_concurrent_strategies",
            "efficiency_score",
            "total_expectancy",
            "diversification_multiplier",
            "independence_multiplier",
            "activity_multiplier",
            "risk_concentration_index",
            "signal_metrics",
            "risk_metrics",
        ]
        missing_stats = [stat for stat in required_stats if stat not in stats]
        if missing_stats:
            log(f"Missing required statistics: {missing_stats}", "error")
            raise KeyError(f"Missing required statistics: {missing_stats}")

        # Create strategy objects
        strategy_objects = []
        for idx, strategy in enumerate(strategies, 1):
            # Ensure strategy has a strategy_id
            if "strategy_id" not in strategy:
                try:
                    strategy_id = generate_strategy_id(strategy)
                    strategy["strategy_id"] = strategy_id
                    log(
                        f"Generated strategy ID for strategy {idx}: {strategy_id}",
                        "debug",
                    )
                except ValueError as e:
                    log(
                        f"Could not generate strategy ID for strategy {idx}: {str(e)}",
                        "warning",
                    )

            ticker = strategy.get("TICKER", "unknown")
            strategy_id = strategy.get("strategy_id", f"strategy_{idx}")
            log(
                f"Processing strategy {idx}/{len(strategies)}: {ticker} (ID: {strategy_id})",
                "info",
            )
            strategy_objects.append(create_strategy_object(strategy, idx, stats))

        # Create portfolio metrics
        log("Creating portfolio metrics", "info")
        portfolio_metrics = create_portfolio_metrics(stats, config)

        # Sort strategies by ID
        log("Sorting strategies by ID", "info")
        strategy_objects.sort(key=lambda x: x["id"])

        # Initialize report with portfolio metrics
        report: ConcurrencyReport = {"portfolio_metrics": portfolio_metrics}

        # Check if ticker metrics should be included in the report
        include_ticker_metrics = True
        if (
            "REPORT_INCLUDES" in config
            and "TICKER_METRICS" in config["REPORT_INCLUDES"]
        ):
            include_ticker_metrics = config["REPORT_INCLUDES"]["TICKER_METRICS"]

        # Only calculate and include ticker metrics if configured to do so
        if include_ticker_metrics:
            log("Calculating ticker metrics", "info")
            ticker_metrics = calculate_ticker_metrics(strategy_objects)
            report["ticker_metrics"] = ticker_metrics

        # Check if strategies should be included in the report
        include_strategies = True
        if "REPORT_INCLUDES" in config and "STRATEGIES" in config["REPORT_INCLUDES"]:
            include_strategies = config["REPORT_INCLUDES"]["STRATEGIES"]

        # Only include strategies if configured to do so
        if include_strategies:
            report["strategies"] = strategy_objects

        # Add Monte Carlo analysis results if available
        if monte_carlo_results and config.get("MC_INCLUDE_IN_REPORTS", False):
            log("Including Monte Carlo analysis in report", "info")

            # Add portfolio-level Monte Carlo metrics
            if (
                hasattr(monte_carlo_results, "__iter__")
                and len(monte_carlo_results) > 0
            ):
                # Calculate portfolio-level metrics from ticker results
                total_tickers = len(monte_carlo_results)
                stable_tickers = 0
                stability_scores = []

                strategy_results = {}
                for strategy_id, result in monte_carlo_results.items():
                    # Convert MonteCarloPortfolioResult to serializable format
                    strategy_data = {
                        "strategy_id": strategy_id,
                        "ticker": getattr(
                            result,
                            "ticker",
                            strategy_id.split("_")[0]
                            if "_" in strategy_id
                            else strategy_id,
                        ),
                        "strategy_stability_score": float(
                            getattr(result, "portfolio_stability_score", 0.0)
                        ),
                        "recommended_parameters": getattr(
                            result, "recommended_parameters", None
                        ),
                        "parameter_variations": [],
                        "analysis_metadata": getattr(result, "analysis_metadata", {}),
                    }

                    # Add parameter results if available
                    if (
                        hasattr(result, "parameter_results")
                        and result.parameter_results
                    ):
                        for param_result in result.parameter_results:
                            param_data = {
                                "parameter_combination": getattr(
                                    param_result, "parameter_combination", None
                                ),
                                "stability_score": float(
                                    getattr(param_result, "stability_score", 0.0)
                                ),
                                "parameter_robustness": float(
                                    getattr(param_result, "parameter_robustness", 0.0)
                                ),
                                "regime_consistency": float(
                                    getattr(param_result, "regime_consistency", 0.0)
                                ),
                                "is_stable": bool(
                                    getattr(param_result, "is_stable", False)
                                ),
                            }
                            strategy_data["parameter_variations"].append(param_data)

                            # Count stable strategies
                            if param_data["is_stable"]:
                                stable_tickers += 1
                                break  # Count strategy as stable if any parameter is stable

                    # Use strategy_id as key for individual strategy analysis
                    strategy_results[strategy_id] = strategy_data
                    stability_scores.append(strategy_data["strategy_stability_score"])

                # Add Monte Carlo metrics to portfolio_metrics
                report["portfolio_metrics"]["monte_carlo"] = {
                    "total_strategies_analyzed": total_tickers,  # More accurate naming
                    "stable_strategies_count": stable_tickers,
                    "stable_strategies_percentage": (
                        stable_tickers / total_tickers * 100
                    )
                    if total_tickers > 0
                    else 0.0,
                    "average_stability_score": sum(stability_scores)
                    / len(stability_scores)
                    if stability_scores
                    else 0.0,
                    "simulation_parameters": {
                        "num_simulations": config.get("MC_NUM_SIMULATIONS", 100),
                        "confidence_level": config.get("MC_CONFIDENCE_LEVEL", 0.95),
                        "max_parameters_tested": config.get(
                            "MC_MAX_PARAMETERS_TO_TEST", 10
                        ),
                    },
                    "strategy_results": strategy_results,
                    "description": "Parameter robustness analysis for individual strategies. Each strategy is tested with parameter variations to assess stability.",
                }

        log("Successfully generated JSON report", "info")
        return report

    except Exception as e:
        log(f"Error generating JSON report: {str(e)}", "error")
        raise
