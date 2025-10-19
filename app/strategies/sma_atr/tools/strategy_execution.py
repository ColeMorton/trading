"""
SMA_ATR Strategy Execution Module

This module handles the execution of SMA_ATR trading strategies,
which combine SMA crossovers for entry signals with ATR trailing stops for exits.
"""

from typing import TYPE_CHECKING, Any

from app.strategies.sma_atr.config_types import Config
from app.tools.backtest_strategy import backtest_strategy
from app.tools.calculate_atr import calculate_atr
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.stats_converter import convert_stats
from app.tools.strategy.signal_utils import is_exit_signal_current, is_signal_current


if TYPE_CHECKING:
    pass

import numpy as np
import polars as pl


def cache_sma_entry_signals(
    data: pl.DataFrame,
    fast_period: int,
    slow_period: int,
    config: dict,
    log: callable,
) -> pl.DataFrame:
    """
    Cache SMA entry signals for reuse across multiple ATR parameter combinations.

    Args:
        data: Price data DataFrame
        fast_period: Fast SMA period
        slow_period: Slow SMA period
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame with SMA signals and price data (no ATR exit logic applied)
    """
    try:
        # Calculate SMA signals using existing functionality
        data_with_sma = calculate_ma_and_signals(
            data, fast_period, slow_period, config, log, strategy_type="SMA"
        )

        log(
            f"Cached SMA entry signals for Fast:{fast_period}, Slow:{slow_period}",
            "debug",
        )
        return data_with_sma

    except Exception as e:
        log(f"Error caching SMA entry signals: {e}", "error")
        raise


def apply_atr_exits_to_cached_entries(
    cached_sma_data: pl.DataFrame,
    atr_length: int,
    atr_multiplier: float,
    current_price: float,
    config: dict,
    log: callable,
) -> pl.DataFrame:
    """
    Apply ATR trailing stop exits to cached SMA entry signals.

    Args:
        cached_sma_data: DataFrame with cached SMA entry signals
        atr_length: ATR calculation length
        atr_multiplier: ATR multiplier for trailing stop
        current_price: Current market price for parameter validation
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame with complete SMA_ATR signals and positions
    """
    try:
        # Calculate ATR for trailing stops
        atr_series = calculate_atr(cached_sma_data.to_pandas(), atr_length)

        # Add ATR column to cached data
        data_with_atr = cached_sma_data.with_columns(
            [pl.Series("ATR", atr_series.values)]
        )

        # Validate ATR parameters based on current market context
        current_atr = atr_series.iloc[-1] if len(atr_series) > 0 else 1.0
        potential_stop = current_price - (current_atr * atr_multiplier)

        # Skip ATR stop combinations that equal current price or more (ensures valid exit signals)
        if potential_stop >= current_price:
            log(
                f"Skipping invalid ATR combination: length={atr_length}, multiplier={atr_multiplier} (stop at/above current price)",
                "debug",
            )
            return None

        # Apply ATR exits to cached SMA entries
        data_with_signals = generate_sma_atr_positions(
            data_with_atr, atr_multiplier, config, log
        )

        return data_with_signals

    except Exception as e:
        log(f"Error applying ATR exits: {e}", "error")
        raise


def apply_atr_exits_to_precalculated_data(
    data_with_atr: pl.DataFrame,
    atr_multiplier: float,
    current_price: float,
    config: dict,
    log: callable,
) -> pl.DataFrame:
    """
    Apply ATR trailing stop exits to data that already has ATR calculated (performance optimized).

    Args:
        data_with_atr: DataFrame with SMA entry signals and pre-calculated ATR column
        atr_multiplier: ATR multiplier for trailing stop
        current_price: Current market price for parameter validation
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame with complete SMA_ATR signals and positions
    """
    try:
        # Extract current ATR value for market-adaptive filtering
        atr_values = data_with_atr.select(pl.col("ATR")).to_pandas()["ATR"]
        current_atr = atr_values.iloc[-1] if len(atr_values) > 0 else 1.0
        potential_stop = current_price - (current_atr * atr_multiplier)

        # Skip ATR stop combinations that equal current price or more (ensures valid exit signals)
        if potential_stop >= current_price:
            return None

        # Apply ATR exits using pre-calculated ATR data (no recalculation!)
        data_with_signals = generate_sma_atr_positions(
            data_with_atr, atr_multiplier, config, log
        )

        return data_with_signals

    except Exception as e:
        log(f"Error applying ATR exits to precalculated data: {e}", "error")
        raise


