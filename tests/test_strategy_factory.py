"""
Test suite for Strategy Factory Pattern implementation.

This test suite ensures that the strategy factory pattern correctly:
1. Creates strategy instances based on type
2. Maintains backward compatibility with existing code
3. Supports registration of new strategies
4. Handles errors gracefully
"""

from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.tools.exceptions import StrategyError
from app.tools.strategy.base import BaseStrategy
from app.tools.strategy.concrete import EMAStrategy, SMAStrategy
from app.tools.strategy.factory import StrategyFactory


@pytest.mark.integration
class TestStrategyFactory:
    """Test cases for the StrategyFactory class."""

    def test_factory_singleton(self):
        """Test that StrategyFactory follows singleton pattern."""
        factory1 = StrategyFactory()
        factory2 = StrategyFactory()
        assert factory1 is factory2

    def test_register_strategy(self):
        """Test registering a new strategy type."""
        factory = StrategyFactory()

        class CustomStrategy(BaseStrategy):
            def calculate(self, data, fast_period, slow_period, config, log):
                return data

        factory.register_strategy("CUSTOM", CustomStrategy)
        assert "CUSTOM" in factory._strategies
        assert factory._strategies["CUSTOM"] == CustomStrategy

    def test_create_sma_strategy(self):
        """Test creating an SMA strategy instance."""
        factory = StrategyFactory()
        strategy = factory.create_strategy("SMA")
        assert isinstance(strategy, SMAStrategy)

    def test_create_ema_strategy(self):
        """Test creating an EMA strategy instance."""
        factory = StrategyFactory()
        strategy = factory.create_strategy("EMA")
        assert isinstance(strategy, EMAStrategy)

    def test_create_unknown_strategy_raises_error(self):
        """Test that creating an unknown strategy raises StrategyError."""
        factory = StrategyFactory()
        with pytest.raises(StrategyError) as exc_info:
            factory.create_strategy("UNKNOWN")
        assert "Unknown strategy type: UNKNOWN" in str(exc_info.value)

    def test_create_strategy_case_insensitive(self):
        """Test that strategy creation is case-insensitive."""
        factory = StrategyFactory()
        strategy1 = factory.create_strategy("sma")
        strategy2 = factory.create_strategy("SMA")
        strategy3 = factory.create_strategy("Sma")

        assert isinstance(strategy1, SMAStrategy)
        assert isinstance(strategy2, SMAStrategy)
        assert isinstance(strategy3, SMAStrategy)

    def test_get_available_strategies(self):
        """Test getting list of available strategies."""
        factory = StrategyFactory()
        strategies = factory.get_available_strategies()
        assert "SMA" in strategies
        assert "EMA" in strategies
        assert len(strategies) >= 2

    def test_clear_registry(self):
        """Test clearing the strategy registry."""
        factory = StrategyFactory()

        # Add a custom strategy
        class CustomStrategy(BaseStrategy):
            def calculate(self, data, fast_period, slow_period, config, log):
                return data

        factory.register_strategy("CUSTOM", CustomStrategy)
        assert "CUSTOM" in factory._strategies

        # Clear and verify default strategies are restored
        factory.clear_registry()
        assert "SMA" in factory._strategies
        assert "EMA" in factory._strategies
        assert "CUSTOM" not in factory._strategies


