"""Tests for portfolio status filtering functions."""

import pytest

from app.tools.portfolio.status_filters import (
    determine_portfolio_status,
    filter_entry_strategies,
)


@pytest.mark.unit
class TestDeterminePortfolioStatus:
    """Test suite for determine_portfolio_status function."""

    def test_entry_signal_takes_precedence(self):
        """Test that entry signal takes precedence over other statuses."""
        portfolio = {
            "Signal Entry": "true",
            "Signal Exit": "false",
            "Total Open Trades": 0,
        }
        assert determine_portfolio_status(portfolio) == "Entry"

    def test_entry_signal_with_open_trade(self):
        """Test entry signal even with open trade."""
        portfolio = {
            "Signal Entry": "true",
            "Signal Exit": "false",
            "Total Open Trades": 1,
        }
        assert determine_portfolio_status(portfolio) == "Entry"

    def test_exit_signal(self):
        """Test exit signal status."""
        portfolio = {
            "Signal Entry": "false",
            "Signal Exit": "true",
            "Total Open Trades": 1,
        }
        assert determine_portfolio_status(portfolio) == "Exit"

    def test_active_status_with_open_trade(self):
        """Test active status when there's an open trade."""
        portfolio = {
            "Signal Entry": "false",
            "Signal Exit": "false",
            "Total Open Trades": 1,
        }
        assert determine_portfolio_status(portfolio) == "Active"

    def test_active_status_with_string_open_trade(self):
        """Test active status when open trade is a string."""
        portfolio = {
            "Signal Entry": "false",
            "Signal Exit": "false",
            "Total Open Trades": "1",
        }
        assert determine_portfolio_status(portfolio) == "Active"

    def test_inactive_status_no_trades(self):
        """Test inactive status when there are no open trades."""
        portfolio = {
            "Signal Entry": "false",
            "Signal Exit": "false",
            "Total Open Trades": 0,
        }
        assert determine_portfolio_status(portfolio) == "Inactive"

    def test_inactive_status_missing_signals(self):
        """Test inactive status with missing signal fields."""
        portfolio = {
            "Total Open Trades": 0,
        }
        assert determine_portfolio_status(portfolio) == "Inactive"

    def test_entry_signal_case_insensitive(self):
        """Test that signal detection is case insensitive."""
        portfolio = {
            "Signal Entry": "True",
            "Signal Exit": "False",
            "Total Open Trades": 0,
        }
        assert determine_portfolio_status(portfolio) == "Entry"

        portfolio["Signal Entry"] = "TRUE"
        assert determine_portfolio_status(portfolio) == "Entry"

    def test_exit_signal_case_insensitive(self):
        """Test that exit signal is case insensitive."""
        portfolio = {
            "Signal Entry": "false",
            "Signal Exit": "True",
            "Total Open Trades": 1,
        }
        assert determine_portfolio_status(portfolio) == "Exit"

        portfolio["Signal Exit"] = "TRUE"
        assert determine_portfolio_status(portfolio) == "Exit"

    def test_inactive_with_multiple_trades(self):
        """Test inactive status with multiple closed trades."""
        portfolio = {
            "Signal Entry": "false",
            "Signal Exit": "false",
            "Total Open Trades": 0,
            "Total Trades": 50,  # Has trade history
        }
        assert determine_portfolio_status(portfolio) == "Inactive"

    def test_entry_priority_over_exit(self):
        """Test that entry takes priority when both signals are true."""
        portfolio = {
            "Signal Entry": "true",
            "Signal Exit": "true",
            "Total Open Trades": 1,
        }
        # Entry should take precedence
        assert determine_portfolio_status(portfolio) == "Entry"


@pytest.mark.unit
class TestFilterEntryStrategies:
    """Test suite for filter_entry_strategies function."""

    def test_filter_only_entry_strategies(self):
        """Test filtering only entry status strategies."""
        portfolios = [
            {
                "Ticker": "AAPL",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
            {
                "Ticker": "MSFT",
                "Signal Entry": "false",
                "Signal Exit": "false",
                "Total Open Trades": 1,
            },
            {
                "Ticker": "TSLA",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
            {
                "Ticker": "NVDA",
                "Signal Entry": "false",
                "Signal Exit": "true",
                "Total Open Trades": 1,
            },
        ]

        result = filter_entry_strategies(portfolios)

        assert len(result) == 2
        assert result[0]["Ticker"] == "AAPL"
        assert result[1]["Ticker"] == "TSLA"

    def test_filter_empty_list(self):
        """Test filtering an empty list."""
        result = filter_entry_strategies([])
        assert result == []

    def test_filter_no_entry_strategies(self):
        """Test filtering when there are no entry strategies."""
        portfolios = [
            {
                "Ticker": "AAPL",
                "Signal Entry": "false",
                "Signal Exit": "false",
                "Total Open Trades": 1,
            },
            {
                "Ticker": "MSFT",
                "Signal Entry": "false",
                "Signal Exit": "true",
                "Total Open Trades": 1,
            },
        ]

        result = filter_entry_strategies(portfolios)
        assert result == []

    def test_filter_all_entry_strategies(self):
        """Test filtering when all strategies are entry status."""
        portfolios = [
            {
                "Ticker": "BTC-USD",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
            {
                "Ticker": "ETH-USD",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
        ]

        result = filter_entry_strategies(portfolios)
        assert len(result) == 2
        assert result[0]["Ticker"] == "BTC-USD"
        assert result[1]["Ticker"] == "ETH-USD"

    def test_filter_preserves_portfolio_data(self):
        """Test that filtering preserves all portfolio data."""
        portfolios = [
            {
                "Ticker": "AAPL",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
                "Score": 1.5,
                "Win Rate [%]": 65.0,
                "Total Return [%]": 123.45,
            },
        ]

        result = filter_entry_strategies(portfolios)

        assert len(result) == 1
        assert result[0]["Ticker"] == "AAPL"
        assert result[0]["Score"] == 1.5
        assert result[0]["Win Rate [%]"] == 65.0
        assert result[0]["Total Return [%]"] == 123.45

    def test_filter_maintains_order(self):
        """Test that filtering maintains the original order."""
        portfolios = [
            {
                "Ticker": "A",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
            {
                "Ticker": "B",
                "Signal Entry": "false",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
            {
                "Ticker": "C",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
            {
                "Ticker": "D",
                "Signal Entry": "true",
                "Signal Exit": "false",
                "Total Open Trades": 0,
            },
        ]

        result = filter_entry_strategies(portfolios)

        assert len(result) == 3
        assert result[0]["Ticker"] == "A"
        assert result[1]["Ticker"] == "C"
        assert result[2]["Ticker"] == "D"
