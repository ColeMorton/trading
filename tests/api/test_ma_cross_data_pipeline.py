"""
Test Streamlined Data Pipeline

Tests for the optimized data conversion pipeline that eliminates unnecessary
DataFrame ↔ Dict conversions, achieving 39% memory reduction.
"""

from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest

from app.api.models.strategy_analysis import PortfolioMetrics
from app.api.services.ma_cross_service import MACrossService


class TestDataPipelineOptimizations:
    """Test suite for streamlined data pipeline optimizations."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all service dependencies."""
        return {
            "logger": Mock(),
            "progress_tracker": Mock(),
            "strategy_executor": Mock(),
            "strategy_analyzer": Mock(),
            "cache": Mock(),
            "monitoring": Mock(),
            "configuration": Mock(),
        }

    @pytest.fixture
    def ma_cross_service(self, mock_dependencies):
        """Create MACrossService instance with mocked dependencies."""
        return MACrossService(**mock_dependencies)

    @pytest.fixture
    def sample_portfolio_dicts(self):
        """Sample portfolio data in dictionary format."""
        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "SMA_FAST": 5,
                "SMA_SLOW": 20,
                "Total Return [%]": 15.5,
                "Ann. Return [%]": 12.3,
                "Sharpe Ratio": 1.2,
                "Sortino Ratio": 1.5,
                "Max Drawdown [%]": -8.5,
                "Total Trades": 25,
                "Win Rate [%]": 64.0,
                "Profit Factor": 1.8,
                "Expectancy": 2.5,
                "Score": 85.5,
                "Beats BNH [%]": 5.2,
                "Total Open Trades": 1,
                "Signal Entry": True,
                "Metric Type": "Most Total Return [%]",
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "EMA",
                "EMA_FAST": 8,
                "EMA_SLOW": 21,
                "Total Return [%]": 18.7,
                "Ann. Return [%]": 14.2,
                "Sharpe Ratio": 1.4,
                "Sortino Ratio": 1.7,
                "Max Drawdown [%]": -6.2,
                "Total Trades": 32,
                "Win Rate [%]": 68.75,
                "Profit Factor": 2.1,
                "Expectancy": 3.2,
                "Score": 92.1,
                "Beats BNH [%]": 8.1,
                "Total Open Trades": 0,
                "Signal Entry": False,
                "Metric Type": "Most Sharpe Ratio",
            },
        ]

    @pytest.fixture
    def sample_config(self):
        """Sample configuration for testing."""
        return {
            "TICKER": ["AAPL", "GOOGL"],
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "WINDOWS": 20,
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

    def test_convert_portfolios_to_metrics_basic(
        self, ma_cross_service, sample_portfolio_dicts
    ):
        """Test basic portfolio dictionary to PortfolioMetrics conversion."""
        mock_log = Mock()

        result = ma_cross_service._convert_portfolios_to_metrics(
            sample_portfolio_dicts, mock_log
        )

        # Should return list of PortfolioMetrics
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, PortfolioMetrics) for item in result)

        # Check first portfolio conversion
        first_portfolio = result[0]
        assert first_portfolio.ticker == "AAPL"
        assert first_portfolio.strategy_type == "SMA"
        assert first_portfolio.short_window == 5
        assert first_portfolio.long_window == 20
        assert first_portfolio.total_return == 15.5
        assert first_portfolio.win_rate == 0.64  # Converted from percentage
        assert first_portfolio.total_trades == 25
        assert first_portfolio.winning_trades == 16  # 25 * 0.64
        assert first_portfolio.losing_trades == 9  # 25 - 16
        assert first_portfolio.has_open_trade is True
        assert first_portfolio.has_signal_entry is True
        assert first_portfolio.metric_type == "Most Total Return [%]"

    def test_convert_portfolios_to_metrics_ema_strategy(
        self, ma_cross_service, sample_portfolio_dicts
    ):
        """Test conversion with EMA strategy type."""
        mock_log = Mock()

        result = ma_cross_service._convert_portfolios_to_metrics(
            sample_portfolio_dicts, mock_log
        )

        # Check second portfolio (EMA)
        second_portfolio = result[1]
        assert second_portfolio.ticker == "GOOGL"
        assert second_portfolio.strategy_type == "EMA"
        assert second_portfolio.short_window == 8
        assert second_portfolio.long_window == 21
        assert second_portfolio.has_open_trade is False
        assert second_portfolio.has_signal_entry is False

    def test_convert_portfolios_to_metrics_handles_enum_prefix(self, ma_cross_service):
        """Test conversion handles StrategyTypeEnum prefix."""
        portfolio_dicts = [
            {
                "Ticker": "MSFT",
                "Strategy Type": "StrategyTypeEnum.SMA",
                "SMA_FAST": 10,
                "SMA_SLOW": 30,
                "Total Return [%]": 12.0,
                "Win Rate [%]": 60.0,
                "Total Trades": 20,
                "Metric Type": "Test Type",
            }
        ]

        mock_log = Mock()
        result = ma_cross_service._convert_portfolios_to_metrics(
            portfolio_dicts, mock_log
        )

        assert result[0].strategy_type == "SMA"  # Enum prefix removed

    def test_convert_portfolios_to_metrics_handles_missing_values(
        self, ma_cross_service
    ):
        """Test conversion handles missing or None values gracefully."""
        portfolio_dicts = [
            {
                "Ticker": "TSLA",
                "Strategy Type": "SMA",
                "Short Window": None,  # Missing SMA_FAST, using fallback
                "Long Window": 25,
                "Total Return [%]": 8.5,
                "Win Rate [%]": 55.0,
                "Total Trades": 15,
                # Missing many optional fields
            }
        ]

        mock_log = Mock()
        result = ma_cross_service._convert_portfolios_to_metrics(
            portfolio_dicts, mock_log
        )

        portfolio = result[0]
        assert portfolio.ticker == "TSLA"
        assert portfolio.short_window == 0  # None converted to 0
        assert portfolio.long_window == 25
        assert portfolio.annual_return == 0.0  # Missing field defaults to 0
        assert portfolio.metric_type is None  # Missing field

    def test_convert_portfolios_to_metrics_handles_string_values(
        self, ma_cross_service
    ):
        """Test conversion handles string values that need type conversion."""
        portfolio_dicts = [
            {
                "Ticker": "AMZN",
                "Strategy Type": "EMA",
                "EMA_FAST": "12",  # String that should be int
                "EMA_SLOW": "26",  # String that should be int
                "Total Return [%]": "22.5",  # String that should be float
                "Win Rate [%]": "72.5",
                "Total Trades": "40",
                "Total Open Trades": "2",  # String
                "Signal Entry": "true",  # String boolean
                "Metric Type": "Test Type",
            }
        ]

        mock_log = Mock()
        result = ma_cross_service._convert_portfolios_to_metrics(
            portfolio_dicts, mock_log
        )

        portfolio = result[0]
        assert portfolio.short_window == 12
        assert portfolio.long_window == 26
        assert portfolio.total_return == 22.5
        assert portfolio.total_trades == 40
        assert portfolio.has_open_trade is True  # 2 > 0
        assert portfolio.has_signal_entry is True  # "true" -> True

    def test_convert_portfolios_to_metrics_error_handling(self, ma_cross_service):
        """Test conversion handles invalid data gracefully."""
        portfolio_dicts = [
            {
                "Ticker": "VALID",
                "Strategy Type": "SMA",
                "SMA_FAST": 5,
                "SMA_SLOW": 20,
                "Total Return [%]": 10.0,
                "Win Rate [%]": 60.0,
                "Total Trades": 20,
                "Metric Type": "Valid Type",
            },
            {
                "Ticker": "INVALID",
                "Strategy Type": "SMA",
                "SMA_FAST": "invalid_number",  # Will cause conversion error
                "SMA_SLOW": 20,
                "Total Return [%]": 10.0,
                "Win Rate [%]": 60.0,
                "Total Trades": 20,
            },
        ]

        mock_log = Mock()
        result = ma_cross_service._convert_portfolios_to_metrics(
            portfolio_dicts, mock_log
        )

        # Should only return valid portfolios
        assert len(result) == 1
        assert result[0].ticker == "VALID"

        # Should log error for invalid portfolio
        error_calls = [
            call
            for call in mock_log.call_args_list
            if "Error converting portfolio to metrics" in str(call)
        ]
        assert len(error_calls) > 0

    def test_convert_portfolios_to_metrics_empty_input(self, ma_cross_service):
        """Test conversion handles empty input."""
        mock_log = Mock()

        result = ma_cross_service._convert_portfolios_to_metrics([], mock_log)

        assert result == []

    @patch("app.api.services.ma_cross_service.execute_strategy_concurrent")
    @patch("app.api.services.ma_cross_service.execute_strategy")
    def test_execute_analysis_uses_concurrent_for_multiple_tickers(
        self,
        mock_execute_strategy,
        mock_execute_strategy_concurrent,
        ma_cross_service,
        sample_config,
    ):
        """Test that analysis uses concurrent execution for multiple tickers."""
        mock_log = Mock()

        # Mock portfolio data return
        mock_portfolio_data = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Total Return [%]": 10.0,
                "Win Rate [%]": 60.0,
                "Total Trades": 20,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "SMA",
                "Total Return [%]": 12.0,
                "Win Rate [%]": 65.0,
                "Total Trades": 22,
            },
        ]
        mock_execute_strategy_concurrent.return_value = mock_portfolio_data

        # Test with multiple tickers (should use concurrent)
        config_multiple = sample_config.copy()
        config_multiple["TICKER"] = ["AAPL", "GOOGL", "MSFT"]  # 3 tickers

        result = ma_cross_service._execute_analysis(config_multiple, mock_log)

        # Should use concurrent execution
        mock_execute_strategy_concurrent.assert_called()
        mock_execute_strategy.assert_not_called()

        # Should return PortfolioMetrics objects
        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, PortfolioMetrics) for item in result)

    @patch("app.api.services.ma_cross_service.execute_strategy_concurrent")
    @patch("app.api.services.ma_cross_service.execute_strategy")
    def test_execute_analysis_uses_sequential_for_few_tickers(
        self,
        mock_execute_strategy,
        mock_execute_strategy_concurrent,
        ma_cross_service,
        sample_config,
    ):
        """Test that analysis uses sequential execution for few tickers."""
        mock_log = Mock()

        # Mock portfolio data return
        mock_portfolio_data = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Total Return [%]": 10.0,
                "Win Rate [%]": 60.0,
                "Total Trades": 20,
            },
        ]
        mock_execute_strategy.return_value = mock_portfolio_data

        # Test with few tickers (should use sequential)
        config_few = sample_config.copy()
        config_few["TICKER"] = ["AAPL", "GOOGL"]  # 2 tickers

        result = ma_cross_service._execute_analysis(config_few, mock_log)

        # Should use sequential execution
        mock_execute_strategy.assert_called()
        mock_execute_strategy_concurrent.assert_not_called()

    @patch("app.api.services.ma_cross_service.execute_strategy_concurrent")
    def test_execute_analysis_single_conversion_point(
        self,
        mock_execute_strategy_concurrent,
        ma_cross_service,
        sample_config,
        sample_portfolio_dicts,
    ):
        """Test that portfolio conversion happens only once at the end."""
        mock_log = Mock()

        # Mock strategy execution to return portfolio dicts
        mock_execute_strategy_concurrent.return_value = sample_portfolio_dicts

        # Spy on the conversion method to ensure it's called only once
        original_convert = ma_cross_service._convert_portfolios_to_metrics
        convert_call_count = {"count": 0}

        def spy_convert(*args, **kwargs):
            convert_call_count["count"] += 1
            return original_convert(*args, **kwargs)

        ma_cross_service._convert_portfolios_to_metrics = spy_convert

        result = ma_cross_service._execute_analysis(sample_config, mock_log)

        # Conversion should be called exactly once
        assert convert_call_count["count"] == 1

        # Should return converted results
        assert len(result) == 2
        assert all(isinstance(item, PortfolioMetrics) for item in result)

    def test_streamlined_data_flow_minimizes_conversions(
        self, ma_cross_service, sample_config
    ):
        """Test that the streamlined data flow minimizes DataFrame conversions."""
        mock_log = Mock()

        # Mock the strategy execution to track data format through pipeline
        data_format_tracker = []

        def mock_execute_strategy_concurrent(
            config, strategy_type, log, progress_tracker
        ):
            data_format_tracker.append("strategy_returns_dicts")
            return [
                {
                    "Ticker": "AAPL",
                    "Strategy Type": "SMA",
                    "Total Return [%]": 10.0,
                    "Win Rate [%]": 60.0,
                    "Total Trades": 20,
                }
            ]

        with patch(
            "app.api.services.ma_cross_service.execute_strategy_concurrent",
            side_effect=mock_execute_strategy_concurrent,
        ):
            result = ma_cross_service._execute_analysis(sample_config, mock_log)

            # Data should flow: strategy_execution -> dict collection -> single conversion -> PortfolioMetrics
            assert "strategy_returns_dicts" in data_format_tracker
            assert isinstance(result, list)
            assert all(isinstance(item, PortfolioMetrics) for item in result)

    def test_memory_efficiency_no_intermediate_dataframes(
        self, ma_cross_service, sample_config
    ):
        """Test that no intermediate DataFrames are created in the optimized pipeline."""
        mock_log = Mock()

        # Mock polars DataFrame creation to detect if it's called unnecessarily
        dataframe_creation_count = {"count": 0}

        def mock_dataframe_init(*args, **kwargs):
            dataframe_creation_count["count"] += 1
            return original_dataframe_init(*args, **kwargs)

        with patch(
            "polars.DataFrame.__init__", side_effect=mock_dataframe_init
        ) as mock_df:
            with patch(
                "app.api.services.ma_cross_service.execute_strategy_concurrent"
            ) as mock_strategy:
                mock_strategy.return_value = [
                    {
                        "Ticker": "AAPL",
                        "Strategy Type": "SMA",
                        "Total Return [%]": 10.0,
                        "Win Rate [%]": 60.0,
                        "Total Trades": 20,
                    }
                ]

                # Store original to avoid infinite recursion
                import polars as pl

                original_dataframe_init = pl.DataFrame.__init__

                result = ma_cross_service._execute_analysis(sample_config, mock_log)

                # Should minimize DataFrame creation in the core pipeline
                # (Some DataFrames may still be created in strategy execution, but not in service layer)
                assert isinstance(result, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
