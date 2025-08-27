"""
Test configuration fixtures for portfolio_review tests.

This module provides test data for various parameter combinations,
configurations, and scenarios used in portfolio review testing.
"""

import pytest
from typing import Dict, Any, List, Tuple


@pytest.fixture
def valid_timeframes():
    """Valid timeframe values for testing."""
    return ["hourly", "4hour", "daily", "2day"]


@pytest.fixture 
def valid_strategy_types():
    """Valid strategy type values for testing."""
    return ["SMA", "EMA", "MACD", "ATR"]


@pytest.fixture
def valid_signal_periods():
    """Valid signal period values for testing."""
    return [5, 9, 14, 21]


@pytest.fixture
def invalid_timeframes():
    """Invalid timeframe values for testing."""
    return ["weekly", "monthly", "1hour", "invalid", None, 123]


@pytest.fixture
def invalid_strategy_types():
    """Invalid strategy type values for testing."""
    return ["RSI", "BOLLINGER", "invalid", None, 123]


@pytest.fixture
def invalid_signal_periods():
    """Invalid signal period values for testing."""
    return [-1, 0, None, "invalid", 3.14]


@pytest.fixture
def parameter_conversion_matrix():
    """Matrix of parameter conversions for comprehensive testing."""
    return [
        # (timeframe, expected_use_hourly, expected_use_4hour, expected_use_2day)
        ("hourly", True, False, False),
        ("4hour", False, True, False),
        ("2day", False, False, True),
        ("daily", False, False, False),
    ]


@pytest.fixture
def strategy_conversion_matrix():
    """Matrix of strategy type conversions."""
    return [
        # (strategy_type, expected_use_sma, expected_strategy_type)
        ("SMA", True, "SMA"),
        ("EMA", False, "EMA"), 
        ("MACD", False, "MACD"),
        ("ATR", False, "ATR"),
    ]


@pytest.fixture
def base_config():
    """Base configuration dictionary for testing."""
    return {
        "TICKER": "TEST-USD",
        "FAST_PERIOD": 10,
        "SLOW_PERIOD": 20,
        "BASE_DIR": "/tmp/trading",
        "YEARS": 2,
        "USE_YEARS": False,
        "PERIOD": "max",
        "USE_SYNTHETIC": False,
        "SHORT": False,
        "USE_GBM": False,
        "WINDOWS": 89,
    }


@pytest.fixture
def legacy_config_with_old_params():
    """Configuration with legacy USE_HOURLY and USE_SMA parameters."""
    return {
        "TICKER": "LEGACY-USD", 
        "FAST_PERIOD": 15,
        "SLOW_PERIOD": 30,
        "USE_HOURLY": True,
        "USE_SMA": False,
        "BASE_DIR": "/tmp/trading",
    }


@pytest.fixture
def modern_config_with_new_params():
    """Configuration with modern TIMEFRAME and STRATEGY_TYPE parameters."""
    return {
        "TICKER": "MODERN-USD",
        "FAST_PERIOD": 12,
        "SLOW_PERIOD": 26,
        "TIMEFRAME": "4hour",
        "STRATEGY_TYPE": "MACD",
        "SIGNAL_PERIOD": 14,
        "BASE_DIR": "/tmp/trading",
    }


@pytest.fixture
def mixed_config():
    """Configuration mixing old and new parameters."""
    return {
        "TICKER": "MIXED-USD",
        "FAST_PERIOD": 8,
        "SLOW_PERIOD": 21,
        "USE_HOURLY": False,  # Legacy param
        "TIMEFRAME": "2day",  # New param
        "USE_SMA": True,      # Legacy param  
        "STRATEGY_TYPE": "EMA", # New param
        "SIGNAL_PERIOD": 9,
        "BASE_DIR": "/tmp/trading",
    }


