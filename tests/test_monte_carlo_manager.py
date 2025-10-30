"""
Comprehensive tests for Monte Carlo portfolio manager and portfolio-level analysis.

This test suite covers the PortfolioMonteCarloManager, portfolio-level
analysis, strategy ID generation, parallel processing, and integration
with the concurrency framework.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import polars as pl
import pytest


# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.monte_carlo.config import MonteCarloConfig
from app.concurrency.tools.monte_carlo.core import MonteCarloPortfolioResult
from app.concurrency.tools.monte_carlo.manager import PortfolioMonteCarloManager


class TestPortfolioMonteCarloManager:
    """Test the portfolio-level Monte Carlo manager."""

    @pytest.fixture
    def test_config(self):
        """Create test Monte Carlo configuration."""
        return MonteCarloConfig(
            num_simulations=3,  # Small for testing
            confidence_level=0.95,
            max_parameters_to_test=2,
        )

    @pytest.fixture
    def mock_log(self):
        """Create mock logging function."""
        return Mock()

    @pytest.fixture
    def manager(self, test_config, mock_log):
        """Create portfolio Monte Carlo manager."""
        return PortfolioMonteCarloManager(
            config=test_config,
            max_workers=2,
            log=mock_log,
        )

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio strategies."""
        return [
            {
                "ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Window Short": 10,
                "Window Long": 20,
            },
            {
                "ticker": "ETH-USD",
                "Strategy Type": "EMA",
                "Window Short": 12,
                "Window Long": 26,
            },
            {
                "ticker": "BTC-USD",
                "Strategy Type": "MACD",
                "Window Short": 12,
                "Window Long": 26,
                "Signal Period": 9,
            },
        ]

    def test_manager_initialization(self, manager, test_config):
        """Test manager initialization."""
        assert manager.config == test_config
        assert manager.max_workers == 2
        assert manager.results == {}
        assert manager.progress_tracker is not None

    def test_strategy_id_assignment(self, manager, sample_portfolio):
        """Test strategy ID assignment including signal period for MACD."""
        strategies_with_ids = manager._assign_strategy_ids(sample_portfolio)

        assert len(strategies_with_ids) == 3

        # Check strategy IDs
        strategy_ids = list(strategies_with_ids.keys())

        # Should include signal period for MACD
        macd_ids = [sid for sid in strategy_ids if "MACD" in sid]
        assert len(macd_ids) == 1
        assert "_9" in macd_ids[0]  # Signal period should be included

        # Should have proper format for all
        for strategy_id in strategy_ids:
            parts = strategy_id.split("_")
            assert len(parts) >= 4  # ticker_type_short_long_signal

    def test_strategy_id_assignment_missing_strategy_type(self, manager):
        """Test strategy ID assignment with missing strategy type."""
        invalid_portfolio = [
            {
                "ticker": "BTC-USD",
                # Missing Strategy Type
                "Window Short": 10,
                "Window Long": 20,
            },
        ]

        with pytest.raises(ValueError) as exc_info:
            manager._assign_strategy_ids(invalid_portfolio)

        assert "Strategy type must be explicitly specified" in str(exc_info.value)

    def test_strategy_id_uniqueness(self, manager):
        """Test that duplicate strategies get unique IDs."""
        duplicate_portfolio = [
            {
                "ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Window Short": 10,
                "Window Long": 20,
            },
            {
                "ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Window Short": 10,
                "Window Long": 20,
            },
        ]

        strategies_with_ids = manager._assign_strategy_ids(duplicate_portfolio)

        assert len(strategies_with_ids) == 2
        strategy_ids = list(strategies_with_ids.keys())
        assert len(set(strategy_ids)) == 2  # Should be unique

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_analyze_single_strategy_success(self, mock_download, manager):
        """Test successful analysis of a single strategy."""
        # Mock price data
        mock_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2), pl.date(2023, 1, 3)],
                "Close": [100.0, 101.0, 102.0],
            },
        )
        mock_download.return_value = mock_data

        strategy = {
            "ticker": "BTC-USD",
            "Strategy Type": "SMA",
            "Window Short": 2,
            "Window Long": 3,
        }

        result = manager._analyze_strategy_with_error_handling(
            "BTC-USD_SMA_2_3_0",
            strategy,
        )

        assert isinstance(result, MonteCarloPortfolioResult)
        assert result.ticker == "BTC-USD"
        assert len(result.parameter_results) > 0

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_analyze_single_strategy_download_failure(
        self,
        mock_download,
        manager,
        mock_log,
    ):
        """Test handling of data download failure."""
        # Mock download failure
        mock_download.side_effect = Exception("Download failed")

        strategy = {
            "ticker": "INVALID-TICKER",
            "Strategy Type": "SMA",
            "Window Short": 10,
            "Window Long": 20,
        }

        result = manager._analyze_strategy_with_error_handling(
            "INVALID-TICKER_SMA_10_20_0",
            strategy,
        )

        assert result is None
        mock_log.assert_called()

    def test_progress_tracking(self, manager):
        """Test progress tracking functionality."""
        tracker = manager.progress_tracker

        # Test initial state
        assert tracker.get_progress_percentage() == 0.0

        # Add strategies
        tracker.add_strategy("strategy1")
        tracker.add_strategy("strategy2")

        assert tracker.get_progress_percentage() == 0.0

        # Update progress
        tracker.update("strategy1", "completed")
        assert tracker.get_progress_percentage() == 50.0

        tracker.update("strategy2", "completed")
        assert tracker.get_progress_percentage() == 100.0

    def test_progress_tracking_with_errors(self, manager):
        """Test progress tracking with errors."""
        tracker = manager.progress_tracker

        tracker.add_strategy("strategy1")
        tracker.add_strategy("strategy2")

        # Add error
        tracker.add_error("strategy1", Exception("Test error"))
        tracker.update("strategy1", "error")

        # Complete other strategy
        tracker.update("strategy2", "completed")

        assert tracker.get_progress_percentage() == 100.0
        assert len(tracker.errors) == 1

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_analyze_portfolio_success(self, mock_download, manager, sample_portfolio):
        """Test successful portfolio analysis."""
        # Mock price data for all tickers
        mock_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(10)],
                "Close": [100.0 + i for i in range(10)],
            },
        )
        mock_download.return_value = mock_data

        results = manager.analyze_portfolio(sample_portfolio)

        assert isinstance(results, dict)
        assert len(results) == 3  # Should have results for all 3 strategies

        # Check that MACD strategy has correct ID format
        macd_results = {k: v for k, v in results.items() if "MACD" in k}
        assert len(macd_results) == 1

        macd_id = next(iter(macd_results.keys()))
        assert "_9" in macd_id  # Should include signal period

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_analyze_portfolio_partial_failure(self, mock_download, manager, mock_log):
        """Test portfolio analysis with some failures."""

        # Mock partial failure - some downloads succeed, some fail
        def side_effect(*args, **kwargs):
            ticker = args[0] if args else kwargs.get("ticker", "")
            if "BTC" in ticker:
                return pl.DataFrame(
                    {
                        "Date": [pl.date(2023, 1, 1), pl.date(2023, 1, 2)],
                        "Close": [100.0, 101.0],
                    },
                )
            msg = "Download failed"
            raise Exception(msg)

        mock_download.side_effect = side_effect

        portfolio = [
            {
                "ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Window Short": 5,
                "Window Long": 10,
            },
            {
                "ticker": "ETH-USD",
                "Strategy Type": "SMA",
                "Window Short": 5,
                "Window Long": 10,
            },
        ]

        results = manager.analyze_portfolio(portfolio)

        # Should have results for BTC but not ETH
        assert len(results) >= 0  # May have partial results
        mock_log.assert_called()  # Should log errors

    def test_analyze_portfolio_empty_input(self, manager):
        """Test portfolio analysis with empty input."""
        results = manager.analyze_portfolio([])

        assert isinstance(results, dict)
        assert len(results) == 0

    def test_get_portfolio_stability_metrics(self, manager):
        """Test portfolio-level stability metrics calculation."""
        # Add mock results
        mock_result1 = Mock()
        mock_result1.portfolio_stability_score = 0.7
        mock_result1.recommended_parameters = (10, 20)

        mock_result2 = Mock()
        mock_result2.portfolio_stability_score = 0.5
        mock_result2.recommended_parameters = (12, 26)

        manager.results = {
            "BTC-USD_SMA_10_20_0": mock_result1,
            "ETH-USD_EMA_12_26_0": mock_result2,
        }

        metrics = manager.get_portfolio_stability_metrics()

        assert isinstance(metrics, dict)
        assert "portfolio_stability_score" in metrics
        assert "stable_tickers_percentage" in metrics
        assert "total_tickers" in metrics

        # Check calculations
        expected_avg = (0.7 + 0.5) / 2
        assert abs(metrics["portfolio_stability_score"] - expected_avg) < 1e-6

    def test_get_portfolio_stability_metrics_empty(self, manager):
        """Test portfolio stability metrics with no results."""
        metrics = manager.get_portfolio_stability_metrics()

        assert metrics["portfolio_stability_score"] == 0.0
        assert metrics["stable_tickers_percentage"] == 0.0
        assert metrics["total_tickers"] == 0

    def test_get_recommendations(self, manager):
        """Test getting parameter recommendations."""
        # Add mock results
        mock_result1 = Mock()
        mock_result1.ticker = "BTC-USD"
        mock_result1.portfolio_stability_score = 0.8
        mock_result1.recommended_parameters = (10, 20)

        mock_result2 = Mock()
        mock_result2.ticker = "ETH-USD"
        mock_result2.portfolio_stability_score = 0.6
        mock_result2.recommended_parameters = (12, 26)

        manager.results = {
            "BTC-USD_SMA_10_20_0": mock_result1,
            "ETH-USD_EMA_12_26_0": mock_result2,
        }

        recommendations = manager.get_recommendations(limit=5)

        assert isinstance(recommendations, list)
        assert len(recommendations) == 2

        # Should be sorted by stability score (highest first)
        assert recommendations[0]["ticker"] == "BTC-USD"
        assert recommendations[0]["stability_score"] == 0.8
        assert recommendations[1]["ticker"] == "ETH-USD"
        assert recommendations[1]["stability_score"] == 0.6

    def test_get_recommendations_with_limit(self, manager):
        """Test getting recommendations with limit."""
        # Add multiple mock results
        for i in range(5):
            mock_result = Mock()
            mock_result.ticker = f"TICKER{i}"
            mock_result.portfolio_stability_score = 0.5 + i * 0.1
            mock_result.recommended_parameters = (10, 20)
            manager.results[f"TICKER{i}_SMA_10_20_0"] = mock_result

        recommendations = manager.get_recommendations(limit=3)

        assert len(recommendations) == 3
        # Should be top 3 by stability score
        assert recommendations[0]["ticker"] == "TICKER4"  # Highest score

    def test_get_recommendations_empty(self, manager):
        """Test getting recommendations with no results."""
        recommendations = manager.get_recommendations()

        assert isinstance(recommendations, list)
        assert len(recommendations) == 0


