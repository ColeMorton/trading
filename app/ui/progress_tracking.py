"""
Progress Tracking Module.

Provides progress bars and status displays for long-running operations.
"""

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.status import Status


class ProgressTracker:
    """
    Progress tracking with Rich progress bars.

    Provides consistent progress display for long-running operations.
    """

    def __init__(self, console: Console | None = None):
        """
        Initialize progress tracker.

        Args:
            console: Rich console instance
        """
        self.console = console or Console()

    def status_context(self, message: str, spinner: str = "dots"):
        """
        Create a status context for operations.

        Args:
            message: Status message to display
            spinner: Spinner style

        Returns:
            Status context manager
        """
        return Status(message, console=self.console, spinner=spinner)

    def progress_context(
        self,
        description: str = "Processing...",
        show_speed: bool = False,
        show_percentage: bool = True,
    ):
        """
        Create a progress context for operations with progress bars.

        Args:
            description: Progress description
            show_speed: Show processing speed
            show_percentage: Show percentage complete

        Returns:
            Progress context manager
        """
        columns = [
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ]

        if show_percentage:
            columns.append(TaskProgressColumn())

        if show_speed:
            columns.extend(
                [
                    TextColumn("•"),
                    TextColumn("[progress.data]{task.fields[speed]}"),
                ]
            )

        columns.append(TimeElapsedColumn())

        return Progress(
            *columns, console=self.console, expand=True, refresh_per_second=10
        )

    def parameter_progress_context(
        self,
        strategy_name: str,
        total_combinations: int,
        show_parallel_workers: bool = True,
        performance_mode: str = "standard",
    ):
        """
        Create enhanced progress context for parameter sweep operations.

        Args:
            strategy_name: Name of the strategy
            total_combinations: Total number of parameter combinations
            show_parallel_workers: Show parallel worker count
            performance_mode: Display mode (minimal/standard/detailed)

        Returns:
            Progress context manager
        """
        if performance_mode == "minimal":
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=30),
                TaskProgressColumn(),
                TimeElapsedColumn(),
            ]
        elif performance_mode == "standard":
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=35),
                TaskProgressColumn(),
                TextColumn("•"),
                TextColumn("[blue]{task.fields[rate]}/sec[/blue]"),
                TimeElapsedColumn(),
            ]
            if show_parallel_workers:
                columns.insert(
                    -1, TextColumn("[dim]({task.fields[workers]} workers)[/dim]")
                )
        else:  # detailed/benchmark
            columns = [
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=40),
                TaskProgressColumn(),
                TextColumn("•"),
                TextColumn("[blue]{task.fields[rate]}/sec[/blue]"),
                TextColumn("•"),
                TextColumn("[green]ETA: {task.fields[eta]}[/green]"),
                TimeElapsedColumn(),
            ]
            if show_parallel_workers:
                columns.insert(
                    -2, TextColumn("[dim]({task.fields[workers]} workers)[/dim]")
                )

        # Calculate adaptive refresh rate
        if total_combinations < 50:
            refresh_rate = 8
        elif total_combinations < 500:
            refresh_rate = 4
        else:
            refresh_rate = 2

        return Progress(
            *columns,
            console=self.console,
            expand=True,
            refresh_per_second=refresh_rate,
        )
