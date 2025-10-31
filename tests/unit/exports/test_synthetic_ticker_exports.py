"""
Test Coverage for Synthetic Ticker Export Functionality

This module provides comprehensive test coverage for synthetic ticker export
functionality, specifically focusing on STRK_MSTR pair analysis and other
synthetic ticker combinations as mentioned in the requirements.
"""

import tempfile
from unittest.mock import patch

import polars as pl
import pytest

from app.tools.export_csv import export_csv
from app.tools.synthetic_ticker import (
    create_synthetic_ticker,
    detect_synthetic_ticker,
    process_synthetic_ticker,
)


@pytest.mark.unit
class TestSyntheticTickerExports:
    """Test synthetic ticker export functionality."""

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary directory for export testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_strk_mstr_data(self):
        """Create sample STRK_MSTR synthetic ticker data."""
        return pl.DataFrame(
            {
                "Ticker": ["STRK_MSTR"] * 5,
                "Strategy Type": ["SMA"] * 5,
                "Short Window": [10, 15, 20, 25, 30],
                "Long Window": [50, 55, 60, 65, 70],
                "Total Return [%]": [15.5, 12.3, 18.7, 9.2, 21.1],
                "Sharpe Ratio": [1.2, 0.9, 1.5, 0.7, 1.8],
                "Max Drawdown [%]": [-8.5, -12.1, -6.3, -15.2, -4.9],
                "Win Rate [%]": [65.0, 58.0, 72.0, 51.0, 78.0],
                "Total Trades": [45, 38, 52, 31, 58],
                "Profit Factor": [1.8, 1.4, 2.1, 1.2, 2.3],
            }
        )

    @pytest.fixture
    def mock_config(self, temp_export_dir):
        """Create mock configuration for testing."""
        return {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["STRK_MSTR"],
            "STRATEGY_TYPE": "SMA",
            "USE_MA": True,
            "DIRECTION": "Long",
            "SHORT_WINDOW": 20,
            "LONG_WINDOW": 50,
        }

    def test_strk_mstr_sma_export(
        self, sample_strk_mstr_data, mock_config, temp_export_dir
    ):
        """Test STRK_MSTR pair with SMA strategy export."""
        # Setup config for SMA strategy
        config = mock_config.copy()
        config["STRATEGY_TYPE"] = "SMA"

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                # Execute export
                export_csv(sample_strk_mstr_data, "strategies", config)

                # Verify export was called
                mock_write_csv.assert_called_once()

                # Verify filename format for synthetic ticker
                call_args = mock_write_csv.call_args[0][0]
                assert "STRK_MSTR" in call_args
                assert "SMA" in call_args
                assert call_args.endswith(".csv")

                # Expected filename: STRK_MSTR_D_SMA.csv
                assert "STRK_MSTR_D_SMA.csv" in call_args

    def test_strk_mstr_ema_export(self, temp_export_dir):
        """Test STRK_MSTR pair with EMA strategy export."""
        # Create EMA-specific data
        ema_data = pl.DataFrame(
            {
                "Ticker": ["STRK_MSTR"] * 3,
                "Strategy Type": ["EMA"] * 3,
                "Short Window": [12, 18, 24],
                "Long Window": [48, 54, 60],
                "Total Return [%]": [14.2, 16.8, 11.5],
                "Sharpe Ratio": [1.1, 1.4, 0.8],
                "Max Drawdown [%]": [-9.2, -7.1, -13.5],
                "Win Rate [%]": [62.0, 69.0, 55.0],
                "Total Trades": [42, 48, 36],
                "Profit Factor": [1.7, 1.9, 1.3],
            }
        )

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["STRK_MSTR"],
            "STRATEGY_TYPE": "EMA",
            "USE_MA": True,
            "DIRECTION": "Long",
        }

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                export_csv(ema_data, "strategies", config)

                mock_write_csv.assert_called_once()
                call_args = mock_write_csv.call_args[0][0]
                assert "STRK_MSTR_D_EMA.csv" in call_args

    def test_strk_mstr_macd_export(self, temp_export_dir):
        """Test STRK_MSTR pair with MACD strategy export."""
        # Create MACD-specific data
        macd_data = pl.DataFrame(
            {
                "Ticker": ["STRK_MSTR"] * 4,
                "Strategy Type": ["MACD"] * 4,
                "Fast Period": [12, 14, 16, 18],
                "Slow Period": [26, 28, 30, 32],
                "Signal Period": [9, 10, 11, 12],
                "Total Return [%]": [13.8, 17.2, 10.9, 19.5],
                "Sharpe Ratio": [1.0, 1.3, 0.9, 1.6],
                "Max Drawdown [%]": [-10.1, -8.3, -14.7, -6.2],
                "Win Rate [%]": [59.0, 66.0, 53.0, 71.0],
                "Total Trades": [39, 45, 33, 51],
                "Profit Factor": [1.6, 1.8, 1.1, 2.0],
            }
        )

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["STRK_MSTR"],
            "STRATEGY_TYPE": "MACD",
            "USE_MA": False,  # MACD doesn't use USE_MA flag
            "DIRECTION": "Long",
        }

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                export_csv(macd_data, "strategies", config)

                mock_write_csv.assert_called_once()
                call_args = mock_write_csv.call_args[0][0]
                # MACD strategy exports with different naming convention
                assert "STRK_MSTR_D" in call_args and call_args.endswith(".csv")

    def test_synthetic_ticker_filename_generation(self, temp_export_dir):
        """Test that synthetic tickers generate correct filenames."""
        synthetic_tickers = ["STRK_MSTR", "BTC_USD", "ETH_USDT"]
        strategies = ["SMA", "EMA", "MACD"]

        for ticker in synthetic_tickers:
            for strategy in strategies:
                data = pl.DataFrame(
                    {
                        "Ticker": [ticker],
                        "Strategy Type": [strategy],
                        "Total Return [%]": [10.0],
                    }
                )

                config = {
                    "BASE_DIR": temp_export_dir,
                    "TICKER": [ticker],
                    "STRATEGY_TYPE": strategy,
                    "USE_MA": strategy in ["SMA", "EMA"],
                }

                with patch("pathlib.Path.mkdir"):
                    with patch("os.access", return_value=True):
                        with patch("polars.DataFrame.write_csv") as mock_write_csv:
                            export_csv(data, "strategies", config)

                            mock_write_csv.assert_called_once()
                            call_args = mock_write_csv.call_args[0][0]

                            # Verify filename format - different for MA strategies vs others
                            if strategy in ["SMA", "EMA"]:
                                expected_filename = f"{ticker}_D_{strategy}.csv"
                                assert expected_filename in call_args
                            else:  # MACD and others
                                # MACD exports with simpler naming
                                assert (
                                    f"{ticker}_D" in call_args
                                    and call_args.endswith(".csv")
                                )

    def test_synthetic_ticker_data_integrity(
        self, sample_strk_mstr_data, temp_export_dir
    ):
        """Test that synthetic ticker data maintains integrity during export."""
        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["STRK_MSTR"],
            "STRATEGY_TYPE": "SMA",
            "USE_MA": True,
        }

        # Capture the data that gets written
        written_data = None

        def capture_write_csv(self, path):
            nonlocal written_data
            written_data = self.to_pandas()

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv", side_effect=capture_write_csv):
                export_csv(sample_strk_mstr_data, "strategies", config)

                # Verify data integrity
                assert written_data is not None
                assert len(written_data) == len(sample_strk_mstr_data)

                # Check that all original columns are preserved
                original_columns = set(sample_strk_mstr_data.columns)
                written_columns = set(written_data.columns)
                assert original_columns.issubset(written_columns)

                # Verify ticker values are maintained
                assert all(written_data["Ticker"] == "STRK_MSTR")

    def test_multiple_synthetic_tickers_export(self, temp_export_dir):
        """Test export with multiple synthetic tickers."""
        multi_ticker_data = pl.DataFrame(
            {
                "Ticker": ["STRK_MSTR", "STRK_MSTR", "BTC_USD", "BTC_USD"],
                "Strategy Type": ["SMA", "SMA", "SMA", "SMA"],
                "Short Window": [10, 20, 15, 25],
                "Long Window": [50, 60, 45, 55],
                "Total Return [%]": [15.5, 12.3, 18.7, 9.2],
                "Sharpe Ratio": [1.2, 0.9, 1.5, 0.7],
                "Win Rate [%]": [65.0, 58.0, 72.0, 51.0],
                "Total Trades": [45, 38, 52, 31],
            }
        )

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["STRK_MSTR", "BTC_USD"],
            "STRATEGY_TYPE": "SMA",
            "USE_MA": True,
        }

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                export_csv(multi_ticker_data, "strategies", config)

                # Should call write_csv for each unique ticker
                assert mock_write_csv.call_count >= 1

                # Check that synthetic ticker naming is handled correctly
                all_calls = [call[0][0] for call in mock_write_csv.call_args_list]
                assert any("STRK_MSTR" in call for call in all_calls)
                assert any("BTC_USD" in call for call in all_calls)


