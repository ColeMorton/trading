"""Tests for file utility functions."""

from pathlib import Path
from unittest.mock import patch

from app.tools.portfolio.file_utils import extract_file_metadata, save_aggregation_csv


class TestExtractFileMetadata:
    """Test suite for extract_file_metadata function."""

    def test_standard_format(self):
        """Test extracting metadata from standard filename format."""
        result = extract_file_metadata("AAPL_D_SMA.csv")

        assert result["filename"] == "AAPL_D_SMA.csv"
        assert result["ticker"] == "AAPL"
        assert result["timeframe"] == "D"
        assert result["strategy"] == "SMA"

    def test_hourly_timeframe(self):
        """Test extracting metadata with hourly timeframe."""
        result = extract_file_metadata("BTC-USD_H_EMA.csv")

        assert result["ticker"] == "BTC-USD"
        assert result["timeframe"] == "H"
        assert result["strategy"] == "EMA"

    def test_macd_strategy(self):
        """Test extracting metadata for MACD strategy."""
        result = extract_file_metadata("TSLA_D_MACD.csv")

        assert result["ticker"] == "TSLA"
        assert result["strategy"] == "MACD"

    def test_ticker_only(self):
        """Test extracting metadata when only ticker is present."""
        result = extract_file_metadata("NVDA.csv")

        assert result["ticker"] == "NVDA"
        assert result["timeframe"] == "D"  # Default
        assert result["strategy"] == "SMA"  # Default

    def test_ticker_and_timeframe_only(self):
        """Test extracting metadata with ticker and timeframe only."""
        result = extract_file_metadata("SPY_W.csv")

        assert result["ticker"] == "SPY"
        assert result["timeframe"] == "W"
        assert result["strategy"] == "SMA"  # Default

    def test_empty_filename(self):
        """Test extracting metadata from empty filename."""
        result = extract_file_metadata(".csv")

        # Should handle gracefully with defaults
        assert result["filename"] == ".csv"
        assert result["timeframe"] == "D"
        assert result["strategy"] == "SMA"

    def test_no_extension(self):
        """Test extracting metadata without file extension."""
        result = extract_file_metadata("MSFT_D_EMA")

        assert result["ticker"] == "MSFT"
        assert result["timeframe"] == "D"
        assert result["strategy"] == "EMA"

    def test_complex_ticker_name(self):
        """Test extracting metadata from ticker with dashes."""
        result = extract_file_metadata("BTC-USD_D_SMA.csv")

        assert result["ticker"] == "BTC-USD"
        assert result["timeframe"] == "D"
        assert result["strategy"] == "SMA"


class TestSaveAggregationCsv:
    """Test suite for save_aggregation_csv function."""

    @patch("app.tools.portfolio.file_utils.pd.DataFrame.to_csv")
    def test_save_ticker_aggregation(self, mock_to_csv):
        """Test saving aggregation results with ticker data."""
        aggregation_results = {
            "by_ticker": {
                "AAPL": {
                    "total_strategies": 3,
                    "total_rows": 150,
                    "avg_score": 1.35,
                    "avg_win_rate": 62.5,
                    "avg_return": 45.2,
                    "best_score": 1.75,
                    "best_strategy": {"strategy": "SMA"},
                    "strategy_types": {"SMA", "EMA"},
                    "timeframes": {"D"},
                }
            },
            "by_strategy": {},
        }

        output_path = Path("/tmp/test_aggregation.csv")
        save_aggregation_csv(aggregation_results, output_path)

        # Verify to_csv was called
        mock_to_csv.assert_called_once_with(output_path, index=False)

    @patch("app.tools.portfolio.file_utils.pd.DataFrame.to_csv")
    def test_save_strategy_aggregation(self, mock_to_csv):
        """Test saving aggregation results with strategy data."""
        aggregation_results = {
            "by_ticker": {},
            "by_strategy": {
                "SMA": {
                    "total_files": 5,
                    "total_rows": 250,
                    "avg_score": 1.22,
                    "avg_win_rate": 58.0,
                    "avg_return": 38.5,
                    "best_score": 1.65,
                    "best_performer": {"ticker": "AAPL"},
                    "tickers": {"AAPL", "MSFT", "GOOGL"},
                    "timeframes": {"D", "W"},
                }
            },
        }

        output_path = Path("/tmp/test_strategy_agg.csv")
        save_aggregation_csv(aggregation_results, output_path)

        mock_to_csv.assert_called_once()

    @patch("app.tools.portfolio.file_utils.pd.DataFrame.to_csv")
    def test_save_empty_aggregation(self, mock_to_csv):
        """Test saving empty aggregation results."""
        aggregation_results = {"by_ticker": {}, "by_strategy": {}}

        output_path = Path("/tmp/test_empty.csv")
        save_aggregation_csv(aggregation_results, output_path)

        # Should still create an empty DataFrame and call to_csv
        mock_to_csv.assert_called_once()

    @patch("app.tools.portfolio.file_utils.pd.DataFrame.to_csv")
    def test_save_both_aggregations(self, mock_to_csv):
        """Test saving results with both ticker and strategy aggregations."""
        aggregation_results = {
            "by_ticker": {
                "TSLA": {
                    "total_strategies": 2,
                    "total_rows": 100,
                    "avg_score": 1.45,
                    "avg_win_rate": 65.0,
                    "avg_return": 52.3,
                    "best_score": 1.60,
                    "best_strategy": {"strategy": "EMA"},
                    "strategy_types": {"EMA"},
                    "timeframes": {"D"},
                }
            },
            "by_strategy": {
                "EMA": {
                    "total_files": 2,
                    "total_rows": 100,
                    "avg_score": 1.45,
                    "avg_win_rate": 65.0,
                    "avg_return": 52.3,
                    "best_score": 1.60,
                    "best_performer": {"ticker": "TSLA"},
                    "tickers": {"TSLA"},
                    "timeframes": {"D"},
                }
            },
        }

        output_path = Path("/tmp/test_both.csv")
        save_aggregation_csv(aggregation_results, output_path)

        mock_to_csv.assert_called_once()

    @patch("app.tools.portfolio.file_utils.pd.DataFrame.to_csv")
    def test_save_handles_none_best_strategy(self, mock_to_csv):
        """Test saving when best_strategy is None."""
        aggregation_results = {
            "by_ticker": {
                "NVDA": {
                    "total_strategies": 1,
                    "total_rows": 50,
                    "avg_score": 0.95,
                    "avg_win_rate": 48.0,
                    "avg_return": 15.0,
                    "best_score": 0.95,
                    "best_strategy": None,  # No best strategy
                    "strategy_types": {"SMA"},
                    "timeframes": {"D"},
                }
            },
            "by_strategy": {},
        }

        output_path = Path("/tmp/test_none.csv")
        save_aggregation_csv(aggregation_results, output_path)

        mock_to_csv.assert_called_once()
