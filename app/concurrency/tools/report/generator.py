"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from collections.abc import Callable
from typing import Any

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
    strategies: list[dict[str, Any]],
    stats: dict[str, Any],
    log: Callable[[str, str], None],
    config: dict[str, Any],
    monte_carlo_results: dict[str, Any] | None = None,
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
            msg = "Strategies list cannot be empty"
            raise ValueError(msg)

        if not stats:
            log("No statistics provided", "error")
            msg = "Statistics dictionary cannot be empty"
            raise ValueError(msg)

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
            msg = f"Missing required statistics: {missing_stats}"
            raise KeyError(msg)

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
                        f"Could not generate strategy ID for strategy {idx}: {e!s}",
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
                    strategy_data: dict[str, Any] = {
                        "strategy_id": strategy_id,
                        "ticker": getattr(
                            result,
                            "ticker",
                            (
                                strategy_id.split("_")[0]
                                if "_" in strategy_id
                                else strategy_id
                            ),
                        ),
                        "strategy_stability_score": float(
                            getattr(result, "portfolio_stability_score", 0.0),
                        ),
                        "recommended_parameters": getattr(
                            result,
                            "recommended_parameters",
                            None,
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
                                    param_result,
                                    "parameter_combination",
                                    None,
                                ),
                                "stability_score": float(
                                    getattr(param_result, "stability_score", 0.0),
                                ),
                                "parameter_robustness": float(
                                    getattr(param_result, "parameter_robustness", 0.0),
                                ),
                                "regime_consistency": float(
                                    getattr(param_result, "regime_consistency", 0.0),
                                ),
                                "is_stable": bool(
                                    getattr(param_result, "is_stable", False),
                                ),
                            }
                            strategy_data["parameter_variations"].append(param_data)

                            # Count stable strategies
                            if param_data["is_stable"]:
                                stable_tickers += 1
                                break  # Count strategy as stable if any parameter is stable

                    # Enhance recommended_parameters with detailed metrics
                    if strategy_data["recommended_parameters"] is not None:
                        # Find the matching parameter result for recommended parameters
                        recommended_details = None
                        for param_data in strategy_data["parameter_variations"]:
                            if (
                                param_data["parameter_combination"]
                                == strategy_data["recommended_parameters"]
                            ):
                                recommended_details = param_data
                                break

                        # If no exact match found, search in raw parameter_results
                        if recommended_details is None and hasattr(
                            result,
                            "parameter_results",
                        ):
                            for param_result in result.parameter_results:
                                if (
                                    getattr(param_result, "parameter_combination", None)
                                    == strategy_data["recommended_parameters"]
                                ):
                                    recommended_details = {
                                        "parameter_combination": getattr(
                                            param_result,
                                            "parameter_combination",
                                            None,
                                        ),
                                        "stability_score": float(
                                            getattr(
                                                param_result,
                                                "stability_score",
                                                0.0,
                                            ),
                                        ),
                                        "parameter_robustness": float(
                                            getattr(
                                                param_result,
                                                "parameter_robustness",
                                                0.0,
                                            ),
                                        ),
                                        "regime_consistency": float(
                                            getattr(
                                                param_result,
                                                "regime_consistency",
                                                0.0,
                                            ),
                                        ),
                                        "is_stable": bool(
                                            getattr(param_result, "is_stable", False),
                                        ),
                                    }
                                    break

                        # Transform recommended_parameters from simple tuple to detailed object
                        if recommended_details:
                            # Validate that all required metrics are present
                            required_metrics = [
                                "stability_score",
                                "parameter_robustness",
                                "regime_consistency",
                                "is_stable",
                            ]
                            missing_metrics = [
                                metric
                                for metric in required_metrics
                                if metric not in recommended_details
                            ]

                            if missing_metrics:
                                log(
                                    f"Warning: Recommended parameters for {strategy_id} missing metrics: {missing_metrics}",
                                    "warning",
                                )

                            # Calculate composite score for validation
                            composite_score = (
                                recommended_details.get("stability_score", 0.0) * 0.4
                                + recommended_details.get("parameter_robustness", 0.0)
                                * 0.4
                                + recommended_details.get("regime_consistency", 0.0)
                                * 0.2
                            )

                            strategy_data["recommended_parameters"] = {
                                "parameters": strategy_data["recommended_parameters"],
                                "stability_score": recommended_details[
                                    "stability_score"
                                ],
                                "parameter_robustness": recommended_details[
                                    "parameter_robustness"
                                ],
                                "regime_consistency": recommended_details[
                                    "regime_consistency"
                                ],
                                "is_stable": recommended_details["is_stable"],
                                "composite_score": round(composite_score, 6),
                                "selection_reason": "Highest weighted composite score (stability*0.4 + robustness*0.4 + consistency*0.2)",
                                "validated": True,
                            }
                            log(
                                f"Enhanced recommended_parameters for {strategy_id} with detailed metrics (composite score: {composite_score:.4f})",
                                "debug",
                            )
                        else:
                            # Keep simple format if no details found, but add warning and validation flag
                            log(
                                f"Warning: No detailed metrics found for recommended parameters {strategy_data['recommended_parameters']} in strategy {strategy_id}",
                                "warning",
                            )
                            # Convert to structured format even without details
                            strategy_data["recommended_parameters"] = {
                                "parameters": strategy_data["recommended_parameters"],
                                "stability_score": None,
                                "parameter_robustness": None,
                                "regime_consistency": None,
                                "is_stable": None,
                                "composite_score": None,
                                "selection_reason": "Data unavailable - no matching parameter analysis found",
                                "validated": False,
                            }

                    # Store for adding to individual strategies
                    strategy_results[strategy_id] = strategy_data
                    stability_scores.append(strategy_data["strategy_stability_score"])

                # Add Monte Carlo results to individual strategies
                if include_strategies and "strategies" in report:
                    for strategy_obj in report["strategies"]:
                        strategy_id = strategy_obj.get("id")
                        if strategy_id in strategy_results:
                            strategy_obj["monte_carlo"] = strategy_results[strategy_id]
                            log(
                                f"Added Monte Carlo results to strategy {strategy_id}",
                                "debug",
                            )

                # Add portfolio-level Monte Carlo summary (without strategy_results)
                report["portfolio_metrics"]["monte_carlo"] = {
                    "total_strategies_analyzed": total_tickers,
                    "stable_strategies_count": stable_tickers,
                    "stable_strategies_percentage": (
                        (stable_tickers / total_tickers * 100)
                        if total_tickers > 0
                        else 0.0
                    ),
                    "average_stability_score": (
                        sum(stability_scores) / len(stability_scores)
                        if stability_scores
                        else 0.0
                    ),
                    "simulation_parameters": {
                        "num_simulations": config.get("MC_NUM_SIMULATIONS", 100),
                        "confidence_level": config.get("MC_CONFIDENCE_LEVEL", 0.95),
                        "max_parameters_tested": config.get(
                            "MC_MAX_PARAMETERS_TO_TEST",
                            10,
                        ),
                    },
                    "description": "Parameter robustness analysis summary for portfolio. Individual strategy results are nested within each strategy object.",
                }

        log("Successfully generated JSON report", "info")
        return report

    except Exception as e:
        log(f"Error generating JSON report: {e!s}", "error")
        raise
