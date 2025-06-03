"""Base classes for concurrency module testing.

Provides common functionality and fixtures for all concurrency tests.
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, patch

from app.concurrency.config import ConcurrencyConfig
from app.concurrency.error_handling import get_error_registry


class ConcurrencyTestCase(unittest.TestCase):
    """Base test case for concurrency module tests."""

    def setUp(self):
        """Set up test environment."""
        # Create temporary directories
        self.test_dir = Path(tempfile.mkdtemp())
        self.log_dir = self.test_dir / "logs"
        self.json_dir = self.test_dir / "json" / "concurrency"
        self.csv_dir = self.test_dir / "csv" / "portfolios"

        # Create directories
        self.log_dir.mkdir(parents=True)
        self.json_dir.mkdir(parents=True)
        self.csv_dir.mkdir(parents=True)

        # Mock logger
        self.log_mock = Mock()

        # Clear error registry
        registry = get_error_registry()
        registry.errors.clear()
        registry.operation_counts.clear()

        # Default test configuration
        self.default_config: ConcurrencyConfig = {
            "PORTFOLIO": "test_portfolio.json",
            "BASE_DIR": str(self.log_dir),
            "REFRESH": True,
            "VISUALIZATION": False,
            "REPORT_INCLUDES": {
                "TICKER_METRICS": True,
                "STRATEGIES": True,
                "STRATEGY_RELATIONSHIPS": True,
            },
        }

    def tearDown(self):
        """Clean up test environment."""
        # Remove temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_portfolio_file(
        self, strategies: List[Dict[str, Any]], filename: str = "test_portfolio.json"
    ) -> str:
        """Create a portfolio file in the test directory.

        Args:
            strategies: List of strategy configurations
            filename: Name of the portfolio file

        Returns:
            Full path to the created file
        """
        file_path = self.test_dir / filename

        if filename.endswith(".json"):
            with open(file_path, "w") as f:
                json.dump(strategies, f, indent=2)
        else:
            # CSV format
            import csv

            with open(file_path, "w", newline="") as f:
                if strategies:
                    # Map JSON fields to CSV headers
                    csv_strategies = []
                    for s in strategies:
                        csv_strategy = {
                            "Ticker": s.get("ticker", ""),
                            "Use SMA": s.get("type", "") == "SMA",
                            "Short Window": s.get("short_window", 0),
                            "Long Window": s.get("long_window", 0),
                            "Signal Window": s.get("signal_window", 0),
                            "Allocation [%]": s.get("allocation", 0),
                            "Stop Loss [%]": s.get("stop_loss", 0),
                        }
                        csv_strategies.append(csv_strategy)

                    writer = csv.DictWriter(f, fieldnames=csv_strategies[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_strategies)

        return str(file_path)

    def assert_report_exists(self, portfolio_name: str) -> Dict[str, Any]:
        """Assert that a JSON report was created and return its contents.

        Args:
            portfolio_name: Base name of the portfolio

        Returns:
            Report contents as dictionary
        """
        report_path = self.json_dir / f"{Path(portfolio_name).stem}.json"
        self.assertTrue(report_path.exists(), f"Report file not found: {report_path}")

        with open(report_path) as f:
            return json.load(f)

    def assert_optimization_report_exists(self, portfolio_name: str) -> Dict[str, Any]:
        """Assert that an optimization report was created.

        Args:
            portfolio_name: Base name of the portfolio

        Returns:
            Optimization report contents
        """
        report_path = (
            self.json_dir
            / "optimization"
            / f"{Path(portfolio_name).stem}_optimization.json"
        )
        self.assertTrue(
            report_path.exists(), f"Optimization report not found: {report_path}"
        )

        with open(report_path) as f:
            return json.load(f)

    def create_mock_price_data(
        self, tickers: List[str], periods: int = 100
    ) -> Dict[str, Dict[str, List[float]]]:
        """Create mock price data for testing.

        Args:
            tickers: List of ticker symbols
            periods: Number of time periods

        Returns:
            Dictionary of price data by ticker
        """
        import numpy as np

        price_data = {}
        for ticker in tickers:
            # Generate simple trending data
            base = 100.0
            trend = np.linspace(0, 10, periods)
            noise = np.random.normal(0, 2, periods)
            prices = base + trend + noise

            price_data[ticker] = {
                "open": prices.tolist(),
                "high": (prices * 1.01).tolist(),
                "low": (prices * 0.99).tolist(),
                "close": prices.tolist(),
            }

        return price_data


class MockDataMixin:
    """Mixin providing mock data generation for tests."""

    @staticmethod
    def create_ma_strategy(
        ticker: str = "BTC-USD",
        strategy_type: str = "SMA",
        short_window: int = 10,
        long_window: int = 30,
        allocation: float = 100.0,
    ) -> Dict[str, Any]:
        """Create a mock MA strategy configuration."""
        return {
            "ticker": ticker,
            "timeframe": "D",
            "type": strategy_type,
            "direction": "long",
            "short_window": short_window,
            "long_window": long_window,
            "allocation": allocation,
        }

    @staticmethod
    def create_macd_strategy(
        ticker: str = "BTC-USD",
        short_window: int = 12,
        long_window: int = 26,
        signal_window: int = 9,
        allocation: float = 100.0,
    ) -> Dict[str, Any]:
        """Create a mock MACD strategy configuration."""
        return {
            "ticker": ticker,
            "timeframe": "D",
            "type": "MACD",
            "direction": "long",
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "allocation": allocation,
        }

    @staticmethod
    def create_mock_signals(periods: int = 100, signal_rate: float = 0.3) -> List[int]:
        """Create mock trading signals.

        Args:
            periods: Number of time periods
            signal_rate: Probability of signal being active

        Returns:
            List of signal values (0 or 1)
        """
        import numpy as np

        np.random.seed(42)
        return (np.random.random(periods) < signal_rate).astype(int).tolist()

    @staticmethod
    def create_mock_portfolio_data(num_strategies: int = 3) -> List[Dict[str, Any]]:
        """Create mock portfolio data."""
        strategies = []
        allocation_per_strategy = 100 / num_strategies

        for i in range(num_strategies):
            strategy = {
                "ticker": f"TEST{i+1}",
                "timeframe": "D",
                "type": "SMA" if i % 2 == 0 else "EMA",
                "direction": "long",
                "short_window": 10 + i * 5,
                "long_window": 30 + i * 10,
                "allocation": allocation_per_strategy,
            }
            strategies.append(strategy)

        return strategies


class AsyncTestMixin:
    """Mixin for testing asynchronous operations."""

    def run_async_test(self, coro):
        """Run an async test function."""
        import asyncio

        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)


# Performance testing utilities
class PerformanceTestMixin:
    """Mixin for performance testing."""

    def time_operation(self, func, *args, **kwargs):
        """Time an operation and return result with timing."""
        import time

        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        return result, duration

    def assert_performance(self, func, max_duration: float, *args, **kwargs):
        """Assert that an operation completes within time limit."""
        result, duration = self.time_operation(func, *args, **kwargs)
        self.assertLess(
            duration,
            max_duration,
            f"Operation took {duration:.2f}s, expected < {max_duration}s",
        )
        return result
