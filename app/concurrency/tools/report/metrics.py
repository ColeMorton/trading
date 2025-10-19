"""Metrics calculation utilities for concurrency analysis.

This module provides functionality for calculating various metrics for concurrency analysis reports.
"""

from typing import Any

# Import types from the parent module
from app.concurrency.tools.types import (
    ConcurrencyMetrics,
    EfficiencyMetrics,
    PortfolioMetrics,
    RiskMetrics,
    SignalMetrics,
    Strategy,
)


def calculate_ticker_metrics(strategies: list[Strategy]) -> dict[str, Any]:
    """Calculates ticker metrics from a list of strategies.

    Args:
        strategies (List[Strategy]): List of strategy objects.

    Returns:
        Dict[str, Any]: Dictionary of ticker metrics, with ticker symbols as keys.
    """
    ticker_metrics: dict[str, Any] = {}
    for strategy in strategies:
        ticker = strategy["parameters"]["ticker"]["value"]
        if ticker not in ticker_metrics:
            ticker_metrics[ticker] = {
                "id": ticker,
                # Remove performance object as requested
                "risk_metrics": {
                    k: v["value"] for k, v in strategy["risk_metrics"].items()
                },
                "efficiency": strategy["efficiency"],
                "signals": strategy["signals"],
            }

            # Original allocation values from CSV are preserved if present
            if "allocation" in strategy:
                ticker_metrics[ticker]["allocation"] = strategy["allocation"]

            # Add signal quality metrics if available
            if "signal_quality_metrics" in strategy:
                ticker_metrics[ticker]["signal_quality_metrics"] = strategy[
                    "signal_quality_metrics"
                ]
        else:
            # Aggregate values for existing ticker
            # Performance object removed as requested

            # Average risk metrics
            num_strategies = len(strategies)  # Dynamic
            for k in ticker_metrics[ticker]["risk_metrics"]:
                ticker_metrics[ticker]["risk_metrics"][k] = (
                    ticker_metrics[ticker]["risk_metrics"][k]
                    + strategy["risk_metrics"][k]["value"]
                ) / num_strategies

            # Average efficiency metrics
            for k in ticker_metrics[ticker]["efficiency"]:
                if isinstance(ticker_metrics[ticker]["efficiency"][k], dict):
                    if "value" in ticker_metrics[ticker]["efficiency"][k]:
                        ticker_metrics[ticker]["efficiency"][k]["value"] = (
                            ticker_metrics[ticker]["efficiency"][k]["value"]
                            + strategy["efficiency"][k]["value"]
                        ) / num_strategies
                    else:
                        for k2 in ticker_metrics[ticker]["efficiency"][k]:
                            ticker_metrics[ticker]["efficiency"][k][k2]["value"] = (
                                ticker_metrics[ticker]["efficiency"][k][k2]["value"]
                                + strategy["efficiency"][k][k2]["value"]
                            ) / num_strategies

            # Average signal metrics
            for k in ticker_metrics[ticker]["signals"]:
                if (
                    isinstance(ticker_metrics[ticker]["signals"][k], dict)
                    and "value" in ticker_metrics[ticker]["signals"][k]
                ):
                    ticker_metrics[ticker]["signals"][k]["value"] = (
                        ticker_metrics[ticker]["signals"][k]["value"]
                        + strategy["signals"][k]["value"]
                    ) / num_strategies
                elif isinstance(ticker_metrics[ticker]["signals"][k], dict):
                    for k2 in ticker_metrics[ticker]["signals"][k]:
                        ticker_metrics[ticker]["signals"][k][k2]["value"] = (
                            ticker_metrics[ticker]["signals"][k][k2]["value"]
                            + strategy["signals"][k][k2]["value"]
                        ) / num_strategies

            # Original allocation values from CSV are preserved if present
            if "allocation" in strategy:
                ticker_metrics[ticker]["allocation"] = strategy["allocation"]

    return ticker_metrics


