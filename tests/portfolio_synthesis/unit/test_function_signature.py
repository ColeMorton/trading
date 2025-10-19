"""
Unit tests for function signature validation in portfolio_synthesis.

This module tests the function interface, parameter validation,
and default value behavior.
"""

import inspect

import pytest

from app.portfolio_synthesis.review import run


class TestFunctionSignature:
    """Test function signature and parameter interface."""

    def test_function_signature_parameters(self):
        """Test that the function has the correct parameters with correct defaults."""
        # Get function signature
        sig = inspect.signature(run)
        params = sig.parameters

        # Verify required parameters exist
        assert "config_dict" in params
        assert "portfolio_file" in params
        assert "timeframe" in params
        assert "strategy_type" in params
        assert "signal_period" in params

        # Verify parameter defaults
        assert params["config_dict"].default is None
        assert params["portfolio_file"].default is None
        assert params["timeframe"].default == "daily"
        assert params["strategy_type"].default == "SMA"
        assert params["signal_period"].default == 9

    def test_function_accepts_new_parameters_with_defaults(self):
        """Test that function can be called with just new parameters using defaults."""
        # This tests that the function can be imported and called
        # We don't need to test the full execution, just parameter acceptance

        try:
            # Import should work
            from app.portfolio_synthesis.review import run

            # Get signature to verify callable interface
            sig = inspect.signature(run)

            # Test that we can bind parameters
            bound_args = sig.bind()
            bound_args.apply_defaults()

            # Verify default values are applied
            assert bound_args.arguments["config_dict"] is None
            assert bound_args.arguments["portfolio_file"] is None
            assert bound_args.arguments["timeframe"] == "daily"
            assert bound_args.arguments["strategy_type"] == "SMA"
            assert bound_args.arguments["signal_period"] == 9

        except ImportError:
            pytest.fail("Could not import run function")
        except Exception as e:
            pytest.fail(f"Unexpected error testing function signature: {e}")

    def test_function_parameter_binding_with_all_parameters(self):
        """Test parameter binding with all parameters provided."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)

        # Test binding with all parameters
        test_config = {"TICKER": "TEST"}
        test_portfolio_file = "test.json"
        test_timeframe = "4hour"
        test_strategy_type = "MACD"
        test_signal_period = 14

        bound_args = sig.bind(
            config_dict=test_config,
            portfolio_file=test_portfolio_file,
            timeframe=test_timeframe,
            strategy_type=test_strategy_type,
            signal_period=test_signal_period,
        )

        # Verify bound arguments
        assert bound_args.arguments["config_dict"] == test_config
        assert bound_args.arguments["portfolio_file"] == test_portfolio_file
        assert bound_args.arguments["timeframe"] == test_timeframe
        assert bound_args.arguments["strategy_type"] == test_strategy_type
        assert bound_args.arguments["signal_period"] == test_signal_period

    def test_function_parameter_binding_with_partial_parameters(self):
        """Test parameter binding with only some parameters provided."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)

        # Test binding with partial parameters
        bound_args = sig.bind(config_dict={"TICKER": "TEST"}, timeframe="hourly")
        bound_args.apply_defaults()

        # Verify provided and default values
        assert bound_args.arguments["config_dict"] == {"TICKER": "TEST"}
        assert bound_args.arguments["portfolio_file"] is None  # Default
        assert bound_args.arguments["timeframe"] == "hourly"  # Provided
        assert bound_args.arguments["strategy_type"] == "SMA"  # Default
        assert bound_args.arguments["signal_period"] == 9  # Default

    def test_function_parameter_types(self):
        """Test that parameters can accept expected types."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)

        # Test various valid parameter combinations
        valid_parameter_sets = [
            {
                "config_dict": None,
                "portfolio_file": None,
                "timeframe": "daily",
                "strategy_type": "SMA",
                "signal_period": 9,
            },
            {
                "config_dict": {"TICKER": "TEST"},
                "portfolio_file": "test.json",
                "timeframe": "hourly",
                "strategy_type": "EMA",
                "signal_period": 21,
            },
            {
                "config_dict": {},
                "portfolio_file": None,
                "timeframe": "4hour",
                "strategy_type": "MACD",
                "signal_period": 14,
            },
            {
                "config_dict": {"TICKER": "BTC-USD", "FAST_PERIOD": 10},
                "portfolio_file": "/path/to/portfolio.json",
                "timeframe": "2day",
                "strategy_type": "ATR",
                "signal_period": 7,
            },
        ]

        for params in valid_parameter_sets:
            try:
                sig.bind(**params)
                # If binding succeeds, parameters are accepted
                assert True
            except TypeError as e:
                pytest.fail(f"Valid parameters rejected: {params}, error: {e}")

    def test_function_has_proper_docstring(self):
        """Test that the function has proper documentation."""
        from app.portfolio_synthesis.review import run

        # Verify docstring exists and contains expected information
        assert run.__doc__ is not None
        docstring = run.__doc__.strip()

        # Verify key documentation elements
        assert "Run portfolio synthesis analysis" in docstring
        assert "Args:" in docstring
        assert "Returns:" in docstring

        # Verify new parameters are documented
        assert "timeframe" in docstring
        assert "strategy_type" in docstring
        assert "signal_period" in docstring

        # Verify parameter descriptions
        assert "hourly, 4hour, daily (default), 2day" in docstring
        assert "SMA (default), EMA, MACD, ATR" in docstring
        assert "Signal period for MACD strategy" in docstring

    def test_backward_compatibility_original_signature(self):
        """Test that function maintains backward compatibility with original signature."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)

        # Test that original parameters still work (config_dict, portfolio_file)
        bound_args = sig.bind(config_dict={"TICKER": "TEST"})
        bound_args.apply_defaults()

        # Original parameters should be bound
        assert bound_args.arguments["config_dict"] == {"TICKER": "TEST"}
        assert bound_args.arguments["portfolio_file"] is None

        # New parameters should have defaults
        assert bound_args.arguments["timeframe"] == "daily"
        assert bound_args.arguments["strategy_type"] == "SMA"
        assert bound_args.arguments["signal_period"] == 9

    def test_function_callable_without_parameters(self):
        """Test that function is callable without any parameters (using all defaults)."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)

        # Should be able to bind with no parameters
        bound_args = sig.bind()
        bound_args.apply_defaults()

        # All parameters should have default values
        assert bound_args.arguments["config_dict"] is None
        assert bound_args.arguments["portfolio_file"] is None
        assert bound_args.arguments["timeframe"] == "daily"
        assert bound_args.arguments["strategy_type"] == "SMA"
        assert bound_args.arguments["signal_period"] == 9

    def test_parameter_position_and_keyword_access(self):
        """Test that parameters can be accessed both positionally and by keyword."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)

        # Test positional parameter binding
        bound_positional = sig.bind(
            {"TICKER": "TEST"},  # config_dict
            "portfolio.json",  # portfolio_file
            "hourly",  # timeframe
            "MACD",  # strategy_type
            14,  # signal_period
        )

        assert bound_positional.arguments["config_dict"] == {"TICKER": "TEST"}
        assert bound_positional.arguments["portfolio_file"] == "portfolio.json"
        assert bound_positional.arguments["timeframe"] == "hourly"
        assert bound_positional.arguments["strategy_type"] == "MACD"
        assert bound_positional.arguments["signal_period"] == 14

        # Test keyword parameter binding
        bound_keyword = sig.bind(
            signal_period=21,
            strategy_type="EMA",
            timeframe="4hour",
            portfolio_file="test.json",
            config_dict={"TICKER": "BTC"},
        )

        assert bound_keyword.arguments["config_dict"] == {"TICKER": "BTC"}
        assert bound_keyword.arguments["portfolio_file"] == "test.json"
        assert bound_keyword.arguments["timeframe"] == "4hour"
        assert bound_keyword.arguments["strategy_type"] == "EMA"
        assert bound_keyword.arguments["signal_period"] == 21

    def test_function_signature_string_representation(self):
        """Test the string representation of the function signature."""
        from app.portfolio_synthesis.review import run

        sig = inspect.signature(run)
        sig_str = str(sig)

        # Verify signature string contains expected parameters with defaults
        expected_elements = [
            "config_dict=None",
            "portfolio_file=None",
            "timeframe='daily'",
            "strategy_type='SMA'",
            "signal_period=9",
        ]

        for element in expected_elements:
            assert element in sig_str, f"Expected '{element}' in signature '{sig_str}'"
