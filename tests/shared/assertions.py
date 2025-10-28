"""
Custom assertions for trading system testing infrastructure.
Phase 3: Testing Infrastructure Consolidation
"""

from typing import Any

import polars as pl
import pytest


def assert_portfolio_performance(
    portfolio_result: dict[str, Any],
    min_return: float | None = None,
    max_drawdown: float | None = None,
    min_sharpe: float | None = None,
    min_win_rate: float | None = None,
):
    """
    Assert portfolio performance meets criteria.

    Args:
        portfolio_result: Portfolio performance dictionary
        min_return: Minimum required return
        max_drawdown: Maximum allowed drawdown
        min_sharpe: Minimum required Sharpe ratio
        min_win_rate: Minimum required win rate
    """
    assert isinstance(portfolio_result, dict), "Portfolio result must be a dictionary"

    required_fields = ["total_return", "max_drawdown", "sharpe_ratio", "win_rate"]
    for field in required_fields:
        assert (
            field in portfolio_result
        ), f"Portfolio result missing required field: {field}"

    if min_return is not None:
        assert (
            portfolio_result["total_return"] >= min_return
        ), f"Return {portfolio_result['total_return']:.2%} below minimum {min_return:.2%}"

    if max_drawdown is not None:
        assert (
            portfolio_result["max_drawdown"] <= max_drawdown
        ), f"Drawdown {portfolio_result['max_drawdown']:.2%} exceeds maximum {max_drawdown:.2%}"

    if min_sharpe is not None:
        assert (
            portfolio_result["sharpe_ratio"] >= min_sharpe
        ), f"Sharpe ratio {portfolio_result['sharpe_ratio']:.2f} below minimum {min_sharpe:.2f}"

    if min_win_rate is not None:
        assert (
            portfolio_result["win_rate"] >= min_win_rate
        ), f"Win rate {portfolio_result['win_rate']:.2%} below minimum {min_win_rate:.2%}"


def assert_market_data_valid(
    data: pl.DataFrame | dict,
    required_columns: list[str] | None = None,
    min_rows: int = 1,
):
    """
    Assert market data is valid and complete.

    Args:
        data: Market data DataFrame or dictionary
        required_columns: List of required column names
        min_rows: Minimum number of rows required
    """
    if isinstance(data, dict):
        assert "data" in data, "Market data dictionary must contain 'data' key"
        data = data["data"]

    assert isinstance(data, pl.DataFrame), "Market data must be a Polars DataFrame"
    assert (
        len(data) >= min_rows
    ), f"Market data has {len(data)} rows, minimum {min_rows} required"

    if required_columns is None:
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

    for col in required_columns:
        assert col in data.columns, f"Market data missing required column: {col}"

    # Check for valid OHLC relationships
    if all(col in data.columns for col in ["Open", "High", "Low", "Close"]):
        # High should be >= max(Open, Close)
        high_valid = (data["High"] >= data["Open"]) & (data["High"] >= data["Close"])
        assert high_valid.all(), "Invalid High prices detected"

        # Low should be <= min(Open, Close)
        low_valid = (data["Low"] <= data["Open"]) & (data["Low"] <= data["Close"])
        assert low_valid.all(), "Invalid Low prices detected"

    # Check for non-negative Volume
    if "Volume" in data.columns:
        assert (data["Volume"] >= 0).all(), "Negative volume detected"


def assert_trading_signals_valid(
    signals: pl.DataFrame | list[dict[str, Any]],
    valid_signal_types: list[str] | None = None,
):
    """
    Assert trading signals are valid.

    Args:
        signals: Trading signals DataFrame or list
        valid_signal_types: List of valid signal types
    """
    if isinstance(signals, list):
        assert len(signals) > 0, "Signal list cannot be empty"
        signals = pl.DataFrame(signals)

    assert isinstance(signals, pl.DataFrame), "Signals must be a Polars DataFrame"
    assert len(signals) > 0, "Signals DataFrame cannot be empty"

    required_columns = ["Date", "Ticker", "Signal"]
    for col in required_columns:
        assert col in signals.columns, f"Signals missing required column: {col}"

    if valid_signal_types is None:
        valid_signal_types = ["BUY", "SELL", "HOLD"]

    signal_values = signals["Signal"].unique().to_list()
    invalid_signals = [s for s in signal_values if s not in valid_signal_types]
    assert len(invalid_signals) == 0, f"Invalid signal types found: {invalid_signals}"

    # Check for valid confidence scores if present
    if "Confidence" in signals.columns:
        confidence_values = signals["Confidence"]
        assert (confidence_values >= 0).all(), "Confidence scores cannot be negative"
        assert (confidence_values <= 1).all(), "Confidence scores cannot exceed 1.0"


