"""
Volume-Based Exit Portfolio Analysis for MA Cross Strategy

This module implements volume and EMA-based exit parameter sensitivity analysis,
processing 231 combinations of exit parameters to optimize exit timing
while using proven MA Cross entry configurations.

Exit Criteria: RVOL(volume_Lookback) >= X AND Price Close < EMA(N)

Key Features:
- Fixed MA Cross entry parameters (SMA 53/64)
- Volume exit parameter sweep: 11 EMA periods × 7 RVOL thresholds × 3 volume lookbacks = 231 combinations
- Memory-optimized processing with progress tracking
- Export to Volume Extended portfolio schema with _VOLUME suffix
"""

import os
import time
from typing import Any, Dict, List

import polars as pl

from app.strategies.ma_cross.tools.volume_parameter_sweep import (
    create_volume_sweep_engine,
)
from app.tools.cache_utils import CacheConfig
from app.tools.entry_point import run_from_command_line
from app.tools.logging_context import logging_context
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType
from app.tools.portfolio.filtering_service import PortfolioFilterService
from app.tools.portfolio_results import sort_portfolios
from app.tools.project_utils import get_project_root

# Volume-specific configuration based on proven MA Cross settings
default_config: CacheConfig = {
    "TICKER": "AMD",
    "FAST_PERIOD": 19,  # Proven MA Cross entry configuration
    "SLOW_PERIOD": 29,  # Proven MA Cross entry configuration
    "BASE_DIR": get_project_root(),
    "USE_SMA": True,
    "REFRESH": True,
    "USE_HOURLY": False,
    "RELATIVE": False,
    "DIRECTION": "Long",
    "USE_CURRENT": False,
    "USE_RSI": False,
    "RSI_WINDOW": 4,
    "RSI_THRESHOLD": 52,
    # Volume Exit Parameter Configuration
    # Exit Criteria: RVOL(volume_Lookback) >= X AND Price Close < EMA(N)
    "EMA_PERIODS": [
        3,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        12,
        13,
    ],  # EMA periods for price exit (N)
    "RVOL_THRESHOLDS": [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0],  # RVOL thresholds (X)
    "VOLUME_LOOKBACKS": [10, 15, 20],  # Volume lookback periods for RVOL calculation
    # "MINIMUMS": {
    #     "WIN_RATE": 0.3,  # Reduced for initial testing
    #     "TRADES": 10,     # Reduced for initial testing
    #     # "WIN_RATE": 0.50,
    #     # "TRADES": 54,
    #     # "WIN_RATE": 0.61,
    #     "EXPECTANCY_PER_TRADE": 0.1,  # Reduced for initial testing
    #     "PROFIT_FACTOR": 1.0,         # Reduced for initial testing
    #     "SORTINO_RATIO": 0.1,         # Reduced for initial testing
    #     # "BEATS_BNH": 0
    #     # "BEATS_BNH": 0.13
    # },
    "SORT_BY": "Score",
    "SORT_ASC": False,
}


