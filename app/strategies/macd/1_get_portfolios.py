"""
Portfolio Analysis Module for MACD Cross Strategy

This module handles portfolio analysis for the MACD cross strategy, supporting both
single ticker and multiple ticker analysis. The strategy identifies MACD crossovers where:

Long:
- Entry when MACD line crosses above Signal line
- Exit when MACD line crosses below Signal line

Short:
- Entry when MACD line crosses below Signal line
- Exit when MACD line crosses above Signal line

It includes functionality for parameter sensitivity analysis and portfolio filtering.
"""

from typing import Any

from app.strategies.macd.config_types import PortfolioConfig
from app.strategies.macd.exceptions import (
    MACDConfigurationError,
    MACDError,
    MACDExecutionError,
    MACDPortfolioError,
)
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


@handle_errors(
    "MACD portfolio analysis",
    {
        ValueError: MACDExecutionError,
        KeyError: MACDConfigurationError,
        ConfigurationError: MACDConfigurationError,
        PortfolioLoadError: MACDPortfolioError,
        StrategyProcessingError: MACDExecutionError,
        Exception: MACDError,
    },
)
def run(
    config: PortfolioConfig = None, external_log=None, progress_update_fn=None
) -> bool:
    """Run portfolio analysis for single or multiple tickers using the MACD cross strategy.

    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis on MACD parameters
    3. Filters portfolios based on criteria
    4. Selects best portfolio from filtered portfolios
    5. Displays and saves results

    The workflow ensures that portfolios that excel in multiple metrics
    (as identified in the filtering step) are properly considered for
    best portfolio selection.

    Args:
        config (PortfolioConfig): Configuration dictionary containing analysis parameters
        external_log: Optional external logger (e.g., from CLI)
        progress_update_fn: Optional progress update function for holistic tracking

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        MACDConfigurationError: If the configuration is invalid
        MACDExecutionError: If there's an error processing a strategy
        MACDPortfolioError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        MACDError: For other unexpected errors
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
    with logging_context(module_name="macd", log_file="1_get_portfolios.log") as log:
        return _run_with_log(config, log, progress_update_fn)


def _run_with_log(config: PortfolioConfig, log, progress_update_fn=None) -> bool:
    """Internal run function with logger provided."""
    # CRITICAL SAFEGUARD: Detect inappropriate batch analysis during portfolio update
    config_copy = config.copy() if config else {}
    if config_copy.get("_PORTFOLIO_UPDATE_MODE", False):
        log(
            "ERROR: MACD batch analysis triggered during portfolio update mode - this should not happen!",
            "error",
        )
        log(
            "This indicates the dual export architecture problem is still active",
            "error",
        )
        # Return success to avoid breaking the process, but don't execute batch analysis
        return True

    # SAFEGUARD: Trade history export is not available for MACD strategy
    # to prevent generating thousands of JSON files due to parameter sweep combinations.
    # Trade history export is only available through app/concurrency/review.py
    if "EXPORT_TRADE_HISTORY" in config_copy:
        del config_copy["EXPORT_TRADE_HISTORY"]
    if config_copy.get("EXPORT_TRADE_HISTORY", False):
        log(
            "WARNING: Trade history export is not supported for MACD strategy. Use app/concurrency/review.py for trade history export.",
            "warning",
        )

    # Use the PortfolioOrchestrator for clean workflow management
    orchestrator = PortfolioOrchestrator(log)
    return orchestrator.run(config_copy, progress_update_fn)


@handle_errors(
    "MACD strategies analysis",
    {
        ValueError: MACDExecutionError,
        KeyError: MACDConfigurationError,
        ConfigurationError: MACDConfigurationError,
        PortfolioLoadError: MACDPortfolioError,
        StrategyProcessingError: MACDExecutionError,
        Exception: MACDError,
    },
)
def run_strategies(config: dict[str, Any] | None = None) -> bool:
    """Run analysis with strategies specified in STRATEGY_TYPES in sequence.

    This function is similar to the run function in ma_cross/1_get_portfolios.py,
    providing a consistent interface across strategy modules.

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        MACDConfigurationError: If the configuration is invalid
        MACDExecutionError: If there's an error processing a strategy
        MACDPortfolioError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        MACDError: For other unexpected errors
    """
    with logging_context(module_name="macd", log_file="1_get_portfolios.log") as log:
        # CRITICAL SAFEGUARD: Detect inappropriate batch analysis during portfolio update
        config_copy = config.copy() if config else {}
        if config_copy.get("_PORTFOLIO_UPDATE_MODE", False):
            log(
                "ERROR: MACD batch analysis triggered during portfolio update mode - this should not happen!",
                "error",
            )
            log(
                "This indicates the dual export architecture problem is still active",
                "error",
            )
            # Return success to avoid breaking the process, but don't execute batch analysis
            return True

        # Prepare config
        config_copy["USE_MA"] = (
            False  # Ensure USE_MA is set correctly for MACD filename suffix
        )

        # SAFEGUARD: Trade history export is not available for MACD strategy
        # to prevent generating thousands of JSON files due to parameter sweep combinations.
        # Trade history export is only available through app/concurrency/review.py
        if "EXPORT_TRADE_HISTORY" in config_copy:
            del config_copy["EXPORT_TRADE_HISTORY"]
        if config_copy.get("EXPORT_TRADE_HISTORY", False):
            log(
                "WARNING: Trade history export is not supported for MACD strategy. Use app/concurrency/review.py for trade history export.",
                "warning",
            )

        # Use the PortfolioOrchestrator for clean workflow management
        orchestrator = PortfolioOrchestrator(log)
        return orchestrator.run(config_copy)


if __name__ == "__main__":
    import warnings

    # Show deprecation warning for direct script usage
    warnings.warn(
        "\n"
        "⚠️  DEPRECATION WARNING: Direct execution of this script is deprecated.\n"
        "   Use the unified CLI interface instead:\n"
        "   \n"
        "   Replace: python app/strategies/macd/1_get_portfolios.py\n"
        "   With:    python -m app.cli strategy run --strategy MACD --ticker BTC-USD\n"
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
        "MACD portfolio analysis",
    )
