"""Strategy execution module for parameter sensitivity analysis.

This version returns ALL analyzed portfolios, not just the best ones.
"""

from typing import Any, Optional

from app.strategies.ma_cross.config_types import Config
from app.tools.get_config import get_config
from app.tools.portfolio.filtering_service import PortfolioFilterService
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)


def process_ticker_portfolios_all(
    ticker: str, config: Config, log: callable
) -> list[dict[str, Any]]:
    """Process portfolios for a single ticker and return ALL analyzed portfolios.

    Args:
        ticker (str): The ticker symbol to process
        config (Config): Configuration for portfolio processing
        log (callable): Logging function

    Returns:
        List[Dict[str, Any]]: List of all analyzed portfolios (not just the best)
    """
    from app.strategies.ma_cross.tools.parameter_sensitivity import (
        analyze_parameter_sensitivity,
    )
    from app.tools.get_data import get_data

    # Get the configuration
    ticker_config = get_config(ticker, config, log)
    if ticker_config is None:
        return []

    # For parameter sensitivity, we need to analyze ALL combinations, not just current signals
    # Get price data
    data = get_data(ticker, ticker_config, log)
    if data is None:
        log(f"Failed to get data for {ticker}", "error")
        return []

    # Get window parameters using explicit ranges
    fast_range = ticker_config.get("FAST_PERIOD_RANGE")
    slow_range = ticker_config.get("SLOW_PERIOD_RANGE")

    # Backward compatibility: fallback to WINDOWS if ranges not specified
    if fast_range is None or slow_range is None:
        if "WINDOWS" in ticker_config:
            import warnings

            warnings.warn(
                "WINDOWS parameter is deprecated. Use FAST_PERIOD_RANGE and SLOW_PERIOD_RANGE instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            max_window = ticker_config["WINDOWS"]
            short_windows = list(range(2, max_window))
            long_windows = list(range(3, max_window + 1))
        else:
            # Default ranges
            short_windows = list(range(5, 90))  # [5, 6, ..., 89]
            long_windows = list(range(8, 90))  # [8, 9, ..., 89]
    else:
        # Use explicit ranges
        short_windows = list(range(fast_range[0], fast_range[1] + 1))
        long_windows = list(range(slow_range[0], slow_range[1] + 1))

    # Run parameter sensitivity analysis
    portfolios_df = analyze_parameter_sensitivity(
        data=data,
        short_windows=short_windows,
        long_windows=long_windows,
        config=ticker_config,
        log=log,
    )

    if portfolios_df is None or len(portfolios_df) == 0:
        log(f"No portfolios generated for {ticker}", "warning")
        return []

    # Apply consolidated filtering using PortfolioFilterService
    filter_service = PortfolioFilterService()
    filtered_df = filter_service.filter_portfolios_dataframe(
        portfolios_df, ticker_config, log
    )

    # Check if any portfolios remain after filtering
    if filtered_df is None or len(filtered_df) == 0:
        log(f"No portfolios remain after filtering for {ticker}", "warning")
        return []

    # Convert to list of dictionaries
    portfolio_dicts = filtered_df.to_dicts()

    # Detect schema version
    schema_version = detect_schema_version(portfolio_dicts)
    log(f"Detected schema version: {schema_version.name}", "info")

    # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
    normalized_portfolios = normalize_portfolio_data(
        portfolio_dicts, schema_version, log
    )

    # Ensure allocation values sum to 100% if they exist
    if schema_version == SchemaVersion.EXTENDED:
        normalized_portfolios = ensure_allocation_sum_100_percent(
            normalized_portfolios, log
        )

    log(f"Returning {len(normalized_portfolios)} portfolios for {ticker}")
    return normalized_portfolios


def execute_strategy_all(
    config: Config,
    strategy_type: str,
    log: callable,
    progress_tracker: Optional["ProgressTracker"] = None,
) -> list[dict[str, Any]]:
    """Execute a trading strategy for all tickers and return ALL analyzed portfolios.

    Args:
        config (Config): Configuration for the analysis
        strategy_type (str): Strategy type (e.g., 'EMA', 'SMA')
        log (callable): Logging function
        progress_tracker (Optional[ProgressTracker]): Progress tracking object

    Returns:
        List[Dict[str, Any]]: List of all analyzed portfolios
    """
    all_portfolios = []

    if "TICKER" not in config:
        log(
            f"ERROR: TICKER key not found in config. Available keys: {list(config.keys())}",
            "error",
        )
        return []

    tickers = (
        [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
    )

    # Update progress if tracker provided
    if progress_tracker:
        progress_tracker.set_total_steps(len(tickers))
        progress_tracker.update(
            phase="analysis", message=f"Starting {strategy_type} strategy analysis"
        )

    for i, ticker in enumerate(tickers):
        log(f"Processing {strategy_type} strategy for ticker: {ticker}")
        ticker_config = config.copy()

        # Handle synthetic tickers
        if (
            config.get("USE_SYNTHETIC", False)
            and isinstance(ticker, str)
            and "_" in ticker
        ):
            # Extract original tickers from synthetic ticker name
            ticker_parts = ticker.split("_")
            if len(ticker_parts) >= 2:
                # Store original ticker parts for later use
                ticker_config["TICKER_1"] = ticker_parts[0]
                if "TICKER_2" not in ticker_config:
                    ticker_config["TICKER_2"] = ticker_parts[1]
                log(
                    f"Extracted ticker components: {ticker_config['TICKER_1']} and {ticker_config['TICKER_2']}"
                )

        # Ensure synthetic tickers use underscore format
        formatted_ticker = (
            ticker.replace("/", "_") if isinstance(ticker, str) else ticker
        )
        ticker_config["TICKER"] = formatted_ticker

        # Set the strategy type in the config
        ticker_config["STRATEGY_TYPE"] = strategy_type

        # Update progress before processing ticker
        if progress_tracker:
            progress_tracker.update(
                step=i, message=f"Processing {ticker} ({i+1}/{len(tickers)})"
            )

        # Get ALL portfolios for this ticker
        ticker_portfolios = process_ticker_portfolios_all(
            formatted_ticker, ticker_config, log
        )

        if ticker_portfolios:
            all_portfolios.extend(ticker_portfolios)
            log(f"Added {len(ticker_portfolios)} portfolios from {ticker}")

        # Update progress after processing ticker
        if progress_tracker:
            progress_tracker.increment(
                message=f"Completed {ticker} ({i+1}/{len(tickers)})"
            )

    # Mark analysis complete
    if progress_tracker:
        progress_tracker.complete(
            f"Completed {strategy_type} analysis for {len(tickers)} tickers"
        )

    log(f"Total portfolios from all tickers: {len(all_portfolios)}")
    return all_portfolios
