"""
ATR Trailing Stop Portfolio Analysis for MA Cross Strategy

This module implements ATR trailing stop parameter sensitivity analysis,
processing 860 combinations of ATR parameters to optimize exit timing
while using proven MA Cross entry configurations.

Key Features:
- Fixed MA Cross entry parameters (SMA 51/69)
- ATR parameter sweep: 20 lengths × 42 multipliers = 840 combinations
- Memory-optimized processing with progress tracking
- Export to ATR Extended portfolio schema with _ATR suffix
"""

import os
import time
from typing import Any, Dict, List

import polars as pl

from app.strategies.ma_cross.tools.atr_parameter_sweep import create_atr_sweep_engine
from app.tools.cache_utils import CacheConfig
from app.tools.entry_point import run_from_command_line
from app.tools.logging_context import logging_context
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType
from app.tools.portfolio.filtering_service import PortfolioFilterService
from app.tools.portfolio_results import sort_portfolios
from app.tools.project_utils import get_project_root

# ATR-specific configuration based on proven MA Cross settings
default_config: CacheConfig = {
    "TICKER": "TSLA",
    "FAST_PERIOD": 10,  # Proven MA Cross entry configuration
    "SLOW_PERIOD": 20,  # Proven MA Cross entry configuration
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
    # ATR Parameter Range Configuration
    "ATR_LENGTH_MIN": 2,  # Minimum ATR period length
    "ATR_LENGTH_MAX": 14,  # Maximum ATR period length
    "ATR_MULTIPLIER_MIN": 1.5,  # Minimum ATR multiplier for stop distance
    "ATR_MULTIPLIER_MAX": 8,  # Maximum ATR multiplier for stop distance
    "ATR_MULTIPLIER_STEP": 0.5,  # Step size for ATR multiplier increments
    # "ATR_LENGTH_MIN": 2,        # Minimum ATR period length
    # "ATR_LENGTH_MAX": 12,       # Maximum ATR period length
    # "ATR_MULTIPLIER_MIN": 1.5,  # Minimum ATR multiplier for stop distance
    # "ATR_MULTIPLIER_MAX": 8.0, # Maximum ATR multiplier for stop distance
    # "ATR_MULTIPLIER_STEP": 1, # Step size for ATR multiplier increments
    "MINIMUMS": {
        "WIN_RATE": 0.5,
        "TRADES": 44,
        "EXPECTANCY_PER_TRADE": 0.5,
        "PROFIT_FACTOR": 1.236,
        "SORTINO_RATIO": 0.5,
    },
    "SORT_BY": "Score",
    "SORT_ASC": False,
}


