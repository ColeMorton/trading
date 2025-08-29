"""
Update Portfolios Module for Multiple Strategy Types

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of SMA, EMA, and MACD strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.

The module supports both regular tickers and synthetic tickers (identified by an underscore
in the ticker name, e.g., 'STRK_MSTR'). Synthetic tickers are automatically detected and
processed by splitting them into their component tickers.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.tools.summary_processing import (
    process_ticker_portfolios,
    update_strategy_files,
)
from app.tools.config_management import normalize_config, resolve_portfolio_filename
from app.tools.entry_point import run_from_command_line
from app.tools.error_context import error_context
from app.tools.error_decorators import handle_errors
from app.tools.exceptions import (
    ExportError,
    PortfolioLoadError,
    StrategyProcessingError,
    SyntheticTickerError,
    TradingSystemError,
)
from app.tools.logging_context import logging_context
from app.tools.portfolio import PortfolioLoadError  # Using specific error type
from app.tools.portfolio import load_portfolio_with_logging  # Using enhanced loader
from app.tools.portfolio.allocation import (
    calculate_position_sizes,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    get_allocation_summary,
    normalize_allocations,
    validate_allocations,
)
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    normalize_portfolio_data,
)
from app.tools.portfolio.stop_loss import (
    get_stop_loss_summary,
    normalize_stop_loss,
    validate_stop_loss,
)
from app.tools.portfolio_results import (
    calculate_breadth_metrics,
    display_portfolio_summary,
    filter_open_trades,
    filter_signal_entries,
    sort_portfolios,
)
from app.tools.project_utils import get_project_root
from app.tools.strategy_utils import filter_portfolios_by_signal
from app.tools.synthetic_ticker import detect_synthetic_ticker, process_synthetic_ticker

# Default Configuration
config = {
    # "PORTFOLIO": 'BTC-USD_SPY_d.csv',
    # "PORTFOLIO": 'portfolio_risk.csv',
    # "PORTFOLIO": 'crypto_d_20250421.csv',
    # "PORTFOLIO": "DAILY_crypto.csv",
    "PORTFOLIO": "DAILY.csv",
    # "PORTFOLIO": 'DAILY_test.csv',
    # "PORTFOLIO": 'crypto_h.csv',
    # "PORTFOLIO": 'DAILY_crypto_short.csv',
    # "PORTFOLIO": 'Indices_d.csv',
    # "PORTFOLIO": "trades_20250605.csv",
    # "PORTFOLIO": 'portfolio_d_20250510.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": "QQQ_d_20250404.csv",
    # "PORTFOLIO": "TLT_d_20250404.csv",
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    # "PORTFOLIO": 'BTC_MSTR_TLT_d_20250404.csv',
    # "PORTFOLIO": "protected.csv",
    # "PORTFOLIO": "live_signals.csv",
    # "PORTFOLIO": "risk_on.csv",
    # "PORTFOLIO": 'MSTY_h.csv',
    # "PORTFOLIO": 'BTC_h_20250416.csv',
    # "PORTFOLIO": 'STRK_h_20250415.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": 'SPY_QQQ_RSP_20250506.csv',
    "REFRESH": True,
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": get_project_root(),  # Use standardized project root resolver
    "DIRECTION": "Long",
    "SORT_BY": "Score",
    "SORT_ASC": False,
    "EQUITY_DATA": {
        "EXPORT": True,
        "METRIC": "mean",
        # Automatic Fresh Analysis Control:
        # - True: Always run fresh analysis to generate equity data (ignore existing files)
        # - False: Only generate missing equity data files (skip if file already exists)
        # This enables intelligent equity export that avoids redundant processing.
        "FORCE_FRESH_ANALYSIS": True,  # Set to True to force regeneration of all equity files
    },
}


@handle_errors(
    "Portfolio update process",
    {
        PortfolioLoadError: PortfolioLoadError,
        ValueError: StrategyProcessingError,
        KeyError: StrategyProcessingError,
        Exception: TradingSystemError,
    },
)
def run(portfolio: str) -> bool:
    """
    Process portfolio and generate portfolio summary.

    This function:
    1. Reads the portfolio
    2. Processes each ticker with appropriate strategy (SMA, EMA, or MACD)
    3. Detects and processes synthetic tickers (those containing an underscore)
    4. Calculates performance metrics and adjustments
    5. Exports combined results to CSV

    Args:
        portfolio (str): Name of the portfolio file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        PortfolioLoadError: If the portfolio cannot be loaded
        StrategyProcessingError: If there's an error processing a strategy
        SyntheticTickerError: If there's an issue with synthetic ticker processing
        ExportError: If results cannot be exported
        TradingSystemError: For other unexpected errors
    """
    with logging_context(
        module_name="strategies", log_file="update_portfolios.log"
    ) as log:
        import time

        start_time = time.time()

        # Get a normalized copy of the global config
        local_config = normalize_config(config.copy())
        
        # CRITICAL: Set portfolio update mode to prevent batch analysis triggers
        # This prevents dispatch_fresh_analysis from triggering comprehensive MACD analysis
        local_config["_PORTFOLIO_UPDATE_MODE"] = True
        
        # CRITICAL: Disable equity export during portfolio updates to prevent batch triggers
        # Portfolio updates should only process the input file, not trigger fresh analysis
        if "EQUITY_DATA" not in local_config:
            local_config["EQUITY_DATA"] = {}
        local_config["EQUITY_DATA"]["EXPORT"] = False

        # Detect 2-day timeframe from portfolio filename
        if "2D" in portfolio.upper():
            local_config["USE_2DAY"] = True
            log(
                f"Detected 2D suffix in portfolio name '{portfolio}' - enabling 2-day timeframe analysis",
                "info",
            )
        # Detect 4-hour timeframe from portfolio filename
        elif "4H" in portfolio.upper():
            local_config["USE_4HOUR"] = True
            log(
                f"Detected 4H suffix in portfolio name '{portfolio}' - enabling 4-hour timeframe analysis",
                "info",
            )

        # Use the enhanced portfolio loader with standardized error handling
        daily_df = None
        with error_context(
            "Loading portfolio", log, {FileNotFoundError: PortfolioLoadError}
        ):
            daily_df = load_portfolio_with_logging(portfolio, log, local_config)
            if not daily_df:
                return False

        # Check if portfolio was loaded successfully
        if not daily_df:
            return False

        # Detect schema version using the schema_detection module
        schema_version = detect_schema_version(daily_df)
        log(f"Detected schema version: {schema_version.name}", "info")

        # Normalize portfolio data to ensure consistent schema handling
        daily_df = normalize_portfolio_data(daily_df, schema_version, log)
        log(f"Normalized portfolio data with {len(daily_df)} rows", "info")

        # Process allocation and stop loss data if using extended schema
        if schema_version == SchemaVersion.EXTENDED:
            log("Processing allocation and stop loss data...", "info")

            # Process allocation values
            # Validate allocation values
            daily_df = validate_allocations(daily_df, log)

            # Normalize allocation field names
            daily_df = normalize_allocations(daily_df, log)

            # Get allocation summary before processing
            allocation_summary = get_allocation_summary(daily_df, log)
            log(f"Initial allocation summary: {allocation_summary}", "info")

            # Only process allocations if user explicitly provided them
            # Do not auto-distribute or auto-normalize empty allocations
            total_rows = (
                allocation_summary["allocated_rows"]
                + allocation_summary["unallocated_rows"]
            )

            # Only process if ALL rows have allocations (user explicitly set them)
            if (
                allocation_summary["allocated_rows"] == total_rows
                and allocation_summary["allocated_rows"] > 0
            ):
                # All positions have allocations - normalize them to sum to 100%
                daily_df = ensure_allocation_sum_100_percent(daily_df, log)

                # Get updated allocation summary
                updated_summary = get_allocation_summary(daily_df, log)
                log(f"Updated allocation summary: {updated_summary}", "info")
            elif (
                allocation_summary["allocated_rows"] > 0
                and allocation_summary["unallocated_rows"] > 0
            ):
                # Partial allocations - warn but don't auto-distribute
                log(
                    f"Warning: Partial allocations detected ({allocation_summary['allocated_rows']} of {total_rows} positions). Empty allocations will remain empty.",
                    "warning",
                )
            else:
                log(
                    "No allocations provided - keeping all allocations empty",
                    "info",
                )

            # Process stop loss values
            # Validate stop loss values
            daily_df = validate_stop_loss(daily_df, log)

            # Normalize stop loss field names
            daily_df = normalize_stop_loss(daily_df, log)

            # Get stop loss summary
            stop_loss_summary = get_stop_loss_summary(daily_df, log)
            log(f"Stop loss summary: {stop_loss_summary}", "info")

            # Add schema version to each row for future reference
            for row in daily_df:
                row["_schema_version"] = schema_version.name

        # Check for allocation and stop loss columns
        has_allocation = any(
            strategy.get("Allocation [%]") is not None
            and strategy.get("Allocation [%]") != ""
            and strategy.get("Allocation [%]") != "None"
            for strategy in daily_df
        )
        has_stop_loss = any(
            strategy.get("Stop Loss [%]") is not None
            and strategy.get("Stop Loss [%]") != ""
            and strategy.get("Stop Loss [%]") != "None"
            for strategy in daily_df
        )

        # Check for column existence even if values are empty
        has_allocation_column = any(
            "Allocation [%]" in strategy for strategy in daily_df
        )
        has_stop_loss_column = any("Stop Loss [%]" in strategy for strategy in daily_df)

        if has_allocation_column:
            log("Portfolio has Allocation [%] column", "info")
            if has_allocation:
                log("Portfolio contains allocation values", "info")
            else:
                log("Portfolio has Allocation [%] column but no values", "info")

        if has_stop_loss_column:
            log("Portfolio has Stop Loss [%] column", "info")
            if has_stop_loss:
                log("Portfolio contains stop loss values", "info")
            else:
                log("Portfolio has Stop Loss [%] column but no values", "info")

        # Set extended schema flag if either column exists
        if has_allocation_column or has_stop_loss_column:
            local_config["USE_EXTENDED_SCHEMA"] = True
            log("Using extended schema for processing", "info")

        portfolios = []

        # Process each ticker
        for strategy in daily_df:
            # Handle both "TICKER" and "Ticker" column names
            ticker = strategy.get("TICKER") or strategy.get("Ticker")
            if not ticker:
                log("ERROR: No ticker found in strategy row", "error")
                log(f"Available keys: {list(strategy.keys())}", "error")
                continue
            log(f"Processing {ticker}")
            # Create a copy of the config for this strategy
            strategy_config = local_config.copy()

            # Process allocation and stop loss values
            allocation_field = "Allocation [%]"
            stop_loss_field = "Stop Loss [%]"

            # Validate and normalize allocation value
            allocation = strategy.get(allocation_field)
            if allocation is not None and allocation != "" and allocation != "None":
                try:
                    allocation_value = float(allocation)
                    if 0 <= allocation_value <= 100:
                        strategy_config["ALLOCATION"] = allocation_value
                        log(
                            f"Using allocation {allocation_value}% for {ticker}", "info"
                        )
                    else:
                        log(
                            f"Invalid allocation value for {ticker}: {allocation_value} (must be between 0 and 100)",
                            "warning",
                        )
                except (ValueError, TypeError):
                    log(
                        f"Invalid allocation value for {ticker}: {allocation}",
                        "warning",
                    )

            # Validate and normalize stop loss value using the stop_loss utility
            stop_loss = strategy.get(stop_loss_field)
            if stop_loss is not None and stop_loss != "" and stop_loss != "None":
                # Use the validate_stop_loss function on a single-item list
                validated_data = validate_stop_loss([strategy], log)
                if (
                    validated_data
                    and validated_data[0].get(stop_loss_field) is not None
                ):
                    stop_loss_value = validated_data[0][stop_loss_field]
                    strategy_config["STOP_LOSS"] = stop_loss_value
                    log(f"Using stop loss {stop_loss_value}% for {ticker}", "info")
                else:
                    log(f"Invalid stop loss value for {ticker}: {stop_loss}", "warning")

            # Check if this is a synthetic ticker (contains underscore)
            with error_context(
                f"Processing synthetic ticker {ticker}",
                log,
                {ValueError: SyntheticTickerError},
                reraise=False,
            ):
                if detect_synthetic_ticker(ticker):
                    try:
                        ticker1, ticker2 = process_synthetic_ticker(ticker)
                        # Update config for synthetic ticker processing
                        strategy_config["USE_SYNTHETIC"] = True
                        strategy_config["TICKER_1"] = ticker1
                        strategy_config["TICKER_2"] = ticker2
                        log(
                            f"Detected synthetic ticker: {ticker} (components: {ticker1}, {ticker2})"
                        )
                    except SyntheticTickerError as e:
                        log(
                            f"Invalid synthetic ticker format: {ticker} - {str(e)}",
                            "warning",
                        )

            # Process the ticker portfolio
            with error_context(
                f"Processing ticker portfolio for {ticker}",
                log,
                {Exception: StrategyProcessingError},
                reraise=False,
            ):
                result = process_ticker_portfolios(
                    ticker, strategy, strategy_config, log
                )
                if result:
                    portfolios.extend(result)

                    # Ensure allocation and stop loss values are preserved in the result
                    for portfolio_result in result:
                        # Only set if not already set by process_ticker_portfolios
                        if (
                            "Allocation [%]" not in portfolio_result
                            or portfolio_result["Allocation [%]"] is None
                        ):
                            if (
                                allocation is not None
                                and allocation != ""
                                and allocation != "None"
                            ):
                                try:
                                    portfolio_result["Allocation [%]"] = float(
                                        allocation
                                    )
                                except (ValueError, TypeError):
                                    log(
                                        f"Invalid allocation value for {ticker}: {allocation}",
                                        "warning",
                                    )
                                    portfolio_result["Allocation [%]"] = None

                        if (
                            "Stop Loss [%]" not in portfolio_result
                            or portfolio_result["Stop Loss [%]"] is None
                        ):
                            if (
                                stop_loss is not None
                                and stop_loss != ""
                                and stop_loss != "None"
                            ):
                                try:
                                    portfolio_result["Stop Loss [%]"] = float(stop_loss)
                                except (ValueError, TypeError):
                                    log(
                                        f"Invalid stop loss value for {ticker}: {stop_loss}",
                                        "warning",
                                    )
                                    portfolio_result["Stop Loss [%]"] = None

                        # Ensure Last Position Open Date and Last Position Close Date are preserved
                        if (
                            "Last Position Open Date" not in portfolio_result
                            or portfolio_result["Last Position Open Date"] is None
                            or portfolio_result["Last Position Open Date"] == ""
                        ):
                            last_open_date = strategy.get("Last Position Open Date")
                            if (
                                last_open_date is not None
                                and last_open_date != ""
                                and last_open_date != "None"
                            ):
                                portfolio_result[
                                    "Last Position Open Date"
                                ] = last_open_date
                            else:
                                portfolio_result["Last Position Open Date"] = None

                        if (
                            "Last Position Close Date" not in portfolio_result
                            or portfolio_result["Last Position Close Date"] is None
                            or portfolio_result["Last Position Close Date"] == ""
                        ):
                            last_close_date = strategy.get("Last Position Close Date")
                            if (
                                last_close_date is not None
                                and last_close_date != ""
                                and last_close_date != "None"
                            ):
                                portfolio_result[
                                    "Last Position Close Date"
                                ] = last_close_date
                            else:
                                portfolio_result["Last Position Close Date"] = None

        # Export results with config
        with error_context(
            "Exporting summary results", log, {Exception: ExportError}, reraise=False
        ):
            # Ensure we're using the correct schema for export
            # This might have been set during schema detection, but let's make sure
            if (
                "USE_EXTENDED_SCHEMA" not in local_config
                or local_config["USE_EXTENDED_SCHEMA"] is None
            ):
                local_config["USE_EXTENDED_SCHEMA"] = True
                log("Explicitly setting USE_EXTENDED_SCHEMA=True for export", "info")

            success = update_strategy_files(portfolios, portfolio, log, local_config)
            # Display strategy data as requested
            if success and portfolios:
                log("=== Strategy Summary ===")

                # Clean portfolios before summary display (remove only EquityData objects)
                clean_portfolios = []
                for portfolio_data in portfolios:
                    clean_portfolio = {}
                    for key, value in portfolio_data.items():
                        # Only skip EquityData objects and internal fields, preserve all other data
                        if key == "_equity_data":
                            continue
                        # Convert complex objects to strings for DataFrame compatibility
                        if value is not None and not isinstance(
                            value, (str, int, float, bool)
                        ):
                            # Check if it's an EquityData object specifically
                            if hasattr(value, "__class__") and "EquityData" in str(
                                type(value)
                            ):
                                continue
                            try:
                                clean_portfolio[key] = str(value)
                            except Exception:
                                continue
                        else:
                            clean_portfolio[key] = value
                    clean_portfolios.append(clean_portfolio)

                # Defensive check: ensure we have data and columns for DataFrame creation
                if not clean_portfolios:
                    log(
                        "ERROR: No portfolios available for summary display after cleaning",
                        "error",
                    )
                    return

                # Verify we have essential columns for sorting
                sample_portfolio = clean_portfolios[0]
                essential_columns = [
                    "Score",
                    "Total Return [%]",
                    "Ticker",
                    "Strategy Type",
                ]
                available_columns = list(sample_portfolio.keys())

                # If no essential columns are present, log error and skip summary display
                if not any(col in available_columns for col in essential_columns):
                    log(
                        f"ERROR: No essential columns found for sorting. Available: {available_columns[:10]}...",
                        "error",
                    )
                    return

                # Sort cleaned portfolios using configuration for main display
                try:
                    sorted_portfolios = sort_portfolios(clean_portfolios, local_config)
                except Exception as e:
                    log(f"ERROR: Failed to sort portfolios: {str(e)}", "error")
                    return

                # Use standardized utility to filter and display open trades
                open_trades_strategies = filter_open_trades(sorted_portfolios, log)

                # Use standardized utility to filter and display signal entries
                # First get signal entries using the strategy_utils filter
                temp_config = {"USE_CURRENT": True}
                signal_entry_strategies = filter_portfolios_by_signal(
                    sorted_portfolios, temp_config, log
                )

                # Then use the portfolio_results utility to process and display them
                signal_entry_strategies = filter_signal_entries(
                    signal_entry_strategies, open_trades_strategies, log
                )

                # Calculate and display breadth metrics
                if sorted_portfolios:
                    calculate_breadth_metrics(
                        sorted_portfolios,
                        open_trades_strategies,
                        signal_entry_strategies,
                        log,
                    )

                # Use allocation utility to get allocation summary
                allocation_summary = get_allocation_summary(sorted_portfolios, log)
                log(f"Allocation summary: {allocation_summary}", "info")

                # Calculate position sizes if account value is provided
                if (
                    "ACCOUNT_VALUE" in local_config
                    and local_config["ACCOUNT_VALUE"] > 0
                ):
                    account_value = float(local_config["ACCOUNT_VALUE"])
                    position_sized_portfolios = calculate_position_sizes(
                        sorted_portfolios, account_value, log
                    )
                    log(
                        f"Calculated position sizes based on account value: {account_value}",
                        "info",
                    )

                    # Log position size summary
                    total_position_size = sum(
                        p.get("Position Size", 0) for p in position_sized_portfolios
                    )
                    log(
                        f"Total position size: {total_position_size:.2f} across {len(position_sized_portfolios)} strategies",
                        "info",
                    )

                # Use the stop_loss utility to get a summary of stop loss values
                stop_loss_summary = get_stop_loss_summary(sorted_portfolios, log)
                if stop_loss_summary["strategies_with_stop_loss"] > 0:
                    log(f"Stop loss summary: {stop_loss_summary}", "info")
                    log(
                        f"Average stop loss: {stop_loss_summary['average_stop_loss']:.2f}% across "
                        f"{stop_loss_summary['strategies_with_stop_loss']} strategies",
                        "info",
                    )

                # Display rich portfolio summary with execution time
                execution_time = time.time() - start_time
                display_portfolio_summary(sorted_portfolios, execution_time, log)

        return success


if __name__ == "__main__":
    import warnings

    # Show deprecation warning for direct script usage
    warnings.warn(
        "\n"
        "⚠️  DEPRECATION WARNING: Direct execution of this script is deprecated.\n"
        "   Use the unified CLI interface instead:\n"
        "   \n"
        "   Replace: python app/strategies/update_portfolios.py\n"
        "   With:    python -m app.cli portfolio update\n"
        "   \n"
        "   For more information: python -m app.cli portfolio --help\n"
        "   \n"
        "   This script will be removed in a future version.\n",
        DeprecationWarning,
        stacklevel=2,
    )

    # Create a normalized copy of the default config
    normalized_config = normalize_config(config.copy())
    portfolio_name = normalized_config.get("PORTFOLIO", "MSTR_d_20250403.csv")

    # Resolve portfolio filename with extension if needed
    resolved_portfolio = resolve_portfolio_filename(portfolio_name)

    # Check if the portfolio file exists and detect its schema
    portfolio_path = os.path.join(
        get_project_root(), "csv", "strategies", resolved_portfolio
    )
    if os.path.exists(portfolio_path):
        try:
            from app.tools.portfolio.schema_detection import (
                SchemaVersion,
                detect_schema_version_from_file,
            )

            schema_version = detect_schema_version_from_file(portfolio_path)
            print(
                f"Detected schema version for {resolved_portfolio}: {schema_version.name}"
            )
            use_extended = schema_version == SchemaVersion.EXTENDED
        except Exception as e:
            print(f"Error detecting schema version: {str(e)}")
            use_extended = True  # Default to extended schema on error for safety
    else:
        print(f"Portfolio file not found: {portfolio_path}")
        use_extended = True  # Default to extended schema if file not found

    # Set extended schema flag to ensure proper handling
    extended_config = {
        "USE_EXTENDED_SCHEMA": use_extended,  # Set based on detection
        "HANDLE_ALLOCATIONS": True,  # Enable allocation handling
        "HANDLE_STOP_LOSS": True,  # Enable stop loss handling
    }

    print(f"Using {'extended' if use_extended else 'base'} schema for processing")

    # Use the standardized entry point utility
    run_from_command_line(
        lambda _: run(
            resolved_portfolio
        ),  # Wrapper function to match expected signature
        extended_config,  # Pass extended schema config
        "portfolio update",
    )
