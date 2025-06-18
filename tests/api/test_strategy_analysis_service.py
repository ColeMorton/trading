"""
Integration tests for Strategy Analysis service layer with modular architecture.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest

from app.api.models.strategy_analysis import (
    MACrossRequest,
    MACrossResponse,
    PortfolioMetrics,
    StrategyAnalysisRequest,
    StrategyTypeEnum,
)
from app.api.services.strategy_analysis_service import (
    StrategyAnalysisService,
    create_strategy_analysis_service,
)
from app.tools.services import (
    PortfolioProcessingService,
    ResultAggregationService,
    ServiceCoordinator,
    StrategyExecutionEngine,
)


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for service testing."""

    class MockCache:
        def __init__(self):
            self._cache = {}

        async def get(self, key):
            return self._cache.get(key)

        async def set(self, key, value):
            self._cache[key] = value

    class MockConfig:
        def __init__(self):
            self.data = {"BASE_DIR": "/mock/path"}

        def __getitem__(self, key):
            return self.data[key]

        def get(self, key, default=None):
            return self.data.get(key, default)

    class MockLogger:
        def __init__(self):
            self.logs = []

        def log(self, message: str, level: str = "info"):
            self.logs.append(f"[{level.upper()}] {message}")

    class MockMetrics:
        def __init__(self):
            self.requests = []

        def record_request(self, **kwargs):
            self.requests.append(kwargs)

    class MockStrategyFactory:
        def create_strategy(self, strategy_type):
            mock_strategy = Mock()
            mock_strategy.validate_parameters.return_value = True
            mock_strategy.execute.return_value = [
                {
                    "ticker": "BTC-USD",
                    "strategy_type": "SMA",
                    "timeframe": "D",
                    "short_window": 20,
                    "long_window": 50,
                    "total_return": 0.25,
                    "sharpe_ratio": 1.5,
                    "max_drawdown": -0.15,
                    "num_trades": 10,
                    "win_rate": 0.6,
                }
            ]
            return mock_strategy

    import concurrent.futures

    class MockExecutor(concurrent.futures.ThreadPoolExecutor):
        def __init__(self):
            # Don't call super().__init__ to avoid creating real threads
            pass

        def submit(self, func, *args, **kwargs):
            # Execute immediately for testing
            from concurrent.futures import Future

            future = Future()
            try:
                result = func(*args, **kwargs)
                future.set_result(result)
            except Exception as e:
                future.set_exception(e)
            return future

    return {
        "cache": MockCache(),
        "config": MockConfig(),
        "logger": MockLogger(),
        "metrics": MockMetrics(),
        "strategy_factory": MockStrategyFactory(),
        "executor": MockExecutor(),
    }


@pytest.fixture
def service(mock_dependencies):
    """Create Strategy Analysis service instance with mocked dependencies."""
    return StrategyAnalysisService(
        strategy_factory=mock_dependencies["strategy_factory"],
        cache=mock_dependencies["cache"],
        config=mock_dependencies["config"],
        logger=mock_dependencies["logger"],
        metrics=mock_dependencies["metrics"],
        executor=mock_dependencies["executor"],
    )


@pytest.fixture
def sample_strategy_request():
    """Create sample strategy analysis request."""
    return StrategyAnalysisRequest(
        ticker=["BTC-USD"],
        strategy_type=StrategyTypeEnum.SMA,
        parameters={"windows": 89},
    )


@pytest.fixture
def sample_ma_cross_request():
    """Create sample MA Cross request for backward compatibility testing."""
    return MACrossRequest(
        ticker=["BTC-USD"],
        strategy_types=[StrategyTypeEnum.SMA],
    )


