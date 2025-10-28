"""
Test Suite for Unified Strategy Implementations

This module tests the unified strategy implementations to ensure they properly
extend BaseStrategy and implement StrategyInterface correctly.
"""

from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.core.interfaces.strategy import StrategyInterface
from app.tools.strategy.base import BaseStrategy
from app.tools.strategy.unified_strategies import (
    UnifiedMACDStrategy,
    UnifiedMAStrategy,
    UnifiedMeanReversionStrategy,
    UnifiedRangeStrategy,
)


class TestUnifiedMAStrategy:
    """Test cases for UnifiedMAStrategy implementation."""

    def test_inheritance(self):
        """Test that UnifiedMAStrategy properly inherits from required base classes."""
        sma_strategy = UnifiedMAStrategy("SMA")
        ema_strategy = UnifiedMAStrategy("EMA")

        assert isinstance(sma_strategy, BaseStrategy)
        assert isinstance(sma_strategy, StrategyInterface)
        assert isinstance(ema_strategy, BaseStrategy)
        assert isinstance(ema_strategy, StrategyInterface)

    def test_ma_type_validation(self):
        """Test that MA type validation works correctly."""
        # Valid MA types
        UnifiedMAStrategy("SMA")
        UnifiedMAStrategy("EMA")

        # Invalid MA type
        with pytest.raises(ValueError, match="Invalid MA type"):
            UnifiedMAStrategy("INVALID")

    def test_strategy_type_identification(self):
        """Test strategy type identification."""
        sma_strategy = UnifiedMAStrategy("SMA")
        ema_strategy = UnifiedMAStrategy("EMA")

        assert sma_strategy.get_strategy_type() == "SMA"
        assert ema_strategy.get_strategy_type() == "EMA"

    def test_parameter_validation(self):
        """Test parameter validation."""
        strategy = UnifiedMAStrategy("SMA")

        # Valid parameters
        valid_config = {"FAST_PERIOD": 10, "SLOW_PERIOD": 50}
        assert strategy.validate_parameters(valid_config) is True

        # Missing parameters
        invalid_config1 = {"FAST_PERIOD": 10}
        assert strategy.validate_parameters(invalid_config1) is False

        # Invalid window relationship
        invalid_config2 = {"FAST_PERIOD": 50, "SLOW_PERIOD": 10}
        assert strategy.validate_parameters(invalid_config2) is False

        # Invalid types
        invalid_config3 = {"FAST_PERIOD": "10", "SLOW_PERIOD": 50}
        assert strategy.validate_parameters(invalid_config3) is False

    def test_parameter_ranges(self):
        """Test parameter ranges."""
        strategy = UnifiedMAStrategy("SMA")
        ranges = strategy.get_parameter_ranges()

        assert "FAST_PERIOD" in ranges
        assert "SLOW_PERIOD" in ranges
        assert ranges["FAST_PERIOD"]["min"] > 0
        assert ranges["SLOW_PERIOD"]["min"] > ranges["FAST_PERIOD"]["min"]

    @patch("app.tools.strategy.unified_strategies.calculate_mas")
    @patch("app.tools.strategy.unified_strategies.calculate_ma_signals")
    @patch("app.tools.strategy.unified_strategies.convert_signals_to_positions")
    def test_calculate_method(self, mock_convert, mock_signals, mock_mas):
        """Test the calculate method with mocked dependencies."""
        strategy = UnifiedMAStrategy("SMA")

        # Create test data
        test_data = pl.DataFrame(
            {
                "Close": [100.0, 101.0, 102.0, 101.5, 103.0],
                "Date": [
                    "2023-01-01",
                    "2023-01-02",
                    "2023-01-03",
                    "2023-01-04",
                    "2023-01-05",
                ],
            },
        )

        # Mock return values
        mock_mas.return_value = test_data
        mock_signals.return_value = (pl.lit(True), pl.lit(False))
        mock_convert.return_value = test_data.with_columns(
            [pl.lit(1).alias("Position")],
        )

        # Mock logger
        mock_log = Mock()

        config = {"FAST_PERIOD": 10, "SLOW_PERIOD": 50, "DIRECTION": "Long"}

        result = strategy.calculate(test_data, 10, 50, config, mock_log)

        # Verify mocks were called
        mock_mas.assert_called_once()
        mock_signals.assert_called_once()
        mock_convert.assert_called_once()

        # Verify result structure
        assert isinstance(result, pl.DataFrame)
        assert "Position" in result.columns

    def test_calculate_validation_errors(self):
        """Test that calculate method properly validates inputs."""
        strategy = UnifiedMAStrategy("SMA")
        mock_log = Mock()

        test_data = pl.DataFrame(
            {
                "Close": [100.0, 101.0, 102.0],
                "Date": ["2023-01-01", "2023-01-02", "2023-01-03"],
            },
        )

        config = {"DIRECTION": "Long"}

        # Invalid windows
        with pytest.raises(ValueError, match="Invalid window parameters"):
            strategy.calculate(test_data, 50, 10, config, mock_log)

        # Invalid data (missing Close column)
        invalid_data = pl.DataFrame({"Price": [100.0, 101.0]})
        with pytest.raises(ValueError, match="Invalid data"):
            strategy.calculate(invalid_data, 10, 50, config, mock_log)


