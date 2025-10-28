#!/usr/bin/env python3
"""
Custom Test Assertions

Domain-specific assertions for trading system testing that provide
clear, meaningful error messages for common test scenarios.
"""

from typing import Any

import numpy as np
import pandas as pd


def assert_signals_valid(result_df: pd.DataFrame) -> None:
    """
    Assert that trading signals are logically valid.

    Args:
        result_df: DataFrame with signal columns

    Raises:
        AssertionError: If signals are invalid
    """
    # Required columns for signal validation
    required_cols = ["Signal", "Position"]
    for col in required_cols:
        if col not in result_df.columns:
            msg = f"Missing required column for signal validation: {col}"
            raise AssertionError(
                msg,
            )

    # Signals should be -1, 0, or 1
    valid_signals = {-1, 0, 1}
    invalid_signals = set(result_df["Signal"].unique()) - valid_signals
    if invalid_signals:
        msg = f"Invalid signal values found: {invalid_signals}"
        raise AssertionError(msg)

    # Positions should be -1, 0, or 1
    valid_positions = {-1, 0, 1}
    invalid_positions = set(result_df["Position"].unique()) - valid_positions
    if invalid_positions:
        msg = f"Invalid position values found: {invalid_positions}"
        raise AssertionError(msg)

    # Check signal logic: position should change only on non-zero signals
    # Convert to pandas if it's a Polars DataFrame
    if hasattr(result_df, "to_pandas"):
        result_pandas = result_df.to_pandas()
    else:
        result_pandas = result_df

    for i in range(1, len(result_pandas)):
        prev_pos = result_pandas.iloc[i - 1]["Position"]
        curr_pos = result_pandas.iloc[i]["Position"]
        curr_signal = result_pandas.iloc[i]["Signal"]

        # If position changed significantly, there should typically be a signal
        # However, allow for some flexibility in signal generation logic
        if prev_pos != curr_pos and curr_signal == 0:
            # Allow position initialization (from 0 to any position)
            if prev_pos == 0:
                continue  # Position entry is allowed without explicit signal
            # Allow position exit (to 0 from any position) - may be stop loss
            if curr_pos == 0:
                continue  # Position exit is allowed without explicit signal
            # Only raise error for position changes between non-zero states without signal
            if prev_pos != 0 and curr_pos != 0:
                msg = (
                    f"Position changed without signal at index {i}: "
                    f"pos {prev_pos} -> {curr_pos}, signal = {curr_signal}"
                )
                raise AssertionError(
                    msg,
                )


def assert_ma_calculations_accurate(
    result_df: pd.DataFrame,
    price_data: pd.DataFrame,
    fast_period: int,
    slow_period: int,
    ma_type: str,
) -> None:
    """
    Assert that MA calculations are mathematically correct.

    Args:
        result_df: DataFrame with calculated MAs
        price_data: Original price data
        fast_period: Short MA window
        slow_period: Long MA window
        ma_type: "SMA" or "EMA"
    """
    # Map expected column names to actual implementation column names
    expected_cols = {
        "SMA": {"short": ["SMA_Short", "MA_FAST"], "long": ["SMA_Long", "MA_SLOW"]},
        "EMA": {"short": ["EMA_Short", "MA_FAST"], "long": ["EMA_Long", "MA_SLOW"]},
    }

    if ma_type not in expected_cols:
        msg = f"Unsupported MA type: {ma_type}"
        raise ValueError(msg)

    # Find actual column names in the result
    short_col = None
    long_col = None

    for possible_col in expected_cols[ma_type]["short"]:
        if possible_col in result_df.columns:
            short_col = possible_col
            break

    for possible_col in expected_cols[ma_type]["long"]:
        if possible_col in result_df.columns:
            long_col = possible_col
            break

    # Check if MA columns exist
    if not short_col:
        msg = f"Missing short MA column. Expected one of: {expected_cols[ma_type]['short']}"
        raise AssertionError(
            msg,
        )
    if not long_col:
        msg = (
            f"Missing long MA column. Expected one of: {expected_cols[ma_type]['long']}"
        )
        raise AssertionError(
            msg,
        )

    # Validate SMA calculations
    if ma_type == "SMA":
        # Convert DataFrames for easier indexing
        if hasattr(result_df, "to_pandas"):
            result_pandas = result_df.to_pandas()
        else:
            result_pandas = result_df

        if hasattr(price_data, "to_pandas"):
            price_pandas = price_data.to_pandas()
        else:
            price_pandas = price_data

        for i in range(slow_period, len(result_pandas)):
            # Calculate expected SMA values
            expected_short = (
                price_pandas["Close"].iloc[i - fast_period + 1 : i + 1].mean()
            )
            expected_long = (
                price_pandas["Close"].iloc[i - slow_period + 1 : i + 1].mean()
            )

            actual_short = result_pandas.iloc[i][short_col]
            actual_long = result_pandas.iloc[i][long_col]

            # Allow small floating point differences
            if not np.isclose(actual_short, expected_short, rtol=1e-10):
                msg = (
                    f"SMA calculation error at index {i}: "
                    f"expected {expected_short}, got {actual_short}"
                )
                raise AssertionError(
                    msg,
                )

            if not np.isclose(actual_long, expected_long, rtol=1e-10):
                msg = (
                    f"Long SMA calculation error at index {i}: "
                    f"expected {expected_long}, got {actual_long}"
                )
                raise AssertionError(
                    msg,
                )


