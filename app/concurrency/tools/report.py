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
    report = {
        "strategies": [],
        "metrics": {
            "concurrency": {
                "total_concurrent_periods": stats['total_concurrent_periods'],
                "concurrency_ratio": stats['concurrency_ratio'],
                "exclusive_ratio": stats['exclusive_ratio'],
                "inactive_ratio": stats['inactive_ratio'],
                "avg_concurrent_strategies": stats['avg_concurrent_strategies'],
                "max_concurrent_strategies": stats['max_concurrent_strategies']
            },
            "efficiency": {
                "efficiency_score": stats['efficiency_score'],
                "total_expectancy": stats['total_expectancy'],
                "diversification_multiplier": stats['diversification_multiplier'],
                "independence_multiplier": stats['independence_multiplier'],
                "activity_multiplier": stats['activity_multiplier']
            },
            "risk": {
                "risk_concentration_index": stats['risk_concentration_index'],
                **stats['risk_metrics']
            }
        }
    }

    # Add strategy details
    for strategy in strategies:
        strategy_info = {
            "ticker": strategy["TICKER"],
            "timeframe": "Hourly" if strategy.get("USE_HOURLY", False) else "Daily",
            "expectancy_per_day": strategy.get("EXPECTANCY_PER_DAY", 0),
        }
        
        # Add strategy-specific parameters
        if "SIGNAL_PERIOD" in strategy:
            strategy_info.update({
                "type": "MACD",
                "short_window": strategy["SHORT_WINDOW"],
                "long_window": strategy["LONG_WINDOW"],
                "signal_period": strategy["SIGNAL_PERIOD"]
            })
        else:
            # Determine if it's EMA or SMA Cross
            ma_type = "EMA Cross" if strategy.get("USE_EMA", True) else "SMA Cross"
            strategy_info.update({
                "type": ma_type,
                "short_window": strategy["SHORT_WINDOW"],
                "long_window": strategy["LONG_WINDOW"]
            })
        
        report["strategies"].append(strategy_info)

    return report
