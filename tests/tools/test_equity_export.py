"""
Unit and integration tests for equity data export functionality.

This module tests the complete equity data export pipeline including
file naming, directory creation, CSV export, and batch processing.
"""

import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from app.tools.equity_data_extractor import EquityData
from app.tools.equity_export import (
    cleanup_old_equity_files,
    ensure_export_directory_exists,
    export_equity_data_batch,
    export_equity_data_to_csv,
    generate_equity_filename,
    get_equity_export_directory,
    get_equity_export_file_path,
    validate_equity_export_requirements,
)
from app.tools.exceptions import TradingSystemError


class TestEquityExportFilenames:
    """Test filename generation functionality."""

    def test_generate_equity_filename_sma(self):
        """Test filename generation for SMA strategy."""
        filename = generate_equity_filename("AAPL", "SMA", 20, 50)
        assert filename == "AAPL_SMA_20_50_0.csv"

    def test_generate_equity_filename_ema(self):
        """Test filename generation for EMA strategy."""
        filename = generate_equity_filename("MSFT", "EMA", 12, 26)
        assert filename == "MSFT_EMA_12_26_0.csv"

    def test_generate_equity_filename_macd(self):
        """Test filename generation for MACD strategy."""
        filename = generate_equity_filename("GOOGL", "MACD", 12, 26, 9)
        assert filename == "GOOGL_MACD_12_26_9.csv"

    def test_generate_equity_filename_special_characters(self):
        """Test filename generation with special characters in ticker."""
        filename = generate_equity_filename("BTC-USD", "SMA", 20, 50)
        assert filename == "BTC-USD_SMA_20_50_0.csv"

        filename = generate_equity_filename("EUR/USD", "EMA", 10, 20)
        assert filename == "EUR-USD_EMA_10_20_0.csv"

    def test_generate_equity_filename_signal_window_none(self):
        """Test filename generation with None signal period."""
        filename = generate_equity_filename("TESLA", "SMA", 15, 30, None)
        assert filename == "TESLA_SMA_15_30_0.csv"


class TestEquityExportDirectories:
    """Test directory handling functionality."""

    @patch("app.tools.equity_export.get_project_root")
    def test_get_equity_export_directory_sma(self, mock_project_root):
        """Test export directory for SMA strategy."""
        mock_project_root.return_value = Path("/test/project")

        export_dir = get_equity_export_directory("SMA")
        expected = Path("/test/project/data/raw/equity")
        assert export_dir == expected

    @patch("app.tools.equity_export.get_project_root")
    def test_get_equity_export_directory_ema(self, mock_project_root):
        """Test export directory for EMA strategy."""
        mock_project_root.return_value = Path("/test/project")

        export_dir = get_equity_export_directory("EMA")
        expected = Path("/test/project/data/raw/equity")
        assert export_dir == expected

    @patch("app.tools.equity_export.get_project_root")
    def test_get_equity_export_directory_macd(self, mock_project_root):
        """Test export directory for MACD strategy."""
        mock_project_root.return_value = Path("/test/project")

        export_dir = get_equity_export_directory("MACD")
        expected = Path("/test/project/data/raw/equity")
        assert export_dir == expected

    def test_get_equity_export_directory_invalid_strategy(self):
        """Test error handling for invalid strategy type."""
        with pytest.raises(TradingSystemError) as exc_info:
            get_equity_export_directory("INVALID")

        assert "Invalid strategy type" in str(exc_info.value)

    def test_ensure_export_directory_exists_new_directory(self):
        """Test creation of new export directory."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir) / "new_directory"

            ensure_export_directory_exists(export_dir, mock_log)

            assert export_dir.exists()
            assert export_dir.is_dir()

            # Check debug log was created
            debug_messages = [msg for msg, level in log_messages if level == "debug"]
            assert len(debug_messages) > 0

    def test_ensure_export_directory_exists_existing_directory(self):
        """Test handling of existing export directory."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir)  # Directory already exists

            ensure_export_directory_exists(export_dir, mock_log)

            assert export_dir.exists()
            assert export_dir.is_dir()