def execute_backtest_on_signals(
    ticker: str,
    signals_data: pl.DataFrame,
    config: dict,
    log: callable,
) -> dict | None:
    """
    Execute backtest using pre-computed SMA_ATR signals (optimization for caching).

    Args:
        ticker: The ticker symbol
        signals_data: DataFrame with complete SMA_ATR signals already computed
        config: Configuration containing strategy parameters
        log: Logging function

    Returns:
        Optional[Dict]: Strategy performance metrics if successful, None otherwise
    """
    try:
        # Check if there's a current entry signal using pre-computed data
        current_signal = is_signal_current(signals_data, config)
        # Reduced logging: only log once per ticker, not per combination

        # Check if there's a current exit signal using pre-computed data
        exit_signal = is_exit_signal_current(signals_data, config)

        # Run backtest using the pre-computed signals (skip signal recalculation)
        portfolio = backtest_strategy(signals_data, config, log)
        if portfolio is None:
            return None

        # Get raw stats from vectorbt
        stats = portfolio.stats()

        # Check for invalid metrics before converting stats
        from app.tools.portfolio.filters import check_invalid_metrics

        valid_stats = check_invalid_metrics(stats, log)
        if valid_stats is None:
            log(
                f"Portfolio for {ticker} with SMA_ATR strategy has invalid metrics - skipping",
                "info",
            )
            return None

        # Convert stats using the standard format
        converted_stats = convert_stats(
            valid_stats, log, config, current_signal, exit_signal
        )

        # Add strategy identification fields (same as original implementation)
        converted_stats.update(
            {
                "TICKER": ticker,
                "Ticker": ticker,  # Add both formats for compatibility
                "Strategy Type": "SMA_ATR",
                "Fast Period": config["FAST_PERIOD"],
                "Slow Period": config["SLOW_PERIOD"],
                "Exit Fast Period": config.get("ATR_LENGTH", 14),
                "Exit Slow Period": round(
                    config.get("ATR_MULTIPLIER", 2.0), 1
                ),  # Round to 1 decimal to avoid floating point errors
                "Exit Signal Period": None,  # Not used by ATR strategy
                "Allocation [%]": config.get("ALLOCATION"),
                "Stop Loss [%]": config.get("STOP_LOSS"),
            }
        )

        return converted_stats

    except Exception as e:
        log(f"Failed to execute backtest on signals: {e!s}", "error")
        return None


def calculate_sma_atr_signals(
    data: pl.DataFrame,
    fast_period: int,
    slow_period: int,
    atr_length: int,
    atr_multiplier: float,
    config: dict,
    log: callable,
) -> pl.DataFrame:
    """
    Calculate SMA_ATR signals combining SMA crossovers for entry and ATR trailing stops for exit.

    Args:
        data: Price data DataFrame
        fast_period: Fast SMA period
        slow_period: Slow SMA period
        atr_length: ATR calculation length
        atr_multiplier: ATR multiplier for trailing stop
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame with SMA_ATR signals and positions
    """
    try:
        # First, calculate SMA signals for entries using existing functionality
        # We'll use SMA specifically (not EMA) for this strategy
        data_with_sma = calculate_ma_and_signals(
            data, fast_period, slow_period, config, log, strategy_type="SMA"
        )

        # Calculate ATR for trailing stops
        atr_series = calculate_atr(data_with_sma.to_pandas(), atr_length)

        # Convert back to polars and add ATR column
        # atr_series is a pandas Series, so we get its values directly
        data_with_atr = data_with_sma.with_columns(
            [pl.Series("ATR", atr_series.values)]
        )

        # Generate combined SMA_ATR signals
        data_with_signals = generate_sma_atr_positions(
            data_with_atr, atr_multiplier, config, log
        )

        return data_with_signals

    except Exception as e:
        log(f"Error calculating SMA_ATR signals: {e}", "error")
        raise


