"""
Portfolio Analysis Module for SMA_ATR Strategy

This module handles portfolio analysis for the SMA_ATR strategy, which combines
SMA crossovers for entry signals and ATR trailing stops for exit signals.
"""

from typing import Any

from app.tools.entry_point import run_from_command_line
from app.tools.error_decorators import handle_errors
from app.tools.logging_context import logging_context
from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from app.tools.portfolio.allocation import (
    calculate_position_sizes,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    normalize_allocations,
    validate_allocations,
)
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    normalize_portfolio_data,
)
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
from app.tools.strategy.error_handling import handle_strategy_error
from app.tools.strategy.types import StrategyConfig as Config
from app.tools.strategy_utils import filter_portfolios_by_signal

from .exceptions import (
    SMAAtrConfigurationError,
    SMAAtrError,
    SMAAtrExecutionError,
    SMAAtrPortfolioError,
)


# Default configuration for SMA_ATR strategy (optimized for 10x performance)
CONFIG: Config = {
    "TICKER": ["AAPL"],
    "FAST_PERIOD_RANGE": [8, 50],  # SMA fast period range
    "SLOW_PERIOD_RANGE": [11, 56],  # SMA slow period range
    "ATR_LENGTH_RANGE": [3, 5, 7, 9, 11, 13],  # ATR discrete length values
    "ATR_MULTIPLIER_RANGE": [1.0, 4.0],  # ATR multiplier range
    "ATR_MULTIPLIER_STEP": 1.5,
    "STEP": 3,  # CRITICAL: SMA step size for 10x performance optimization
    "BASE_DIR": get_project_root(),
    "REFRESH": True,
    "STRATEGY_TYPES": ["SMA_ATR"],
    "STRATEGY_TYPE": "SMA_ATR",
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


def filter_portfolios(
    portfolios: list[dict[str, Any]],
    config: Config,
    log,
) -> list[dict[str, Any]]:
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
        validated_portfolios = validate_allocations(normalized_portfolios, log)
        normalized_portfolios = normalize_allocations(validated_portfolios, log)
        distributed_portfolios = distribute_missing_allocations(
            normalized_portfolios,
            log,
        )
        normalized_portfolios = ensure_allocation_sum_100_percent(
            distributed_portfolios,
            log,
        )

        # Calculate position sizes if account value is provided
        if "ACCOUNT_VALUE" in config and config["ACCOUNT_VALUE"] > 0:
            account_value = float(config["ACCOUNT_VALUE"])
            normalized_portfolios = calculate_position_sizes(
                normalized_portfolios,
                account_value,
                log,
            )
            log(
                f"Calculated position sizes based on account value: {account_value}",
                "info",
            )

        # Process stop loss values
        validated_stop_loss = validate_stop_loss(normalized_portfolios, log)
        normalized_portfolios = normalize_stop_loss(validated_stop_loss, log)

        # If we have entry prices, calculate stop loss levels
        if config.get("ENTRY_PRICES"):
            normalized_portfolios = calculate_stop_loss_levels(
                normalized_portfolios,
                config["ENTRY_PRICES"],
                log,
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


@handle_errors(SMAAtrError)
def run(
    config: dict[str, Any] | None = None,
    error_handler: Any | None = None,
    external_log: Any | None = None,
    progress_update_fn: Any | None = None,
) -> bool:
    """Run the SMA_ATR strategy execution workflow.

    Args:
        config: Optional configuration dictionary to override defaults
        error_handler: Optional error handler
        external_log: Optional external logger for CLI integration
        progress_update_fn: Optional progress update function for CLI integration

    Returns:
        bool: True if execution succeeded, False otherwise
    """
    # Use config passed in or default CONFIG
    if config is None:
        config = CONFIG
    else:
        # Merge with defaults
        merged_config = CONFIG.copy()
        merged_config.update(config)
        config = merged_config

    # Use logging_context for thread-safe logging
    with logging_context("sma_atr", "sma_atr_analysis.log") as log:
        # Use external log if provided (for CLI integration)
        if external_log is not None:
            # Map log levels to external_log methods if they exist
            def log_wrapper(msg, level="info"):
                if hasattr(external_log, level):
                    getattr(external_log, level)(msg)
                # Fallback to info level if specific level doesn't exist
                elif hasattr(external_log, "info"):
                    external_log.info(f"[{level.upper()}] {msg}")
                else:
                    log(msg, level)

            log = log_wrapper

        try:
            # Create PortfolioOrchestrator to manage the portfolio processing workflow
            orchestrator = PortfolioOrchestrator(log)

            # Run the orchestration workflow which handles:
            # 1. Multi-ticker processing
            # 2. Strategy execution for each ticker
            # 3. Portfolio aggregation and filtering
            # 4. Best portfolio selection
            # 5. CSV export to various directories
            result = orchestrator.run(config, progress_update_fn)

            if result:
                log("SMA_ATR strategy execution completed successfully", "info")
            else:
                log("SMA_ATR strategy execution completed with warnings", "warning")

            return result

        except SMAAtrConfigurationError as e:
            handle_strategy_error(e, "SMA_ATR Configuration Error", log)
            return False

        except SMAAtrExecutionError as e:
            handle_strategy_error(e, "SMA_ATR Execution Error", log)
            return False

        except SMAAtrPortfolioError as e:
            handle_strategy_error(e, "SMA_ATR Portfolio Error", log)
            return False

        except Exception as e:
            handle_strategy_error(e, "Unexpected SMA_ATR Error", log)
            return False


if __name__ == "__main__":
    # Support command line execution with config override
    # Usage: python 1_get_portfolios.py --ticker AAPL,MSFT --fast_period_range 10,50
    run_from_command_line(run, CONFIG)
