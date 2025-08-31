from typing import Any, Callable, Dict, Optional

import polars as pl

# Import export_portfolios inside functions to avoid circular imports
from app.tools.portfolio.collection import sort_portfolios
from app.tools.strategy.sensitivity_analysis import analyze_parameter_combinations


def analyze_parameter_sensitivity(
    data: pl.DataFrame,
    short_windows: list[int],
    long_windows: list[int],
    config: Dict[str, Any],
    log: Callable,
) -> Optional[pl.DataFrame]:
    """
    Perform parameter sensitivity analysis and export results.

    Args:
        data: Price data DataFrame
        short_windows: List of fast period periods
        long_windows: List of slow period periods
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: DataFrame containing portfolio results, None if analysis fails
    """
    try:
        log("Starting parameter sensitivity analysis")

        # Convert window lists to parameter sets format for unified framework
        parameter_sets = []
        for fast_period in short_windows:
            for slow_period in long_windows:
                if fast_period < slow_period:  # Ensure short < long
                    parameter_sets.append(
                        {"fast_period": fast_period, "slow_period": slow_period}
                    )

        # Handle multiple strategy types
        strategy_types = config.get(
            "strategy_types", [config.get("STRATEGY_TYPE", "SMA")]
        )
        if isinstance(strategy_types, str):
            strategy_types = [strategy_types]

        log(f"Analyzing {len(strategy_types)} strategy type(s): {strategy_types}")

        all_portfolios = []
        for strategy_type in strategy_types:
            log(f"Analyzing parameter combinations for {strategy_type} strategy")

            # Enable parallel processing for large parameter sets
            use_parallel = len(parameter_sets) > 10 and config.get(
                "ENABLE_PARALLEL", True
            )

            # Analyze parameter combinations for this strategy type
            strategy_portfolios = analyze_parameter_combinations(
                data,
                parameter_sets,
                config,
                log,
                strategy_type=strategy_type,
                parallel=use_parallel,
            )

            if strategy_portfolios:
                log(
                    f"Generated {len(strategy_portfolios)} portfolios for {strategy_type}"
                )
                all_portfolios.extend(strategy_portfolios)
            else:
                log(f"No portfolios generated for {strategy_type}", "warning")

        portfolios = all_portfolios

        if not portfolios:
            log("No valid portfolios generated", "warning")
            return None

        # Create DataFrame and use centralized sorting
        df = pl.DataFrame(portfolios)
        df = sort_portfolios(df, config)

        # Export results
        export_results(df, config, log)

        return df

    except Exception as e:
        log(f"Parameter sensitivity analysis failed: {e}", "error")
        return None


def export_results(df: pl.DataFrame, config: Dict[str, Any], log: Callable) -> None:
    """
    Export analysis results to CSV.

    Args:
        df: DataFrame containing analysis results
        config: Configuration dictionary
        log: Logging function for recording events and errors
    """
    try:
        log(f"Exporting results for {config.get('TICKER', '')}")
        log(f"USE_HOURLY: {config.get('USE_HOURLY', False)}")
        log(f"USE_SMA: {config.get('USE_SMA', False)}")
        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios

        # Export using centralized portfolio export functionality
        export_portfolios(
            portfolios=df.to_dicts(), config=config, export_type="portfolios", log=log
        )

        log("Analysis results exported successfully")
        log(f"Analysis complete. Total rows in output: {len(df)}", "debug")

    except Exception as e:
        log(f"Failed to export results: {e}", "error")
        raise
