"""
Comprehensive Portfolio Analysis Tests for MA Cross Strategy

This module provides comprehensive end-to-end testing for the MA Cross strategy
portfolio analysis system, following the established testing framework patterns.
Integrated into the existing test infrastructure for the trading platform.
"""

from datetime import datetime, timedelta
from pathlib import Path
import tempfile
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import polars as pl
import pytest

from app.strategies.ma_cross.exceptions import MACrossError
from app.tools.orchestration.portfolio_orchestrator import PortfolioOrchestrator


@pytest.mark.e2e
@pytest.mark.strategy
@pytest.mark.slow
class TestMACrossPortfolioComprehensive:
    """Comprehensive portfolio analysis tests for MA Cross strategy."""

    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for test files."""
        with tempfile.TemporaryDirectory(prefix="ma_cross_test_") as base_temp:
            base_path = Path(base_temp)
            dirs = {
                "base": base_path,
                "portfolios": base_path / "csv" / "portfolios" / "20250615",
                "portfolios_filtered": base_path
                / "csv"
                / "portfolios_filtered"
                / "20250615",
                "portfolios_best": base_path / "csv" / "portfolios_best",
                "price_data": base_path / "csv" / "price_data",
                "logs": base_path / "logs" / "ma_cross_test",
            }

            # Create directory structure
            for dir_path in dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)

            yield dirs

    @pytest.fixture
    def mock_log(self):
        """Mock logging function for testing."""
        return Mock()

    @pytest.fixture
    def comprehensive_test_config(self, temp_dirs):
        """Configuration for comprehensive portfolio testing."""
        return {
            "TICKER": ["GLD", "CL=F", "BTC-USD", "SPY", "QQQ", "DX-Y.NYB"],
            "WINDOWS": 21,  # Reduced for test performance
            "BASE_DIR": str(temp_dirs["base"]),
            "REFRESH": True,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "DIRECTION": "Long",
            "USE_HOURLY": False,
            "USE_YEARS": False,
            "YEARS": 15,
            "USE_SYNTHETIC": False,
            "USE_CURRENT": False,  # No current position filtering
            "MINIMUMS": {},  # No minimums applied
            "SORT_BY": "Total Return [%]",
            "SORT_ASC": False,
            "USE_GBM": False,
            "USE_MA": True,
            "DISPLAY_RESULTS": True,
        }

    @pytest.fixture
    def realistic_market_data(self):
        """Generate realistic market data for different asset classes."""

        def generate_asset_data(
            ticker: str,
            days: int = 1000,
            base_price: float = 100.0,
        ) -> pd.DataFrame:
            """Generate realistic OHLCV data for different asset types."""
            np.random.seed(hash(ticker) % 2**32)  # Deterministic but ticker-specific

            # Asset-specific parameters
            asset_params = {
                "GLD": {"volatility": 0.015, "drift": 0.0002, "base": 120.0},
                "CL=F": {"volatility": 0.025, "drift": 0.0001, "base": 70.0},
                "BTC-USD": {"volatility": 0.045, "drift": 0.0008, "base": 35000.0},
                "SPY": {"volatility": 0.012, "drift": 0.0003, "base": 420.0},
                "QQQ": {"volatility": 0.018, "drift": 0.0004, "base": 350.0},
                "DX-Y.NYB": {"volatility": 0.008, "drift": 0.0001, "base": 103.0},
            }

            params = asset_params.get(
                ticker,
                {"volatility": 0.02, "drift": 0.0002, "base": base_price},
            )

            # Generate dates
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            dates = pd.date_range(start=start_date, end=end_date, freq="D")[:days]

            # Generate price series using geometric Brownian motion
            dt = 1 / 252  # Daily time step (252 trading days per year)
            returns = np.random.normal(
                params["drift"] * dt,
                params["volatility"] * np.sqrt(dt),
                days,
            )

            # Create price series
            prices = [params["base"]]
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))

            # Generate OHLC from close prices
            closes = np.array(prices)
            opens = np.roll(closes, 1)
            opens[0] = params["base"]

            # Add intraday volatility for highs and lows
            intraday_range = params["volatility"] * 0.3
            highs = closes * (1 + np.abs(np.random.normal(0, intraday_range, days)))
            lows = closes * (1 - np.abs(np.random.normal(0, intraday_range, days)))

            # Ensure OHLC relationships are maintained
            highs = np.maximum(highs, np.maximum(opens, closes))
            lows = np.minimum(lows, np.minimum(opens, closes))

            # Generate realistic volume
            base_volume = {
                "GLD": 8000000,
                "CL=F": 150000,
                "BTC-USD": 25000000000,
                "SPY": 60000000,
                "QQQ": 45000000,
                "DX-Y.NYB": 1000000,
            }.get(ticker, 10000000)

            volumes = np.random.lognormal(np.log(base_volume), 0.5, days).astype(int)

            return pd.DataFrame(
                {
                    "Date": dates,
                    "Open": opens,
                    "High": highs,
                    "Low": lows,
                    "Close": closes,
                    "Volume": volumes,
                },
            )

        return generate_asset_data

    @pytest.fixture
    def mock_yfinance_download(self, realistic_market_data):
        """Mock yfinance download with realistic data."""

        def mock_download_func(ticker, *args, **kwargs):
            # Handle special ticker names for filenames
            ticker.replace("=", "_").replace("-", "_")
            data = realistic_market_data(ticker)
            data = data.set_index("Date")
            return data

        return mock_download_func

    def test_comprehensive_portfolio_analysis_workflow(
        self,
        comprehensive_test_config,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test complete portfolio analysis workflow with multiple tickers and strategies."""

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            # Initialize orchestrator
            orchestrator = PortfolioOrchestrator(mock_log)

            # Execute the complete workflow
            success = orchestrator.run(comprehensive_test_config)

            # Verify execution success
            assert success, "Portfolio analysis workflow should complete successfully"

            # Verify log calls were made
            assert mock_log.call_count > 0, "Logging should be active during execution"

    def test_portfolio_file_generation(
        self,
        comprehensive_test_config,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test that all expected portfolio files are generated."""

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            orchestrator = PortfolioOrchestrator(mock_log)
            success = orchestrator.run(comprehensive_test_config)

            assert success, "Portfolio generation should succeed"

            # Check that portfolio files were created
            tickers = comprehensive_test_config["TICKER"]
            strategies = comprehensive_test_config["STRATEGY_TYPES"]

            expected_files = []
            for ticker in tickers:
                ticker_clean = ticker.replace("=", "_").replace("-", "_")
                for strategy in strategies:
                    expected_files.append(f"{ticker_clean}_D_{strategy}.csv")

            # Verify files exist in portfolios directory
            portfolios_dir = temp_dirs["base"] / "csv" / "portfolios"
            actual_files = []
            for file_path in portfolios_dir.rglob("*.csv"):
                actual_files.append(file_path.name)

            # Check that we have files for all tickers and strategies
            for expected_file in expected_files:
                matching_files = [f for f in actual_files if expected_file in f]
                assert (
                    len(matching_files) > 0
                ), f"Expected portfolio file {expected_file} not found"

    def test_best_portfolio_aggregation(
        self,
        comprehensive_test_config,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test that best portfolio aggregation works correctly."""

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            orchestrator = PortfolioOrchestrator(mock_log)
            success = orchestrator.run(comprehensive_test_config)

            assert success, "Portfolio aggregation should succeed"

            # Check for best portfolio files
            best_dir = temp_dirs["base"] / "csv" / "portfolios_best"
            best_files = list(best_dir.glob("*.csv"))

            assert (
                len(best_files) > 0
            ), "At least one best portfolio file should be created"

            # Verify best portfolio has expected structure
            best_file = best_files[0]
            df = pl.read_csv(best_file)

            # Check required columns exist
            required_cols = [
                "Ticker",
                "Strategy Type",
                "Total Return [%]",
                "Win Rate [%]",
                "Allocation [%]",
            ]
            for col in required_cols:
                assert (
                    col in df.columns
                ), f"Required column {col} missing from best portfolio"

            # Verify we have results from multiple tickers
            unique_tickers = df["Ticker"].unique().to_list()
            assert (
                len(unique_tickers) > 1
            ), "Best portfolio should include multiple tickers"

    @pytest.mark.performance
    def test_execution_performance(
        self,
        comprehensive_test_config,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test execution performance meets expectations."""

        import time

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            start_time = time.time()

            orchestrator = PortfolioOrchestrator(mock_log)
            success = orchestrator.run(comprehensive_test_config)

            execution_time = time.time() - start_time

            assert success, "Performance test should complete successfully"
            assert (
                execution_time < 120
            ), f"Execution should complete within 120s, took {execution_time:.2f}s"

    def test_configuration_validation(self, temp_dirs, mock_log):
        """Test that invalid configurations are properly handled."""

        # Test with missing required fields
        invalid_config = {
            "TICKER": [],  # Empty ticker list
            "WINDOWS": 10,
            "BASE_DIR": str(temp_dirs["base"]),
        }

        orchestrator = PortfolioOrchestrator(mock_log)

        # Should handle gracefully without crashing
        try:
            result = orchestrator.run(invalid_config)
            # Either succeeds with no results or handles error gracefully
            assert isinstance(result, bool), "Should return boolean result"
        except Exception as e:
            # If it raises an exception, it should be a known type
            assert isinstance(
                e,
                MACrossError | ValueError | KeyError,
            ), f"Unexpected exception type: {type(e)}"

    def test_use_current_false_behavior(
        self,
        comprehensive_test_config,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test that USE_CURRENT=False includes all results without current position filtering."""

        # Ensure USE_CURRENT is False
        comprehensive_test_config["USE_CURRENT"] = False

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            orchestrator = PortfolioOrchestrator(mock_log)
            success = orchestrator.run(comprehensive_test_config)

            assert success, "Execution with USE_CURRENT=False should succeed"

            # Verify that results are not filtered by current signals
            # Check portfolio files have expected number of rows (190 for WINDOWS=21)
            portfolios_dir = temp_dirs["base"] / "csv" / "portfolios"
            portfolio_files = list(portfolios_dir.rglob("*.csv"))

            assert len(portfolio_files) > 0, "Portfolio files should be generated"

            # Check file content
            for file_path in portfolio_files[:3]:  # Check first few files
                df = pl.read_csv(file_path)
                # With WINDOWS=21, we expect 190 combinations (21*20/2)
                assert (
                    len(df) > 50
                ), f"Portfolio file {file_path.name} should have substantial results"

    def test_no_minimums_behavior(
        self,
        comprehensive_test_config,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test that empty MINIMUMS includes all results without filtering."""

        # Ensure MINIMUMS is empty
        comprehensive_test_config["MINIMUMS"] = {}

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            orchestrator = PortfolioOrchestrator(mock_log)
            success = orchestrator.run(comprehensive_test_config)

            assert success, "Execution with no minimums should succeed"

            # Verify filtered files exist and contain results
            filtered_dir = temp_dirs["base"] / "csv" / "portfolios_filtered"
            filtered_files = list(filtered_dir.rglob("*.csv"))

            assert (
                len(filtered_files) > 0
            ), "Filtered portfolio files should be generated"

            # Check that filtered files contain substantial results (not heavily filtered)
            for file_path in filtered_files[:3]:  # Check first few files
                df = pl.read_csv(file_path)
                assert (
                    len(df) > 10
                ), f"Filtered file {file_path.name} should contain results without strict filtering"

    @pytest.mark.error_handling
    def test_error_handling_network_failure(
        self,
        comprehensive_test_config,
        temp_dirs,
        mock_log,
    ):
        """Test error handling when data download fails."""

        def mock_download_failure(*args, **kwargs):
            msg = "Network connection failed"
            raise ConnectionError(msg)

        with patch("yfinance.download", side_effect=mock_download_failure):
            orchestrator = PortfolioOrchestrator(mock_log)

            # Should handle network errors gracefully
            try:
                result = orchestrator.run(comprehensive_test_config)
                # Either returns False or handles the error gracefully
                assert isinstance(
                    result,
                    bool,
                ), "Should return boolean even on network failure"
            except Exception as e:
                # If it raises an exception, it should be a known error type
                assert isinstance(
                    e,
                    MACrossError | ConnectionError,
                ), f"Unexpected exception: {type(e)}"

    def test_special_character_ticker_handling(
        self,
        mock_yfinance_download,
        temp_dirs,
        mock_log,
    ):
        """Test handling of tickers with special characters (futures, forex)."""

        special_config = {
            "TICKER": ["CL=F", "BTC-USD", "DX-Y.NYB"],  # Futures, crypto, forex
            "WINDOWS": 10,
            "BASE_DIR": str(temp_dirs["base"]),
            "REFRESH": True,
            "STRATEGY_TYPES": ["SMA"],
            "USE_CURRENT": False,
            "MINIMUMS": {},
            "USE_MA": True,
        }

        with patch("yfinance.download", side_effect=mock_yfinance_download):
            orchestrator = PortfolioOrchestrator(mock_log)
            success = orchestrator.run(special_config)

            assert success, "Should handle special character tickers successfully"

            # Verify files are created with proper naming (special chars converted)
            portfolios_dir = temp_dirs["base"] / "csv" / "portfolios"
            actual_files = [f.name for f in portfolios_dir.rglob("*.csv")]

            # Check for converted filenames
            expected_patterns = ["CL_F_D_SMA", "BTC_USD_D_SMA", "DX_Y.NYB_D_SMA"]
            for pattern in expected_patterns:
                matching_files = [f for f in actual_files if pattern in f]
                assert len(matching_files) > 0, f"File with pattern {pattern} not found"


# Pytest markers for test categorization
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.strategy,
    pytest.mark.portfolio,
]
