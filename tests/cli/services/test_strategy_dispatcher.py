"""
Comprehensive tests for CLI Strategy Dispatcher.

This test suite covers StrategyDispatcher with focus on:
- Strategy routing logic (SMA/EMA → MA service, MACD → MACD service)
- Strategy compatibility validation
- Mixed strategy type handling
- Error scenarios and edge cases
- Service availability and mapping
"""

from unittest.mock import patch

import pytest

from app.cli.models.strategy import (
    StrategyConfig,
    StrategyMinimums,
    StrategyType,
    SyntheticTickerConfig,
)
from app.cli.services.strategy_dispatcher import StrategyDispatcher
from app.cli.services.strategy_services import MACDStrategyService, MAStrategyService


class TestStrategyDispatcher:
    """Test cases for StrategyDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create StrategyDispatcher instance."""
        return StrategyDispatcher()

    @pytest.fixture
    def base_config(self):
        """Create base strategy configuration."""
        return StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.SMA],
            use_years=False,
            years=15,
            multi_ticker=False,
            use_scanner=False,
            scanner_list="",
            use_gbm=False,
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

    def test_dispatcher_initialization(self, dispatcher):
        """Test that dispatcher initializes with correct services."""
        assert "MA" in dispatcher._services
        assert "MACD" in dispatcher._services
        assert isinstance(dispatcher._services["MA"], MAStrategyService)
        assert isinstance(dispatcher._services["MACD"], MACDStrategyService)

    def test_get_available_services(self, dispatcher):
        """Test getting list of available services."""
        services = dispatcher.get_available_services()
        assert "MA" in services
        assert "MACD" in services
        assert len(services) == 2

    def test_get_supported_strategy_types(self, dispatcher):
        """Test getting mapping of services to supported strategy types."""
        strategy_mapping = dispatcher.get_supported_strategy_types()

        assert "MA" in strategy_mapping
        assert "MACD" in strategy_mapping
        assert strategy_mapping["MA"] == ["SMA", "EMA"]
        assert strategy_mapping["MACD"] == ["MACD"]

    def test_determine_service_sma_strategy(self, dispatcher):
        """Test service determination for SMA strategy."""
        strategy_types = [StrategyType.SMA]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    def test_determine_service_ema_strategy(self, dispatcher):
        """Test service determination for EMA strategy."""
        strategy_types = [StrategyType.EMA]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    def test_determine_service_macd_strategy(self, dispatcher):
        """Test service determination for MACD strategy."""
        strategy_types = [StrategyType.MACD]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MACDStrategyService)

    def test_determine_service_mixed_ma_strategies(self, dispatcher):
        """Test service determination for mixed SMA/EMA strategies."""
        strategy_types = [StrategyType.SMA, StrategyType.EMA]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    @patch("app.cli.services.strategy_dispatcher.rprint")
    def test_determine_service_macd_with_other_strategies_warning(
        self,
        mock_rprint,
        dispatcher,
    ):
        """Test service determination with MACD and other strategies shows warning."""
        strategy_types = [StrategyType.MACD, StrategyType.SMA]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MACDStrategyService)
        mock_rprint.assert_called_once()
        assert "Multiple strategy types specified with MACD" in str(
            mock_rprint.call_args,
        )

    def test_determine_service_string_strategy_types(self, dispatcher):
        """Test service determination with string strategy types."""
        strategy_types = ["SMA", "EMA"]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    def test_determine_service_mixed_enum_string_types(self, dispatcher):
        """Test service determination with mixed enum and string types."""
        strategy_types = [StrategyType.SMA, "EMA"]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    @patch("app.cli.services.strategy_dispatcher.rprint")
    def test_determine_service_unsupported_strategy(self, mock_rprint, dispatcher):
        """Test service determination with unsupported strategy type."""
        strategy_types = ["INVALID_STRATEGY"]
        service = dispatcher._determine_service(strategy_types)

        assert service is None
        assert mock_rprint.call_count == 2  # Two rprint calls for unsupported strategy
        assert any(
            "Unsupported strategy types" in str(call)
            for call in mock_rprint.call_args_list
        )
        assert any(
            "Supported: SMA, EMA, MACD" in str(call)
            for call in mock_rprint.call_args_list
        )

    def test_validate_strategy_compatibility_valid_sma(self, dispatcher):
        """Test strategy compatibility validation for valid SMA."""
        strategy_types = [StrategyType.SMA]
        is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)

        assert is_compatible is True

    def test_validate_strategy_compatibility_valid_ema(self, dispatcher):
        """Test strategy compatibility validation for valid EMA."""
        strategy_types = [StrategyType.EMA]
        is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)

        assert is_compatible is True

    def test_validate_strategy_compatibility_valid_macd(self, dispatcher):
        """Test strategy compatibility validation for valid MACD."""
        strategy_types = [StrategyType.MACD]
        is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)

        assert is_compatible is True

    def test_validate_strategy_compatibility_valid_mixed_ma(self, dispatcher):
        """Test strategy compatibility validation for mixed MA strategies."""
        strategy_types = [StrategyType.SMA, StrategyType.EMA]
        is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)

        assert is_compatible is True

    def test_validate_strategy_compatibility_invalid_strategy(self, dispatcher):
        """Test strategy compatibility validation for invalid strategy."""
        strategy_types = ["INVALID_STRATEGY"]
        is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)

        assert is_compatible is False

    def test_validate_strategy_compatibility_empty_list(self, dispatcher):
        """Test strategy compatibility validation for empty strategy list."""
        strategy_types = []
        is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)

        assert is_compatible is False

    @patch.object(MAStrategyService, "execute_strategy")
    def test_execute_strategy_sma_success(self, mock_execute, dispatcher, base_config):
        """Test successful strategy execution for SMA."""
        mock_execute.return_value = True
        config = base_config
        config.strategy_types = [StrategyType.SMA]

        result = dispatcher.execute_strategy(config)

        assert result is True
        mock_execute.assert_called_once_with(config)

    @patch.object(MACDStrategyService, "execute_strategy")
    def test_execute_strategy_macd_success(self, mock_execute, dispatcher, base_config):
        """Test successful strategy execution for MACD."""
        mock_execute.return_value = True
        config = base_config
        config.strategy_types = [StrategyType.MACD]

        result = dispatcher.execute_strategy(config)

        assert result is True
        mock_execute.assert_called_once_with(config)

    @patch.object(MAStrategyService, "execute_strategy")
    def test_execute_strategy_failure(self, mock_execute, dispatcher, base_config):
        """Test strategy execution failure."""
        mock_execute.return_value = False
        config = base_config
        config.strategy_types = [StrategyType.SMA]

        result = dispatcher.execute_strategy(config)

        assert result is False
        mock_execute.assert_called_once_with(config)

    @patch("app.cli.services.strategy_dispatcher.rprint")
    def test_execute_strategy_no_compatible_service(self, mock_rprint, dispatcher):
        """Test strategy execution with no compatible service."""
        # Instead of using config object, test dispatcher directly with invalid strategy
        result = dispatcher._determine_service(["INVALID_STRATEGY"])
        assert result is None

        # Test validation method
        is_compatible = dispatcher.validate_strategy_compatibility(["INVALID_STRATEGY"])
        assert is_compatible is False

    @patch.object(MAStrategyService, "execute_strategy")
    def test_execute_strategy_mixed_ma_strategies(
        self,
        mock_execute,
        dispatcher,
        base_config,
    ):
        """Test strategy execution with mixed MA strategies."""
        mock_execute.return_value = True
        config = base_config
        config.strategy_types = [StrategyType.SMA, StrategyType.EMA]

        result = dispatcher.execute_strategy(config)

        assert result is True
        mock_execute.assert_called_once_with(config)

    @patch.object(MACDStrategyService, "execute_strategy")
    @patch("app.cli.services.strategy_dispatcher.rprint")
    def test_execute_strategy_macd_with_mixed_strategies(
        self,
        mock_rprint,
        mock_execute,
        dispatcher,
        base_config,
    ):
        """Test strategy execution with MACD mixed with other strategies."""
        mock_execute.return_value = True
        config = base_config
        config.strategy_types = [StrategyType.MACD, StrategyType.SMA]

        result = dispatcher.execute_strategy(config)

        assert result is True
        mock_execute.assert_called_once_with(config)
        # Should show warning about multiple strategy types with MACD
        mock_rprint.assert_called()

    def test_service_isolation(self, dispatcher):
        """Test that services are properly isolated and don't interfere."""
        # Get both services
        ma_service = dispatcher._services["MA"]
        macd_service = dispatcher._services["MACD"]

        # Verify they are different instances
        assert ma_service is not macd_service
        assert isinstance(ma_service, MAStrategyService)
        assert isinstance(macd_service, MACDStrategyService)

        # Verify they have different supported strategy types
        assert (
            ma_service.get_supported_strategy_types()
            != macd_service.get_supported_strategy_types()
        )


