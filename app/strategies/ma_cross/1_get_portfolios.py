"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA and SMA cross strategies, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

from typing import Any, Dict, List

import polars as pl

from app.strategies.ma_cross.exceptions import (
    MACrossConfigurationError,
    MACrossError,
    MACrossExecutionError,
    MACrossPortfolioError,
)
from app.strategies.ma_cross.tools.strategy_execution import execute_strategy
from app.tools.entry_point import run_from_command_line
from app.tools.error_decorators import handle_errors
from app.tools.exceptions import (
    ConfigurationError,
    PortfolioLoadError,
    StrategyProcessingError,
)

# New imports for standardized logging and error handling
from app.tools.logging_context import logging_context
from app.tools.orchestration import PortfolioOrchestrator

# Import allocation utilities
from app.tools.portfolio.allocation import (
    calculate_position_sizes,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    normalize_allocations,
    validate_allocations,
)

# Import schema detection utilities
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    normalize_portfolio_data,
)

# Import stop loss utilities
from app.tools.portfolio.stop_loss import (
    calculate_stop_loss_levels,
    normalize_stop_loss,
    validate_stop_loss,
)
from app.tools.portfolio_results import (
    calculate_breadth_metrics,
    filter_open_trades,
    filter_signal_entries,
    sort_portfolios,
)
from app.tools.project_utils import get_project_root

# Use centralized error handling
from app.tools.strategy.error_handling import (
    ErrorSeverity,
    StrategyErrorCode,
    create_error_handler,
    handle_strategy_error,
)
from app.tools.strategy.types import StrategyConfig as Config
from app.tools.strategy_utils import filter_portfolios_by_signal, get_strategy_types

# Config management is now handled by ConfigService

CONFIG: Config = {
    "TICKER": ["AAPL"],
    # "TICKER_2": 'AVGO',
    "FAST_PERIOD_RANGE": [5, 89],
    "SLOW_PERIOD_RANGE": [8, 89],
    # "SCANNER_LIST": 'DAILY.csv',
    # "USE_SCANNER": True,
    "BASE_DIR": get_project_root(),  # Use standardized project root resolver
    "REFRESH": True,
    "STRATEGY_TYPES": ["SMA", "EMA"],
    # "STRATEGY_TYPES": ["SMA"],
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": True,
    "MINIMUMS": {},
    "SORT_BY": "Score",
    "SORT_ASC": False,
    "USE_GBM": False,
}

# Using the standardized synthetic_ticker module instead of local implementation


# Using standardized strategy utilities from app.tools.strategy_utils
def filter_portfolios(
    portfolios: List[Dict[str, Any]], config: Config, log
) -> List[Dict[str, Any]]:
    """Filter portfolios based on configuration.

    Args:
        portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        log: Logging function

    Returns:
        Filtered list of portfolio dictionaries
    """
    # First detect schema version and normalize portfolio data
    schema_version = detect_schema_version(portfolios)
    log(f"Detected schema version: {schema_version.name}", "info")

    # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
    normalized_portfolios = normalize_portfolio_data(portfolios, schema_version, log)

    # Process allocation and stop loss values if they exist
    if schema_version == SchemaVersion.EXTENDED:
        # Process allocation values
        # Validate allocation values
        validated_portfolios = validate_allocations(normalized_portfolios, log)

        # Normalize allocation field names
        normalized_portfolios = normalize_allocations(validated_portfolios, log)

        # Distribute missing allocations if some rows have values and others don't
        distributed_portfolios = distribute_missing_allocations(
            normalized_portfolios, log
        )

        # Ensure allocation values sum to 100%
        normalized_portfolios = ensure_allocation_sum_100_percent(
            distributed_portfolios, log
        )

        # Calculate position sizes if account value is provided in config
        if "ACCOUNT_VALUE" in config and config["ACCOUNT_VALUE"] > 0:
            account_value = float(config["ACCOUNT_VALUE"])
            normalized_portfolios = calculate_position_sizes(
                normalized_portfolios, account_value, log
            )
            log(
                f"Calculated position sizes based on account value: {account_value}",
                "info",
            )

        # Process stop loss values
        # Validate stop loss values
        validated_stop_loss = validate_stop_loss(normalized_portfolios, log)

        # Normalize stop loss field names
        normalized_portfolios = normalize_stop_loss(validated_stop_loss, log)

        # If we have entry prices, calculate stop loss levels
        if "ENTRY_PRICES" in config and config["ENTRY_PRICES"]:
            normalized_portfolios = calculate_stop_loss_levels(
                normalized_portfolios, config["ENTRY_PRICES"], log
            )
            log("Calculated stop loss levels based on entry prices", "info")

    # Filter by signal using the standardized filter_portfolios_by_signal function
    filtered = filter_portfolios_by_signal(normalized_portfolios, config, log)

    # Apply consolidated filtering using PortfolioFilterService
    from app.tools.portfolio.filtering_service import PortfolioFilterService

    filter_service = PortfolioFilterService()
    filtered = filter_service.filter_portfolios_list(filtered, config, log)

    # If we have results and want to display them, use the portfolio_results utilities
    if (
        filtered is not None
        and len(filtered) > 0
        and config.get("DISPLAY_RESULTS", True)
    ):
        # Sort portfolios
        sorted_portfolios = sort_portfolios(
            filtered,
            config.get("SORT_BY", "Total Return [%]"),
            config.get("SORT_ASC", False),
        )

        # Get open trades
        open_trades = filter_open_trades(sorted_portfolios, log)

        # Get signal entries
        signal_entries = filter_signal_entries(sorted_portfolios, open_trades, log)

        # Calculate breadth metrics
        calculate_breadth_metrics(sorted_portfolios, open_trades, signal_entries, log)

        return sorted_portfolios

    return filtered


