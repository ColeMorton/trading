"""
Strategy Execution Module

This module handles the execution of trading strategies, including portfolio processing,
filtering, and best portfolio selection for both single and multiple tickers.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import polars as pl

from app.strategies.ma_cross.config_types import Config
from app.strategies.ma_cross.tools.filter_portfolios import filter_portfolios
from app.strategies.ma_cross.tools.signal_processing import process_ticker_portfolios
from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)
from app.tools.portfolio.selection import get_best_portfolio
from app.tools.stats_converter import convert_stats
from app.tools.strategy.export_portfolios import PortfolioExportError, export_portfolios
from app.tools.strategy.signal_utils import is_exit_signal_current, is_signal_current

if TYPE_CHECKING:
    from app.tools.progress_tracking import ProgressTracker


def execute_single_strategy(
    ticker: str, config: Config, log: callable
) -> Optional[Dict]:
    """Execute a single strategy with specified parameters.

    This function tests a specific MA strategy (SMA or EMA) with exact window
    parameters, using the same workflow as execute_strategy but without
    parameter searching or filtering.

    Args:
        ticker: The ticker symbol
        config: Configuration containing:
            - STRATEGY_TYPE: str (Strategy type, e.g., "SMA" or "EMA")
            - SHORT_WINDOW: int (Fast MA period)
            - LONG_WINDOW: int (Slow MA period)
            - Other standard config parameters
        log: Logging function

    Returns:
        Optional[Dict]: Strategy performance metrics if successful, None otherwise
    """
    try:
        # Get price data
        data_result = get_data(ticker, config, log)
        if isinstance(data_result, tuple):
            data, synthetic_ticker = data_result
            config["TICKER"] = synthetic_ticker  # Update config with synthetic ticker
        else:
            data = data_result

        if data is None:
            log(f"Failed to get price data for {ticker}", "error")
            return None

        # Get strategy type from config or default to SMA
        strategy_type = config.get("STRATEGY_TYPE", "SMA")

        # Calculate MA and signals
        data = calculate_ma_and_signals(
            data,
            config["SHORT_WINDOW"],
            config["LONG_WINDOW"],
            config,
            log,
            strategy_type,
        )
        if data is None:
            log(f"Failed to calculate signals for {ticker}", "error")
            return None

        # Check if there's a current entry signal
        current_signal = is_signal_current(data, config)
        log(f"Current entry signal for {ticker}: {current_signal}", "info")

        # Check if there's a current exit signal
        exit_signal = is_exit_signal_current(data, config)
        log(f"Current exit signal for {ticker}: {exit_signal}", "info")

        # Run backtest using app/tools/backtest_strategy.py
        portfolio = backtest_strategy(data, config, log)
        if portfolio is None:
            return None

        # Get raw stats from vectorbt
        stats = portfolio.stats()

        # Check for invalid metrics before converting stats
        from app.tools.portfolio.filters import check_invalid_metrics

        valid_stats = check_invalid_metrics(stats, log)
        if valid_stats is None:
            log(
                f"Portfolio for {ticker} with {strategy_type} strategy (short window: {config['SHORT_WINDOW']}, long window: {config['LONG_WINDOW']}) has invalid metrics - skipping",
                "info",
            )
            return None

        # Convert stats using app/tools/stats_converter.py
        # Pass both the current entry and exit signals to convert_stats
        converted_stats = convert_stats(
            valid_stats, log, config, current_signal, exit_signal
        )

        # Add strategy identification fields
        converted_stats.update(
            {
                "TICKER": ticker,  # Use uppercase TICKER
                "Strategy Type": strategy_type,
                "SMA_FAST": config["SHORT_WINDOW"] if strategy_type == "SMA" else None,
                "SMA_SLOW": config["LONG_WINDOW"] if strategy_type == "SMA" else None,
                "EMA_FAST": config["SHORT_WINDOW"] if strategy_type == "EMA" else None,
                "EMA_SLOW": config["LONG_WINDOW"] if strategy_type == "EMA" else None,
                # Add Allocation [%] and Stop Loss [%] fields if they exist in config
                "Allocation [%]": config.get("ALLOCATION", None),
                "Stop Loss [%]": config.get("STOP_LOSS", None),
            }
        )

        return converted_stats

    except Exception as e:
        log(f"Failed to execute strategy: {str(e)}", "error")
        return None


def process_single_ticker(
    ticker: str,
    config: Config,
    log: callable,
    progress_tracker: Optional["ProgressTracker"] = None,
) -> Optional[Dict[str, Any]]:
    """Process a single ticker through the portfolio analysis pipeline.

    Args:
        ticker (str): The ticker symbol to process
        config (Config): Configuration for the analysis
        log (callable): Logging function
        progress_tracker: Optional progress tracking object

    Returns:
        Optional[Dict[str, Any]]: Best portfolio if found, None otherwise
    """
    # Create a config copy with single ticker
    ticker_config = config.copy()
    # Use the ticker from config if it exists (for synthetic tickers), otherwise use the parameter
    if "TICKER" not in ticker_config:
        # Ensure synthetic tickers use underscore format
        formatted_ticker = (
            ticker.replace("/", "_") if isinstance(ticker, str) else ticker
        )
        ticker_config["TICKER"] = formatted_ticker
    ticker_config["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix

    # Process portfolios for ticker
    # Get the actual ticker from config (which may be synthetic)
    actual_ticker = ticker_config.get("TICKER", ticker)
    if progress_tracker:
        progress_tracker.update(message=f"Analyzing portfolios for {actual_ticker}")

    portfolios_df = process_ticker_portfolios(actual_ticker, ticker_config, log)
    if portfolios_df is None:
        return None

    # Apply consolidated filtering using PortfolioFilterService
    if progress_tracker:
        progress_tracker.update(message=f"Filtering portfolios for {ticker}")

    from app.tools.portfolio.filtering_service import PortfolioFilterService

    filter_service = PortfolioFilterService()
    portfolios_df = filter_service.filter_portfolios_dataframe(
        portfolios_df, ticker_config, log
    )

    # Check if any portfolios remain after filtering
    if portfolios_df is None or len(portfolios_df) == 0:
        log("No portfolios remain after filtering", "warning")
        return None

    try:
        # Convert to dictionaries and normalize schema
        if progress_tracker:
            progress_tracker.update(message=f"Exporting portfolios for {ticker}")

        portfolio_dicts = portfolios_df.to_dicts()

        # Detect schema version
        schema_version = detect_schema_version(portfolio_dicts)
        log(f"Detected schema version for export: {schema_version.name}", "info")

        # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
        normalized_portfolios = normalize_portfolio_data(
            portfolio_dicts, schema_version, log
        )

        # Ensure allocation values sum to 100% if they exist
        if schema_version == SchemaVersion.EXTENDED:
            normalized_portfolios = ensure_allocation_sum_100_percent(
                normalized_portfolios, log
            )

        export_portfolios(
            portfolios=normalized_portfolios,
            config=ticker_config,
            export_type="portfolios",
            log=log,
        )
    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios for {actual_ticker}: {str(e)}", "error")
        return None

    # Filter portfolios for individual ticker
    filtered_portfolios = filter_portfolios(portfolios_df, ticker_config, log)
    if filtered_portfolios is None:
        return None

    log(f"Filtered results for {actual_ticker}")
    print(filtered_portfolios)

    # Export filtered portfolios
    try:
        # Convert to dictionaries and normalize schema
        filtered_dicts = filtered_portfolios.to_dicts()

        # Detect schema version
        schema_version = detect_schema_version(filtered_dicts)
        log(
            f"Detected schema version for filtered export: {schema_version.name}",
            "info",
        )

        # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
        normalized_filtered = normalize_portfolio_data(
            filtered_dicts, schema_version, log
        )

        # Ensure allocation values sum to 100% if they exist
        if schema_version == SchemaVersion.EXTENDED:
            normalized_filtered = ensure_allocation_sum_100_percent(
                normalized_filtered, log
            )

        export_portfolios(
            portfolios=normalized_filtered,
            config=ticker_config,
            export_type="portfolios_filtered",
            log=log,
        )
    except (ValueError, PortfolioExportError) as e:
        log(
            f"Failed to export filtered portfolios for {actual_ticker}: {str(e)}",
            "error",
        )

    # Get best portfolio
    best_portfolio = get_best_portfolio(filtered_portfolios, ticker_config, log)
    if best_portfolio is not None:
        log(f"Best portfolio for {actual_ticker}:")
        return best_portfolio

    return None


def execute_strategy(
    config: Config,
    strategy_type: str,
    log: callable,
    progress_tracker: Optional["ProgressTracker"] = None,
) -> List[Dict[str, Any]]:
    """Execute a trading strategy for all tickers.

    Args:
        config (Config): Configuration for the analysis
        strategy_type (str): Strategy type (e.g., 'EMA', 'SMA')
        log (callable): Logging function
        progress_tracker (Optional[ProgressTracker]): Progress tracking object

    Returns:
        List[Dict[str, Any]]: List of best portfolios found
    """
    best_portfolios = []

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

        # Pass the formatted ticker from config to ensure synthetic tickers are preserved
        formatted_ticker_to_process = ticker_config.get("TICKER", ticker)
        best_portfolio = process_single_ticker(
            formatted_ticker_to_process, ticker_config, log, progress_tracker
        )
        if best_portfolio is not None:
            best_portfolios.append(best_portfolio)

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

    return best_portfolios