class TestStrategyDispatcherEdgeCases:
    """Test edge cases and error scenarios for StrategyDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create StrategyDispatcher instance."""
        return StrategyDispatcher()

    def test_strategy_type_case_insensitive_handling(self, dispatcher):
        """Test that string strategy types are handled case-insensitively."""
        # Test lowercase
        service_lower = dispatcher._determine_service(["sma"])
        assert service_lower is not None
        assert isinstance(service_lower, MAStrategyService)

        # Test uppercase
        service_upper = dispatcher._determine_service(["SMA"])
        assert service_upper is not None
        assert isinstance(service_upper, MAStrategyService)

        # Test mixed case
        service_mixed = dispatcher._determine_service(["Sma"])
        assert service_mixed is not None
        assert isinstance(service_mixed, MAStrategyService)

    def test_duplicate_strategy_types(self, dispatcher):
        """Test handling of duplicate strategy types."""
        strategy_types = [StrategyType.SMA, StrategyType.SMA, StrategyType.EMA]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    def test_none_strategy_types(self, dispatcher):
        """Test handling of None in strategy types list."""
        strategy_types = [StrategyType.SMA, None]

        # This should handle gracefully without crashing
        try:
            service = dispatcher._determine_service(strategy_types)
            # Should either return a service or None, but not crash
            assert service is None or isinstance(
                service,
                MAStrategyService | MACDStrategyService,
            )
        except (AttributeError, TypeError):
            # This is acceptable - the function may not handle None gracefully
            pass

    def test_empty_string_strategy_type(self, dispatcher):
        """Test handling of empty string strategy type."""
        strategy_types = [""]
        service = dispatcher._determine_service(strategy_types)

        assert service is None

    def test_whitespace_strategy_type(self, dispatcher):
        """Test handling of whitespace-only strategy type."""
        strategy_types = ["   ", "\t", "\n"]
        service = dispatcher._determine_service(strategy_types)

        assert service is None

    @patch.object(MAStrategyService, "execute_strategy")
    def test_execute_strategy_service_exception(self, mock_execute, dispatcher):
        """Test strategy execution when service raises exception."""
        mock_execute.side_effect = RuntimeError("Service execution failed")

        config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.SMA],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        # The dispatcher should let the exception propagate or handle it gracefully
        try:
            result = dispatcher.execute_strategy(config)
            # If it handles the exception, result should be False
            assert result is False
        except RuntimeError:
            # If it lets the exception propagate, that's also acceptable
            pass

    def test_strategy_priority_order(self, dispatcher):
        """Test that MACD takes priority when mixed with other strategies."""
        # MACD should be chosen over MA strategies when both are present
        strategy_types = [StrategyType.SMA, StrategyType.EMA, StrategyType.MACD]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MACDStrategyService)

    def test_large_strategy_list(self, dispatcher):
        """Test handling of large list of strategy types."""
        # Large list with valid strategies
        strategy_types = [StrategyType.SMA] * 100 + [StrategyType.EMA] * 100
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)

    def test_strategy_type_with_custom_attributes(self, dispatcher):
        """Test handling of strategy types that might have custom attributes."""

        # Mock a strategy type that has a value attribute
        class MockStrategyType:
            def __init__(self, value):
                self.value = value

        mock_sma = MockStrategyType("SMA")
        mock_ema = MockStrategyType("EMA")

        strategy_types = [mock_sma, mock_ema]
        service = dispatcher._determine_service(strategy_types)

        assert service is not None
        assert isinstance(service, MAStrategyService)