def create_portfolio_metrics(
    stats: dict[str, Any], config: dict[str, Any] | None = None
) -> PortfolioMetrics:
    """Create portfolio metrics with the optimized structure.

    Args:
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        config (Dict[str, Any], optional): Configuration dictionary. Defaults to None.

    Returns:
        PortfolioMetrics: Portfolio metrics with the optimized structure
    """
    # Default config if none provided
    if config is None:
        config = {}
    concurrency: ConcurrencyMetrics = {
        "total_concurrent_periods": {
            "value": stats["total_concurrent_periods"],
            "description": "Number of periods with concurrent positions",
        },
        "concurrency_ratio": {
            "value": stats["concurrency_ratio"],
            "description": "Ratio of concurrent periods to total periods",
        },
        "exclusive_ratio": {
            "value": stats["exclusive_ratio"],
            "description": "Ratio of periods with exactly one strategy in position",
        },
        "inactive_ratio": {
            "value": stats["inactive_ratio"],
            "description": "Ratio of periods with no active strategies",
        },
        "avg_concurrent_strategies": {
            "value": stats["avg_concurrent_strategies"],
            "description": "Average number of concurrent strategies",
        },
        "max_concurrent_strategies": {
            "value": stats["max_concurrent_strategies"],
            "description": "Maximum number of concurrent strategies",
        },
    }

    efficiency: EfficiencyMetrics = {
        "efficiency_score": {
            "value": stats["efficiency_score"],
            "description": "Risk-Adjusted Performance",
        },
        "expectancy": {
            "value": stats.get("total_weighted_expectancy", stats["total_expectancy"]),
            "description": "Combined expectancy per trade across all strategies (allocation-weighted)",
        },
        "multipliers": {
            "diversification": {
                "value": stats["diversification_multiplier"],
                "description": "Multiplier effect from strategy diversification",
            },
            "independence": {
                "value": stats["independence_multiplier"],
                "description": "Multiplier effect from strategy independence",
            },
            "activity": {
                "value": stats["activity_multiplier"],
                "description": "Multiplier effect from strategy activity levels",
            },
        },
    }

    risk: RiskMetrics = {
        "portfolio_metrics": {
            "risk_concentration_index": {
                "value": stats["risk_concentration_index"],
                "description": "Measure of risk concentration",
            },
            "total_portfolio_risk": {
                "value": stats["risk_metrics"].get("total_portfolio_risk", 0.0),
                "description": "Overall portfolio risk measure",
            },
        },
        "combined_risk": {
            "var_95": {
                "value": stats["risk_metrics"].get("combined_var_95", 0.0),
                "description": "Combined Value at Risk (95% confidence)",
            },
            "cvar_95": {
                "value": stats["risk_metrics"].get("combined_cvar_95", 0.0),
                "description": "Combined Conditional Value at Risk (95% confidence)",
            },
            "var_99": {
                "value": stats["risk_metrics"].get("combined_var_99", 0.0),
                "description": "Combined Value at Risk (99% confidence)",
            },
            "cvar_99": {
                "value": stats["risk_metrics"].get("combined_cvar_99", 0.0),
                "description": "Combined Conditional Value at Risk (99% confidence)",
            },
        },
    }

    # Check if strategy relationships should be included
    include_relationships = True
    if (
        config
        and "REPORT_INCLUDES" in config
        and "STRATEGY_RELATIONSHIPS" in config["REPORT_INCLUDES"]
    ):
        include_relationships = config["REPORT_INCLUDES"]["STRATEGY_RELATIONSHIPS"]

    # Add strategy relationships if configured to include them
    if include_relationships:
        risk["strategy_relationships"] = {
            key: {"value": value, "description": f"Risk relationship metric: {key}"}
            for key, value in stats["risk_metrics"].items()
            if key.startswith("risk_overlap_")
        }

    # Use portfolio-level signal metrics from the root level
    signals: SignalMetrics = {
        "monthly_statistics": {
            "mean": {
                "value": stats["signal_metrics"]["mean_signals"],
                "description": "Average number of signals per month",
            },
            "median": {
                "value": stats["signal_metrics"]["median_signals"],
                "description": "Median number of signals per month",
            },
            "std_below": {
                "value": stats["signal_metrics"]["std_below_mean"],
                "description": "One standard deviation below mean signals",
            },
            "std_above": {
                "value": stats["signal_metrics"]["std_above_mean"],
                "description": "One standard deviation above mean signals",
            },
        },
        "summary": {
            "volatility": {
                "value": stats["signal_metrics"]["signal_volatility"],
                "description": "Standard deviation of monthly signals",
            },
            "max_monthly": {
                "value": stats["signal_metrics"]["max_monthly_signals"],
                "description": "Maximum signals in any month",
            },
            "min_monthly": {
                "value": stats["signal_metrics"]["min_monthly_signals"],
                "description": "Minimum signals in any month",
            },
            "total": {
                "value": stats["signal_metrics"]["total_signals"],
                "description": "Total number of signals across period",
            },
        },
    }

    # Add aggregate signal quality metrics if available
    portfolio_metrics: PortfolioMetrics = {
        "concurrency": concurrency,
        "efficiency": efficiency,
        "risk": risk,
        "signals": signals,
    }

    # Add aggregate signal quality metrics if available
    if (
        "signal_quality_metrics" in stats
        and "aggregate" in stats["signal_quality_metrics"]
    ):
        aggregate_metrics = stats["signal_quality_metrics"]["aggregate"]

        # Format the metrics in the standard format
        formatted_metrics = {}
        for key, value in aggregate_metrics.items():
            if isinstance(value, int | float):
                formatted_metrics[key] = {
                    "value": value,
                    "description": f"Aggregate {key.replace('_', ' ')}",
                }

        if formatted_metrics:
            portfolio_metrics["signal_quality"] = formatted_metrics

    return portfolio_metrics