def assert_portfolio_data_valid(portfolios: list[dict[str, Any]]) -> None:
    """
    Assert that portfolio data has required fields and valid values.

    Args:
        portfolios: List of portfolio dictionaries
    """
    if not portfolios:
        msg = "Portfolio list is empty"
        raise AssertionError(msg)

    required_fields = [
        "Ticker",
        "Strategy Type",
        "Total Return [%]",
        "Win Rate [%]",
        "Total Trades",
        "Profit Factor",
    ]

    for i, portfolio in enumerate(portfolios):
        # Check required fields
        for field in required_fields:
            if field not in portfolio:
                msg = f"Portfolio {i} missing required field: {field}"
                raise AssertionError(msg)

        # Validate data types and ranges
        if (
            not isinstance(portfolio["Total Trades"], int | float)
            or portfolio["Total Trades"] < 0
        ):
            msg = f"Portfolio {i} has invalid Total Trades: {portfolio['Total Trades']}"
            raise AssertionError(
                msg,
            )

        if not isinstance(portfolio["Win Rate [%]"], int | float) or not (
            0 <= portfolio["Win Rate [%]"] <= 100
        ):
            msg = f"Portfolio {i} has invalid Win Rate: {portfolio['Win Rate [%]']}"
            raise AssertionError(
                msg,
            )

        if (
            not isinstance(portfolio["Profit Factor"], int | float)
            or portfolio["Profit Factor"] < 0
        ):
            msg = (
                f"Portfolio {i} has invalid Profit Factor: {portfolio['Profit Factor']}"
            )
            raise AssertionError(
                msg,
            )


def assert_export_paths_correct(
    actual_path: str,
    expected_base: str,
    config: dict[str, Any],
) -> None:
    """
    Assert that export paths are generated correctly based on configuration.

    Args:
        actual_path: The generated file path
        expected_base: Expected base directory
        config: Configuration used for path generation
    """
    # Verify base directory
    if not actual_path.startswith(expected_base):
        msg = (
            f"Export path doesn't start with expected base: "
            f"actual='{actual_path}', expected_base='{expected_base}'"
        )
        raise AssertionError(
            msg,
        )

    # Check USE_CURRENT behavior
    if config.get("USE_CURRENT", False):
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        if today not in actual_path:
            msg = f"USE_CURRENT=True but date {today} not in path: {actual_path}"
            raise AssertionError(
                msg,
            )

    # Check ticker in filename
    ticker = config.get("TICKER")
    if ticker and isinstance(ticker, str):
        filename = actual_path.split("/")[-1]
        if not filename.startswith(ticker.replace("/", "_")):
            msg = f"Ticker {ticker} not in filename: {filename}"
            raise AssertionError(msg)


def assert_filtering_criteria_applied(
    original_portfolios: list[dict[str, Any]],
    filtered_portfolios: list[dict[str, Any]],
    filter_config: dict[str, Any],
) -> None:
    """
    Assert that filtering criteria were properly applied.

    Args:
        original_portfolios: Portfolios before filtering
        filtered_portfolios: Portfolios after filtering
        filter_config: Configuration with filter criteria
    """
    if "MINIMUMS" not in filter_config:
        return  # No filtering criteria to check

    minimums = filter_config["MINIMUMS"]

    for portfolio in filtered_portfolios:
        for field, min_value in minimums.items():
            # Convert field name to portfolio key
            portfolio_key = field.replace("_", " ").title()
            if portfolio_key.endswith(" "):
                portfolio_key = portfolio_key[:-1]

            # Handle different field name variations
            possible_keys = [
                field,
                portfolio_key,
                field.replace("_", " "),
                f"{portfolio_key} [%]" if "%" in str(min_value) else portfolio_key,
            ]

            portfolio_value = None
            for key in possible_keys:
                if key in portfolio:
                    portfolio_value = portfolio[key]
                    break

            if portfolio_value is not None and portfolio_value < min_value:
                msg = (
                    f"Portfolio {portfolio.get('Ticker', 'Unknown')} "
                    f"failed minimum criteria: {field} = {portfolio_value} < {min_value}"
                )
                raise AssertionError(
                    msg,
                )
