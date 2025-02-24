from typing import List, Dict, Any, Callable, TypedDict, NotRequired, Union
"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from typing import List, Dict, Any, Callable, TypedDict, NotRequired
from pathlib import Path

class StrategyParameter(TypedDict):
    """Parameter definition with value and description."""
    value: Any
    description: str

class StrategyParameters(TypedDict):
    """Strategy parameters with descriptions."""
    ticker: StrategyParameter
    timeframe: StrategyParameter
    type: StrategyParameter
    direction: StrategyParameter
    short_window: StrategyParameter
    long_window: StrategyParameter
    signal_window: NotRequired[StrategyParameter]
    stop_loss: NotRequired[StrategyParameter]
    rsi_period: NotRequired[StrategyParameter]
    rsi_threshold: NotRequired[StrategyParameter]

class StrategyPerformance(TypedDict):
    """Strategy performance metrics."""
    expectancy_per_month: StrategyParameter

class StrategyRiskMetrics(TypedDict):
    """Strategy-specific risk metrics."""
    var_95: StrategyParameter
    cvar_95: StrategyParameter
    var_99: StrategyParameter
    cvar_99: StrategyParameter
    risk_contribution: StrategyParameter
    alpha: StrategyParameter

class EfficiencyMultipliers(TypedDict):
    """Efficiency multiplier metrics."""
    diversification: StrategyParameter
    independence: StrategyParameter
    activity: StrategyParameter

class EfficiencyMetrics(TypedDict):
    """Strategy efficiency metrics."""
    efficiency_score: StrategyParameter
    total_expectancy: StrategyParameter
    multipliers: EfficiencyMultipliers

class SignalMonthlyStats(TypedDict):
    """Monthly signal statistics."""
    mean: StrategyParameter
    median: StrategyParameter
    std_below: StrategyParameter
    std_above: StrategyParameter

class SignalSummary(TypedDict):
    """Signal summary statistics."""
    volatility: StrategyParameter
    max_monthly: StrategyParameter
    min_monthly: StrategyParameter
    total: StrategyParameter

class SignalMetrics(TypedDict):
    """Complete signal metrics."""
    monthly_statistics: SignalMonthlyStats
    summary: SignalSummary

class Strategy(TypedDict):
    """Complete strategy definition."""
    id: str
    parameters: StrategyParameters
    performance: StrategyPerformance
    risk_metrics: StrategyRiskMetrics
    efficiency: EfficiencyMetrics
    signals: SignalMetrics
    allocation_score: StrategyParameter

class ConcurrencyMetrics(TypedDict):
    """Concurrency analysis metrics."""
    total_concurrent_periods: StrategyParameter
    concurrency_ratio: StrategyParameter
    exclusive_ratio: StrategyParameter
    inactive_ratio: StrategyParameter
    avg_concurrent_strategies: StrategyParameter
    max_concurrent_strategies: StrategyParameter

class PortfolioRiskMetrics(TypedDict):
    """Portfolio-level risk metrics."""
    risk_concentration_index: StrategyParameter
    total_portfolio_risk: StrategyParameter

class CombinedRiskMetrics(TypedDict):
    """Combined risk metrics for the portfolio."""
    var_95: StrategyParameter
    cvar_95: StrategyParameter
    var_99: StrategyParameter
    cvar_99: StrategyParameter

class RiskMetrics(TypedDict):
    """Complete risk metrics."""
    portfolio_metrics: PortfolioRiskMetrics
    combined_risk: CombinedRiskMetrics
    strategy_relationships: Dict[str, StrategyParameter]

class PortfolioMetrics(TypedDict):
    """Complete portfolio metrics."""
    concurrency: ConcurrencyMetrics
    efficiency: EfficiencyMetrics
    risk: RiskMetrics
    signals: SignalMetrics

class ConcurrencyReport(TypedDict):
    """Complete concurrency analysis report."""
    strategies: List[Strategy]
    ticker_metrics: Dict[str, Any]
    portfolio_metrics: PortfolioMetrics

