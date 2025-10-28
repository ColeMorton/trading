"""
Performance and data validation tests for trade history export.
"""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import Mock

import pandas as pd
import vectorbt as vbt

from app.tools.trade_history_exporter import (
    analyze_trade_performance,
    create_comprehensive_trade_history,
    export_trade_history,
    extract_orders_history,
    extract_positions_history,
    extract_trade_history,
    generate_trade_filename,
)


class TestTradeHistoryPerformance(unittest.TestCase):
    """Performance tests for trade history export functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.large_portfolio = self._create_large_portfolio()
        self.config = {
            "TICKER": "BTC-USD",
            "STRATEGY_TYPE": "SMA",
            "fast_period": 20,
            "slow_period": 50,
            "BASE_DIR": ".",
        }

    def _create_large_portfolio(self, num_trades=1000):
        """Create a mock portfolio with many trades for performance testing."""
        # Generate large dataset
        dates = pd.date_range("2020-01-01", periods=num_trades * 2, freq="D")

        trade_data = {
            "Entry Timestamp": [dates[i * 2] for i in range(num_trades)],
            "Exit Timestamp": [dates[i * 2 + 1] for i in range(num_trades)],
            "Avg Entry Price": [100 + i * 0.1 for i in range(num_trades)],
            "Avg Exit Price": [100 + i * 0.1 + (i % 10 - 5) for i in range(num_trades)],
            "Size": [0.1 + (i % 10) * 0.01 for i in range(num_trades)],
            "PnL": [(i % 10 - 5) * 0.1 for i in range(num_trades)],
            "Return": [(i % 10 - 5) * 0.001 for i in range(num_trades)],
            "Direction": ["Long"] * num_trades,
            "Status": ["Closed"] * (num_trades - 10)
            + ["Open"] * 10,  # Some open trades
        }

        order_data = {
            "Order Id": list(range(num_trades * 2)),
            "Column": [0] * (num_trades * 2),
            "Timestamp": [dates[i] for i in range(num_trades * 2)],
            "Size": [0.1 + (i % 10) * 0.01 for i in range(num_trades * 2)],
            "Price": [100 + i * 0.1 for i in range(num_trades * 2)],
            "Fees": [0.001] * (num_trades * 2),
            "Side": ["Buy", "Sell"] * num_trades,
        }

        position_data = {
            "Position Id": list(range(num_trades)),
            "Column": [0] * num_trades,
            "Size": [0.1 + (i % 10) * 0.01 for i in range(num_trades)],
            "Entry Timestamp": [dates[i * 2] for i in range(num_trades)],
            "Avg Entry Price": [100 + i * 0.1 for i in range(num_trades)],
            "Entry Fees": [0.001] * num_trades,
            "Exit Timestamp": [dates[i * 2 + 1] for i in range(num_trades)],
            "Avg Exit Price": [100 + i * 0.1 + (i % 10 - 5) for i in range(num_trades)],
            "Exit Fees": [0.001] * num_trades,
            "PnL": [(i % 10 - 5) * 0.1 for i in range(num_trades)],
            "Return": [(i % 10 - 5) * 0.001 for i in range(num_trades)],
            "Direction": ["Long"] * num_trades,
            "Status": ["Closed"] * (num_trades - 10) + ["Open"] * 10,
        }

        # Create mock portfolio
        mock_portfolio = Mock(spec=vbt.Portfolio)

        # Mock trades
        mock_trades = Mock()
        mock_trades.records_readable = pd.DataFrame(trade_data)
        mock_trades.count.return_value = num_trades
        mock_trades.win_rate.return_value = 0.6
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
        mock_portfolio.total_return.return_value = 0.25
        mock_portfolio.sharpe_ratio.return_value = 1.5
        mock_portfolio.max_drawdown.return_value = -0.08

        return mock_portfolio

    def test_extract_trade_history_performance(self):
        """Test performance of trade history extraction with large dataset."""
        start_time = time.time()

        trades_df = extract_trade_history(self.large_portfolio)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in reasonable time (< 5 seconds for 1000 trades)
        self.assertLess(
            execution_time,
            5.0,
            f"Trade history extraction too slow: {execution_time:.2f}s",
        )

        # Verify data integrity
        self.assertEqual(len(trades_df), 1000)
        self.assertIn("Duration", trades_df.columns)
        self.assertIn("Trade_Type", trades_df.columns)
        self.assertIn("Cumulative_PnL", trades_df.columns)

    def test_extract_orders_performance(self):
        """Test performance of orders extraction."""
        start_time = time.time()

        orders_df = extract_orders_history(self.large_portfolio)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should be very fast
        self.assertLess(
            execution_time, 1.0, f"Orders extraction too slow: {execution_time:.2f}s",
        )
        self.assertEqual(len(orders_df), 2000)  # 2 orders per trade

    def test_extract_positions_performance(self):
        """Test performance of positions extraction."""
        start_time = time.time()

        positions_df = extract_positions_history(self.large_portfolio)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should be fast
        self.assertLess(
            execution_time, 2.0, f"Positions extraction too slow: {execution_time:.2f}s",
        )
        self.assertEqual(len(positions_df), 1000)

    def test_comprehensive_trade_history_performance(self):
        """Test performance of comprehensive trade history creation."""
        start_time = time.time()

        trade_history = create_comprehensive_trade_history(
            self.large_portfolio, self.config,
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in reasonable time
        self.assertLess(
            execution_time,
            10.0,
            f"Comprehensive trade history too slow: {execution_time:.2f}s",
        )

        # Verify structure
        self.assertIn("metadata", trade_history)
        self.assertIn("trades", trade_history)
        self.assertIn("orders", trade_history)
        self.assertIn("positions", trade_history)
        self.assertIn("analytics", trade_history)

        # Verify data counts
        self.assertEqual(len(trade_history["trades"]), 1000)
        self.assertEqual(len(trade_history["orders"]), 2000)
        self.assertEqual(len(trade_history["positions"]), 1000)

    def test_json_export_performance(self):
        """Test performance of JSON export with large dataset."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = self.config.copy()
            config["BASE_DIR"] = temp_dir

            start_time = time.time()

            success = export_trade_history(
                self.large_portfolio, config, export_type="json",
            )

            end_time = time.time()
            execution_time = end_time - start_time

            # Should complete in reasonable time
            self.assertLess(
                execution_time, 15.0, f"JSON export too slow: {execution_time:.2f}s",
            )
            self.assertTrue(success)

            # Check file was created and has reasonable size
            filename = generate_trade_filename(config, "json")
            filepath = os.path.join(temp_dir, "json", "trade_history", filename)

            self.assertTrue(os.path.exists(filepath))

            file_size = os.path.getsize(filepath)
            # Should be substantial but not excessive (rough estimate)
            self.assertGreater(file_size, 100000)  # At least 100KB
            self.assertLess(file_size, 50000000)  # Less than 50MB

    def test_analyze_trade_performance_with_large_dataset(self):
        """Test trade performance analysis with large dataset."""
        # Create large trade DataFrame
        num_trades = 5000
        trade_data = pd.DataFrame(
            {
                "Status": ["Closed"] * (num_trades - 100) + ["Open"] * 100,
                "Return": [(i % 20 - 10) * 0.01 for i in range(num_trades)],
                "PnL": [(i % 20 - 10) * 10 for i in range(num_trades)],
                "Duration_Days": [i % 30 + 1 for i in range(num_trades)],
                "Trade_Type": [
                    ["Big Winner", "Winner", "Breakeven", "Loser", "Big Loser"][i % 5]
                    for i in range(num_trades)
                ],
            },
        )

        start_time = time.time()

        analytics = analyze_trade_performance(trade_data)

        end_time = time.time()
        execution_time = end_time - start_time

        # Should be very fast
        self.assertLess(
            execution_time,
            2.0,
            f"Trade performance analysis too slow: {execution_time:.2f}s",
        )

        # Verify analytics
        self.assertEqual(analytics["total_trades"], 5000)
        self.assertEqual(analytics["closed_trades"], 4900)
        self.assertEqual(analytics["open_trades"], 100)
        self.assertIn("win_rate", analytics)
        self.assertIn("profit_factor", analytics)
        self.assertIn("trade_type_distribution", analytics)

    def test_memory_usage_with_large_dataset(self):
        """Test memory usage remains reasonable with large datasets."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create very large portfolio
        very_large_portfolio = self._create_large_portfolio(num_trades=10000)

        # Perform operations
        trades_df = extract_trade_history(very_large_portfolio)
        orders_df = extract_orders_history(very_large_portfolio)
        positions_df = extract_positions_history(very_large_portfolio)

        # Create comprehensive history
        trade_history = create_comprehensive_trade_history(
            very_large_portfolio, self.config,
        )

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 500MB for 10k trades)
        self.assertLess(
            memory_increase,
            500,
            f"Memory usage too high: {memory_increase:.1f}MB increase",
        )

        # Clean up
        del trades_df, orders_df, positions_df, trade_history, very_large_portfolio

    def test_filename_generation_performance(self):
        """Test filename generation performance with many configurations."""
        configs = []
        for i in range(1000):
            configs.append(
                {
                    "TICKER": f"TEST-{i}",
                    "STRATEGY_TYPE": ["SMA", "EMA", "MACD"][i % 3],
                    "fast_period": 10 + (i % 20),
                    "slow_period": 30 + (i % 20),
                    "USE_HOURLY": i % 2 == 0,
                    "DIRECTION": ["Long", "Short"][i % 2],
                    "STOP_LOSS": 0.05 if i % 3 == 0 else None,
                },
            )

        start_time = time.time()

        filenames = [generate_trade_filename(config, "json") for config in configs]

        end_time = time.time()
        execution_time = end_time - start_time

        # Should be very fast
        self.assertLess(
            execution_time, 1.0, f"Filename generation too slow: {execution_time:.2f}s",
        )

        # All filenames should be unique
        self.assertEqual(len(set(filenames)), len(filenames))


class TestTradeHistoryDataValidation(unittest.TestCase):
    """Data validation tests for trade history export."""

    def test_json_schema_validation(self):
        """Test that exported JSON follows expected schema."""
        # Create mock portfolio
        mock_portfolio = Mock(spec=vbt.Portfolio)

        trade_data = pd.DataFrame(
            {
                "Entry Timestamp": ["2023-01-01", "2023-02-01"],
                "Exit Timestamp": ["2023-01-05", "2023-02-05"],
                "Avg Entry Price": [100.0, 105.0],
                "Avg Exit Price": [103.0, 102.0],
                "Size": [1.0, 0.5],
                "PnL": [3.0, -1.5],
                "Return": [0.03, -0.0286],
                "Direction": ["Long", "Long"],
                "Status": ["Closed", "Closed"],
            },
        )

        mock_trades = Mock()
        mock_trades.records_readable = trade_data
        mock_trades.count.return_value = 2
        mock_trades.win_rate.return_value = 0.5
        mock_portfolio.trades = mock_trades

        mock_orders = Mock()
        mock_orders.records_readable = pd.DataFrame()
        mock_portfolio.orders = mock_orders

        mock_positions = Mock()
        mock_positions.records_readable = pd.DataFrame()
        mock_portfolio.positions = mock_positions

        mock_portfolio.total_return.return_value = 0.15
        mock_portfolio.sharpe_ratio.return_value = 1.2
        mock_portfolio.max_drawdown.return_value = -0.05

        config = {
            "TICKER": "BTC-USD",
            "STRATEGY_TYPE": "SMA",
            "fast_period": 20,
            "slow_period": 50,
        }

        # Create comprehensive trade history
        trade_history = create_comprehensive_trade_history(mock_portfolio, config)

        # Validate JSON structure
        self.assertIsInstance(trade_history, dict)

        # Check required top-level keys
        required_keys = ["metadata", "trades", "orders", "positions", "analytics"]
        for key in required_keys:
            self.assertIn(key, trade_history)

        # Validate metadata structure
        metadata = trade_history["metadata"]
        self.assertIn("export_timestamp", metadata)
        self.assertIn("strategy_config", metadata)
        self.assertIn("portfolio_summary", metadata)

        # Validate strategy config
        strategy_config = metadata["strategy_config"]
        required_strategy_keys = [
            "ticker",
            "timeframe",
            "strategy_type",
            "direction",
            "parameters",
        ]
        for key in required_strategy_keys:
            self.assertIn(key, strategy_config)

        # Validate portfolio summary
        portfolio_summary = metadata["portfolio_summary"]
        required_summary_keys = [
            "total_return",
            "total_trades",
            "win_rate",
            "sharpe_ratio",
            "max_drawdown",
        ]
        for key in required_summary_keys:
            self.assertIn(key, portfolio_summary)

        # Validate trades data
        trades = trade_history["trades"]
        self.assertIsInstance(trades, list)
        self.assertEqual(len(trades), 2)

        if trades:
            trade = trades[0]
            required_trade_keys = [
                "Entry Timestamp",
                "Exit Timestamp",
                "Avg Entry Price",
                "Avg Exit Price",
                "Size",
                "PnL",
                "Return",
                "Direction",
                "Status",
            ]
            for key in required_trade_keys:
                self.assertIn(key, trade)

    def test_data_type_consistency(self):
        """Test that data types are consistent in exported JSON."""
        # Create test data with specific types
        mock_portfolio = Mock(spec=vbt.Portfolio)

        trade_data = pd.DataFrame(
            {
                "Entry Timestamp": pd.to_datetime(["2023-01-01", "2023-02-01"]),
                "Exit Timestamp": pd.to_datetime(["2023-01-05", "2023-02-05"]),
                "Avg Entry Price": [100.5, 105.75],
                "Avg Exit Price": [103.25, 102.0],
                "Size": [1.0, 0.5],
                "PnL": [3.25, -1.875],
                "Return": [0.03256, -0.02857],
                "Direction": ["Long", "Long"],
                "Status": ["Closed", "Closed"],
            },
        )

        mock_trades = Mock()
        mock_trades.records_readable = trade_data
        mock_trades.count.return_value = 2
        mock_trades.win_rate.return_value = 0.5
        mock_portfolio.trades = mock_trades

        mock_orders = Mock()
        mock_orders.records_readable = pd.DataFrame()
        mock_portfolio.orders = mock_orders

        mock_positions = Mock()
        mock_positions.records_readable = pd.DataFrame()
        mock_portfolio.positions = mock_positions

        mock_portfolio.total_return.return_value = 0.15234
        mock_portfolio.sharpe_ratio.return_value = 1.2567
        mock_portfolio.max_drawdown.return_value = -0.05123

        config = {
            "TICKER": "TEST",
            "STRATEGY_TYPE": "SMA",
            "fast_period": 10,
            "slow_period": 20,
        }

        trade_history = create_comprehensive_trade_history(mock_portfolio, config)

        # Convert to JSON and back to test serialization
        json_str = json.dumps(trade_history, default=str)
        parsed_data = json.loads(json_str)

        # Verify numeric values
        self.assertIsInstance(
            parsed_data["metadata"]["portfolio_summary"]["total_return"], float,
        )

        # Verify timestamp strings
        if parsed_data["trades"]:
            trade = parsed_data["trades"][0]
            self.assertIsInstance(trade["Entry Timestamp"], str)
            self.assertIsInstance(trade["Avg Entry Price"], float)
            self.assertIsInstance(trade["Size"], float)

    def test_edge_case_data_handling(self):
        """Test handling of edge cases in data."""
        mock_portfolio = Mock(spec=vbt.Portfolio)

        # Create data with edge cases
        trade_data = pd.DataFrame(
            {
                "Entry Timestamp": pd.to_datetime(["2023-01-01"]),
                "Exit Timestamp": pd.to_datetime(["NaT"]),  # Missing exit timestamp
                "Avg Entry Price": [100.0],
                "Avg Exit Price": [float("nan")],  # NaN exit price
                "Size": [0.0],  # Zero size
                "PnL": [float("inf")],  # Infinite PnL
                "Return": [float("-inf")],  # Negative infinite return
                "Direction": ["Long"],
                "Status": ["Open"],
            },
        )

        mock_trades = Mock()
        mock_trades.records_readable = trade_data
        mock_trades.count.return_value = 1
        mock_trades.win_rate.return_value = 0.0
        mock_portfolio.trades = mock_trades

        mock_orders = Mock()
        mock_orders.records_readable = pd.DataFrame()
        mock_portfolio.orders = mock_orders

        mock_positions = Mock()
        mock_positions.records_readable = pd.DataFrame()
        mock_portfolio.positions = mock_positions

        mock_portfolio.total_return.return_value = float("nan")
        mock_portfolio.sharpe_ratio.return_value = float("inf")
        mock_portfolio.max_drawdown.return_value = float("-inf")

        config = {"TICKER": "TEST", "STRATEGY_TYPE": "SMA"}

        # Should not raise exception
        trade_history = create_comprehensive_trade_history(mock_portfolio, config)

        # Should be serializable to JSON
        json_str = json.dumps(trade_history, default=str)
        self.assertIsInstance(json_str, str)


if __name__ == "__main__":
    unittest.main()
