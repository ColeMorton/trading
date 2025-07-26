"""
MACD Sensitivity Analysis Module

This module handles parameter sensitivity analysis for MACD cross strategies,
analyzing combinations of short EMA, long EMA, and signal line windows.
"""

from typing import Any, Callable, Dict, Optional

import polars as pl

from app.tools.portfolio.collection import sort_portfolios
from app.tools.strategy.sensitivity_analysis import (
    analyze_parameter_combinations as base_analyze_parameter_combinations,
)


def analyze_parameter_combinations(
    data: pl.DataFrame,
    short_windows: range,
    long_windows: range,
    signal_windows: range,
    config: Dict[str, Any],
    log: Callable,
) -> Optional[pl.DataFrame]:
    """
    Perform MACD parameter sensitivity analysis across window combinations.

    Args:
        data: Price data DataFrame
        short_windows: Range of short EMA window values
        long_windows: Range of long EMA window values
        signal_windows: Range of signal line window values
        config: Configuration dictionary with MACD parameters
        log: Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: DataFrame containing portfolio results, None if analysis fails
    """
    try:
        log("Starting MACD parameter sensitivity analysis")

        # Generate MACD parameter combinations from the provided ranges
        parameter_sets = []
        for short_window in short_windows:
            for long_window in long_windows:
                if long_window <= short_window:  # Skip invalid combinations
                    continue
                for signal_window in signal_windows:
                    parameter_sets.append(
                        {
                            "short_window": short_window,
                            "long_window": long_window,
                            "signal_window": signal_window,
                        }
                    )

        log(f"Generated {len(parameter_sets)} MACD parameter combinations")

        # Analyze all parameter combinations using centralized framework
        portfolios = base_analyze_parameter_combinations(
            data,
            parameter_sets,
            config,
            log,
            strategy_type="MACD",
        )

        if portfolios is None or (
            isinstance(portfolios, list) and len(portfolios) == 0
        ):
            log("No valid MACD portfolios generated", "warning")
            return None

        # Create DataFrame and use centralized sorting
        df = pl.DataFrame(portfolios)
        df = sort_portfolios(df, config)

        # Export results
        export_results(df, config, log)

        return df

    except Exception as e:
        log(f"MACD parameter sensitivity analysis failed: {e}", "error")
        return None


def analyze_parameter_combination(
    data: pl.DataFrame,
    short_window: int,
    long_window: int,
    signal_window: int,
    config: Dict[str, Any],
    log: Callable,
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single MACD parameter combination.

    Args:
        data: Price data DataFrame
        short_window: Short EMA window
        long_window: Long EMA window
        signal_window: Signal line window
        config: Configuration dictionary
        log: Logging function

    Returns:
        Optional[Dict[str, Any]]: Portfolio result dictionary or None if analysis fails
    """
    try:
        # Import MACD signal generation
        from app.strategies.macd.tools.signal_generation import generate_macd_signals

        # Create temporary config for this parameter combination
        temp_config = config.copy()
        temp_config.update({
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
        })

        # Generate signals for this parameter combination
        signal_data = generate_macd_signals(data.clone(), temp_config)
        if signal_data is None or len(signal_data) == 0:
            return None

        # Import portfolio analysis from the unified framework
        from app.tools.strategy.sensitivity_analysis import analyze_single_portfolio

        # Analyze the portfolio using the centralized framework
        result = analyze_single_portfolio(
            signal_data, temp_config, log, strategy_type="MACD"
        )

        if result is not None:
            # Add MACD-specific parameters to the result
            result.update({
                "Short Window": short_window,
                "Long Window": long_window,
                "Signal Window": signal_window,
            })

        return result

    except Exception as e:
        log(f"Failed to analyze MACD parameter combination {short_window}/{long_window}/{signal_window}: {str(e)}", "error")
        return None


def export_results(df: pl.DataFrame, config: Dict[str, Any], log: Callable) -> None:
    """
    Export MACD analysis results to CSV.

    Args:
        df: DataFrame containing analysis results
        config: Configuration dictionary
        log: Logging function for recording events and errors
    """
    try:
        log(f"Exporting MACD results for {config.get('TICKER', '')}")

        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios

        # Export using centralized portfolio export functionality
        export_portfolios(
            portfolios=df.to_dicts(), config=config, export_type="portfolios", log=log
        )

        log("MACD analysis results exported successfully")
        print(f"MACD analysis complete. Total rows in output: {len(df)}")

    except Exception as e:
        log(f"Failed to export MACD results: {e}", "error")
        raise
