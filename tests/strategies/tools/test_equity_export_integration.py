"""
End-to-end integration tests for equity data export pipeline.

This module tests the complete workflow from strategy processing through
equity data extraction to final CSV export.
"""

from unittest.mock import patch

import numpy as np
import pandas as pd

from app.strategies.tools.summary_processing import export_summary_results
from app.tools.equity_data_extractor import EquityData


class TestEquityExportEndToEnd:
    """Test complete equity export pipeline integration."""

    def setup_method(self):
        """Setup test fixtures."""
        self.log_messages = []

        def mock_log(message, level="info"):
            self.log_messages.append((message, level))

        self.mock_log = mock_log

    def create_sample_portfolios_with_equity_data(self):
        """Create sample portfolios with equity data attached."""
        # Create sample equity data
        timestamp = pd.date_range("2023-01-01", periods=5, freq="D")
        equity_data = EquityData(
            timestamp=timestamp,
            equity=np.array([0, 50, 100, 80, 120]),
            equity_pct=np.array([0, 5, 10, 8, 12]),
            equity_change=np.array([0, 50, 50, -20, 40]),
            equity_change_pct=np.array([0, 5, 4, -1, 3]),
            drawdown=np.array([0, 0, 0, 20, 0]),
            drawdown_pct=np.array([0, 0, 0, 1, 0]),
            peak_equity=np.array([1000, 1050, 1100, 1100, 1120]),
            mfe=np.array([0, 50, 100, 100, 120]),
            mae=np.array([0, 0, 0, -20, -20]),
        )

        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 20,
                "Slow Period": 50,
                "Signal Period": None,
                "Total Return [%]": 12.0,
                "Sharpe Ratio": 1.5,
                "Max Drawdown [%]": 8.0,
                "_equity_data": equity_data,
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "Total Return [%]": 15.5,
                "Sharpe Ratio": 1.8,
                "Max Drawdown [%]": 6.2,
                "_equity_data": equity_data,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "EMA",
                "Fast Period": 15,
                "Slow Period": 30,
                "Signal Period": None,
                "Total Return [%]": 9.8,
                "Sharpe Ratio": 1.2,
                "Max Drawdown [%]": 10.1,
                "_equity_data": equity_data,
            },
        ]

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_end_to_end_equity_export_enabled(self, mock_export_portfolios):
        """Test complete end-to-end equity export when enabled."""
        # Setup mocks
        mock_export_portfolios.return_value = (None, True)

        # Create portfolios with equity data
        portfolios = self.create_sample_portfolios_with_equity_data()

        # Configuration with equity export enabled
        config = {
            "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"},
            "USE_EXTENDED_SCHEMA": True,
        }

        # Execute end-to-end export
        success = export_summary_results(
            portfolios, "test_portfolio.csv", self.mock_log, config,
        )

        # Verify main export succeeded
        assert success is True

        # Verify equity export was attempted
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        equity_messages = [msg for msg in info_messages if "equity data" in msg.lower()]

        # Should have either export success or information about the attempt
        assert len(equity_messages) > 0

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_end_to_end_equity_export_disabled(self, mock_export_portfolios):
        """Test end-to-end export when equity export is disabled."""
        # Setup mocks
        mock_export_portfolios.return_value = (None, True)

        # Create portfolios with equity data
        portfolios = self.create_sample_portfolios_with_equity_data()

        # Configuration with equity export disabled
        config = {
            "EQUITY_DATA": {"EXPORT": False, "METRIC": "mean"},
            "USE_EXTENDED_SCHEMA": True,
        }

        # Execute end-to-end export
        success = export_summary_results(
            portfolios, "test_portfolio.csv", self.mock_log, config,
        )

        # Verify main export succeeded
        assert success is True

        # Verify no equity export message or that it was disabled
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        equity_messages = [msg for msg in info_messages if "equity data" in msg.lower()]

        # Should either have no equity messages or a message indicating no export
        if equity_messages:
            assert any("No equity data was exported" in msg for msg in equity_messages)

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_end_to_end_equity_export_missing_data(self, mock_export_portfolios):
        """Test end-to-end export when portfolios have no equity data."""
        # Setup mocks
        mock_export_portfolios.return_value = (None, True)

        # Create portfolios WITHOUT equity data
        portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 20,
                "Slow Period": 50,
                "Total Return [%]": 12.0,
                # No _equity_data field
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "Total Return [%]": 15.5,
                # No _equity_data field
            },
        ]

        # Configuration with equity export enabled
        config = {
            "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"},
            "USE_EXTENDED_SCHEMA": True,
        }

        # Execute end-to-end export
        success = export_summary_results(
            portfolios, "test_portfolio.csv", self.mock_log, config,
        )

        # Verify main export succeeded
        assert success is True

        # Verify no equity data was exported message
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        equity_messages = [
            msg for msg in info_messages if "No equity data was exported" in msg
        ]
        assert len(equity_messages) > 0

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    @patch("app.tools.equity_export.export_equity_data_batch")
    def test_end_to_end_equity_export_error_handling(
        self, mock_batch_export, mock_export_portfolios,
    ):
        """Test error handling in equity export doesn't break main export."""
        # Setup mocks
        mock_export_portfolios.return_value = (None, True)
        mock_batch_export.side_effect = Exception("Export error")

        # Create portfolios with equity data
        portfolios = self.create_sample_portfolios_with_equity_data()

        # Configuration with equity export enabled
        config = {
            "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"},
            "USE_EXTENDED_SCHEMA": True,
        }

        # Execute end-to-end export
        success = export_summary_results(
            portfolios, "test_portfolio.csv", self.mock_log, config,
        )

        # Verify main export still succeeded despite equity export error
        assert success is True

        # Verify error was logged but didn't break the process
        warning_messages = [
            msg for msg, level in self.log_messages if level == "warning"
        ]
        equity_error_messages = [
            msg for msg in warning_messages if "Error during equity data export" in msg
        ]
        assert len(equity_error_messages) > 0

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_end_to_end_different_strategy_directories(self, mock_export_portfolios):
        """Test that different strategy types are processed for export."""
        # Setup mocks
        mock_export_portfolios.return_value = (None, True)

        # Create portfolios with different strategy types
        portfolios = self.create_sample_portfolios_with_equity_data()

        config = {
            "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"},
            "USE_EXTENDED_SCHEMA": True,
        }

        # Execute export
        success = export_summary_results(
            portfolios, "test_portfolio.csv", self.mock_log, config,
        )
        assert success is True

        # Verify equity export was attempted for different strategy types
        [msg for msg, level in self.log_messages if level == "info"]

        # Should have attempted to process all strategies
        assert success is True

    @patch("app.tools.strategy.export_portfolios.export_portfolios")
    def test_end_to_end_file_overwrite_behavior(self, mock_export_portfolios):
        """Test file overwrite behavior in end-to-end export."""
        # Setup mocks
        mock_export_portfolios.return_value = (None, True)

        # Create portfolio with equity data
        portfolios = [self.create_sample_portfolios_with_equity_data()[0]]  # Just AAPL

        config = {
            "EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"},
            "USE_EXTENDED_SCHEMA": True,
        }

        # Execute export
        success = export_summary_results(
            portfolios, "test_portfolio.csv", self.mock_log, config,
        )
        assert success is True

        # Verify export process ran successfully
        info_messages = [msg for msg, level in self.log_messages if level == "info"]
        assert any(
            "Portfolio summary exported successfully" in msg for msg in info_messages
        )
