"""
Main CLI application using Typer.

This module provides the main entry point and command structure for the
unified trading CLI system.
"""

from pathlib import Path
import sys

from rich import print as rprint
from rich.console import Console
from rich.table import Table
import typer

from .commands import (
    concurrency,
    config,
    portfolio,
    positions,
    seasonality,
    spds,
    strategy,
    tools,
    trade_history,
)
from .config import ConfigLoader, ConfigManager


# Initialize Typer app
app = typer.Typer(
    name="trading-cli",
    help="Unified Trading Strategy Analysis CLI",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

# Add subcommands
app.add_typer(
    strategy.app, name="strategy", help="MA Cross strategy execution and analysis"
)
app.add_typer(
    portfolio.app, name="portfolio", help="Portfolio processing and aggregation"
)
app.add_typer(
    positions.app, name="positions", help="Position management and equity generation"
)
app.add_typer(
    concurrency.app, name="concurrency", help="Concurrency analysis and trade history"
)
app.add_typer(config.app, name="config", help="Configuration and profile management")
app.add_typer(tools.app, name="tools", help="Utility tools and system management")
app.add_typer(
    spds.app,
    name="spds",
    help="Statistical Performance Divergence System - Portfolio Analysis",
)
app.add_typer(
    trade_history.app,
    name="trade-history",
    help="Trade History Analysis and Position Management",
)
app.add_typer(
    seasonality.app,
    name="seasonality",
    help="Seasonality Analysis and Seasonal Pattern Detection",
)

# Initialize console for rich output
console = Console()


@app.command()
def version():
    """Show version information."""
    from . import __version__

    rprint(f"[bold blue]Trading CLI[/bold blue] version [green]{__version__}[/green]")


@app.command()
def status():
    """Show system status and configuration."""
    try:
        config_manager = ConfigManager()
        ConfigLoader()

        # Create status table
        table = Table(
            title="Trading CLI Status", show_header=True, header_style="bold magenta"
        )
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="white")

        # Check profiles directory
        profiles_dir = config_manager.profile_manager.profiles_dir
        if profiles_dir.exists():
            profile_count = len(config_manager.profile_manager.list_profiles())
            table.add_row(
                "Profiles Directory",
                "✓ Found",
                f"{profiles_dir} ({profile_count} profiles)",
            )
        else:
            table.add_row("Profiles Directory", "✗ Missing", f"{profiles_dir}")

        # Check default profile
        default_profile = config_manager.get_default_profile()
        if default_profile:
            table.add_row("Default Profile", "✓ Set", default_profile)
        else:
            table.add_row(
                "Default Profile",
                "⚠ Not Set",
                "Use 'trading-cli config set-default <profile>'",
            )

        # Check available profiles
        profiles = config_manager.profile_manager.list_profiles()
        if profiles:
            table.add_row(
                "Available Profiles",
                "✓ Found",
                ", ".join(profiles[:5]) + ("..." if len(profiles) > 5 else ""),
            )
        else:
            table.add_row(
                "Available Profiles",
                "⚠ None",
                "Use 'trading-cli init' to verify default profiles",
            )

        console.print(table)

        # Show quick help
        rprint("\n[bold]Quick Start:[/bold]")
        rprint(
            "• [cyan]trading-cli init[/cyan] - Initialize and verify default configuration profiles"
        )
        rprint("• [cyan]trading-cli config list[/cyan] - List available profiles")
        rprint(
            "• [cyan]trading-cli strategy run --help[/cyan] - Get help for strategy commands"
        )
        rprint("• [cyan]trading-cli --help[/cyan] - Show all available commands")

    except Exception as e:
        rprint(f"[red]Error checking status: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def init():
    """Initialize the trading CLI with default profiles and configuration."""
    try:
        config_manager = ConfigManager()
        ConfigLoader()

        rprint("[bold]Initializing Trading CLI...[/bold]")

        # Create profiles directory
        profiles_dir = config_manager.profile_manager.profiles_dir
        profiles_dir.mkdir(parents=True, exist_ok=True)
        rprint(f"✓ Created profiles directory: [cyan]{profiles_dir}[/cyan]")

        # Verify required default profiles exist
        with console.status("[bold green]Verifying default profiles..."):
            required_profiles = [
                "default_strategy",
                "default_portfolio",
                "default_trade_history",
                "ma_cross_crypto",
            ]

            verified_profiles = []
            for profile_name in required_profiles:
                try:
                    # Try to load the profile to verify it exists and is valid
                    config_manager.profile_manager.load_profile(profile_name)
                    verified_profiles.append(profile_name)
                except Exception:
                    rprint(
                        f"⚠ Profile not found or invalid: [yellow]{profile_name}[/yellow]"
                    )

        for profile_name in verified_profiles:
            rprint(f"✓ Verified profile: [green]{profile_name}[/green]")

        # Set default profile
        if verified_profiles:
            config_manager.set_default_profile(verified_profiles[0])
            rprint(f"✓ Set default profile: [green]{verified_profiles[0]}[/green]")
        else:
            rprint("[yellow]Warning: No valid default profiles found[/yellow]")

        rprint("\n[bold green]Initialization complete![/bold green]")
        rprint("Use [cyan]trading-cli status[/cyan] to check system status")
        rprint("Use [cyan]trading-cli config list[/cyan] to see available profiles")

    except Exception as e:
        rprint(f"[red]Error during initialization: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def pinescript(
    ctx: typer.Context,
    filename: str = typer.Argument(
        ...,
        help="CSV filename (with or without .csv extension). Searches in data/raw/strategies/",
    ),
    ticker: str
    | None = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Filter to specific ticker(s), comma-separated (e.g., 'BTC-USD' or 'HIMS,MP,NVDA')",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview generation without writing files"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed generation information"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Minimal output - only success/failure and file path",
    ),
):
    """
    Generate PineScript indicator code from strategy CSV file.

    This command generates a multi-ticker breadth oscillator indicator
    from a strategy CSV file. The CSV file is automatically looked up in
    data/raw/strategies/ and the output is saved to the same directory.

    The generated indicator includes:
    - Automatic ticker selection dropdown
    - Individual strategy signal calculations (SMA, EMA, MACD)
    - Percentage-based breadth oscillator
    - Visual threshold lines and coloring
    - Statistics display table
    - Alert conditions

    Examples:
        trading-cli pinescript MSTR.csv
        trading-cli pinescript SMR
        trading-cli pinescript portfolio --ticker BTC-USD
        trading-cli pinescript portfolio.csv -t HIMS,MP,NVDA
        trading-cli pinescript portfolio --dry-run --verbose
        trading-cli pinescript portfolio --quiet
    """
    try:
        # Get global verbose flag or use local
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
        verbose = verbose or global_verbose

        # Construct CSV path
        if not filename.endswith(".csv"):
            filename = f"{filename}.csv"

        csv_dir = Path("data/raw/strategies")
        csv_path = csv_dir / filename

        if not csv_path.exists():
            rprint(f"[red]Error: CSV file not found: {csv_path}[/red]")
            rprint(f"[yellow]Looking in: {csv_dir.absolute()}[/yellow]")
            raise typer.Exit(1)

        # Parse ticker filter if provided
        ticker_filter = None
        if ticker:
            ticker_filter = [t.strip() for t in ticker.split(",")]
            if verbose and not quiet:
                rprint(f"[dim]Applying ticker filter: {', '.join(ticker_filter)}[/dim]")

        # Construct output path (same directory, .pine extension)
        output_filename = csv_path.stem
        if ticker_filter and len(ticker_filter) == 1:
            # If single ticker, include in filename
            output_filename = f"{csv_path.stem}_{ticker_filter[0]}"
        elif ticker_filter:
            # If multiple tickers, include count
            output_filename = f"{csv_path.stem}_{len(ticker_filter)}tickers"

        output_path = csv_dir / f"{output_filename}.pine"

        # Show generation info (unless quiet)
        if not quiet:
            if verbose:
                rprint("[cyan]Generating PineScript indicator...[/cyan]")
                rprint(f"[dim]Source: {csv_path}[/dim]")
                rprint(f"[dim]Output: {output_path}[/dim]")
            else:
                rprint(f"[cyan]Generating PineScript from {csv_path.name}...[/cyan]")

        # Import and initialize generator
        from app.tools.pinescript_generator import PineScriptGenerator

        generator = PineScriptGenerator(str(csv_path), ticker_filter=ticker_filter)

        # Get statistics
        stats = generator.get_stats()

        # Generate code
        if dry_run:
            code = generator.generate(output_path=None)
            if not quiet:
                rprint("[yellow]DRY RUN - No files written[/yellow]")
        else:
            code = generator.generate(output_path=str(output_path))

        # Display results based on mode
        if quiet:
            # Quiet mode: minimal output
            if dry_run:
                rprint("[yellow]DRY RUN[/yellow]")
            else:
                rprint("[green]Success[/green]")
                rprint(f"{output_path}")
        else:
            # Default comprehensive preview
            rprint("[green]Successfully generated PineScript indicator![/green]")

            if not dry_run:
                rprint(f"\n[cyan]Output File:[/cyan] {output_path}")

            # Create ticker breakdown table
            from rich.panel import Panel

            table = Table(
                title="Strategy Breakdown", show_header=True, header_style="bold cyan"
            )
            table.add_column("Ticker", style="cyan", no_wrap=True)
            table.add_column("Strategies", justify="right", style="green")
            table.add_column("Types", style="yellow")

            for ticker_name in stats["tickers"]:
                count = stats["strategies_per_ticker"][ticker_name]
                types = ", ".join(stats["strategy_types_per_ticker"][ticker_name])
                table.add_row(ticker_name, str(count), types)

            console.print(table)

            # Summary statistics in panel
            summary_text = (
                f"[cyan]Total Strategies:[/cyan] {stats['total_strategies']}\n"
            )
            summary_text += f"[cyan]Total Tickers:[/cyan] {stats['total_tickers']}\n"
            summary_text += f"[cyan]Lines of Code:[/cyan] {len(code.splitlines())}"

            if ticker_filter:
                summary_text += (
                    f"\n[yellow]Filtered to:[/yellow] {', '.join(ticker_filter)}"
                )

            summary_panel = Panel(summary_text, title="Summary", border_style="cyan")
            console.print(summary_panel)

            # Code preview with syntax highlighting
            from rich.syntax import Syntax

            rprint("\n[bold cyan]Code Preview (first 40 lines):[/bold cyan]")
            preview_code = "\n".join(code.splitlines()[:40])
            syntax = Syntax(preview_code, "pine", theme="monokai", line_numbers=True)
            console.print(syntax)

            if len(code.splitlines()) > 40:
                rprint(f"[dim]... and {len(code.splitlines()) - 40} more lines[/dim]")

            # Usage instructions
            if not dry_run:
                usage_panel = Panel(
                    "[bold]Next Steps:[/bold]\n"
                    "1. Open TradingView Pine Editor\n"
                    f"2. Copy contents of: [cyan]{output_path}[/cyan]\n"
                    "3. Paste into Pine Editor and click 'Add to Chart'\n"
                    "4. Select ticker from dropdown to view breadth oscillator",
                    title="Usage Instructions",
                    border_style="green",
                )
                console.print(usage_panel)
            else:
                rprint("\n[yellow]Remove --dry-run to write the file[/yellow]")

        # Verbose additions (if not quiet)
        if verbose and not quiet:
            rprint("\n[bold cyan]Detailed Breakdown:[/bold cyan]")
            for ticker_name in stats["tickers"]:
                count = stats["strategies_per_ticker"][ticker_name]
                types = stats["strategy_types_per_ticker"][ticker_name]
                rprint(
                    f"  [cyan]{ticker_name}:[/cyan] {count} strategies ({', '.join(types)})"
                )

    except ValueError as e:
        # Handle validation errors (e.g., no strategies found for ticker)
        rprint(f"[red]Validation Error: {e}[/red]")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error generating PineScript: {e}[/red]")
        if verbose and not quiet:
            console.print_exception()
        raise typer.Exit(1)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output with rich formatting"
    ),
    show_output: bool = typer.Option(
        False,
        "--show-output",
        "-o",
        help="Enable rich terminal output (default: enabled)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all output except success/failure messages",
    ),
    profiles_dir: Path
    | None = typer.Option(None, "--profiles-dir", help="Custom profiles directory"),
):
    """
    Unified Trading Strategy Analysis CLI.

    A comprehensive system for strategy execution, portfolio management,
    and concurrency analysis with type-safe configuration management.

    By default, the CLI shows rich terminal output for better user experience.
    Use --quiet to suppress all output except success/failure messages.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["show_output"] = show_output
    ctx.obj["quiet"] = quiet  # Only quiet when explicitly requested
    ctx.obj["profiles_dir"] = profiles_dir

    # Configure console for verbose output
    if verbose:
        console.print(
            f"[dim]Using profiles directory: {profiles_dir or 'default'}[/dim]"
        )


def cli_main():
    """Entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        rprint("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        rprint(f"[red]Unexpected error: {e}[/red]")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            raise
        sys.exit(1)


def module_main():
    """Module execution entry point."""
    cli_main()


if __name__ == "__main__":
    module_main()
