"""Optimization report generation for strategy permutation analysis.

This module provides functionality for generating reports that compare
the full strategy set with the optimal subset identified through permutation analysis.
"""

from typing import Dict, List, Callable, Any
from pathlib import Path
import json

from app.tools.portfolio import StrategyConfig
from app.concurrency.tools.types import ConcurrencyConfig


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy data types and None values."""
    def default(self, obj):
        import numpy as np
        if obj is None:
            return 1  # Convert None to 1 for best_horizon (default horizon)
        elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


def generate_optimization_report(
    all_strategies: List[StrategyConfig],
    all_stats: Dict[str, Any],
    optimal_strategies: List[StrategyConfig],
    optimal_stats: Dict[str, Any],
    config: ConcurrencyConfig,
    log: Callable[[str, str], None]
) -> Dict[str, Any]:
    """Generate a report comparing all strategies with the optimal subset.
    
    Args:
        all_strategies (List[StrategyConfig]): All strategies
        all_stats (Dict[str, Any]): Stats for all strategies
        optimal_strategies (List[StrategyConfig]): Optimal subset of strategies
        optimal_stats (Dict[str, Any]): Stats for optimal subset
        config (ConcurrencyConfig): Configuration dictionary
        log (Callable[[str, str], None]): Logging function
        
    Returns:
        Dict[str, Any]: Optimization report
    """
    log("Generating optimization report", "info")
    
    # Calculate improvement percentages
    efficiency_improvement = (
        (optimal_stats['efficiency_score'] - all_stats['efficiency_score']) / 
        all_stats['efficiency_score'] * 100
    )
    
    # Extract strategy tickers for easier reference
    all_tickers = [s.get('TICKER', 'unknown') for s in all_strategies]
    optimal_tickers = [s.get('TICKER', 'unknown') for s in optimal_strategies]
    
    # Create report
    report = {
        "optimization_summary": {
            "all_strategies_count": len(all_strategies),
            "all_strategies_tickers": all_tickers,
            "optimal_strategies_count": len(optimal_strategies),
            "optimal_strategies_tickers": optimal_tickers,
            "efficiency_improvement_percent": efficiency_improvement,
        },
        "all_strategies": {
            # Risk-adjusted efficiency score (combines structural and performance metrics)
            "efficiency_score": all_stats['efficiency_score'],
            
            # Structural components
            "diversification_multiplier": all_stats['diversification_multiplier'],
            "independence_multiplier": all_stats['independence_multiplier'],
            "activity_multiplier": all_stats['activity_multiplier'],
            
            # Performance metrics
            "total_expectancy": all_stats['total_expectancy'],
            "average_expectancy": all_stats['total_expectancy'] / len(all_strategies),
            "weighted_efficiency": all_stats.get('weighted_efficiency', 0.0),
            
            # Risk metrics
            "risk_concentration_index": all_stats['risk_concentration_index'],
        },
        "optimal_strategies": {
            # Risk-adjusted efficiency score (combines structural and performance metrics)
            "efficiency_score": optimal_stats['efficiency_score'],
            
            # Structural components
            "diversification_multiplier": optimal_stats['diversification_multiplier'],
            "independence_multiplier": optimal_stats['independence_multiplier'],
            "activity_multiplier": optimal_stats['activity_multiplier'],
            
            # Performance metrics
            "total_expectancy": optimal_stats['total_expectancy'],
            "average_expectancy": optimal_stats['total_expectancy'] / len(optimal_strategies),
            "weighted_efficiency": optimal_stats.get('weighted_efficiency', 0.0),
            
            # Risk metrics
            "risk_concentration_index": optimal_stats['risk_concentration_index'],
        },
        "config": {
            "portfolio": config["PORTFOLIO"],
            "min_strategies_per_permutation": config.get("OPTIMIZE_MIN_STRATEGIES", 3),
            "max_permutations": config.get("OPTIMIZE_MAX_PERMUTATIONS", None),
        },
        "efficiency_calculation_note": (
            "The efficiency_score is a comprehensive risk-adjusted performance metric "
            "that combines structural components (diversification, independence, activity) "
            "with performance metrics (expectancy, risk factors, allocation). "
            "Equal allocations were used for all strategies during optimization analysis."
        )
    }
    
    log("Optimization report generated", "info")
    return report


def save_optimization_report(
    report: Dict[str, Any],
    config: ConcurrencyConfig,
    log: Callable[[str, str], None]
) -> Path:
    """Save optimization report to file.
    
    Args:
        report (Dict[str, Any]): Report data to save
        config (ConcurrencyConfig): Configuration dictionary
        log (Callable[[str, str], None]): Logging function
        
    Returns:
        Path: Path where report was saved
        
    Raises:
        IOError: If the report cannot be saved
    """
    try:
        # Ensure the json/concurrency/optimization directory exists
        json_dir = Path("json/concurrency/optimization")
        json_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the portfolio filename without extension
        portfolio_filename = Path(config["PORTFOLIO"]).stem
        report_filename = f"{portfolio_filename}_optimization.json"
        
        # Save the report
        report_path = json_dir / report_filename
        log(f"Saving optimization report to {report_path}", "info")
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=4, cls=NumpyEncoder)
        
        log(f"Optimization report saved to {report_path}", "info")
        return report_path
        
    except Exception as e:
        log(f"Error saving optimization report: {str(e)}", "error")
        raise IOError(f"Failed to save optimization report: {str(e)}")