"""
Console Display Module.

Provides Rich-based user-facing console output separated from logging concerns.
"""

from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table


class ConsoleDisplay:
    """
    User-facing console display with Rich formatting.

    Provides clean separation between terminal output and file logging.
    Use this for user-facing messages, not for audit logs.
    """

    def __init__(
        self,
        console: Console | None = None,
        show_time: bool = False,
        verbose: bool = False,
        quiet: bool = False,
    ):
        """
        Initialize console display.

        Args:
            console: Rich console instance (creates new if None)
            show_time: Whether to show timestamps in output
            verbose: Enable verbose output
            quiet: Suppress non-essential output
        """
        self.console = console or Console()
        self.show_time = show_time
        self.verbose = verbose
        self.quiet = quiet

    def show_success(self, message: str, **kwargs) -> None:
        """Display success message with green checkmark."""
        self.console.print(f"[green]✅ {message}[/green]", **kwargs)

    def show_error(self, message: str, **kwargs) -> None:
        """Display error message with red X."""
        self.console.print(f"[red]❌ {message}[/red]", **kwargs)

    def show_warning(self, message: str, **kwargs) -> None:
        """Display warning message with yellow warning sign."""
        if not self.quiet:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]", **kwargs)

    def show_info(self, message: str, **kwargs) -> None:
        """Display info message with blue info icon."""
        if not self.quiet:
            self.console.print(f"[blue]ℹ️  {message}[/blue]", **kwargs)  # noqa: RUF001

    def show_debug(self, message: str, **kwargs) -> None:
        """Display debug message (only in verbose mode)."""
        if self.verbose and not self.quiet:
            self.console.print(f"[dim]🔍 {message}[/dim]", **kwargs)

    def show_progress(self, message: str, **kwargs) -> None:
        """Display progress message with gear icon."""
        if not self.quiet:
            self.console.print(f"[cyan]⚙️  {message}[/cyan]", **kwargs)

    def show_heading(self, message: str, level: int = 1, **kwargs) -> None:
        """Display heading with appropriate formatting."""
        if not self.quiet:
            if level == 1:
                self.console.print(f"\n[bold cyan]🚀 {message}[/bold cyan]", **kwargs)
            elif level == 2:
                self.console.print(f"\n[bold blue]📊 {message}[/bold blue]", **kwargs)
            elif level == 3:
                self.console.print(
                    f"\n[bold yellow]💡 {message}[/bold yellow]",
                    **kwargs,
                )
            else:
                self.console.print(f"\n[bold white]• {message}[/bold white]", **kwargs)

    def show_section(self, title: str, content: str = "", **kwargs) -> None:
        """Display content in a panel section."""
        if not self.quiet:
            if content:
                panel = Panel(content, title=title, border_style="blue")
            else:
                panel = Panel(title, border_style="blue")
            self.console.print(panel, **kwargs)

    def show_table(self, table: Table, **kwargs) -> None:
        """Display a Rich table."""
        if not self.quiet:
            self.console.print(table, **kwargs)

    def show_panel(
        self,
        content: str,
        title: str | None = None,
        border_style: str = "blue",
        **kwargs,
    ) -> None:
        """Display content in a panel."""
        if not self.quiet:
            panel = Panel(content, title=title, border_style=border_style, **kwargs)
            self.console.print(panel)

    def show_rule(self, title: str = "", style: str = "blue") -> None:
        """Display a horizontal rule separator."""
        if not self.quiet:
            if title:
                rule = Rule(f"[bold {style}]{title}[/bold {style}]", style=style)
            else:
                rule = Rule(style=style)
            self.console.print(rule)

    def show_completion_banner(self, message: str = "Complete") -> None:
        """Display a completion banner."""
        if not self.quiet:
            panel = Panel(
                f"[bold green]✅ {message}[/bold green]",
                border_style="green",
                box=ROUNDED,
                padding=(0, 2),
            )
            self.console.print(panel)

    def data_summary_table(self, ticker: str, data_info: dict[str, Any]) -> None:
        """Display market data summary in a formatted table."""
        if self.quiet:
            return

        table = Table(
            title=f"📊 Market Data Summary: {ticker}",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="blue",
        )
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Format values nicely
        if "date_range" in data_info:
            table.add_row("Date Range", data_info["date_range"])
        if "price_range" in data_info:
            table.add_row("Price Range", data_info["price_range"])
        if "avg_volume" in data_info:
            volume = data_info["avg_volume"]
            if isinstance(volume, int | float):
                table.add_row("Avg Volume", f"{volume:,.0f}")
            else:
                table.add_row("Avg Volume", str(volume))
        if "frequency" in data_info:
            table.add_row("Frequency", data_info["frequency"])
        if "records_count" in data_info:
            table.add_row("Records", f"{data_info['records_count']:,}")

        self.console.print(table)

    def strategy_header(
        self,
        ticker: str,
        strategy_types: list[str],
        profile: str | None = None,
    ) -> None:
        """Display strategy analysis header with enhanced formatting."""
        if self.quiet:
            return

        title = f"🎯 Strategy Analysis: {ticker}"
        if len(strategy_types) == 1:
            subtitle = f"Strategy: {strategy_types[0]}"
        else:
            subtitle = f"Strategies: {', '.join(strategy_types)}"

        if profile:
            subtitle += f" | Profile: {profile}"

        content = f"[bold white]{subtitle}[/bold white]"

        panel = Panel(
            content,
            title=title,
            border_style="cyan",
            box=ROUNDED,
            padding=(0, 2),
        )

        self.console.print("\n")
        self.console.print(panel)

    def results_summary_table(
        self,
        portfolios_generated: int,
        best_config: str | None = None,
        files_exported: int | None = None,
    ) -> None:
        """Display analysis results summary."""
        if self.quiet:
            return

        table = Table(
            title="📈 Analysis Summary",
            show_header=False,
            box=ROUNDED,
            border_style="green",
        )
        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Portfolios Generated", f"{portfolios_generated:,}")
        if best_config:
            table.add_row("Best Configuration", best_config)
        if files_exported:
            table.add_row("Files Exported", str(files_exported))

        self.console.print(table)

    def verbose_warning(self, message: str, **kwargs) -> None:
        """Display warning message only in verbose mode."""
        if self.verbose and not self.quiet:
            self.console.print(f"[yellow]⚠️  {message}[/yellow]", **kwargs)