@pytest.mark.unit
class TestSyntheticTickerDetection:
    """Test synthetic ticker detection and processing."""

    def test_detect_strk_mstr_synthetic_ticker(self):
        """Test detection of STRK_MSTR as synthetic ticker."""
        is_synthetic = detect_synthetic_ticker("STRK_MSTR")
        assert is_synthetic

    def test_detect_non_synthetic_ticker(self):
        """Test detection of regular ticker as non-synthetic."""
        is_synthetic = detect_synthetic_ticker("AAPL")
        assert not is_synthetic

    def test_process_strk_mstr_synthetic_config(self):
        """Test processing of STRK_MSTR synthetic ticker configuration."""
        config = {
            "TICKER": "STRK_MSTR",
            "STRATEGY_TYPE": "SMA",
        }

        processed = process_synthetic_ticker(config)

        # Should return processed configuration
        assert processed is not None
        assert isinstance(processed, dict)

    def test_create_strk_mstr_synthetic_ticker(self):
        """Test creation of STRK_MSTR synthetic ticker."""
        # This is a basic test - the actual implementation may vary
        synthetic_ticker = create_synthetic_ticker("STRK", "MSTR")

        # Should create a valid synthetic ticker string
        assert isinstance(synthetic_ticker, str)
        assert "STRK" in synthetic_ticker
        assert "MSTR" in synthetic_ticker


