"""Shared fixtures for seasonality tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def standard_5yr_data():
    """Generate 5 years of price data with clear monthly seasonality pattern.

    Pattern: Q1 months (Jan-Mar) have higher returns than other months.
    This allows testing that monthly pattern detection works correctly.
    """
    np.random.seed(42)  # For reproducibility

    # 5 years of business days (approx 1,260 trading days)
    dates = pd.date_range("2020-01-01", periods=1260, freq="B")

    # Generate returns with monthly pattern
    returns = []
    for date in dates:
        base_return = 0.001  # 0.1% daily base return

        # Add monthly effect: Q1 months get boost, others get penalty
        if date.month <= 3:
            monthly_effect = 0.002  # +0.2% for Q1 months
        else:
            monthly_effect = -0.001  # -0.1% for other months

        # Add random noise
        noise = np.random.normal(0, 0.02)  # 2% daily volatility

        returns.append(base_return + monthly_effect + noise)

    # Convert returns to prices
    prices = [100.0]
    for r in returns:
        prices.append(prices[-1] * (1 + r))

    return pd.DataFrame(
        {"Date": dates, "Close": prices[:-1]},  # Remove last price (one extra from loop)
    ).set_index("Date")


@pytest.fixture
def short_1yr_data():
    """Generate 1 year of price data - insufficient for 3-year minimum.

    Used to test the insufficient data path and auto-download triggering.
    """
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=252, freq="B")

    # Simple random walk
    prices = [100.0]
    for _ in range(251):
        change = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + change))

    return pd.DataFrame({"Date": dates, "Close": prices}).set_index("Date")


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
def few_samples_data():
    """Generate minimal data for edge case testing.

    Less than 10 samples in some months - tests min_sample_size filtering.
    """
    # Just 2 months of data
    dates = pd.date_range("2024-01-01", periods=40, freq="B")

    prices = [100.0]
    for _ in range(39):
        change = np.random.normal(0.001, 0.02)
        prices.append(prices[-1] * (1 + change))

    return pd.DataFrame({"Date": dates, "Close": prices}).set_index("Date")


@pytest.fixture
def mock_yfinance_success_data():
    """Mock yfinance download data with MultiIndex columns.

    Simulates the actual structure returned by yf.download() for a single ticker,
    which can have MultiIndex columns that need flattening.
    """
    dates = pd.date_range("2020-01-01", periods=1260, freq="D")

    # Create DataFrame with regular columns
    data = pd.DataFrame(
        {
            "Open": np.random.uniform(90, 110, 1260),
            "High": np.random.uniform(95, 115, 1260),
            "Low": np.random.uniform(85, 105, 1260),
            "Close": np.random.uniform(90, 110, 1260),
            "Volume": np.random.randint(1000000, 10000000, 1260),
        },
        index=dates,
    )

    data.index.name = "Date"

    return data


@pytest.fixture
def mock_yfinance_multiindex_data():
    """Mock yfinance data with MultiIndex columns (ticker-specific).

    This simulates the problematic case where yfinance returns
    MultiIndex columns like ('Close', 'HIMS') instead of just 'Close'.
    """
    dates = pd.date_range("2020-01-01", periods=1260, freq="D")

    # Create MultiIndex columns
    pd.MultiIndex.from_tuples(
        [
            ("Open", "TEST"),
            ("High", "TEST"),
            ("Low", "TEST"),
            ("Close", "TEST"),
            ("Volume", "TEST"),
        ],
    )

    data = pd.DataFrame(
        {
            ("Open", "TEST"): np.random.uniform(90, 110, 1260),
            ("High", "TEST"): np.random.uniform(95, 115, 1260),
            ("Low", "TEST"): np.random.uniform(85, 105, 1260),
            ("Close", "TEST"): np.random.uniform(90, 110, 1260),
            ("Volume", "TEST"): np.random.randint(1000000, 10000000, 1260),
        },
        index=dates,
    )

    data.index.name = "Date"

    return data