def execute_atr_analysis_for_ticker(
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
    log(f"=== Starting ATR analysis for {ticker} ===", "info")
    analysis_start_time = time.time()

    try:
        # Create ATR parameter sweep engine
        sweep_engine = create_atr_sweep_engine(
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

        # Log ATR parameter ranges
        atr_length_min = config.get("ATR_LENGTH_MIN", 2)
        atr_length_max = config.get("ATR_LENGTH_MAX", 21)
        atr_multiplier_min = config.get("ATR_MULTIPLIER_MIN", 1.5)
        atr_multiplier_max = config.get("ATR_MULTIPLIER_MAX", 10.0)
        atr_multiplier_step = config.get("ATR_MULTIPLIER_STEP", 0.2)

        # Calculate expected combinations
        length_count = atr_length_max - atr_length_min + 1
        multiplier_count = int(
            (atr_multiplier_max - atr_multiplier_min) / atr_multiplier_step
        )
        expected_combinations = length_count * multiplier_count

        log(f"ATR parameter ranges:", "info")
        log(
            f"  ATR Length: {atr_length_min} to {atr_length_max} ({length_count} values)",
            "info",
        )
        log(
            f"  ATR Multiplier: {atr_multiplier_min} to {atr_multiplier_max} step {atr_multiplier_step} ({multiplier_count} values)",
            "info",
        )
        log(f"  Expected combinations: {expected_combinations}", "info")

        # Execute the parameter sweep
        portfolio_results, sweep_stats = sweep_engine.execute_atr_parameter_sweep(
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
                f"ATR sweep validation failed for {ticker}: {len(validation_errors)} errors",
                "error",
            )
            for error in validation_errors[:3]:  # Log first 3 errors
                log(f"  Validation error: {error}", "error")
            return []

        # Log final statistics
        analysis_duration = time.time() - analysis_start_time
        log(f"=== ATR analysis completed for {ticker} ===", "info")
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
        log(f"ATR analysis failed for {ticker}: {str(e)}", "error")
        import traceback

        log(f"Error details: {traceback.format_exc()}", "error")
        return []


def export_atr_portfolios(
    portfolios: List[Dict[str, Any]],
    ticker: str,
    config: CacheConfig,
    log: callable,
) -> bool:
    """
    Export ATR portfolios to CSV with _ATR suffix naming.

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
        sorted_portfolios = sort_portfolios(filtered_portfolios, config)

        # Create filename with _ATR suffix
        strategy_type = "SMA" if config.get("USE_SMA", True) else "EMA"
        filename = f"{ticker}_D_{strategy_type}_{config['FAST_PERIOD']}_{config['SLOW_PERIOD']}_ATR.csv"

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

        if detected_schema != SchemaType.EXTENDED:
            log(
                f"Warning: Expected Extended schema (with universal exit parameters), detected {detected_schema}",
                "warning",
            )

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
            f"Exported {len(sorted_portfolios)} sorted ATR portfolios to {export_path}",
            "info",
        )
        return True

    except Exception as e:
        log(f"Failed to export ATR portfolios for {ticker}: {str(e)}", "error")
        return False


def run_atr_analysis(config: CacheConfig = None) -> bool:
    """
    Run ATR trailing stop parameter sensitivity analysis.

    Args:
        config: Configuration dictionary (uses default_config if None)

    Returns:
        True if analysis successful, False otherwise
    """
    if config is None:
        config = default_config.copy()

    with logging_context(
        module_name="ma_cross_atr", log_file="3_get_atr_stop_portfolios.log"
    ) as log:
        log("=== ATR Trailing Stop Parameter Sensitivity Analysis ===", "info")
        log(
            f"Configuration: MA Cross SMA({config['FAST_PERIOD']}/{config['SLOW_PERIOD']}) + ATR Trailing Stops",
            "info",
        )

        # Calculate and log target combinations dynamically
        atr_length_min = config.get("ATR_LENGTH_MIN", 2)
        atr_length_max = config.get("ATR_LENGTH_MAX", 21)
        atr_multiplier_min = config.get("ATR_MULTIPLIER_MIN", 1.5)
        atr_multiplier_max = config.get("ATR_MULTIPLIER_MAX", 10.0)
        atr_multiplier_step = config.get("ATR_MULTIPLIER_STEP", 0.2)

        length_count = atr_length_max - atr_length_min + 1
        multiplier_count = int(
            (atr_multiplier_max - atr_multiplier_min) / atr_multiplier_step
        )
        target_combinations = length_count * multiplier_count

        log(
            f"ATR Length Range: {atr_length_min}-{atr_length_max} ({length_count} values)",
            "info",
        )
        log(
            f"ATR Multiplier Range: {atr_multiplier_min}-{atr_multiplier_max} step {atr_multiplier_step} ({multiplier_count} values)",
            "info",
        )
        log(
            f"Target combinations: {target_combinations} ({length_count} lengths × {multiplier_count} multipliers)",
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

            # Execute ATR analysis for this ticker
            ticker_portfolios = execute_atr_analysis_for_ticker(ticker, config, log)

            if ticker_portfolios:
                total_portfolios += len(ticker_portfolios)

                # Export results
                if export_atr_portfolios(ticker_portfolios, ticker, config, log):
                    successful_exports += 1
                    log(f"Successfully exported ATR results for {ticker}", "info")
                else:
                    log(f"Failed to export ATR results for {ticker}", "error")
            else:
                log(f"No ATR portfolios generated for {ticker}", "warning")

        # Final summary
        log("\n=== ATR Analysis Summary ===", "info")
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
        run_atr_analysis, default_config, "ATR Trailing Stop Parameter Analysis"
    )
