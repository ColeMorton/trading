"""
Test fixtures for schema validation and transformation testing.

Provides comprehensive test data for all schema validation scenarios,
including edge cases and real-world examples.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import pytest


class SchemaTestFixtures:
    """Test fixtures for schema testing."""

    @staticmethod
    def get_complete_base_portfolio() -> Dict[str, Any]:
        """Get a complete base portfolio with all 56 columns."""
        return {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Short Window": 20,
            "Long Window": 50,
            "Signal Window": 0,
            "Signal Entry": False,
            "Signal Exit": False,
            "Total Open Trades": 0,
            "Total Trades": 100,
            "Score": 1.5,
            "Win Rate [%]": 65.0,
            "Profit Factor": 1.8,
            "Expectancy per Trade": 0.05,
            "Sortino Ratio": 1.2,
            "Beats BNH [%]": 15.0,
            "Avg Trade Duration": "5 days 00:00:00",
            "Trades Per Day": 0.2,
            "Trades per Month": 6.0,
            "Signals per Month": 12.0,
            "Expectancy per Month": 0.3,
            "Start": "2023-01-01 00:00:00",
            "End": "2023-12-31 00:00:00",
            "Period": "365 days 00:00:00",
            "Start Value": 10000.0,
            "End Value": 11500.0,
            "Total Return [%]": 15.0,
            "Benchmark Return [%]": 10.0,
            "Max Gross Exposure [%]": 100.0,
            "Total Fees Paid": 150.0,
            "Max Drawdown [%]": 8.0,
            "Max Drawdown Duration": "30 days 00:00:00",
            "Total Closed Trades": 100,
            "Open Trade PnL": 0.0,
            "Best Trade [%]": 12.0,
            "Worst Trade [%]": -5.0,
            "Avg Winning Trade [%]": 4.0,
            "Avg Losing Trade [%]": -2.0,
            "Avg Winning Trade Duration": "4 days 00:00:00",
            "Avg Losing Trade Duration": "2 days 00:00:00",
            "Expectancy": 0.05,
            "Sharpe Ratio": 1.1,
            "Calmar Ratio": 1.9,
            "Omega Ratio": 1.3,
            "Skew": 0.2,
            "Kurtosis": 3.1,
            "Tail Ratio": 1.1,
            "Common Sense Ratio": 1.2,
            "Value at Risk": 2.5,
            "Daily Returns": 0.041,
            "Annual Returns": 0.15,
            "Cumulative Returns": 0.15,
            "Annualized Return": 0.15,
            "Annualized Volatility": 0.18,
            "Signal Count": 200,
            "Position Count": 100,
            "Total Period": 365.0,
        }

    @staticmethod
    def get_complete_extended_portfolio() -> Dict[str, Any]:
        """Get a complete extended portfolio with all 58 columns."""
        base_portfolio = SchemaTestFixtures.get_complete_base_portfolio()
        base_portfolio.update({"Allocation [%]": 25.0, "Stop Loss [%]": 5.0})
        return base_portfolio

    @staticmethod
    def get_complete_filtered_portfolio() -> Dict[str, Any]:
        """Get a complete filtered portfolio with all 59 columns."""
        extended_portfolio = SchemaTestFixtures.get_complete_extended_portfolio()
        # Insert Metric Type at the beginning
        filtered_portfolio = {"Metric Type": "Most Total Return [%]"}
        filtered_portfolio.update(extended_portfolio)
        return filtered_portfolio

    @staticmethod
    def get_minimal_portfolio() -> Dict[str, Any]:
        """Get a minimal portfolio with only essential columns."""
        return {
            "Ticker": "AAPL",
            "Strategy Type": "SMA",
            "Short Window": 20,
            "Long Window": 50,
            "Total Trades": 100,
            "Score": 1.5,
            "Win Rate [%]": 65.0,
            "Total Return [%]": 15.0,
        }

    @staticmethod
    def get_crypto_portfolio() -> Dict[str, Any]:
        """Get a crypto portfolio example."""
        portfolio = SchemaTestFixtures.get_complete_base_portfolio()
        portfolio.update(
            {
                "Ticker": "BTC-USD",
                "Strategy Type": "EMA",
                "Short Window": 12,
                "Long Window": 26,
                "Total Trades": 250,
                "Score": 2.1,
                "Win Rate [%]": 58.0,
                "Total Return [%]": 85.0,
                "Benchmark Return [%]": 120.0,
                "Beats BNH [%]": -29.17,  # Negative beats BnH
                "Max Drawdown [%]": 25.0,
                "Sharpe Ratio": 0.8,
                "Sortino Ratio": 1.1,
                "Annualized Volatility": 0.65,  # High volatility for crypto
            }
        )
        return portfolio

    @staticmethod
    def get_portfolio_with_missing_columns() -> Dict[str, Any]:
        """Get a portfolio with some missing columns."""
        return {
            "Ticker": "GOOGL",
            "Strategy Type": "EMA",
            "Short Window": 15,
            "Long Window": 35,
            "Total Trades": 85,
            "Score": 1.8,
            "Win Rate [%]": 72.0,
            "Total Return [%]": 28.0,
            # Missing many standard columns
        }

    @staticmethod
    def get_portfolio_with_none_values() -> Dict[str, Any]:
        """Get a portfolio with None values for testing."""
        portfolio = SchemaTestFixtures.get_complete_base_portfolio()
        portfolio.update(
            {
                "Score": None,
                "Win Rate [%]": None,
                "Sharpe Ratio": None,
                "Sortino Ratio": None,
                "Expectancy per Trade": None,
            }
        )
        return portfolio

    @staticmethod
    def get_portfolio_with_invalid_types() -> Dict[str, Any]:
        """Get a portfolio with invalid data types."""
        portfolio = SchemaTestFixtures.get_complete_base_portfolio()
        portfolio.update(
            {
                "Total Trades": "invalid_string",  # Should be numeric
                "Win Rate [%]": "65%",  # Should be numeric
                "Signal Entry": "yes",  # Should be boolean
                "Start Value": "10k",  # Should be numeric
            }
        )
        return portfolio

    @staticmethod
    def get_portfolio_with_extra_columns() -> Dict[str, Any]:
        """Get a portfolio with extra unexpected columns."""
        portfolio = SchemaTestFixtures.get_complete_base_portfolio()
        portfolio.update(
            {
                "Custom Metric 1": 100.0,
                "Debug Info": "test_data",
                "Internal ID": "portfolio_123",
                "Extra Field": None,
            }
        )
        return portfolio

    @staticmethod
    def get_multiple_portfolios() -> List[Dict[str, Any]]:
        """Get multiple portfolios for batch testing."""
        return [
            SchemaTestFixtures.get_complete_base_portfolio(),
            SchemaTestFixtures.get_crypto_portfolio(),
            SchemaTestFixtures.get_portfolio_with_missing_columns(),
            SchemaTestFixtures.get_minimal_portfolio(),
        ]

    @staticmethod
    def get_edge_case_portfolios() -> List[Dict[str, Any]]:
        """Get edge case portfolios for comprehensive testing."""
        return [
            {},  # Empty portfolio
            {"Ticker": "ONLY_TICKER"},  # Single column
            SchemaTestFixtures.get_portfolio_with_none_values(),
            SchemaTestFixtures.get_portfolio_with_invalid_types(),
            SchemaTestFixtures.get_portfolio_with_extra_columns(),
        ]

    @staticmethod
    def get_performance_test_data(count: int = 1000) -> List[Dict[str, Any]]:
        """Get large dataset for performance testing."""
        base_portfolio = SchemaTestFixtures.get_complete_base_portfolio()
        portfolios = []

        for i in range(count):
            portfolio = base_portfolio.copy()
            portfolio.update(
                {
                    "Ticker": f"STOCK_{i:04d}",
                    "Score": 1.0 + (i % 100) / 100.0,
                    "Win Rate [%]": 50.0 + (i % 50),
                    "Total Return [%]": (i % 200) - 100,  # Range -100 to 99
                    "Total Trades": 50 + (i % 200),
                }
            )
            portfolios.append(portfolio)

        return portfolios

    @staticmethod
    def get_real_world_examples() -> Dict[str, Dict[str, Any]]:
        """Get real-world portfolio examples from different strategies."""
        return {
            "ma_cross_aapl": {
                "Ticker": "AAPL",
                "Strategy Type": "SMA",
                "Short Window": 20,
                "Long Window": 50,
                "Signal Window": 0,
                "Signal Entry": True,
                "Signal Exit": False,
                "Total Open Trades": 1,
                "Total Trades": 156,
                "Score": 1.82,
                "Win Rate [%]": 62.18,
                "Profit Factor": 1.45,
                "Expectancy per Trade": 0.0234,
                "Sortino Ratio": 1.28,
                "Beats BNH [%]": 8.43,
                "Avg Trade Duration": "12 days 06:30:00",
                "Trades Per Day": 0.085,
                "Trades per Month": 2.6,
                "Signals per Month": 5.2,
                "Expectancy per Month": 0.0608,
                "Start": "2020-01-01 00:00:00",
                "End": "2023-12-31 00:00:00",
                "Period": "1460 days 00:00:00",
                "Start Value": 10000.0,
                "End Value": 14250.0,
                "Total Return [%]": 42.50,
                "Benchmark Return [%]": 39.20,
                "Max Gross Exposure [%]": 100.0,
                "Total Fees Paid": 312.0,
                "Max Drawdown [%]": 18.5,
                "Max Drawdown Duration": "89 days 00:00:00",
                "Total Closed Trades": 155,
                "Open Trade PnL": 156.8,
                "Best Trade [%]": 8.9,
                "Worst Trade [%]": -6.2,
                "Avg Winning Trade [%]": 3.1,
                "Avg Losing Trade [%]": -2.4,
                "Avg Winning Trade Duration": "15 days 12:00:00",
                "Avg Losing Trade Duration": "8 days 18:00:00",
                "Expectancy": 0.0234,
                "Sharpe Ratio": 0.89,
                "Calmar Ratio": 2.3,
                "Omega Ratio": 1.15,
                "Skew": 0.34,
                "Kurtosis": 2.89,
                "Tail Ratio": 1.08,
                "Common Sense Ratio": 1.12,
                "Value at Risk": 3.2,
                "Daily Returns": 0.000291,
                "Annual Returns": 0.106,
                "Cumulative Returns": 0.425,
                "Annualized Return": 0.106,
                "Annualized Volatility": 0.245,
                "Signal Count": 312,
                "Position Count": 156,
                "Total Period": 1460.0,
            },
            "macd_btc": {
                "Ticker": "BTC-USD",
                "Strategy Type": "MACD",
                "Short Window": 12,
                "Long Window": 26,
                "Signal Window": 9,
                "Signal Entry": False,
                "Signal Exit": True,
                "Total Open Trades": 0,
                "Total Trades": 89,
                "Score": 2.15,
                "Win Rate [%]": 55.06,
                "Profit Factor": 2.18,
                "Expectancy per Trade": 0.0445,
                "Sortino Ratio": 1.65,
                "Beats BNH [%]": -15.2,
                "Avg Trade Duration": "8 days 14:30:00",
                "Trades Per Day": 0.244,
                "Trades per Month": 7.4,
                "Signals per Month": 14.8,
                "Expectancy per Month": 0.329,
                "Start": "2023-01-01 00:00:00",
                "End": "2023-12-31 00:00:00",
                "Period": "365 days 00:00:00",
                "Start Value": 10000.0,
                "End Value": 13960.0,
                "Total Return [%]": 39.6,
                "Benchmark Return [%]": 156.8,
                "Max Gross Exposure [%]": 100.0,
                "Total Fees Paid": 178.0,
                "Max Drawdown [%]": 28.4,
                "Max Drawdown Duration": "45 days 00:00:00",
                "Total Closed Trades": 89,
                "Open Trade PnL": 0.0,
                "Best Trade [%]": 15.2,
                "Worst Trade [%]": -12.8,
                "Avg Winning Trade [%]": 5.8,
                "Avg Losing Trade [%]": -4.1,
                "Avg Winning Trade Duration": "11 days 08:00:00",
                "Avg Losing Trade Duration": "5 days 16:00:00",
                "Expectancy": 0.0445,
                "Sharpe Ratio": 0.72,
                "Calmar Ratio": 1.39,
                "Omega Ratio": 1.28,
                "Skew": -0.12,
                "Kurtosis": 3.45,
                "Tail Ratio": 0.95,
                "Common Sense Ratio": 0.98,
                "Value at Risk": 8.9,
                "Daily Returns": 0.00109,
                "Annual Returns": 0.396,
                "Cumulative Returns": 0.396,
                "Annualized Return": 0.396,
                "Annualized Volatility": 0.685,
                "Signal Count": 178,
                "Position Count": 89,
                "Total Period": 365.0,
            },
        }

    @staticmethod
    def get_metric_type_variations() -> List[str]:
        """Get various metric type examples for filtered portfolios."""
        return [
            "Most Total Return [%]",
            "Least Total Return [%]",
            "Mean Total Return [%]",
            "Median Total Return [%]",
            "Most Score",
            "Least Score",
            "Mean Score",
            "Median Score",
            "Most Win Rate [%]",
            "Least Win Rate [%]",
            "Most Profit Factor",
            "Least Profit Factor",
            "Most Sharpe Ratio",
            "Least Sharpe Ratio",
            "Most Sortino Ratio",
            "Least Sortino Ratio",
        ]

    @staticmethod
    def get_allocation_variations() -> List[float]:
        """Get various allocation percentage examples."""
        return [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 33.33, 50.0, 100.0]

    @staticmethod
    def get_stop_loss_variations() -> List[float]:
        """Get various stop loss percentage examples."""
        return [1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0]


@pytest.fixture
def base_portfolio():
    """Fixture for complete base portfolio."""
    return SchemaTestFixtures.get_complete_base_portfolio()


@pytest.fixture
def extended_portfolio():
    """Fixture for complete extended portfolio."""
    return SchemaTestFixtures.get_complete_extended_portfolio()


@pytest.fixture
def filtered_portfolio():
    """Fixture for complete filtered portfolio."""
    return SchemaTestFixtures.get_complete_filtered_portfolio()


@pytest.fixture
def minimal_portfolio():
    """Fixture for minimal portfolio."""
    return SchemaTestFixtures.get_minimal_portfolio()


@pytest.fixture
def crypto_portfolio():
    """Fixture for crypto portfolio."""
    return SchemaTestFixtures.get_crypto_portfolio()


@pytest.fixture
def portfolios_with_missing_columns():
    """Fixture for portfolios with missing columns."""
    return SchemaTestFixtures.get_portfolio_with_missing_columns()


@pytest.fixture
def portfolios_with_none_values():
    """Fixture for portfolios with None values."""
    return SchemaTestFixtures.get_portfolio_with_none_values()


@pytest.fixture
def portfolios_with_extra_columns():
    """Fixture for portfolios with extra columns."""
    return SchemaTestFixtures.get_portfolio_with_extra_columns()


@pytest.fixture
def multiple_portfolios():
    """Fixture for multiple portfolios."""
    return SchemaTestFixtures.get_multiple_portfolios()


@pytest.fixture
def edge_case_portfolios():
    """Fixture for edge case portfolios."""
    return SchemaTestFixtures.get_edge_case_portfolios()


@pytest.fixture
def real_world_examples():
    """Fixture for real-world portfolio examples."""
    return SchemaTestFixtures.get_real_world_examples()


@pytest.fixture(params=SchemaTestFixtures.get_metric_type_variations())
def metric_type_variation(request):
    """Parametrized fixture for metric type variations."""
    return request.param


@pytest.fixture(params=SchemaTestFixtures.get_allocation_variations())
def allocation_variation(request):
    """Parametrized fixture for allocation variations."""
    return request.param


@pytest.fixture(params=SchemaTestFixtures.get_stop_loss_variations())
def stop_loss_variation(request):
    """Parametrized fixture for stop loss variations."""
    return request.param