def generate_sma_atr_positions(
    data: pl.DataFrame, atr_multiplier: float, config: dict, log: callable
) -> pl.DataFrame:
    """
    Generate trading positions using SMA entries and ATR trailing stops (OPTIMIZED).

    This implementation uses numpy vectorized operations where possible while maintaining
    a minimal loop for complex state transitions. Provides significant performance improvement
    while ensuring mathematical correctness and full vectorbt integration.

    Args:
        data: DataFrame with SMA signals and ATR values
        atr_multiplier: ATR multiplier for trailing stop calculation
        config: Configuration dictionary
        log: Logging function

    Returns:
        DataFrame with SMA_ATR positions
    """
    try:
        direction = config.get("DIRECTION", "Long")

        # Convert to pandas for optimized operations
        df = data.to_pandas()

        # Pre-allocate arrays for performance
        n = len(df)
        positions = np.zeros(n, dtype=np.int8)
        trailing_stops = np.full(n, np.nan, dtype=np.float64)
        highest_since_entry = np.full(n, np.nan, dtype=np.float64)

        # Extract arrays for vectorized access
        close_prices = df["Close"].values
        atr_values = df["ATR"].values
        sma_signals = df["Signal"].values

        if direction == "Long":
            # OPTIMIZED LONG POSITION ALGORITHM
            position = 0
            trailing_stop = np.nan
            highest_price = np.nan

            # Vectorized main loop with minimal state tracking
            for i in range(1, n):
                current_price = close_prices[i]
                current_atr = atr_values[i]
                sma_signal = sma_signals[i]

                if position == 0:  # Not in position
                    if sma_signal == 1:  # SMA buy signal
                        position = 1
                        trailing_stop = current_price - (current_atr * atr_multiplier)
                        highest_price = current_price

                elif position == 1:  # In long position
                    # Update highest price (vectorized where possible)
                    highest_price = max(current_price, highest_price)

                    # Update trailing stop (can only move up)
                    new_stop = highest_price - (current_atr * atr_multiplier)
                    if not np.isnan(trailing_stop):
                        trailing_stop = max(trailing_stop, new_stop)
                    else:
                        trailing_stop = new_stop

                    # Check exit conditions
                    if current_price <= trailing_stop or sma_signal == -1:
                        position = 0
                        trailing_stop = np.nan
                        highest_price = np.nan

                # Store state in pre-allocated arrays
                positions[i] = position
                trailing_stops[i] = trailing_stop
                highest_since_entry[i] = highest_price

        else:  # Short direction
            # OPTIMIZED SHORT POSITION ALGORITHM
            position = 0
            trailing_stop = np.nan
            lowest_price = np.nan

            for i in range(1, n):
                current_price = close_prices[i]
                current_atr = atr_values[i]
                sma_signal = sma_signals[i]

                if position == 0:  # Not in position
                    if sma_signal == -1:  # SMA sell signal
                        position = -1
                        trailing_stop = current_price + (current_atr * atr_multiplier)
                        lowest_price = current_price

                elif position == -1:  # In short position
                    # Update lowest price since entry
                    lowest_price = min(current_price, lowest_price)

                    # Update trailing stop (can only move down)
                    new_stop = lowest_price + (current_atr * atr_multiplier)
                    if not np.isnan(trailing_stop):
                        trailing_stop = min(trailing_stop, new_stop)
                    else:
                        trailing_stop = new_stop

                    # Check exit conditions
                    if current_price >= trailing_stop or sma_signal == 1:
                        position = 0
                        trailing_stop = np.nan
                        lowest_price = np.nan

                # Store state
                positions[i] = position
                trailing_stops[i] = trailing_stop
                highest_since_entry[i] = lowest_price  # For short, this tracks lowest

        # Assign arrays back to dataframe (vectorized assignment)
        df["Position"] = positions
        df["TrailingStop"] = trailing_stops
        df["HighestSinceEntry"] = highest_since_entry

        # Convert back to polars
        result_data = pl.from_pandas(df)

        return result_data

    except Exception as e:
        log(f"Error generating SMA_ATR positions (optimized): {e}", "error")
        raise


