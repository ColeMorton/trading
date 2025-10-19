"""
ATR Strategy Execution Module

This module handles the execution of ATR trailing stop strategies, including portfolio processing,
parameter sweeps, and portfolio generation for both single and multiple tickers.
"""

from typing import Any

import numpy as np
import pandas as pd
import vectorbt as vbt

from app.strategies.atr.config_types import ATRConfig
from app.tools.backtest_strategy import backtest_strategy
from app.tools.get_data import get_data
from app.tools.stats_converter import convert_stats


def calculate_atr(data: pd.DataFrame, length: int) -> pd.Series:
    """
    Calculate Average True Range (ATR) using vectorized operations.

    Args:
        data (pd.DataFrame): Price data with High, Low, Close columns
        length (int): ATR period length

    Returns:
        pd.Series: ATR values
    """
    # Ensure data has proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        print("Warning: Data index is not DatetimeIndex in calculate_atr.")

    # Vectorized calculation of true range components
    high_low = data["High"] - data["Low"]
    high_close = np.abs(data["High"] - data["Close"].shift())
    low_close = np.abs(data["Low"] - data["Close"].shift())

    # Create a DataFrame with the three components, ensuring it has the same
    # index as the input data
    ranges = pd.DataFrame(
        {"HL": high_low, "HC": high_close, "LC": low_close}, index=data.index
    )

    # Calculate the true range as the maximum of the three components
    true_range = ranges.max(axis=1)

    # Use pandas rolling mean for the ATR calculation
    atr = true_range.rolling(window=length).mean()

    # Ensure the result has the same index as the input data
    return pd.Series(atr.values, index=data.index)


def generate_signals(
    data: pd.DataFrame, atr_length: int, atr_multiplier: float, direction: str = "Long"
) -> pd.DataFrame:
    """
    Generate trading signals based on proper ATR Trailing Stop algorithm.

    Implements standard ATR trailing stop behavior for both Long and Short directions:

    Long Direction:
    - When not in position: trailing stop moves freely with price
    - When in position: trailing stop can only move up (never down)
    - Entry: close >= trailing stop (when not in position)
    - Exit: close < trailing stop (when in position)

    Short Direction:
    - When not in position: trailing stop moves freely with price
    - When in position: trailing stop can only move down (never up)
    - Entry: close <= trailing stop (when not in position)
    - Exit: close > trailing stop (when in position)

    Args:
        data (pd.DataFrame): Price data
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier
        direction (str): Trading direction - "Long" or "Short"

    Returns:
        pd.DataFrame: Data with signals and trailing stop values
    """
    # Create a copy to avoid modifying the original
    data = data.copy()

    # Ensure data has a proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        if "Date" in data.columns:
            data = data.set_index("Date")
        else:
            # Create a dummy datetime index if no date column exists
            data = data.reset_index(drop=True)
            data.index = pd.date_range(start="2000-01-01", periods=len(data), freq="D")

    # Ensure all input columns are 1D arrays
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in data.columns:
            # Check if values are 2D and flatten if needed
            if hasattr(data[col].values, "shape") and len(data[col].values.shape) > 1:
                data[col] = pd.Series(data[col].values.flatten(), index=data.index)

    # Calculate ATR
    data["ATR"] = calculate_atr(data, atr_length)

    # Initialize columns
    data["Signal"] = pd.Series(np.zeros(len(data)), index=data.index)
    data["ATR_Trailing_Stop"] = pd.Series(np.full(len(data), np.nan), index=data.index)

    # Track position state
    in_position = False
    trailing_stop = np.nan

    # Generate signals using proper ATR trailing stop logic
    is_long = direction.lower() == "long"

    for i in range(1, len(data)):
        current_high = float(data["High"].iloc[i])
        current_low = float(data["Low"].iloc[i])
        current_close = float(data["Close"].iloc[i])
        current_atr = float(data["ATR"].iloc[i])

        if pd.isna(current_atr):
            continue

        # Calculate potential trailing stop for this period
        if is_long:
            # Long: trailing stop below price (high - atr * multiplier)
            potential_stop = current_high - (current_atr * atr_multiplier)
        else:
            # Short: trailing stop above price (low + atr * multiplier)
            potential_stop = current_low + (current_atr * atr_multiplier)

        if not in_position:
            # When not in position, trailing stop moves freely with price
            trailing_stop = potential_stop

            # Check for entry signal based on direction
            if is_long:
                # Long entry: close >= trailing stop
                if current_close >= trailing_stop:
                    data.loc[data.index[i], "Signal"] = 1
                    in_position = True
                else:
                    data.loc[data.index[i], "Signal"] = 0
            # Short entry: close <= trailing stop
            elif current_close <= trailing_stop:
                data.loc[data.index[i], "Signal"] = -1  # Use -1 for short entries
                in_position = True
            else:
                data.loc[data.index[i], "Signal"] = 0

        # When in position, trailing stop moves in favorable direction only
        elif is_long:
            # Long: trailing stop can only move up (never down)
            trailing_stop = max(trailing_stop, potential_stop)

            # Long exit: close < trailing stop
            if current_close < trailing_stop:
                data.loc[data.index[i], "Signal"] = 0
                in_position = False
            else:
                data.loc[data.index[i], "Signal"] = 1
        else:
            # Short: trailing stop can only move down (never up)
            trailing_stop = min(trailing_stop, potential_stop)

            # Short exit: close > trailing stop
            if current_close > trailing_stop:
                data.loc[data.index[i], "Signal"] = 0
                in_position = False
            else:
                data.loc[data.index[i], "Signal"] = -1  # Use -1 for short position hold

        # Store the trailing stop value for this period
        data.loc[data.index[i], "ATR_Trailing_Stop"] = trailing_stop

    # Calculate position column (shifted signals for entry/exit timing)
    data["Position"] = data["Signal"].shift()

    # Ensure all columns have the same index and are 1D arrays
    for col in data.columns:
        if isinstance(data[col], pd.Series):
            # Check if values are 2D and flatten if needed
            if hasattr(data[col].values, "shape") and len(data[col].values.shape) > 1:
                data[col] = pd.Series(data[col].values.flatten(), index=data.index)

    return data


