"""Text formatting utilities for portfolio display.

This module provides functions for formatting text values, durations,
and status indicators.
"""

from rich.text import Text


def format_duration(value) -> Text:
    """Format duration with compact display.

    Args:
        value: Duration value (typically a pandas timedelta or string)

    Returns:
        Rich Text object with formatted duration
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        duration_str = str(value)
        # Parse "X days HH:MM:SS.microseconds" format
        if "days" in duration_str:
            parts = duration_str.split()
            days = int(parts[0])
            if len(parts) > 2:
                time_part = parts[2]
                hours = int(time_part.split(":")[0])
                return Text(f"{days}d {hours}h", style="blue")
            else:
                return Text(f"{days}d", style="blue")
        else:
            # Handle time-only format "HH:MM:SS"
            time_parts = duration_str.split(":")
            if len(time_parts) >= 2:
                hours = int(float(time_parts[0]))
                return Text(f"{hours}h", style="blue")
            else:
                return Text(str(value)[:10], style="dim")  # Truncate long values
    except (ValueError, TypeError, IndexError):
        return Text(str(value)[:10], style="dim")  # Truncate and show as-is


def parse_duration_to_hours(value) -> float:
    """Parse duration string to total hours for averaging calculations.

    Args:
        value: Duration value (typically a pandas timedelta or string)

    Returns:
        Total hours as a float
    """
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return 0.0

    try:
        duration_str = str(value)
        total_hours = 0.0

        # Parse "X days HH:MM:SS.microseconds" format
        if "days" in duration_str:
            parts = duration_str.split()
            days = int(parts[0])
            total_hours = days * 24.0  # Convert days to hours

            if len(parts) > 2:
                time_part = parts[2]
                time_components = time_part.split(":")
                if len(time_components) >= 1:
                    total_hours += int(time_components[0])  # Add hours
                if len(time_components) >= 2:
                    total_hours += (
                        int(time_components[1]) / 60.0
                    )  # Add minutes as fractional hours
        else:
            # Handle time-only format "HH:MM:SS"
            time_parts = duration_str.split(":")
            if len(time_parts) >= 1:
                total_hours += int(float(time_parts[0]))  # Hours
            if len(time_parts) >= 2:
                total_hours += int(time_parts[1]) / 60.0  # Minutes as fractional hours

        return total_hours
    except (ValueError, TypeError, IndexError):
        return 0.0


def format_average_duration(hours: float) -> str:
    """Format average hours back to readable duration string.

    Args:
        hours: Total hours as a float

    Returns:
        Formatted duration string (e.g., "5d 12h", "18h")
    """
    if hours <= 0:
        return "0h"

    days = int(hours // 24)
    remaining_hours = int(hours % 24)

    if days > 0:
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        else:
            return f"{days}d"
    else:
        return f"{remaining_hours}h"


def format_status(status: str) -> Text:
    """Format status with emoji and color coding.

    Args:
        status: Status string ("Entry", "Active", "Exit", or "Inactive")

    Returns:
        Rich Text object with formatted status
    """
    if status == "Entry":
        return Text("🎯 Entry", style="green")
    elif status == "Active":
        return Text("🔒 Active", style="blue")
    elif status == "Exit":
        return Text("🚪 Exit", style="red")
    else:  # Inactive
        return Text("Inactive", style="white")


def format_signal_status(entry: bool, exit: bool, unconfirmed: str = None) -> Text:
    """Format signal status with appropriate icons and colors.

    Args:
        entry: Whether an entry signal is present
        exit: Whether an exit signal is present
        unconfirmed: Unconfirmed signal indicator

    Returns:
        Rich Text object with formatted signal status
    """
    if entry:
        return Text("🎯 ENTRY", style="bright_green bold")
    elif exit:
        return Text("🚪 EXIT", style="red bold")
    elif unconfirmed and str(unconfirmed).lower() not in ["none", "n/a", ""]:
        return Text("⏳ PENDING", style="yellow")
    else:
        return Text("🔒 HOLD", style="blue")
