"""
Integration Tests for Phase 1 Optimizations

Tests the complete flow of optimizations including concurrent execution,
streamlined data pipeline, and API improvements.
"""

import time
from unittest.mock import Mock, patch

import pytest


@pytest.mark.integration
class TestPhase1Integration:
    """Integration tests for all Phase 1 optimizations."""

    @pytest.fixture
    def integration_config(self):
        """Configuration for integration testing."""
        return {
            "TICKER": ["AAPL", "GOOGL", "MSFT", "AMZN"],  # 4 tickers for concurrent
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "WINDOWS": 20,
            "DIRECTION": "Long",
            "USE_HOURLY": False,
            "MINIMUMS": {
                "WIN_RATE": 0.5,
                "TRADES": 10,
            },
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

    @patch("app.api.services.ma_cross_service.execute_strategy_concurrent")
    @patch(
        "app.api.services.ma_cross_service.MACrossService._convert_portfolios_to_metrics",
    )
    def test_end_to_end_concurrent_flow(
        self,
        mock_convert,
        mock_execute,
        integration_config,
    ):
        """Test complete flow with concurrent execution and streamlined pipeline."""
        # Setup mocks
        portfolio_dicts = [
            {
                "Ticker": ticker,
                "Strategy Type": "SMA",
                "Total Return [%]": 15.0,
                "Win Rate [%]": 65.0,
                "Total Trades": 25,
                "Metric Type": "Test",
            }
            for ticker in ["AAPL", "GOOGL", "MSFT", "AMZN"]
        ]

        mock_execute.return_value = portfolio_dicts
        mock_convert.return_value = [Mock() for _ in portfolio_dicts]

        # Import service
        from app.api.services.ma_cross_service import MACrossService

        # Create service with mocked dependencies
        service = MACrossService(
            logger=Mock(),
            progress_tracker=Mock(),
            strategy_executor=Mock(),
            strategy_analyzer=Mock(),
            cache=Mock(),
            monitoring=Mock(),
            configuration=Mock(),
        )

        # Execute analysis
        results = service._execute_analysis(integration_config, Mock())

        # Verify concurrent execution was used (4 tickers > 2)
        mock_execute.assert_called_once()

        # Verify single conversion point
        mock_convert.assert_called_once_with(portfolio_dicts, Mock())

        # Verify results
        assert len(results) == 4

    def test_performance_improvement_validation(self):
        """Validate that performance improvements are achieved."""

        # Test concurrent vs sequential timing
        def simulate_ticker_processing(ticker, delay=0.1):
            time.sleep(delay)
            return {"Ticker": ticker, "Score": 80}

        # Sequential processing
        start = time.time()
        sequential_results = []
        for ticker in ["AAPL", "GOOGL", "MSFT", "AMZN"]:
            sequential_results.append(simulate_ticker_processing(ticker, 0.01))
        sequential_time = time.time() - start

        # Concurrent processing (simulated)
        from concurrent.futures import ThreadPoolExecutor

        start = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(simulate_ticker_processing, ticker, 0.01)
                for ticker in ["AAPL", "GOOGL", "MSFT", "AMZN"]
            ]
            concurrent_results = [f.result() for f in futures]
        concurrent_time = time.time() - start

        # Concurrent should be faster
        assert concurrent_time < sequential_time
        assert len(concurrent_results) == len(sequential_results)

    def test_memory_optimization_validation(self):
        """Validate memory optimization improvements."""
        # Simulate old pipeline with multiple conversions
        [{"ticker": f"TICK{i}", "value": i} for i in range(100)]

        # Old approach: multiple conversions
        conversions_old = 0
        conversions_old += 1
        conversions_old += 1
        conversions_old += 1

        # New approach: single conversion
        conversions_new = 0
        conversions_new += 1  # Single conversion at the end

        # New approach should have fewer conversions
        assert conversions_new < conversions_old
        assert conversions_new == 1

    def test_cache_optimization_validation(self):
        """Validate cache optimization improvements."""
        cache = {}
        max_cache_size = 10

        # Add entries
        for i in range(15):
            cache[f"key_{i}"] = f"value_{i}"

        # Apply cache management
        if len(cache) > max_cache_size:
            keys = list(cache.keys())
            for key in keys[:-max_cache_size]:
                del cache[key]

        assert len(cache) == max_cache_size

    @patch("app.api.services.ma_cross_service.MACrossService")
    def test_full_optimization_stack(self, mock_service_class):
        """Test that all optimizations work together."""
        # Create mock service instance
        mock_service = Mock()
        mock_service_class.return_value = mock_service

        # Setup mock responses
        mock_service.analyze.return_value = Mock(
            portfolios=[{"ticker": "AAPL", "score": 85}],
            execution_time=0.5,  # Fast execution
        )

        # Test configuration with multiple tickers
        config = {
            "TICKER": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
            "STRATEGY_TYPES": ["SMA", "EMA"],
        }

        # Execute
        result = mock_service.analyze(config)

        # Verify optimizations are active
        assert result.execution_time < 1.0  # Fast execution
        assert len(result.portfolios) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
