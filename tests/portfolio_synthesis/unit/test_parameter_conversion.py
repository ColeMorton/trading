"""
Unit tests for parameter conversion logic in portfolio_synthesis.

This module tests the convert_parameters_to_legacy function and related
parameter mapping functionality in isolation.
"""

from unittest.mock import MagicMock, patch

import numpy as np

from app.portfolio_synthesis.review import run


def create_mock_portfolio():
    """Create a properly configured mock portfolio for testing."""
    mock_portfolio = MagicMock()
    mock_portfolio.stats.return_value = {}

    mock_value_series = MagicMock()
    mock_value_series.__getitem__ = MagicMock(return_value=1000)
    mock_value_series.index = ["2023-01-01", "2023-01-02"]
    mock_value_series.values = np.array([1000, 1050])
    mock_portfolio.value.return_value = mock_value_series

    return mock_portfolio


class TestParameterConversionLogic:
    """Test parameter conversion from new format to legacy format."""

    def test_timeframe_conversion_hourly(self):
        """Test timeframe 'hourly' converts to correct legacy flags."""
        # We need to test the internal convert_parameters_to_legacy function
        # Since it's defined inside the run function, we'll test via run behavior

        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_ma_and_signals",
            ) as mock_calc_ma,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test hourly timeframe conversion
            run(config_dict=mock_config, timeframe="hourly")

            # Verify get_config was called with enhanced config containing legacy flags
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            assert enhanced_config["USE_HOURLY"] is True
            assert enhanced_config["USE_4HOUR"] is False
            assert enhanced_config["USE_2DAY"] is False

    def test_timeframe_conversion_4hour(self):
        """Test timeframe '4hour' converts to correct legacy flags."""
        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_ma_and_signals",
            ) as mock_calc_ma,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test 4hour timeframe conversion
            run(config_dict=mock_config, timeframe="4hour")

            # Verify get_config was called with enhanced config containing legacy flags
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_4HOUR"] is True
            assert enhanced_config["USE_2DAY"] is False

    def test_timeframe_conversion_2day(self):
        """Test timeframe '2day' converts to correct legacy flags."""
        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_ma_and_signals",
            ) as mock_calc_ma,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test 2day timeframe conversion
            run(config_dict=mock_config, timeframe="2day")

            # Verify get_config was called with enhanced config containing legacy flags
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_4HOUR"] is False
            assert enhanced_config["USE_2DAY"] is True

    def test_timeframe_conversion_daily_default(self):
        """Test timeframe 'daily' (default) converts to all false flags."""
        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_ma_and_signals",
            ) as mock_calc_ma,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test daily timeframe conversion (default)
            run(config_dict=mock_config, timeframe="daily")

            # Verify get_config was called with enhanced config containing legacy flags
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_4HOUR"] is False
            assert enhanced_config["USE_2DAY"] is False

    def test_strategy_type_conversion_sma(self):
        """Test strategy_type 'SMA' converts to USE_SMA=True."""
        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_ma_and_signals",
            ) as mock_calc_ma,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test SMA strategy type conversion
            run(config_dict=mock_config, strategy_type="SMA")

            # Verify get_config was called with enhanced config containing legacy flags
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            assert enhanced_config["USE_SMA"] is True
            assert enhanced_config["STRATEGY_TYPE"] == "SMA"

    def test_strategy_type_conversion_non_sma(self):
        """Test non-SMA strategy types convert to USE_SMA=False."""
        for strategy_type in ["EMA", "MACD", "ATR"]:
            with self.subTest(strategy_type=strategy_type):
                mock_config = {
                    "TICKER": "TEST",
                    "FAST_PERIOD": 10,
                    "SLOW_PERIOD": 20,
                    "BASE_DIR": "/tmp",
                }

                with (
                    patch(
                        "app.portfolio_synthesis.review.setup_logging",
                    ) as mock_logging,
                    patch(
                        "app.portfolio_synthesis.review.get_config",
                    ) as mock_get_config,
                    patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
                    patch(
                        "app.portfolio_synthesis.review.calculate_ma_and_signals",
                    ) as mock_calc_ma,
                    patch(
                        "app.portfolio_synthesis.review.calculate_macd_and_signals",
                    ) as mock_calc_macd,
                    patch(
                        "app.portfolio_synthesis.review.backtest_strategy",
                    ) as mock_backtest,
                    patch("app.portfolio_synthesis.review.os.makedirs"),
                    patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
                    patch("app.tools.plotting.create_portfolio_plot_files"),
                ):
                    # Setup mocks
                    mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
                    mock_get_config.return_value = mock_config.copy()
                    mock_get_data.return_value = MagicMock()
                    mock_calc_ma.return_value = MagicMock()
                    mock_calc_macd.return_value = MagicMock()

                    mock_portfolio = MagicMock()
                    mock_portfolio.stats.return_value = {}
                    mock_portfolio.value.return_value = MagicMock()
                    mock_portfolio.value.return_value.__getitem__ = MagicMock(
                        return_value=1000,
                    )
                    mock_portfolio.value.return_value.index = []
                    mock_portfolio.value.return_value.values = []
                    mock_backtest.return_value = mock_portfolio

                    mock_df.return_value.write_csv = MagicMock()

                    # Test non-SMA strategy type conversion
                    run(config_dict=mock_config, strategy_type=strategy_type)

                    # Verify get_config was called with enhanced config containing legacy flags
                    mock_get_config.assert_called_once()
                    enhanced_config = mock_get_config.call_args[0][0]

                    assert enhanced_config["USE_SMA"] is False
                    assert enhanced_config["STRATEGY_TYPE"] == strategy_type

    def test_signal_period_conversion(self):
        """Test signal_period parameter is correctly passed through."""
        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        test_signal_period = 14

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_ma_and_signals",
            ) as mock_calc_ma,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_ma.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test signal period conversion
            run(config_dict=mock_config, signal_period=test_signal_period)

            # Verify get_config was called with enhanced config containing signal period
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            assert enhanced_config["SIGNAL_PERIOD"] == test_signal_period

    def test_complete_parameter_conversion_combination(self):
        """Test complete parameter conversion with all parameters combined."""
        mock_config = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            patch(
                "app.portfolio_synthesis.review.calculate_macd_and_signals",
            ) as mock_calc_macd,
            patch("app.portfolio_synthesis.review.backtest_strategy") as mock_backtest,
            patch("app.portfolio_synthesis.review.os.makedirs"),
            patch("app.portfolio_synthesis.review.pl.DataFrame") as mock_df,
            patch("app.tools.plotting.create_portfolio_plot_files"),
        ):
            # Setup mocks
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config.copy()
            mock_get_data.return_value = MagicMock()
            mock_calc_macd.return_value = MagicMock()

            mock_portfolio = MagicMock()
            mock_portfolio.stats.return_value = {}
            mock_portfolio.value.return_value = MagicMock()
            mock_portfolio.value.return_value.__getitem__ = MagicMock(return_value=1000)
            mock_portfolio.value.return_value.index = []
            mock_portfolio.value.return_value.values = []
            mock_backtest.return_value = mock_portfolio

            mock_df.return_value.write_csv = MagicMock()

            # Test complete parameter conversion
            run(
                config_dict=mock_config,
                timeframe="4hour",
                strategy_type="MACD",
                signal_period=21,
            )

            # Verify get_config was called with enhanced config containing all conversions
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify timeframe conversion
            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_4HOUR"] is True
            assert enhanced_config["USE_2DAY"] is False

            # Verify strategy type conversion
            assert enhanced_config["USE_SMA"] is False
            assert enhanced_config["STRATEGY_TYPE"] == "MACD"

            # Verify signal period
            assert enhanced_config["SIGNAL_PERIOD"] == 21
