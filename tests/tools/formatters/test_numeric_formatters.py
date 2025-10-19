"""Tests for numeric formatting functions."""

from rich.text import Text

from app.tools.formatters.numeric_formatters import (
    format_currency,
    format_percentage,
    format_ratio,
    format_score,
    format_win_rate,
)


class TestFormatPercentage:
    """Test suite for format_percentage function."""

    def test_positive_value_default_positive_good(self):
        """Test that positive values are colored green when positive_good=True."""
        result = format_percentage(25.5)
        assert isinstance(result, Text)
        assert "25.50%" in result.plain
        assert result.style == "green"

    def test_negative_value_default_positive_good(self):
        """Test that negative values are colored red when positive_good=True."""
        result = format_percentage(-15.3)
        assert isinstance(result, Text)
        assert "-15.30%" in result.plain
        assert result.style == "red"

    def test_positive_value_positive_good_false(self):
        """Test that positive values are colored red when positive_good=False."""
        result = format_percentage(10.0, positive_good=False)
        assert isinstance(result, Text)
        assert "10.00%" in result.plain
        assert result.style == "red"

    def test_negative_value_positive_good_false(self):
        """Test that negative values are colored green when positive_good=False."""
        result = format_percentage(-10.0, positive_good=False)
        assert isinstance(result, Text)
        assert "-10.00%" in result.plain
        assert result.style == "green"

    def test_very_small_value(self):
        """Test that very small values are colored yellow."""
        result = format_percentage(0.005)
        assert isinstance(result, Text)
        assert "0.00%" in result.plain or "0.01%" in result.plain
        assert result.style == "yellow"

    def test_none_value(self):
        """Test handling of None value."""
        result = format_percentage(None)
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_empty_string(self):
        """Test handling of empty string."""
        result = format_percentage("")
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_string_none(self):
        """Test handling of string 'none'."""
        result = format_percentage("none")
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_invalid_value(self):
        """Test handling of invalid value."""
        result = format_percentage("invalid")
        assert isinstance(result, Text)
        assert "invalid" in result.plain
        assert result.style == "dim"

    def test_zero_value(self):
        """Test handling of zero value."""
        result = format_percentage(0.0)
        assert isinstance(result, Text)
        assert "0.00%" in result.plain
        assert result.style == "yellow"


class TestFormatCurrency:
    """Test suite for format_currency function."""

    def test_positive_value(self):
        """Test formatting of positive currency value."""
        result = format_currency(1500.50)
        assert isinstance(result, Text)
        assert "$1.5K" in result.plain
        assert result.style == "green"

    def test_negative_value(self):
        """Test formatting of negative currency value."""
        result = format_currency(-2500.75)
        assert isinstance(result, Text)
        # Note: negative sign appears after the dollar sign
        assert "$-2.5K" in result.plain or "$-2.6K" in result.plain
        assert result.style == "red"

    def test_zero_value(self):
        """Test formatting of zero value."""
        result = format_currency(0.0)
        assert isinstance(result, Text)
        assert "$0.00" in result.plain
        assert result.style == "yellow"

    def test_large_value_millions(self):
        """Test formatting of value in millions."""
        result = format_currency(5_500_000)
        assert isinstance(result, Text)
        assert "$5.50M" in result.plain
        assert result.style == "green"

    def test_small_value(self):
        """Test formatting of small value (< 1000)."""
        result = format_currency(123.45)
        assert isinstance(result, Text)
        assert "$123.45" in result.plain
        assert result.style == "green"

    def test_none_value(self):
        """Test handling of None value."""
        result = format_currency(None)
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_invalid_value(self):
        """Test handling of invalid value."""
        result = format_currency("not a number")
        assert isinstance(result, Text)
        assert "not a number" in result.plain
        assert result.style == "dim"