def create_strategy_object(
    config: Dict[str, Any],
    index: int,
    stats: Dict[str, Any]
) -> Strategy:
    """Create a strategy object with the optimized structure.

    Args:
        config (Dict[str, Any]): Strategy configuration
        index (int): Strategy index for ID generation
        stats (Dict[str, Any]): Statistics containing risk and efficiency metrics

    Returns:
        Strategy: Strategy object with parameters, performance, risk metrics, and efficiency metrics
    """
    strategy_type = config.get("STRATEGY_TYPE", "EMA")
    strategy_id = str(index)
    
    # Create base parameters
    parameters: StrategyParameters = {
        "ticker": {
            "value": config["TICKER"],
            "description": "Ticker symbol to analyze"
        },
        "timeframe": {
            "value": "Hourly" if config.get("USE_HOURLY", False) else "Daily",
            "description": "Trading timeframe (Hourly or Daily)"
        },
        "type": {
            "value": strategy_type,
            "description": "Strategy type (MACD, SMA, or EMA)"
        },
        "direction": {
            "value": config.get("DIRECTION", "Long"),
            "description": "Trading direction (Long or Short)"
        },
        "short_window": {
            "value": config["SHORT_WINDOW"],
            "description": "Period for short moving average or MACD fast line"
        },
        "long_window": {
            "value": config["LONG_WINDOW"],
            "description": "Period for long moving average or MACD slow line"
        }
    }
    
    # Add signal_window for MACD strategies
    if strategy_type == "MACD" and "SIGNAL_WINDOW" in config:
        parameters["signal_window"] = {
            "value": config["SIGNAL_WINDOW"],
            "description": "Period for MACD signal line"
        }
    
    # Add RSI parameters if present
    if config.get("USE_RSI", False) and "RSI_PERIOD" in config:
        parameters["rsi_period"] = {
            "value": config["RSI_PERIOD"],
            "description": "Period for RSI calculation"
        }
        parameters["rsi_threshold"] = {
            "value": config["RSI_THRESHOLD"],
            "description": "RSI threshold for signal filtering"
        }
    
    # Add stop loss if present
    if "STOP_LOSS" in config:
        parameters["stop_loss"] = {
            "value": config["STOP_LOSS"],
            "description": "Stop loss percentage"
        }
    
    performance: StrategyPerformance = {
        "expectancy_per_month": {
            "value": config.get("EXPECTANCY_PER_MONTH", 0.0),
            "description": "Expected monthly return"
        }
    }
    
    # Extract strategy-specific risk metrics
    risk_metrics_data = stats.get('risk_metrics', {})
    
    risk_metrics: StrategyRiskMetrics = {
        "var_95": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_var_95", 0.0),
            "description": "Value at Risk (95% confidence)"
        },
        "cvar_95": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_cvar_95", 0.0),
            "description": "Conditional Value at Risk (95% confidence)"
        },
        "var_99": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_var_99", 0.0),
            "description": "Value at Risk (99% confidence)"
        },
        "cvar_99": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_cvar_99", 0.0),
            "description": "Conditional Value at Risk (99% confidence)"
        },
        "risk_contribution": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_risk_contrib", 0.0),
            "description": "Contribution to portfolio risk"
        },
        "alpha": {
            "value": risk_metrics_data.get(f"strategy_{strategy_id}_alpha", 0.0),
            "description": "Strategy alpha relative to portfolio"
        }
    }
    
    # Get strategy-specific efficiency metrics
    strategy_metrics = stats.get("strategy_efficiency_metrics", {})
    
    efficiency: EfficiencyMetrics = {
        "efficiency_score": {
            "value": strategy_metrics.get(f"strategy_{strategy_id}_efficiency_score", 0.0),
            "description": "Risk-adjusted performance score for this strategy"
        },
        "total_expectancy": {
            "value": strategy_metrics.get(f"strategy_{strategy_id}_expectancy", config.get("EXPECTANCY_PER_MONTH", 0.0)),
            "description": "Total expected return for this strategy"
        },
        "multipliers": {
            "diversification": {
                "value": strategy_metrics.get(f"strategy_{strategy_id}_diversification", 0.0),
                "description": "Strategy-specific diversification effect"
            },
            "independence": {
                "value": strategy_metrics.get(f"strategy_{strategy_id}_independence", 0.0),
                "description": "Strategy-specific independence from other strategies"
            },
            "activity": {
                "value": strategy_metrics.get(f"strategy_{strategy_id}_activity", 0.0),
                "description": "Strategy-specific activity level impact"
            }
        }
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
                "description": "Average number of signals per month"
            },
            "median": {
                "value": median_signals,
                "description": "Median number of signals per month"
            },
            "std_below": {
                "value": max(0.0, mean_signals - std_signals),
                "description": "One standard deviation below mean signals"
            },
            "std_above": {
                "value": mean_signals + std_signals,
                "description": "One standard deviation above mean signals"
            }
        },
        "summary": {
            "volatility": {
                "value": std_signals,
                "description": "Standard deviation of monthly signals"
            },
            "max_monthly": {
                "value": max_monthly,
                "description": "Maximum signals in any month"
            },
            "min_monthly": {
                "value": min_monthly,
                "description": "Minimum signals in any month"
            },
            "total": {
                "value": total_signals,
                "description": "Total number of signals across period"
            }
        }
    }
    
    return {
      "id": f"strategy_{strategy_id}",
      "parameters": parameters,
      "performance": performance,
      "risk_metrics": risk_metrics,
      "efficiency": efficiency,
      "signals": signals,
      "allocation_score": stats.get(f"strategy_{int(strategy_id)+1}_allocation", 0.0),
      "allocation": stats.get(f"strategy_{int(strategy_id)+1}_allocation_percentage", 0.0)
    }

