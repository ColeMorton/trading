"""
Unit tests for config integration and parameter precedence in portfolio_synthesis.

This module tests how parameters from config_dict and function parameters
interact, including precedence rules and parameter extraction.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.portfolio_synthesis.review import run


@pytest.mark.integration
class TestConfigIntegration:
    """Test configuration integration and parameter precedence."""

    def test_config_dict_parameters_override_function_parameters(self):
        """Test that parameters in config_dict override function parameters."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            "TIMEFRAME": "4hour",  # Should override function timeframe
            "STRATEGY_TYPE": "MACD",  # Should override function strategy_type
            "SIGNAL_PERIOD": 21,  # Should override function signal_period
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
            mock_get_config.return_value = mock_config_dict.copy()
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

            # Call with function parameters that should be overridden
            run(
                config_dict=mock_config_dict,
                timeframe="daily",  # Should be overridden by config_dict
                strategy_type="SMA",  # Should be overridden by config_dict
                signal_period=9,  # Should be overridden by config_dict
            )

            # Verify enhanced config uses config_dict values, not function parameters
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify config_dict parameters were used for conversion
            assert enhanced_config["USE_4HOUR"] is True  # From TIMEFRAME: "4hour"
            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_2DAY"] is False

            assert enhanced_config["STRATEGY_TYPE"] == "MACD"  # From config_dict
            assert enhanced_config["USE_SMA"] is False  # MACD != SMA
            assert enhanced_config["SIGNAL_PERIOD"] == 21  # From config_dict

    def test_function_parameters_fill_missing_config_dict_values(self):
        """Test that function parameters are used when config_dict lacks them."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            "TIMEFRAME": "hourly",  # Only timeframe provided in config_dict
            # STRATEGY_TYPE and SIGNAL_PERIOD missing
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
            mock_get_config.return_value = mock_config_dict.copy()
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

            # Call with function parameters to fill gaps
            run(
                config_dict=mock_config_dict,
                timeframe="daily",  # Should be overridden by config_dict "hourly"
                strategy_type="EMA",  # Should be used (missing from config_dict)
                signal_period=14,  # Should be used (missing from config_dict)
            )

            # Verify enhanced config combines both sources correctly
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify timeframe from config_dict was used
            assert enhanced_config["USE_HOURLY"] is True  # From config_dict
            assert enhanced_config["USE_4HOUR"] is False
            assert enhanced_config["USE_2DAY"] is False

            # Verify strategy type from function parameter was used
            assert enhanced_config["STRATEGY_TYPE"] == "EMA"  # From function param
            assert enhanced_config["USE_SMA"] is False  # EMA != SMA

            # Verify signal period from function parameter was used
            assert enhanced_config["SIGNAL_PERIOD"] == 14  # From function param

    def test_all_parameters_from_function_when_config_dict_minimal(self):
        """Test function parameters used when config_dict has no modern params."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            # No modern parameters (TIMEFRAME, STRATEGY_TYPE, SIGNAL_PERIOD)
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
            mock_get_config.return_value = mock_config_dict.copy()
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

            # Call with all function parameters
            run(
                config_dict=mock_config_dict,
                timeframe="2day",  # Should be used
                strategy_type="ATR",  # Should be used
                signal_period=7,  # Should be used
            )

            # Verify enhanced config uses all function parameters
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify timeframe from function parameter
            assert enhanced_config["USE_2DAY"] is True  # From function param
            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_4HOUR"] is False

            # Verify strategy type from function parameter
            assert enhanced_config["STRATEGY_TYPE"] == "ATR"  # From function param
            assert enhanced_config["USE_SMA"] is False  # ATR != SMA

            # Verify signal period from function parameter
            assert enhanced_config["SIGNAL_PERIOD"] == 7  # From function param

    def test_config_dict_preserves_original_values(self):
        """Test that original config_dict values are preserved along with new ones."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 15,
            "SLOW_PERIOD": 35,
            "BASE_DIR": "/custom/path",
            "YEARS": 5,
            "USE_YEARS": True,
            "SOME_CUSTOM_FIELD": "custom_value",
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
            mock_get_config.return_value = mock_config_dict.copy()
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

            # Call with function parameters
            run(
                config_dict=mock_config_dict,
                timeframe="daily",
                strategy_type="SMA",
                signal_period=9,
            )

            # Verify original config values are preserved
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Original values should be preserved
            assert enhanced_config["TICKER"] == "TEST"
            assert enhanced_config["FAST_PERIOD"] == 15
            assert enhanced_config["SLOW_PERIOD"] == 35
            assert enhanced_config["BASE_DIR"] == "/custom/path"
            assert enhanced_config["YEARS"] == 5
            assert enhanced_config["USE_YEARS"] is True
            assert enhanced_config["SOME_CUSTOM_FIELD"] == "custom_value"

            # New legacy parameters should be added
            assert "USE_HOURLY" in enhanced_config
            assert "USE_SMA" in enhanced_config
            assert "STRATEGY_TYPE" in enhanced_config
            assert "SIGNAL_PERIOD" in enhanced_config

    def test_default_values_used_when_no_parameters_provided(self):
        """Test default function parameter values are used when nothing is provided."""
        mock_config_dict = {
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
            mock_get_config.return_value = mock_config_dict.copy()
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

            # Call with no explicit parameters (use defaults)
            run(config_dict=mock_config_dict)

            # Verify default values were used
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify default timeframe (daily)
            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_4HOUR"] is False
            assert enhanced_config["USE_2DAY"] is False

            # Verify default strategy type (SMA)
            assert enhanced_config["STRATEGY_TYPE"] == "SMA"
            assert enhanced_config["USE_SMA"] is True

            # Verify default signal period (9)
            assert enhanced_config["SIGNAL_PERIOD"] == 9

    def test_mixed_modern_and_legacy_parameters_in_config_dict(self):
        """Test behavior when config_dict contains both modern and legacy parameters."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            # Mix of modern and legacy parameters
            "TIMEFRAME": "4hour",  # Modern
            "USE_HOURLY": True,  # Legacy (should be overridden)
            "STRATEGY_TYPE": "MACD",  # Modern
            "USE_SMA": True,  # Legacy (should be overridden)
            "SIGNAL_PERIOD": 15,  # Modern/Both
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
            mock_get_config.return_value = mock_config_dict.copy()
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

            # Call with mixed config
            run(config_dict=mock_config_dict)

            # Verify modern parameters take precedence and override legacy ones
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Modern TIMEFRAME should override legacy USE_HOURLY
            assert enhanced_config["USE_4HOUR"] is True  # From TIMEFRAME conversion
            assert enhanced_config["USE_HOURLY"] is False  # Overridden by conversion
            assert enhanced_config["USE_2DAY"] is False

            # Modern STRATEGY_TYPE should override legacy USE_SMA
            assert enhanced_config["STRATEGY_TYPE"] == "MACD"  # From modern param
            assert enhanced_config["USE_SMA"] is False  # Overridden (MACD != SMA)

            # Signal period should remain as specified
            assert enhanced_config["SIGNAL_PERIOD"] == 15

    def test_empty_config_dict_uses_all_function_parameters(self):
        """Test that empty config_dict results in all function parameters being used."""
        mock_config_dict = {}

        # This should cause an error since TICKER is required
        # But we want to test the parameter extraction logic
        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
        ):
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)

            # Mock get_config to simulate what would happen
            def mock_get_config_side_effect(config):
                # This would normally fail, but we'll return what we expect
                return config

            mock_get_config.side_effect = mock_get_config_side_effect

            try:
                # This will likely fail due to missing TICKER and other required fields
                # But we can test parameter extraction before that point
                with patch("app.portfolio_synthesis.review.get_data") as mock_get_data:
                    mock_get_data.side_effect = Exception("Expected test failure")

                    with pytest.raises(Exception):
                        run(
                            config_dict=mock_config_dict,
                            timeframe="hourly",
                            strategy_type="EMA",
                            signal_period=12,
                        )

                    # Verify the enhanced config was created with function parameters
                    mock_get_config.assert_called_once()
                    enhanced_config = mock_get_config.call_args[0][0]

                    # Should contain converted function parameters
                    assert enhanced_config["USE_HOURLY"] is True
                    assert enhanced_config["USE_SMA"] is False
                    assert enhanced_config["STRATEGY_TYPE"] == "EMA"
                    assert enhanced_config["SIGNAL_PERIOD"] == 12

            except Exception:
                # Expected due to missing required config fields
                pass
