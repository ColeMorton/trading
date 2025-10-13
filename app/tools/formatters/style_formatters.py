"""Style formatting utilities for portfolio display.

This module provides functions for creating styled headers and
visual elements.
"""

from rich import print as rprint


def create_section_header(title: str, emoji: str = "📊") -> None:
    """Create a styled section header.

    Args:
        title: The section title text
        emoji: Emoji to display before the title (default: "📊")
    """
    rprint(f"\n[bold cyan]{emoji} {title}[/bold cyan]")
    rprint("=" * (len(title) + 3))