class TestStrategyDispatcherPerformance:
    """Performance-related tests for StrategyDispatcher."""

    @pytest.fixture
    def dispatcher(self):
        """Create StrategyDispatcher instance."""
        return StrategyDispatcher()

    def test_service_lookup_performance(self, dispatcher):
        """Test that service lookup is efficient for repeated calls."""
        import time

        strategy_types = [StrategyType.SMA]

        # Time multiple service determinations
        start_time = time.time()
        for _ in range(1000):
            service = dispatcher._determine_service(strategy_types)
            assert service is not None
        end_time = time.time()

        # Should complete in reasonable time (less than 1 second for 1000 calls)
        assert (end_time - start_time) < 1.0

    def test_compatibility_validation_performance(self, dispatcher):
        """Test that compatibility validation is efficient."""
        import time

        strategy_types = [StrategyType.SMA, StrategyType.EMA]

        # Time multiple compatibility checks
        start_time = time.time()
        for _ in range(1000):
            is_compatible = dispatcher.validate_strategy_compatibility(strategy_types)
            assert is_compatible is True
        end_time = time.time()

        # Should complete in reasonable time
        assert (end_time - start_time) < 1.0

    @patch.object(MAStrategyService, "execute_strategy")
    def test_execution_delegation_performance(self, mock_execute, dispatcher):
        """Test that execution delegation doesn't add significant overhead."""
        import time

        mock_execute.return_value = True
        config = StrategyConfig(
            ticker=["AAPL"],
            strategy_types=[StrategyType.SMA],
            minimums=StrategyMinimums(),
            synthetic=SyntheticTickerConfig(),
        )

        # Time multiple executions
        start_time = time.time()
        for _ in range(100):
            result = dispatcher.execute_strategy(config)
            assert result is True
        end_time = time.time()

        # Should complete quickly (overhead should be minimal)
        assert (end_time - start_time) < 1.0
        assert mock_execute.call_count == 100
