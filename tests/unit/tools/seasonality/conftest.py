"""Shared fixtures for seasonality unit tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def high_skew_data():
    """Generate data with high positive skewness (outliers on right tail).

    Tests skewness calculation - should detect right-skewed distribution.
    """
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=1260, freq="B")

    # Most returns normal, but occasional large positive spike
    returns = []
    for i in range(1260):
        if i % 100 == 0:  # Every 100 days, big spike
            returns.append(0.05)  # +5% spike
        else:
            returns.append(np.random.normal(0.0005, 0.01))

    prices = [100.0]
    for r in returns:
        prices.append(prices[-1] * (1 + r))

    return pd.DataFrame({"Date": dates, "Close": prices[:-1]}).set_index("Date")


@pytest.fixture
def all_positive_returns_data():
    """Generate data where every return is positive.

    Tests edge cases:
    - No downside deviation (Sortino ratio special case)
    - Max drawdown should be 0 or very small
    - Win rate should be 100%
    """
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=1260, freq="B")

    # All positive returns
    returns = np.random.uniform(0.001, 0.03, size=1260)

    prices = [100.0]
    for r in returns:
        prices.append(prices[-1] * (1 + r))

    return pd.DataFrame({"Date": dates, "Close": prices[:-1]}).set_index("Date")


@pytest.fixture
def all_negative_returns_data():
    """Generate data where every return is negative.

    Tests edge cases:
    - Negative Sharpe and Sortino ratios
    - Large max drawdown
    - Win rate should be 0%
    """
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", periods=1260, freq="B")

    # All negative returns
    returns = np.random.uniform(-0.03, -0.001, size=1260)

    prices = [100.0]
    for r in returns:
        prices.append(prices[-1] * (1 + r))

    return pd.DataFrame({"Date": dates, "Close": prices[:-1]}).set_index("Date")


@pytest.fixture
def flat_returns_data():
    """Generate data with zero volatility - all same return.

    Tests edge cases:
    - Zero std deviation (Sharpe ratio should handle)
    - Skewness and kurtosis edge cases
    """
    dates = pd.date_range("2020-01-01", periods=1260, freq="B")

    # Constant return
    constant_return = 0.001
    prices = [100.0]
    for _ in range(1259):
        prices.append(prices[-1] * (1 + constant_return))

    return pd.DataFrame({"Date": dates, "Close": prices}).set_index("Date")