def assert_risk_metrics_valid(
    risk_metrics: dict[str, float],
    check_bounds: bool = True,
):
    """
    Assert risk metrics are valid and within expected bounds.

    Args:
        risk_metrics: Dictionary of risk metrics
        check_bounds: Whether to check metric bounds
    """
    assert isinstance(risk_metrics, dict), "Risk metrics must be a dictionary"

    required_metrics = ["sharpe_ratio", "max_drawdown"]
    for metric in required_metrics:
        assert metric in risk_metrics, f"Risk metrics missing required metric: {metric}"
        assert isinstance(
            risk_metrics[metric],
            int | float,
        ), f"Risk metric {metric} must be numeric"

    if check_bounds:
        # Max drawdown should be between 0 and 1 (or negative)
        max_dd = risk_metrics["max_drawdown"]
        assert -1 <= max_dd <= 1, f"Max drawdown {max_dd} outside valid range [-1, 1]"

        # Sharpe ratio should be reasonable (typically -3 to +5)
        sharpe = risk_metrics["sharpe_ratio"]
        assert (
            -5 <= sharpe <= 10
        ), f"Sharpe ratio {sharpe} outside reasonable range [-5, 10]"

        # Check VaR if present
        if "var_95" in risk_metrics:
            var = risk_metrics["var_95"]
            assert var <= 0, f"VaR should be negative or zero, got {var}"

        # Check beta if present
        if "beta" in risk_metrics:
            beta = risk_metrics["beta"]
            assert 0 <= beta <= 3, f"Beta {beta} outside reasonable range [0, 3]"


def assert_backtest_results_valid(
    backtest_results: dict[str, Any],
    min_trades: int = 1,
    require_positive_return: bool = False,
):
    """
    Assert backtest results are valid and complete.

    Args:
        backtest_results: Backtest results dictionary
        min_trades: Minimum number of trades required
        require_positive_return: Whether to require positive returns
    """
    assert isinstance(backtest_results, dict), "Backtest results must be a dictionary"

    required_fields = [
        "total_return",
        "num_trades",
        "win_rate",
        "max_drawdown",
        "sharpe_ratio",
        "start_date",
        "end_date",
    ]

    for field in required_fields:
        assert (
            field in backtest_results
        ), f"Backtest results missing required field: {field}"

    # Check trade count
    num_trades = backtest_results["num_trades"]
    assert (
        num_trades >= min_trades
    ), f"Backtest has {num_trades} trades, minimum {min_trades} required"

    # Check win rate bounds
    win_rate = backtest_results["win_rate"]
    assert 0 <= win_rate <= 1, f"Win rate {win_rate} outside valid range [0, 1]"

    # Check date order
    start_date = backtest_results["start_date"]
    end_date = backtest_results["end_date"]
    assert start_date < end_date, "Start date must be before end date"

    # Check return requirement
    if require_positive_return:
        total_return = backtest_results["total_return"]
        assert total_return > 0, f"Backtest return {total_return:.2%} is not positive"

    # Validate risk metrics
    risk_metrics = {
        key: backtest_results[key]
        for key in ["sharpe_ratio", "max_drawdown"]
        if key in backtest_results
    }
    assert_risk_metrics_valid(risk_metrics)


def assert_configuration_valid(
    config: dict[str, Any],
    schema: dict[str, type] | None = None,
):
    """
    Assert configuration is valid against schema.

    Args:
        config: Configuration dictionary
        schema: Optional schema to validate against
    """
    assert isinstance(config, dict), "Configuration must be a dictionary"
    assert len(config) > 0, "Configuration cannot be empty"

    if schema:
        for field, expected_type in schema.items():
            assert field in config, f"Configuration missing required field: {field}"
            actual_type = type(config[field])
            assert actual_type == expected_type or isinstance(
                config[field],
                expected_type,
            ), f"Field {field} expected type {expected_type}, got {actual_type}"