class TestUnifiedMACDStrategy:
    """Test cases for UnifiedMACDStrategy implementation."""

    def test_inheritance(self):
        """Test proper inheritance."""
        strategy = UnifiedMACDStrategy()
        assert isinstance(strategy, BaseStrategy)
        assert isinstance(strategy, StrategyInterface)

    def test_strategy_type(self):
        """Test strategy type identification."""
        strategy = UnifiedMACDStrategy()
        assert strategy.get_strategy_type() == "MACD"

    def test_parameter_validation(self):
        """Test MACD parameter validation."""
        strategy = UnifiedMACDStrategy()

        # Valid parameters
        valid_config = {"FAST_PERIOD": 12, "SLOW_PERIOD": 26, "SIGNAL_PERIOD": 9}
        assert strategy.validate_parameters(valid_config) is True

        # Missing SIGNAL_PERIOD
        invalid_config = {"FAST_PERIOD": 12, "SLOW_PERIOD": 26}
        assert strategy.validate_parameters(invalid_config) is False

    def test_parameter_ranges(self):
        """Test MACD parameter ranges."""
        strategy = UnifiedMACDStrategy()
        ranges = strategy.get_parameter_ranges()

        assert "SIGNAL_PERIOD" in ranges
        assert "FAST_PERIOD" in ranges
        assert "SLOW_PERIOD" in ranges

    @patch("app.tools.strategy.unified_strategies.convert_signals_to_positions")
    def test_calculate_requires_signal_window(self, mock_convert):
        """Test that MACD calculation requires SIGNAL_PERIOD."""
        strategy = UnifiedMACDStrategy()
        mock_log = Mock()

        test_data = pl.DataFrame({"Close": [100.0, 101.0, 102.0, 101.5, 103.0]})

        config = {"DIRECTION": "Long"}  # Missing SIGNAL_PERIOD

        with pytest.raises(
            ValueError,
            match="MACD strategy requires valid SIGNAL_PERIOD",
        ):
            strategy.calculate(test_data, 12, 26, config, mock_log)


class TestUnifiedMeanReversionStrategy:
    """Test cases for UnifiedMeanReversionStrategy implementation."""

    def test_inheritance(self):
        """Test proper inheritance."""
        strategy = UnifiedMeanReversionStrategy()
        assert isinstance(strategy, BaseStrategy)
        assert isinstance(strategy, StrategyInterface)

    def test_strategy_type(self):
        """Test strategy type identification."""
        strategy = UnifiedMeanReversionStrategy()
        assert strategy.get_strategy_type() == "MEAN_REVERSION"

    def test_parameter_validation(self):
        """Test parameter validation."""
        strategy = UnifiedMeanReversionStrategy()

        valid_config = {"FAST_PERIOD": 20, "SLOW_PERIOD": 50}
        assert strategy.validate_parameters(valid_config) is True

    def test_parameter_ranges(self):
        """Test parameter ranges include mean reversion specific parameters."""
        strategy = UnifiedMeanReversionStrategy()
        ranges = strategy.get_parameter_ranges()

        assert "RSI_OVERSOLD" in ranges
        assert "RSI_OVERBOUGHT" in ranges


class TestUnifiedRangeStrategy:
    """Test cases for UnifiedRangeStrategy implementation."""

    def test_inheritance(self):
        """Test proper inheritance."""
        strategy = UnifiedRangeStrategy()
        assert isinstance(strategy, BaseStrategy)
        assert isinstance(strategy, StrategyInterface)

    def test_strategy_type(self):
        """Test strategy type identification."""
        strategy = UnifiedRangeStrategy()
        assert strategy.get_strategy_type() == "RANGE"


