"""
Strategy Execution Module

This module handles the execution of trading strategies, including portfolio processing,
filtering, and best portfolio selection for both single and multiple tickers.
"""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from app.strategies.ma_cross.config_types import Config
from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.performance_tracker import (
    get_strategy_performance_tracker,
    monitor_performance,
    timing_context,
)
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)
from app.tools.portfolio.selection import (
    get_best_portfolio,
    get_best_portfolios_per_strategy_type,
)
from app.tools.stats_converter import convert_stats
from app.tools.strategy.export_portfolios import PortfolioExportError, export_portfolios
from app.tools.strategy.filter_portfolios import filter_portfolios
from app.tools.strategy.signal_processing import process_ticker_portfolios
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
            - FAST_PERIOD: int (Fast MA period)
            - SLOW_PERIOD: int (Slow MA period)
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
            config["FAST_PERIOD"],
            config["SLOW_PERIOD"],
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
                f"Portfolio for {ticker} with {strategy_type} strategy (fast period: {config['FAST_PERIOD']}, slow period: {config['SLOW_PERIOD']}) has invalid metrics - skipping",
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
                "Fast Period": config["FAST_PERIOD"],  # Always use Fast Period
                "Slow Period": config["SLOW_PERIOD"],  # Always use Slow Period
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
    # Use the ticker from config if it exists (for synthetic tickers),
    # otherwise use the parameter
    if "TICKER" not in ticker_config:
        # Ensure synthetic tickers use underscore format
        formatted_ticker = (
            ticker.replace("/", "_") if isinstance(ticker, str) else ticker
        )
        ticker_config["TICKER"] = formatted_ticker
    # Set strategy-specific configuration for proper filename generation
    ticker_config["USE_MA"] = True  # Enable strategy suffix in filename
    # Ensure STRATEGY_TYPE is set for accurate strategy identification
    if "STRATEGY_TYPE" not in ticker_config:
        ticker_config["STRATEGY_TYPE"] = config.get("STRATEGY_TYPE", "SMA")

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

    from app.tools.strategy.filter_portfolios import filter_portfolios

    portfolios_df = filter_portfolios(portfolios_df, ticker_config, log)

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
            export_type="strategies",
            log=log,
        )
    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios for {actual_ticker}: {str(e)}", "error")
        return None

    # Filter portfolios for individual ticker
    # Apply filtering to get filtered portfolios
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
            export_type="strategies",
            log=log,
        )
    except (ValueError, PortfolioExportError) as e:
        log(
            f"Failed to export filtered portfolios for {actual_ticker}: {str(e)}",
            "error",
        )

    # Get best portfolios (one per strategy type if multiple exist)
    best_portfolios = get_best_portfolios_per_strategy_type(
        filtered_portfolios, ticker_config, log
    )

    if best_portfolios:
        log(f"Found {len(best_portfolios)} best portfolio(s) for {actual_ticker}")

        # For backward compatibility, return first portfolio if only one exists
        # This preserves existing behavior for single-strategy scenarios
        if len(best_portfolios) == 1:
            return best_portfolios[0]
        else:
            # For multi-strategy scenarios, return all best portfolios
            # The calling code will need to handle the list format
            return best_portfolios

    return None


def process_ticker_batch(
    ticker_batch: List[str], config: Config, strategy_type: str, log: callable
) -> List[Dict[str, Any]]:
    """Process a batch of tickers sequentially within a single thread.

    Args:
        ticker_batch: List of ticker symbols to process
        config: Configuration for the analysis
        strategy_type: Strategy type (e.g., 'EMA', 'SMA')
        log: Logging function

    Returns:
        List of best portfolios found for the batch
    """
    batch_portfolios = []

    for ticker in ticker_batch:
        try:
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

            # Process the ticker
            formatted_ticker_to_process = ticker_config.get("TICKER", ticker)
            best_portfolio = process_single_ticker(
                formatted_ticker_to_process,
                ticker_config,
                log,
                None,  # No progress tracker for concurrent execution
            )
            if best_portfolio is not None:
                batch_portfolios.append(best_portfolio)

        except Exception as e:
            log(f"Error processing ticker {ticker}: {str(e)}", "error")
            continue

    return batch_portfolios


def create_ticker_batches(
    tickers: List[str], batch_size: int = None
) -> List[List[str]]:
    """Create batches of tickers for concurrent processing.

    Args:
        tickers: List of all tickers to process
        batch_size: Size of each batch (defaults to optimal size based on ticker count)

    Returns:
        List of ticker batches
    """
    if batch_size is None:
        # Optimize batch size based on ticker count
        if len(tickers) <= 4:
            batch_size = 1  # One ticker per thread for small lists
        elif len(tickers) <= 20:
            batch_size = 2  # Two tickers per thread for medium lists
        else:
            batch_size = max(
                1, len(tickers) // 8
            )  # Distribute across 8 threads for large lists

    batches = []
    for i in range(0, len(tickers), batch_size):
        batches.append(tickers[i : i + batch_size])

    return batches