def calculate_ticker_metrics(strategies: List[Strategy], ratio_based_allocation: bool) -> Dict[str, Any]:
    """Calculates ticker metrics from a list of strategies.

    Args:
        strategies (List[Strategy]): List of strategy objects.

    Returns:
        Dict[str, Any]: Dictionary of ticker metrics, with ticker symbols as keys.
    """
    ticker_metrics: Dict[str, Any] = {}
    for strategy in strategies:
        ticker = strategy["parameters"]["ticker"]["value"]
        if ticker not in ticker_metrics:
            ticker_metrics[ticker] = {
                "id": ticker,
                "performance": {
                    "expectancy_per_month": {
                        "value": strategy["performance"]["expectancy_per_month"]["value"],
                        "description": strategy["performance"]["expectancy_per_month"]["description"]
                    }
                },
                "risk_metrics": {k: v["value"] for k, v in strategy["risk_metrics"].items()},
                "efficiency": strategy["efficiency"],
                "signals": strategy["signals"],
                "allocation_score": strategy["allocation_score"],
                "allocation": strategy["allocation"]
            }
        else:
            # Aggregate values for existing ticker
            ticker_metrics[ticker]["performance"]["expectancy_per_month"]["value"] += strategy["performance"]["expectancy_per_month"]["value"]
            
            # Average risk metrics
            num_strategies = len(strategies) # Dynamic
            for k in ticker_metrics[ticker]["risk_metrics"]:
                ticker_metrics[ticker]["risk_metrics"][k] = (ticker_metrics[ticker]["risk_metrics"][k] + strategy["risk_metrics"][k]["value"]) / num_strategies

            # Average efficiency metrics
            for k in ticker_metrics[ticker]["efficiency"]:
                if isinstance(ticker_metrics[ticker]["efficiency"][k], dict):
                    if "value" in ticker_metrics[ticker]["efficiency"][k]:
                        ticker_metrics[ticker]["efficiency"][k]["value"] = (ticker_metrics[ticker]["efficiency"][k]["value"] + strategy["efficiency"][k]["value"]) / num_strategies
                    else:
                        for k2 in ticker_metrics[ticker]["efficiency"][k]:
                            ticker_metrics[ticker]["efficiency"][k][k2]["value"] = (ticker_metrics[ticker]["efficiency"][k][k2]["value"] + strategy["efficiency"][k][k2]["value"]) / num_strategies

            # Average signal metrics
            for k in ticker_metrics[ticker]["signals"]:
                if isinstance(ticker_metrics[ticker]["signals"][k], dict) and "value" in ticker_metrics[ticker]["signals"][k]:
                    ticker_metrics[ticker]["signals"][k]["value"] = (ticker_metrics[ticker]["signals"][k]["value"] + strategy["signals"][k]["value"]) / num_strategies
                elif isinstance(ticker_metrics[ticker]["signals"][k], dict):
                    for k2 in ticker_metrics[ticker]["signals"][k]:
                        ticker_metrics[ticker]["signals"][k][k2]["value"] = (ticker_metrics[ticker]["signals"][k][k2]["value"] + strategy["signals"][k][k2]["value"]) / num_strategies

            ticker_metrics[ticker]["allocation_score"] += strategy["allocation_score"]
            ticker_metrics[ticker]["allocation"] += strategy["allocation"]

    return ticker_metrics