class TestStrategyAnalysisService:
    """Test Strategy Analysis service functionality with modular architecture."""

    def test_service_initialization(self, service):
        """Test service initialization with modular components."""
        assert service is not None
        assert isinstance(service, StrategyAnalysisService)
        assert isinstance(service, ServiceCoordinator)

        # Test that modular components are properly initialized
        assert hasattr(service, "strategy_engine")
        assert hasattr(service, "portfolio_processor")
        assert hasattr(service, "result_aggregator")

        assert isinstance(service.strategy_engine, StrategyExecutionEngine)
        assert isinstance(service.portfolio_processor, PortfolioProcessingService)
        assert isinstance(service.result_aggregator, ResultAggregationService)

        # Test memory optimization integration
        assert hasattr(service.strategy_engine, "memory_optimizer")
        assert hasattr(service.strategy_engine, "data_converter")
        assert hasattr(service.strategy_engine, "streaming_processor")
        assert service.strategy_engine.enable_memory_optimization is True

    @pytest.mark.asyncio
    async def test_analyze_strategy_success(
        self, service, sample_strategy_request, mock_dependencies
    ):
        """Test successful strategy analysis with new analyze_strategy method."""

        with patch("app.tools.setup_logging.setup_logging") as mock_setup_logging:
            # Mock logging setup
            mock_log = Mock()
            mock_log_close = Mock()
            mock_setup_logging.return_value = (mock_log, mock_log_close, None, None)

            response = await service.analyze_strategy(sample_strategy_request)

            assert isinstance(response, MACrossResponse)
            assert response.status == "success"
            assert len(response.portfolios) >= 0
            assert response.execution_time >= 0
            assert response.timestamp is not None
            assert response.request_id is not None
            assert response.ticker is not None
            assert response.strategy_types is not None

    @pytest.mark.asyncio
    async def test_analyze_portfolio_backward_compatibility(
        self, service, sample_ma_cross_request
    ):
        """Test backward compatibility with analyze_portfolio method."""

        with patch("app.tools.setup_logging.setup_logging") as mock_setup_logging:
            # Mock logging setup
            mock_log = Mock()
            mock_log_close = Mock()
            mock_setup_logging.return_value = (mock_log, mock_log_close, None, None)

            response = await service.analyze_portfolio(sample_ma_cross_request)

            assert isinstance(response, MACrossResponse)
            assert response.status == "success"

    def test_analyze_portfolio_async(self, service, sample_ma_cross_request):
        """Test asynchronous analysis functionality."""
        response = service.analyze_portfolio_async(sample_ma_cross_request)

        assert hasattr(response, "execution_id")
        assert hasattr(response, "status")
        assert response.status == "accepted"
        assert response.execution_id is not None

    @pytest.mark.asyncio
    async def test_cache_functionality(self, service, sample_strategy_request):
        """Test caching functionality in modular architecture."""

        with patch("app.tools.setup_logging.setup_logging") as mock_setup_logging:
            mock_log = Mock()
            mock_log_close = Mock()
            mock_setup_logging.return_value = (mock_log, mock_log_close, None, None)

            # First request should execute strategy
            response1 = await service.analyze_strategy(sample_strategy_request)

            # Second request should hit cache
            response2 = await service.analyze_strategy(sample_strategy_request)

            # Both responses should be successful
            assert response1.status == "success"
            assert response2.status == "success"

    def test_factory_function(self):
        """Test factory function for creating service with defaults."""
        service = create_strategy_analysis_service()

        assert isinstance(service, StrategyAnalysisService)
        assert hasattr(service, "strategy_engine")
        assert hasattr(service, "portfolio_processor")
        assert hasattr(service, "result_aggregator")

    def test_backward_compatibility_aliases(self):
        """Test backward compatibility aliases."""
        from app.api.services.strategy_analysis_service import (
            MACrossService,
            MACrossServiceError,
        )

        # Test that aliases exist and are correct types
        assert issubclass(MACrossService, StrategyAnalysisService)
        assert issubclass(MACrossServiceError, Exception)


class TestModularServices:
    """Test individual modular service components."""

    def test_strategy_execution_engine(self, mock_dependencies):
        """Test StrategyExecutionEngine independently."""
        engine = StrategyExecutionEngine(
            strategy_factory=mock_dependencies["strategy_factory"],
            cache=mock_dependencies["cache"],
            config=mock_dependencies["config"],
            logger=mock_dependencies["logger"],
        )

        assert engine is not None
        assert hasattr(engine, "strategy_factory")
        assert hasattr(engine, "cache")

    def test_portfolio_processing_service(self, mock_dependencies):
        """Test PortfolioProcessingService independently."""
        processor = PortfolioProcessingService(logger=mock_dependencies["logger"])

        assert processor is not None

        # Test portfolio validation
        valid_portfolio = {
            "ticker": "BTC-USD",
            "strategy_type": "SMA",
            "timeframe": "D",
        }

        assert processor.validate_portfolio_data(
            valid_portfolio, mock_dependencies["logger"].log
        )

    def test_result_aggregation_service(self, mock_dependencies):
        """Test ResultAggregationService independently."""
        aggregator = ResultAggregationService(
            logger=mock_dependencies["logger"],
            metrics=mock_dependencies["metrics"],
        )

        assert aggregator is not None
        assert hasattr(aggregator, "logger")
        assert hasattr(aggregator, "metrics")

        # Test execution ID generation
        exec_id = aggregator.generate_execution_id()
        assert exec_id is not None
        assert isinstance(exec_id, str)

    def test_service_coordinator(self, mock_dependencies):
        """Test ServiceCoordinator orchestration."""
        coordinator = ServiceCoordinator(
            strategy_factory=mock_dependencies["strategy_factory"],
            cache=mock_dependencies["cache"],
            config=mock_dependencies["config"],
            logger=mock_dependencies["logger"],
            metrics=mock_dependencies["metrics"],
        )

        assert coordinator is not None
        assert hasattr(coordinator, "strategy_engine")
        assert hasattr(coordinator, "portfolio_processor")
        assert hasattr(coordinator, "result_aggregator")