@monitor_performance("strategy_execution_concurrent", track_throughput=True)
def execute_strategy_concurrent(
    config: Config,
    strategy_type: str,
    log: callable,
    progress_tracker: Optional["ProgressTracker"] = None,
    max_workers: int = 4,
) -> List[Dict[str, Any]]:
    """Execute a trading strategy for all tickers using concurrent processing.

    Args:
        config (Config): Configuration for the analysis
        strategy_type (str): Strategy type (e.g., 'EMA', 'SMA')
        log (callable): Logging function
        progress_tracker (Optional[ProgressTracker]): Progress tracking object
        max_workers (int): Maximum number of concurrent workers

    Returns:
        List[Dict[str, Any]]: List of best portfolios found
    """
    # Generate unique execution ID for performance tracking
    execution_id = str(uuid.uuid4())

    if "TICKER" not in config:
        log(
            f"ERROR: TICKER key not found in config. Available keys: {list(config.keys())}",
            "error",
        )
        return []

    tickers = (
        [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
    )

    # For small ticker lists, use sequential processing to avoid overhead
    if len(tickers) <= 2:
        log(f"Using sequential processing for {len(tickers)} tickers", "info")
        return execute_strategy(config, strategy_type, log, progress_tracker)

    log(
        f"Using concurrent processing for {len(tickers)} tickers with {max_workers} workers",
        "info",
    )

    # Initialize performance tracking
    tracker = get_strategy_performance_tracker()

    # Calculate parameter combinations for tracking
    short_windows = config.get("SHORT_WINDOWS", [5])
    long_windows = config.get("LONG_WINDOWS", [20])
    parameter_combinations = len(tickers) * len(short_windows) * len(long_windows)

    # Create ticker batches for optimal processing
    ticker_batches = create_ticker_batches(tickers)

    tracker.start_strategy_execution(
        execution_id=execution_id,
        strategy_type=strategy_type,
        ticker_count=len(tickers),
        parameter_combinations=parameter_combinations,
        concurrent_execution=True,
        batch_size=len(ticker_batches[0]) if ticker_batches else 1,
        worker_count=max_workers,
    )

    # Update progress if tracker provided
    if progress_tracker:
        progress_tracker.set_total_steps(len(tickers))
        progress_tracker.update(
            phase="analysis",
            message=f"Starting concurrent {strategy_type} strategy analysis",
        )
    log(
        f"Created {len(ticker_batches)} ticker batches for concurrent processing",
        "info",
    )

    all_portfolios = []
    processed_count = 0

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all batch processing tasks
        future_to_batch = {
            executor.submit(
                process_ticker_batch, batch, config, strategy_type, log
            ): batch
            for batch in ticker_batches
        }

        # Process completed tasks as they finish
        for future in as_completed(future_to_batch):
            batch = future_to_batch[future]
            try:
                batch_portfolios = future.result()
                all_portfolios.extend(batch_portfolios)
                processed_count += len(batch)

                # Update progress
                if progress_tracker:
                    progress_tracker.update(
                        step=processed_count,
                        message=f"Processed {processed_count}/{len(tickers)} tickers",
                    )

                # Update performance tracking progress
                tracker.update_execution_progress(
                    execution_id=execution_id, portfolios_generated=len(all_portfolios)
                )

                log(
                    f"Completed batch with {len(batch)} tickers, found {len(batch_portfolios)} portfolios",
                    "info",
                )

            except Exception as e:
                log(f"Batch processing failed for {batch}: {str(e)}", "error")
                # Update error count in performance tracking
                tracker.update_execution_progress(
                    execution_id=execution_id, error_count=1
                )
                # Continue processing other batches
                continue

    # Mark analysis complete
    if progress_tracker:
        progress_tracker.complete(
            f"Completed concurrent {strategy_type} analysis for {len(tickers)} tickers"
        )

    # Finalize performance tracking
    tracker.update_execution_progress(
        execution_id=execution_id,
        portfolios_generated=len(all_portfolios),
        portfolios_filtered=len(
            all_portfolios
        ),  # For best portfolios, filtered equals generated
    )

    final_metrics = tracker.end_strategy_execution(execution_id)
    if final_metrics:
        log(
            f"Concurrent strategy execution completed with efficiency score: {final_metrics.calculate_efficiency_score():.2f}"
        )

    log(
        f"Concurrent processing completed: {len(all_portfolios)} total portfolios found",
        "info",
    )
    return all_portfolios


@monitor_performance("strategy_execution", track_throughput=True)
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
    # Generate unique execution ID for performance tracking
    execution_id = str(uuid.uuid4())

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

    # Initialize performance tracking
    tracker = get_strategy_performance_tracker()

    # Calculate parameter combinations for tracking
    short_windows = config.get("SHORT_WINDOWS", [5])
    long_windows = config.get("LONG_WINDOWS", [20])
    parameter_combinations = len(tickers) * len(short_windows) * len(long_windows)

    tracker.start_strategy_execution(
        execution_id=execution_id,
        strategy_type=strategy_type,
        ticker_count=len(tickers),
        parameter_combinations=parameter_combinations,
        concurrent_execution=False,  # This is the sequential version
        batch_size=None,
        worker_count=None,
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

        # Pass the formatted ticker from config to ensure synthetic tickers are
        # preserved
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

        # Update performance tracking progress
        tracker.update_execution_progress(
            execution_id=execution_id, portfolios_generated=len(best_portfolios)
        )

    # Mark analysis complete
    if progress_tracker:
        progress_tracker.complete(
            f"Completed {strategy_type} analysis for {len(tickers)} tickers"
        )

    # Finalize performance tracking
    tracker.update_execution_progress(
        execution_id=execution_id,
        portfolios_generated=len(best_portfolios),
        portfolios_filtered=len(
            best_portfolios
        ),  # Filtered count equals generated for best portfolios
    )

    final_metrics = tracker.end_strategy_execution(execution_id)
    if final_metrics:
        log(
            f"Strategy execution completed with efficiency score: {final_metrics.calculate_efficiency_score():.2f}"
        )

    return best_portfolios
