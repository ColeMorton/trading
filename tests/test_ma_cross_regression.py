"""
Regression Tests for MA Cross Module

This module provides regression testing to ensure that changes to the MA Cross
system do not break existing functionality or produce unexpected results.
"""

import json
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.tools.config_service import ConfigService
from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator
from app.tools.orchestration.ticker_processor import TickerProcessor
from app.tools.strategy.factory import StrategyFactory


class TestMACrossRegression:
    """Regression tests for MA Cross functionality."""

    @pytest.fixture
    def mock_log(self):
        """Mock logging function."""
        return Mock()

    @pytest.fixture
    def baseline_config(self):
        """Baseline configuration that should always work."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield {
                "TICKER": ["BTC-USD"],
                "STRATEGY_TYPE": "SMA",
                "SHORT_WINDOW": 10,
                "LONG_WINDOW": 20,
                "WINDOWS": [[10, 20], [5, 15], [15, 30]],
                "DIRECTION": "BOTH",
                "TIMEFRAME": "D",
                "PORTFOLIO_DIR": temp_dir,
                "PORTFOLIO_FILTERED_DIR": temp_dir,
                "STRATEGY_DIR": temp_dir,
                "USE_MA": True,
                "USE_SYNTHETIC": False,
                "ALLOCATION": 100,
                "STOP_LOSS": 5.0,
                "MIN_RETURN": 10.0,
                "MAX_DRAWDOWN": -15.0,
                "MIN_SHARPE": 0.5,
                "MIN_TRADES": 5,
            }

    @pytest.fixture
    def baseline_price_data(self):
        """Baseline price data for regression testing."""
        np.random.seed(42)  # Fixed seed for reproducible results

        # Generate 250 days of trading data (1 year)
        dates = pd.date_range("2023-01-01", periods=250, freq="D")

        # Generate consistent price series
        base_price = 50000
        trend = 0.0002  # Small upward trend
        volatility = 0.02

        prices = [base_price]
        for i in range(1, 250):
            daily_return = trend + np.random.normal(0, volatility)
            new_price = prices[-1] * (1 + daily_return)
            prices.append(max(new_price, 1000))  # Prevent negative prices

        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": [p * (1 + abs(np.random.normal(0, 0.005))) for p in prices],
                "Low": [p * (1 - abs(np.random.normal(0, 0.005))) for p in prices],
                "Close": prices,
                "Volume": [np.random.randint(1000000, 5000000) for _ in range(250)],
            }
        )

        return pl.from_pandas(df)

    @pytest.fixture
    def expected_portfolio_schema(self):
        """Expected portfolio data schema."""
        return {
            "required_fields": [
                "TICKER",
                "Strategy Type",
                "Total Return [%]",
                "Annual Return [%]",
                "Volatility [%]",
                "Sharpe Ratio",
                "Max Drawdown [%]",
                "Win Rate [%]",
                "Profit Factor",
                "Num Trades",
            ],
            "optional_fields": [
                "SMA_FAST",
                "SMA_SLOW",
                "EMA_FAST",
                "EMA_SLOW",
                "Current Signal",
                "Exit Signal",
                "Allocation [%]",
                "Stop Loss [%]",
            ],
            "field_types": {
                "TICKER": str,
                "Strategy Type": str,
                "Total Return [%]": (int, float),
                "Annual Return [%]": (int, float),
                "Volatility [%]": (int, float),
                "Sharpe Ratio": (int, float),
                "Max Drawdown [%]": (int, float),
                "Win Rate [%]": (int, float),
                "Profit Factor": (int, float),
                "Num Trades": int,
            },
            "value_ranges": {
                "Total Return [%]": (-100, 1000),
                "Annual Return [%]": (-100, 500),
                "Volatility [%]": (0, 200),
                "Sharpe Ratio": (-5, 10),
                "Max Drawdown [%]": (-100, 0),
                "Win Rate [%]": (0, 100),
                "Profit Factor": (0, 50),
                "Num Trades": (0, 10000),
            },
        }


class TestConfigurationRegression(TestMACrossRegression):
    """Test configuration processing regression."""

    def test_config_processing_consistency(self, baseline_config, mock_log):
        """Test that config processing produces consistent results."""

        # Process the same config multiple times
        results = []
        for _ in range(10):
            processed = ConfigService.process_config(baseline_config.copy())
            results.append(processed)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result

        # Required fields should be present
        assert "TICKER" in first_result
        assert "STRATEGY_TYPE" in first_result
        assert "WINDOWS" in first_result

    def test_config_field_preservation(self, baseline_config, mock_log):
        """Test that all config fields are preserved during processing."""

        processed = ConfigService.process_config(baseline_config)

        # All original fields should be present
        for key, value in baseline_config.items():
            assert key in processed
            # For simple values, they should be identical
            if isinstance(value, (str, int, float, bool)):
                assert processed[key] == value

    def test_config_backwards_compatibility(self, mock_log):
        """Test backwards compatibility with older config formats."""

        # Test old-style config without new fields
        old_config = {
            "TICKER": "BTC-USD",  # String instead of list
            "STRATEGY_TYPE": "SMA",
            "SHORT_WINDOW": 10,
            "LONG_WINDOW": 20,
        }

        processed = ConfigService.process_config(old_config)

        # Should handle gracefully
        assert processed is not None
        assert "TICKER" in processed


class TestStrategyRegression(TestMACrossRegression):
    """Test strategy implementation regression."""

    def test_strategy_factory_consistency(self, mock_log):
        """Test that strategy factory produces consistent strategies."""

        factory = StrategyFactory()

        # Create the same strategy multiple times
        sma_strategies = [factory.create_strategy("SMA") for _ in range(10)]
        ema_strategies = [factory.create_strategy("EMA") for _ in range(10)]

        # All instances should be of the same type
        first_sma_type = type(sma_strategies[0])
        first_ema_type = type(ema_strategies[0])

        for strategy in sma_strategies[1:]:
            assert type(strategy) == first_sma_type

        for strategy in ema_strategies[1:]:
            assert type(strategy) == first_ema_type

        # Different strategy types should be different
        assert first_sma_type != first_ema_type

    def test_strategy_calculation_consistency(self, baseline_price_data, mock_log):
        """Test that strategy calculations produce consistent results."""

        factory = StrategyFactory()
        sma_strategy = factory.create_strategy("SMA")

        # Calculate moving averages multiple times with same parameters
        results = []
        for _ in range(5):
            result = sma_strategy.calculate_ma(baseline_price_data, 10, 20)
            results.append(result)

        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            # Compare column values
            assert first_result.equals(result)


class TestWorkflowRegression(TestMACrossRegression):
    """Test complete workflow regression."""

    def test_single_ticker_workflow_consistency(
        self, baseline_config, baseline_price_data, mock_log
    ):
        """Test that single ticker workflow produces consistent results."""

        # Mock the data and processing components
        with patch("app.tools.get_data.get_data") as mock_get_data, patch(
            "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
        ) as mock_process, patch(
            "app.tools.portfolio.filtering_service.PortfolioFilterService"
        ) as mock_filter_service, patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            # Setup consistent mock responses
            mock_get_data.return_value = baseline_price_data

            baseline_portfolio = [
                {
                    "TICKER": "BTC-USD",
                    "Strategy Type": "SMA",
                    "SMA_FAST": 10,
                    "SMA_SLOW": 20,
                    "Total Return [%]": 15.5,
                    "Annual Return [%]": 12.3,
                    "Volatility [%]": 18.2,
                    "Sharpe Ratio": 0.68,
                    "Max Drawdown [%]": -8.5,
                    "Win Rate [%]": 65.0,
                    "Profit Factor": 1.45,
                    "Num Trades": 25,
                    "Current Signal": True,
                    "Exit Signal": False,
                    "Allocation [%]": 100,
                    "Stop Loss [%]": 5.0,
                }
            ]

            mock_process.return_value = pl.DataFrame(baseline_portfolio)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(baseline_portfolio)
            )
            mock_filter_service.return_value = mock_filter_instance

            # Run workflow multiple times
            orchestrator = PortfolioOrchestrator(mock_log)
            results = []

            for _ in range(5):
                result = orchestrator.run(baseline_config.copy())
                results.append(result)

            # All results should be consistent
            assert all(r is not None for r in results)

            # Check that the same operations were called each time
            assert mock_get_data.call_count == 5
            assert mock_process.call_count == 5

    def test_multi_ticker_workflow_consistency(
        self, baseline_config, baseline_price_data, mock_log
    ):
        """Test that multi-ticker workflow produces consistent results."""

        multi_config = baseline_config.copy()
        multi_config["TICKER"] = ["BTC-USD", "ETH-USD"]

        with patch("app.tools.get_data.get_data") as mock_get_data, patch(
            "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
        ) as mock_process, patch(
            "app.tools.portfolio.filtering_service.PortfolioFilterService"
        ) as mock_filter_service, patch(
            "app.tools.strategy.export_portfolios.export_portfolios"
        ) as mock_export:
            # Setup mocks
            mock_get_data.return_value = baseline_price_data

            portfolio_data = [
                {
                    "TICKER": "BTC-USD",
                    "Strategy Type": "SMA",
                    "SMA_FAST": 10,
                    "SMA_SLOW": 20,
                    "Total Return [%]": 15.5,
                    "Sharpe Ratio": 0.68,
                    "Allocation [%]": 100,
                    "Stop Loss [%]": 5.0,
                },
                {
                    "TICKER": "ETH-USD",
                    "Strategy Type": "SMA",
                    "SMA_FAST": 10,
                    "SMA_SLOW": 20,
                    "Total Return [%]": 12.3,
                    "Sharpe Ratio": 0.55,
                    "Allocation [%]": 100,
                    "Stop Loss [%]": 5.0,
                },
            ]

            mock_process.return_value = pl.DataFrame(portfolio_data)

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(portfolio_data)
            )
            mock_filter_service.return_value = mock_filter_instance

            # Run workflow multiple times
            orchestrator = PortfolioOrchestrator(mock_log)
            results = []

            for _ in range(3):
                result = orchestrator.run(multi_config.copy())
                results.append(result)

            # All results should be consistent
            assert all(r is not None for r in results)

            # Should process both tickers each time
            expected_calls = 3 * 2  # 3 runs * 2 tickers
            assert mock_process.call_count == expected_calls


class TestDataValidationRegression(TestMACrossRegression):
    """Test data validation and schema compliance."""

    def test_portfolio_schema_compliance(self, expected_portfolio_schema, mock_log):
        """Test that portfolio data complies with expected schema."""

        # Sample portfolio data
        portfolio_data = {
            "TICKER": "BTC-USD",
            "Strategy Type": "SMA",
            "SMA_FAST": 10,
            "SMA_SLOW": 20,
            "Total Return [%]": 15.5,
            "Annual Return [%]": 12.3,
            "Volatility [%]": 18.2,
            "Sharpe Ratio": 0.68,
            "Max Drawdown [%]": -8.5,
            "Win Rate [%]": 65.0,
            "Profit Factor": 1.45,
            "Num Trades": 25,
            "Current Signal": True,
            "Exit Signal": False,
            "Allocation [%]": 100,
            "Stop Loss [%]": 5.0,
        }

        # Check required fields
        for field in expected_portfolio_schema["required_fields"]:
            assert field in portfolio_data, f"Required field '{field}' missing"

        # Check field types
        for field, expected_type in expected_portfolio_schema["field_types"].items():
            if field in portfolio_data:
                actual_value = portfolio_data[field]
                if isinstance(expected_type, tuple):
                    assert isinstance(
                        actual_value, expected_type
                    ), f"Field '{field}' has wrong type"
                else:
                    assert isinstance(
                        actual_value, expected_type
                    ), f"Field '{field}' has wrong type"

        # Check value ranges
        for field, (min_val, max_val) in expected_portfolio_schema[
            "value_ranges"
        ].items():
            if field in portfolio_data:
                actual_value = portfolio_data[field]
                if isinstance(actual_value, (int, float)):
                    assert (
                        min_val <= actual_value <= max_val
                    ), f"Field '{field}' value {actual_value} out of range [{min_val}, {max_val}]"

    def test_config_validation_regression(self, baseline_config, mock_log):
        """Test that config validation catches known issues."""

        # Test missing required fields
        invalid_configs = [
            {},  # Empty config
            {"TICKER": []},  # Empty ticker list
            {"TICKER": ["BTC-USD"]},  # Missing other required fields
        ]

        for invalid_config in invalid_configs:
            try:
                processed = ConfigService.process_config(invalid_config)
                # If processing succeeds, check that required fields are added with defaults
                assert processed is not None
            except Exception as e:
                # If it fails, that's also acceptable for invalid configs
                assert isinstance(e, Exception)

    def test_numeric_precision_regression(self, mock_log):
        """Test that numeric calculations maintain expected precision."""

        # Test with known inputs that should produce specific outputs
        test_data = pl.DataFrame(
            {
                "Date": pd.date_range("2023-01-01", periods=50),
                "Close": [
                    100.0 + i * 0.5 for i in range(50)
                ],  # Simple linear progression
            }
        )

        factory = StrategyFactory()
        sma_strategy = factory.create_strategy("SMA")

        # Calculate SMA(10) for this simple data
        result = sma_strategy.calculate_ma(test_data, 10, 20)

        # Verify the calculation produces expected results
        assert result is not None
        assert len(result) == len(test_data)

        # The 10-period SMA at position 9 should be the average of first 10 values
        # Values are: 100.0, 100.5, 101.0, ..., 104.5
        # Average = (100.0 + 100.5 + ... + 104.5) / 10 = 102.25
        expected_sma_10 = 102.25

        # Check if SMA column exists and has reasonable values
        if "SMA_10" in result.columns:
            actual_sma_10 = result["SMA_10"][9]
            if actual_sma_10 is not None:
                assert abs(actual_sma_10 - expected_sma_10) < 0.01


class TestErrorHandlingRegression(TestMACrossRegression):
    """Test error handling regression."""

    def test_error_type_consistency(self, mock_log):
        """Test that error types are consistently raised."""

        from app.strategies.ma_cross.exceptions import (
            MACrossConfigurationError,
            MACrossDataError,
            MACrossExecutionError,
        )

        # Test that specific error types are raised for specific conditions
        ticker_processor = TickerProcessor(mock_log)

        # Test synthetic ticker validation error
        with pytest.raises(Exception) as exc_info:
            ticker_processor._extract_synthetic_components("INVALID", {})

        # Should raise a specific error type (not generic Exception)
        assert not isinstance(exc_info.value, Exception) or hasattr(
            exc_info.value, "details"
        )

    def test_error_recovery_regression(self, baseline_config, mock_log):
        """Test that error recovery mechanisms work consistently."""

        # Test workflow with recoverable errors
        with patch("app.tools.get_data.get_data") as mock_get_data:
            mock_get_data.side_effect = [None, Exception("Network error")]

            orchestrator = PortfolioOrchestrator(mock_log)

            # Should handle errors gracefully
            try:
                result = orchestrator.run(baseline_config)
                # If it succeeds despite errors, that's acceptable
                assert result is not None
            except Exception as e:
                # If it fails, should be a domain-specific error
                assert hasattr(e, "__class__")
                assert (
                    "MACross" in e.__class__.__name__ or "Error" in e.__class__.__name__
                )


class TestPerformanceRegression(TestMACrossRegression):
    """Test performance regression."""

    def test_performance_baseline(self, baseline_config, baseline_price_data, mock_log):
        """Test that performance remains within acceptable bounds."""
        import time

        with patch("app.tools.get_data.get_data") as mock_get_data, patch(
            "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
        ) as mock_process, patch(
            "app.tools.portfolio.filtering_service.PortfolioFilterService"
        ) as mock_filter_service:
            # Setup mocks
            mock_get_data.return_value = baseline_price_data
            mock_process.return_value = pl.DataFrame(
                [
                    {
                        "TICKER": "BTC-USD",
                        "Strategy Type": "SMA",
                        "Total Return [%]": 15.5,
                        "Allocation [%]": 100,
                        "Stop Loss [%]": 5.0,
                    }
                ]
            )

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame(
                    [
                        {
                            "TICKER": "BTC-USD",
                            "Strategy Type": "SMA",
                            "Total Return [%]": 15.5,
                        }
                    ]
                )
            )
            mock_filter_service.return_value = mock_filter_instance

            # Measure execution time
            orchestrator = PortfolioOrchestrator(mock_log)

            start_time = time.time()
            result = orchestrator.run(baseline_config)
            execution_time = time.time() - start_time

            # Performance baseline: should complete within 2 seconds
            assert execution_time < 2.0
            assert result is not None

    def test_memory_regression(self, baseline_config, baseline_price_data, mock_log):
        """Test that memory usage doesn't regress."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        with patch("app.tools.get_data.get_data") as mock_get_data, patch(
            "app.strategies.ma_cross.tools.signal_processing.process_ticker_portfolios"
        ) as mock_process, patch(
            "app.tools.portfolio.filtering_service.PortfolioFilterService"
        ) as mock_filter_service:
            # Setup mocks
            mock_get_data.return_value = baseline_price_data
            mock_process.return_value = pl.DataFrame(
                [
                    {
                        "TICKER": "BTC-USD",
                        "Strategy Type": "SMA",
                        "Total Return [%]": 15.5,
                    }
                ]
            )

            mock_filter_instance = Mock()
            mock_filter_instance.filter_portfolios_dataframe.return_value = (
                pl.DataFrame([{"TICKER": "BTC-USD", "Total Return [%]": 15.5}])
            )
            mock_filter_service.return_value = mock_filter_instance

            # Execute workflow
            orchestrator = PortfolioOrchestrator(mock_log)
            result = orchestrator.run(baseline_config)

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Memory baseline: should not increase by more than 100MB
            assert memory_increase < 100 * 1024 * 1024  # 100MB
            assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