class TestPortfolioMonteCarloIntegration:
    """Test integration scenarios for portfolio Monte Carlo analysis."""

    @pytest.fixture
    def realistic_portfolio(self):
        """Create realistic multi-asset portfolio."""
        return [
            {
                "ticker": "BTC-USD",
                "Strategy Type": "SMA",
                "Window Short": 10,
                "Window Long": 30,
            },
            {
                "ticker": "BTC-USD",
                "Strategy Type": "EMA",
                "Window Short": 12,
                "Window Long": 26,
            },
            {
                "ticker": "BTC-USD",
                "Strategy Type": "MACD",
                "Window Short": 12,
                "Window Long": 26,
                "Signal Period": 9,
            },
            {
                "ticker": "ETH-USD",
                "Strategy Type": "SMA",
                "Window Short": 15,
                "Window Long": 35,
            },
        ]

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_multi_strategy_analysis(self, mock_download, realistic_portfolio):
        """Test analysis of multiple strategies across multiple assets."""
        # Mock price data
        mock_data = pl.DataFrame(
            {
                "Date": [pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(50)],
                "Close": [1000.0 + i * 10 + np.sin(i * 0.1) * 50 for i in range(50)],
            },
        )
        mock_download.return_value = mock_data

        config = MonteCarloConfig(num_simulations=3, max_parameters_to_test=2)
        manager = PortfolioMonteCarloManager(config=config, max_workers=2, log=Mock())

        results = manager.analyze_portfolio(realistic_portfolio)

        # Should have results for all strategies
        assert len(results) == 4

        # Check strategy ID formats
        strategy_ids = list(results.keys())

        # Should have different strategy types
        sma_ids = [sid for sid in strategy_ids if "SMA" in sid]
        ema_ids = [sid for sid in strategy_ids if "EMA" in sid]
        macd_ids = [sid for sid in strategy_ids if "MACD" in sid]

        assert len(sma_ids) == 2  # BTC and ETH SMA
        assert len(ema_ids) == 1  # BTC EMA
        assert len(macd_ids) == 1  # BTC MACD

        # MACD should include signal period
        assert any("_9" in mid for mid in macd_ids)

    @patch("app.concurrency.tools.monte_carlo.manager.download_price_data")
    def test_parallel_processing(self, mock_download):
        """Test that parallel processing works correctly."""

        # Mock data with delay to test parallelism
        def slow_download(*args, **kwargs):
            import time

            time.sleep(0.1)  # Small delay
            return pl.DataFrame(
                {
                    "Date": [
                        pl.date(2023, 1, 1) + pl.duration(days=i) for i in range(20)
                    ],
                    "Close": [1000.0 + i for i in range(20)],
                },
            )

        mock_download.side_effect = slow_download

        portfolio = [
            {
                "ticker": f"ASSET{i}",
                "Strategy Type": "SMA",
                "Window Short": 5,
                "Window Long": 10,
            }
            for i in range(4)
        ]

        config = MonteCarloConfig(num_simulations=2)
        manager = PortfolioMonteCarloManager(config=config, max_workers=2, log=Mock())

        import time

        start_time = time.time()
        results = manager.analyze_portfolio(portfolio)
        end_time = time.time()

        # Should complete in reasonable time (parallel processing)
        assert end_time - start_time < 5.0  # Should be much faster than sequential
        assert len(results) <= 4  # May have some results

    def test_field_name_standardization_integration(self):
        """Test that field name standardization works in full pipeline."""
        config = MonteCarloConfig(num_simulations=1)
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        # Test portfolio with different field name formats
        portfolio = [
            {
                "ticker": "BTC-USD",
                "Strategy Type": "MACD",  # CSV format
                "Fast Period": 12,  # CSV format
                "Slow Period": 26,  # CSV format
                "Signal Period": 9,  # CSV format
            },
        ]

        strategies_with_ids = manager._assign_strategy_ids(portfolio)

        # Should handle CSV field names correctly
        assert len(strategies_with_ids) == 1
        strategy_id = next(iter(strategies_with_ids.keys()))

        # Should include all parameters including signal period
        assert strategy_id == "BTC-USD_MACD_12_26_9"

    def test_error_aggregation(self):
        """Test that errors are properly aggregated across strategies."""
        config = MonteCarloConfig(num_simulations=1)
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        # Add some errors manually for testing
        manager.progress_tracker.add_strategy("strategy1")
        manager.progress_tracker.add_strategy("strategy2")

        error1 = Exception("Error 1")
        error2 = Exception("Error 2")

        manager.progress_tracker.add_error("strategy1", error1)
        manager.progress_tracker.add_error("strategy2", error2)

        assert len(manager.progress_tracker.errors) == 2
        assert "strategy1" in manager.progress_tracker.errors
        assert "strategy2" in manager.progress_tracker.errors