class TestStrategyFactory:
    """Test cases for updated StrategyFactory with unified strategies."""

    def test_factory_creates_unified_strategies(self):
        """Test that factory can create unified strategies."""
        from app.tools.strategy.factory import StrategyFactory

        factory = StrategyFactory()

        # Test unified strategies
        sma_strategy = factory.create_strategy("UNIFIED_SMA")
        assert isinstance(sma_strategy, UnifiedMAStrategy)
        assert sma_strategy.get_strategy_type() == "SMA"

        ema_strategy = factory.create_strategy("UNIFIED_EMA")
        assert isinstance(ema_strategy, UnifiedMAStrategy)
        assert ema_strategy.get_strategy_type() == "EMA"

        macd_strategy = factory.create_strategy("UNIFIED_MACD")
        assert isinstance(macd_strategy, UnifiedMACDStrategy)

        # Test aliases
        alias_sma = factory.create_strategy("MA_CROSS_SMA")
        assert isinstance(alias_sma, UnifiedMAStrategy)

    def test_factory_backward_compatibility(self):
        """Test that factory maintains backward compatibility."""
        from app.tools.strategy.factory import StrategyFactory

        factory = StrategyFactory()

        # Original strategies should still work
        sma_strategy = factory.create_strategy("SMA")
        ema_strategy = factory.create_strategy("EMA")
        macd_strategy = factory.create_strategy("MACD")

        # They should be the original concrete implementations
        assert sma_strategy.__class__.__name__ == "SMAStrategy"
        assert ema_strategy.__class__.__name__ == "EMAStrategy"
        assert macd_strategy.__class__.__name__ == "MACDStrategy"

    def test_factory_lists_all_strategies(self):
        """Test that factory lists all available strategies."""
        from app.tools.strategy.factory import StrategyFactory

        factory = StrategyFactory()
        strategies = factory.get_available_strategies()

        # Should include both original and unified strategies
        assert "SMA" in strategies
        assert "UNIFIED_SMA" in strategies
        assert "MA_CROSS_SMA" in strategies
        assert "UNIFIED_MACD" in strategies
        assert "MEAN_REVERSION" in strategies
        assert "RANGE" in strategies


class TestStrategyAdapter:
    """Test cases for StrategyAdapter."""

    def test_adapter_maps_legacy_types(self):
        """Test that adapter correctly maps legacy strategy types."""
        from app.tools.strategy.strategy_adapter import StrategyAdapter

        adapter = StrategyAdapter()

        # Test mapping
        assert adapter._map_legacy_strategy_type("SMA") == "UNIFIED_SMA"
        assert adapter._map_legacy_strategy_type("EMA") == "UNIFIED_EMA"
        assert adapter._map_legacy_strategy_type("MACD") == "UNIFIED_MACD"

    def test_adapter_parameter_validation(self):
        """Test adapter parameter validation."""
        from app.tools.strategy.strategy_adapter import StrategyAdapter

        adapter = StrategyAdapter()

        valid_config = {"FAST_PERIOD": 10, "SLOW_PERIOD": 50}

        assert adapter.validate_strategy_parameters("SMA", valid_config) is True

        invalid_config = {"FAST_PERIOD": 50, "SLOW_PERIOD": 10}

        assert adapter.validate_strategy_parameters("SMA", invalid_config) is False

    def test_adapter_gets_parameter_ranges(self):
        """Test adapter retrieves parameter ranges."""
        from app.tools.strategy.strategy_adapter import StrategyAdapter

        adapter = StrategyAdapter()
        ranges = adapter.get_strategy_parameter_ranges("SMA")

        assert "FAST_PERIOD" in ranges
        assert "SLOW_PERIOD" in ranges


@pytest.fixture
def sample_price_data():
    """Fixture providing sample price data for testing."""
    return pl.DataFrame(
        {
            "Close": [100.0, 101.0, 102.0, 101.5, 103.0, 102.0, 104.0],
            "Date": [
                "2023-01-01",
                "2023-01-02",
                "2023-01-03",
                "2023-01-04",
                "2023-01-05",
                "2023-01-06",
                "2023-01-07",
            ],
        },
    )


@pytest.fixture
def mock_logger():
    """Fixture providing a mock logger."""
    return Mock()


if __name__ == "__main__":
    pytest.main([__file__])