@pytest.fixture
def parameter_precedence_test_cases():
    """Test cases for parameter precedence (config_dict vs function params)."""
    return [
        {
            "name": "config_dict_overrides_all",
            "config_dict": {
                "TICKER": "TEST1",
                "TIMEFRAME": "hourly",
                "STRATEGY_TYPE": "MACD", 
                "SIGNAL_PERIOD": 21,
            },
            "function_params": {
                "timeframe": "daily",
                "strategy_type": "SMA",
                "signal_period": 9,
            },
            "expected": {
                "timeframe": "hourly",
                "strategy_type": "MACD",
                "signal_period": 21,
            },
        },
        {
            "name": "function_params_fill_gaps",
            "config_dict": {
                "TICKER": "TEST2",
                "TIMEFRAME": "4hour",
                # Missing STRATEGY_TYPE and SIGNAL_PERIOD
            },
            "function_params": {
                "timeframe": "daily", # Should be overridden
                "strategy_type": "EMA", # Should be used
                "signal_period": 14,   # Should be used
            },
            "expected": {
                "timeframe": "4hour",
                "strategy_type": "EMA",
                "signal_period": 14,
            },
        },
        {
            "name": "all_from_function_params",
            "config_dict": {
                "TICKER": "TEST3",
                # No modern parameters
            },
            "function_params": {
                "timeframe": "2day",
                "strategy_type": "ATR",
                "signal_period": 7,
            },
            "expected": {
                "timeframe": "2day",
                "strategy_type": "ATR", 
                "signal_period": 7,
            },
        },
    ]


@pytest.fixture
def complete_conversion_test_cases():
    """Complete test cases for legacy parameter conversion."""
    return [
        {
            "input": {
                "timeframe": "hourly",
                "strategy_type": "SMA",
                "signal_period": 9,
            },
            "expected_legacy": {
                "USE_HOURLY": True,
                "USE_4HOUR": False,
                "USE_2DAY": False,
                "USE_SMA": True,
                "STRATEGY_TYPE": "SMA",
                "SIGNAL_PERIOD": 9,
            },
        },
        {
            "input": {
                "timeframe": "4hour",
                "strategy_type": "MACD",
                "signal_period": 12,
            },
            "expected_legacy": {
                "USE_HOURLY": False,
                "USE_4HOUR": True,
                "USE_2DAY": False,
                "USE_SMA": False,
                "STRATEGY_TYPE": "MACD",
                "SIGNAL_PERIOD": 12,
            },
        },
        {
            "input": {
                "timeframe": "daily",
                "strategy_type": "EMA",
                "signal_period": 21,
            },
            "expected_legacy": {
                "USE_HOURLY": False,
                "USE_4HOUR": False,
                "USE_2DAY": False,
                "USE_SMA": False,
                "STRATEGY_TYPE": "EMA",
                "SIGNAL_PERIOD": 21,
            },
        },
        {
            "input": {
                "timeframe": "2day",
                "strategy_type": "ATR",
                "signal_period": 14,
            },
            "expected_legacy": {
                "USE_HOURLY": False,
                "USE_4HOUR": False,
                "USE_2DAY": True,
                "USE_SMA": False,
                "STRATEGY_TYPE": "ATR",
                "SIGNAL_PERIOD": 14,
            },
        },
    ]


@pytest.fixture
def mock_portfolio_data():
    """Mock portfolio data for JSON file testing."""
    return [
        {
            "ticker": "MOCK1-USD",
            "timeframe": "hourly",
            "fast_period": 5,
            "slow_period": 15,
            "direction": "Long",
            "type": "SMA",
            "signal_period": 9,
        },
        {
            "ticker": "MOCK2-USD", 
            "timeframe": "daily",
            "fast_period": 12,
            "slow_period": 26,
            "direction": "Long",
            "type": "MACD",
            "signal_period": 9,
        },
    ]


@pytest.fixture
def edge_case_configs():
    """Edge case configurations for testing."""
    return [
        {
            "name": "minimal_config",
            "config": {"TICKER": "MIN"},
        },
        {
            "name": "missing_required_fields",
            "config": {"TIMEFRAME": "daily"},  # Missing TICKER
        },
        {
            "name": "zero_signal_period", 
            "config": {
                "TICKER": "ZERO",
                "SIGNAL_PERIOD": 0,
            },
        },
        {
            "name": "negative_signal_period",
            "config": {
                "TICKER": "NEG",
                "SIGNAL_PERIOD": -5,
            },
        },
    ]


@pytest.fixture
def expected_conversion_calls():
    """Expected function calls for mocking validation."""
    return {
        "get_config_called": True,
        "get_data_called": True,
        "calculate_ma_and_signals_called": False,  # Depends on strategy type
        "calculate_macd_and_signals_called": False, # Depends on strategy type
        "backtest_strategy_called": True,
    }