def backtest_atr_strategy(data: pd.DataFrame) -> "vbt.Portfolio":
    """
    Backtest the ATR Trailing Stop strategy using basic VectorBT implementation.

    Note: This function is deprecated. Use the shared backtest_strategy from
    app.tools.backtest_strategy for consistent metrics across all strategies.

    Args:
        data (pd.DataFrame): Price data with signals

    Returns:
        vbt.Portfolio: Portfolio object with backtest results

    Raises:
        ValueError: If data is empty or doesn't have required columns
    """
    # Validate input data
    if len(data) == 0:
        raise ValueError("Input data is empty")

    required_columns = ["Close", "Signal"]
    for col in required_columns:
        if col not in data.columns:
            raise ValueError(f"Required column '{col}' not found in data")

    # Ensure data has proper index
    if not isinstance(data.index, pd.DatetimeIndex):
        if "Date" in data.columns:
            data = data.set_index("Date")
        else:
            # Create a dummy datetime index if no date column exists
            data = data.reset_index(drop=True)
            data.index = pd.date_range(start="2000-01-01", periods=len(data), freq="D")

    # Debug column shapes before processing
    for col in ["Close", "Signal"]:
        if hasattr(data[col].values, "shape"):
            # Ensure 1D
            if len(data[col].values.shape) > 1:
                data[col] = pd.Series(data[col].values.flatten(), index=data.index)

    # Pre-calculate entry and exit conditions for better performance
    entries = (data["Signal"] == 1) & (data["Signal"].shift(1) != 1)
    exits = (data["Signal"] == 0) & (data["Signal"].shift(1) == 1)

    # Create portfolio with vectorized operations
    try:
        # Ensure all Series are 1-dimensional and have the same index
        # Extract values as 1D arrays to prevent dimensionality issues
        close_values = data["Close"].values
        entries_values = entries.values
        exits_values = exits.values

        # Flatten if needed
        if hasattr(close_values, "shape") and len(close_values.shape) > 1:
            close_values = close_values.flatten()

        if hasattr(entries_values, "shape") and len(entries_values.shape) > 1:
            entries_values = entries_values.flatten()

        if hasattr(exits_values, "shape") and len(exits_values.shape) > 1:
            exits_values = exits_values.flatten()

        # Create Series with proper index and 1D values
        close_series = pd.Series(close_values, index=data.index)
        entries_series = pd.Series(entries_values, index=data.index)
        exits_series = pd.Series(exits_values, index=data.index)

        portfolio: vbt.Portfolio = vbt.Portfolio.from_signals(
            close=close_series,
            entries=entries_series,
            exits=exits_series,
            init_cash=1000,
            fees=0.001,
        )
        return portfolio
    except Exception:
        # Return a dummy portfolio with zero returns if backtesting fails
        dummy_index = data.index
        dummy_close = pd.Series(100, index=dummy_index)
        dummy_entries = pd.Series(False, index=dummy_index)
        dummy_exits = pd.Series(False, index=dummy_index)

        dummy_portfolio = vbt.Portfolio.from_signals(
            close=dummy_close,
            entries=dummy_entries,
            exits=dummy_exits,
            init_cash=1000,
            fees=0.001,
        )
        return dummy_portfolio


