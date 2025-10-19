#!/usr/bin/env python3
"""
Comprehensive Test Suite for PortfolioAnalysisService

Tests the new portfolio analysis service functionality including:
- File discovery and aggregation
- Current vs general mode operations
- DataFrame processing and statistics
- CSV output generation
- Error handling and edge cases
"""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

from app.cli.services.portfolio_analysis_service import PortfolioAnalysisService


class TestPortfolioAnalysisService(unittest.TestCase):
    """Test class for PortfolioAnalysisService."""

    def setUp(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create directory structure
        self.portfolios_best_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        self.current_date_dir = self.portfolios_best_dir / "20250815"

        self.portfolios_best_dir.mkdir(parents=True)
        self.current_date_dir.mkdir(parents=True)

        # Create test data
        self.sample_portfolio_data = {
            "Ticker": ["AAPL", "AAPL", "MSFT"],
            "Strategy Type": ["SMA", "EMA", "SMA"],
            "Score": [0.85, 0.72, 0.91],
            "Win Rate [%]": [65.5, 58.2, 72.1],
            "Total Return [%]": [123.4, 98.7, 145.2],
            "Total Trades": [25, 18, 31],
            "Profit Factor": [2.1, 1.8, 2.4],
            "Expectancy per Trade": [4.2, 3.1, 4.8],
            "Sortino Ratio": [1.5, 1.2, 1.8],
            "Sharpe Ratio": [1.3, 1.0, 1.6],
            "Max Drawdown [%]": [-8.5, -12.3, -6.2],
        }

        # Create sample CSV files
        self._create_test_csv_files()

    def tearDown(self):
        """Clean up test environment after each test."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_csv_files(self):
        """Create test CSV files in both current and general directories."""
        # Sample data for different tickers and strategies
        aapl_data = pd.DataFrame(
            {
                "Ticker": ["AAPL"] * 2,
                "Strategy Type": ["SMA", "EMA"],
                "Score": [0.85, 0.72],
                "Win Rate [%]": [65.5, 58.2],
                "Total Return [%]": [123.4, 98.7],
                "Total Trades": [25, 18],
                "Profit Factor": [2.1, 1.8],
                "Expectancy per Trade": [4.2, 3.1],
                "Sortino Ratio": [1.5, 1.2],
                "Sharpe Ratio": [1.3, 1.0],
                "Max Drawdown [%]": [-8.5, -12.3],
            }
        )

        msft_data = pd.DataFrame(
            {
                "Ticker": ["MSFT"],
                "Strategy Type": ["MACD"],
                "Score": [0.91],
                "Win Rate [%]": [72.1],
                "Total Return [%]": [145.2],
                "Total Trades": [31],
                "Profit Factor": [2.4],
                "Expectancy per Trade": [4.8],
                "Sortino Ratio": [1.8],
                "Sharpe Ratio": [1.6],
                "Max Drawdown [%]": [-6.2],
            }
        )

        # Create files in current date directory
        aapl_current_path = self.current_date_dir / "AAPL_D_SMA.csv"
        msft_current_path = self.current_date_dir / "MSFT_D_MACD.csv"
        aapl_data.to_csv(aapl_current_path, index=False)
        msft_data.to_csv(msft_current_path, index=False)

        # Create files in general directory
        aapl_general_path = self.portfolios_best_dir / "AAPL_D_SMA.csv"
        msft_general_path = self.portfolios_best_dir / "MSFT_D_MACD.csv"
        aapl_data.to_csv(aapl_general_path, index=False)
        msft_data.to_csv(msft_general_path, index=False)

        # Create empty file for edge case testing
        empty_file_path = self.current_date_dir / "EMPTY_D_TEST.csv"
        pd.DataFrame().to_csv(empty_file_path, index=False)

    def test_initialization_general_mode(self):
        """Test service initialization in general mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        self.assertEqual(service.base_dir, self.temp_path)
        self.assertFalse(service.use_current)
        self.assertEqual(service.portfolios_best_dir, self.portfolios_best_dir)

    def test_initialization_current_mode(self):
        """Test service initialization in current mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=True
        )

        self.assertEqual(service.base_dir, self.temp_path)
        self.assertTrue(service.use_current)
        self.assertEqual(service.portfolios_best_dir, self.portfolios_best_dir)

    def test_get_current_date_string(self):
        """Test current date string generation."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        # Test that it returns a string in the expected format
        date_string = service._get_current_date_string()

        # Should be 8 digits (YYYYMMDD format)
        self.assertEqual(len(date_string), 8)
        self.assertTrue(date_string.isdigit())

        # Should start with 20 (assuming current century)
        self.assertTrue(date_string.startswith("20"))

    def test_find_ticker_files_current_mode(self):
        """Test finding ticker files in current mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=True
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            files = service._find_ticker_files("AAPL")

        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("AAPL_D_"))

    def test_find_ticker_files_general_mode(self):
        """Test finding ticker files in general mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        files = service._find_ticker_files("AAPL")

        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].name.startswith("AAPL_D_"))

    def test_find_ticker_files_nonexistent_ticker(self):
        """Test finding files for nonexistent ticker."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        files = service._find_ticker_files("NONEXISTENT")

        self.assertEqual(len(files), 0)

    @patch("builtins.print")  # Mock rprint which is aliased to print
    def test_aggregate_portfolios_best_current_mode(self, mock_print):
        """Test aggregating portfolios in current mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=True
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            result_df = service.aggregate_portfolios_best(["AAPL", "MSFT"])

        self.assertFalse(result_df.empty)
        self.assertEqual(len(result_df), 3)  # 2 AAPL + 1 MSFT
        self.assertIn("AAPL", result_df["Ticker"].values)
        self.assertIn("MSFT", result_df["Ticker"].values)

    @patch("builtins.print")
    def test_aggregate_portfolios_best_general_mode(self, mock_print):
        """Test aggregating portfolios in general mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        result_df = service.aggregate_portfolios_best(["AAPL", "MSFT"])

        self.assertFalse(result_df.empty)
        self.assertEqual(len(result_df), 3)  # 2 AAPL + 1 MSFT
        self.assertIn("AAPL", result_df["Ticker"].values)
        self.assertIn("MSFT", result_df["Ticker"].values)

    @patch("builtins.print")
    def test_aggregate_portfolios_best_missing_tickers(self, mock_print):
        """Test aggregating portfolios with some missing tickers."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        result_df = service.aggregate_portfolios_best(["AAPL", "NONEXISTENT"])

        self.assertFalse(result_df.empty)
        self.assertEqual(len(result_df), 2)  # Only AAPL found
        self.assertIn("AAPL", result_df["Ticker"].values)
        self.assertNotIn("NONEXISTENT", result_df["Ticker"].values)

    @patch("builtins.print")
    def test_aggregate_portfolios_best_no_valid_data(self, mock_print):
        """Test aggregating portfolios when no valid data found."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        result_df = service.aggregate_portfolios_best(["NONEXISTENT1", "NONEXISTENT2"])

        self.assertTrue(result_df.empty)

    @patch("builtins.print")
    def test_aggregate_all_current_portfolios(self, mock_print):
        """Test aggregating all current portfolios."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=True
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            result_df = service.aggregate_all_current_portfolios()

        self.assertFalse(result_df.empty)
        self.assertEqual(len(result_df), 3)  # 2 AAPL + 1 MSFT (empty file ignored)

    @patch("builtins.print")
    def test_aggregate_all_current_portfolios_not_current_mode(self, mock_print):
        """Test aggregating all current portfolios when not in current mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        result_df = service.aggregate_all_current_portfolios()

        self.assertTrue(result_df.empty)

    def test_discover_all_current_files(self):
        """Test discovering all current files."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=True
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            files = service._discover_all_current_files()

        self.assertGreaterEqual(len(files), 2)  # At least AAPL and MSFT
        file_names = [f.name for f in files]
        self.assertIn("AAPL_D_SMA.csv", file_names)
        self.assertIn("MSFT_D_MACD.csv", file_names)

    def test_discover_all_current_files_not_current_mode(self):
        """Test discovering all current files when not in current mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        files = service._discover_all_current_files()

        self.assertEqual(len(files), 0)

    def test_remove_metric_type_column(self):
        """Test removing Metric Type column."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        # Create DataFrame with Metric Type column
        test_df = pd.DataFrame(
            {"Ticker": ["AAPL"], "Metric Type": ["Best"], "Score": [0.85]}
        )

        result_df = service.remove_metric_type_column(test_df)

        self.assertNotIn("Metric Type", result_df.columns)
        self.assertIn("Ticker", result_df.columns)
        self.assertIn("Score", result_df.columns)

    def test_remove_metric_type_column_empty_df(self):
        """Test removing Metric Type column from empty DataFrame."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        empty_df = pd.DataFrame()
        result_df = service.remove_metric_type_column(empty_df)

        self.assertTrue(result_df.empty)

    def test_sort_portfolios(self):
        """Test sorting portfolios by score."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        test_df = pd.DataFrame(
            {"Ticker": ["AAPL", "MSFT", "GOOGL"], "Score": [0.85, 0.91, 0.72]}
        )

        result_df = service.sort_portfolios(test_df, sort_by="Score", ascending=False)

        # Should be sorted by Score descending: MSFT (0.91), AAPL (0.85), GOOGL (0.72)
        self.assertEqual(result_df.iloc[0]["Ticker"], "MSFT")
        self.assertEqual(result_df.iloc[1]["Ticker"], "AAPL")
        self.assertEqual(result_df.iloc[2]["Ticker"], "GOOGL")

    def test_sort_portfolios_missing_column(self):
        """Test sorting portfolios by missing column."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        test_df = pd.DataFrame({"Ticker": ["AAPL", "MSFT"], "Score": [0.85, 0.91]})

        result_df = service.sort_portfolios(test_df, sort_by="NonExistent")

        # Should return original DataFrame unchanged
        self.assertEqual(len(result_df), 2)
        self.assertEqual(result_df.iloc[0]["Ticker"], "AAPL")

    def test_calculate_stats(self):
        """Test calculating portfolio statistics."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        test_df = pd.DataFrame(self.sample_portfolio_data)
        stats = service._calculate_stats(test_df)

        self.assertEqual(stats["total_portfolios"], 3)
        self.assertAlmostEqual(stats["avg_score"], 0.826667, places=5)
        self.assertEqual(stats["win_rate_range"], (58.2, 72.1))
        self.assertEqual(stats["best_ticker"], "MSFT")
        self.assertAlmostEqual(stats["best_return"], 145.2, places=1)

    def test_calculate_stats_empty_df(self):
        """Test calculating statistics from empty DataFrame."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        empty_df = pd.DataFrame()
        stats = service._calculate_stats(empty_df)

        expected_stats = {
            "total_portfolios": 0,
            "avg_score": 0,
            "win_rate_range": (0, 0),
            "best_ticker": "N/A",
            "best_return": 0,
        }

        self.assertEqual(stats, expected_stats)

    def test_format_for_display(self):
        """Test formatting DataFrame for display."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        test_df = pd.DataFrame(self.sample_portfolio_data)
        result = service.format_for_display(test_df, top_n=2)

        self.assertIn("top_results", result)
        self.assertIn("all_results", result)
        self.assertIn("stats", result)

        # Top results should be limited to 2
        self.assertEqual(len(result["top_results"]), 2)

        # All results should contain all data
        self.assertEqual(len(result["all_results"]), 3)

        # Stats should be calculated
        self.assertEqual(result["stats"]["total_portfolios"], 3)

    def test_format_for_display_empty_df(self):
        """Test formatting empty DataFrame for display."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        empty_df = pd.DataFrame()
        result = service.format_for_display(empty_df)

        self.assertTrue(result["top_results"].empty)
        self.assertTrue(result["all_results"].empty)
        self.assertEqual(result["stats"]["total_portfolios"], 0)

    def test_generate_csv_output(self):
        """Test generating CSV output string."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        test_df = pd.DataFrame({"Ticker": ["AAPL", "MSFT"], "Score": [0.85, 0.91]})

        csv_output = service.generate_csv_output(test_df)

        self.assertIn("Ticker,Score", csv_output)
        self.assertIn("AAPL,0.85", csv_output)
        self.assertIn("MSFT,0.91", csv_output)

        # Should have proper line breaks
        lines = csv_output.split("\n")
        self.assertEqual(len(lines), 3)  # Header + 2 data rows

    def test_generate_csv_output_empty_df(self):
        """Test generating CSV output from empty DataFrame."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        empty_df = pd.DataFrame()
        csv_output = service.generate_csv_output(empty_df)

        self.assertEqual(csv_output, "No data available")

    def test_get_display_columns(self):
        """Test getting display columns list."""
        service = PortfolioAnalysisService(base_dir=str(self.temp_path))

        columns = service.get_display_columns()

        expected_columns = [
            "Ticker",
            "Strategy Type",
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Total Return [%]",
            "Sharpe Ratio",
            "Max Drawdown [%]",
            "Total Trades",
        ]

        self.assertEqual(columns, expected_columns)

    @patch("app.cli.services.portfolio_analysis_service.pd.read_csv")
    def test_error_handling_corrupt_csv(self, mock_read_csv):
        """Test error handling when CSV file is corrupt."""
        mock_read_csv.side_effect = Exception("Corrupt CSV file")

        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        with patch("builtins.print"):  # Mock rprint
            result_df = service.aggregate_portfolios_best(["AAPL"])

        # Should return empty DataFrame when files can't be read
        self.assertTrue(result_df.empty)

    def test_file_discovery_patterns(self):
        """Test file discovery patterns for different timeframes."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        # Create files with different timeframe patterns
        test_files = [
            "AAPL_D_SMA.csv",  # Daily
            "AAPL_4H_EMA.csv",  # 4-hour
            "AAPL_H_MACD.csv",  # Hourly
            "AAPL_D.csv",  # Daily without strategy
        ]

        for filename in test_files:
            file_path = self.portfolios_best_dir / filename
            pd.DataFrame({"Ticker": ["AAPL"]}).to_csv(file_path, index=False)

        files = service._find_ticker_files("AAPL")

        # Should find all timeframe patterns
        self.assertGreaterEqual(len(files), 4)
        file_names = [f.name for f in files]
        for expected_file in test_files:
            self.assertIn(expected_file, file_names)


