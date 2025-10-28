#!/usr/bin/env python3
"""
ATR Strategy Test Fixtures and Utilities

Shared test utilities, fixtures, and helper functions for ATR strategy testing:
- Market data generators with realistic patterns
- Configuration builders and validators
- Assertion helpers for ATR-specific validation
- Mock objects and test doubles
- Performance measurement utilities
- Common test data patterns

Focus: Reusable testing infrastructure for consistent ATR test implementation
"""

from collections.abc import Callable
import os
import tempfile
from typing import Any
from unittest.mock import Mock

import numpy as np
import pandas as pd
import polars as pl


class ATRTestDataGenerator:
    """Generate various types of market data for ATR testing."""

    @staticmethod
    def create_trending_data(
        start_date: str = "2020-01-01",
        periods: int = 252,
        start_price: float = 100.0,
        trend: float = 0.001,
        volatility: float = 0.02,
        ticker: str = "TEST",
    ) -> pd.DataFrame:
        """Create trending market data with specified characteristics."""
        dates = pd.date_range(start_date, periods=periods, freq="D")

        # Generate returns with trend
        np.random.seed(42)  # Reproducible for testing
        returns = np.random.normal(trend, volatility, periods)
        prices = start_price * np.exp(np.cumsum(returns))

        # Create realistic OHLC data
        daily_ranges = np.abs(np.random.normal(0, volatility * 0.3, periods))
        highs = prices * (1 + daily_ranges)
        lows = prices * (1 - daily_ranges * 0.8)
        opens = prices * np.random.uniform(0.999, 1.001, periods)
        volumes = np.random.randint(100000, 1000000, periods)

        return pd.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": volumes,
                "Ticker": ticker,
            },
        ).set_index("Date")

    @staticmethod
    def create_ranging_data(
        start_date: str = "2020-01-01",
        periods: int = 252,
        base_price: float = 100.0,
        range_width: float = 10.0,
        volatility: float = 0.015,
        ticker: str = "RANGE",
    ) -> pd.DataFrame:
        """Create ranging/sideways market data."""
        dates = pd.date_range(start_date, periods=periods, freq="D")

        # Create oscillating pattern within range
        np.random.seed(123)
        cycle_length = 20  # Days per cycle
        cycles = np.arange(periods) / cycle_length
        base_oscillation = np.sin(cycles * 2 * np.pi) * (range_width / 2)

        # Add noise
        noise = np.random.normal(0, volatility * base_price, periods)
        prices = base_price + base_oscillation + noise

        # Create OHLC
        daily_ranges = np.abs(
            np.random.normal(0, volatility * base_price * 0.5, periods),
        )
        highs = prices + daily_ranges
        lows = prices - daily_ranges * 0.8
        opens = prices * np.random.uniform(0.998, 1.002, periods)
        volumes = np.random.randint(50000, 500000, periods)

        return pd.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": volumes,
                "Ticker": ticker,
            },
        ).set_index("Date")

    @staticmethod
    def create_volatile_data(
        start_date: str = "2020-01-01",
        periods: int = 252,
        start_price: float = 100.0,
        base_volatility: float = 0.05,
        volatility_clustering: bool = True,
        ticker: str = "VOLATILE",
    ) -> pd.DataFrame:
        """Create highly volatile market data with clustering."""
        dates = pd.date_range(start_date, periods=periods, freq="D")

        np.random.seed(789)
        returns = []
        current_vol = base_volatility

        for _i in range(periods):
            if volatility_clustering:
                # GARCH-like volatility clustering
                vol_persistence = 0.9
                vol_innovation = np.random.gamma(2, base_volatility * 0.1)
                current_vol = (
                    vol_persistence * current_vol
                    + (1 - vol_persistence) * vol_innovation
                )
            else:
                current_vol = base_volatility

            # Generate return with current volatility
            ret = np.random.normal(0, current_vol)
            returns.append(ret)

        prices = start_price * np.exp(np.cumsum(returns))

        # Exaggerated OHLC for volatile data
        daily_ranges = np.abs(np.random.normal(0, current_vol * 0.8, periods))
        highs = prices * (1 + daily_ranges)
        lows = prices * (1 - daily_ranges)
        opens = prices * np.random.uniform(0.99, 1.01, periods)
        volumes = np.random.randint(200000, 2000000, periods)

        return pd.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": volumes,
                "Ticker": ticker,
            },
        ).set_index("Date")

    @staticmethod
    def create_crash_recovery_data(
        start_date: str = "2020-01-01",
        periods: int = 500,
        start_price: float = 100.0,
        crash_start: int = 100,
        crash_duration: int = 50,
        crash_magnitude: float = -0.4,
        recovery_duration: int = 150,
        ticker: str = "CRASH",
    ) -> pd.DataFrame:
        """Create data with market crash and recovery pattern."""
        dates = pd.date_range(start_date, periods=periods, freq="D")

        np.random.seed(456)
        prices = []
        current_price = start_price

        for i in range(periods):
            if crash_start <= i < crash_start + crash_duration:
                # Crash period: negative trend with high volatility
                daily_return = np.random.normal(crash_magnitude / crash_duration, 0.08)
            elif (
                crash_start + crash_duration
                <= i
                < crash_start + crash_duration + recovery_duration
            ):
                # Recovery period: positive trend with moderate volatility
                recovery_rate = (
                    -crash_magnitude / recovery_duration * 1.5
                )  # Faster recovery
                daily_return = np.random.normal(recovery_rate, 0.04)
            else:
                # Normal periods: slight positive trend
                daily_return = np.random.normal(0.0005, 0.02)

            current_price *= 1 + daily_return
            prices.append(current_price)

        # Create OHLC
        highs = [p * np.random.uniform(1.005, 1.03) for p in prices]
        lows = [p * np.random.uniform(0.97, 0.995) for p in prices]
        opens = [p * np.random.uniform(0.995, 1.005) for p in prices]
        volumes = np.random.randint(500000, 5000000, periods)

        return pd.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": volumes,
                "Ticker": ticker,
            },
        ).set_index("Date")


