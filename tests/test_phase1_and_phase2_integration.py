"""
Integration Tests for Phase 1 + Phase 2 Combined

Tests that Phase 1 performance optimizations work seamlessly with
Phase 2 service decomposition and unified configuration.
"""

import time
from unittest.mock import Mock, patch

import pytest

from app.api.models.strategy_analysis import MACrossRequest, MinimumCriteria
from app.api.services.ma_cross_orchestrator import MACrossOrchestrator
from app.strategies.ma_cross.config.parameter_testing import ParameterTestingConfig


class TestPhase1And2Integration:
    """Integration tests for combined Phase 1 and Phase 2 optimizations."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked dependencies."""
        return MACrossOrchestrator(
            logger=Mock(),
            progress_tracker=Mock(),
            strategy_executor=Mock(),
            strategy_analyzer=Mock(),
            cache=Mock(),
            monitoring=Mock(),
            configuration=Mock(),
        )

    @pytest.fixture
    def multi_ticker_request(self):
        """Request with multiple tickers to trigger Phase 1 concurrent execution."""
        return MACrossRequest(
            ticker=[
                "AAPL",
                "GOOGL",
                "MSFT",
                "AMZN",
                "TSLA",
            ],  # 5 tickers for concurrent
            windows=20,
            strategy_types=["SMA", "EMA"],
            direction="Long",
            use_hourly=False,
            minimums=MinimumCriteria(
                win_rate=0.6,
                trades=10,
                profit_factor=1.5,
            ),
        )

    def test_phase2_config_creation_from_phase1_request(
        self, orchestrator, multi_ticker_request,
    ):
        """Test that Phase 2 orchestrator creates proper config from Phase 1 optimized request."""
        config = orchestrator._create_config_from_request(multi_ticker_request)

        # Should create configuration compatible with Phase 1 concurrent execution
        assert config["TICKER"] == ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        assert len(config["TICKER"]) > 2  # Will trigger Phase 1 concurrent execution
        assert config["STRATEGY_TYPES"] == ["SMA", "EMA"]
        assert config["WINDOWS"] == 20

    def test_phase2_filter_criteria_from_phase1_request(
        self, orchestrator, multi_ticker_request,
    ):
        """Test that Phase 2 filter service uses criteria from optimized Phase 1 request."""
        criteria = orchestrator._create_filter_criteria(multi_ticker_request)

        # Should properly map Phase 1 request minimums to Phase 2 filter criteria
        assert criteria["minimums"]["win_rate"] == 0.6
        assert criteria["minimums"]["trades"] == 10
        assert criteria["minimums"]["profit_factor"] == 1.5

    def test_phase2_config_validation_with_phase1_optimization_triggers(self):
        """Test that Phase 2 config validation recognizes Phase 1 optimization scenarios."""
        # Create config that will trigger Phase 1 optimizations
        config = ParameterTestingConfig(
            tickers=[
                "AAPL",
                "GOOGL",
                "MSFT",
                "AMZN",
            ],  # 4 tickers → concurrent execution
            windows=30,  # Reasonable window size
            strategy_types=["SMA", "EMA"],  # Multiple strategies
        )

        validation_result = config.validate()
        summary = config.get_execution_summary()

        # Should be valid and recognize concurrent execution
        assert validation_result.is_valid is True
        assert summary["uses_concurrent"] is True  # Phase 1 concurrent execution
        assert summary["ticker_count"] == 4
        assert summary["estimated_combinations"] == 8  # 4 tickers * 2 strategies

    @patch("app.api.services.parameter_testing_service.execute_strategy_concurrent")
    @patch("app.api.services.parameter_testing_service.ConfigService.process_config")
    def test_phase1_concurrent_execution_with_phase2_services(
        self,
        mock_process_config,
        mock_execute_concurrent,
        orchestrator,
        multi_ticker_request,
    ):
        """Test that Phase 1 concurrent execution works through Phase 2 service layer."""
        # Setup mocks for Phase 1 concurrent execution
        mock_process_config.return_value = {
            "TICKER": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "WINDOWS": 20,
            "BASE_DIR": "/Users/colemorton/Projects/trading",
        }

        # Mock Phase 1 concurrent execution results
        mock_execute_concurrent.return_value = [
            {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Total Return [%]": 15.5,
                "Win Rate [%]": 65.0,
                "Total Trades": 25,
                "Profit Factor": 1.8,
                "Score": 85.0,
            },
            {
                "Ticker": "GOOGL",
                "Strategy Type": "EMA",
                "Total Return [%]": 18.7,
                "Win Rate [%]": 70.0,
                "Total Trades": 30,
                "Profit Factor": 2.1,
                "Score": 92.0,
            },
        ]

        # Get estimate (should use Phase 2 orchestrator with Phase 1 optimization detection)
        estimate = orchestrator.get_execution_estimate(multi_ticker_request)

        # Should recognize concurrent execution (Phase 1 optimization)
        assert estimate["factors"]["uses_concurrent"] is True
        assert estimate["factors"]["ticker_count"] == 5
        assert estimate["estimated_seconds"] > 0

    def test_phase1_performance_with_phase2_service_decomposition(self):
        """Test that Phase 2 service decomposition doesn't degrade Phase 1 performance."""
        from app.api.services.parameter_testing_service import ParameterTestingService

        service = ParameterTestingService(
            logger=Mock(),
            progress_tracker=Mock(),
            strategy_executor=Mock(),
        )

        # Test Phase 1 optimization: concurrent execution should be faster
        concurrent_estimate = service.estimate_execution_time(
            ticker_count=5,  # Triggers Phase 1 concurrent execution
            window_size=20,
            strategy_count=2,
        )

        sequential_estimate = service.estimate_execution_time(
            ticker_count=2,  # Uses sequential execution
            window_size=20,
            strategy_count=2,
        )

        # Phase 1 optimization: concurrent should be faster through Phase 2 services
        assert concurrent_estimate < sequential_estimate

    def test_phase2_configuration_preserves_phase1_optimizations(self):
        """Test that Phase 2 configuration system preserves Phase 1 optimization settings."""
        # Create config with Phase 1 optimization triggers
        config_dict = {
            "TICKER": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],  # 5 tickers
            "WINDOWS": 20,
            "STRATEGY_TYPES": ["SMA", "EMA"],
            "DIRECTION": "Long",
            "MAX_WORKERS": 4,  # Phase 1 concurrent execution setting
            "ENABLE_CACHING": True,  # Phase 1 caching optimization
        }

        # Convert through Phase 2 configuration system
        config = ParameterTestingConfig.from_dict(config_dict)
        result_dict = config.to_dict()

        # Should preserve Phase 1 optimization settings
        assert result_dict["TICKER"] == config_dict["TICKER"]
        assert (
            len(result_dict["TICKER"]) > 2
        )  # Will trigger Phase 1 concurrent execution
        assert config.execution_options.max_workers == 4  # Phase 1 setting preserved
        assert (
            config.execution_options.enable_caching is True
        )  # Phase 1 setting preserved

    def test_end_to_end_phase1_and_phase2_workflow(self, orchestrator):
        """Test complete workflow using both Phase 1 and Phase 2 optimizations."""
        # Create request that triggers Phase 1 optimizations
        request = MACrossRequest(
            ticker=["AAPL", "GOOGL", "MSFT", "AMZN"],  # 4 tickers → Phase 1 concurrent
            windows=20,
            strategy_types=["SMA", "EMA"],  # Multiple strategies
            direction="Long",
            minimums=MinimumCriteria(win_rate=0.6, trades=10),  # Phase 2 filtering
        )

        # Test cache key generation (Phase 2 with Phase 1 optimization awareness)
        cache_key = orchestrator._generate_cache_key(request)
        assert "t:AAPL,AMZN,GOOGL,MSFT" in cache_key  # Sorted tickers (Phase 2)
        assert "s:EMA,SMA" in cache_key  # Sorted strategies (Phase 2)

        # Test config creation (Phase 2 with Phase 1 optimization triggers)
        config = orchestrator._create_config_from_request(request)
        assert len(config["TICKER"]) > 2  # Will use Phase 1 concurrent execution

        # Test filter criteria creation (Phase 2 service)
        criteria = orchestrator._create_filter_criteria(request)
        assert criteria["minimums"]["win_rate"] == 0.6  # Phase 2 filtering

    def test_backward_compatibility_phase1_through_phase2(self):
        """Test that Phase 2 services maintain Phase 1 backward compatibility."""
        from app.strategies.ma_cross.config_types import validate_config_compatibility

        # Legacy config format that worked with Phase 1
        legacy_config = {
            "TICKER": ["AAPL", "GOOGL", "MSFT", "AMZN"],
            "WINDOWS": 20,
            "STRATEGY_TYPES": ["SMA"],
            "BASE_DIR": "/Users/colemorton/Projects/trading",
            "MINIMUMS": {
                "WIN_RATE": 0.6,
                "TRADES": 10,
            },
        }

        # Should be compatible with both Phase 1 and Phase 2
        warnings = validate_config_compatibility(legacy_config)

        # Should have no compatibility issues
        error_warnings = [w for w in warnings if "error" in w.lower()]
        assert len(error_warnings) == 0  # No breaking changes


