"""
Main CLI application using Typer.

This module provides the main entry point and command structure for the
unified trading CLI system.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from .commands import (
    concurrency,
    config,
    portfolio,
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
        loader = ConfigLoader()

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
                "Use 'trading-cli config create-defaults' to create default profiles",
            )

        console.print(table)

        # Show quick help
        rprint("\n[bold]Quick Start:[/bold]")
        rprint(
            "• [cyan]trading-cli config create-defaults[/cyan] - Create default configuration profiles"
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
        loader = ConfigLoader()

        rprint("[bold]Initializing Trading CLI...[/bold]")

        # Create profiles directory
        profiles_dir = config_manager.profile_manager.profiles_dir
        profiles_dir.mkdir(parents=True, exist_ok=True)
        rprint(f"✓ Created profiles directory: [cyan]{profiles_dir}[/cyan]")

        # Create default profiles
        with console.status("[bold green]Creating default profiles..."):
            created_profiles = loader.create_default_profiles()

        for profile_name in created_profiles:
            rprint(f"✓ Created profile: [green]{profile_name}[/green]")

        # Set default profile
        if created_profiles:
            config_manager.set_default_profile(created_profiles[0])
            rprint(f"✓ Set default profile: [green]{created_profiles[0]}[/green]")

        rprint("\n[bold green]Initialization complete![/bold green]")
        rprint("Use [cyan]trading-cli status[/cyan] to check system status")
        rprint("Use [cyan]trading-cli config list[/cyan] to see available profiles")

    except Exception as e:
        rprint(f"[red]Error during initialization: {e}[/red]")
        raise typer.Exit(1)


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    profiles_dir: Optional[Path] = typer.Option(
        None, "--profiles-dir", help="Custom profiles directory"
    ),
):
    """
    Unified Trading Strategy Analysis CLI.

    A comprehensive system for strategy execution, portfolio management,
    and concurrency analysis with type-safe configuration management.
    """
    # Store global options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
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


def main():
    """Module execution entry point."""
    cli_main()


if __name__ == "__main__":
    main()