def analyze_params(
    data: pd.DataFrame,
    atr_length: int,
    atr_multiplier: float,
    ticker: str,
    log: callable,
    config: dict | None = None,
) -> dict[str, Any]:
    """
    Analyze parameters for ATR trailing stop strategy and return portfolio dict.

    Args:
        data (pd.DataFrame): Price data
        atr_length (int): ATR length
        atr_multiplier (float): ATR multiplier
        ticker (str): Ticker symbol
        log: Logging function
        config (dict): Configuration dictionary containing direction and other parameters

    Returns:
        Dict[str, Any]: Portfolio dictionary with performance metrics
    """
    try:
        # Get direction from config, default to Long for backward compatibility
        direction = "Long" if config is None else config.get("DIRECTION", "Long")

        # Generate signals with optimized function
        data_with_signals: pd.DataFrame = generate_signals(
            data.copy(), atr_length, atr_multiplier, direction
        )

        # Create config for shared backtest strategy with ATR-specific parameters
        backtest_config = {
            "TICKER": ticker,
            "USE_HOURLY": False,  # ATR uses daily data by default
            "DIRECTION": direction,  # Use direction from config (Long or Short)
            "fast_period": atr_length,  # Map ATR length to fast period
            "slow_period": int(
                atr_multiplier * 10
            ),  # Map ATR multiplier to slow period
            "signal_period": 0,  # ATR doesn't use signal period
        }

        # Convert pandas DataFrame to polars for shared backtest function
        import polars as pl

        data_polars = pl.from_pandas(data_with_signals)

        # Use shared backtest strategy for comprehensive metrics
        portfolio: vbt.Portfolio = backtest_strategy(data_polars, backtest_config, log)

        # Calculate signal information using proper ATR signal detection
        # Convert pandas DataFrame to polars for signal detection
        import polars as pl

        from app.strategies.atr.tools.signal_utils import (
            is_exit_signal_current,
            is_signal_current,
        )

        data_polars = pl.from_pandas(data_with_signals)

        # Use ATR-specific signal detection functions
        current_signal = is_signal_current(data_polars, backtest_config)
        exit_signal = is_exit_signal_current(data_polars, backtest_config)

        # Get raw stats from vectorbt (same as other strategies)
        stats = portfolio.stats()

        # Use convert_stats for consistency with other strategies (calculates Score field)
        converted_stats = convert_stats(
            stats, log, backtest_config, current_signal, exit_signal
        )

        # Override with ATR-specific field mappings to maintain proper naming
        # Ensure numeric fields are properly typed
        converted_stats.update(
            {
                "Ticker": ticker,
                "Strategy Type": "ATR",
                "Fast Period": int(atr_length),  # Use ATR length as Fast Period
                "Slow Period": int(
                    atr_multiplier * 10
                ),  # Convert multiplier to int for Slow Period
                "Signal Period": 0,  # ATR doesn't use signal period
                # Ensure signal fields reflect our ATR-specific detection
                "Signal Entry": current_signal,
                "Signal Exit": exit_signal,
            }
        )

        # Ensure critical numeric fields are proper types (fix string conversion issue)
        numeric_fields = [
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Score",
            "Profit Factor",
            "Sortino Ratio",
            "Expectancy per Trade",
        ]

        for field in numeric_fields:
            if field in converted_stats:
                value = converted_stats[field]
                if isinstance(value, str):
                    try:
                        # Try to convert string to float, then to int if it's a whole number
                        float_val = float(value)
                        if field in ["Total Trades", "Signal Period"]:
                            converted_stats[field] = int(float_val)
                        else:
                            converted_stats[field] = float_val
                    except (ValueError, TypeError):
                        # Keep original value if conversion fails
                        pass

        return converted_stats

    except Exception as e:
        log(
            f"Error in analyze_params for {ticker} (ATR {atr_length}, Mult {atr_multiplier}): {e!s}",
            "error",
        )

        # Return a minimal portfolio dict on error
        return {
            "Ticker": ticker,
            "Strategy Type": "ATR",
            "Fast Period": atr_length,
            "Slow Period": int(atr_multiplier * 10),
            "Signal Period": 0,
            "Signal Entry": False,
            "Signal Exit": False,
            "Total Trades": 0,
            "Win Rate [%]": 0.0,
            "Total Return [%]": 0.0,
            "Score": 0.0,
            "Expectancy per Trade": 0.0,
            "Profit Factor": 0.0,
        }


