"""Core analysis functionality for concurrency analysis."""

from typing import List, Tuple, Callable
import polars as pl
from app.concurrency.tools.types import ConcurrencyStats, StrategyConfig
from app.concurrency.tools.data_alignment import align_multiple_data
from app.concurrency.tools.risk_metrics import calculate_risk_contributions
from app.concurrency.tools.efficiency import (
    calculate_strategy_efficiency,
    calculate_portfolio_efficiency,
    calculate_allocation_scores
)
from app.concurrency.tools.position_metrics import calculate_position_metrics
from app.concurrency.tools.signal_metrics import calculate_signal_metrics
from app.concurrency.tools.signal_quality import calculate_signal_quality_metrics

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
    signal_quality_metrics: dict,
    strategy_expectancies: List[float],
    strategy_efficiencies: List[Tuple[float, float, float, float]],
    log: Callable[[str, str], None]
) -> ConcurrencyStats:
    """Compile analysis statistics.

    Args:
        aligned_data (List[pl.DataFrame]): Aligned dataframes
        position_metrics (Tuple): Position-based metrics
        risk_metrics (dict): Risk contribution metrics
        efficiency_metrics (Tuple): Efficiency score and components
        signal_metrics (dict): Signal-based metrics
        strategy_expectancies (List[float]): List of strategy expectancies
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

        # Store individual strategy efficiency metrics
        strategy_efficiency_metrics = {}
        for idx, ((efficiency, div, ind, act), expectancy) in enumerate(zip(strategy_efficiencies, strategy_expectancies), 1):
            strategy_efficiency_metrics.update({
                f"strategy_{idx}_efficiency_score": efficiency,
                f"strategy_{idx}_expectancy": expectancy,
                f"strategy_{idx}_diversification": div,
                f"strategy_{idx}_independence": ind,
                f"strategy_{idx}_activity": act
            })

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
            "strategy_expectancies": strategy_expectancies,
            "strategy_efficiency_metrics": strategy_efficiency_metrics,
            "risk_metrics": risk_metrics,
            "signal_metrics": signal_metrics,
            "signal_quality_metrics": signal_quality_metrics,
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
    """Analyze concurrent positions across multiple strategies."""
    stats = {}
    signal_metrics = {}
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
        strategy_allocations = [
            config.get('ALLOCATION', 0.0)
            for config in config_list
        ]
        risk_metrics = calculate_risk_contributions(
            position_arrays,
            aligned_data,
            strategy_allocations,
            log
        )

        # Calculate efficiency metrics
        log("Calculating efficiency metrics", "info")
        
        # Calculate strategy expectancies
        strategy_expectancies = [
            config.get('EXPECTANCY_PER_MONTH', 0) / (30 if config.get('USE_HOURLY', False) else 21)
            for config in config_list
        ]
        
        # Calculate ratios
        total_periods = len(aligned_data[0])
        concurrent_ratio = position_metrics[2] / total_periods
        exclusive_ratio = position_metrics[3] / total_periods
        inactive_ratio = position_metrics[4] / total_periods
        
        # Calculate individual strategy efficiencies
        log("Calculating individual strategy efficiencies", "info")
        strategy_efficiencies = []
        for i, expectancy in enumerate(strategy_expectancies):
            efficiency, div, ind, act = calculate_strategy_efficiency(
                expectancy=expectancy,
                correlation=position_metrics[1],  # avg_correlation
                concurrent_ratio=concurrent_ratio,
                exclusive_ratio=exclusive_ratio,
                inactive_ratio=inactive_ratio,
                log=log
            )
            strategy_efficiencies.append((efficiency, div, ind, act))
        
        # Calculate portfolio efficiency
        log("Calculating portfolio efficiency", "info")
        portfolio_metrics = calculate_portfolio_efficiency(
            strategy_efficiencies=[e[0] for e in strategy_efficiencies],
            strategy_expectancies=strategy_expectancies,
            strategy_allocations=strategy_allocations,
            avg_correlation=position_metrics[1],
            concurrent_periods=position_metrics[2],
            exclusive_periods=position_metrics[3],
            inactive_periods=position_metrics[4],
            total_periods=total_periods,
            log=log
        )
        
        # Package metrics in legacy format for backward compatibility
        efficiency_metrics = (
            portfolio_metrics['portfolio_efficiency'],
            portfolio_metrics['total_expectancy'],
            portfolio_metrics['diversification_multiplier'],
            portfolio_metrics['independence_multiplier'],
            portfolio_metrics['activity_multiplier']
        )

        # Calculate signal metrics
        log("Calculating signal metrics", "info")
        signal_metrics = calculate_signal_metrics(aligned_data, log)
        
        # Calculate signal quality metrics
        log("Calculating signal quality metrics", "info")
        signal_quality_metrics = {}
        strategy_quality_metrics = {}
        
        # Create returns dataframes for signal quality calculation
        for i, df in enumerate(aligned_data, 1):
            try:
                # Calculate returns from Close prices
                returns_df = df.select(["Date", "Close"]).with_columns(
                    pl.col("Close").pct_change().alias("return")
                )
                
                # Create signals dataframe
                signals_df = df.select(["Date", "Position"]).with_columns(
                    pl.col("Position").diff().alias("signal")
                )
                
                # Calculate signal quality metrics for this strategy
                strategy_metrics = calculate_signal_quality_metrics(
                    signals_df=signals_df,
                    returns_df=returns_df,
                    strategy_id=f"strategy_{i}",
                    log=log
                )
                
                if strategy_metrics:
                    strategy_id = f"strategy_{i}"
                    signal_quality_metrics[strategy_id] = strategy_metrics
                    strategy_quality_metrics[strategy_id] = strategy_metrics
            except Exception as e:
                log(f"Error calculating signal quality metrics for strategy {i}: {str(e)}", "error")
        
        # Calculate aggregate signal quality metrics across all strategies
        try:
            from app.concurrency.tools.signal_quality import calculate_aggregate_signal_quality
            
            log("Calculating aggregate signal quality metrics", "info")
            aggregate_metrics = calculate_aggregate_signal_quality(
                strategy_metrics=strategy_quality_metrics,
                log=log
            )
            
            if aggregate_metrics:
                signal_quality_metrics["aggregate"] = aggregate_metrics
                log("Aggregate signal quality metrics added", "info")
        except Exception as e:
            log(f"Error calculating aggregate signal quality metrics: {str(e)}", "error")

        # Extract strategy risk contributions, signal quality scores, and efficiencies for allocation
        strategy_risk_contributions = [risk_metrics.get(f"strategy_{i+1}_risk_contrib", 0.0) for i in range(len(config_list))]
        strategy_signal_quality_scores = [risk_metrics.get(f"strategy_{i+1}_alpha_to_portfolio", 0.0) for i in range(len(config_list))]
        allocation_efficiencies = [efficiency[0] for efficiency in strategy_efficiencies]

        # Extract tickers from configs
        strategy_tickers = [config.get('TICKER', '') for config in config_list]
        
        # Calculate allocation scores
        log("Calculating allocation scores", "info")
        allocation_scores, allocation_percentages = calculate_allocation_scores(
            strategy_risk_contributions,
            strategy_signal_quality_scores,
            allocation_efficiencies,
            strategy_tickers,  # Add strategy_tickers parameter
            log,
            ratio_based_allocation=True  # Enable ratio-based allocation
        )

        # Compile all statistics
        stats = compile_statistics(
            aligned_data,
            position_metrics,
            risk_metrics,
            efficiency_metrics,
            signal_metrics,
            signal_quality_metrics,
            strategy_expectancies,
            strategy_efficiencies,  # Pass individual strategy efficiencies
            log
        )

        # Add allocation scores
        for i, (score, percentage) in enumerate(zip(allocation_scores, allocation_percentages), 1):
            stats[f"strategy_{i+1}_allocation"] = score
            stats[f"strategy_{i+1}_allocation_percentage"] = percentage

        log("Analysis completed successfully", "info")
        return stats, aligned_data

    except Exception as e:
        log(f"Error during analysis: {str(e)}", "error")
        # Ensure stats is defined even if an error occurs
        stats = {
            "total_periods": 0,
            "total_concurrent_periods": 0,
            "exclusive_periods": 0,
            "concurrency_ratio": 0.0,
            "exclusive_ratio": 0.0,
            "inactive_ratio": 0.0,
            "avg_concurrent_strategies": 0.0,
            "risk_concentration_index": 0.0,
            "max_concurrent_strategies": 0,
            "strategy_correlations": {},
            "avg_position_length": 0.0,
            "efficiency_score": 0.0,
            "total_expectancy": 0.0,
            "diversification_multiplier": 0.0,
            "independence_multiplier": 0.0,
            "activity_multiplier": 0.0,
            "strategy_expectancies": [],
            "strategy_efficiency_metrics": {},
            "risk_metrics": {},
            "signal_metrics": signal_metrics,
            "signal_quality_metrics": {},
            "start_date": "",
            "end_date": ""
        }
        raise
