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

    log("Compiled metrics data for concurrency, efficiency, and risk analysis", "info")

    # Add strategy details - preserve all original properties and add expectancy_per_day
    for idx, strategy in enumerate(strategies, 1):
        log(f"Processing strategy {idx}/{len(strategies)}: {strategy['TICKER']}", "info")
        
        # Convert internal strategy config format to output format
        strategy_info = {
            "ticker": strategy["TICKER"],
            "timeframe": "Hourly" if strategy.get("USE_HOURLY", False) else "Daily",
            "type": "MACD" if "SIGNAL_PERIOD" in strategy else "EMA",
            "short_window": strategy["SHORT_WINDOW"],
            "long_window": strategy["LONG_WINDOW"],
            "stop_loss": strategy["STOP_LOSS"]
        }
        
        # Add RSI parameters if present
        if strategy.get("USE_RSI", False) and "RSI_PERIOD" in strategy:
            strategy_info["rsi_period"] = strategy["RSI_PERIOD"]
            strategy_info["rsi_threshold"] = strategy["RSI_THRESHOLD"]
            
        # Add MACD signal period if present
        if "SIGNAL_PERIOD" in strategy:
            strategy_info["signal_period"] = strategy["SIGNAL_PERIOD"]
            
        # Add expectancy per day
        if "EXPECTANCY_PER_DAY" in strategy:
            strategy_info["expectancy_per_day"] = strategy["EXPECTANCY_PER_DAY"]
        
        report["strategies"].append(strategy_info)

    log("Successfully generated JSON report", "info")
    return report