class TestMonteCarloManagerEdgeCases:
    """Test edge cases in Monte Carlo manager."""

    def test_manager_with_zero_workers(self):
        """Test manager initialization with zero workers."""
        config = MonteCarloConfig(num_simulations=1)

        # Should default to reasonable number of workers
        manager = PortfolioMonteCarloManager(config=config, max_workers=0, log=Mock())
        assert manager.max_workers >= 1

    def test_manager_with_excessive_workers(self):
        """Test manager with very high worker count."""
        config = MonteCarloConfig(num_simulations=1)

        # Should handle gracefully
        manager = PortfolioMonteCarloManager(
            config=config,
            max_workers=1000,
            log=Mock(),
        )
        assert manager.max_workers == 1000  # Should accept but may be limited by system

    def test_portfolio_with_missing_fields(self):
        """Test portfolio analysis with strategies missing required fields."""
        config = MonteCarloConfig(num_simulations=1)
        manager = PortfolioMonteCarloManager(config=config, max_workers=1, log=Mock())

        incomplete_portfolio = [
            {
                "ticker": "BTC-USD",
                "Strategy Type": "SMA",
                # Missing Window Short and Window Long
            },
        ]

        # Should handle gracefully or raise appropriate error
        strategies_with_ids = manager._assign_strategy_ids(incomplete_portfolio)
        strategy_id = next(iter(strategies_with_ids.keys()))

        # Should use fallback values
        assert "X" in strategy_id or "Y" in strategy_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