def execute_volume_analysis_for_ticker(
    ticker: str,
    config: CacheConfig,
    log: callable,
) -> List[Dict[str, Any]]:
    """
    Execute ATR parameter sensitivity analysis for a single ticker.

    Args:
        ticker: Ticker symbol to analyze
        config: Configuration dictionary
        log: Logging function

    Returns:
        List of ATR portfolio results
    """
    log(f"=== Starting volume analysis for {ticker} ===", "info")
    analysis_start_time = time.time()

    try:
        # Create volume parameter sweep engine
        sweep_engine = create_volume_sweep_engine(
            config, enable_memory_optimization=True  # Use sensible default
        )

        # Prepare MA Cross configuration for fixed entry parameters
        ma_config = {
            "TICKER": ticker,
            "FAST_PERIOD": config["FAST_PERIOD"],
            "SLOW_PERIOD": config["SLOW_PERIOD"],
            "USE_SMA": config["USE_SMA"],
            "BASE_DIR": config["BASE_DIR"],
            "REFRESH": config["REFRESH"],
            "USE_HOURLY": config["USE_HOURLY"],
            "DIRECTION": config["DIRECTION"],
            "USE_CURRENT": config["USE_CURRENT"],
        }

        log(
            f"MA Cross entry configuration: SMA({config['FAST_PERIOD']}/{config['SLOW_PERIOD']})",
            "info",
        )

        # Log volume parameter ranges
        ema_periods = config.get("EMA_PERIODS", [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
        rvol_thresholds = config.get(
            "RVOL_THRESHOLDS", [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        )
        volume_lookbacks = config.get("VOLUME_LOOKBACKS", [10, 15, 20])

        # Calculate expected combinations
        expected_combinations = (
            len(ema_periods) * len(rvol_thresholds) * len(volume_lookbacks)
        )

        log(f"Volume parameter ranges:", "info")
        log(f"  EMA Periods: {config.get('EMA_PERIODS', [])}", "info")
        log(f"  RVOL Thresholds: {config.get('RVOL_THRESHOLDS', [])}", "info")
        log(f"  Volume Lookbacks: {config.get('VOLUME_LOOKBACKS', [])}", "info")
        log(f"  Expected combinations: {expected_combinations}", "info")

        # Execute the parameter sweep
        portfolio_results, sweep_stats = sweep_engine.execute_volume_parameter_sweep(
            ticker,
            ma_config,
            log,
            use_concurrent=False,  # Disable concurrent processing to avoid threading issues
        )

        # Validate sweep results
        is_valid, validation_errors = sweep_engine.validate_sweep_results(
            portfolio_results, log
        )
        if not is_valid:
            log(
                f"Volume sweep validation failed for {ticker}: {len(validation_errors)} errors",
                "error",
            )
            for error in validation_errors[:3]:  # Log first 3 errors
                log(f"  Validation error: {error}", "error")
            return []

        # Log final statistics
        analysis_duration = time.time() - analysis_start_time
        log(f"=== Volume analysis completed for {ticker} ===", "info")
        log(f"  Total portfolios generated: {len(portfolio_results)}", "info")
        log(f"  Analysis duration: {analysis_duration:.2f}s", "info")
        log(
            f"  Processing rate: {len(portfolio_results) / analysis_duration:.1f} portfolios/second",
            "info",
        )

        if sweep_stats.get("successful_combinations", 0) > 0:
            success_rate = (
                sweep_stats["successful_combinations"]
                / sweep_stats["total_combinations"]
                * 100
            )
            log(f"  Success rate: {success_rate:.1f}%", "info")

        return portfolio_results

    except Exception as e:
        log(f"Volume analysis failed for {ticker}: {str(e)}", "error")
        import traceback

        log(f"Error details: {traceback.format_exc()}", "error")
        return []


def export_volume_portfolios(
    portfolios: List[Dict[str, Any]],
    ticker: str,
    config: CacheConfig,
    log: callable,
) -> bool:
    """
    Export volume portfolios to CSV with _VOLUME suffix naming.

    Args:
        portfolios: List of portfolio dictionaries
        ticker: Ticker symbol
        config: Configuration dictionary
        log: Logging function

    Returns:
        True if export successful, False otherwise
    """
    if not portfolios:
        log(f"No portfolios to export for {ticker}", "warning")
        return False

    try:
        # Apply MINIMUMS filtering before sorting using the same logic as 1_get_portfolios.py
        filter_service = PortfolioFilterService()
        filtered_portfolios = filter_service.filter_portfolios_list(
            portfolios, config, log
        )

        if not filtered_portfolios:
            log(f"No portfolios passed MINIMUMS filtering for {ticker}", "warning")
            return False

        log(
            f"Filtered portfolios: {len(portfolios)} → {len(filtered_portfolios)} (passed MINIMUMS criteria)",
            "info",
        )

        # Sort portfolios after filtering
        sort_by = config.get("SORT_BY", "Score")
        sort_asc = config.get("SORT_ASC", False)

        log(
            f"Sorting {len(filtered_portfolios)} portfolios by '{sort_by}' (ascending: {sort_asc})",
            "info",
        )
        sorted_portfolios = sort_portfolios(filtered_portfolios, sort_by, sort_asc)

        # Create filename with _VOLUME suffix
        strategy_type = "SMA" if config.get("USE_SMA", True) else "EMA"
        filename = f"{ticker}_D_{strategy_type}_{config['FAST_PERIOD']}_{config['SLOW_PERIOD']}_VOLUME.csv"

        # Determine export directory
        base_dir = config.get("BASE_DIR", ".")
        export_dir = os.path.join(base_dir, "csv", "portfolios")

        # Ensure export directory exists
        os.makedirs(export_dir, exist_ok=True)

        # Convert to Polars DataFrame for export
        portfolios_df = pl.DataFrame(sorted_portfolios)

        # Verify schema compliance
        schema_transformer = SchemaTransformer()
        sample_portfolio = sorted_portfolios[0]
        detected_schema = schema_transformer.detect_schema_type(sample_portfolio)

        log(f"Detected portfolio schema: {detected_schema}", "info")

        # Convert duration columns to strings for CSV compatibility
        # Convert to pandas first for easier duration handling, then back to polars
        portfolios_pd = portfolios_df.to_pandas()

        duration_columns = [
            "Period",
            "Max Drawdown Duration",
            "Avg Winning Trade Duration",
            "Avg Losing Trade Duration",
            "Avg Trade Duration",
        ]

        for col in duration_columns:
            if col in portfolios_pd.columns:
                # Convert any duration-like columns to string representation
                portfolios_pd[col] = portfolios_pd[col].astype(str)

        # Convert back to polars
        portfolios_df = pl.from_pandas(portfolios_pd)

        # Export portfolios to CSV
        export_path = os.path.join(export_dir, filename)
        portfolios_df.write_csv(export_path)

        log(
            f"Exported {len(sorted_portfolios)} sorted volume portfolios to {export_path}",
            "info",
        )
        return True

    except Exception as e:
        log(f"Failed to export volume portfolios for {ticker}: {str(e)}", "error")
        return False


def run_volume_analysis(config: CacheConfig = None) -> bool:
    """
    Run volume-based exit parameter sensitivity analysis.

    Args:
        config: Configuration dictionary (uses default_config if None)

    Returns:
        True if analysis successful, False otherwise
    """
    if config is None:
        config = default_config.copy()

    with logging_context(
        module_name="ma_cross_volume", log_file="3_get_volume_stop_portfolios.log"
    ) as log:
        log("=== Volume-Based Exit Parameter Sensitivity Analysis ===", "info")
        log(
            f"Configuration: MA Cross SMA({config['FAST_PERIOD']}/{config['SLOW_PERIOD']}) + Volume Exits",
            "info",
        )

        # Calculate and log target combinations dynamically
        ema_periods = config.get("EMA_PERIODS", [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])
        rvol_thresholds = config.get(
            "RVOL_THRESHOLDS", [1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0]
        )
        volume_lookbacks = config.get("VOLUME_LOOKBACKS", [10, 15, 20])

        ema_count = len(ema_periods)
        rvol_count = len(rvol_thresholds)
        lookback_count = len(volume_lookbacks)
        target_combinations = ema_count * rvol_count * lookback_count

        log(f"EMA Periods: {ema_periods} ({ema_count} values)", "info")
        log(f"RVOL Thresholds: {rvol_thresholds} ({rvol_count} values)", "info")
        log(f"Volume Lookbacks: {volume_lookbacks} ({lookback_count} values)", "info")
        log(
            f"Target combinations: {target_combinations} ({ema_count} EMAs × {rvol_count} thresholds × {lookback_count} lookbacks)",
            "info",
        )

        # Handle single ticker or multiple tickers
        tickers = config.get("TICKER", "AMZN")
        if isinstance(tickers, str):
            tickers = [tickers]

        log(f"Processing {len(tickers)} ticker(s): {', '.join(tickers)}", "info")

        total_portfolios = 0
        successful_exports = 0

        for i, ticker in enumerate(tickers):
            log(f"\n--- Processing ticker {i+1}/{len(tickers)}: {ticker} ---", "info")

            # Execute volume analysis for this ticker
            ticker_portfolios = execute_volume_analysis_for_ticker(ticker, config, log)

            if ticker_portfolios:
                total_portfolios += len(ticker_portfolios)

                # Export results
                if export_volume_portfolios(ticker_portfolios, ticker, config, log):
                    successful_exports += 1
                    log(f"Successfully exported volume results for {ticker}", "info")
                else:
                    log(f"Failed to export volume results for {ticker}", "error")
            else:
                log(f"No volume portfolios generated for {ticker}", "warning")

        # Final summary
        log("\n=== Volume Analysis Summary ===", "info")
        log(f"Tickers processed: {len(tickers)}", "info")
        log(f"Total portfolios generated: {total_portfolios}", "info")
        log(f"Successful exports: {successful_exports}/{len(tickers)}", "info")

        if total_portfolios > 0:
            log(
                f"Average portfolios per ticker: {total_portfolios / len(tickers):.1f}",
                "info",
            )

        success = successful_exports == len(tickers) and total_portfolios > 0
        log(
            f"Analysis {'COMPLETED SUCCESSFULLY' if success else 'COMPLETED WITH ISSUES'}",
            "info" if success else "warning",
        )

        return success


if __name__ == "__main__":
    run_from_command_line(
        run_volume_analysis, default_config, "Volume-Based Exit Parameter Analysis"
    )