def create_portfolio_metrics(stats: Dict[str, Any]) -> PortfolioMetrics:
    """Create portfolio metrics with the optimized structure.

    Args:
        stats (Dict[str, Any]): Statistics from the concurrency analysis

    Returns:
        PortfolioMetrics: Portfolio metrics with the optimized structure
    """
    concurrency: ConcurrencyMetrics = {
        "total_concurrent_periods": {
            "value": stats["total_concurrent_periods"],
            "description": "Number of periods with concurrent positions"
        },
        "concurrency_ratio": {
            "value": stats["concurrency_ratio"],
            "description": "Ratio of concurrent periods to total periods"
        },
        "exclusive_ratio": {
            "value": stats["exclusive_ratio"],
            "description": "Ratio of periods with exactly one strategy in position"
        },
        "inactive_ratio": {
            "value": stats["inactive_ratio"],
            "description": "Ratio of periods with no active strategies"
        },
        "avg_concurrent_strategies": {
            "value": stats["avg_concurrent_strategies"],
            "description": "Average number of concurrent strategies"
        },
        "max_concurrent_strategies": {
            "value": stats["max_concurrent_strategies"],
            "description": "Maximum number of concurrent strategies"
        }
    }
    
    efficiency: EfficiencyMetrics = {
        "efficiency_score": {
            "value": stats["efficiency_score"],
            "description": "Risk-Adjusted Performance"
        },
        "total_expectancy": {
            "value": stats["total_expectancy"],
            "description": "Combined expected return across all strategies"
        },
        "multipliers": {
            "diversification": {
                "value": stats["diversification_multiplier"],
                "description": "Multiplier effect from strategy diversification"
            },
            "independence": {
                "value": stats["independence_multiplier"],
                "description": "Multiplier effect from strategy independence"
            },
            "activity": {
                "value": stats["activity_multiplier"],
                "description": "Multiplier effect from strategy activity levels"
            }
        }
    }
    
    risk: RiskMetrics = {
        "portfolio_metrics": {
            "risk_concentration_index": {
                "value": stats["risk_concentration_index"],
                "description": "Measure of risk concentration"
            },
            "total_portfolio_risk": {
                "value": stats["risk_metrics"].get("total_portfolio_risk", 0.0),
                "description": "Overall portfolio risk measure"
            }
        },
        "combined_risk": {
            "var_95": {
                "value": stats["risk_metrics"].get("combined_var_95", 0.0),
                "description": "Combined Value at Risk (95% confidence)"
            },
            "cvar_95": {
                "value": stats["risk_metrics"].get("combined_cvar_95", 0.0),
                "description": "Combined Conditional Value at Risk (95% confidence)"
            },
            "var_99": {
                "value": stats["risk_metrics"].get("combined_var_99", 0.0),
                "description": "Combined Value at Risk (99% confidence)"
            },
            "cvar_99": {
                "value": stats["risk_metrics"].get("combined_cvar_99", 0.0),
                "description": "Combined Conditional Value at Risk (99% confidence)"
            }
        },
        "strategy_relationships": {
            key: {"value": value, "description": f"Risk relationship metric: {key}"}
            for key, value in stats["risk_metrics"].items()
            if key.startswith("risk_overlap_")
        }
    }
    
    # Use portfolio-level signal metrics from the root level
    signals: SignalMetrics = {
        "monthly_statistics": {
            "mean": {
                "value": stats["signal_metrics"]["mean_signals"],
                "description": "Average number of signals per month"
            },
            "median": {
                "value": stats["signal_metrics"]["median_signals"],
                "description": "Median number of signals per month"
            },
            "std_below": {
                "value": stats["signal_metrics"]["std_below_mean"],
                "description": "One standard deviation below mean signals"
            },
            "std_above": {
                "value": stats["signal_metrics"]["std_above_mean"],
                "description": "One standard deviation above mean signals"
            }
        },
        "summary": {
            "volatility": {
                "value": stats["signal_metrics"]["signal_volatility"],
                "description": "Standard deviation of monthly signals"
            },
            "max_monthly": {
                "value": stats["signal_metrics"]["max_monthly_signals"],
                "description": "Maximum signals in any month"
            },
            "min_monthly": {
                "value": stats["signal_metrics"]["min_monthly_signals"],
                "description": "Minimum signals in any month"
            },
            "total": {
                "value": stats["signal_metrics"]["total_signals"],
                "description": "Total number of signals across period"
            }
        }
    }
    
    return {
        "concurrency": concurrency,
        "efficiency": efficiency,
        "risk": risk,
        "signals": signals
    }