class ATRTestConfigBuilder:
    """Build various ATR test configurations."""

    @staticmethod
    def create_basic_config(
        ticker: str = "TEST",
        atr_length_min: int = 10,
        atr_length_max: int = 20,
        atr_multiplier_min: float = 1.5,
        atr_multiplier_max: float = 3.0,
        atr_multiplier_step: float = 0.5,
        use_current: bool = False,
    ) -> dict[str, Any]:
        """Create basic ATR configuration for testing."""
        return {
            "TICKER": ticker,
            "ATR_LENGTH_MIN": atr_length_min,
            "ATR_LENGTH_MAX": atr_length_max,
            "ATR_MULTIPLIER_MIN": atr_multiplier_min,
            "ATR_MULTIPLIER_MAX": atr_multiplier_max,
            "ATR_MULTIPLIER_STEP": atr_multiplier_step,
            "USE_CURRENT": use_current,
            "BASE_DIR": tempfile.mkdtemp(),
            "DIRECTION": "Long",
            "MINIMUMS": {
                "WIN_RATE": 0.30,
                "TRADES": 5,
                "EXPECTANCY_PER_TRADE": 0.0,
                "PROFIT_FACTOR": 1.0,
                "SORTINO_RATIO": 0.0,
            },
            "SORT_BY": "Score",
            "SORT_ASC": False,
        }

    @staticmethod
    def create_performance_config(
        ticker: str = "PERF_TEST",
        large_parameter_space: bool = False,
    ) -> dict[str, Any]:
        """Create configuration optimized for performance testing."""
        if large_parameter_space:
            return {
                "TICKER": ticker,
                "ATR_LENGTH_MIN": 5,
                "ATR_LENGTH_MAX": 25,  # 21 lengths
                "ATR_MULTIPLIER_MIN": 1.0,
                "ATR_MULTIPLIER_MAX": 5.0,  # 9 multipliers
                "ATR_MULTIPLIER_STEP": 0.5,
                "USE_CURRENT": False,
                "BASE_DIR": tempfile.mkdtemp(),
                "DIRECTION": "Long",
                "MINIMUMS": {
                    "WIN_RATE": 0.20,
                    "TRADES": 3,
                    "EXPECTANCY_PER_TRADE": -10.0,
                    "PROFIT_FACTOR": 0.5,
                    "SORTINO_RATIO": -5.0,
                },
            }
        return ATRTestConfigBuilder.create_basic_config(ticker)

    @staticmethod
    def create_regression_config(ticker: str = "REGRESSION") -> dict[str, Any]:
        """Create configuration for regression testing."""
        config = ATRTestConfigBuilder.create_basic_config(ticker)
        config.update(
            {
                "ATR_LENGTH_MIN": 14,
                "ATR_LENGTH_MAX": 15,  # Limited range for focused testing
                "ATR_MULTIPLIER_MIN": 1.5,
                "ATR_MULTIPLIER_MAX": 2.5,
                "ATR_MULTIPLIER_STEP": 0.5,
            },
        )
        return config


