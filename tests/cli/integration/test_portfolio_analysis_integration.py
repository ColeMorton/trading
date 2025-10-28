#!/usr/bin/env python3
"""
Integration Tests for Portfolio Analysis Service with CLI Commands

Tests the integration of PortfolioAnalysisService with CLI commands to ensure
end-to-end functionality works correctly in realistic scenarios.
"""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
from typer.testing import CliRunner

from app.cli.services.portfolio_analysis_service import PortfolioAnalysisService


class TestPortfolioAnalysisIntegration(unittest.TestCase):
    """Integration tests for portfolio analysis service with CLI commands."""

    def setUp(self):
        """Set up integration test environment."""
        self.runner = CliRunner()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # Create realistic test environment
        self.portfolios_best_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        self.current_date_dir = self.portfolios_best_dir / "20250815"

        self.portfolios_best_dir.mkdir(parents=True)
        self.current_date_dir.mkdir(parents=True)

        self._create_test_portfolio_files()

    def tearDown(self):
        """Clean up integration test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_portfolio_files(self):
        """Create realistic test portfolio files for integration testing."""
        # Create comprehensive portfolio data
        portfolio_data = {
            "Ticker": ["AAPL", "AAPL", "MSFT", "MSFT", "GOOGL"],
            "Strategy Type": ["SMA", "EMA", "SMA", "MACD", "RSI"],
            "Score": [0.85, 0.72, 0.91, 0.68, 0.79],
            "Win Rate [%]": [65.5, 58.2, 72.1, 55.8, 61.3],
            "Total Return [%]": [123.4, 98.7, 145.2, 87.9, 112.6],
            "Total Trades": [25, 18, 31, 22, 28],
            "Profit Factor": [2.1, 1.8, 2.4, 1.6, 1.9],
            "Expectancy per Trade": [4.2, 3.1, 4.8, 2.7, 3.8],
            "Sortino Ratio": [1.5, 1.2, 1.8, 1.1, 1.4],
            "Sharpe Ratio": [1.3, 1.0, 1.6, 0.9, 1.2],
            "Max Drawdown [%]": [-8.5, -12.3, -6.2, -15.1, -10.8],
            "Metric Type": [
                "Best",
                "Best",
                "Best",
                "Best",
                "Best",
            ],  # For testing column removal
        }

        # Create multiple portfolio files
        tickers_data = {}
        for ticker in ["AAPL", "MSFT", "GOOGL"]:
            [row for i, row in enumerate(portfolio_data["Ticker"]) if row == ticker]
            ticker_df_data = {}
            for key, values in portfolio_data.items():
                ticker_df_data[key] = [
                    values[i]
                    for i, ticker_val in enumerate(portfolio_data["Ticker"])
                    if ticker_val == ticker
                ]
            tickers_data[ticker] = pd.DataFrame(ticker_df_data)

        # Create files in both current and general directories
        for ticker, df in tickers_data.items():
            # Current date files
            current_file = self.current_date_dir / f"{ticker}_D_MULTI.csv"
            df.to_csv(current_file, index=False)

            # General files
            general_file = self.portfolios_best_dir / f"{ticker}_D_MULTI.csv"
            df.to_csv(general_file, index=False)

    def test_service_initialization_with_realistic_paths(self):
        """Test service initializes correctly with realistic file paths."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=True,
        )

        self.assertTrue(service.portfolios_best_dir.exists())
        self.assertEqual(str(service.base_dir), str(self.temp_path))
        self.assertTrue(service.use_current)

    @patch("builtins.print")  # Mock rprint
    def test_end_to_end_portfolio_aggregation_current_mode(self, mock_print):
        """Test complete workflow from service initialization to final results."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=True,
        )

        # Simulate current date
        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            # Step 1: Aggregate portfolios
            df = service.aggregate_portfolios_best(["AAPL", "MSFT", "GOOGL"])

            # Step 2: Remove metric type column
            df_clean = service.remove_metric_type_column(df)

            # Step 3: Sort by score
            df_sorted = service.sort_portfolios(df_clean, "Score", ascending=False)

            # Step 4: Format for display
            display_data = service.format_for_display(df_sorted, top_n=3)

            # Step 5: Generate CSV output
            csv_output = service.generate_csv_output(display_data["top_results"])

        # Verify complete workflow
        self.assertFalse(df.empty)
        self.assertNotIn("Metric Type", df_clean.columns)
        self.assertGreater(df_sorted.iloc[0]["Score"], df_sorted.iloc[-1]["Score"])
        self.assertEqual(len(display_data["top_results"]), 3)
        self.assertIn("Ticker,Strategy Type", csv_output)

    @patch("builtins.print")
    def test_end_to_end_portfolio_aggregation_general_mode(self, mock_print):
        """Test complete workflow in general (non-current) mode."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        # Complete workflow
        df = service.aggregate_portfolios_best(["AAPL", "MSFT"])
        df_clean = service.remove_metric_type_column(df)
        df_sorted = service.sort_portfolios(
            df_clean,
            "Total Return [%]",
            ascending=False,
        )
        display_data = service.format_for_display(df_sorted, top_n=5)

        # Verify results
        self.assertFalse(df.empty)
        self.assertNotIn("Metric Type", df_clean.columns)
        self.assertEqual(len(display_data["all_results"]), len(df))
        self.assertGreater(display_data["stats"]["total_portfolios"], 0)

    @patch("builtins.print")
    def test_auto_discovery_workflow(self, mock_print):
        """Test auto-discovery workflow for current portfolios."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=True,
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            # Auto-discover all portfolios
            df = service.aggregate_all_current_portfolios()

            # Process discovered data
            df_clean = service.remove_metric_type_column(df)
            stats = service._calculate_stats(df_clean)
            display_columns = service.get_display_columns()

        # Verify auto-discovery worked
        self.assertFalse(df.empty)
        self.assertGreater(stats["total_portfolios"], 0)
        self.assertIn("Ticker", display_columns)
        self.assertIn("Score", display_columns)

    def test_error_handling_missing_directories(self):
        """Test error handling when directories don't exist."""
        # Use non-existent directory
        non_existent_path = "/tmp/non_existent_trading_dir"
        service = PortfolioAnalysisService(base_dir=non_existent_path, use_current=True)

        with patch("builtins.print"):  # Mock rprint
            # Should handle missing directories gracefully
            df = service.aggregate_portfolios_best(["AAPL"])

        # Should return empty DataFrame without crashing
        self.assertTrue(df.empty)

    def test_performance_with_large_dataset(self):
        """Test performance and functionality with larger datasets."""
        # Create larger dataset
        large_data = []
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NFLX", "NVDA"]
        strategies = ["SMA", "EMA", "MACD", "RSI", "BOLLINGER"]

        for ticker in tickers:
            for strategy in strategies:
                large_data.append(
                    {
                        "Ticker": ticker,
                        "Strategy Type": strategy,
                        "Score": 0.5 + (hash(f"{ticker}{strategy}") % 100) / 200,
                        "Win Rate [%]": 45 + (hash(f"{ticker}{strategy}") % 30),
                        "Total Return [%]": 50 + (hash(f"{ticker}{strategy}") % 150),
                        "Total Trades": 15 + (hash(f"{ticker}{strategy}") % 25),
                        "Profit Factor": 1.0
                        + (hash(f"{ticker}{strategy}") % 100) / 100,
                        "Expectancy per Trade": 1
                        + (hash(f"{ticker}{strategy}") % 50) / 10,
                        "Sortino Ratio": 0.5
                        + (hash(f"{ticker}{strategy}") % 100) / 100,
                        "Sharpe Ratio": 0.3 + (hash(f"{ticker}{strategy}") % 100) / 100,
                        "Max Drawdown [%]": -5 - (hash(f"{ticker}{strategy}") % 20),
                    },
                )

        # Create large dataset file
        large_df = pd.DataFrame(large_data)
        large_file = self.current_date_dir / "LARGE_DATASET_D_MULTI.csv"
        large_df.to_csv(large_file, index=False)

        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=True,
        )

        with patch.object(service, "_get_current_date_string", return_value="20250815"):
            with patch("builtins.print"):
                # Should handle large dataset efficiently
                df = service.aggregate_all_current_portfolios()
                sorted_df = service.sort_portfolios(df, "Score", ascending=False)
                display_data = service.format_for_display(sorted_df, top_n=10)

        # Verify large dataset processing
        self.assertGreater(len(df), 30)  # Should have many portfolios
        self.assertEqual(len(display_data["top_results"]), 10)
        self.assertGreater(display_data["stats"]["total_portfolios"], 30)

    def test_column_filtering_and_display_formatting(self):
        """Test column filtering and display formatting for different use cases."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        with patch("builtins.print"):
            df = service.aggregate_portfolios_best(["AAPL", "MSFT", "GOOGL"])

        # Test display column filtering
        display_columns = service.get_display_columns()

        # Ensure all critical columns are included
        critical_columns = [
            "Ticker",
            "Strategy Type",
            "Score",
            "Win Rate [%]",
            "Total Return [%]",
        ]
        for col in critical_columns:
            self.assertIn(col, display_columns)

        # Test that Metric Type removal works
        df_clean = service.remove_metric_type_column(df)
        self.assertNotIn("Metric Type", df_clean.columns)

        # Test different sorting options
        by_score = service.sort_portfolios(df_clean, "Score", ascending=False)
        by_return = service.sort_portfolios(
            df_clean,
            "Total Return [%]",
            ascending=False,
        )
        by_winrate = service.sort_portfolios(df_clean, "Win Rate [%]", ascending=False)

        # Verify sorting worked correctly
        self.assertGreaterEqual(by_score.iloc[0]["Score"], by_score.iloc[-1]["Score"])
        self.assertGreaterEqual(
            by_return.iloc[0]["Total Return [%]"],
            by_return.iloc[-1]["Total Return [%]"],
        )
        self.assertGreaterEqual(
            by_winrate.iloc[0]["Win Rate [%]"],
            by_winrate.iloc[-1]["Win Rate [%]"],
        )

    def test_csv_output_formatting(self):
        """Test CSV output formatting for different scenarios."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        with patch("builtins.print"):
            df = service.aggregate_portfolios_best(["AAPL", "MSFT"])

        # Test CSV generation with different data sizes
        csv_all = service.generate_csv_output(df)
        csv_top = service.generate_csv_output(df.head(2))
        csv_empty = service.generate_csv_output(pd.DataFrame())

        # Verify CSV formatting
        self.assertIn("Ticker,Strategy Type", csv_all)
        self.assertIn("AAPL", csv_all)
        self.assertIn("MSFT", csv_all)

        self.assertIn("Ticker,Strategy Type", csv_top)
        lines_top = csv_top.split("\n")
        self.assertEqual(len(lines_top), 3)  # Header + 2 data rows

        self.assertEqual(csv_empty, "No data available")

    @patch("builtins.print")
    def test_statistics_calculation_accuracy(self, mock_print):
        """Test accuracy of statistics calculations with known data."""
        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        df = service.aggregate_portfolios_best(["AAPL", "MSFT", "GOOGL"])
        stats = service._calculate_stats(df)

        # Verify statistics are calculated correctly
        self.assertGreater(stats["total_portfolios"], 0)
        self.assertIsInstance(stats["avg_score"], float)
        self.assertIsInstance(stats["win_rate_range"], tuple)
        self.assertEqual(len(stats["win_rate_range"]), 2)
        self.assertIsInstance(stats["best_ticker"], str)
        self.assertIsInstance(stats["best_return"], float)

        # Verify logical consistency
        self.assertGreater(stats["win_rate_range"][1], stats["win_rate_range"][0])
        self.assertGreater(stats["avg_score"], 0)
        self.assertGreater(stats["best_return"], 0)


class TestPortfolioAnalysisServiceEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for PortfolioAnalysisService."""

    def setUp(self):
        """Set up edge case testing environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up edge case test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_empty_directory_handling(self):
        """Test handling of empty directories."""
        # Create empty directory structure
        portfolios_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        portfolios_dir.mkdir(parents=True)

        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        with patch("builtins.print"):
            df = service.aggregate_portfolios_best(["AAPL", "MSFT"])

        self.assertTrue(df.empty)

    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV files."""
        # Create directory structure
        portfolios_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        portfolios_dir.mkdir(parents=True)

        # Create truly malformed CSV that will cause pandas to fail
        malformed_file = portfolios_dir / "AAPL_D_BAD.csv"
        with open(malformed_file, "w") as f:
            f.write("Invalid data without proper CSV structure")

        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        with patch("builtins.print"):
            # Mock pd.read_csv to raise an exception for this test
            with patch("pandas.read_csv", side_effect=Exception("Malformed CSV")):
                df = service.aggregate_portfolios_best(["AAPL"])

        # Should return empty result when CSV reading fails
        self.assertTrue(df.empty)

    def test_missing_columns_handling(self):
        """Test handling of CSV files with missing required columns."""
        # Create directory structure
        portfolios_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        portfolios_dir.mkdir(parents=True)

        # Create CSV with missing columns
        incomplete_data = pd.DataFrame(
            {
                "Ticker": ["AAPL"],
                "Strategy Type": ["SMA"],
                # Missing Score, Win Rate, etc.
            },
        )
        incomplete_file = portfolios_dir / "AAPL_D_INCOMPLETE.csv"
        incomplete_data.to_csv(incomplete_file, index=False)

        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        with patch("builtins.print"):
            df = service.aggregate_portfolios_best(["AAPL"])
            stats = service._calculate_stats(df)

        # Should handle missing columns gracefully
        self.assertFalse(df.empty)
        self.assertEqual(stats["avg_score"], 0)  # Default when Score column missing
        self.assertEqual(
            stats["win_rate_range"],
            (0, 0),
        )  # Default when Win Rate missing

    def test_non_numeric_data_handling(self):
        """Test handling of non-numeric data in numeric columns."""
        # Create directory structure
        portfolios_dir = self.temp_path / "data" / "raw" / "portfolios_best"
        portfolios_dir.mkdir(parents=True)

        # Create CSV with non-numeric data in numeric columns
        bad_numeric_data = pd.DataFrame(
            {
                "Ticker": ["AAPL", "MSFT"],
                "Strategy Type": ["SMA", "EMA"],
                "Score": ["not_a_number", 0.85],
                "Win Rate [%]": [65.5, "invalid"],
                "Total Return [%]": ["bad_return", 98.7],
                "Total Trades": [25, 18],
            },
        )
        bad_file = portfolios_dir / "AAPL_D_BADNUMS.csv"
        bad_numeric_data.to_csv(bad_file, index=False)

        service = PortfolioAnalysisService(
            base_dir=str(self.temp_path),
            use_current=False,
        )

        with patch("builtins.print"):
            df = service.aggregate_portfolios_best(["AAPL"])
            service.sort_portfolios(df, "Score", ascending=False)
            stats = service._calculate_stats(df)

        # Should handle non-numeric data gracefully
        self.assertFalse(df.empty)
        self.assertIsInstance(
            stats["avg_score"],
            float,
        )  # Should handle non-numeric gracefully


if __name__ == "__main__":
    unittest.main()