def execute_single_strategy(
    ticker: str, data: pl.DataFrame, config: Config, log: callable
) -> dict | None:
    """Execute a single SMA_ATR strategy with specified parameters and pre-fetched data.

    Args:
        ticker: The ticker symbol
        data: Pre-fetched price data DataFrame
        config: Configuration containing SMA_ATR parameters
        log: Logging function

    Returns:
        Optional[Dict]: Strategy performance metrics if successful, None otherwise
    """
    try:
        # Use pre-fetched data (no redundant data fetching)
        if data is None:
            log(f"No price data provided for {ticker}", "error")
            return None

        # Calculate SMA_ATR signals
        data = calculate_sma_atr_signals(
            data,
            config["FAST_PERIOD"],
            config["SLOW_PERIOD"],
            config.get("ATR_LENGTH", 14),
            config.get("ATR_MULTIPLIER", 2.0),
            config,
            log,
        )
        if data is None:
            log(f"Failed to calculate SMA_ATR signals for {ticker}", "error")
            return None

        # Check if there's a current entry signal
        current_signal = is_signal_current(data, config)

        # Check if there's a current exit signal
        exit_signal = is_exit_signal_current(data, config)

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
                f"Portfolio for {ticker} with SMA_ATR strategy has invalid metrics - skipping",
                "info",
            )
            return None

        # Convert stats using app/tools/stats_converter.py
        converted_stats = convert_stats(
            valid_stats, log, config, current_signal, exit_signal
        )

        # Add strategy identification fields
        converted_stats.update(
            {
                "TICKER": ticker,
                "Ticker": ticker,  # Add both formats for compatibility
                "Strategy Type": "SMA_ATR",
                "Fast Period": config["FAST_PERIOD"],
                "Slow Period": config["SLOW_PERIOD"],
                "Exit Fast Period": config.get("ATR_LENGTH", 14),
                "Exit Slow Period": round(
                    config.get("ATR_MULTIPLIER", 2.0), 1
                ),  # Round to 1 decimal to avoid floating point errors
                "Exit Signal Period": None,  # Not used by ATR strategy
                "Allocation [%]": config.get("ALLOCATION", None),
                "Stop Loss [%]": config.get("STOP_LOSS", None),
            }
        )

        return converted_stats

    except Exception as e:
        log(f"Failed to execute SMA_ATR strategy: {e!s}", "error")
        return None


