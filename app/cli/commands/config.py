"""
Configuration command implementations.

This module provides CLI commands for managing configuration profiles,
settings, and system configuration.
"""

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import ConfigLoader, ConfigManager
from ..models.base import BaseConfig

# Create config sub-app
app = typer.Typer(
    name="config", help="Configuration and profile management", no_args_is_help=True
)

console = Console()


@app.command()
def list():
    """List all available configuration profiles."""
    try:
        config_manager = ConfigManager()
        profiles = config_manager.profile_manager.list_profiles()

        if not profiles:
            rprint(
                "[yellow]No profiles found. Use 'create-defaults' to create default profiles.[/yellow]"
            )
            return

        # Create profiles table
        table = Table(title="Available Configuration Profiles", show_header=True)
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Type", style="blue")
        table.add_column("Description", style="white")
        table.add_column("Default", style="green", justify="center")

        default_profile = config_manager.get_default_profile()

        for profile_name in profiles:
            try:
                profile = config_manager.profile_manager.load_profile(profile_name)
                is_default = "✓" if profile_name == default_profile else ""

                table.add_row(
                    profile_name,
                    profile.config_type,
                    profile.metadata.description or "",
                    is_default,
                )
            except Exception as e:
                table.add_row(profile_name, "ERROR", f"Failed to load: {e}", "")

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error listing profiles: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def show(
    profile_name: str = typer.Argument(help="Profile name to display"),
    resolved: bool = typer.Option(
        False, "--resolved", help="Show resolved configuration with inheritance"
    ),
):
    """Show configuration details for a specific profile."""
    try:
        config_manager = ConfigManager()
        profile = config_manager.profile_manager.load_profile(profile_name)

        # Show metadata
        rprint(f"[bold]Profile: {profile.metadata.name}[/bold]")
        rprint(f"Type: {profile.config_type}")
        if profile.metadata.description:
            rprint(f"Description: {profile.metadata.description}")
        if profile.inherits_from:
            rprint(f"Inherits from: {profile.inherits_from}")
        rprint(f"Created: {profile.metadata.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        rprint(f"Updated: {profile.metadata.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")

        # Show configuration
        if resolved and profile.inherits_from:
            rprint("\n[bold]Resolved Configuration (with inheritance):[/bold]")
            config_dict = config_manager.profile_manager.resolve_inheritance(profile)
        else:
            rprint("\n[bold]Configuration:[/bold]")
            config_dict = profile.config

        # Pretty print configuration
        import json

        rprint(json.dumps(config_dict, indent=2, default=str))

    except Exception as e:
        rprint(f"[red]Error showing profile: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def create_defaults():
    """Create default configuration profiles."""
    try:
        loader = ConfigLoader()

        rprint("[bold]Creating default configuration profiles...[/bold]")
        created_profiles = loader.create_default_profiles()

        for profile_name in created_profiles:
            rprint(f"✓ Created profile: [green]{profile_name}[/green]")

        if created_profiles:
            config_manager = ConfigManager()
            config_manager.set_default_profile(created_profiles[0])
            rprint(f"✓ Set default profile: [green]{created_profiles[0]}[/green]")

        rprint(
            f"\n[bold green]Created {len(created_profiles)} default profiles![/bold green]"
        )

    except Exception as e:
        rprint(f"[red]Error creating default profiles: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def set_default(
    profile_name: str = typer.Argument(help="Profile name to set as default"),
):
    """Set the default configuration profile."""
    try:
        config_manager = ConfigManager()

        if not config_manager.profile_manager.profile_exists(profile_name):
            rprint(f"[red]Profile '{profile_name}' does not exist[/red]")
            raise typer.Exit(1)

        config_manager.set_default_profile(profile_name)
        rprint(f"✓ Set default profile: [green]{profile_name}[/green]")

    except Exception as e:
        rprint(f"[red]Error setting default profile: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def edit(profile_name: str = typer.Argument(help="Profile name to edit")):
    """Edit a configuration profile."""
    try:
        # TODO: Implement profile editing functionality
        rprint(f"[yellow]Profile editing for '{profile_name}' coming soon![/yellow]")
        rprint("For now, you can manually edit profile files in:")

        config_manager = ConfigManager()
        profiles_dir = config_manager.profile_manager.profiles_dir
        profile_path = profiles_dir / f"{profile_name}.yaml"

        if profile_path.exists():
            rprint(f"[cyan]{profile_path}[/cyan]")
        else:
            rprint(f"[red]Profile file not found: {profile_path}[/red]")

    except Exception as e:
        rprint(f"[red]Error editing profile: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    profile_name: Optional[str] = typer.Argument(
        None, help="Profile name to validate (validates all if not specified)"
    )
):
    """Validate configuration profiles."""
    try:
        config_manager = ConfigManager()

        if profile_name:
            profiles_to_validate = [profile_name]
        else:
            profiles_to_validate = config_manager.profile_manager.list_profiles()

        if not profiles_to_validate:
            rprint("[yellow]No profiles found to validate[/yellow]")
            return

        rprint(f"[bold]Validating {len(profiles_to_validate)} profile(s)...[/bold]")

        valid_count = 0
        invalid_count = 0

        for name in profiles_to_validate:
            try:
                profile = config_manager.profile_manager.load_profile(name)
                profile.validate_config()
                rprint(f"✓ [green]{name}[/green] - Valid")
                valid_count += 1
            except Exception as e:
                rprint(f"✗ [red]{name}[/red] - Invalid: {e}")
                invalid_count += 1

        rprint(
            f"\n[bold]Validation complete:[/bold] {valid_count} valid, {invalid_count} invalid"
        )

        if invalid_count > 0:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        rprint(f"[red]Error validating profiles: {e}[/red]")
        raise typer.Exit(1)