class ATRTestAssertions:
    """Custom assertion helpers for ATR testing."""

    @staticmethod
    def assert_valid_atr_portfolio(
        portfolio: dict[str, Any],
        ticker: str | None = None,
    ):
        """Assert that portfolio dictionary has valid ATR structure."""
        # Required fields
        required_fields = [
            "Ticker",
            "Strategy Type",
            "Fast Period",
            "Slow Period",
            "Signal Period",
            "Total Trades",
            "Win Rate [%]",
            "Total Return [%]",
            "Score",
        ]

        for field in required_fields:
            assert field in portfolio, f"Missing required field: {field}"

        # ATR-specific validations
        assert (
            portfolio["Strategy Type"] == "ATR"
        ), f"Expected ATR, got {portfolio['Strategy Type']}"
        assert (
            portfolio["Signal Period"] == 0
        ), f"ATR Signal Period should be 0, got {portfolio['Signal Period']}"

        if ticker:
            assert (
                portfolio["Ticker"] == ticker
            ), f"Expected ticker {ticker}, got {portfolio['Ticker']}"

        # Numeric validations
        assert isinstance(
            portfolio["Fast Period"],
            int | float,
        ), "Fast Period should be numeric"
        assert isinstance(
            portfolio["Slow Period"],
            int | float,
        ), "Slow Period should be numeric"
        assert isinstance(
            portfolio["Total Trades"],
            int | float,
        ), "Total Trades should be numeric"
        assert isinstance(
            portfolio["Win Rate [%]"],
            int | float,
        ), "Win Rate should be numeric"
        assert isinstance(portfolio["Score"], int | float), "Score should be numeric"

        # Range validations
        assert (
            0 <= portfolio["Win Rate [%]"] <= 100
        ), f"Invalid Win Rate: {portfolio['Win Rate [%]']}"
        assert (
            portfolio["Total Trades"] >= 0
        ), f"Negative Total Trades: {portfolio['Total Trades']}"

    @staticmethod
    def assert_valid_signals_dataframe(signals_df: pd.DataFrame):
        """Assert that signals DataFrame has valid ATR structure."""
        required_columns = ["Signal", "ATR_Trailing_Stop", "ATR", "Position"]

        for col in required_columns:
            assert col in signals_df.columns, f"Missing required column: {col}"

        # Data type validations
        signal_values = signals_df["Signal"].dropna().unique()
        valid_signals = {0, 1}  # Only 0 and 1 are valid for ATR
        assert set(signal_values).issubset(
            valid_signals,
        ), f"Invalid signal values: {signal_values}"

        # ATR values should be positive
        atr_values = signals_df["ATR"].dropna()
        if len(atr_values) > 0:
            assert (atr_values > 0).all(), "ATR values should be positive"

        # Trailing stop values should be positive
        stop_values = signals_df["ATR_Trailing_Stop"].dropna()
        if len(stop_values) > 0:
            assert (
                stop_values > 0
            ).all(), "ATR Trailing Stop values should be positive"

    @staticmethod
    def assert_no_regression_bugs(portfolio: dict[str, Any], ticker: str):
        """Assert that common regression bugs are not present."""
        # Bug 1: Ticker corruption (shows as "UNKNOWN")
        assert (
            portfolio["Ticker"] != "UNKNOWN"
        ), "REGRESSION: Ticker corruption detected"
        assert (
            portfolio["Ticker"] == ticker
        ), f"REGRESSION: Ticker mismatch {portfolio['Ticker']} != {ticker}"

        # Bug 2: Strategy type corruption (shows as "SMA")
        assert (
            portfolio["Strategy Type"] == "ATR"
        ), f"REGRESSION: Wrong strategy type {portfolio['Strategy Type']}"

        # Bug 3: Hardcoded period values (20, 50)
        assert (
            portfolio["Fast Period"] != 20 or portfolio["Slow Period"] != 50
        ), "REGRESSION: Hardcoded period values detected"

        # Bug 4: Score always zero
        if portfolio["Total Trades"] > 0:
            assert portfolio["Score"] != 0.0, "REGRESSION: Score calculation broken"

        # Bug 5: Signal Entry always true (if field exists)
        if "Signal Entry" in portfolio:
            # Can't test specific value without context, but should be string representation
            assert isinstance(
                portfolio["Signal Entry"],
                str,
            ), "Signal Entry should be string representation"

    @staticmethod
    def assert_performance_acceptable(
        execution_time: float,
        memory_usage: float,
        dataset_size: int,
        max_time_per_row: float = 0.01,
        max_memory_per_row: float = 0.1,
    ):
        """Assert that performance metrics are within acceptable bounds."""
        time_per_row = execution_time / dataset_size
        memory_per_row = memory_usage / dataset_size

        assert (
            time_per_row <= max_time_per_row
        ), f"Performance regression: {time_per_row:.6f}s/row > {max_time_per_row}s/row"

        assert (
            memory_per_row <= max_memory_per_row
        ), f"Memory regression: {memory_per_row:.3f}MB/row > {max_memory_per_row}MB/row"