def assert_api_response_valid(
    response: dict | Any,
    expected_status: int = 200,
    required_fields: list[str] | None = None,
):
    """
    Assert API response is valid.

    Args:
        response: API response object
        expected_status: Expected HTTP status code
        required_fields: List of required fields in response
    """
    # Check status code if response has status_code attribute
    if hasattr(response, "status_code"):
        assert (
            response.status_code == expected_status
        ), f"Expected status {expected_status}, got {response.status_code}"

    # Parse JSON if response has json() method
    if hasattr(response, "json"):
        data = response.json()
    else:
        data = response

    assert isinstance(data, dict), "API response must be a dictionary"

    if required_fields:
        for field in required_fields:
            assert field in data, f"API response missing required field: {field}"


def assert_performance_within_tolerance(
    actual_time: float,
    expected_time: float,
    tolerance: float = 0.2,
):
    """
    Assert performance is within acceptable tolerance.

    Args:
        actual_time: Actual execution time
        expected_time: Expected execution time
        tolerance: Tolerance as fraction (0.2 = 20%)
    """
    assert actual_time > 0, "Execution time must be positive"

    min_time = expected_time * (1 - tolerance)
    max_time = expected_time * (1 + tolerance)

    assert (
        min_time <= actual_time <= max_time
    ), f"Execution time {actual_time:.2f}s outside tolerance [{min_time:.2f}s, {max_time:.2f}s]"


def assert_dataframe_schema(df: pl.DataFrame, expected_schema: dict[str, pl.DataType]):
    """
    Assert DataFrame has expected schema.

    Args:
        df: Polars DataFrame to validate
        expected_schema: Expected column name to type mapping
    """
    assert isinstance(df, pl.DataFrame), "Input must be a Polars DataFrame"

    # Check all expected columns exist
    for col_name, expected_type in expected_schema.items():
        assert col_name in df.columns, f"Missing expected column: {col_name}"

        actual_type = df[col_name].dtype
        assert (
            actual_type == expected_type
        ), f"Column {col_name} expected type {expected_type}, got {actual_type}"

    # Check for unexpected columns
    unexpected_cols = set(df.columns) - set(expected_schema.keys())
    if unexpected_cols:
        pytest.warnings.warn(f"Unexpected columns found: {unexpected_cols}")


def assert_no_data_leakage(
    train_data: pl.DataFrame,
    test_data: pl.DataFrame,
    date_column: str = "Date",
):
    """
    Assert no data leakage between train and test sets.

    Args:
        train_data: Training dataset
        test_data: Test dataset
        date_column: Name of date column
    """
    assert date_column in train_data.columns, f"Train data missing {date_column} column"
    assert date_column in test_data.columns, f"Test data missing {date_column} column"

    train_max_date = train_data[date_column].max()
    test_min_date = test_data[date_column].min()

    assert (
        train_max_date < test_min_date
    ), f"Data leakage detected: train max date {train_max_date} >= test min date {test_min_date}"


class PerformanceAssertion:
    """Context manager for performance assertions."""

    def __init__(self, max_duration: float, operation_name: str = "operation"):
        self.max_duration = max_duration
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        import time

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time

        self.end_time = time.time()
        duration = self.end_time - self.start_time

        assert (
            duration <= self.max_duration
        ), f"{self.operation_name} took {duration:.2f}s, expected <= {self.max_duration:.2f}s"


class MemoryAssertion:
    """Context manager for memory usage assertions."""

    def __init__(self, max_memory_mb: float, operation_name: str = "operation"):
        self.max_memory_mb = max_memory_mb
        self.operation_name = operation_name
        self.initial_memory = None
        self.peak_memory = None

    def __enter__(self):
        import os

        import psutil

        self.process = psutil.Process(os.getpid())
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - self.initial_memory

        assert (
            memory_increase <= self.max_memory_mb
        ), f"{self.operation_name} used {memory_increase:.2f}MB, expected <= {self.max_memory_mb:.2f}MB"
