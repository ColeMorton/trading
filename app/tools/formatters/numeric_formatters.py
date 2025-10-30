"""Numeric formatting utilities for portfolio display.

This module provides functions for formatting numeric values with appropriate
color coding and styling.
"""

from typing import Any

from rich.text import Text


def format_percentage(value: Any, positive_good: bool = True) -> Text:
    """Format percentage with color coding.

    Args:
        value: The percentage value to format
        positive_good: Whether positive values should be colored green (default: True)

    Returns:
        Rich Text object with formatted percentage and color styling
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        color = (
            "green"
            if (val > 0 and positive_good) or (val < 0 and not positive_good)
            else "red"
        )
        if abs(val) < 0.01:  # Very small values
            color = "yellow"
        return Text(f"{val:.2f}%", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_currency(value: Any) -> Text:
    """Format currency value with color coding.

    Args:
        value: The currency value to format

    Returns:
        Rich Text object with formatted currency and color styling
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        color = "green" if val > 0 else "red" if val < 0 else "yellow"
        if abs(val) >= 1000000:
            formatted = f"${val / 1000000:.2f}M"
        elif abs(val) >= 1000:
            formatted = f"${val / 1000:.1f}K"
        else:
            formatted = f"${val:.2f}"
        return Text(formatted, style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_score(value: Any) -> Text:
    """Format score with color coding based on performance thresholds.

    Args:
        value: The score value to format

    Returns:
        Rich Text object with formatted score, emoji, and color styling
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        if val >= 1.5:
            color = "bright_green"
            emoji = "🔥"
        elif val >= 1.2:
            color = "green"
            emoji = "📈"
        elif val >= 1.0:
            color = "yellow"
            emoji = "⚖️"
        elif val >= 0.8:
            color = "orange"
            emoji = "⚠️"
        else:
            color = "red"
            emoji = "📉"
        return Text(f"{emoji} {val:.4f}", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_win_rate(value: Any) -> Text:
    """Format win rate with color coding.

    Args:
        value: The win rate percentage to format

    Returns:
        Rich Text object with formatted win rate and color styling
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        if val > 50:
            color = "green"
        elif val >= 45:
            color = "yellow"
        else:
            color = "red"
        return Text(f"{val:.1f}%", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_ratio(value: Any) -> Text:
    """Format ratio with color coding based on performance thresholds.

    Args:
        value: The ratio value to format

    Returns:
        Rich Text object with formatted ratio and color styling
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        if val >= 1.34:
            color = "green"
        elif val >= 1.0:
            color = "yellow"
        else:
            color = "red"
        return Text(f"{val:.2f}", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")
