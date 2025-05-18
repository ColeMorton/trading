"""Report generation utilities for concurrency analysis.

This module provides functionality for generating JSON reports from concurrency analysis results.
"""

from typing import Dict, Any, List, Callable

# Import from local modules
from app.concurrency.tools.report.strategy import create_strategy_object
from app.concurrency.tools.report.metrics import calculate_ticker_metrics, create_portfolio_metrics

# Import types from the parent module
from app.concurrency.tools.types import ConcurrencyReport

def generate_json_report(
    strategies: List[Dict[str, Any]],
    stats: Dict[str, Any],
    log: Callable[[str, str], None],
    config: Dict[str, Any]
) -> ConcurrencyReport:
    """Generate a comprehensive JSON report of the concurrency analysis.

    Args:
        strategies (List[Dict[str, Any]]): List of strategy configurations
        stats (Dict[str, Any]): Statistics from the concurrency analysis
        log (Callable[[str, str], None]): Logging function
        config (Dict[str, Any]): Configuration dictionary containing RATIO_BASED_ALLOCATION

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

        # Check if allocation is enabled
        include_allocation = config.get("REPORT_INCLUDES", {}).get("ALLOCATION", True)
        log(f"ALLOCATION flag in report generator: {include_allocation}", "info")
        
        # Add allocation flag to stats for other functions to use
        stats["include_allocation"] = include_allocation

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
        portfolio_metrics = create_portfolio_metrics(stats, config)

        # Sort strategies by allocation if enabled, otherwise by ID
        if include_allocation:
            log("Sorting strategies by allocation", "info")
            strategy_objects.sort(key=lambda x: x.get("allocation", 0.0), reverse=True)
        else:
            log("Sorting strategies by ID (allocation disabled)", "info")
            strategy_objects.sort(key=lambda x: x["id"])
        
        # Initialize report with portfolio metrics
        report: ConcurrencyReport = {
            "portfolio_metrics": portfolio_metrics
        }
        
        # Check if ticker metrics should be included in the report
        include_ticker_metrics = True
        if "REPORT_INCLUDES" in config and "TICKER_METRICS" in config["REPORT_INCLUDES"]:
            include_ticker_metrics = config["REPORT_INCLUDES"]["TICKER_METRICS"]
        
        # Only calculate and include ticker metrics if configured to do so
        if include_ticker_metrics:
            log("Calculating ticker metrics", "info")
            ratio_based = config.get("RATIO_BASED_ALLOCATION", False)
            ticker_metrics = calculate_ticker_metrics(
                strategy_objects,
                ratio_based_allocation=ratio_based,
                include_allocation=include_allocation
            )
            report["ticker_metrics"] = ticker_metrics
        
        # Check if strategies should be included in the report
        include_strategies = True
        if "REPORT_INCLUDES" in config and "STRATEGIES" in config["REPORT_INCLUDES"]:
            include_strategies = config["REPORT_INCLUDES"]["STRATEGIES"]
        
        # Only include strategies if configured to do so
        if include_strategies:
            report["strategies"] = strategy_objects
        
        log("Successfully generated JSON report", "info")
        return report
        
    except Exception as e:
        log(f"Error generating JSON report: {str(e)}", "error")
        raise