# Using the standardized synthetic_ticker module instead of local implementation


def execute_all_strategies(config: Config, log) -> List[Dict[str, Any]]:
    """Execute all strategies and collect results.

    Args:
        config: Configuration dictionary
        log: Logging function

    Returns:
        List of portfolio dictionaries

    Raises:
        StrategyProcessingError: If there's an error processing a strategy
    """
    strategy_types = get_strategy_types(config, log)
    log(f"Running strategies in sequence: {' -> '.join(strategy_types)}")

    all_portfolios = []

    for strategy_type in strategy_types:
        log(f"Running {strategy_type} strategy analysis...")
        strategy_config = {**config}
        strategy_config["STRATEGY_TYPE"] = strategy_type

        # Pass progress update function directly to strategy execution
        portfolios = execute_strategy(
            strategy_config, strategy_type, log, progress_update_fn
        )

        # Check if portfolios is not None and not empty
        if portfolios is not None:
            if isinstance(portfolios, pl.DataFrame):
                portfolio_count = len(portfolios)
                if portfolio_count > 0:
                    # Convert to dictionaries and process allocation and stop loss
                    # values
                    portfolio_dicts = portfolios.to_dicts()
                    all_portfolios.extend(portfolio_dicts)
            else:
                portfolio_count = len(portfolios)
                if portfolio_count > 0:
                    all_portfolios.extend(portfolios)

            log(f"{strategy_type} portfolios: {portfolio_count}", "info")
        else:
            log(f"{strategy_type} portfolios: 0", "info")

    if not all_portfolios:
        log(
            "No portfolios returned from any strategy. Filtering criteria might be too strict.",
            "warning",
        )

    return all_portfolios


@handle_errors(
    "MA Cross portfolio analysis",
    {
        ValueError: MACrossExecutionError,
        KeyError: MACrossConfigurationError,
        ConfigurationError: MACrossConfigurationError,
        PortfolioLoadError: MACrossPortfolioError,
        StrategyProcessingError: MACrossExecutionError,
        Exception: MACrossError,
    },
)
def run(config: Config = CONFIG, external_log=None, progress_update_fn=None) -> bool:
    """Run portfolio analysis for single or multiple tickers.

    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis
    3. Filters portfolios based on criteria
    4. Displays and saves results

    Args:
        config (Config): Configuration dictionary containing analysis parameters
        external_log: Optional external logger (e.g., from CLI)

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        MACrossConfigurationError: If the configuration is invalid
        MACrossExecutionError: If there's an error processing a strategy
        MACrossPortfolioError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        MACrossError: For other unexpected errors
    """
    # Use external logger if provided, otherwise use default logging context
    if external_log:
        # Create callable wrapper for console logger
        def log_wrapper(message, level="info"):
            if hasattr(external_log, level):
                getattr(external_log, level)(message)
            elif hasattr(external_log, "info"):
                external_log.info(message)  # fallback to info level
            else:
                # Last resort - try to call it directly
                external_log(message, level)

        # Store reference to original logger for enhanced progress display detection
        log_wrapper.__self__ = external_log

        return _run_with_log(config, log_wrapper, progress_update_fn)
    else:
        with logging_context(
            module_name="ma_cross", log_file="1_get_portfolios.log"
        ) as log:
            return _run_with_log(config, log, progress_update_fn)