class ATRTestMocks:
    """Mock objects and test doubles for ATR testing."""

    @staticmethod
    def create_mock_logger() -> Mock:
        """Create mock logger for testing."""
        mock_logger = Mock()
        mock_logger.log_messages = []

        def capture_log(message, level="info"):
            mock_logger.log_messages.append(f"{level}: {message}")

        mock_logger.side_effect = capture_log
        return mock_logger

    @staticmethod
    def create_mock_data_loader(data: pd.DataFrame) -> Mock:
        """Create mock data loader that returns specified data."""
        mock_loader = Mock()
        mock_loader.return_value = pl.from_pandas(data.reset_index())
        return mock_loader

    @staticmethod
    def create_mock_progress_tracker() -> Mock:
        """Create mock progress tracker for testing."""
        mock_tracker = Mock()
        mock_tracker.total_steps = 0
        mock_tracker.current_step = 0

        def set_total(total):
            mock_tracker.total_steps = total

        def update():
            mock_tracker.current_step += 1

        def complete():
            mock_tracker.current_step = mock_tracker.total_steps

        mock_tracker.set_total_steps = Mock(side_effect=set_total)
        mock_tracker.update = Mock(side_effect=update)
        mock_tracker.complete = Mock(side_effect=complete)

        return mock_tracker

    @staticmethod
    def create_mock_export_function(capture_data: bool = True) -> Mock:
        """Create mock export function for testing."""
        mock_export = Mock()
        if capture_data:
            mock_export.captured_data = []
            mock_export.captured_paths = []

            def capture_export(data, path):
                mock_export.captured_data.append(data)
                mock_export.captured_paths.append(path)
                return True

            mock_export.side_effect = capture_export
        else:
            mock_export.return_value = True

        return mock_export


class ATRTestUtilities:
    """Utility functions for ATR testing."""

    @staticmethod
    def calculate_expected_atr_manual(data: pd.DataFrame, length: int) -> pd.Series:
        """Calculate ATR manually for validation against implementation."""
        # Manual True Range calculation
        tr_values = []

        for i in range(1, len(data)):
            high = data["High"].iloc[i]
            low = data["Low"].iloc[i]
            prev_close = data["Close"].iloc[i - 1]

            tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)

        # Calculate ATR as simple moving average of TR
        atr_values = []
        for i in range(length - 1, len(tr_values)):
            atr = np.mean(tr_values[i - length + 1 : i + 1])
            atr_values.append(atr)

        # Create series with proper index alignment
        atr_index = data.index[length:]  # Skip first 'length' rows
        return pd.Series(atr_values, index=atr_index, name="ATR_Manual")

    @staticmethod
    def generate_parameter_combinations(
        atr_length_min: int,
        atr_length_max: int,
        atr_multiplier_min: float,
        atr_multiplier_max: float,
        atr_multiplier_step: float,
    ) -> list[tuple]:
        """Generate all parameter combinations for testing."""
        combinations = []

        lengths = list(range(atr_length_min, atr_length_max + 1))

        # Generate multiplier values
        multipliers = []
        mult = atr_multiplier_min
        while (
            mult <= atr_multiplier_max + 1e-10
        ):  # Small epsilon for floating point comparison
            multipliers.append(round(mult, 1))  # Round to avoid floating point issues
            mult += atr_multiplier_step

        for length in lengths:
            for multiplier in multipliers:
                combinations.append((length, multiplier))

        return combinations

    @staticmethod
    def create_temporary_config_file(
        config: dict[str, Any],
        filename: str | None = None,
    ) -> str:
        """Create temporary configuration file for testing."""
        import yaml

        if filename is None:
            temp_file = tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".yaml",
                delete=False,
            )
            filename = temp_file.name
        else:
            temp_file = open(filename, "w")

        yaml.dump(config, temp_file, default_flow_style=False)
        temp_file.close()

        return filename

    @staticmethod
    def cleanup_test_files(file_paths: list[str]):
        """Clean up temporary test files."""
        for path in file_paths:
            try:
                if os.path.exists(path):
                    if os.path.isdir(path):
                        import shutil

                        shutil.rmtree(path)
                    else:
                        os.remove(path)
            except Exception as e:
                print(f"Warning: Could not cleanup {path}: {e}")

    @staticmethod
    def measure_execution_time(func: Callable, *args, **kwargs) -> tuple:
        """Measure execution time of function call."""
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def measure_memory_usage(func: Callable, *args, **kwargs) -> tuple:
        """Measure memory usage of function call."""
        import gc

        import psutil

        process = psutil.Process()

        gc.collect()  # Clean up before measurement
        start_memory = process.memory_info().rss / 1024 / 1024  # MB

        result = func(*args, **kwargs)

        gc.collect()  # Clean up after measurement
        end_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_usage = end_memory - start_memory
        return result, memory_usage


# Convenience imports for easy access
__all__ = [
    "ATRTestAssertions",
    "ATRTestConfigBuilder",
    "ATRTestDataGenerator",
    "ATRTestMocks",
    "ATRTestUtilities",
]
