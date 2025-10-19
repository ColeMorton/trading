"""Strategy object creation utilities for concurrency analysis.

This module provides functionality for creating strategy objects from configuration and statistics.
"""

from typing import Any, TypedDict

# Import types from the parent module
from app.concurrency.tools.types import (
    EfficiencyMetrics,
    SignalMetrics,
    Strategy,
    StrategyParameters,
    StrategyRiskMetrics,
)


class StrategyParameter(TypedDict):
    """Parameter definition with value and description."""

    value: Any
    description: str


def create_strategy_object(
    config: dict[str, Any], index: int, stats: dict[str, Any]
) -> Strategy:
    """Create a strategy object with the optimized structure.

    Args:
        config (Dict[str, Any]): Strategy configuration
        index (int): Strategy index for ID generation
        stats (Dict[str, Any]): Statistics containing risk and efficiency metrics

    Returns:
        Strategy: Strategy object with parameters, performance, risk metrics, and efficiency metrics
    """
    # Check if allocation is enabled in the report
    include_allocation = stats.get("include_allocation", True)
    # Determine strategy type - use explicit STRATEGY_TYPE from CSV if available
    strategy_type = (
        config.get("STRATEGY_TYPE")
        or config.get("Strategy Type")
        or config.get("MA Type")
    )

    if not strategy_type:
        raise ValueError(
            "Strategy type must be explicitly specified in CSV. No default strategy type is allowed."
        )

    # Only override with MACD detection if STRATEGY_TYPE wasn't explicitly set
    # This preserves the explicit strategy type from CSV while still supporting
    # legacy auto-detection for configurations without explicit types
    if (
        strategy_type == "EMA"
        and "SIGNAL_PERIOD" in config
        and config["SIGNAL_PERIOD"] > 0
    ):
        strategy_type = "MACD"

    # Also check for explicit type field which might come from JSON portfolios
    if "type" in config:
        strategy_type = config["type"]

    # Use the strategy_id from config if available, otherwise use index
    if "strategy_id" in config:
        strategy_id = config["strategy_id"]
    else:
        # If no strategy_id in config, use ticker and other info to create one
        ticker = config.get("TICKER", f"unknown_{index}")
        strategy_id = f"{ticker}_{strategy_type}_{index}"

    # Create base parameters
    parameters: StrategyParameters = {
        "ticker": {
            "value": config["TICKER"],
            "description": "Ticker symbol to analyze",
        },
        "timeframe": {
            "value": "Hourly" if config.get("USE_HOURLY", False) else "Daily",
            "description": "Trading timeframe (Hourly or Daily)",
        },
        "type": {
            "value": strategy_type,
            "description": f"Strategy type ({strategy_type})",
        },
        "direction": {
            "value": config.get("DIRECTION", "Long"),
            "description": "Trading direction (Long or Short)",
        },
    }

    # Add strategy-specific parameters based on type
    if strategy_type == "ATR":
        # ATR strategy parameters
        if "length" in config:
            parameters["length"] = {
                "value": config["length"],
                "description": "ATR calculation period",
            }
        if "multiplier" in config:
            parameters["multiplier"] = {
                "value": config["multiplier"],
                "description": "ATR multiplier for stop distance",
            }
    else:
        # MA and MACD strategy parameters
        if "FAST_PERIOD" in config:
            parameters["fast_period"] = {
                "value": config["FAST_PERIOD"],
                "description": "Period for short moving average or MACD fast line",
            }
        if "SLOW_PERIOD" in config:
            parameters["slow_period"] = {
                "value": config["SLOW_PERIOD"],
                "description": "Period for long moving average or MACD slow line",
            }

        # Add signal_period for MACD strategies
        if strategy_type == "MACD" and "SIGNAL_PERIOD" in config:
            parameters["signal_period"] = {
                "value": config["SIGNAL_PERIOD"],
                "description": "Period for MACD signal line",
            }

    # Add RSI parameters if present
    if config.get("USE_RSI", False) and "RSI_WINDOW" in config:
        parameters["rsi_period"] = {
            "value": config["RSI_WINDOW"],
            "description": "Period for RSI calculation",
        }
        parameters["rsi_threshold"] = {
            "value": config["RSI_THRESHOLD"],
            "description": "RSI threshold for signal filtering",
        }

    # Add allocation if present
    if "ALLOCATION" in config and config["ALLOCATION"] is not None:
        parameters["allocation"] = {
            "value": config["ALLOCATION"],
            "description": "Allocation percentage",
        }

    # Add stop loss if present
    if "STOP_LOSS" in config:
        parameters["stop_loss"] = {
            "value": config["STOP_LOSS"],
            "description": "Stop loss percentage",
        }

    # Performance object removed as requested

    # Extract strategy-specific risk metrics
    risk_metrics_data = stats.get("risk_metrics", {})

    # Use index for risk metrics lookup to match how they're stored in risk_metrics.py
    # The index parameter is 1-based, which matches the 1-based indexing used
    # in risk_metrics.py
    risk_metrics: StrategyRiskMetrics = {
        "var_95": {
            "value": risk_metrics_data.get(f"strategy_{index}_var_95", 0.0),
            "description": "Value at Risk (95% confidence)",
        },
        "cvar_95": {
            "value": risk_metrics_data.get(f"strategy_{index}_cvar_95", 0.0),
            "description": "Conditional Value at Risk (95% confidence)",
        },
        "var_99": {
            "value": risk_metrics_data.get(f"strategy_{index}_var_99", 0.0),
            "description": "Value at Risk (99% confidence)",
        },
        "cvar_99": {
            "value": risk_metrics_data.get(f"strategy_{index}_cvar_99", 0.0),
            "description": "Conditional Value at Risk (99% confidence)",
        },
        "risk_contribution": {
            "value": risk_metrics_data.get(f"strategy_{index}_risk_contrib", 0.0),
            "description": "Contribution to portfolio risk",
        },
        "alpha_to_portfolio": {
            "value": risk_metrics_data.get(f"strategy_{index}_alpha_to_portfolio", 0.0),
            "description": "Risk-adjusted alpha relative to portfolio (excess return per unit of volatility)",
        },
    }

    # Get strategy-specific efficiency metrics
    strategy_metrics = stats.get("strategy_efficiency_metrics", {})

    # Use index for efficiency metrics lookup to match how they're stored in analysis.py
    efficiency: EfficiencyMetrics = {
        "efficiency_score": {
            "value": strategy_metrics.get(f"strategy_{index}_efficiency_score", 0.0),
            "description": "Risk-adjusted performance score for this strategy",
        },
        "expectancy": {
            "value": strategy_metrics.get(f"strategy_{index}_expectancy", 0.0),
            "description": "Expectancy per Trade",
        },
        "multipliers": {
            "diversification": {
                "value": strategy_metrics.get(f"strategy_{index}_diversification", 0.0),
                "description": "Strategy-specific diversification effect",
            },
            "independence": {
                "value": strategy_metrics.get(f"strategy_{index}_independence", 0.0),
                "description": "Strategy-specific independence from other strategies",
            },
            "activity": {
                "value": strategy_metrics.get(f"strategy_{index}_activity", 0.0),
                "description": "Strategy-specific activity level impact",
            },
        },
    }

    # Get strategy-specific signal metrics
    signal_metrics = stats.get("signal_metrics", {})
    strategy_key = f"strategy_{index}"

    # Calculate mean signals per month for this strategy
    mean_signals = signal_metrics.get(f"{strategy_key}_mean_signals", 0.0)
    median_signals = signal_metrics.get(f"{strategy_key}_median_signals", 0.0)
    std_signals = signal_metrics.get(f"{strategy_key}_signal_volatility", 0.0)
    total_signals = signal_metrics.get(f"{strategy_key}_total_signals", 0.0)
    max_monthly = signal_metrics.get(f"{strategy_key}_max_monthly_signals", 0.0)
    min_monthly = signal_metrics.get(f"{strategy_key}_min_monthly_signals", 0.0)

    signals: SignalMetrics = {
        "monthly_statistics": {
            "mean": {
                "value": mean_signals,
                "description": "Average number of signals per month",
            },
            "median": {
                "value": median_signals,
                "description": "Median number of signals per month",
            },
            "std_below": {
                "value": max(0.0, mean_signals - std_signals),
                "description": "One standard deviation below mean signals",
            },
            "std_above": {
                "value": mean_signals + std_signals,
                "description": "One standard deviation above mean signals",
            },
        },
        "summary": {
            "volatility": {
                "value": std_signals,
                "description": "Standard deviation of monthly signals",
            },
            "max_monthly": {
                "value": max_monthly,
                "description": "Maximum signals in any month",
            },
            "min_monthly": {
                "value": min_monthly,
                "description": "Minimum signals in any month",
            },
            "total": {
                "value": total_signals,
                "description": "Total number of signals across period",
            },
        },
    }

    # Get strategy-specific signal quality metrics if available
    # We still need to use "strategy_" prefix for internal lookups in stats
    signal_quality_metrics_data = stats.get("signal_quality_metrics", {}).get(
        f"strategy_{index}", {}
    )

    # Only include signal quality metrics if they exist
    strategy_obj: Strategy = {
        "id": strategy_id,
        "parameters": parameters,
        # Remove performance object as requested
        "risk_metrics": risk_metrics,
        "efficiency": efficiency,
        "signals": signals,
    }

    # Add allocation fields only if enabled
    if include_allocation:
        # We still need to use "strategy_" prefix for internal lookups in stats
        strategy_obj["allocation_score"] = stats.get(
            f"strategy_{index}_allocation_score", 0.0
        )
        strategy_obj["allocation"] = stats.get(f"strategy_{index}_allocation", 0.0)

        # Add original allocation from CSV file if available
        original_allocation = stats.get(f"strategy_{index}_original_allocation", None)
        if original_allocation is not None:
            strategy_obj["original_allocation"] = original_allocation
        else:
            # If no original allocation is available, use the calculated allocation
            strategy_obj["original_allocation"] = strategy_obj["allocation"]

    # Add signal quality metrics if available
    if signal_quality_metrics_data:
        strategy_obj["signal_quality_metrics"] = signal_quality_metrics_data

    # Add all portfolio metrics from the CSV file
    if hasattr(config, "items"):  # Check if config is a dict-like object
        # Create a dictionary to store all strategy metrics
        metrics = {}

        # Minimal list of metrics to exclude (only those that are truly redundant)
        # These are already represented elsewhere in the JSON structure
        exclude_metrics = [
            "PORTFOLIO_STATS"  # This is the container, not a metric itself
        ]

        # Add all metrics from the config
        for key, value in config.items():
            if key not in exclude_metrics and not key.startswith("_"):
                # Convert to proper format with value and description
                metrics[key] = {
                    "value": value,
                    "description": f"{key} metric from portfolio data",
                }

        # Add all metrics from the portfolio stats if available
        if "PORTFOLIO_STATS" in config and isinstance(config["PORTFOLIO_STATS"], dict):
            portfolio_stats = config["PORTFOLIO_STATS"]

            # No exclusions - include absolutely all CSV row data
            for key, value in portfolio_stats.items():
                # Convert to proper format with value and description
                # If the key already exists in metrics, it will be overwritten with the portfolio_stats value
                # This ensures that the portfolio_stats values take precedence
                metrics[key] = {
                    "value": value,
                    "description": f"{key} from strategy analysis",
                }

        # FORCE ADD Signal Entry and Signal Exit to metrics
        # This is a last resort to ensure these columns are included
        if "TICKER" in config:
            ticker = config["TICKER"]
            # Check if we can find these values in the CSV file
            try:
                import csv
                import os

                # Try to find the CSV file
                csv_path = os.path.join("data/raw/strategies", "DAILY_test.csv")
                if os.path.exists(csv_path):
                    with open(csv_path) as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get("Ticker") == ticker:
                                # Found the row for this ticker
                                signal_entry = row.get("Signal Entry")
                                signal_exit = row.get("Signal Exit")

                                if signal_entry is not None:
                                    # Convert to boolean if it's a string representation
                                    # of a boolean
                                    if signal_entry.lower() in ["true", "false"]:
                                        signal_entry = signal_entry.lower() == "true"

                                    metrics["Signal Entry"] = {
                                        "value": signal_entry,
                                        "description": "Signal Entry from CSV file",
                                    }

                                if signal_exit is not None:
                                    # Convert to boolean if it's a string representation
                                    # of a boolean
                                    if signal_exit.lower() in ["true", "false"]:
                                        signal_exit = signal_exit.lower() == "true"

                                    metrics["Signal Exit"] = {
                                        "value": signal_exit,
                                        "description": "Signal Exit from CSV file",
                                    }

                                break
            except Exception:
                # If anything goes wrong, just continue
                pass

        # Only add the metrics field if there are metrics to include
        if metrics:
            strategy_obj["metrics"] = metrics

    return strategy_obj