def execute_strategy(
    config: ATRConfig, strategy_type: str, log: callable
) -> list[dict[str, Any]]:
    """Execute ATR strategy with parameter sweep and return portfolio results.

    This function performs parameter sensitivity analysis by testing combinations
    of ATR length and multiplier values, then returns portfolio results in the
    standard format for CSV export.

    Args:
        config: Configuration dictionary
        strategy_type: Strategy type (should be "ATR")
        log: Logging function

    Returns:
        List of portfolio dictionaries
    """
    if strategy_type != "ATR":
        log(f"Warning: Expected strategy_type 'ATR', got '{strategy_type}'", "warning")

    all_portfolios = []

    # Get list of tickers to analyze
    tickers = config.get("TICKER", [])
    if isinstance(tickers, str):
        tickers = [tickers]

    if not tickers:
        log("No tickers specified in configuration", "error")
        return []

    # Define parameter ranges with robust None handling
    atr_length_start = config.get("ATR_LENGTH_START") or 2
    atr_length_end = config.get("ATR_LENGTH_END") or 15
    atr_multiplier_start = config.get("ATR_MULTIPLIER_START") or 1.5
    atr_multiplier_end = config.get("ATR_MULTIPLIER_END") or 8.0
    atr_multiplier_step = config.get("ATR_MULTIPLIER_STEP") or 0.5
    length_step = config.get("STEP") or 1

    atr_lengths = list(range(atr_length_start, atr_length_end + 1, length_step))
    atr_multipliers = list(
        np.arange(
            atr_multiplier_start,
            atr_multiplier_end + atr_multiplier_step,
            atr_multiplier_step,
        )
    )

    log(
        f"Testing {len(atr_lengths)} ATR lengths and {len(atr_multipliers)} multipliers across {len(tickers)} tickers"
    )

    for ticker in tickers:
        log(f"Processing ticker: {ticker}")

        try:
            # Get price data
            data_result = get_data(ticker, config, log)
            if isinstance(data_result, tuple):
                data, synthetic_ticker = data_result
                ticker_name = synthetic_ticker  # Use synthetic ticker name
            else:
                data = data_result
                ticker_name = ticker

            # Ensure data is a proper pandas DataFrame
            if data is None:
                log(f"Failed to get price data for {ticker} - data is None", "error")
                continue

            # Convert Polars DataFrame to pandas if needed
            if not isinstance(data, pd.DataFrame):
                try:
                    # Check if it's a Polars DataFrame
                    if hasattr(data, "to_pandas"):
                        data = data.to_pandas()
                        log(f"Converted Polars DataFrame to pandas for {ticker}")
                    else:
                        log(
                            f"Failed to get price data for {ticker} - data is not a DataFrame, got {type(data)}",
                            "error",
                        )
                        continue
                except Exception as e:
                    log(f"Failed to convert data for {ticker}: {e!s}", "error")
                    continue

            if len(data) == 0:
                log(f"Failed to get price data for {ticker} - data is empty", "error")
                continue

            # Parameter sweep
            for atr_length in atr_lengths:
                for atr_multiplier in atr_multipliers:
                    try:
                        portfolio_result = analyze_params(
                            data.copy(),
                            atr_length,
                            atr_multiplier,
                            ticker_name,
                            log,
                            config,
                        )
                        all_portfolios.append(portfolio_result)

                    except Exception as e:
                        log(
                            f"Error processing {ticker} with ATR({atr_length}, {atr_multiplier}): {e!s}",
                            "error",
                        )
                        continue

        except Exception as e:
            log(f"Error processing ticker {ticker}: {e!s}", "error")
            continue

    log(f"Generated {len(all_portfolios)} portfolio results")
    return all_portfolios
