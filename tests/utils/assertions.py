#!/usr/bin/env python3
"""
Custom Test Assertions

Domain-specific assertions for trading system testing that provide
clear, meaningful error messages for common test scenarios.
"""

from typing import Any, Dict, List

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
            raise AssertionError(
                f"Missing required column for signal validation: {col}"
            )

    # Signals should be -1, 0, or 1
    valid_signals = {-1, 0, 1}
    invalid_signals = set(result_df["Signal"].unique()) - valid_signals
    if invalid_signals:
        raise AssertionError(f"Invalid signal values found: {invalid_signals}")

    # Positions should be -1, 0, or 1
    valid_positions = {-1, 0, 1}
    invalid_positions = set(result_df["Position"].unique()) - valid_positions
    if invalid_positions:
        raise AssertionError(f"Invalid position values found: {invalid_positions}")

    # Check signal logic: position should change only on non-zero signals
    for i in range(1, len(result_df)):
        prev_pos = result_df.iloc[i - 1]["Position"]
        curr_pos = result_df.iloc[i]["Position"]
        curr_signal = result_df.iloc[i]["Signal"]

        # If position changed, there should be a signal
        if prev_pos != curr_pos and curr_signal == 0:
            raise AssertionError(
                f"Position changed without signal at index {i}: "
                f"pos {prev_pos} -> {curr_pos}, signal = {curr_signal}"
            )


def assert_ma_calculations_accurate(
    result_df: pd.DataFrame,
    price_data: pd.DataFrame,
    short_window: int,
    long_window: int,
    ma_type: str,
) -> None:
    """
    Assert that MA calculations are mathematically correct.

    Args:
        result_df: DataFrame with calculated MAs
        price_data: Original price data
        short_window: Short MA window
        long_window: Long MA window
        ma_type: "SMA" or "EMA"
    """
    if ma_type == "SMA":
        short_col = "SMA_Short"
        long_col = "SMA_Long"
    elif ma_type == "EMA":
        short_col = "EMA_Short"
        long_col = "EMA_Long"
    else:
        raise ValueError(f"Unsupported MA type: {ma_type}")

    # Check if MA columns exist
    for col in [short_col, long_col]:
        if col not in result_df.columns:
            raise AssertionError(f"Missing MA column: {col}")

    # Validate SMA calculations
    if ma_type == "SMA":
        for i in range(long_window, len(result_df)):
            # Calculate expected SMA values
            expected_short = (
                price_data["Close"].iloc[i - short_window + 1 : i + 1].mean()
            )
            expected_long = price_data["Close"].iloc[i - long_window + 1 : i + 1].mean()

            actual_short = result_df.iloc[i][short_col]
            actual_long = result_df.iloc[i][long_col]

            # Allow small floating point differences
            if not np.isclose(actual_short, expected_short, rtol=1e-10):
                raise AssertionError(
                    f"SMA calculation error at index {i}: "
                    f"expected {expected_short}, got {actual_short}"
                )

            if not np.isclose(actual_long, expected_long, rtol=1e-10):
                raise AssertionError(
                    f"Long SMA calculation error at index {i}: "
                    f"expected {expected_long}, got {actual_long}"
                )


def assert_portfolio_data_valid(portfolios: List[Dict[str, Any]]) -> None:
    """
    Assert that portfolio data has required fields and valid values.

    Args:
        portfolios: List of portfolio dictionaries
    """
    if not portfolios:
        raise AssertionError("Portfolio list is empty")

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
                raise AssertionError(f"Portfolio {i} missing required field: {field}")

        # Validate data types and ranges
        if (
            not isinstance(portfolio["Total Trades"], (int, float))
            or portfolio["Total Trades"] < 0
        ):
            raise AssertionError(
                f"Portfolio {i} has invalid Total Trades: {portfolio['Total Trades']}"
            )

        if not isinstance(portfolio["Win Rate [%]"], (int, float)) or not (
            0 <= portfolio["Win Rate [%]"] <= 100
        ):
            raise AssertionError(
                f"Portfolio {i} has invalid Win Rate: {portfolio['Win Rate [%]']}"
            )

        if (
            not isinstance(portfolio["Profit Factor"], (int, float))
            or portfolio["Profit Factor"] < 0
        ):
            raise AssertionError(
                f"Portfolio {i} has invalid Profit Factor: {portfolio['Profit Factor']}"
            )


def assert_export_paths_correct(
    actual_path: str, expected_base: str, config: Dict[str, Any]
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
        raise AssertionError(
            f"Export path doesn't start with expected base: "
            f"actual='{actual_path}', expected_base='{expected_base}'"
        )

    # Check USE_CURRENT behavior
    if config.get("USE_CURRENT", False):
        from datetime import datetime

        today = datetime.now().strftime("%Y%m%d")
        if today not in actual_path:
            raise AssertionError(
                f"USE_CURRENT=True but date {today} not in path: {actual_path}"
            )

    # Check ticker in filename
    ticker = config.get("TICKER")
    if ticker and isinstance(ticker, str):
        filename = actual_path.split("/")[-1]
        if not filename.startswith(ticker.replace("/", "_")):
            raise AssertionError(f"Ticker {ticker} not in filename: {filename}")


def assert_filtering_criteria_applied(
    original_portfolios: List[Dict[str, Any]],
    filtered_portfolios: List[Dict[str, Any]],
    filter_config: Dict[str, Any],
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
                raise AssertionError(
                    f"Portfolio {portfolio.get('Ticker', 'Unknown')} "
                    f"failed minimum criteria: {field} = {portfolio_value} < {min_value}"
                )
