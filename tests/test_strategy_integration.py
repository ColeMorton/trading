"""
Integration tests for the strategy factory pattern with existing codebase.

This test file ensures that the factory pattern integration doesn't break
any existing functionality.
"""

import pytest
import polars as pl
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ma_cross.tools.strategy_execution import execute_single_strategy
from app.tools.strategy.factory import factory


def create_test_data(num_days=100):
    """Create test price data."""
    dates = [datetime.now() - timedelta(days=i) for i in range(num_days, 0, -1)]
    prices = [100 + i * 0.5 for i in range(num_days)]  # Upward trend
    
    return pl.DataFrame({
        "timestamp": dates,
        "close": prices
    })


class TestFactoryIntegrationWithExistingCode:
    """Test that factory pattern works with existing code paths."""
    
    def test_calculate_ma_and_signals_with_sma(self):
        """Test calculate_ma_and_signals works with SMA strategy."""
        data = create_test_data()
        config = {"STRATEGY_TYPE": "SMA", "DIRECTION": "Long"}
        log = Mock()
        
        with patch('app.tools.strategy.concrete.calculate_mas') as mock_mas, \
             patch('app.tools.strategy.concrete.calculate_ma_signals') as mock_signals, \
             patch('app.tools.strategy.concrete.convert_signals_to_positions') as mock_positions:
            
            # Setup mocks
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100)
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))
            
            # Execute
            result = calculate_ma_and_signals(data, 10, 20, config, log)
            
            # Verify
            assert result is not None
            assert "Signal" in result.columns
            mock_mas.assert_called_once()
            
    def test_calculate_ma_and_signals_with_ema(self):
        """Test calculate_ma_and_signals works with EMA strategy."""
        data = create_test_data()
        config = {"DIRECTION": "Long"}  # No STRATEGY_TYPE, should default to EMA
        log = Mock()
        
        with patch('app.tools.strategy.concrete.calculate_mas') as mock_mas, \
             patch('app.tools.strategy.concrete.calculate_ma_signals') as mock_signals, \
             patch('app.tools.strategy.concrete.convert_signals_to_positions') as mock_positions:
            
            # Setup mocks
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100)
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))
            
            # Execute with default strategy type
            result = calculate_ma_and_signals(data, 12, 26, config, log, "EMA")
            
            # Verify
            assert result is not None
            # Verify EMA was used (use_sma=False)
            mock_mas.assert_called_with(data, 12, 26, False, log)
            
    def test_execute_single_strategy_with_factory(self):
        """Test execute_single_strategy works with factory pattern."""
        config = {
            "STRATEGY_TYPE": "SMA",
            "SHORT_WINDOW": 10,
            "LONG_WINDOW": 20,
            "DIRECTION": "Long",
            "BASE_DIR": ".",
            "USE_YEARS": False
        }
        log = Mock()
        
        with patch('app.ma_cross.tools.strategy_execution.get_data') as mock_get_data, \
             patch('app.ma_cross.tools.strategy_execution.calculate_ma_and_signals') as mock_calc, \
             patch('app.ma_cross.tools.strategy_execution.is_signal_current') as mock_signal, \
             patch('app.ma_cross.tools.strategy_execution.is_exit_signal_current') as mock_exit, \
             patch('app.ma_cross.tools.strategy_execution.backtest_strategy') as mock_backtest, \
             patch('app.tools.portfolio.filters.check_invalid_metrics') as mock_check, \
             patch('app.ma_cross.tools.strategy_execution.convert_stats') as mock_convert:
            
            # Setup mocks
            test_data = create_test_data()
            mock_get_data.return_value = test_data
            mock_calc.return_value = test_data.with_columns(pl.lit(0).alias("Signal"))
            mock_signal.return_value = False
            mock_exit.return_value = False
            
            # Mock portfolio and stats
            mock_portfolio = Mock()
            mock_portfolio.stats.return_value = {"Total Return [%]": 25.0}
            mock_backtest.return_value = mock_portfolio
            mock_check.return_value = {"Total Return [%]": 25.0}
            mock_convert.return_value = {"Total Return [%]": 25.0}
            
            # Execute
            result = execute_single_strategy("BTC-USD", config, log)
            
            # Verify
            assert result is not None
            assert result["Strategy Type"] == "SMA"
            mock_calc.assert_called_once()
            
    def test_factory_available_strategies(self):
        """Test that factory provides correct available strategies."""
        strategies = factory.get_available_strategies()
        assert "SMA" in strategies
        assert "EMA" in strategies
        
    def test_backward_compatibility_with_string_parameter(self):
        """Test backward compatibility when strategy_type is passed as string."""
        data = create_test_data()
        config = {"DIRECTION": "Long"}  # No STRATEGY_TYPE in config
        log = Mock()
        
        with patch('app.tools.strategy.concrete.calculate_mas') as mock_mas, \
             patch('app.tools.strategy.concrete.calculate_ma_signals') as mock_signals, \
             patch('app.tools.strategy.concrete.convert_signals_to_positions') as mock_positions:
            
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100)
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))
            
            # Test with SMA passed as parameter
            result = calculate_ma_and_signals(data, 20, 50, config, log, "SMA")
            
            # Verify SMA was used
            mock_mas.assert_called_with(data, 20, 50, True, log)
            
    def test_config_override_strategy_type(self):
        """Test that config STRATEGY_TYPE overrides parameter."""
        data = create_test_data()
        config = {"STRATEGY_TYPE": "EMA", "DIRECTION": "Long"}
        log = Mock()
        
        with patch('app.tools.strategy.concrete.calculate_mas') as mock_mas, \
             patch('app.tools.strategy.concrete.calculate_ma_signals') as mock_signals, \
             patch('app.tools.strategy.concrete.convert_signals_to_positions') as mock_positions:
            
            mock_mas.return_value = data
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100)
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))
            
            # Pass SMA as parameter but config says EMA
            result = calculate_ma_and_signals(data, 12, 26, config, log, "SMA")
            
            # Verify EMA was used (config overrides parameter)
            mock_mas.assert_called_with(data, 12, 26, False, log)
            
    def test_error_handling_with_invalid_strategy(self):
        """Test error handling when invalid strategy type is provided."""
        data = create_test_data()
        config = {"STRATEGY_TYPE": "INVALID", "DIRECTION": "Long"}
        log = Mock()
        
        with pytest.raises(Exception) as exc_info:
            calculate_ma_and_signals(data, 10, 20, config, log)
            
        assert "Unknown strategy type: INVALID" in str(exc_info.value)
        log.assert_called_with(
            "Failed to calculate Long INVALIDs and signals: Unknown strategy type: INVALID. Available strategies: SMA, EMA",
            "error"
        )