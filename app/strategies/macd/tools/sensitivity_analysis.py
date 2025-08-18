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
    fast_periods: range = None,
    slow_periods: range = None,
    signal_periods: range = None,
    short_windows: range = None,
    long_windows: range = None,
    signal_windows: range = None,
    config: Dict[str, Any] = None,
    log: Callable = None,
) -> Optional[pl.DataFrame]:
    """
    Perform MACD parameter sensitivity analysis across period combinations.

    Args:
        data: Price data DataFrame
        fast_periods: Range of fast EMA period values (new parameter name)
        slow_periods: Range of slow EMA period values (new parameter name)
        signal_periods: Range of signal line period values (new parameter name)
        short_windows: Range of short EMA window values (legacy parameter name)
        long_windows: Range of long EMA window values (legacy parameter name)
        signal_windows: Range of signal line window values (legacy parameter name)
        config: Configuration dictionary with MACD parameters
        log: Logging function for recording events and errors

    Returns:
        Optional[pl.DataFrame]: DataFrame containing portfolio results, None if analysis fails
    """
    try:
        log("Starting MACD parameter sensitivity analysis")

        # Handle both new and legacy parameter names
        fast_range = fast_periods or short_windows
        slow_range = slow_periods or long_windows
        signal_range = signal_periods or signal_windows

        if fast_range is None or slow_range is None or signal_range is None:
            raise ValueError(
                "Must provide either fast_periods/slow_periods/signal_periods or short_windows/long_windows/signal_windows"
            )

        # Generate MACD parameter combinations from the provided ranges
        parameter_sets = []
        for fast_period in fast_range:
            for slow_period in slow_range:
                if slow_period <= fast_period:  # Skip invalid combinations
                    continue
                for signal_period in signal_range:
                    parameter_sets.append(
                        {
                            "fast_period": fast_period,
                            "slow_period": slow_period,
                            "signal_period": signal_period,
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
    fast_period: int = None,
    slow_period: int = None,
    signal_period: int = None,
    config: Dict[str, Any] = None,
    log: Callable = None,
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single MACD parameter combination.

    Args:
        data: Price data DataFrame
        fast_period: Fast EMA period (new parameter name)
        slow_period: Slow EMA period (new parameter name)
        signal_period: Signal period (new parameter name)
        fast_period: Short EMA window (legacy parameter name)
        slow_period: Long EMA window (legacy parameter name)
        signal_period: Signal line window (legacy parameter name)
        config: Configuration dictionary
        log: Logging function

    Returns:
        Optional[Dict[str, Any]]: Portfolio result dictionary or None if analysis fails
    """
    try:
        # Import MACD signal generation
        from app.strategies.macd.tools.signal_generation import generate_macd_signals

        # Handle both new and legacy parameter names
        fast = fast_period or fast_period
        slow = slow_period or slow_period
        signal = signal_period or signal_period

        if fast is None or slow is None or signal is None:
            raise ValueError(
                "Must provide either fast_period/slow_period/signal_period or fast_period/slow_period/signal_period parameters"
            )

        # Create temporary config for this parameter combination
        temp_config = config.copy()
        temp_config.update(
            {
                "fast_period": fast,
                "slow_period": slow,
                "signal_period": signal,
                # Keep legacy names for backwards compatibility
                "fast_period": fast,
                "slow_period": slow,
                "signal_period": signal,
            }
        )

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
            # Add MACD-specific parameters to the result with new column names
            result.update(
                {
                    "Fast Period": fast,
                    "Slow Period": slow,
                    "Signal Period": signal,
                    # Keep legacy names for backwards compatibility during transition
                    "Fast Period": fast,
                    "Slow Period": slow,
                    "Signal Period": signal,
                }
            )

        return result

    except Exception as e:
        fast = fast_period or fast_period
        slow = slow_period or slow_period
        signal = signal_period or signal_period
        log(
            f"Failed to analyze MACD parameter combination {fast}/{slow}/{signal}: {str(e)}",
            "error",
        )
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
            portfolios=df.to_dicts(), config=config, export_type="strategies", log=log
        )

        log("MACD analysis results exported successfully")
        print(f"MACD analysis complete. Total rows in output: {len(df)}")

    except Exception as e:
        log(f"Failed to export MACD results: {e}", "error")
        raise
