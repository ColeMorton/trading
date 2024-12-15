"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from typing import List, Dict, Any, Callable
from app.concurrency.tools.types import StrategyConfig

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
            - metrics: Dictionary of concurrency, efficiency and risk metrics
    """
    log(f"Starting JSON report generation for {len(strategies)} strategies", "info")

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
            }
        }
    }

    # Add risk metrics with descriptions
    for key, value in stats['risk_metrics'].items():
        report["metrics"]["risk"][key] = {
            "value": value,
            "description": f"Risk metric: {key}"
        }

    log("Compiled metrics data for concurrency, efficiency, and risk analysis", "info")

    # Add strategy details - preserve all original properties and add expectancy_per_day
    for idx, strategy in enumerate(strategies, 1):
        log(f"Processing strategy {idx}/{len(strategies)}: {strategy['TICKER']}", "info")
        
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
        
        # Add stop_loss only if present
        if "STOP_LOSS" in strategy:
            strategy_info["stop_loss"] = {
                "value": strategy["STOP_LOSS"],
                "description": "Stop loss percentage"
            }
        
        # Add RSI parameters if present
        if strategy.get("USE_RSI", False) and "RSI_PERIOD" in strategy:
            strategy_info["rsi_period"] = {
                "value": strategy["RSI_PERIOD"],
                "description": "Period for RSI calculation"
            }
            strategy_info["rsi_threshold"] = {
                "value": strategy["RSI_THRESHOLD"],
                "description": "RSI threshold for signal filtering"
            }
            
        # Add MACD signal period if present
        if "SIGNAL_PERIOD" in strategy:
            strategy_info["signal_period"] = {
                "value": strategy["SIGNAL_PERIOD"],
                "description": "Period for MACD signal line"
            }
            
        # Add expectancy per day
        if "EXPECTANCY_PER_DAY" in strategy:
            strategy_info["expectancy_per_day"] = {
                "value": strategy["EXPECTANCY_PER_DAY"],
                "description": "Expected daily return"
            }
        
        report["strategies"].append(strategy_info)

    log("Successfully generated JSON report", "info")
    return report
