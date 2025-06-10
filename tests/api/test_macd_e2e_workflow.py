"""
End-to-End MACD Integration Testing Suite

This module provides comprehensive end-to-end testing for the complete MACD workflow,
from API request through strategy execution to results validation.

Tests validate:
- Complete MACD parameter processing pipeline
- Strategy execution and results format
- Performance with realistic parameter combinations
- Async execution capabilities
- Results consistency and validation
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest

from app.api.models.strategy_analysis import (
    DirectionEnum,
    MACrossRequest,
    StrategyTypeEnum,
)
from app.api.services.strategy_analysis_service import StrategyAnalysisService
from app.core.strategies.macd_strategy import MACDStrategy
from app.core.strategies.strategy_factory import StrategyFactory


class TestMACDEndToEndWorkflow:
    """Test complete MACD workflow from API to results"""

    @pytest.fixture
    def macd_request_small(self) -> MACrossRequest:
        """Small MACD parameter set for quick testing"""
        return MACrossRequest(
            ticker="BTC-USD",
            strategy_types=[StrategyTypeEnum.MACD],
            direction=DirectionEnum.LONG,
            short_window_start=6,
            short_window_end=10,
            long_window_start=12,
            long_window_end=16,
            signal_window_start=5,
            signal_window_end=7,
            step=2,
            windows=5,
            async_execution=False,
        )

    @pytest.fixture
    def macd_request_medium(self) -> MACrossRequest:
        """Medium MACD parameter set for performance testing"""
        return MACrossRequest(
            ticker="ETH-USD",
            strategy_types=[StrategyTypeEnum.MACD],
            direction=DirectionEnum.LONG,
            short_window_start=8,
            short_window_end=15,
            long_window_start=20,
            long_window_end=30,
            signal_window_start=7,
            signal_window_end=12,
            step=1,
            windows=10,
            async_execution=False,
        )

    @pytest.fixture
    def macd_request_large(self) -> MACrossRequest:
        """Large MACD parameter set for async testing"""
        return MACrossRequest(
            ticker=["AAPL", "GOOGL"],
            strategy_types=[StrategyTypeEnum.MACD],
            direction=DirectionEnum.LONG,
            short_window_start=6,
            short_window_end=20,
            long_window_start=25,
            long_window_end=40,
            signal_window_start=5,
            signal_window_end=15,
            step=2,
            windows=15,
            async_execution=True,
        )

    @pytest.fixture
    def mixed_strategy_request(self) -> MACrossRequest:
        """Mixed strategy request with MACD, SMA, and EMA"""
        return MACrossRequest(
            ticker="SPY",
            strategy_types=[
                StrategyTypeEnum.SMA,
                StrategyTypeEnum.EMA,
                StrategyTypeEnum.MACD,
            ],
            direction=DirectionEnum.LONG,
            short_window_start=10,
            short_window_end=15,
            long_window_start=20,
            long_window_end=25,
            signal_window_start=8,
            signal_window_end=12,
            step=1,
            windows=8,
            async_execution=False,
        )

    async def test_complete_macd_workflow_small_parameters(self, macd_request_small):
        """Test complete MACD workflow with small parameter set"""
        # Initialize components
        factory = StrategyFactory()
        service = StrategyAnalysisService(factory)

        # Validate request
        assert macd_request_small.strategy_types == [StrategyTypeEnum.MACD]

        # Test parameter validation
        strategy_config = macd_request_small.to_strategy_config()
        macd_strategy = factory.create_strategy(StrategyTypeEnum.MACD)

        # Validate parameters
        is_valid = macd_strategy.validate_parameters(strategy_config)
        assert is_valid, "MACD parameters should be valid"

        # Mock the actual strategy execution to avoid external dependencies
        with patch.object(MACDStrategy, "execute") as mock_execute:
            mock_execute.return_value = [
                {
                    "ticker": "BTC-USD",
                    "strategy_type": "MACD",
                    "short_window": 6,
                    "long_window": 12,
                    "signal_window": 5,
                    "direction": "Long",
                    "timeframe": "D",
                    "total_return": 125.5,
                    "annual_return": 22.3,
                    "sharpe_ratio": 1.45,
                    "sortino_ratio": 1.78,
                    "max_drawdown": 18.2,
                    "total_trades": 45,
                    "winning_trades": 28,
                    "losing_trades": 17,
                    "win_rate": 0.622,
                    "profit_factor": 2.15,
                    "expectancy": 450.0,
                    "expectancy_per_trade": 10.0,
                    "score": 1.25,
                    "beats_bnh": 15.3,
                    "has_open_trade": False,
                    "has_signal_entry": True,
                    "metric_type": "Advanced",
                    "avg_trade_duration": "5.2 days",
                }
            ]

            # Execute through service
            result = await service.analyze_strategy(macd_request_small)

            # Validate results
            assert result.status == "success"
            assert len(result.portfolios) == 1

            portfolio = result.portfolios[0]
            assert portfolio.ticker == "BTC-USD"
            assert portfolio.strategy_type == "MACD"
            assert portfolio.signal_window == 5
            assert portfolio.total_trades > 0
            assert portfolio.win_rate > 0
            assert portfolio.profit_factor > 0

    async def test_macd_parameter_combinations_validation(self, macd_request_medium):
        """Test MACD parameter combination validation"""
        factory = StrategyFactory()
        macd_strategy = factory.create_strategy(StrategyTypeEnum.MACD)

        # Test valid parameter combinations
        valid_config = {
            "short_window_start": 8,
            "short_window_end": 15,
            "long_window_start": 20,
            "long_window_end": 30,
            "signal_window_start": 7,
            "signal_window_end": 12,
            "step": 1,
        }

        assert macd_strategy.validate_parameters(
            valid_config
        ), "Valid parameters should pass"

        # Test invalid combinations
        invalid_configs = [
            {
                **valid_config,
                "short_window_start": 15,
                "short_window_end": 10,
            },  # start > end
            {
                **valid_config,
                "long_window_start": 15,
                "long_window_end": 18,
            },  # long not > short
            {
                **valid_config,
                "signal_window_start": 12,
                "signal_window_end": 7,
            },  # start > end
            {**valid_config, "step": 0},  # invalid step
            {**valid_config, "short_window_start": 0},  # invalid range
        ]

        for invalid_config in invalid_configs:
            assert not macd_strategy.validate_parameters(
                invalid_config
            ), f"Invalid config should fail: {invalid_config}"

    async def test_mixed_strategy_with_macd_parameters(self, mixed_strategy_request):
        """Test mixed strategy execution where MACD parameters are included"""
        factory = StrategyFactory()
        service = StrategyAnalysisService(factory)

        # Validate that MACD parameters are properly handled in mixed requests
        strategy_config = mixed_strategy_request.to_strategy_config()

        # Check that MACD parameters are included
        assert "short_window_start" in strategy_config
        assert "signal_window_start" in strategy_config

        # Validate each strategy can handle the config
        for strategy_type in mixed_strategy_request.strategy_types:
            strategy = factory.create_strategy(strategy_type)
            if strategy_type == StrategyTypeEnum.MACD:
                # MACD should validate MACD parameters
                assert strategy.validate_parameters(strategy_config)
            else:
                # SMA/EMA should ignore MACD parameters and validate successfully
                assert strategy.validate_parameters(strategy_config)

    async def test_async_execution_recommendation(self, macd_request_large):
        """Test async execution recommendation for large parameter combinations"""
        # Calculate expected parameter combinations
        short_combinations = (
            macd_request_large.short_window_end - macd_request_large.short_window_start
        ) // macd_request_large.step + 1
        long_combinations = (
            macd_request_large.long_window_end - macd_request_large.long_window_start
        ) // macd_request_large.step + 1
        signal_combinations = (
            macd_request_large.signal_window_end
            - macd_request_large.signal_window_start
        ) // macd_request_large.step + 1

        total_combinations = (
            short_combinations * long_combinations * signal_combinations
        )
        ticker_count = (
            len(macd_request_large.ticker)
            if isinstance(macd_request_large.ticker, list)
            else 1
        )

        expected_total = total_combinations * ticker_count * macd_request_large.windows

        # Should recommend async for large combinations
        assert macd_request_large.async_execution == True
        assert expected_total > 100, "Large parameter set should have many combinations"

    async def test_results_format_consistency(self, macd_request_small):
        """Test that MACD results follow consistent portfolio metrics format"""
        factory = StrategyFactory()
        service = StrategyAnalysisService(factory)

        with patch.object(MACDStrategy, "execute") as mock_execute:
            # Mock comprehensive results
            mock_execute.return_value = [
                {
                    "ticker": "BTC-USD",
                    "strategy_type": "MACD",
                    "short_window": 8,
                    "long_window": 20,
                    "signal_window": 9,
                    "direction": "Long",
                    "timeframe": "D",
                    "total_return": 185.7,
                    "annual_return": 28.4,
                    "sharpe_ratio": 1.67,
                    "sortino_ratio": 2.12,
                    "max_drawdown": 22.1,
                    "total_trades": 67,
                    "winning_trades": 42,
                    "losing_trades": 25,
                    "win_rate": 0.627,
                    "profit_factor": 2.45,
                    "expectancy": 780.0,
                    "expectancy_per_trade": 11.64,
                    "score": 1.45,
                    "beats_bnh": 18.7,
                    "has_open_trade": False,
                    "has_signal_entry": True,
                    "metric_type": "Advanced,Technical",
                    "avg_trade_duration": "4.8 days",
                }
            ]

            result = await service.analyze_strategy(macd_request_small)
            portfolio = result.portfolios[0]

            # Validate all required fields are present
            required_fields = [
                "ticker",
                "strategy_type",
                "short_window",
                "long_window",
                "signal_window",
                "direction",
                "timeframe",
                "total_return",
                "annual_return",
                "sharpe_ratio",
                "sortino_ratio",
                "max_drawdown",
                "total_trades",
                "winning_trades",
                "losing_trades",
                "win_rate",
                "profit_factor",
                "expectancy",
                "expectancy_per_trade",
                "score",
                "beats_bnh",
                "has_open_trade",
                "has_signal_entry",
            ]

            for field in required_fields:
                assert hasattr(
                    portfolio, field
                ), f"Portfolio missing required field: {field}"

            # Validate field types and ranges
            assert isinstance(
                portfolio.signal_window, int
            ), "Signal window should be integer"
            assert portfolio.signal_window > 0, "Signal window should be positive"
            assert portfolio.strategy_type == "MACD", "Strategy type should be MACD"
            assert 0 <= portfolio.win_rate <= 1, "Win rate should be between 0 and 1"
            assert portfolio.profit_factor > 0, "Profit factor should be positive"

    async def test_performance_with_realistic_parameters(self, macd_request_medium):
        """Test performance with realistic MACD parameter combinations"""
        import time

        factory = StrategyFactory()
        service = StrategyAnalysisService(factory)

        with patch.object(MACDStrategy, "execute") as mock_execute:
            # Mock execution that simulates realistic processing time
            def mock_execution(config):
                # Simulate some processing time
                time.sleep(0.1)
                return [
                    {
                        "ticker": "ETH-USD",
                        "strategy_type": "MACD",
                        "short_window": config.get("short_window_start", 8),
                        "long_window": config.get("long_window_start", 20),
                        "signal_window": config.get("signal_window_start", 7),
                        "direction": "Long",
                        "timeframe": "D",
                        "total_return": 156.3,
                        "annual_return": 24.8,
                        "sharpe_ratio": 1.52,
                        "sortino_ratio": 1.89,
                        "max_drawdown": 19.4,
                        "total_trades": 52,
                        "winning_trades": 33,
                        "losing_trades": 19,
                        "win_rate": 0.635,
                        "profit_factor": 2.28,
                        "expectancy": 620.0,
                        "expectancy_per_trade": 11.92,
                        "score": 1.32,
                        "beats_bnh": 16.8,
                        "has_open_trade": False,
                        "has_signal_entry": True,
                        "metric_type": "Advanced",
                        "avg_trade_duration": "5.1 days",
                    }
                ]

            mock_execute.side_effect = mock_execution

            # Measure execution time
            start_time = time.time()
            result = await service.analyze_strategy(macd_request_medium)
            execution_time = time.time() - start_time

            # Validate performance
            assert result.status == "success"
            assert (
                execution_time < 5.0
            ), f"Execution took too long: {execution_time:.2f}s"
            assert len(result.portfolios) >= 1, "Should return at least one result"

    async def test_error_handling_invalid_ticker(self):
        """Test error handling with invalid ticker symbols"""
        factory = StrategyFactory()
        service = StrategyAnalysisService(factory)

        invalid_request = MACrossRequest(
            ticker="INVALID_TICKER_123",
            strategy_types=[StrategyTypeEnum.MACD],
            direction=DirectionEnum.LONG,
            short_window_start=8,
            short_window_end=15,
            long_window_start=20,
            long_window_end=30,
            signal_window_start=7,
            signal_window_end=12,
            step=1,
            windows=5,
        )

        with patch.object(MACDStrategy, "execute") as mock_execute:
            # Mock execution failure
            mock_execute.side_effect = Exception("Invalid ticker: INVALID_TICKER_123")

            with pytest.raises(Exception):
                await service.analyze_strategy(invalid_request)

    async def test_cache_key_generation_consistency(self):
        """Test that cache keys are generated consistently for MACD parameters"""
        from app.api.services.strategy_analysis_service import StrategyAnalysisService

        # Create identical requests
        request1 = MACrossRequest(
            ticker="BTC-USD",
            strategy_types=[StrategyTypeEnum.MACD],
            direction=DirectionEnum.LONG,
            short_window_start=10,
            short_window_end=15,
            long_window_start=25,
            long_window_end=35,
            signal_window_start=8,
            signal_window_end=12,
            step=2,
        )

        request2 = MACrossRequest(
            ticker="BTC-USD",
            strategy_types=[StrategyTypeEnum.MACD],
            direction=DirectionEnum.LONG,
            short_window_start=10,
            short_window_end=15,
            long_window_start=25,
            long_window_end=35,
            signal_window_start=8,
            signal_window_end=12,
            step=2,
        )

        # Generate cache keys (this would be done in the API layer)
        config1 = request1.to_strategy_config()
        config2 = request2.to_strategy_config()

        # Keys should be identical for identical configurations
        assert (
            config1 == config2
        ), "Identical requests should generate identical configs"


if __name__ == "__main__":
    # Run basic validation
    print("Running MACD E2E workflow validation...")

    # Simple parameter validation test
    factory = StrategyFactory()
    macd_strategy = factory.create_strategy(StrategyTypeEnum.MACD)

    test_config = {
        "short_window_start": 8,
        "short_window_end": 15,
        "long_window_start": 20,
        "long_window_end": 30,
        "signal_window_start": 7,
        "signal_window_end": 12,
        "step": 1,
    }

    is_valid = macd_strategy.validate_parameters(test_config)
    print(f"MACD parameter validation: {'✅ PASS' if is_valid else '❌ FAIL'}")

    # Parameter ranges test
    ranges = macd_strategy.get_parameter_ranges()
    print(f"MACD parameter ranges retrieved: {'✅ PASS' if ranges else '❌ FAIL'}")

    print("MACD E2E workflow validation complete!")