class TestMemoryOptimizationIntegration:
    """Test memory optimization integration with strategy analysis."""

    def test_memory_optimization_disabled(self, mock_dependencies):
        """Test service with memory optimization disabled."""
        from app.tools.services.service_coordinator import ServiceCoordinator

        # Create service with memory optimization disabled
        service = ServiceCoordinator(
            strategy_factory=mock_dependencies["strategy_factory"],
            cache=mock_dependencies["cache"],
            config=mock_dependencies["config"],
            logger=mock_dependencies["logger"],
            metrics=mock_dependencies["metrics"],
        )

        # Override strategy engine with memory optimization disabled
        from app.tools.services.strategy_execution_engine import StrategyExecutionEngine

        service.strategy_engine = StrategyExecutionEngine(
            strategy_factory=mock_dependencies["strategy_factory"],
            cache=mock_dependencies["cache"],
            config=mock_dependencies["config"],
            logger=mock_dependencies["logger"],
            enable_memory_optimization=False,
        )

        assert service.strategy_engine.enable_memory_optimization is False
        assert service.strategy_engine.memory_optimizer is None
        assert service.strategy_engine.data_converter is None
        assert service.strategy_engine.streaming_processor is None

    @pytest.mark.asyncio
    async def test_memory_optimization_in_strategy_execution(
        self, service, sample_strategy_request
    ):
        """Test memory optimization during strategy execution."""
        with patch("app.tools.setup_logging.setup_logging") as mock_setup_logging:
            mock_log = Mock()
            mock_log_close = Mock()
            mock_setup_logging.return_value = (mock_log, mock_log_close, None, None)

            # Mock memory optimizer to track calls
            with patch.object(
                service.strategy_engine.memory_optimizer.monitor, "monitor_operation"
            ) as mock_monitor:
                mock_monitor.return_value.__enter__ = Mock()
                mock_monitor.return_value.__exit__ = Mock()

                response = await service.analyze_strategy(sample_strategy_request)

                # Verify memory monitoring was called
                mock_monitor.assert_called()
                assert response.status == "success"

    def test_dataframe_optimization_integration(self, service):
        """Test DataFrame optimization integration."""
        import pandas as pd

        # Create test DataFrame with inefficient types
        test_df = pd.DataFrame(
            {
                "int_col": [1, 2, 3, 4, 5],
                "float_col": [1.0, 2.0, 3.0, 4.0, 5.0],
                "string_col": ["A", "B", "A", "B", "A"],
            }
        )

        # Force inefficient types
        test_df["int_col"] = test_df["int_col"].astype("int64")
        test_df["float_col"] = test_df["float_col"].astype("float64")

        # Test optimization through strategy engine
        portfolio_dicts = [{"test_data": test_df}]
        optimized = service.strategy_engine._optimize_portfolio_results(
            portfolio_dicts, service.logger.log
        )

        assert len(optimized) == 1
        assert "test_data" in optimized[0]
        # Verify optimization was applied (string column should be categorical)
        optimized_df = optimized[0]["test_data"]
        assert optimized_df["string_col"].dtype.name == "category"


class TestErrorHandling:
    """Test error handling in modular architecture."""

    @pytest.mark.asyncio
    async def test_strategy_execution_error(self, mock_dependencies):
        """Test error handling in strategy execution."""
        # Create a failing strategy factory
        failing_factory = Mock()
        failing_factory.create_strategy.side_effect = ValueError("Invalid strategy")

        service = StrategyAnalysisService(
            strategy_factory=failing_factory,
            cache=mock_dependencies["cache"],
            config=mock_dependencies["config"],
            logger=mock_dependencies["logger"],
            metrics=mock_dependencies["metrics"],
        )

        request = StrategyAnalysisRequest(
            ticker=["BTC-USD"],
            strategy_type=StrategyTypeEnum.SMA,
        )

        with patch("app.tools.setup_logging.setup_logging") as mock_setup_logging:
            mock_log = Mock()
            mock_log_close = Mock()
            mock_setup_logging.return_value = (mock_log, mock_log_close, None, None)

            with pytest.raises(Exception):  # Should raise StrategyAnalysisServiceError
                await service.analyze_strategy(request)

    def test_portfolio_processing_error(self, mock_dependencies):
        """Test error handling in portfolio processing."""
        processor = PortfolioProcessingService(logger=mock_dependencies["logger"])

        # Test with invalid portfolio data
        invalid_portfolios = [{"invalid": "data"}]

        # Should handle errors gracefully
        summary = processor.calculate_portfolio_summary(
            invalid_portfolios, mock_dependencies["logger"].log
        )
        assert "error" in summary or summary["total_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
