"""Tests for text formatting functions."""

import pytest
from rich.text import Text

from app.tools.formatters.text_formatters import (
    format_average_duration,
    format_duration,
    format_signal_status,
    format_status,
    parse_duration_to_hours,
)


@pytest.mark.unit
class TestFormatDuration:
    """Test suite for format_duration function."""

    def test_days_and_hours(self):
        """Test formatting duration with days and hours."""
        result = format_duration("5 days 08:30:45")
        assert isinstance(result, Text)
        assert "5d 8h" in result.plain
        assert result.style == "blue"

    def test_days_only(self):
        """Test formatting duration with only days."""
        result = format_duration("10 days")
        assert isinstance(result, Text)
        assert "10d" in result.plain
        assert result.style == "blue"

    def test_hours_only(self):
        """Test formatting duration with only hours."""
        result = format_duration("15:30:00")
        assert isinstance(result, Text)
        assert "15h" in result.plain
        assert result.style == "blue"

    def test_none_value(self):
        """Test handling of None value."""
        result = format_duration(None)
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_empty_string(self):
        """Test handling of empty string."""
        result = format_duration("")
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_string_na(self):
        """Test handling of 'n/a' string."""
        result = format_duration("n/a")
        assert isinstance(result, Text)
        assert "N/A" in result.plain
        assert result.style == "dim"

    def test_invalid_format(self):
        """Test handling of invalid format."""
        result = format_duration("invalid format")
        assert isinstance(result, Text)
        # Should truncate to 10 characters
        assert len(result.plain) <= 10
        assert result.style == "dim"


@pytest.mark.unit
class TestParseDurationToHours:
    """Test suite for parse_duration_to_hours function."""

    def test_days_and_hours_format(self):
        """Test parsing duration with days and hours."""
        result = parse_duration_to_hours("5 days 08:30:00")
        # 5 days = 120 hours, + 8 hours + 0.5 hours = 128.5 hours
        assert result == pytest.approx(128.5, rel=0.01)

    def test_days_only(self):
        """Test parsing duration with only days."""
        result = parse_duration_to_hours("3 days")
        # 3 days = 72 hours
        assert result == 72.0

    def test_hours_only(self):
        """Test parsing duration with only hours."""
        result = parse_duration_to_hours("10:45:00")
        # 10 hours + 45/60 hours = 10.75 hours
        assert result == pytest.approx(10.75, rel=0.01)

    def test_none_value(self):
        """Test handling of None value."""
        result = parse_duration_to_hours(None)
        assert result == 0.0

    def test_empty_string(self):
        """Test handling of empty string."""
        result = parse_duration_to_hours("")
        assert result == 0.0

    def test_string_na(self):
        """Test handling of 'n/a' string."""
        result = parse_duration_to_hours("n/a")
        assert result == 0.0

    def test_invalid_format(self):
        """Test handling of invalid format."""
        result = parse_duration_to_hours("invalid")
        assert result == 0.0


@pytest.mark.unit
class TestFormatAverageDuration:
    """Test suite for format_average_duration function."""

    def test_days_and_hours(self):
        """Test formatting average duration with days and hours."""
        # 125 hours = 5 days and 5 hours
        result = format_average_duration(125.0)
        assert result == "5d 5h"

    def test_days_only(self):
        """Test formatting average duration with exact days."""
        # 72 hours = 3 days
        result = format_average_duration(72.0)
        assert result == "3d"

    def test_hours_only(self):
        """Test formatting average duration with only hours."""
        # 15 hours
        result = format_average_duration(15.0)
        assert result == "15h"

    def test_zero_hours(self):
        """Test formatting zero hours."""
        result = format_average_duration(0.0)
        assert result == "0h"

    def test_negative_hours(self):
        """Test formatting negative hours (should return 0h)."""
        result = format_average_duration(-10.0)
        assert result == "0h"

    def test_fractional_hours_rounds_down(self):
        """Test that fractional hours are rounded down."""
        # 25.8 hours = 1 day and 1 hour (fractional part ignored)
        result = format_average_duration(25.8)
        assert result == "1d 1h"


@pytest.mark.unit
class TestFormatStatus:
    """Test suite for format_status function."""

    def test_entry_status(self):
        """Test formatting of Entry status."""
        result = format_status("Entry")
        assert isinstance(result, Text)
        assert "🎯 Entry" in result.plain
        assert result.style == "green"

    def test_active_status(self):
        """Test formatting of Active status."""
        result = format_status("Active")
        assert isinstance(result, Text)
        assert "🔒 Active" in result.plain
        assert result.style == "blue"

    def test_exit_status(self):
        """Test formatting of Exit status."""
        result = format_status("Exit")
        assert isinstance(result, Text)
        assert "🚪 Exit" in result.plain
        assert result.style == "red"

    def test_inactive_status(self):
        """Test formatting of Inactive status."""
        result = format_status("Inactive")
        assert isinstance(result, Text)
        assert "Inactive" in result.plain
        assert result.style == "white"

    def test_unknown_status(self):
        """Test formatting of unknown status (defaults to Inactive)."""
        result = format_status("Unknown")
        assert isinstance(result, Text)
        assert "Inactive" in result.plain
        assert result.style == "white"


@pytest.mark.unit
class TestFormatSignalStatus:
    """Test suite for format_signal_status function."""

    def test_entry_signal(self):
        """Test formatting of entry signal."""
        result = format_signal_status(entry=True, exit=False)
        assert isinstance(result, Text)
        assert "🎯 ENTRY" in result.plain
        assert result.style == "bright_green bold"

    def test_exit_signal(self):
        """Test formatting of exit signal."""
        result = format_signal_status(entry=False, exit=True)
        assert isinstance(result, Text)
        assert "🚪 EXIT" in result.plain
        assert result.style == "red bold"

    def test_pending_signal(self):
        """Test formatting of pending/unconfirmed signal."""
        result = format_signal_status(entry=False, exit=False, unconfirmed="pending")
        assert isinstance(result, Text)
        assert "⏳ PENDING" in result.plain
        assert result.style == "yellow"

    def test_hold_signal(self):
        """Test formatting of hold signal."""
        result = format_signal_status(entry=False, exit=False, unconfirmed=None)
        assert isinstance(result, Text)
        assert "🔒 HOLD" in result.plain
        assert result.style == "blue"

    def test_unconfirmed_none_string(self):
        """Test that 'none' string for unconfirmed is treated as no signal."""
        result = format_signal_status(entry=False, exit=False, unconfirmed="none")
        assert isinstance(result, Text)
        assert "🔒 HOLD" in result.plain
        assert result.style == "blue"

    def test_unconfirmed_na_string(self):
        """Test that 'n/a' string for unconfirmed is treated as no signal."""
        result = format_signal_status(entry=False, exit=False, unconfirmed="n/a")
        assert isinstance(result, Text)
        assert "🔒 HOLD" in result.plain
        assert result.style == "blue"

    def test_entry_takes_precedence(self):
        """Test that entry signal takes precedence over exit."""
        result = format_signal_status(entry=True, exit=True)
        assert isinstance(result, Text)
        assert "🎯 ENTRY" in result.plain
        assert result.style == "bright_green bold"