@pytest.mark.integration
class TestBaseStrategy:
    """Test cases for the BaseStrategy abstract class."""

    def test_base_strategy_cannot_be_instantiated(self):
        """Test that BaseStrategy cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseStrategy()

    def test_base_strategy_requires_calculate_method(self):
        """Test that concrete strategies must implement calculate method."""

        class IncompleteStrategy(BaseStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteStrategy()

    def test_base_strategy_validate_periods(self):
        """Test period validation in base strategy."""

        class TestStrategy(BaseStrategy):
            def calculate(self, data, fast_period, slow_period, config, log):
                return data

        strategy = TestStrategy()
        log = Mock()

        # Valid periods
        assert strategy.validate_periods(5, 10, log) is True

        # Invalid: fast >= slow
        assert strategy.validate_periods(10, 5, log) is False
        log.assert_called_with(
            "Fast period (10) must be less than slow period (5)",
            "error",
        )

        # Invalid: negative period
        assert strategy.validate_periods(-5, 10, log) is False
        assert strategy.validate_periods(5, -10, log) is False

        # Invalid: zero period
        assert strategy.validate_periods(0, 10, log) is False
        assert strategy.validate_periods(5, 0, log) is False

    def test_base_strategy_validate_data(self):
        """Test data validation in base strategy."""

        class TestStrategy(BaseStrategy):
            def calculate(self, data, fast_period, slow_period, config, log):
                return data

        strategy = TestStrategy()
        log = Mock()

        # Valid data
        valid_data = pl.DataFrame({"Close": [1.0, 2.0, 3.0]})
        assert strategy.validate_data(valid_data, log) is True

        # Invalid: no Close column
        invalid_data = pl.DataFrame({"price": [1.0, 2.0, 3.0]})
        assert strategy.validate_data(invalid_data, log) is False
        log.assert_called_with("Data must contain 'Close' column", "error")

        # Invalid: empty dataframe
        empty_data = pl.DataFrame({"Close": []})
        assert strategy.validate_data(empty_data, log) is False

        # Invalid: None
        assert strategy.validate_data(None, log) is False


@pytest.mark.integration
class TestSMAStrategy:
    """Test cases for the SMAStrategy class."""

    def test_sma_strategy_calculate(self):
        """Test SMA strategy calculation."""
        strategy = SMAStrategy()
        log = Mock()
        config = {"DIRECTION": "Long"}

        # Create test data
        data = pl.DataFrame(
            {"Close": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]},
        )

        # Mock the imported functions
        with (
            patch("app.tools.strategy.concrete.calculate_mas") as mock_mas,
            patch("app.tools.strategy.concrete.calculate_ma_signals") as mock_signals,
            patch(
                "app.tools.strategy.concrete.convert_signals_to_positions",
            ) as mock_positions,
        ):
            # Setup mocks
            mock_mas.return_value = data.with_columns(
                [
                    pl.lit([2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5]).alias(
                        "sma_5",
                    ),
                    pl.lit([5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0]).alias(
                        "sma_10",
                    ),
                ],
            )
            mock_signals.return_value = (
                pl.Series(
                    [
                        False,
                        False,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                        False,
                        False,
                    ],
                ),
                pl.Series(
                    [
                        False,
                        False,
                        False,
                        False,
                        False,
                        True,
                        False,
                        False,
                        False,
                        False,
                    ],
                ),
            )
            mock_positions.return_value = data

            # Execute strategy
            strategy.calculate(data, 5, 10, config, log)

            # Verify calls
            mock_mas.assert_called_once_with(data, 5, 10, True, log)
            mock_signals.assert_called_once()
            mock_positions.assert_called_once()

            # Verify log messages
            log.assert_any_call(
                "Calculating Long SMAs and signals with fast period 5 and slow period 10",
            )

    def test_sma_strategy_with_rsi(self):
        """Test SMA strategy with RSI enabled."""
        strategy = SMAStrategy()
        log = Mock()
        config = {"DIRECTION": "Long", "USE_RSI": True, "RSI_WINDOW": 14}

        data = pl.DataFrame({"Close": list(range(1, 21))})  # 20 data points for RSI

        with (
            patch("app.tools.strategy.concrete.calculate_mas") as mock_mas,
            patch("app.tools.strategy.concrete.calculate_rsi") as mock_rsi,
            patch("app.tools.strategy.concrete.calculate_ma_signals") as mock_signals,
            patch(
                "app.tools.strategy.concrete.convert_signals_to_positions",
            ) as mock_positions,
        ):
            mock_mas.return_value = data
            mock_rsi.return_value = data.with_columns(pl.lit(50.0).alias("rsi"))
            mock_signals.return_value = (
                pl.Series([False] * 20),
                pl.Series([False] * 20),
            )
            mock_positions.return_value = data

            strategy.calculate(data, 5, 10, config, log)

            # Verify RSI was calculated
            mock_rsi.assert_called_once_with(data, 14)
            log.assert_any_call("Calculated RSI with period 14", "info")

    def test_sma_strategy_short_direction(self):
        """Test SMA strategy with short direction."""
        strategy = SMAStrategy()
        log = Mock()
        config = {"DIRECTION": "Short"}

        data = pl.DataFrame(
            {"Close": [10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0]},
        )

        with (
            patch("app.tools.strategy.concrete.calculate_mas") as mock_mas,
            patch("app.tools.strategy.concrete.calculate_ma_signals") as mock_signals,
            patch(
                "app.tools.strategy.concrete.convert_signals_to_positions",
            ) as mock_positions,
        ):
            entries = pl.Series(
                [False, False, False, True, False, False, False, False, False, False],
            )
            mock_mas.return_value = data
            mock_signals.return_value = (entries, pl.Series([False] * 10))
            mock_positions.return_value = data

            strategy.calculate(data, 3, 6, config, log)

            # Verify short direction in log
            log.assert_any_call(
                "Calculating Short SMAs and signals with fast period 3 and slow period 6",
            )


@pytest.mark.integration
class TestEMAStrategy:
    """Test cases for the EMAStrategy class."""

    def test_ema_strategy_calculate(self):
        """Test EMA strategy calculation."""
        strategy = EMAStrategy()
        log = Mock()
        config = {"DIRECTION": "Long"}

        data = pl.DataFrame(
            {"Close": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]},
        )

        with (
            patch("app.tools.strategy.concrete.calculate_mas") as mock_mas,
            patch("app.tools.strategy.concrete.calculate_ma_signals") as mock_signals,
            patch(
                "app.tools.strategy.concrete.convert_signals_to_positions",
            ) as mock_positions,
        ):
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 10),
                pl.Series([False] * 10),
            )
            mock_positions.return_value = data

            strategy.calculate(data, 12, 26, config, log)

            # Verify EMA was used (use_sma=False)
            mock_mas.assert_called_once_with(data, 12, 26, False, log)
            log.assert_any_call(
                "Calculating Long EMAs and signals with fast period 12 and slow period 26",
            )

    def test_ema_strategy_error_handling(self):
        """Test EMA strategy error handling."""
        strategy = EMAStrategy()
        log = Mock()
        config = {"DIRECTION": "Long"}

        data = pl.DataFrame({"Close": [1.0, 2.0, 3.0]})

        with patch("app.tools.strategy.concrete.calculate_mas") as mock_mas:
            mock_mas.side_effect = Exception("Calculation error")

            with pytest.raises(Exception) as exc_info:
                strategy.calculate(data, 5, 10, config, log)

            assert "Calculation error" in str(exc_info.value)
            log.assert_any_call(
                "Failed to calculate Long EMAs and signals: Calculation error",
                "error",
            )


@pytest.mark.integration
class TestStrategyIntegration:
    """Integration tests for strategy factory pattern."""

    def test_factory_integration_with_calculate_ma_and_signals(self):
        """Test that factory can be integrated with existing calculate_ma_and_signals."""
        factory = StrategyFactory()
        log = Mock()
        config = {"STRATEGY_TYPE": "SMA", "DIRECTION": "Long"}

        data = pl.DataFrame({"Close": list(range(1, 101))})  # 100 data points

        # Get strategy from factory
        strategy = factory.create_strategy(config.get("STRATEGY_TYPE", "EMA"))

        # Mock the strategy's dependencies
        with (
            patch("app.tools.strategy.concrete.calculate_mas") as mock_mas,
            patch("app.tools.strategy.concrete.calculate_ma_signals") as mock_signals,
            patch(
                "app.tools.strategy.concrete.convert_signals_to_positions",
            ) as mock_positions,
        ):
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100),
            )
            mock_positions.return_value = data

            # Execute strategy
            result = strategy.calculate(data, 20, 50, config, log)

            assert result is not None
            assert isinstance(result, pl.DataFrame)

    def test_backward_compatibility(self):
        """Test that new factory pattern maintains backward compatibility."""
        # This test ensures that existing code paths continue to work
        # when we integrate the factory pattern

        from app.tools.calculate_ma_and_signals import calculate_ma_and_signals

        log = Mock()
        config = {"STRATEGY_TYPE": "EMA", "DIRECTION": "Long"}

        data = pl.DataFrame({"Close": list(range(1, 51))})  # 50 data points

        # Mock all the dependencies
        with (
            patch("app.tools.strategy.concrete.calculate_mas") as mock_mas,
            patch("app.tools.strategy.concrete.calculate_rsi"),
            patch("app.tools.strategy.concrete.calculate_ma_signals") as mock_signals,
            patch(
                "app.tools.strategy.concrete.convert_signals_to_positions",
            ) as mock_positions,
        ):
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 50),
                pl.Series([False] * 50),
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))

            # This should work with existing function signature
            result = calculate_ma_and_signals(data, 12, 26, config, log, "EMA")

            assert result is not None
            assert "Signal" in result.columns
