"""
Portfolio Analysis Module for ATR Trailing Stop Strategy

This module handles portfolio analysis for the ATR trailing stop strategy, supporting both
single ticker and multiple ticker analysis. The strategy identifies optimal ATR parameters
for trailing stop loss implementation where:

Long:
- Entry when price breaks above ATR trailing stop
- Exit when price drops below ATR trailing stop

The ATR trailing stop is calculated as:
- Stop Level = Highest Price Since Entry - (ATR × Multiplier)

It includes functionality for parameter sensitivity analysis and portfolio filtering.
"""

from typing import Any, Dict, List

from app.strategies.atr.config_types import ATRConfig
from app.strategies.atr.exceptions import (
    ATRConfigurationError,
    ATRError,
    ATRExecutionError,
    ATRPortfolioError,
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
    "ATR portfolio analysis",
    {
        ValueError: ATRExecutionError,
        KeyError: ATRConfigurationError,
        ConfigurationError: ATRConfigurationError,
        PortfolioLoadError: ATRPortfolioError,
        StrategyProcessingError: ATRExecutionError,
        Exception: ATRError,
    },
)
def run(config: ATRConfig = None, external_log=None, progress_update_fn=None) -> bool:
    """Run portfolio analysis for single or multiple tickers using the ATR trailing stop strategy.

    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis on ATR parameters
    3. Filters portfolios based on criteria
    4. Selects best portfolio from filtered portfolios
    5. Displays and saves results

    The workflow ensures that portfolios that excel in multiple metrics
    (as identified in the filtering step) are properly considered for
    best portfolio selection.

    Args:
        config (ATRConfig): Configuration dictionary containing analysis parameters
        external_log: Optional external logger (e.g., from CLI)
        progress_update_fn: Optional progress update function for holistic tracking

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        ATRConfigurationError: If the configuration is invalid
        ATRExecutionError: If there's an error processing a strategy
        ATRPortfolioError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        ATRError: For other unexpected errors
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
        with logging_context(module_name="atr", log_file="1_get_portfolios.log") as log:
            return _run_with_log(config, log, progress_update_fn)


def _run_with_log(config: ATRConfig, log, progress_update_fn=None) -> bool:
    """Internal run function with logger provided."""
    # SAFEGUARD: Trade history export is not available for ATR strategy
    # to prevent generating thousands of JSON files due to parameter sweep combinations.
    # Trade history export is only available through app/concurrency/review.py
    config_copy = config.copy() if config else {}
    if "EXPORT_TRADE_HISTORY" in config_copy:
        del config_copy["EXPORT_TRADE_HISTORY"]
    if config_copy.get("EXPORT_TRADE_HISTORY", False):
        log(
            "WARNING: Trade history export is not supported for ATR strategy. Use app/concurrency/review.py for trade history export.",
            "warning",
        )

    # Set ATR-specific configuration flags
    config_copy["USE_MA"] = False  # ATR is not a moving average strategy
    config_copy["STRATEGY_TYPE"] = "ATR"  # Ensure strategy type is set

    # Use the PortfolioOrchestrator for clean workflow management
    orchestrator = PortfolioOrchestrator(log)
    return orchestrator.run(config_copy, progress_update_fn)


@handle_errors(
    "ATR strategies analysis",
    {
        ValueError: ATRExecutionError,
        KeyError: ATRConfigurationError,
        ConfigurationError: ATRConfigurationError,
        PortfolioLoadError: ATRPortfolioError,
        StrategyProcessingError: ATRExecutionError,
        Exception: ATRError,
    },
)
def run_strategies(config: Dict[str, Any] = None) -> bool:
    """Run analysis with ATR strategy parameters.

    This function is similar to the run function in other strategy modules,
    providing a consistent interface across strategy modules.

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        ATRConfigurationError: If the configuration is invalid
        ATRExecutionError: If there's an error processing a strategy
        ATRPortfolioError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        ATRError: For other unexpected errors
    """
    with logging_context(module_name="atr", log_file="1_get_portfolios.log") as log:
        # Prepare config
        config_copy = config.copy() if config else {}
        config_copy["USE_MA"] = False  # ATR is not a moving average strategy
        config_copy["STRATEGY_TYPE"] = "ATR"  # Ensure strategy type is set

        # SAFEGUARD: Trade history export is not available for ATR strategy
        # to prevent generating thousands of JSON files due to parameter sweep combinations.
        # Trade history export is only available through app/concurrency/review.py
        if "EXPORT_TRADE_HISTORY" in config_copy:
            del config_copy["EXPORT_TRADE_HISTORY"]
        if config_copy.get("EXPORT_TRADE_HISTORY", False):
            log(
                "WARNING: Trade history export is not supported for ATR strategy. Use app/concurrency/review.py for trade history export.",
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
        "   Replace: python app/strategies/atr/1_get_portfolios.py\n"
        "   With:    python -m app.cli strategy run --strategy ATR --ticker BTC-USD\n"
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
        "ATR portfolio analysis",
    )