class TestEquityDataExport:
    """Test equity data CSV export functionality."""

    def create_sample_equity_data(self):
        """Create sample equity data for testing."""
        timestamp = pd.date_range("2023-01-01", periods=5, freq="D")
        return EquityData(
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

    @patch("app.tools.equity_export.get_equity_export_directory")
    def test_export_equity_data_to_csv_success(self, mock_get_dir):
        """Test successful equity data export to CSV."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        equity_data = self.create_sample_equity_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir)
            mock_get_dir.return_value = export_dir

            success = export_equity_data_to_csv(
                equity_data=equity_data,
                ticker="AAPL",
                strategy_type="SMA",
                fast_period=20,
                slow_period=50,
                signal_period=None,
                log=mock_log,
                overwrite=True,
            )

            assert success is True

            # Check file was created
            expected_file = export_dir / "AAPL_SMA_20_50_0.csv"
            assert expected_file.exists()

            # Check file contents
            df = pd.read_csv(expected_file)
            assert len(df) == 5
            assert "timestamp" in df.columns
            assert "equity" in df.columns
            assert "equity_pct" in df.columns

            # Check success log message
            info_messages = [msg for msg, level in log_messages if level == "info"]
            assert any("Successfully exported" in msg for msg in info_messages)

    @patch("app.tools.equity_export.get_equity_export_directory")
    def test_export_equity_data_to_csv_empty_data(self, mock_get_dir):
        """Test handling of empty equity data."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        # Create empty equity data
        timestamp = pd.Index([])
        empty_equity_data = EquityData(
            timestamp=timestamp,
            equity=np.array([]),
            equity_pct=np.array([]),
            equity_change=np.array([]),
            equity_change_pct=np.array([]),
            drawdown=np.array([]),
            drawdown_pct=np.array([]),
            peak_equity=np.array([]),
            mfe=np.array([]),
            mae=np.array([]),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir)
            mock_get_dir.return_value = export_dir

            success = export_equity_data_to_csv(
                equity_data=empty_equity_data,
                ticker="EMPTY",
                strategy_type="SMA",
                fast_period=20,
                slow_period=50,
                signal_period=None,
                log=mock_log,
                overwrite=True,
            )

            assert success is False

            # Check warning was logged
            warning_messages = [
                msg for msg, level in log_messages if level == "warning"
            ]
            assert any("No equity data to export" in msg for msg in warning_messages)

    @patch("app.tools.equity_export.get_equity_export_directory")
    def test_export_equity_data_to_csv_overwrite_disabled(self, mock_get_dir):
        """Test export with overwrite disabled and existing file."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        equity_data = self.create_sample_equity_data()

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir)
            mock_get_dir.return_value = export_dir

            # Create existing file
            existing_file = export_dir / "TEST_SMA_20_50_0.csv"
            existing_file.touch()

            success = export_equity_data_to_csv(
                equity_data=equity_data,
                ticker="TEST",
                strategy_type="SMA",
                fast_period=20,
                slow_period=50,
                signal_period=None,
                log=mock_log,
                overwrite=False,
            )

            assert success is False

            # Check warning was logged
            warning_messages = [
                msg for msg, level in log_messages if level == "warning"
            ]
            assert any(
                "already exists and overwrite disabled" in msg
                for msg in warning_messages
            )


class TestEquityBatchExport:
    """Test batch export functionality."""

    def create_sample_portfolios(self):
        """Create sample portfolios for batch testing."""
        equity_data = EquityData(
            timestamp=pd.date_range("2023-01-01", periods=3, freq="D"),
            equity=np.array([0, 10, 20]),
            equity_pct=np.array([0, 1, 2]),
            equity_change=np.array([0, 10, 10]),
            equity_change_pct=np.array([0, 1, 1]),
            drawdown=np.array([0, 0, 0]),
            drawdown_pct=np.array([0, 0, 0]),
            peak_equity=np.array([1000, 1010, 1020]),
            mfe=np.array([0, 10, 20]),
            mae=np.array([0, 0, 0]),
        )

        return [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Fast Period": 20,
                "Slow Period": 50,
                "Signal Period": None,
                "_equity_data": equity_data,
            },
            {
                "Ticker": "MSFT",
                "Strategy Type": "MACD",
                "Fast Period": 12,
                "Slow Period": 26,
                "Signal Period": 9,
                "_equity_data": equity_data,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "EMA",
                "Fast Period": 15,
                "Slow Period": 30,
                "Signal Period": None,
                # No equity data for this one
            },
        ]

    @patch("app.tools.equity_export.export_equity_data_to_csv")
    def test_export_equity_data_batch_success(self, mock_export_csv):
        """Test successful batch export."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        mock_export_csv.return_value = True
        portfolios = self.create_sample_portfolios()

        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        results = export_equity_data_batch(portfolios, mock_log, config)

        assert results["total_portfolios"] == 3
        assert results["exported_count"] == 2  # Two portfolios have equity data
        assert results["skipped_count"] == 1  # One portfolio without equity data
        assert results["error_count"] == 0

        # Verify export_equity_data_to_csv was called twice
        assert mock_export_csv.call_count == 2

    def test_export_equity_data_batch_disabled(self):
        """Test batch export when feature is disabled."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        portfolios = self.create_sample_portfolios()

        config = {"EQUITY_DATA": {"EXPORT": False, "METRIC": "mean"}}

        results = export_equity_data_batch(portfolios, mock_log, config)

        assert results["total_portfolios"] == 3
        assert results["exported_count"] == 0
        assert results["skipped_count"] == 3
        assert results["error_count"] == 0

        # Check that disabled message was logged
        info_messages = [msg for msg, level in log_messages if level == "info"]
        assert any("disabled" in msg for msg in info_messages)

    def test_export_equity_data_batch_missing_config(self):
        """Test batch export with missing configuration."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        portfolios = self.create_sample_portfolios()
        config = {}  # No EQUITY_DATA config

        results = export_equity_data_batch(portfolios, mock_log, config)

        assert results["total_portfolios"] == 3
        assert results["exported_count"] == 0
        assert results["skipped_count"] == 3
        assert results["error_count"] == 0

    @patch("app.tools.equity_export.export_equity_data_to_csv")
    def test_export_equity_data_batch_with_errors(self, mock_export_csv):
        """Test batch export with some errors."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        # First call succeeds, second call fails
        mock_export_csv.side_effect = [True, Exception("Export error")]

        portfolios = self.create_sample_portfolios()
        config = {"EQUITY_DATA": {"EXPORT": True, "METRIC": "mean"}}

        results = export_equity_data_batch(portfolios, mock_log, config)

        assert results["total_portfolios"] == 3
        assert results["exported_count"] == 1  # One successful
        assert results["skipped_count"] == 1  # One without equity data
        assert results["error_count"] == 1  # One error
        assert len(results["errors"]) == 1


class TestEquityExportValidation:
    """Test validation functionality."""

    def test_validate_equity_export_requirements_valid_sma(self):
        """Test validation with valid SMA parameters."""
        result = validate_equity_export_requirements("AAPL", "SMA", 20, 50)
        assert result is True

    def test_validate_equity_export_requirements_valid_macd(self):
        """Test validation with valid MACD parameters."""
        result = validate_equity_export_requirements("MSFT", "MACD", 12, 26, 9)
        assert result is True

    def test_validate_equity_export_requirements_invalid_ticker(self):
        """Test validation with invalid ticker."""
        result = validate_equity_export_requirements("", "SMA", 20, 50)
        assert result is False

        result = validate_equity_export_requirements(None, "SMA", 20, 50)
        assert result is False

    def test_validate_equity_export_requirements_invalid_strategy(self):
        """Test validation with invalid strategy type."""
        result = validate_equity_export_requirements("AAPL", "INVALID", 20, 50)
        assert result is False

    def test_validate_equity_export_requirements_invalid_windows(self):
        """Test validation with invalid window parameters."""
        result = validate_equity_export_requirements("AAPL", "SMA", None, 50)
        assert result is False

        result = validate_equity_export_requirements("AAPL", "SMA", 0, 50)
        assert result is False

        result = validate_equity_export_requirements("AAPL", "SMA", "invalid", 50)
        assert result is False

    def test_validate_equity_export_requirements_macd_missing_signal(self):
        """Test validation for MACD without signal period."""
        result = validate_equity_export_requirements("AAPL", "MACD", 12, 26, None)
        assert result is False

        result = validate_equity_export_requirements("AAPL", "MACD", 12, 26, 0)
        assert result is False


class TestEquityExportUtilities:
    """Test utility functions."""

    @patch("app.tools.equity_export.get_equity_export_directory")
    def test_get_equity_export_file_path(self, mock_get_dir):
        """Test file path generation."""
        mock_get_dir.return_value = Path("/test/export")

        file_path = get_equity_export_file_path("AAPL", "SMA", 20, 50)
        expected = Path("/test/export/AAPL_SMA_20_50_0.csv")
        assert file_path == expected

    @patch("app.tools.equity_export.get_equity_export_directory")
    def test_cleanup_old_equity_files(self, mock_get_dir):
        """Test cleanup of old equity files."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        with tempfile.TemporaryDirectory() as temp_dir:
            export_dir = Path(temp_dir)
            mock_get_dir.return_value = export_dir

            # Create some test files
            old_file = export_dir / "old_file.csv"
            new_file = export_dir / "new_file.csv"
            old_file.touch()
            new_file.touch()

            # Set old file modification time to be old enough for cleanup
            import time

            old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
            os.utime(old_file, (old_time, old_time))

            deleted_count = cleanup_old_equity_files(
                "SMA", 7, mock_log
            )  # 7 day threshold

            assert deleted_count == 1
            assert not old_file.exists()
            assert new_file.exists()

    @patch("app.tools.equity_export.get_equity_export_directory")
    def test_cleanup_old_equity_files_nonexistent_directory(self, mock_get_dir):
        """Test cleanup when directory doesn't exist."""
        log_messages = []

        def mock_log(msg, level):
            log_messages.append((msg, level))

        mock_get_dir.return_value = Path("/nonexistent/directory")

        deleted_count = cleanup_old_equity_files("SMA", 7, mock_log)
        assert deleted_count == 0
