"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from typing import List, Dict, Any, Callable
from app.portfolio_optimization.tools.types import StrategyConfig

def generate_json_report(
    strategies: List[StrategyConfig], 
    stats: Dict[str, Any], 
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    """Generate a comprehensive JSON report of the concurrency analysis.

    Args:
        strategies (List[StrategyConfig]): List of strategy configurations
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, Any]: Complete report in dictionary format containing:
            - strategies: List of strategy details and parameters
            - metrics: Dictionary of concurrency, efficiency, risk and signal metrics

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

        log("Creating report structure", "info")
        report = {
            "strategies": [],
            "metrics": {
                "concurrency": {
                    "total_concurrent_periods": {
                        "value": stats['total_concurrent_periods'],
                        "description": "Number of periods with concurrent positions"
                    },
                    "concurrency_ratio": {
                        "value": stats['concurrency_ratio'],
                        "description": "Ratio of concurrent periods to total periods"
                    },
                    "exclusive_ratio": {
                        "value": stats['exclusive_ratio'],
                        "description": "Ratio of periods with exactly one strategy in position"
                    },
                    "inactive_ratio": {
                        "value": stats['inactive_ratio'],
                        "description": "Ratio of periods with no active strategies"
                    },
                    "avg_concurrent_strategies": {
                        "value": stats['avg_concurrent_strategies'],
                        "description": "Average number of concurrent strategies"
                    },
                    "max_concurrent_strategies": {
                        "value": stats['max_concurrent_strategies'],
                        "description": "Maximum number of concurrent strategies"
                    }
                },
                "efficiency": {
                    "efficiency_score": {
                        "value": stats['efficiency_score'],
                        "description": "Risk-Adjusted Performance"
                    },
                    "total_expectancy": {
                        "value": stats['total_expectancy'],
                        "description": "Combined expected return across all strategies"
                    },
                    "diversification_multiplier": {
                        "value": stats['diversification_multiplier'],
                        "description": "Multiplier effect from strategy diversification"
                    },
                    "independence_multiplier": {
                        "value": stats['independence_multiplier'],
                        "description": "Multiplier effect from strategy independence"
                    },
                    "activity_multiplier": {
                        "value": stats['activity_multiplier'],
                        "description": "Multiplier effect from strategy activity levels"
                    }
                },
                "risk": {
                    "risk_concentration_index": {
                        "value": stats['risk_concentration_index'],
                        "description": "Measure of risk concentration"
                    }
                },
                "signals": {
                    "mean_signals": {
                        "value": stats['signal_metrics']['mean_signals'],
                        "description": "Average number of signals per month"
                    },
                    "median_signals": {
                        "value": stats['signal_metrics']['median_signals'],
                        "description": "Median number of signals per month"
                    },
                    "std_below_mean": {
                        "value": stats['signal_metrics']['std_below_mean'],
                        "description": "One standard deviation below mean signals"
                    },
                    "std_above_mean": {
                        "value": stats['signal_metrics']['std_above_mean'],
                        "description": "One standard deviation above mean signals"
                    },
                    "signal_volatility": {
                        "value": stats['signal_metrics']['signal_volatility'],
                        "description": "Standard deviation of monthly signals"
                    },
                    "max_monthly_signals": {
                        "value": stats['signal_metrics']['max_monthly_signals'],
                        "description": "Maximum signals in any month"
                    },
                    "min_monthly_signals": {
                        "value": stats['signal_metrics']['min_monthly_signals'],
                        "description": "Minimum signals in any month"
                    },
                    "total_signals": {
                        "value": stats['signal_metrics']['total_signals'],
                        "description": "Total number of signals across period"
                    }
                }
            }
        }

        # Add risk metrics with descriptions
        log("Adding risk metrics", "info")
        for key, value in stats['risk_metrics'].items():
            report["metrics"]["risk"][key] = {
                "value": value,
                "description": f"Risk metric: {key}"
            }

        log("Compiled metrics data for concurrency, efficiency, risk, and signal analysis", "info")

        # Add strategy details - preserve all original properties and add expectancy_per_month
        log("Processing strategy details", "info")
        for idx, strategy in enumerate(strategies, 1):
            log(f"Processing strategy {idx}/{len(strategies)}: {strategy['TICKER']}", "info")
            
            # Validate required strategy fields
            required_fields = ["TICKER", "SHORT_WINDOW", "LONG_WINDOW"]
            missing_fields = [field for field in required_fields if field not in strategy]
            if missing_fields:
                log(f"Strategy {idx} missing required fields: {missing_fields}", "error")
                raise KeyError(f"Strategy {idx} missing required fields: {missing_fields}")
            
            # Use the stored strategy type directly
            strategy_type = strategy.get("STRATEGY_TYPE", "EMA")  # Default to EMA if not found
            
            # Convert internal strategy config format to output format
            strategy_info = {
                "ticker": {
                    "value": strategy["TICKER"],
                    "description": "Ticker symbol to analyze"
                },
                "timeframe": {
                    "value": "Hourly" if strategy.get("USE_HOURLY", False) else "Daily",
                    "description": "Trading timeframe (Hourly or Daily)"
                },
                "type": {
                    "value": strategy_type,
                    "description": "Strategy type (MACD, SMA, or EMA)"
                },
                "direction": {
                    "value": strategy.get("DIRECTION", "Long"),
                    "description": "Trading direction (Long or Short)"
                },
                "short_window": {
                    "value": strategy["SHORT_WINDOW"],
                    "description": "Period for short moving average or MACD fast line"
                },
                "long_window": {
                    "value": strategy["LONG_WINDOW"],
                    "description": "Period for long moving average or MACD slow line"
                }
            }
            
            # Add optional strategy parameters
            log(f"Adding optional parameters for strategy {strategy['TICKER']}", "info")
            
            if "STOP_LOSS" in strategy:
                strategy_info["stop_loss"] = {
                    "value": strategy["STOP_LOSS"],
                    "description": "Stop loss percentage"
                }
            
            if strategy.get("USE_RSI", False) and "RSI_PERIOD" in strategy:
                strategy_info["rsi_period"] = {
                    "value": strategy["RSI_PERIOD"],
                    "description": "Period for RSI calculation"
                }
                strategy_info["rsi_threshold"] = {
                    "value": strategy["RSI_THRESHOLD"],
                    "description": "RSI threshold for signal filtering"
                }
                
            if "SIGNAL_PERIOD" in strategy:
                strategy_info["signal_period"] = {
                    "value": strategy["SIGNAL_PERIOD"],
                    "description": "Period for MACD signal line"
                }
                
            if "EXPECTANCY_PER_MONTH" in strategy:
                strategy_info["expectancy_per_month"] = {
                    "value": strategy["EXPECTANCY_PER_MONTH"],
                    "description": "Expected monthly return"
                }
            
            report["strategies"].append(strategy_info)

        log("Successfully generated JSON report", "info")
        return report
        
    except Exception as e:
        log(f"Error generating JSON report: {str(e)}", "error")
        raise