class TestFormatScore:
    """Test suite for format_score function."""

    def test_excellent_score(self):
        """Test formatting of excellent score (>= 1.5)."""
        result = format_score(1.75)
        assert isinstance(result, Text)
        assert "1.7500" in result.plain
        assert "🔥" in result.plain
        assert result.style == "bright_green"

    def test_good_score(self):
        """Test formatting of good score (1.2 - 1.5)."""
        result = format_score(1.35)
        assert isinstance(result, Text)
        assert "1.3500" in result.plain
        assert "📈" in result.plain
        assert result.style == "green"

    def test_neutral_score(self):
        """Test formatting of neutral score (1.0 - 1.2)."""
        result = format_score(1.1)
        assert isinstance(result, Text)
        assert "1.1000" in result.plain
        assert "⚖️" in result.plain
        assert result.style == "yellow"

    def test_warning_score(self):
        """Test formatting of warning score (0.8 - 1.0)."""
        result = format_score(0.9)
        assert isinstance(result, Text)
        assert "0.9000" in result.plain
        assert "⚠️" in result.plain
        assert result.style == "orange"

    def test_poor_score(self):
        """Test formatting of poor score (< 0.8)."""
        result = format_score(0.5)
        assert isinstance(result, Text)
        assert "0.5000" in result.plain
        assert "📉" in result.plain
        assert result.style == "red"

    def test_none_value(self):
        """Test handling of None value."""
        result = format_score(None)
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_invalid_value(self):
        """Test handling of invalid value."""
        result = format_score("invalid")
        assert isinstance(result, Text)
        assert "invalid" in result.plain
        assert result.style == "dim"


class TestFormatWinRate:
    """Test suite for format_win_rate function."""

    def test_high_win_rate(self):
        """Test formatting of high win rate (> 50%)."""
        result = format_win_rate(65.5)
        assert isinstance(result, Text)
        assert "65.5%" in result.plain
        assert result.style == "green"

    def test_medium_win_rate(self):
        """Test formatting of medium win rate (45-50%)."""
        result = format_win_rate(48.0)
        assert isinstance(result, Text)
        assert "48.0%" in result.plain
        assert result.style == "yellow"

    def test_low_win_rate(self):
        """Test formatting of low win rate (< 45%)."""
        result = format_win_rate(35.0)
        assert isinstance(result, Text)
        assert "35.0%" in result.plain
        assert result.style == "red"

    def test_boundary_fifty(self):
        """Test formatting at 50% boundary."""
        result = format_win_rate(50.0)
        assert isinstance(result, Text)
        assert "50.0%" in result.plain
        assert result.style == "yellow"

    def test_boundary_fortyfive(self):
        """Test formatting at 45% boundary."""
        result = format_win_rate(45.0)
        assert isinstance(result, Text)
        assert "45.0%" in result.plain
        assert result.style == "yellow"

    def test_none_value(self):
        """Test handling of None value."""
        result = format_win_rate(None)
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_invalid_value(self):
        """Test handling of invalid value."""
        result = format_win_rate("not a number")
        assert isinstance(result, Text)
        assert "not a number" in result.plain
        assert result.style == "dim"


class TestFormatRatio:
    """Test suite for format_ratio function."""

    def test_good_ratio(self):
        """Test formatting of good ratio (>= 1.34)."""
        result = format_ratio(1.5)
        assert isinstance(result, Text)
        assert "1.50" in result.plain
        assert result.style == "green"

    def test_neutral_ratio(self):
        """Test formatting of neutral ratio (1.0 - 1.34)."""
        result = format_ratio(1.2)
        assert isinstance(result, Text)
        assert "1.20" in result.plain
        assert result.style == "yellow"

    def test_poor_ratio(self):
        """Test formatting of poor ratio (< 1.0)."""
        result = format_ratio(0.8)
        assert isinstance(result, Text)
        assert "0.80" in result.plain
        assert result.style == "red"

    def test_boundary_one_thirtyfour(self):
        """Test formatting at 1.34 boundary."""
        result = format_ratio(1.34)
        assert isinstance(result, Text)
        assert "1.34" in result.plain
        assert result.style == "green"

    def test_boundary_one(self):
        """Test formatting at 1.0 boundary."""
        result = format_ratio(1.0)
        assert isinstance(result, Text)
        assert "1.00" in result.plain
        assert result.style == "yellow"

    def test_none_value(self):
        """Test handling of None value."""
        result = format_ratio(None)
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_invalid_value(self):
        """Test handling of invalid value."""
        result = format_ratio("invalid")
        assert isinstance(result, Text)
        assert "invalid" in result.plain
        assert result.style == "dim"