def _run_with_log(config: Config, log, progress_update_fn=None) -> bool:
    """Internal run function that accepts a logger."""
    # SAFEGUARD: Trade history export is not available for MA Cross strategy
    # to prevent generating thousands of JSON files due to parameter sweep combinations.
    # Trade history export is only available through app/concurrency/review.py
    config_copy = config.copy()
    if "EXPORT_TRADE_HISTORY" in config_copy:
        del config_copy["EXPORT_TRADE_HISTORY"]
    if config.get("EXPORT_TRADE_HISTORY", False):
        log(
            "WARNING: Trade history export is not supported for MA Cross strategy. Use app/concurrency/review.py for trade history export.",
            "warning",
        )

    # Use the new PortfolioOrchestrator for cleaner workflow management
    orchestrator = PortfolioOrchestrator(log)
    return orchestrator.run(config_copy, progress_update_fn)


@handle_errors(
    "MA Cross strategies analysis",
    {
        ValueError: MACrossExecutionError,
        KeyError: MACrossConfigurationError,
        ConfigurationError: MACrossConfigurationError,
        PortfolioLoadError: MACrossPortfolioError,
        StrategyProcessingError: MACrossExecutionError,
        Exception: MACrossError,
    },
)
def run_strategies(config: Dict[str, Any] = None) -> bool:
    """Run analysis with strategies specified in STRATEGY_TYPES in sequence.

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        MACrossConfigurationError: If the configuration is invalid
        MACrossExecutionError: If there's an error processing a strategy
        MACrossPortfolioError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        MACrossError: For other unexpected errors
    """
    with logging_context(
        module_name="ma_cross", log_file="1_get_portfolios.log"
    ) as log:
        # Prepare config
        if config is not None and config:
            config_copy = config.copy()
        else:
            config_copy = CONFIG.copy()
        config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix

        # SAFEGUARD: Trade history export is not available for MA Cross strategy
        # to prevent generating thousands of JSON files due to parameter sweep combinations.
        # Trade history export is only available through app/concurrency/review.py
        if "EXPORT_TRADE_HISTORY" in config_copy:
            del config_copy["EXPORT_TRADE_HISTORY"]
        if config_copy.get("EXPORT_TRADE_HISTORY", False):
            log(
                "WARNING: Trade history export is not supported for MA Cross strategy. Use app/concurrency/review.py for trade history export.",
                "warning",
            )

        # Use the new PortfolioOrchestrator for cleaner workflow management
        orchestrator = PortfolioOrchestrator(log)
        return orchestrator.run(config_copy, progress_update_fn=None)


if __name__ == "__main__":
    import warnings

    # Show deprecation warning for direct script usage
    warnings.warn(
        "\n"
        "⚠️  DEPRECATION WARNING: Direct execution of this script is deprecated.\n"
        "   Use the unified CLI interface instead:\n"
        "   \n"
        "   Replace: python app/strategies/ma_cross/1_get_portfolios.py\n"
        "   With:    python -m app.cli strategy run --profile ma_cross_crypto\n"
        "   \n"
        "   For more information: python -m app.cli strategy --help\n"
        "   \n"
        "   This script will be removed in a future version.\n",
        DeprecationWarning,
        stacklevel=2,
    )

    run_from_command_line(
        run_strategies,
        {},  # Empty config as run_strategies uses the default CONFIG
        "MA Cross portfolio analysis",
    )
