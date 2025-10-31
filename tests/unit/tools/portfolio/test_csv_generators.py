"""Tests for CSV generation functions."""

import pytest

from app.tools.portfolio.csv_generators import generate_csv_output_for_portfolios


@pytest.mark.unit
class TestGenerateCsvOutputForPortfolios:
    """Test suite for generate_csv_output_for_portfolios function."""

    def test_generate_csv_with_portfolios(self):
        """Test generating CSV output from portfolio data."""
        portfolios = [
            {
                "Ticker": "AAPL",
                "Strategy": "SMA",
                "Score": 1.5,
                "Win Rate [%]": 65.0,
            },
            {
                "Ticker": "MSFT",
                "Strategy": "EMA",
                "Score": 1.3,
                "Win Rate [%]": 60.0,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        # Verify it's a CSV string
        assert isinstance(result, str)
        assert "Ticker" in result
        assert "Strategy" in result
        assert "Score" in result
        assert "Win Rate [%]" in result
        assert "AAPL" in result
        assert "MSFT" in result
        assert "SMA" in result
        assert "EMA" in result

    def test_generate_csv_empty_list(self):
        """Test generating CSV with empty portfolio list."""
        result = generate_csv_output_for_portfolios([])
        assert result == "No Entry strategies found"

    def test_generate_csv_single_portfolio(self):
        """Test generating CSV with single portfolio."""
        portfolios = [
            {
                "Ticker": "BTC-USD",
                "Strategy": "MACD",
                "Score": 2.0,
                "Return": 150.5,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        assert isinstance(result, str)
        assert "Ticker" in result
        assert "BTC-USD" in result
        assert "MACD" in result
        assert "2.0" in result

    def test_generate_csv_preserves_column_order(self):
        """Test that CSV generation preserves data structure."""
        portfolios = [
            {
                "Ticker": "TSLA",
                "Fast Period": 20,
                "Slow Period": 50,
                "Score": 1.2,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        lines = result.strip().split("\n")
        assert len(lines) == 2  # Header + 1 data row
        assert "Ticker" in lines[0]
        assert "TSLA" in lines[1]

    def test_generate_csv_with_special_characters(self):
        """Test CSV generation with special characters in data."""
        portfolios = [
            {
                "Ticker": "BTC-USD",
                "Note": "High volatility, use caution",
                "Score": 1.5,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        assert isinstance(result, str)
        assert "BTC-USD" in result
        assert "Score" in result

    def test_generate_csv_with_numeric_values(self):
        """Test CSV generation with various numeric types."""
        portfolios = [
            {
                "Ticker": "SPY",
                "Score": 1.234567,
                "Win Rate": 65,
                "Return": 123.45,
                "Trades": 100,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        assert "SPY" in result
        assert "1.234567" in result
        assert "65" in result
        assert "123.45" in result
        assert "100" in result

    def test_generate_csv_with_null_values(self):
        """Test CSV generation with None/null values."""
        portfolios = [
            {
                "Ticker": "NVDA",
                "Score": 1.5,
                "Stop Loss": None,
                "RSI Window": None,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        assert isinstance(result, str)
        assert "NVDA" in result
        assert "Score" in result

    def test_generate_csv_multiple_portfolios_maintains_structure(self):
        """Test that multiple portfolios maintain consistent structure."""
        portfolios = [
            {
                "Ticker": "AAPL",
                "Score": 1.5,
                "Win Rate": 65.0,
            },
            {
                "Ticker": "GOOGL",
                "Score": 1.3,
                "Win Rate": 58.0,
            },
            {
                "Ticker": "AMZN",
                "Score": 1.7,
                "Win Rate": 72.0,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        lines = result.strip().split("\n")
        assert len(lines) == 4  # Header + 3 data rows
        assert "Ticker" in lines[0]
        assert "Score" in lines[0]
        assert "Win Rate" in lines[0]

    def test_generate_csv_no_newlines_at_end(self):
        """Test that CSV output is stripped of trailing newlines."""
        portfolios = [
            {
                "Ticker": "TEST",
                "Value": 123,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        # Should not end with newline
        assert not result.endswith("\n")
        assert not result.endswith("\r\n")

    def test_generate_csv_with_boolean_values(self):
        """Test CSV generation with boolean values."""
        portfolios = [
            {
                "Ticker": "FB",
                "Active": True,
                "Use Hourly": False,
                "Score": 1.2,
            },
        ]

        result = generate_csv_output_for_portfolios(portfolios)

        assert "FB" in result
        assert "True" in result or "true" in result.lower()
        assert "False" in result or "false" in result.lower()
