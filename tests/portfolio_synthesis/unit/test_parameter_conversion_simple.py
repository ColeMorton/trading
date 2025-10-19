"""
Simplified unit tests for parameter conversion logic in portfolio_synthesis.

This module tests parameter conversion without running the full workflow,
focusing on the core conversion logic.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.portfolio_synthesis.review import run


class TestParameterConversionSimple:
    """Test parameter conversion logic in a simplified way."""

    def test_parameter_conversion_extraction_and_precedence(self):
        """Test parameter extraction and precedence logic."""
        # Test config_dict override behavior
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            "TIMEFRAME": "4hour",  # Should override function parameter
            "STRATEGY_TYPE": "MACD",  # Should override function parameter
            "SIGNAL_PERIOD": 21,  # Should override function parameter
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
        ):
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config_dict
            mock_get_data.side_effect = Exception("Stop execution here for testing")

            # Call with different function parameters (should be overridden)
            with pytest.raises(Exception, match="Stop execution here for testing"):
                run(
                    config_dict=mock_config_dict,
                    timeframe="daily",  # Should be overridden by config_dict
                    strategy_type="SMA",  # Should be overridden by config_dict
                    signal_period=9,  # Should be overridden by config_dict
                )

            # Verify enhanced_config contains conversion from config_dict values
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify conversions based on config_dict values, not function parameters
            assert enhanced_config["USE_4HOUR"] is True  # From "4hour" in config_dict
            assert enhanced_config["USE_HOURLY"] is False
            assert enhanced_config["USE_2DAY"] is False
            assert enhanced_config["STRATEGY_TYPE"] == "MACD"
            assert enhanced_config["USE_SMA"] is False  # MACD != SMA
            assert enhanced_config["SIGNAL_PERIOD"] == 21

    def test_parameter_conversion_function_param_fallback(self):
        """Test that function parameters are used when config_dict lacks them."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
            # No modern parameters - should use function parameters
        }

        with (
            patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
            patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
            patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
        ):
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config_dict
            mock_get_data.side_effect = Exception("Stop execution here for testing")

            # Call with function parameters (should be used)
            with pytest.raises(Exception, match="Stop execution here for testing"):
                run(
                    config_dict=mock_config_dict,
                    timeframe="hourly",  # Should be used
                    strategy_type="EMA",  # Should be used
                    signal_period=14,  # Should be used
                )

            # Verify enhanced_config contains conversion from function parameters
            mock_get_config.assert_called_once()
            enhanced_config = mock_get_config.call_args[0][0]

            # Verify conversions based on function parameters
            assert enhanced_config["USE_HOURLY"] is True  # From "hourly" function param
            assert enhanced_config["USE_4HOUR"] is False
            assert enhanced_config["USE_2DAY"] is False
            assert enhanced_config["STRATEGY_TYPE"] == "EMA"
            assert enhanced_config["USE_SMA"] is False  # EMA != SMA
            assert enhanced_config["SIGNAL_PERIOD"] == 14

    @pytest.mark.parametrize(
        "timeframe,expected_hourly,expected_4hour,expected_2day",
        [
            ("hourly", True, False, False),
            ("4hour", False, True, False),
            ("2day", False, False, True),
            ("daily", False, False, False),
        ],
    )
    def test_all_timeframe_conversions(
        self, timeframe, expected_hourly, expected_4hour, expected_2day
    ):
        """Test all timeframe conversion combinations."""
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
        ):
            mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
            mock_get_config.return_value = mock_config_dict
            mock_get_data.side_effect = Exception("Stop execution here for testing")

            with pytest.raises(Exception, match="Stop execution here for testing"):
                run(config_dict=mock_config_dict, timeframe=timeframe)

            enhanced_config = mock_get_config.call_args[0][0]
            assert enhanced_config["USE_HOURLY"] == expected_hourly
            assert enhanced_config["USE_4HOUR"] == expected_4hour
            assert enhanced_config["USE_2DAY"] == expected_2day

    def test_all_strategy_type_conversions(self):
        """Test all strategy type conversion combinations."""
        strategy_conversions = [
            ("SMA", True, "SMA"),
            ("EMA", False, "EMA"),
            ("MACD", False, "MACD"),
            ("ATR", False, "ATR"),
        ]

        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        for (
            strategy_type,
            expected_use_sma,
            expected_strategy_type,
        ) in strategy_conversions:
            with (
                self.subTest(strategy_type=strategy_type),
                patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
                patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
                patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            ):
                mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
                mock_get_config.return_value = mock_config_dict
                mock_get_data.side_effect = Exception("Stop execution here for testing")

                with pytest.raises(Exception, match="Stop execution here for testing"):
                    run(config_dict=mock_config_dict, strategy_type=strategy_type)

                enhanced_config = mock_get_config.call_args[0][0]
                assert enhanced_config["USE_SMA"] == expected_use_sma
                assert enhanced_config["STRATEGY_TYPE"] == expected_strategy_type

    def test_signal_period_conversion(self):
        """Test signal period parameter conversion."""
        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        test_signal_periods = [5, 9, 14, 21, 30]

        for signal_period in test_signal_periods:
            with (
                self.subTest(signal_period=signal_period),
                patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
                patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
                patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            ):
                mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
                mock_get_config.return_value = mock_config_dict
                mock_get_data.side_effect = Exception("Stop execution here for testing")

                with pytest.raises(Exception, match="Stop execution here for testing"):
                    run(config_dict=mock_config_dict, signal_period=signal_period)

                enhanced_config = mock_get_config.call_args[0][0]
                assert enhanced_config["SIGNAL_PERIOD"] == signal_period

    def test_combined_parameter_conversion(self):
        """Test combined parameter conversion scenarios."""
        test_cases = [
            {
                "timeframe": "4hour",
                "strategy_type": "MACD",
                "signal_period": 12,
                "expected": {
                    "USE_HOURLY": False,
                    "USE_4HOUR": True,
                    "USE_2DAY": False,
                    "USE_SMA": False,
                    "STRATEGY_TYPE": "MACD",
                    "SIGNAL_PERIOD": 12,
                },
            },
            {
                "timeframe": "hourly",
                "strategy_type": "SMA",
                "signal_period": 9,
                "expected": {
                    "USE_HOURLY": True,
                    "USE_4HOUR": False,
                    "USE_2DAY": False,
                    "USE_SMA": True,
                    "STRATEGY_TYPE": "SMA",
                    "SIGNAL_PERIOD": 9,
                },
            },
            {
                "timeframe": "2day",
                "strategy_type": "ATR",
                "signal_period": 21,
                "expected": {
                    "USE_HOURLY": False,
                    "USE_4HOUR": False,
                    "USE_2DAY": True,
                    "USE_SMA": False,
                    "STRATEGY_TYPE": "ATR",
                    "SIGNAL_PERIOD": 21,
                },
            },
        ]

        mock_config_dict = {
            "TICKER": "TEST",
            "FAST_PERIOD": 10,
            "SLOW_PERIOD": 20,
            "BASE_DIR": "/tmp",
        }

        for test_case in test_cases:
            with (
                self.subTest(test_case=test_case),
                patch("app.portfolio_synthesis.review.setup_logging") as mock_logging,
                patch("app.portfolio_synthesis.review.get_config") as mock_get_config,
                patch("app.portfolio_synthesis.review.get_data") as mock_get_data,
            ):
                mock_logging.return_value = (MagicMock(), MagicMock(), None, None)
                mock_get_config.return_value = mock_config_dict
                mock_get_data.side_effect = Exception("Stop execution here for testing")

                with pytest.raises(Exception, match="Stop execution here for testing"):
                    run(
                        config_dict=mock_config_dict,
                        timeframe=test_case["timeframe"],
                        strategy_type=test_case["strategy_type"],
                        signal_period=test_case["signal_period"],
                    )

                enhanced_config = mock_get_config.call_args[0][0]

                for key, expected_value in test_case["expected"].items():
                    assert (
                        enhanced_config[key] == expected_value
                    ), f"Expected {key}={expected_value}, got {enhanced_config[key]}"