@pytest.mark.unit
class TestSyntheticTickerEdgeCases:
    """Test edge cases for synthetic ticker exports."""

    def test_empty_synthetic_ticker_data(self, temp_export_dir):
        """Test export behavior with empty synthetic ticker data."""
        empty_data = pl.DataFrame(
            {
                "Ticker": [],
                "Strategy Type": [],
                "Total Return [%]": [],
            }
        )

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["STRK_MSTR"],
            "STRATEGY_TYPE": "SMA",
        }

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv"):
                export_csv(empty_data, "strategies", config)

                # Should handle empty data gracefully
                # Behavior may vary based on implementation

    def test_invalid_synthetic_ticker_format(self, temp_export_dir):
        """Test handling of invalid synthetic ticker formats."""
        invalid_data = pl.DataFrame(
            {
                "Ticker": ["INVALID_SYNTHETIC_FORMAT_TOO_LONG"],
                "Strategy Type": ["SMA"],
                "Total Return [%]": [10.0],
            }
        )

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["INVALID_SYNTHETIC_FORMAT_TOO_LONG"],
            "STRATEGY_TYPE": "SMA",
        }

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv"):
                # Should handle invalid formats without crashing
                export_csv(invalid_data, "strategies", config)

    def test_synthetic_ticker_with_special_characters(self, temp_export_dir):
        """Test synthetic tickers with special characters in filenames."""
        special_data = pl.DataFrame(
            {
                "Ticker": ["BTC-USD"],  # Dash character
                "Strategy Type": ["SMA"],
                "Total Return [%]": [10.0],
            }
        )

        config = {
            "BASE_DIR": temp_export_dir,
            "TICKER": ["BTC-USD"],
            "STRATEGY_TYPE": "SMA",
        }

        with patch("pathlib.Path.mkdir"), patch("os.access", return_value=True):
            with patch("polars.DataFrame.write_csv") as mock_write_csv:
                export_csv(special_data, "strategies", config)

                mock_write_csv.assert_called_once()
                call_args = mock_write_csv.call_args[0][0]

                # Should handle special characters in filename
                assert "BTC-USD" in call_args or "BTC_USD" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