class TestPhase1And2PerformanceRegression:
    """Performance regression tests for combined optimizations."""

    def test_no_performance_regression_from_service_decomposition(self):
        """Ensure Phase 2 service decomposition doesn't slow down Phase 1 optimizations."""
        from app.api.services.parameter_testing_service import ParameterTestingService
        from app.api.services.portfolio_filter_service import PortfolioFilterService
        from app.api.services.results_export_service import ResultsExportService

        # Test that Phase 2 services are lightweight and don't add overhead
        start_time = time.time()

        # Create all Phase 2 services
        param_service = ParameterTestingService(Mock(), Mock(), Mock())
        filter_service = PortfolioFilterService(Mock())
        export_service = ResultsExportService(Mock())

        # Execute lightweight operations
        param_service.validate_parameters(["AAPL"], 20, ["SMA"])
        filter_service.filter_portfolios([], {})
        export_service.convert_to_portfolio_metrics([])

        creation_time = time.time() - start_time

        # Phase 2 service creation and basic operations should be fast
        assert creation_time < 0.1  # Less than 100ms overhead

    def test_memory_efficiency_maintained_through_decomposition(self):
        """Test that Phase 2 decomposition maintains Phase 1 memory efficiency."""
        # Large dataset to test memory efficiency
        large_portfolio_set = []
        for i in range(1000):
            large_portfolio_set.append(
                {
                    "Ticker": f"TICK{i:04d}",
                    "Strategy Type": "SMA",
                    "Total Return [%]": 10.0 + (i % 20),
                    "Win Rate [%]": 50.0 + (i % 50),
                    "Total Trades": 20 + (i % 30),
                    "Score": 60.0 + (i % 40),
                },
            )

        from app.api.services.portfolio_filter_service import PortfolioFilterService
        from app.api.services.results_export_service import ResultsExportService

        filter_service = PortfolioFilterService(Mock())
        export_service = ResultsExportService(Mock())

        # Phase 2 services should handle large datasets efficiently (Phase 1 memory optimization)
        start_time = time.time()

        # Filter large dataset
        filtered = filter_service.filter_portfolios(
            large_portfolio_set, {"minimums": {"win_rate": 0.7}},
        )

        # Convert results
        metrics = export_service.convert_to_portfolio_metrics(
            filtered[:100],
        )  # Limit for test

        processing_time = time.time() - start_time

        # Should process efficiently (Phase 1 memory optimization preserved)
        assert processing_time < 2.0  # Less than 2 seconds for 1000 portfolios
        assert len(filtered) > 0  # Should have filtered results
        assert len(metrics) > 0  # Should have converted results


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
