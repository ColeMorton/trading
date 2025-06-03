"""
Smoke test for MA Cross module with factory pattern integration.

This test ensures that the main MA Cross functionality still works
after implementing the factory pattern.
"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import polars as pl
import pytest

from app.strategies.ma_cross.tools.strategy_execution import execute_single_strategy
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals


def create_test_price_data(ticker="TEST", num_days=100):
    """Create realistic test price data."""
    dates = [datetime.now() - timedelta(days=i) for i in range(num_days, 0, -1)]
    # Create trending price data with some noise
    base_price = 100
    prices = []
    for i in range(num_days):
        trend = i * 0.3  # Upward trend
        noise = (i % 5 - 2) * 0.5  # Some noise
        prices.append(base_price + trend + noise)

    return pl.DataFrame(
        {
            "timestamp": dates,
            "open": [p - 0.5 for p in prices],
            "high": [p + 0.5 for p in prices],
            "low": [p - 0.5 for p in prices],
            "close": prices,
            "volume": [1000000] * num_days,
        }
    )


class TestMAcrossSmokeTest:
    """Smoke tests to ensure basic MA Cross functionality works."""

    def test_calculate_ma_and_signals_basic_sma(self):
        """Test basic SMA calculation works."""
        data = create_test_price_data()
        config = {"STRATEGY_TYPE": "SMA", "DIRECTION": "Long"}
        log = Mock()

        # Test that function executes without errors
        with patch("app.tools.strategy.concrete.calculate_mas") as mock_mas, patch(
            "app.tools.strategy.concrete.calculate_ma_signals"
        ) as mock_signals, patch(
            "app.tools.strategy.concrete.convert_signals_to_positions"
        ) as mock_positions:
            # Set up minimal mocks
            mock_mas.return_value = data.with_columns(
                [pl.lit(100.0).alias("sma_20"), pl.lit(100.0).alias("sma_50")]
            )
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100),
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))

            result = calculate_ma_and_signals(data, 20, 50, config, log)

            assert result is not None
            assert isinstance(result, pl.DataFrame)
            assert "Signal" in result.columns

            # Verify SMA was called with correct parameters
            mock_mas.assert_called_once_with(data, 20, 50, True, log)  # use_sma=True

    def test_calculate_ma_and_signals_basic_ema(self):
        """Test basic EMA calculation works."""
        data = create_test_price_data()
        config = {"STRATEGY_TYPE": "EMA", "DIRECTION": "Long"}
        log = Mock()

        with patch("app.tools.strategy.concrete.calculate_mas") as mock_mas, patch(
            "app.tools.strategy.concrete.calculate_ma_signals"
        ) as mock_signals, patch(
            "app.tools.strategy.concrete.convert_signals_to_positions"
        ) as mock_positions:
            mock_mas.return_value = data.with_columns(
                [pl.lit(100.0).alias("ema_12"), pl.lit(100.0).alias("ema_26")]
            )
            mock_signals.return_value = (
                pl.Series([False] * 100),
                pl.Series([False] * 100),
            )
            mock_positions.return_value = data.with_columns(pl.lit(0).alias("Signal"))

            result = calculate_ma_and_signals(data, 12, 26, config, log)

            assert result is not None
            assert isinstance(result, pl.DataFrame)

            # Verify EMA was called with correct parameters
            mock_mas.assert_called_once_with(data, 12, 26, False, log)  # use_sma=False

    def test_execute_single_strategy_smoke(self):
        """Test execute_single_strategy basic functionality."""
        config = {
            "STRATEGY_TYPE": "SMA",
            "SHORT_WINDOW": 20,
            "LONG_WINDOW": 50,
            "DIRECTION": "Long",
            "BASE_DIR": ".",
            "USE_YEARS": False,
            "USE_SYNTHETIC": False,
        }
        log = Mock()

        with patch(
            "app.strategies.ma_cross.tools.strategy_execution.get_data"
        ) as mock_get_data, patch(
            "app.strategies.ma_cross.tools.strategy_execution.calculate_ma_and_signals"
        ) as mock_calc, patch(
            "app.strategies.ma_cross.tools.strategy_execution.is_signal_current"
        ) as mock_signal, patch(
            "app.strategies.ma_cross.tools.strategy_execution.is_exit_signal_current"
        ) as mock_exit, patch(
            "app.strategies.ma_cross.tools.strategy_execution.backtest_strategy"
        ) as mock_backtest, patch(
            "app.tools.portfolio.filters.check_invalid_metrics"
        ) as mock_check, patch(
            "app.strategies.ma_cross.tools.strategy_execution.convert_stats"
        ) as mock_convert:
            # Set up test data and mocks
            test_data = create_test_price_data("BTC-USD")
            mock_get_data.return_value = test_data
            mock_calc.return_value = test_data.with_columns(pl.lit(0).alias("Signal"))
            mock_signal.return_value = True
            mock_exit.return_value = False

            # Mock portfolio
            mock_portfolio = Mock()
            mock_portfolio.stats.return_value = {
                "Total Return [%]": 25.5,
                "Win Rate [%]": 55.0,
                "Sharpe Ratio": 1.2,
            }
            mock_backtest.return_value = mock_portfolio
            mock_check.return_value = mock_portfolio.stats()
            mock_convert.return_value = {
                "Total Return [%]": 25.5,
                "Win Rate [%]": 55.0,
                "Sharpe Ratio": 1.2,
            }

            # Execute
            result = execute_single_strategy("BTC-USD", config, log)

            # Verify
            assert result is not None
            assert result["Strategy Type"] == "SMA"
            assert result["TICKER"] == "BTC-USD"
            assert "Total Return [%]" in result

            # Verify calculate_ma_and_signals was called
            mock_calc.assert_called_once()
            args = mock_calc.call_args[0]
            assert args[1] == 20  # short_window
            assert args[2] == 50  # long_window

    def test_strategy_type_selection(self):
        """Test that strategy type is correctly selected from config."""
        data = create_test_price_data()
        log = Mock()

        # Test 1: Config overrides parameter
        config_with_sma = {"STRATEGY_TYPE": "SMA", "DIRECTION": "Long"}

        with patch("app.tools.strategy.factory.factory.create_strategy") as mock_create:
            mock_strategy = Mock()
            mock_strategy.calculate.return_value = data.with_columns(
                pl.lit(0).alias("Signal")
            )
            mock_create.return_value = mock_strategy

            # Call with EMA as parameter but SMA in config
            result = calculate_ma_and_signals(data, 20, 50, config_with_sma, log, "EMA")

            # Verify SMA was used (from config, not parameter)
            mock_create.assert_called_once_with("SMA")

        # Test 2: Parameter used when no config STRATEGY_TYPE
        config_no_type = {"DIRECTION": "Long"}

        with patch("app.tools.strategy.factory.factory.create_strategy") as mock_create:
            mock_strategy = Mock()
            mock_strategy.calculate.return_value = data.with_columns(
                pl.lit(0).alias("Signal")
            )
            mock_create.return_value = mock_strategy

            # Call with EMA as parameter and no STRATEGY_TYPE in config
            result = calculate_ma_and_signals(data, 12, 26, config_no_type, log, "EMA")

            # Verify EMA was used (from parameter)
            mock_create.assert_called_once_with("EMA")
