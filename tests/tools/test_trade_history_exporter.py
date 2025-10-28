"""
Comprehensive test suite for trade history exporter functionality.

NOTE: Trade history export is only available through app/concurrency/review.py.
These tests verify the core export functionality when properly enabled.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock

import pandas as pd
import vectorbt as vbt

from app.tools.trade_history_exporter import (
    _categorize_trade_performance,
    _enrich_position_data,
    _enrich_trade_data,
    _extract_all_strategy_parameters,
    _extract_strategy_parameters,
    _is_trade_history_current,
    analyze_trade_performance,
    create_comprehensive_trade_history,
    export_trade_history,
    extract_orders_history,
    extract_positions_history,
    extract_trade_history,
    generate_trade_filename,
)


class TestTradeHistoryExporter(unittest.TestCase):
    """Test suite for trade history export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create mock portfolio data
        self.mock_portfolio = self._create_mock_portfolio()

        # Common test configurations
        self.test_configs = {
            "sma_config": {
                "TICKER": "BTC-USD",
                "STRATEGY_TYPE": "SMA",
                "fast_period": 20,
                "slow_period": 50,
                "BASE_DIR": ".",
            },
            "macd_config": {
                "TICKER": "MSTR",
                "STRATEGY_TYPE": "MACD",
                "fast_window": 12,
                "slow_window": 26,
                "signal_period": 9,
                "STOP_LOSS": 0.05,
                "BASE_DIR": ".",
            },
            "ema_hourly_config": {
                "TICKER": "ETH-USD",
                "USE_HOURLY": True,
                "STRATEGY_TYPE": "EMA",
                "FAST_PERIOD": 12,
                "SLOW_PERIOD": 26,
                "DIRECTION": "Short",
                "BASE_DIR": ".",
            },
        }

    def _create_mock_portfolio(self):
        """Create a mock VectorBT portfolio for testing."""
        # Create sample data for portfolio
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        pd.Series([100 + i * 0.5 for i in range(100)], index=dates)

        # Create mock trades DataFrame with integer indices (like VectorBT returns)
        trade_data = {
            "Entry Timestamp": [4, 31],  # Integer indices into the date range
            "Exit Timestamp": [9, 45],  # Integer indices into the date range
            "Avg Entry Price": [102.5, 120.0],
            "Avg Exit Price": [105.0, 118.0],
            "Size": [0.5, 0.3],
            "PnL": [1.25, -0.6],
            "Return": [0.024, -0.017],
            "Direction": ["Long", "Long"],
            "Status": ["Closed", "Closed"],
        }

        # Create mock orders DataFrame
        order_data = {
            "Order Id": [0, 1, 2, 3],
            "Column": [0, 0, 0, 0],
            "Timestamp": [4, 9, 31, 45],  # Integer indices
            "Size": [0.5, 0.5, 0.3, 0.3],
            "Price": [102.5, 105.0, 120.0, 118.0],
            "Fees": [0.1, 0.1, 0.12, 0.12],
            "Side": ["Buy", "Sell", "Buy", "Sell"],
        }

        # Create mock positions DataFrame
        position_data = {
            "Position Id": [0, 1],
            "Column": [0, 0],
            "Size": [0.5, 0.3],
            "Entry Timestamp": [4, 31],  # Integer indices
            "Avg Entry Price": [102.5, 120.0],
            "Entry Fees": [0.1, 0.12],
            "Exit Timestamp": [9, 45],  # Integer indices
            "Avg Exit Price": [105.0, 118.0],
            "Exit Fees": [0.1, 0.12],
            "PnL": [1.25, -0.6],
            "Return": [0.024, -0.017],
            "Direction": ["Long", "Long"],
            "Status": ["Closed", "Closed"],
        }

        # Create mock portfolio
        mock_portfolio = Mock(spec=vbt.Portfolio)

        # Mock trades
        mock_trades = Mock()
        mock_trades.records_readable = pd.DataFrame(trade_data)
        mock_trades.count.return_value = 2
        mock_trades.win_rate.return_value = 0.5
        mock_portfolio.trades = mock_trades

        # Mock orders
        mock_orders = Mock()
        mock_orders.records_readable = pd.DataFrame(order_data)
        mock_portfolio.orders = mock_orders

        # Mock positions
        mock_positions = Mock()
        mock_positions.records_readable = pd.DataFrame(position_data)
        mock_portfolio.positions = mock_positions

        # Mock portfolio metrics
        mock_portfolio.total_return.return_value = 0.15
        mock_portfolio.sharpe_ratio.return_value = 1.2
        mock_portfolio.max_drawdown.return_value = -0.05

        # Add required _data_pd attribute for timestamp mapping
        dates = pd.date_range("2023-01-01", periods=100, freq="D")
        mock_portfolio._data_pd = pd.DataFrame({"Date": dates})

        return mock_portfolio

    def test_filename_generation_sma(self):
        """Test filename generation for SMA strategy."""
        config = self.test_configs["sma_config"]
        expected = "BTC-USD_D_SMA_20_50.json"
        actual = generate_trade_filename(config, "json")
        self.assertEqual(actual, expected)

    def test_filename_generation_macd(self):
        """Test filename generation for MACD strategy."""
        config = self.test_configs["macd_config"]
        expected = "MSTR_D_MACD_12_26_9_SL_0.0500.json"
        actual = generate_trade_filename(config, "json")
        self.assertEqual(actual, expected)

    def test_filename_generation_ema_hourly_short(self):
        """Test filename generation for hourly EMA short strategy."""
        config = self.test_configs["ema_hourly_config"]
        expected = "ETH-USD_H_EMA_12_26_SHORT.json"
        actual = generate_trade_filename(config, "json")
        self.assertEqual(actual, expected)

    def test_filename_generation_synthetic_ticker(self):
        """Test filename generation with synthetic ticker."""
        config = {
            "TICKER": "STRK/MSTR",
            "STRATEGY_TYPE": "SMA",
            "fast_period": 10,
            "slow_period": 20,
        }
        expected = "STRK_MSTR_D_SMA_10_20.json"
        actual = generate_trade_filename(config, "json")
        self.assertEqual(actual, expected)

    def test_filename_generation_ticker_list(self):
        """Test filename generation with ticker list."""
        config = {
            "TICKER": ["BTC-USD"],
            "STRATEGY_TYPE": "EMA",
            "FAST_PERIOD": 5,
            "SLOW_PERIOD": 15,
        }
        expected = "BTC-USD_D_EMA_5_15.json"
        actual = generate_trade_filename(config, "json")
        self.assertEqual(actual, expected)

    def test_extract_trade_history(self):
        """Test trade history extraction."""
        trades_df = extract_trade_history(self.mock_portfolio)

        self.assertIsInstance(trades_df, pd.DataFrame)
        self.assertEqual(len(trades_df), 2)

        # Check enriched columns are added
        expected_columns = [
            "Entry Timestamp",
            "Exit Timestamp",
            "Avg Entry Price",
            "Avg Exit Price",
            "Size",
            "PnL",
            "Return",
            "Direction",
            "Status",
            "Duration",
            "Duration_Days",
            "Entry_Month",
            "Entry_Year",
            "Entry_Quarter",
            "Trade_Type",
            "Cumulative_PnL",
            "Trade_Number",
            "Rolling_Avg_Return",
            "Rolling_Win_Rate",
        ]

        for col in expected_columns:
            self.assertIn(col, trades_df.columns)

    def test_extract_orders_history(self):
        """Test orders history extraction."""
        orders_df = extract_orders_history(self.mock_portfolio)

        self.assertIsInstance(orders_df, pd.DataFrame)
        self.assertEqual(len(orders_df), 4)

        expected_columns = [
            "Order Id",
            "Column",
            "Timestamp",
            "Size",
            "Price",
            "Fees",
            "Side",
        ]
        for col in expected_columns:
            self.assertIn(col, orders_df.columns)

    def test_extract_positions_history(self):
        """Test positions history extraction."""
        positions_df = extract_positions_history(self.mock_portfolio)

        self.assertIsInstance(positions_df, pd.DataFrame)
        self.assertEqual(len(positions_df), 2)

        expected_columns = [
            "Position Id",
            "Column",
            "Size",
            "Entry Timestamp",
            "Avg Entry Price",
            "Entry Fees",
            "Exit Timestamp",
            "Avg Exit Price",
            "Exit Fees",
            "PnL",
            "Return",
            "Direction",
            "Status",
        ]

        for col in expected_columns:
            self.assertIn(col, positions_df.columns)

    def test_categorize_trade_performance(self):
        """Test trade performance categorization."""
        test_cases = [
            (0.08, "Big Winner"),
            (0.03, "Winner"),
            (0.005, "Breakeven"),
            (-0.02, "Loser"),
            (-0.08, "Big Loser"),
            (None, "Unknown"),
        ]

        for return_val, expected in test_cases:
            result = _categorize_trade_performance(return_val)
            self.assertEqual(result, expected)

    def test_extract_strategy_parameters_sma(self):
        """Test strategy parameter extraction for SMA."""
        config = self.test_configs["sma_config"]
        params = _extract_strategy_parameters(config, "SMA")
        expected = ["20", "50"]
        self.assertEqual(params, expected)

    def test_extract_strategy_parameters_macd(self):
        """Test strategy parameter extraction for MACD."""
        config = self.test_configs["macd_config"]
        params = _extract_strategy_parameters(config, "MACD")
        expected = ["12", "26", "9"]
        self.assertEqual(params, expected)

    def test_extract_all_strategy_parameters(self):
        """Test extraction of all strategy parameters."""
        config = {
            "fast_period": 20,
            "slow_period": 50,
            "STOP_LOSS": 0.05,
            "RSI_WINDOW": 14,
            "OTHER_PARAM": "ignored",
        }

        params = _extract_all_strategy_parameters(config)
        expected = {
            "fast_period": 20,
            "slow_period": 50,
            "stop_loss": 0.05,
            "rsi_window": 14,
        }
        self.assertEqual(params, expected)

    def test_analyze_trade_performance(self):
        """Test trade performance analysis."""
        # Create sample trade data
        trade_data = pd.DataFrame(
            {
                "Status": ["Closed", "Closed", "Closed", "Open"],
                "Return": [0.05, -0.02, 0.01, 0.03],
                "PnL": [50, -20, 10, 30],
                "Duration_Days": [5, 3, 7, None],
                "Trade_Type": ["Winner", "Loser", "Winner", "Winner"],
            }
        )

        analytics = analyze_trade_performance(trade_data)

        self.assertEqual(analytics["total_trades"], 4)
        self.assertEqual(analytics["closed_trades"], 3)
        self.assertEqual(analytics["open_trades"], 1)
        self.assertAlmostEqual(analytics["win_rate"], 66.67, places=1)
        self.assertEqual(analytics["total_pnl"], 40)
        self.assertAlmostEqual(analytics["avg_trade_duration"], 5.0)

    def test_create_comprehensive_trade_history(self):
        """Test comprehensive trade history creation."""
        config = self.test_configs["sma_config"]
        trade_history = create_comprehensive_trade_history(self.mock_portfolio, config)

        # Check structure
        self.assertIn("metadata", trade_history)
        self.assertIn("trades", trade_history)
        self.assertIn("orders", trade_history)
        self.assertIn("positions", trade_history)
        self.assertIn("analytics", trade_history)

        # Check metadata structure
        metadata = trade_history["metadata"]
        self.assertIn("export_timestamp", metadata)
        self.assertIn("strategy_config", metadata)
        self.assertIn("portfolio_summary", metadata)

        # Check strategy config
        strategy_config = metadata["strategy_config"]
        self.assertEqual(strategy_config["ticker"], "BTC-USD")
        self.assertEqual(strategy_config["timeframe"], "D")
        self.assertEqual(strategy_config["strategy_type"], "SMA")

        # Check data counts
        self.assertEqual(len(trade_history["trades"]), 2)
        self.assertEqual(len(trade_history["orders"]), 4)
        self.assertEqual(len(trade_history["positions"]), 2)

    def test_export_trade_history_json(self):
        """Test JSON export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            config["BASE_DIR"] = temp_dir

            success = export_trade_history(
                self.mock_portfolio, config, export_type="json"
            )

            self.assertTrue(success)

            # Check file was created
            expected_filename = generate_trade_filename(config, "json")
            expected_path = os.path.join(
                temp_dir, "json", "trade_history", expected_filename
            )
            self.assertTrue(os.path.exists(expected_path))

            # Check JSON structure
            with open(expected_path) as f:
                data = json.load(f)

            self.assertIn("metadata", data)
            self.assertIn("trades", data)
            self.assertIn("orders", data)
            self.assertIn("positions", data)
            self.assertIn("analytics", data)

    def test_export_trade_history_skip_if_current(self):
        """Test that export is skipped if current file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            config["BASE_DIR"] = temp_dir

            # First export
            success1 = export_trade_history(
                self.mock_portfolio, config, export_type="json"
            )
            self.assertTrue(success1)

            expected_filename = generate_trade_filename(config, "json")
            expected_path = os.path.join(
                temp_dir, "json", "trade_history", expected_filename
            )

            # Get file modification time
            original_mtime = os.path.getmtime(expected_path)

            # Small delay to ensure timestamp difference would be detectable
            import time

            time.sleep(0.1)

            # Second export should be skipped
            success2 = export_trade_history(
                self.mock_portfolio, config, export_type="json"
            )
            self.assertTrue(success2)

            # File should not have been modified
            current_mtime = os.path.getmtime(expected_path)
            self.assertEqual(original_mtime, current_mtime)

    def test_export_trade_history_force_refresh(self):
        """Test that force_refresh bypasses current file check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            config["BASE_DIR"] = temp_dir

            # First export
            success1 = export_trade_history(
                self.mock_portfolio, config, export_type="json"
            )
            self.assertTrue(success1)

            expected_filename = generate_trade_filename(config, "json")
            expected_path = os.path.join(
                temp_dir, "json", "trade_history", expected_filename
            )

            # Get file modification time
            original_mtime = os.path.getmtime(expected_path)

            # Small delay to ensure timestamp difference
            import time

            time.sleep(0.1)

            # Force refresh should regenerate the file
            success2 = export_trade_history(
                self.mock_portfolio, config, export_type="json", force_refresh=True
            )
            self.assertTrue(success2)

            # File should have been modified
            current_mtime = os.path.getmtime(expected_path)
            self.assertGreater(current_mtime, original_mtime)

    def test_export_trade_history_csv_legacy(self):
        """Test legacy CSV export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            config["BASE_DIR"] = temp_dir

            success = export_trade_history(
                self.mock_portfolio, config, export_type="csv"
            )

            self.assertTrue(success)

            # Check files were created
            base_filename = generate_trade_filename(config, "csv")
            trade_history_dir = os.path.join(temp_dir, "json", "trade_history")

            trades_file = os.path.join(
                trade_history_dir, base_filename.replace(".csv", "_trades.csv")
            )
            orders_file = os.path.join(
                trade_history_dir, base_filename.replace(".csv", "_orders.csv")
            )
            positions_file = os.path.join(
                trade_history_dir, base_filename.replace(".csv", "_positions.csv")
            )

            self.assertTrue(os.path.exists(trades_file))
            self.assertTrue(os.path.exists(orders_file))
            self.assertTrue(os.path.exists(positions_file))

    def test_csv_export_optimization_not_affected(self):
        """Test that CSV export is not affected by JSON optimization (since it doesn't use the current file check)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            config["BASE_DIR"] = temp_dir

            # First CSV export
            success1 = export_trade_history(
                self.mock_portfolio, config, export_type="csv"
            )
            self.assertTrue(success1)

            base_filename = generate_trade_filename(config, "csv")
            trade_history_dir = os.path.join(temp_dir, "json", "trade_history")
            trades_file = os.path.join(
                trade_history_dir, base_filename.replace(".csv", "_trades.csv")
            )

            self.assertTrue(os.path.exists(trades_file))
            original_mtime = os.path.getmtime(trades_file)

            import time

            time.sleep(0.1)

            # Second CSV export (CSV doesn't have optimization, so file should be regenerated)
            success2 = export_trade_history(
                self.mock_portfolio, config, export_type="csv"
            )
            self.assertTrue(success2)

            # File should have been modified (CSV doesn't skip)
            current_mtime = os.path.getmtime(trades_file)
            self.assertGreater(current_mtime, original_mtime)

    def test_empty_portfolio_handling(self):
        """Test handling of empty portfolio data."""
        # Create mock portfolio with no trades
        empty_portfolio = Mock(spec=vbt.Portfolio)

        # Mock empty trades
        mock_trades = Mock()
        mock_trades.records_readable = pd.DataFrame()
        empty_portfolio.trades = mock_trades

        # Mock empty orders
        mock_orders = Mock()
        mock_orders.records_readable = pd.DataFrame()
        empty_portfolio.orders = mock_orders

        # Mock empty positions
        mock_positions = Mock()
        mock_positions.records_readable = pd.DataFrame()
        empty_portfolio.positions = mock_positions

        # Test extraction functions
        trades_df = extract_trade_history(empty_portfolio)
        orders_df = extract_orders_history(empty_portfolio)
        positions_df = extract_positions_history(empty_portfolio)

        self.assertTrue(trades_df.empty)
        self.assertTrue(orders_df.empty)
        self.assertTrue(positions_df.empty)

    def test_error_handling_in_extraction(self):
        """Test error handling in data extraction."""
        # Create mock portfolio that raises exceptions
        error_portfolio = Mock(spec=vbt.Portfolio)
        error_portfolio.trades.records_readable.side_effect = Exception("Test error")

        # Should return empty DataFrame and not raise
        trades_df = extract_trade_history(error_portfolio)
        self.assertTrue(trades_df.empty)

    def test_missing_config_parameters(self):
        """Test handling of missing configuration parameters."""
        minimal_config = {"TICKER": "TEST"}

        # Should handle missing parameters gracefully
        filename = generate_trade_filename(minimal_config, "json")
        self.assertTrue(filename.endswith(".json"))
        self.assertIn("TEST", filename)

    def test_enrich_trade_data_edge_cases(self):
        """Test trade data enrichment edge cases."""
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        enriched_empty = _enrich_trade_data(empty_df, self.mock_portfolio)
        self.assertTrue(enriched_empty.empty)

        # Test with DataFrame missing timestamp columns
        minimal_df = pd.DataFrame(
            {"Return": [0.05, -0.02], "PnL": [50, -20], "Status": ["Closed", "Closed"]}
        )
        enriched_minimal = _enrich_trade_data(minimal_df, self.mock_portfolio)
        self.assertEqual(len(enriched_minimal), 2)
        self.assertIn("Trade_Type", enriched_minimal.columns)

    def test_enrich_position_data_edge_cases(self):
        """Test position data enrichment edge cases."""
        # Test with empty DataFrame
        empty_df = pd.DataFrame()
        enriched_empty = _enrich_position_data(empty_df)
        self.assertTrue(enriched_empty.empty)

        # Test with minimal data
        minimal_df = pd.DataFrame(
            {"Return": [0.03, -0.01], "Status": ["Closed", "Open"]}
        )
        enriched_minimal = _enrich_position_data(minimal_df)
        self.assertEqual(len(enriched_minimal), 2)
        self.assertIn("Position_Type", enriched_minimal.columns)

    def test_is_trade_history_current(self):
        """Test trade history currency check."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test_file.json")

            # Non-existent file should return False
            self.assertFalse(_is_trade_history_current(test_file))

            # Create file and test
            with open(test_file, "w") as f:
                f.write("{}")

            # File created today should return True
            self.assertTrue(_is_trade_history_current(test_file))

            # Simulate old file by changing modification time
            import time

            old_time = time.time() - (24 * 60 * 60 + 1)  # More than 24 hours ago
            os.utime(test_file, (old_time, old_time))

            # Old file should return False
            self.assertFalse(_is_trade_history_current(test_file))

    def test_is_trade_history_current_edge_cases(self):
        """Test edge cases for trade history currency check."""
        # Test with invalid file path
        self.assertFalse(_is_trade_history_current("/nonexistent/path/file.json"))

        # Test with directory instead of file
        with tempfile.TemporaryDirectory() as temp_dir:
            self.assertFalse(_is_trade_history_current(temp_dir))

    def test_export_trade_history_with_base_dir_override(self):
        """Test export with base_dir parameter override."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            # Don't set BASE_DIR in config
            if "BASE_DIR" in config:
                del config["BASE_DIR"]

            # Use base_dir parameter instead
            success = export_trade_history(
                self.mock_portfolio, config, export_type="json", base_dir=temp_dir
            )

            self.assertTrue(success)

            expected_filename = generate_trade_filename(config, "json")
            expected_path = os.path.join(
                temp_dir, "json", "trade_history", expected_filename
            )
            self.assertTrue(os.path.exists(expected_path))

    def test_export_optimization_with_config_changes(self):
        """Test that optimization works correctly when configs change."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First config
            config1 = {
                "BASE_DIR": temp_dir,
                "TICKER": "BTC-USD",
                "STRATEGY_TYPE": "SMA",
                "fast_period": 10,
                "slow_period": 20,
            }

            # Export first strategy
            success1 = export_trade_history(
                self.mock_portfolio, config1, export_type="json"
            )
            self.assertTrue(success1)

            filename1 = generate_trade_filename(config1, "json")
            path1 = os.path.join(temp_dir, "json", "trade_history", filename1)
            self.assertTrue(os.path.exists(path1))

            # Different config (different filename)
            config2 = {
                "BASE_DIR": temp_dir,
                "TICKER": "ETH-USD",  # Different ticker
                "STRATEGY_TYPE": "SMA",
                "fast_period": 10,
                "slow_period": 20,
            }

            # Export second strategy (should create new file, not skip)
            success2 = export_trade_history(
                self.mock_portfolio, config2, export_type="json"
            )
            self.assertTrue(success2)

            filename2 = generate_trade_filename(config2, "json")
            path2 = os.path.join(temp_dir, "json", "trade_history", filename2)
            self.assertTrue(os.path.exists(path2))

            # Verify different filenames
            self.assertNotEqual(filename1, filename2)

    def test_export_skip_behavior_with_config_export_history_false(self):
        """Test that optimization still works when EXPORT_TRADE_HISTORY is in config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.test_configs["sma_config"].copy()
            config["BASE_DIR"] = temp_dir
            config[
                "EXPORT_TRADE_HISTORY"
            ] = False  # Should not affect the function directly

            # First export
            success1 = export_trade_history(
                self.mock_portfolio, config, export_type="json"
            )
            self.assertTrue(success1)

            expected_filename = generate_trade_filename(config, "json")
            expected_path = os.path.join(
                temp_dir, "json", "trade_history", expected_filename
            )

            original_mtime = os.path.getmtime(expected_path)

            import time

            time.sleep(0.1)

            # Second export should still be skipped
            success2 = export_trade_history(
                self.mock_portfolio, config, export_type="json"
            )
            self.assertTrue(success2)

            # File should not have been modified
            current_mtime = os.path.getmtime(expected_path)
            self.assertEqual(original_mtime, current_mtime)


class TestTradeHistoryExporterIntegration(unittest.TestCase):
    """Integration tests for trade history exporter."""

    def test_backtest_integration(self):
        """Test integration with backtest_strategy function."""
        # This would require more complex setup with actual VectorBT portfolio
        # For now, we'll test the import and basic functionality
        try:
            from app.tools.backtest_strategy import backtest_strategy

            # Test that the import works and function exists
            self.assertTrue(callable(backtest_strategy))
        except ImportError:
            self.skipTest("backtest_strategy not available for integration test")

    def test_export_directory_creation(self):
        """Test that export directories are created properly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                "BASE_DIR": temp_dir,
                "TICKER": "TEST",
                "STRATEGY_TYPE": "SMA",
                "fast_period": 10,
                "slow_period": 20,
            }

            # Create mock portfolio
            mock_portfolio = Mock(spec=vbt.Portfolio)
            mock_trades = Mock()
            mock_trades.records_readable = pd.DataFrame(
                {
                    "Entry Timestamp": ["2023-01-01"],
                    "Exit Timestamp": ["2023-01-02"],
                    "Avg Entry Price": [100],
                    "Avg Exit Price": [105],
                    "Size": [1],
                    "PnL": [5],
                    "Return": [0.05],
                    "Direction": ["Long"],
                    "Status": ["Closed"],
                }
            )
            mock_portfolio.trades = mock_trades

            mock_orders = Mock()
            mock_orders.records_readable = pd.DataFrame()
            mock_portfolio.orders = mock_orders

            mock_positions = Mock()
            mock_positions.records_readable = pd.DataFrame()
            mock_portfolio.positions = mock_positions

            # Mock portfolio metrics
            mock_portfolio.total_return.return_value = 0.05
            mock_portfolio.sharpe_ratio.return_value = 1.0
            mock_portfolio.max_drawdown.return_value = -0.02

            # Mock trades count and win rate
            mock_trades.count.return_value = 1
            mock_trades.win_rate.return_value = 1.0

            # Test export
            success = export_trade_history(mock_portfolio, config, export_type="json")

            self.assertTrue(success)

            # Check directory was created
            export_dir = os.path.join(temp_dir, "json", "trade_history")
            self.assertTrue(os.path.exists(export_dir))


if __name__ == "__main__":
    unittest.main()
