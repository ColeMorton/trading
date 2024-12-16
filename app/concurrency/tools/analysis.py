"""Core analysis functionality for concurrency analysis."""

from typing import List, Tuple, Callable
import polars as pl
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_multiple_data
from app.concurrency.tools.risk_metrics import calculate_risk_contributions
from app.concurrency.tools.efficiency import calculate_efficiency_score
from app.concurrency.tools.position_metrics import calculate_position_metrics
from app.concurrency.tools.signal_metrics import calculate_signal_metrics

def validate_inputs(
    data_list: List[pl.DataFrame],
    config_list: List[StrategyConfig],
    log: Callable[[str, str], None]
) -> None:
    """Validate input data and configurations.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        config_list (List[StrategyConfig]): List of configurations
        log (Callable[[str, str], None]): Logging function

    Raises:
        ValueError: If invalid input data
    """
    if len(data_list) != len(config_list):
        raise ValueError("Number of dataframes must match number of configurations")
    
    if len(data_list) < 2:
        raise ValueError("At least two strategies are required for analysis")

    required_cols = ["Date", "Position", "Close"]
    for df in data_list:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

def compile_statistics(
    aligned_data: List[pl.DataFrame],
    position_metrics: Tuple[dict, float, int, int, int, int, float],
    risk_metrics: dict,
    efficiency_metrics: Tuple[float, float, float, float, float],
    signal_metrics: dict,
    log: Callable[[str, str], None]
) -> ConcurrencyStats:
    """Compile analysis statistics.

    Args:
        aligned_data (List[pl.DataFrame]): Aligned dataframes
        position_metrics (Tuple): Position-based metrics
        risk_metrics (dict): Risk contribution metrics
        efficiency_metrics (Tuple): Efficiency score and components
        signal_metrics (dict): Signal-based metrics
        log (Callable[[str, str], None]): Logging function

    Returns:
        ConcurrencyStats: Compiled statistics
    """
    try:
        log("Compiling analysis statistics", "info")
        
        (
            correlations,
            _,
            concurrent_periods,
            exclusive_periods,
            inactive_periods,
            max_concurrent,
            avg_concurrent
        ) = position_metrics

        (
            efficiency_score,
            total_expectancy,
            diversification_multiplier,
            independence_multiplier,
            activity_multiplier
        ) = efficiency_metrics

        total_periods = len(aligned_data[0])
        risk_concentration_index = (
            avg_concurrent / max_concurrent
            if max_concurrent > 0
            else 0.0
        )

        stats = {
            "total_periods": total_periods,
            "total_concurrent_periods": concurrent_periods,
            "exclusive_periods": exclusive_periods,
            "concurrency_ratio": float(concurrent_periods / total_periods),
            "exclusive_ratio": float(exclusive_periods / total_periods),
            "inactive_ratio": float(inactive_periods / total_periods),
            "avg_concurrent_strategies": avg_concurrent,
            "risk_concentration_index": risk_concentration_index,
            "max_concurrent_strategies": max_concurrent,
            "strategy_correlations": correlations,
            "avg_position_length": float(
                sum(df["Position"].sum() for df in aligned_data) / len(aligned_data)
            ),
            "efficiency_score": efficiency_score,
            "total_expectancy": total_expectancy,
            "diversification_multiplier": diversification_multiplier,
            "independence_multiplier": independence_multiplier,
            "activity_multiplier": activity_multiplier,
            "risk_metrics": risk_metrics,
            "signal_metrics": signal_metrics,
            "start_date": str(aligned_data[0]["Date"].min()),
            "end_date": str(aligned_data[0]["Date"].max())
        }
        
        log("Statistics compilation completed", "info")
        return stats
        
    except Exception as e:
        log(f"Error compiling statistics: {str(e)}", "error")
        raise

def analyze_concurrency(
    data_list: List[pl.DataFrame],
    config_list: List[StrategyConfig],
    log: Callable[[str, str], None]
) -> Tuple[ConcurrencyStats, List[pl.DataFrame]]:
    """Analyze concurrent positions across multiple strategies.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        config_list (List[StrategyConfig]): List of configurations
        log (Callable[[str, str], None]): Logging function

    Returns:
        Tuple[ConcurrencyStats, List[pl.DataFrame]]: Statistics and aligned data

    Raises:
        ValueError: If invalid input data
    """
    try:
        validate_inputs(data_list, config_list, log)
        log("Starting concurrency analysis", "info")
        
        # Get hourly flags and align data
        log("Preparing data alignment", "info")
        hourly_flags = [config.get('USE_HOURLY', False) for config in config_list]
        aligned_data = align_multiple_data(data_list, hourly_flags, log)
        
        # Extract position arrays and calculate metrics
        log("Extracting position arrays", "info")
        position_arrays = [
            df["Position"].fill_null(0).to_numpy()
            for df in aligned_data
        ]
        
        log("Calculating position metrics", "info")
        position_metrics = calculate_position_metrics(position_arrays, log)
        
        # Calculate risk metrics
        log("Calculating risk metrics", "info")
        risk_metrics = calculate_risk_contributions(position_arrays, aligned_data, log)

        # Calculate efficiency metrics
        log("Calculating efficiency metrics", "info")
        strategy_expectancies = [
            config.get('EXPECTANCY_PER_DAY', 0)
            for config in config_list
        ]
        efficiency_metrics = calculate_efficiency_score(
            strategy_expectancies,
            position_metrics[1],  # avg_correlation
            position_metrics[2],  # concurrent_periods
            position_metrics[3],  # exclusive_periods
            position_metrics[4],  # inactive_periods
            len(aligned_data[0]),  # total_periods
            log
        )

        # Calculate signal metrics
        log("Calculating signal metrics", "info")
        signal_metrics = calculate_signal_metrics(aligned_data, log)
        
        # Compile final statistics
        stats = compile_statistics(
            aligned_data,
            position_metrics,
            risk_metrics,
            efficiency_metrics,
            signal_metrics,
            log
        )
        
        log("Analysis completed successfully", "info")
        return stats, aligned_data
        
    except Exception as e:
        log(f"Error during analysis: {str(e)}", "error")
        raise