def generate_json_report(
    strategies: List[Dict[str, Any]], 
    stats: Dict[str, Any], 
    log: Callable[[str, str], None]
) -> ConcurrencyReport:
    """Generate a comprehensive JSON report of the concurrency analysis.

    Args:
        strategies (List[Dict[str, Any]]): List of strategy configurations
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        log (Callable[[str, str], None]): Logging function

    Returns:
        ConcurrencyReport: Complete report containing:
            - strategies: List of strategy details and parameters
            - portfolio_metrics: Dictionary of concurrency, efficiency, risk and signal metrics

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

        # Validate required statistics
        required_stats = [
            'total_concurrent_periods', 'concurrency_ratio', 'exclusive_ratio',
            'inactive_ratio', 'avg_concurrent_strategies', 'max_concurrent_strategies',
            'efficiency_score', 'total_expectancy', 'diversification_multiplier',
            'independence_multiplier', 'activity_multiplier', 'risk_concentration_index',
            'signal_metrics', 'risk_metrics'
        ]
        missing_stats = [stat for stat in required_stats if stat not in stats]
        if missing_stats:
            log(f"Missing required statistics: {missing_stats}", "error")
            raise KeyError(f"Missing required statistics: {missing_stats}")
            
        # Create strategy objects
        strategy_objects = []
        for idx, strategy in enumerate(strategies, 1):
            log(f"Processing strategy {idx}/{len(strategies)}: {strategy['TICKER']}", "info")
            strategy_objects.append(create_strategy_object(strategy, idx, stats))
        
        # Create portfolio metrics
        log("Creating portfolio metrics", "info")
        portfolio_metrics = create_portfolio_metrics(stats)

        # Calculate ticker metrics
        log("Calculating ticker metrics", "info")
        ticker_metrics = calculate_ticker_metrics(strategy_objects, ratio_based_allocation=True)
        
        # Create report
        strategy_objects.sort(key=lambda x: x.get("allocation", 0.0), reverse=True)
        report: ConcurrencyReport = {
            "strategies": strategy_objects,
            "ticker_metrics": ticker_metrics,
            "portfolio_metrics": portfolio_metrics
        }
        
        log("Successfully generated JSON report", "info")
        return report
        
    except Exception as e:
        log(f"Error generating JSON report: {str(e)}", "error")
        raise
