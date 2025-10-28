"""
Configuration command implementations.

This module provides CLI commands for managing configuration profiles,
settings, and system configuration.
"""

import builtins

from rich import print as rprint
from rich.console import Console
from rich.table import Table
import typer

from ..config import ConfigManager


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
                "[yellow]No profiles found. Use 'trading-cli init' to verify default profiles.[/yellow]"
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
def verify_defaults():
    """Verify that required default configuration profiles exist."""
    try:
        config_manager = ConfigManager()

        rprint("[bold]Verifying default configuration profiles...[/bold]")

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

        rprint(
            f"\n[bold green]Verified {len(verified_profiles)} default profiles![/bold green]"
        )
        rprint("Use [cyan]trading-cli config list[/cyan] to see all available profiles")

    except Exception as e:
        rprint(f"[red]Error verifying default profiles: {e}[/red]")
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
def edit(
    profile_name: str = typer.Argument(help="Profile name to edit"),
    set_field: builtins.list[str] = typer.Option(
        [], "--set-field", help="Set field value (format: field.path value)"
    ),
    interactive: bool = typer.Option(
        False, "--interactive", help="Use interactive editor"
    ),
):
    """Edit a configuration profile."""
    from ..services.profile_editor_service import ProfileEditorService

    try:
        config_manager = ConfigManager()
        editor_service = ProfileEditorService(config_manager)

        # Load existing profile
        try:
            profile_data = editor_service.load_profile(profile_name)
            rprint(f"[green]Profile loaded successfully: {profile_name}[/green]")
            rprint("[dim]Current configuration:[/dim]")
            _display_profile_summary(profile_data)

        except (FileNotFoundError, ValueError) as e:
            rprint(f"[red]{e}[/red]")
            raise typer.Exit(1)

        # Create backup before editing
        try:
            backup_path = editor_service.create_backup(profile_name)
            rprint(f"[dim]Backup created: {backup_path}[/dim]")
        except Exception as e:
            rprint(f"[yellow]Warning: Could not create backup: {e}[/yellow]")

        # Handle field modifications
        if set_field:
            modified_profile = profile_data.copy()
            for field_spec in set_field:
                parts = field_spec.split()
                if len(parts) < 2:
                    rprint(f"[red]Invalid field specification: {field_spec}[/red]")
                    rprint("[red]Format: --set-field field.path value[/red]")
                    raise typer.Exit(1)

                field_path = parts[0]
                field_value = " ".join(parts[1:])

                # Apply field modification with validation
                try:
                    editor_service.set_field_value(
                        modified_profile, field_path, field_value
                    )
                except ValueError as e:
                    rprint(f"[red]Invalid value for {field_path}: {e}[/red]")
                    raise typer.Exit(1)

            # Save modified profile
            editor_service.save_profile(profile_name, modified_profile)
            rprint(f"[green]Profile updated successfully: {profile_name}[/green]")

        # Handle interactive editing
        elif interactive:
            rprint("[bold cyan]Interactive Profile Editor[/bold cyan]")
            _run_interactive_editor(profile_data, editor_service, profile_name)

        else:
            # Just display current profile for viewing
            rprint(
                f"[yellow]Use --set-field or --interactive to edit {profile_name}[/yellow]"
            )

    except typer.Exit:
        raise
    except Exception as e:
        rprint(f"[red]Error editing profile: {e}[/red]")
        raise typer.Exit(1)


def _display_profile_summary(profile_data: dict) -> None:
    """Display a summary of the profile configuration."""

    # Simple display for now
    rprint("[dim]Profile data loaded and ready for editing[/dim]")


def _run_interactive_editor(
    profile_data: dict, editor_service, profile_name: str
) -> None:
    """Run interactive profile editor."""
    rprint("\n[bold cyan]Interactive Profile Editor[/bold cyan]")

    editable_fields = editor_service.get_editable_fields(profile_data)

    while True:
        rprint("\nSelect field to edit:")
        for i, (field, value) in enumerate(editable_fields, 1):
            rprint(f"[{i}] {field}: {value}")
        rprint(f"[{len(editable_fields) + 1}] Save and exit")

        try:
            choice = input("Enter choice: ").strip()
            choice_num = int(choice)

            if choice_num == len(editable_fields) + 1:
                # Save and exit
                editor_service.save_profile(profile_name, profile_data)
                rprint(f"[green]Profile saved successfully: {profile_name}[/green]")
                break
            if 1 <= choice_num <= len(editable_fields):
                # Edit selected field
                field_name, current_value = editable_fields[choice_num - 1]
                new_value = input(
                    f"Enter new value for {field_name} (current: {current_value}): "
                ).strip()

                if new_value:
                    try:
                        editor_service.set_field_value(
                            profile_data, f"config.{field_name}", new_value
                        )
                        # Update the display list
                        editable_fields[choice_num - 1] = (field_name, new_value)
                        rprint(f"[green]Updated {field_name} = {new_value}[/green]")
                    except ValueError as e:
                        rprint(f"[red]Invalid value: {e}[/red]")
            else:
                rprint("[red]Invalid choice[/red]")

        except (ValueError, KeyboardInterrupt):
            rprint("\n[yellow]Exiting without saving[/yellow]")
            break


@app.command()
def validate(
    profile_name: str
    | None = typer.Argument(
        None, help="Profile name to validate (validates all if not specified)"
    ),
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

                # Basic profile validation
                try:
                    profile.validate_config()
                    validation_status = "✓ Valid configuration"
                    status_color = "green"

                    # Additional checks for portfolio review profiles
                    if profile.config_type == "portfolio_review":
                        warnings = []

                        # Check for inheritance
                        if profile.inherits_from:
                            try:
                                resolved_config = (
                                    config_manager.profile_manager.resolve_inheritance(
                                        profile
                                    )
                                )
                                strategies = resolved_config.get("strategies", [])
                            except Exception:
                                warnings.append("inheritance resolution failed")
                                strategies = profile.config.get("strategies", [])
                        else:
                            strategies = profile.config.get("strategies", [])

                        # Check strategies
                        if not strategies:
                            warnings.append("no strategies defined")
                        elif len(strategies) == 1:
                            validation_status += " (single strategy)"
                        else:
                            validation_status += f" ({len(strategies)} strategies)"

                        # Check for template placeholders
                        config_str = str(profile.config)
                        if "{{" in config_str:
                            warnings.append("contains template placeholders")

                        # Check date range validity
                        start_date = profile.config.get("start_date")
                        end_date = profile.config.get("end_date")
                        if start_date and end_date and start_date >= end_date:
                            warnings.append("invalid date range")

                        # Check benchmark settings
                        benchmark = profile.config.get("benchmark", {})
                        if isinstance(benchmark, dict):
                            if benchmark.get("symbol") == "null":
                                validation_status += " (no benchmark)"

                        if warnings:
                            validation_status += f" - Warning: {', '.join(warnings)}"
                            status_color = "yellow"

                    rprint(
                        f"✓ [{status_color}]{name}[/{status_color}] - {validation_status}"
                    )
                    valid_count += 1

                except Exception as validation_error:
                    rprint(
                        f"✗ [red]{name}[/red] - Configuration invalid: {validation_error}"
                    )
                    invalid_count += 1

            except Exception as e:
                rprint(f"✗ [red]{name}[/red] - Load failed: {e}")
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
