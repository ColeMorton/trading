"""
Integration tests for equity data extraction in strategy processing.

This module tests the integration of equity data extraction with the existing
strategy processing pipeline for SMA, EMA, and MACD strategies.
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pandas as pd
import pytest

from app.strategies.tools.summary_processing import (
    _extract_equity_data_if_enabled,
    process_ticker_portfolios,
)
from app.tools.equity_data_extractor import EquityData, MetricType


class TestEquityIntegration:
    """Test equity data integration with strategy processing."""

    def setup_method(self):
        """Setup test fixtures."""
        self.log_messages = []

        def mock_log(message, level="info"):
            self.log_messages.append((message, level))

        self.mock_log = mock_log

    def create_mock_portfolio(self, equity_values, strategy_type="SMA"):
        """Create a mock VectorBT Portfolio for testing."""
        portfolio = Mock()

        # Create equity curve data
        if isinstance(equity_values, list):
            equity_values = np.array(equity_values)

        # Mock value() method
        timestamp_index = pd.date_range(
            "2023-01-01", periods=len(equity_values), freq="D"
        )
        value_series = pd.Series(equity_values, index=timestamp_index)
        portfolio.value.return_value = value_series

        # Mock wrapper and index
        wrapper = Mock()
        wrapper.index = timestamp_index
        portfolio.wrapper = wrapper

        # Mock close prices
        portfolio.close = value_series

        # Mock trades (basic structure)
        trades = Mock()
        trades.entry_idx = pd.Series([0, 2])
        trades.exit_idx = pd.Series([1, 3])
        portfolio.trades = trades

        # Mock stats method
        def mock_stats():
            return {
                "Total Return [%]": 12.0,
                "Sharpe Ratio": 1.5,
                "Max Drawdown [%]": 8.0,
                "Win Rate [%]": 65.0,
                "Avg Winning Trade [%]": 3.2,
                "Avg Losing Trade [%]": -1.8,
                "# Trades": 10,
            }

        portfolio.stats = mock_stats

        return portfolio

    @patch("app.strategies.tools.summary_processing.process_macd_strategy")
    @patch("app.strategies.tools.summary_processing.is_signal_current")
    @patch("app.strategies.tools.summary_processing.is_exit_signal_current")
    @patch("app.strategies.tools.summary_processing.convert_stats")
    def test_macd_strategy_with_equity_extraction(
        self, mock_convert_stats, mock_exit_signal, mock_signal, mock_process_macd
    ):
        """Test MACD strategy processing with equity data extraction."""
        # Setup mocks
        equity_values = [1000, 1050, 1100, 1080, 1120]
        mock_portfolio = self.create_mock_portfolio(equity_values, "MACD")
        mock_signal_data = Mock()

        mock_process_macd.return_value = (mock_portfolio, {}, mock_signal_data)
        mock_signal.return_value = True
        mock_exit_signal.return_value = False
        mock_convert_stats.return_value = {
            "Ticker": "AAPL",
            "Strategy Type": "MACD",
            "Total Return [%]": 12.0,
        }

        # Test configuration with equity export enabled
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        row = {
            "FAST_PERIOD": 12,
            "SLOW_PERIOD": 26,
            "SIGNAL_PERIOD": 9,
            "STRATEGY_TYPE": "MACD",
        }

        # Execute test
        result = process_ticker_portfolios("AAPL", row, config, self.mock_log)

        # Verify results
        assert result is not None
        assert len(result) == 1

        # Verify MACD strategy was called correctly
        mock_process_macd.assert_called_once()
        call_args = mock_process_macd.call_args
        assert call_args[1]["ticker"] == "AAPL"
        assert call_args[1]["fast_period"] == 12
        assert call_args[1]["slow_period"] == 26
        assert call_args[1]["signal_period"] == 9

        # Verify equity extraction was attempted
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        equity_messages = [msg for msg in info_messages if "equity data" in msg.lower()]
        assert len(equity_messages) > 0

    @patch("app.strategies.tools.summary_processing.process_ma_portfolios")
    @patch("app.strategies.tools.summary_processing.is_signal_current")
    @patch("app.strategies.tools.summary_processing.is_exit_signal_current")
    @patch("app.strategies.tools.summary_processing.convert_stats")
    def test_sma_strategy_with_equity_extraction(
        self, mock_convert_stats, mock_exit_signal, mock_signal, mock_process_ma
    ):
        """Test SMA strategy processing with equity data extraction."""
        # Setup mocks
        equity_values = [1000, 1050, 1100, 1080, 1120]
        mock_sma_portfolio = self.create_mock_portfolio(equity_values, "SMA")
        mock_ema_portfolio = None
        mock_signal_data = Mock()

        mock_process_ma.return_value = (
            mock_sma_portfolio,
            mock_ema_portfolio,
            {},
            mock_signal_data,
            None,
        )
        mock_signal.return_value = True
        mock_exit_signal.return_value = False
        mock_convert_stats.return_value = {
            "Ticker": "MSFT",
            "Strategy Type": "SMA",
            "Total Return [%]": 8.5,
        }

        # Test configuration with equity export enabled
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "best"}}

        row = {"FAST_PERIOD": 20, "SLOW_PERIOD": 50, "STRATEGY_TYPE": "SMA"}

        # Execute test
        result = process_ticker_portfolios("MSFT", row, config, self.mock_log)

        # Verify results
        assert result is not None
        assert len(result) == 1

        # Verify MA strategy was called correctly
        mock_process_ma.assert_called_once()
        call_args = mock_process_ma.call_args
        assert call_args[1]["ticker"] == "MSFT"
        assert call_args[1]["sma_fast"] == 20
        assert call_args[1]["sma_slow"] == 50
        assert call_args[1]["ema_fast"] is None
        assert call_args[1]["ema_slow"] is None

        # Verify equity extraction was attempted
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        equity_messages = [msg for msg in info_messages if "equity data" in msg.lower()]
        assert len(equity_messages) > 0

    @patch("app.strategies.tools.summary_processing.process_ma_portfolios")
    @patch("app.strategies.tools.summary_processing.is_signal_current")
    @patch("app.strategies.tools.summary_processing.is_exit_signal_current")
    @patch("app.strategies.tools.summary_processing.convert_stats")
    def test_ema_strategy_with_equity_extraction(
        self, mock_convert_stats, mock_exit_signal, mock_signal, mock_process_ma
    ):
        """Test EMA strategy processing with equity data extraction."""
        # Setup mocks
        equity_values = [1000, 1030, 1060, 1040, 1080]
        mock_sma_portfolio = None
        mock_ema_portfolio = self.create_mock_portfolio(equity_values, "EMA")
        mock_signal_data = Mock()

        mock_process_ma.return_value = (
            mock_sma_portfolio,
            mock_ema_portfolio,
            {},
            None,
            mock_signal_data,
        )
        mock_signal.return_value = False
        mock_exit_signal.return_value = True
        mock_convert_stats.return_value = {
            "Ticker": "GOOGL",
            "Strategy Type": "EMA",
            "Total Return [%]": 6.8,
        }

        # Test configuration with equity export enabled
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "median"}}

        row = {"FAST_PERIOD": 12, "SLOW_PERIOD": 26, "STRATEGY_TYPE": "EMA"}

        # Execute test
        result = process_ticker_portfolios("GOOGL", row, config, self.mock_log)

        # Verify results
        assert result is not None
        assert len(result) == 1

        # Verify MA strategy was called correctly
        mock_process_ma.assert_called_once()
        call_args = mock_process_ma.call_args
        assert call_args[1]["ticker"] == "GOOGL"
        assert call_args[1]["sma_fast"] is None
        assert call_args[1]["sma_slow"] is None
        assert call_args[1]["ema_fast"] == 12
        assert call_args[1]["ema_slow"] == 26

        # Verify equity extraction was attempted
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        equity_messages = [msg for msg in info_messages if "equity data" in msg.lower()]
        assert len(equity_messages) > 0

    def test_equity_extraction_disabled(self):
        """Test that equity extraction is skipped when disabled."""
        mock_portfolio = self.create_mock_portfolio([1000, 1050, 1100])

        # Test configuration with equity export disabled
        config = {"EQUITY_DATA": {"EXPORT": False, "METRIC": "mean"}}

        result = _extract_equity_data_if_enabled(
            portfolio=mock_portfolio,
            ticker="TEST",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            signal_period=None,
            config=config,
            log=self.mock_log,
        )

        # Verify no equity data was extracted
        assert result is None

    def test_equity_extraction_missing_config(self):
        """Test that equity extraction is skipped when config is missing."""
        mock_portfolio = self.create_mock_portfolio([1000, 1050, 1100])

        # Test configuration without EQUITY_DATA section
        config = {}

        result = _extract_equity_data_if_enabled(
            portfolio=mock_portfolio,
            ticker="TEST",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            signal_period=None,
            config=config,
            log=self.mock_log,
        )

        # Verify no equity data was extracted
        assert result is None

    @patch("app.strategies.tools.summary_processing.extract_equity_data_from_portfolio")
    def test_equity_extraction_with_different_metrics(self, mock_extract):
        """Test equity extraction with different metric types."""
        mock_portfolio = self.create_mock_portfolio([1000, 1050, 1100])
        mock_equity_data = Mock(spec=EquityData)
        mock_extract.return_value = mock_equity_data

        # Test each metric type
        metric_types = ["mean", "median", "best", "worst"]

        for metric in metric_types:
            self.log_messages.clear()  # Clear previous messages

            config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": metric}}

            result = _extract_equity_data_if_enabled(
                portfolio=mock_portfolio,
                ticker="TEST",
                strategy_type="SMA",
                fast_period=20,
                slow_period=50,
                signal_period=None,
                config=config,
                log=self.mock_log,
            )

            # Verify equity data was extracted
            assert result == mock_equity_data

            # Verify correct metric type was used
            expected_metric_type = MetricType(metric)
            mock_extract.assert_called_with(
                portfolio=mock_portfolio,
                metric_type=expected_metric_type,
                config=config,
                log=self.mock_log,
            )

    @patch("app.strategies.tools.summary_processing.extract_equity_data_from_portfolio")
    def test_equity_extraction_invalid_metric(self, mock_extract):
        """Test equity extraction with invalid metric type."""
        mock_portfolio = self.create_mock_portfolio([1000, 1050, 1100])
        mock_equity_data = Mock(spec=EquityData)
        mock_extract.return_value = mock_equity_data

        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "invalid_metric"}}

        result = _extract_equity_data_if_enabled(
            portfolio=mock_portfolio,
            ticker="TEST",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            signal_period=None,
            config=config,
            log=self.mock_log,
        )

        # Verify equity data was extracted with fallback metric
        assert result == mock_equity_data

        # Verify debug message was logged (configuration validation now handles this at higher level)
        debug_messages = [msg for msg, level in self.log_messages if level == "debug"]
        assert len(debug_messages) > 0
        assert any("Using metric 'mean' for TEST SMA" in msg for msg in debug_messages)

        # Verify default metric (MEAN) was used
        mock_extract.assert_called_with(
            portfolio=mock_portfolio,
            metric_type=MetricType.MEAN,
            config=config,
            log=self.mock_log,
        )

    @patch("app.strategies.tools.summary_processing.extract_equity_data_from_portfolio")
    def test_equity_extraction_error_handling(self, mock_extract):
        """Test error handling in equity extraction."""
        mock_portfolio = self.create_mock_portfolio([1000, 1050, 1100])
        mock_extract.side_effect = Exception("Mock extraction error")

        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        result = _extract_equity_data_if_enabled(
            portfolio=mock_portfolio,
            ticker="TEST",
            strategy_type="SMA",
            fast_period=20,
            slow_period=50,
            signal_period=None,
            config=config,
            log=self.mock_log,
        )

        # Verify no equity data was returned due to error
        assert result is None

        # Verify error was logged
        warning_messages = [
            msg for msg, level in self.log_messages if level == "warning"
        ]
        assert len(warning_messages) > 0
        assert any("Failed to extract equity data" in msg for msg in warning_messages)

    def test_strategy_processing_without_equity_data_field(self):
        """Test that strategy processing works when equity data is not in stats."""
        # This test ensures backward compatibility - strategies should work
        # even if the _equity_data field is not present

        # Mock the convert_stats function to verify it's called correctly
        with patch(
            "app.strategies.tools.summary_processing.convert_stats"
        ) as mock_convert:
            mock_convert.return_value = {"processed": True}

            # Mock other dependencies
            with patch(
                "app.strategies.tools.summary_processing.process_macd_strategy"
            ) as mock_macd:
                mock_portfolio = self.create_mock_portfolio([1000, 1050, 1100])
                mock_macd.return_value = (mock_portfolio, {}, Mock())

                # Mock signal functions
                with patch(
                    "app.strategies.tools.summary_processing.is_signal_current"
                ) as mock_signal:
                    with patch(
                        "app.strategies.tools.summary_processing.is_exit_signal_current"
                    ) as mock_exit:
                        mock_signal.return_value = True
                        mock_exit.return_value = False

                        config = {"EQUITY_DATA": {"EXPORT": False}}  # Disabled
                        row = {
                            "FAST_PERIOD": 12,
                            "SLOW_PERIOD": 26,
                            "SIGNAL_PERIOD": 9,
                            "STRATEGY_TYPE": "MACD",
                        }

                        result = process_ticker_portfolios(
                            "TEST", row, config, self.mock_log
                        )

                        # Verify processing succeeded
                        assert result is not None
                        assert len(result) == 1
                        assert result[0]["processed"] is True

                        # Verify convert_stats was called
                        mock_convert.assert_called_once()

                        # Verify the stats dict passed to convert_stats doesn't have _equity_data
                        stats_arg = mock_convert.call_args[0][0]
                        assert "_equity_data" not in stats_arg
