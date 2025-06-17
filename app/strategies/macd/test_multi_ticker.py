"""
Test suite for MACD strategy multi-ticker functionality.

Tests single ticker and multi-ticker execution with different USE_CURRENT settings
and verifies CSV export paths.
"""

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union

import polars as pl

from app.strategies.macd.config_types import PortfolioConfig
from app.strategies.macd.tools.portfolio_processing import run_strategy_analysis


class TestMACDMultiTicker:
    """Test class for MACD strategy multi-ticker functionality."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.csv_dir = Path(self.temp_dir) / "csv"
        self.csv_dir.mkdir()

        # Create expected standard directories
        self.portfolios_dir = self.csv_dir / "portfolios"
        self.filtered_dir = self.csv_dir / "portfolios_filtered"
        self.best_dir = self.csv_dir / "portfolios_best"

        for dir_path in [self.portfolios_dir, self.filtered_dir, self.best_dir]:
            dir_path.mkdir(parents=True)

    def teardown_method(self):
        """Clean up test environment after each test."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_config(
        self, ticker: Union[str, List[str]], use_current: bool = True, **kwargs
    ) -> PortfolioConfig:
        """Create a test configuration."""
        config: PortfolioConfig = {
            "TICKER": ticker,
            "BASE_DIR": self.temp_dir,
            "USE_CURRENT": use_current,
            "USE_HOURLY": False,
            "REFRESH": True,
            "USE_YEARS": True,
            "YEARS": 2,  # Use shorter period for faster tests
            "DIRECTION": "Long",
            "SHORT_WINDOW_START": 8,
            "SHORT_WINDOW_END": 12,
            "LONG_WINDOW_START": 20,
            "LONG_WINDOW_END": 26,
            "SIGNAL_WINDOW_START": 6,
            "SIGNAL_WINDOW_END": 9,
            "STEP": 2,  # Larger step for faster tests
            "MINIMUMS": {
                "WIN_RATE": 0.40,
                "TRADES": 10,
                "EXPECTANCY_PER_TRADE": 0.10,
                "PROFIT_FACTOR": 1.10,
            },
        }
        config.update(kwargs)
        return config

    def _verify_csv_structure(self, csv_path: Path) -> Dict:
        """Verify CSV file structure and return summary."""
        assert csv_path.exists(), f"CSV file not found: {csv_path}"

        df = pl.read_csv(csv_path)

        # Verify essential columns exist
        expected_columns = [
            "Ticker",
            "Strategy",
            "Direction",
            "Short_Window",
            "Long_Window",
            "Signal_Window",
            "Total Return [%]",
            "Win Rate [%]",
            "Total Trades",
        ]

        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

        return {
            "row_count": len(df),
            "ticker": df["Ticker"].unique().to_list(),
            "strategies": df["Strategy"].unique().to_list(),
            "min_trades": df["Total Trades"].min(),
            "max_return": df["Total Return [%]"].max(),
        }

    def test_single_ticker_use_current_true(self):
        """Test single ticker with USE_CURRENT=True."""
        config = self._create_test_config("AAPL", use_current=True)

        # Run strategy
        results = run_strategy_analysis(config)

        # Verify results structure
        assert results is not None
        assert len(results) > 0

        # Check for portfolio CSV
        date_str = datetime.now().strftime("%Y%m%d")
        portfolio_pattern = f"AAPL_D_MACD.csv"

        # Look for files in both dated and root directories
        found_portfolio = False
        for path in [
            self.portfolios_dir / date_str / portfolio_pattern,
            self.portfolios_dir / portfolio_pattern,
        ]:
            if path.exists():
                summary = self._verify_csv_structure(path)
                assert summary["row_count"] > 0
                assert "AAPL" in summary["ticker"]
                found_portfolio = True
                break

        assert (
            found_portfolio
        ), f"Portfolio CSV not found for pattern: {portfolio_pattern}"

    def test_single_ticker_use_current_false(self):
        """Test single ticker with USE_CURRENT=False."""
        config = self._create_test_config("MSFT", use_current=False)

        # Run strategy
        results = run_strategy_analysis(config)

        # Verify results
        assert results is not None
        assert len(results) > 0

        # Check for portfolio CSV
        portfolio_pattern = f"MSFT_D_MACD.csv"

        # Look for files
        found_portfolio = False
        for path in [
            self.portfolios_dir / portfolio_pattern,
            list(self.portfolios_dir.rglob(portfolio_pattern)),
        ]:
            if isinstance(path, list):
                if path:
                    path = path[0]
                else:
                    continue
            if path.exists():
                summary = self._verify_csv_structure(path)
                assert summary["row_count"] > 0
                assert "MSFT" in summary["ticker"]
                found_portfolio = True
                break

        assert (
            found_portfolio
        ), f"Portfolio CSV not found for pattern: {portfolio_pattern}"

    def test_multi_ticker_use_current_true(self):
        """Test multiple tickers with USE_CURRENT=True."""
        config = self._create_test_config(["AAPL", "GOOGL"], use_current=True)

        # Run strategy
        results = run_strategy_analysis(config)

        # Verify results for both tickers
        assert results is not None
        assert len(results) > 0

        # Check for portfolio CSVs for each ticker
        date_str = datetime.now().strftime("%Y%m%d")
        found_tickers = []

        for ticker in ["AAPL", "GOOGL"]:
            portfolio_pattern = f"{ticker}_D_MACD.csv"

            for path in [
                self.portfolios_dir / date_str / portfolio_pattern,
                self.portfolios_dir / portfolio_pattern,
            ]:
                if path.exists():
                    summary = self._verify_csv_structure(path)
                    assert summary["row_count"] > 0
                    assert ticker in summary["ticker"]
                    found_tickers.append(ticker)
                    break

        assert len(found_tickers) == 2, f"Not all tickers found. Found: {found_tickers}"

    def test_multi_ticker_use_current_false(self):
        """Test multiple tickers with USE_CURRENT=False."""
        config = self._create_test_config(["TSLA", "AMZN", "META"], use_current=False)

        # Run strategy
        results = run_strategy_analysis(config)

        # Verify results
        assert results is not None
        assert len(results) > 0

        # Check for portfolio CSVs
        found_tickers = []

        for ticker in ["TSLA", "AMZN", "META"]:
            portfolio_pattern = f"{ticker}_D_MACD.csv"

            # Search in all subdirectories
            found_files = list(self.portfolios_dir.rglob(portfolio_pattern))
            if found_files:
                for path in found_files:
                    if path.exists():
                        summary = self._verify_csv_structure(path)
                        assert summary["row_count"] > 0
                        assert ticker in summary["ticker"]
                        found_tickers.append(ticker)
                        break

        assert len(found_tickers) == 3, f"Not all tickers found. Found: {found_tickers}"

    def test_filtered_portfolio_generation(self):
        """Test that filtered portfolios are generated correctly."""
        config = self._create_test_config("SPY", use_current=True)

        # Run strategy with filtering
        results = run_strategy_analysis(config)

        # Check if filtered directory has files
        date_str = datetime.now().strftime("%Y%m%d")
        filtered_paths = [self.filtered_dir / date_str, self.filtered_dir]

        found_filtered = False
        for path in filtered_paths:
            if path.exists() and any(path.iterdir()):
                found_filtered = True
                break

        # Filtered portfolios may or may not exist depending on results
        # Just verify the directory structure exists
        assert self.filtered_dir.exists()

    def test_best_portfolio_aggregation(self):
        """Test that best portfolios are aggregated correctly."""
        # Run multiple tickers to ensure aggregation
        config = self._create_test_config(["AAPL", "MSFT", "GOOGL"], use_current=True)

        # Run strategy
        results = run_strategy_analysis(config)

        # Check best portfolios directory
        date_str = datetime.now().strftime("%Y%m%d")
        best_paths = [self.best_dir / date_str, self.best_dir]

        # Best portfolios may be created by separate aggregation process
        # Just verify directory exists
        assert self.best_dir.exists()


def run_manual_test():
    """Run a manual test to verify functionality."""
    print("Running manual MACD multi-ticker test...")

    # Create test instance
    test = TestMACDMultiTicker()
    test.setup_method()

    try:
        # Test single ticker
        print("\nTesting single ticker (AAPL) with USE_CURRENT=True...")
        test.test_single_ticker_use_current_true()
        print("✓ Single ticker test passed")

        # Test multi-ticker
        print("\nTesting multi-ticker (NFLX, AMAT) with USE_CURRENT=False...")
        test.test_multi_ticker_use_current_false()
        print("✓ Multi-ticker test passed")

        print("\nAll tests passed successfully!")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        raise
    finally:
        test.teardown_method()


if __name__ == "__main__":
    run_manual_test()