class TestPortfolioAnalysisServiceIntegration(unittest.TestCase):
    """Integration tests for PortfolioAnalysisService with realistic data."""

    def setUp(self):
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create realistic directory structure
        self.portfolios_best_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        self.current_date_dir = self.portfolios_best_dir / "20250815"

        self.portfolios_best_dir.mkdir(parents=True)
        self.current_date_dir.mkdir(parents=True)

        # Create realistic portfolio data
        self._create_realistic_test_data()

    def tearDown(self):
        """Clean up integration test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_realistic_test_data(self):
        """Create realistic portfolio data for testing."""
        # Large realistic dataset with multiple tickers and strategies
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        strategies = ["SMA", "EMA", "MACD", "RSI"]

        all_data = []
        for ticker in tickers:
            for i, strategy in enumerate(strategies):
                # Generate realistic metrics
                base_score = 0.6 + (i * 0.1) + (hash(ticker) % 100) / 1000
                all_data.append(
                    {
                        "Ticker": ticker,
                        "Strategy Type": strategy,
                        "Score": round(base_score, 3),
                        "Win Rate [%]": round(50 + (base_score * 30), 1),
                        "Total Return [%]": round(base_score * 200, 1),
                        "Total Trades": 20 + i * 5,
                        "Profit Factor": round(1.0 + base_score, 2),
                        "Expectancy per Trade": round(base_score * 5, 2),
                        "Sortino Ratio": round(base_score * 2, 2),
                        "Sharpe Ratio": round(base_score * 1.8, 2),
                        "Max Drawdown [%]": round(-5 - (base_score * 10), 1),
                    }
                )

        # Create individual files for each ticker
        for ticker in tickers:
            ticker_data = [row for row in all_data if row["Ticker"] == ticker]
            df = pd.DataFrame(ticker_data)

            # Create in both current and general directories
            current_file = self.current_date_dir / f"{ticker}_D_MULTI.csv"
            general_file = self.portfolios_best_dir / f"{ticker}_D_MULTI.csv"

            df.to_csv(current_file, index=False)
            df.to_csv(general_file, index=False)

    @patch("builtins.print")
    def test_large_portfolio_aggregation(self, mock_print):
        """Test aggregating large number of portfolios."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=True
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            result_df = service.aggregate_all_current_portfolios()

        # Should load all 20 portfolios (5 tickers × 4 strategies)
        self.assertEqual(len(result_df), 20)

        # Verify all tickers and strategies are present
        unique_tickers = set(result_df["Ticker"].values)
        unique_strategies = set(result_df["Strategy Type"].values)

        self.assertEqual(len(unique_tickers), 5)
        self.assertEqual(len(unique_strategies), 4)

    @patch("builtins.print")
    def test_performance_sorting_and_filtering(self, mock_print):
        """Test performance with sorting and filtering operations."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        # Aggregate all portfolios
        df = service.aggregate_portfolios_best(
            ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        )

        # Test sorting by different metrics
        sorted_by_score = service.sort_portfolios(df, "Score", ascending=False)
        sorted_by_return = service.sort_portfolios(
            df, "Total Return [%]", ascending=False
        )

        # Verify sorting worked correctly
        scores = sorted_by_score["Score"].tolist()
        returns = sorted_by_return["Total Return [%]"].tolist()

        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(returns, sorted(returns, reverse=True))

    @patch("builtins.print")
    def test_comprehensive_stats_calculation(self, mock_print):
        """Test comprehensive statistics calculation with realistic data."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        df = service.aggregate_portfolios_best(["AAPL", "MSFT", "GOOGL"])
        stats = service._calculate_stats(df)

        # Verify all stats are calculated correctly
        self.assertEqual(stats["total_portfolios"], 12)  # 3 tickers × 4 strategies
        self.assertGreater(stats["avg_score"], 0)
        self.assertIsInstance(stats["win_rate_range"], tuple)
        self.assertIn(stats["best_ticker"], ["AAPL", "MSFT", "GOOGL"])
        self.assertGreater(stats["best_return"], 0)

    def test_display_formatting_with_large_dataset(self):
        """Test display formatting with large dataset."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path), use_current=False
        )

        with patch("builtins.print"):
            df = service.aggregate_portfolios_best(
                ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            )

        # Test with different top_n values
        result_small = service.format_for_display(df, top_n=5)
        result_large = service.format_for_display(df, top_n=15)

        self.assertEqual(len(result_small["top_results"]), 5)
        self.assertEqual(len(result_large["top_results"]), 15)
        self.assertEqual(len(result_small["all_results"]), 20)  # Full dataset
        self.assertEqual(len(result_large["all_results"]), 20)  # Full dataset


if __name__ == "__main__":
    unittest.main()
