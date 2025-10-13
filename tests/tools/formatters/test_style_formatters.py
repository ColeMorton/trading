"""Tests for style formatting functions."""

from unittest.mock import MagicMock, patch

from app.tools.formatters.style_formatters import create_section_header


class TestCreateSectionHeader:
    """Test suite for create_section_header function."""

    @patch("app.tools.formatters.style_formatters.rprint")
    def test_default_emoji(self, mock_rprint):
        """Test creating section header with default emoji."""
        create_section_header("Test Section")

        # Should call rprint twice (title line and separator line)
        assert mock_rprint.call_count == 2

        # Check first call (title with emoji)
        first_call = mock_rprint.call_args_list[0][0][0]
        assert "Test Section" in first_call
        assert "📊" in first_call
        assert "[bold cyan]" in first_call

        # Check second call (separator line)
        second_call = mock_rprint.call_args_list[1][0][0]
        # Separator should be "=" * (len("Test Section") + 3)
        assert "=" in second_call
        assert len(second_call) == len("Test Section") + 3

    @patch("app.tools.formatters.style_formatters.rprint")
    def test_custom_emoji(self, mock_rprint):
        """Test creating section header with custom emoji."""
        create_section_header("Custom Header", emoji="🎯")

        # Should call rprint twice
        assert mock_rprint.call_count == 2

        # Check first call has custom emoji
        first_call = mock_rprint.call_args_list[0][0][0]
        assert "Custom Header" in first_call
        assert "🎯" in first_call
        assert "[bold cyan]" in first_call

    @patch("app.tools.formatters.style_formatters.rprint")
    def test_separator_length(self, mock_rprint):
        """Test that separator line length matches title length + emoji space."""
        title = "Portfolio Analysis"
        create_section_header(title)

        # Get the separator line (second call)
        second_call = mock_rprint.call_args_list[1][0][0]

        # Separator should be len(title) + 3 (space + emoji + space)
        expected_length = len(title) + 3
        assert len(second_call) == expected_length
        assert second_call == "=" * expected_length

    @patch("app.tools.formatters.style_formatters.rprint")
    def test_multiple_calls_independent(self, mock_rprint):
        """Test that multiple calls produce independent headers."""
        create_section_header("First", emoji="🔥")
        create_section_header("Second", emoji="💰")

        # Should have 4 total calls (2 per header)
        assert mock_rprint.call_count == 4

        # Check first header
        first_title = mock_rprint.call_args_list[0][0][0]
        assert "First" in first_title
        assert "🔥" in first_title

        # Check second header
        third_title = mock_rprint.call_args_list[2][0][0]
        assert "Second" in third_title
        assert "💰" in third_title