def process_single_ticker(
    ticker: str,
    config: Config,
    log: callable,
    progress_update_fn=None,
) -> dict[str, Any] | None:
    """
    Process a single ticker through SMA_ATR parameter sweep.

    Args:
        ticker: Ticker symbol to process
        config: Strategy configuration
        log: Logging function
        progress_update_fn: Optional progress update callback

    Returns:
        Dictionary containing portfolios and metadata
    """
    try:
        log(f"Processing SMA_ATR strategy for ticker: {ticker}", "info")

        # Get price data
        data_result = get_data(ticker, config, log)
        if isinstance(data_result, tuple):
            data, synthetic_ticker = data_result
            ticker = synthetic_ticker  # Use synthetic ticker name for processing
        else:
            data = data_result

        if data is None:
            log(f"Failed to get data for {ticker}", "error")
            return None

        portfolios = []

        # Get parameter ranges
        fast_range = config.get("FAST_PERIOD_RANGE", [8, 50])
        slow_range = config.get("SLOW_PERIOD_RANGE", [11, 56])
        atr_length_values = config.get("ATR_LENGTH_RANGE", [3, 5, 7, 9, 11, 13])
        atr_multiplier_range = config.get("ATR_MULTIPLIER_RANGE", [1.0, 4.0])
        atr_multiplier_step = config.get("ATR_MULTIPLIER_STEP", 1.5)
        sma_step = config.get("STEP", 3)  # SMA parameter step size

        # Ensure step values are not None
        if atr_multiplier_step is None:
            atr_multiplier_step = 1.5
        if sma_step is None:
            sma_step = 3

        # Handle both discrete ATR length values and range-based values
        if isinstance(atr_length_values, list):
            atr_lengths = atr_length_values
        else:
            # Fallback for range-based configuration
            atr_lengths = list(range(atr_length_values[0], atr_length_values[1] + 1))

        # Calculate total combinations for progress tracking
        total_combinations = 0
        for fast in range(fast_range[0], fast_range[1] + 1, sma_step):
            for slow in range(slow_range[0], slow_range[1] + 1, sma_step):
                if fast < slow:  # Only valid SMA combinations
                    for atr_length in atr_lengths:
                        multiplier = atr_multiplier_range[0]
                        while multiplier <= atr_multiplier_range[1]:
                            total_combinations += 1
                            multiplier += atr_multiplier_step

        processed_combinations = 0
        log(
            f"Processing {total_combinations} SMA_ATR parameter combinations for {ticker}",
            "info",
        )

        # Get current price for market-adaptive filtering
        current_price = float(data.select(pl.col("Close").last()).item())

        # OPTIMIZED Parameter sweep with SMA entry caching, ATR caching, and filtering
        sma_entry_cache = {}  # Cache for SMA entry signals
        atr_cache = {}  # Cache for ATR calculations by length

        for fast in range(fast_range[0], fast_range[1] + 1, sma_step):
            for slow in range(slow_range[0], slow_range[1] + 1, sma_step):
                if fast >= slow:  # Skip invalid combinations
                    continue

                # PHASE 1: Cache SMA entry signals (once per SMA combination)
                sma_key = f"{fast}_{slow}"
                if sma_key not in sma_entry_cache:
                    try:
                        cached_sma_signals = cache_sma_entry_signals(
                            data, fast, slow, config, log
                        )
                        sma_entry_cache[sma_key] = cached_sma_signals
                        log(
                            f"Cached SMA entry signals for Fast:{fast}, Slow:{slow}",
                            "debug",
                        )
                    except Exception as e:
                        log(
                            f"Error caching SMA signals Fast:{fast}, Slow:{slow}: {e}",
                            "warning",
                        )
                        continue

                # PHASE 1.5: Pre-calculate ATR for all lengths (once per SMA combination)
                for atr_length in atr_lengths:
                    atr_key = f"{sma_key}_{atr_length}"
                    if atr_key not in atr_cache:
                        try:
                            atr_series = calculate_atr(
                                sma_entry_cache[sma_key].to_pandas(), atr_length
                            )
                            data_with_atr = sma_entry_cache[sma_key].with_columns(
                                [pl.Series("ATR", atr_series.values)]
                            )
                            atr_cache[atr_key] = data_with_atr
                            log(
                                f"Cached ATR calculation for {sma_key}, length:{atr_length}",
                                "debug",
                            )
                        except Exception as e:
                            log(
                                f"Error caching ATR for {sma_key}, length:{atr_length}: {e}",
                                "warning",
                            )
                            continue

                # PHASE 2: Apply ATR exits using cached ATR data
                for atr_length in atr_lengths:
                    multiplier = atr_multiplier_range[0]
                    while multiplier <= atr_multiplier_range[1]:
                        try:
                            # Use cached ATR data instead of recalculating
                            atr_key = f"{sma_key}_{atr_length}"
                            if atr_key not in atr_cache:
                                log(
                                    f"ATR cache miss for {atr_key} - skipping combination",
                                    "warning",
                                )
                                processed_combinations += 1
                                if progress_update_fn:
                                    progress_update_fn(1)
                                multiplier += atr_multiplier_step
                                continue

                            # Apply ATR exits using pre-calculated ATR data (no recalculation!)
                            complete_signals = apply_atr_exits_to_precalculated_data(
                                atr_cache[atr_key],
                                atr_multiplier=multiplier,
                                current_price=current_price,
                                config=config,
                                log=log,
                            )

                            # Skip if ATR combination was filtered out
                            if complete_signals is None:
                                log(
                                    f"Filtered out ATR combination: Fast:{fast}, Slow:{slow}, ATR:{atr_length}, Mult:{multiplier:.1f}",
                                    "debug",
                                )
                                processed_combinations += 1
                                if progress_update_fn:
                                    progress_update_fn(1)
                                multiplier += atr_multiplier_step
                                continue

                            # Create config for backtesting
                            param_config = config.copy()
                            param_config.update(
                                {
                                    "FAST_PERIOD": fast,
                                    "SLOW_PERIOD": slow,
                                    "ATR_LENGTH": atr_length,
                                    "ATR_MULTIPLIER": multiplier,
                                }
                            )

                            # Run backtest with complete signals (skip signal recalculation)
                            result = execute_backtest_on_signals(
                                ticker, complete_signals, param_config, log
                            )
                            if result is not None:
                                portfolios.append(result)

                            processed_combinations += 1

                            # Update progress if callback provided
                            if progress_update_fn:
                                progress_update_fn(1)

                        except Exception as e:
                            log(
                                f"Error processing combination Fast:{fast}, Slow:{slow}, ATR:{atr_length}, Mult:{multiplier:.1f}: {e}",
                                "warning",
                            )

                        multiplier += atr_multiplier_step

        log("Performance optimization applied:", "info")
        log(
            f"  SMA entry signal caching: {len(sma_entry_cache)} unique combinations cached",
            "info",
        )
        log(
            f"  ATR calculation caching: {len(atr_cache)} unique ATR calculations cached",
            "info",
        )
        # PHASE 4 FIX: Correct performance calculation
        # Without caching: total_combinations would each calculate ATR separately
        # With caching: only len(atr_cache) unique ATR calculations needed
        atr_performance_gain = (
            total_combinations // len(atr_cache) if len(atr_cache) > 0 else 0
        )
        log(
            f"  ATR performance gain: {total_combinations} calculations without caching vs {len(atr_cache)} with caching ({atr_performance_gain}x improvement)",
            "info",
        )

        log(
            f"Generated {len(portfolios)} valid SMA_ATR portfolios for {ticker}", "info"
        )

        # Return portfolios directly for orchestration compatibility
        # The orchestration system expects a list of portfolio dictionaries, not a wrapper dict
        return portfolios

    except Exception as e:
        log(f"Error processing ticker {ticker}: {e}", "error")
        return None


def execute_strategy(
    config: Config,
    log: callable,
    progress_update_fn=None,
) -> bool:
    """
    Execute SMA_ATR strategy for configured tickers.

    Args:
        config: Strategy configuration
        log: Logging function
        progress_update_fn: Optional progress update callback

    Returns:
        True if execution succeeded, False otherwise
    """
    try:
        # Use PortfolioOrchestrator for standardized execution
        from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator

        orchestrator = PortfolioOrchestrator(log)

        # Execute the orchestration workflow with progress callback
        return orchestrator.run(config, progress_update_fn)

    except Exception as e:
        log(f"SMA_ATR strategy execution failed: {e}", "error")
        return False
