"""
Tests for console display.

Smoke tests to verify display methods don't crash.
"""

import pytest
from rich.table import Table

from app.ui.console_display import ConsoleDisplay


@pytest.mark.unit
def test_console_display_creation():
    """Test console display instantiation."""
    console = ConsoleDisplay()
    assert console is not None


@pytest.mark.unit
def test_console_display_quiet():
    """Test console display in quiet mode."""
    console = ConsoleDisplay(quiet=True)
    assert console.quiet is True


@pytest.mark.unit
def test_console_display_verbose():
    """Test console display in verbose mode."""
    console = ConsoleDisplay(verbose=True)
    assert console.verbose is True


@pytest.mark.unit
def test_show_success():
    """Test success message display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_success("Operation completed")


@pytest.mark.unit
def test_show_error():
    """Test error message display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_error("Operation failed")


@pytest.mark.unit
def test_show_warning():
    """Test warning message display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_warning("Warning message")


@pytest.mark.unit
def test_show_info():
    """Test info message display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_info("Info message")


@pytest.mark.unit
def test_show_debug():
    """Test debug message display."""
    console = ConsoleDisplay(verbose=True)
    # Should not raise
    console.show_debug("Debug message")


@pytest.mark.unit
def test_show_progress():
    """Test progress message display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_progress("Processing...")


@pytest.mark.unit
def test_show_heading():
    """Test heading display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_heading("Test Heading", level=1)
    console.show_heading("Test Heading", level=2)
    console.show_heading("Test Heading", level=3)


@pytest.mark.unit
def test_show_section():
    """Test section display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_section("Test Section", "Section content")


@pytest.mark.unit
def test_show_table():
    """Test table display."""
    console = ConsoleDisplay()
    table = Table(title="Test Table")
    table.add_column("Column 1")
    table.add_column("Column 2")
    table.add_row("Value 1", "Value 2")

    # Should not raise
    console.show_table(table)


@pytest.mark.unit
def test_show_panel():
    """Test panel display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_panel("Panel content", title="Test Panel")


@pytest.mark.unit
def test_show_rule():
    """Test rule display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_rule("Section Break")


@pytest.mark.unit
def test_show_completion_banner():
    """Test completion banner display."""
    console = ConsoleDisplay()
    # Should not raise
    console.show_completion_banner("Test Complete")


@pytest.mark.unit
def test_data_summary_table():
    """Test data summary table display."""
    console = ConsoleDisplay()
    data_info = {
        "date_range": "2020-01-01 to 2021-01-01",
        "price_range": "$100 - $200",
        "avg_volume": 1000000,
        "frequency": "Daily",
        "records_count": 365,
    }

    # Should not raise
    console.data_summary_table("AAPL", data_info)


@pytest.mark.unit
def test_strategy_header():
    """Test strategy header display."""
    console = ConsoleDisplay()
    # Should not raise
    console.strategy_header("AAPL", ["SMA", "EMA"], "default_profile")


@pytest.mark.unit
def test_results_summary_table():
    """Test results summary table display."""
    console = ConsoleDisplay()
    # Should not raise
    console.results_summary_table(
        portfolios_generated=50,
        best_config="SMA_20_50",
        files_exported=3,
    )


@pytest.mark.unit
def test_quiet_mode_suppresses_output():
    """Test that quiet mode suppresses non-essential output."""
    console = ConsoleDisplay(quiet=True)

    # These should not raise, but also should not display
    console.show_info("Should not display")
    console.show_warning("Should not display")
    console.show_progress("Should not display")

    # These should always display even in quiet mode
    console.show_success("Should display")
    console.show_error("Should display")


@pytest.mark.unit
def test_verbose_mode_shows_debug():
    """Test that verbose mode shows debug messages."""
    console = ConsoleDisplay(verbose=True)
    # Should not raise
    console.show_debug("Debug message")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
