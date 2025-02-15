"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from typing import List, Dict, Any, Callable
from app.concurrency.tools.types import (
    StrategyConfig,
    Strategy,
    StrategyParameters,
    StrategyPerformance,
    StrategyRiskMetrics,
    PortfolioMetrics,
    ConcurrencyMetrics,
    EfficiencyMetrics,
    RiskMetrics,
    SignalMetrics,
    OptimizedConcurrencyReport
)

def create_strategy_object(
    config: StrategyConfig,
    index: int,
    stats: Dict[str, Any]
) -> Strategy:
    """Create a strategy object with the new structure.

    Args:
        config (StrategyConfig): Strategy configuration
        index (int): Strategy index for ID generation
        stats (Dict[str, Any]): Statistics containing risk metrics

    Returns:
        Strategy: Strategy object with the new structure
    """
    strategy_type = config.get("STRATEGY_TYPE", "EMA")
    
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
    
    performance: StrategyPerformance = {
        "expectancy_per_month": {
            "value": config.get("EXPECTANCY_PER_MONTH", 0.0),
            "description": "Expected monthly return"
        }
    }
    
    # Extract strategy-specific risk metrics
    risk_metrics_data = stats.get('risk_metrics', {})
    strategy_id = str(index)
    
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
    
    return {
        "id": f"strategy_{strategy_id}",
        "parameters": parameters,
        "performance": performance,
        "risk_metrics": risk_metrics
    }

def create_portfolio_metrics(stats: Dict[str, Any]) -> PortfolioMetrics:
    """Create portfolio metrics with the new structure.

    Args:
        stats (Dict[str, Any]): Statistics from the concurrency analysis

    Returns:
        PortfolioMetrics: Portfolio metrics with the new structure
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
    strategies: List[StrategyConfig], 
    stats: Dict[str, Any], 
    log: Callable[[str, str], None],
    use_new_format: bool = True
) -> Dict[str, Any]:
    """Generate a comprehensive JSON report of the concurrency analysis.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        log (Callable[[str, str], None]): Logging function
        use_new_format (bool): Whether to use the new optimized format

    Returns:
        Dict[str, Any]: Complete report in dictionary format containing:
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

        if use_new_format:
            log("Using new optimized format", "info")
            
            # Create strategy objects
            strategy_objects = []
            for idx, strategy in enumerate(strategies, 1):
                log(f"Processing strategy {idx}/{len(strategies)}: {strategy['TICKER']}", "info")
                strategy_objects.append(create_strategy_object(strategy, idx, stats))
            
            # Create portfolio metrics
            log("Creating portfolio metrics", "info")
            portfolio_metrics = create_portfolio_metrics(stats)
            
            # Create optimized report
            report: OptimizedConcurrencyReport = {
                "strategies": strategy_objects,
                "portfolio_metrics": portfolio_metrics
            }
            
        else:
            log("Using legacy format", "info")
            # Create legacy format report (existing implementation)
            report = {
                "strategies": [],
                "metrics": {
                    "concurrency": {},
                    "efficiency": {},
                    "risk": {},
                    "signals": {}
                }
            }
            # ... (rest of legacy implementation)

        log("Successfully generated JSON report", "info")
        return report
        
    except Exception as e:
        log(f"Error generating JSON report: {str(e)}", "error")
        raise
