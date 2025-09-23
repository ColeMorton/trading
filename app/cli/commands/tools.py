"""Tools command implementations.

This module provides CLI commands for utility tools, system management,
and maintenance operations.
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import ConfigLoader
from ..models.tools import (
    ExportMADataConfig,
    HealthConfig,
    SchemaConfig,
    ValidationConfig,
)

# Create tools sub-app
app = typer.Typer(
    name="tools", help="Utility tools and system management", no_args_is_help=True
)

console = Console()


@app.command()
def schema(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    file_path: Optional[str] = typer.Option(
        None, "--file", "-f", help="Path to CSV file for schema operations"
    ),
    detect: bool = typer.Option(
        False, "--detect", help="Detect schema version of file"
    ),
    convert: bool = typer.Option(
        False, "--convert", help="Convert file to target schema"
    ),
    target_schema: str = typer.Option(
        "extended", "--target", help="Target schema: base, extended, filtered"
    ),
    validate_only: bool = typer.Option(
        False, "--validate-only", help="Only validate schema, don't convert"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path for conversions"
    ),
):
    """
    Schema detection and conversion tools.

    This command provides utilities for detecting portfolio CSV schema versions,
    validating schema compliance, and converting between schema formats.

    Examples:
        trading-cli tools schema --detect --file portfolio.csv
        trading-cli tools schema --convert --file base_portfolio.csv --target extended
        trading-cli tools schema --validate-only --file portfolio.csv
    """
    try:
        if not file_path and not detect and not convert:
            rprint(
                "[yellow]Please specify a file and operation (--detect, --convert, or --validate-only)[/yellow]"
            )
            raise typer.Exit(1)

        if not file_path:
            rprint("[red]File path is required for schema operations[/red]")
            raise typer.Exit(1)

        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "file_path": file_path,
            "target_schema": target_schema,
            "validate_only": validate_only,
            "output_file": output_file,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, SchemaConfig, overrides)
        else:
            rprint(
                "[red]Error: No profile specified. Schema tools require a configuration profile.[/red]"
            )
            rprint("Please specify a profile using --profile or -p option")
            raise typer.Exit(1)

        if global_verbose:
            rprint("[dim]Loading schema detection modules...[/dim]")

        # Import schema detection and validation modules
        from ...tools.portfolio.schema_detection import (
            detect_schema_version_from_file,
            normalize_portfolio_data,
        )
        from ...tools.portfolio.schema_validation import (
            generate_schema_compliance_report,
            validate_csv_schema,
        )

        file_path_obj = Path(config.file_path)

        if not file_path_obj.exists():
            rprint(f"[red]File not found: {config.file_path}[/red]")
            raise typer.Exit(1)

        if detect or not convert:
            # Detect schema version
            rprint("🔍 Detecting schema version...")
            try:
                schema_version = detect_schema_version_from_file(config.file_path)
                rprint(f"📋 Detected schema: [cyan]{schema_version.name}[/cyan]")

                # Also run validation
                validation_result = validate_csv_schema(
                    config.file_path, strict=config.strict_mode
                )

                if validation_result["is_valid"]:
                    rprint(f"[green]✅ Schema validation passed[/green]")
                else:
                    rprint(
                        f"[red]❌ Schema validation failed with {len(validation_result['violations'])} violations[/red]"
                    )

                    # Show first few violations
                    for violation in validation_result["violations"][:3]:
                        rprint(f"  • {violation['message']}")

                    if len(validation_result["violations"]) > 3:
                        rprint(
                            f"  • ... and {len(validation_result['violations']) - 3} more"
                        )

                # Show summary
                rprint(
                    f"📊 File contains {validation_result['total_rows']:,} rows with {validation_result['total_columns']} columns"
                )

                if global_verbose:
                    # Generate detailed report
                    report = generate_schema_compliance_report(validation_result)
                    rprint("\n[bold]Detailed Schema Report:[/bold]")
                    rprint(report)

            except Exception as e:
                rprint(f"[red]Schema detection failed: {e}[/red]")
                raise typer.Exit(1)

        if convert and not config.validate_only:
            # Convert schema
            rprint(f"🔄 Converting to {config.target_schema} schema...")

            try:
                import pandas as pd

                # Read source file
                df = pd.read_csv(config.file_path)
                source_data = df.to_dict("records")

                # Normalize to target schema
                normalized_data = normalize_portfolio_data(source_data)

                # Determine output file
                if config.output_file:
                    output_path = Path(config.output_file)
                else:
                    output_path = (
                        file_path_obj.parent
                        / f"{file_path_obj.stem}_{config.target_schema}{file_path_obj.suffix}"
                    )

                # Save converted data
                converted_df = pd.DataFrame(normalized_data)
                converted_df.to_csv(output_path, index=False)

                rprint(f"[green]✅ Schema conversion completed![/green]")
                rprint(f"📁 Output saved to: {output_path}")
                rprint(
                    f"📊 Converted {len(normalized_data):,} rows to {len(converted_df.columns)} columns"
                )

                # Validate converted file
                if global_verbose:
                    rprint("🔍 Validating converted file...")
                    validation_result = validate_csv_schema(
                        str(output_path), strict=False
                    )
                    if validation_result["is_valid"]:
                        rprint(f"[green]✅ Converted file validation passed[/green]")
                    else:
                        rprint(
                            f"[yellow]⚠️ Converted file has {len(validation_result['violations'])} validation issues[/yellow]"
                        )

            except Exception as e:
                rprint(f"[red]Schema conversion failed: {e}[/red]")
                if global_verbose:
                    raise
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error in schema operations: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def validate(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    files: List[str] = typer.Option(
        [], "--file", "-f", help="File paths to validate (can be used multiple times)"
    ),
    directory: Optional[str] = typer.Option(
        None, "--directory", "-d", help="Directory to validate all CSV files"
    ),
    schema_validation: bool = typer.Option(
        True, "--schema/--no-schema", help="Enable/disable schema validation"
    ),
    data_validation: bool = typer.Option(
        True, "--data/--no-data", help="Enable/disable data content validation"
    ),
    strict_mode: bool = typer.Option(False, "--strict", help="Strict validation mode"),
    output_format: str = typer.Option(
        "table", "--output", help="Output format: table, json, summary"
    ),
    save_report: Optional[str] = typer.Option(
        None, "--save-report", help="Save validation report to file"
    ),
):
    """
    Data validation utilities.

    This command validates portfolio CSV files for schema compliance,
    data integrity, and content quality.

    Examples:
        trading-cli tools validate --file portfolio.csv
        trading-cli tools validate --directory ./data/raw/strategies/
        trading-cli tools validate --file portfolio.csv --strict --save-report report.json
    """
    try:
        if not files and not directory:
            rprint(
                "[yellow]Please specify files (--file) or directory (--directory) to validate[/yellow]"
            )
            raise typer.Exit(1)

        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "file_paths": files,
            "directory": directory,
            "schema_validation": schema_validation,
            "data_validation": data_validation,
            "strict_mode": strict_mode,
            "output_format": output_format,
            "save_report": save_report,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, ValidationConfig, overrides)
        else:
            rprint(
                "[red]Error: No profile specified. Validation tools require a configuration profile.[/red]"
            )
            rprint("Please specify a profile using --profile or -p option")
            raise typer.Exit(1)

        if global_verbose:
            rprint("[dim]Loading validation modules...[/dim]")

        # Import validation modules
        from ...tools.portfolio.schema_validation import (
            batch_validate_csv_files,
            generate_schema_compliance_report,
        )
        from ...tools.portfolio.validation import validate_portfolio_schema

        # Collect files to validate
        files_to_validate = []

        if config.file_paths:
            files_to_validate.extend(config.file_paths)

        if config.directory:
            directory_path = Path(config.directory)
            if directory_path.exists() and directory_path.is_dir():
                csv_files = list(directory_path.glob("*.csv"))
                files_to_validate.extend([str(f) for f in csv_files])
                if global_verbose:
                    rprint(
                        f"Found {len(csv_files)} CSV files in directory: {config.directory}"
                    )
            else:
                rprint(f"[red]Directory not found: {config.directory}[/red]")
                raise typer.Exit(1)

        if not files_to_validate:
            rprint("[yellow]No files found to validate[/yellow]")
            raise typer.Exit(0)

        rprint(f"🔍 Validating {len(files_to_validate)} files...")

        # Run validation
        if config.schema_validation:
            validation_results = batch_validate_csv_files(
                files_to_validate, strict=config.strict_mode
            )
        else:
            # Simple data validation without schema checks
            validation_results = {}
            for file_path in files_to_validate:
                try:
                    import pandas as pd

                    df = pd.read_csv(file_path)
                    validation_results[file_path] = {
                        "is_valid": True,
                        "total_rows": len(df),
                        "total_columns": len(df.columns),
                        "violations": [],
                        "warnings": [],
                    }
                except Exception as e:
                    validation_results[file_path] = {
                        "is_valid": False,
                        "error": str(e),
                        "violations": [{"type": "file_error", "message": str(e)}],
                    }

        # Process and display results
        total_files = len(validation_results)
        valid_files = sum(
            1 for result in validation_results.values() if result["is_valid"]
        )
        invalid_files = total_files - valid_files

        # Display results based on output format
        if config.output_format == "table":
            _display_validation_results_table(validation_results)
        elif config.output_format == "json":
            _display_validation_results_json(validation_results)
        else:  # summary
            _display_validation_results_summary(validation_results)

        # Overall summary
        rprint(f"\n📊 Validation Summary: {valid_files}/{total_files} files passed")
        if invalid_files > 0:
            rprint(f"[red]❌ {invalid_files} files failed validation[/red]")
        else:
            rprint(f"[green]✅ All files passed validation![/green]")

        # Save report if requested
        if config.save_report:
            _save_validation_report(validation_results, config.save_report)
            rprint(f"📄 Validation report saved to: {config.save_report}")

        # Exit with error code if any files failed validation
        if invalid_files > 0:
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error in validation: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def health(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    check_files: bool = typer.Option(
        True, "--files/--no-files", help="Check file system health"
    ),
    check_dependencies: bool = typer.Option(
        True, "--deps/--no-deps", help="Check Python dependencies"
    ),
    check_data: bool = typer.Option(
        True, "--data/--no-data", help="Check data integrity"
    ),
    check_config: bool = typer.Option(
        True, "--config/--no-config", help="Check configuration validity"
    ),
    check_performance: bool = typer.Option(
        False, "--performance", help="Run performance checks"
    ),
    output_format: str = typer.Option(
        "table", "--output", help="Output format: table, json, summary"
    ),
    save_report: Optional[str] = typer.Option(
        None, "--save-report", help="Save health report to file"
    ),
):
    """
    System health check.

    This command performs comprehensive health checks on the trading system,
    including file system, dependencies, data integrity, and configuration.

    Examples:
        trading-cli tools health
        trading-cli tools health --performance --save-report health.json
        trading-cli tools health --no-deps --no-data
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "check_files": check_files,
            "check_dependencies": check_dependencies,
            "check_data": check_data,
            "check_config": check_config,
            "check_performance": check_performance,
            "output_format": output_format,
            "save_report": save_report,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, HealthConfig, overrides)
        else:
            rprint(
                "[red]Error: No profile specified. Health tools require a configuration profile.[/red]"
            )
            rprint("Please specify a profile using --profile or -p option")
            raise typer.Exit(1)

        rprint("🔍 Running system health checks...")

        health_results = {
            "timestamp": str(Path().cwd() / "health_check"),
            "checks": {},
            "overall_status": "healthy",
            "issues_found": 0,
        }

        # File system health check
        if config.check_files:
            if global_verbose:
                rprint("[dim]Checking file system health...[/dim]")
            health_results["checks"]["files"] = _check_file_system_health(
                global_verbose
            )

        # Dependencies check
        if config.check_dependencies:
            if global_verbose:
                rprint("[dim]Checking Python dependencies...[/dim]")
            health_results["checks"]["dependencies"] = _check_dependencies_health(
                global_verbose
            )

        # Data integrity check
        if config.check_data:
            if global_verbose:
                rprint("[dim]Checking data integrity...[/dim]")
            health_results["checks"]["data"] = _check_data_integrity(global_verbose)

        # Configuration check
        if config.check_config:
            if global_verbose:
                rprint("[dim]Checking configuration validity...[/dim]")
            health_results["checks"]["config"] = _check_configuration_health(
                global_verbose
            )

        # Performance check
        if config.check_performance:
            if global_verbose:
                rprint("[dim]Running performance checks...[/dim]")
            health_results["checks"]["performance"] = _check_performance_health(
                global_verbose
            )

        # Calculate overall status
        total_issues = sum(
            check.get("issues", 0) for check in health_results["checks"].values()
        )
        health_results["issues_found"] = total_issues

        if total_issues == 0:
            health_results["overall_status"] = "healthy"
        elif total_issues <= 3:
            health_results["overall_status"] = "warning"
        else:
            health_results["overall_status"] = "unhealthy"

        # Display results
        if config.output_format == "table":
            _display_health_results_table(health_results)
        elif config.output_format == "json":
            _display_health_results_json(health_results)
        else:  # summary
            _display_health_results_summary(health_results)

        # Save report if requested
        if config.save_report:
            _save_health_report(health_results, config.save_report)
            rprint(f"📄 Health report saved to: {config.save_report}")

        # Overall summary
        status_color = {"healthy": "green", "warning": "yellow", "unhealthy": "red"}[
            health_results["overall_status"]
        ]

        rprint(
            f"\n🏥 System Health: [{status_color}]{health_results['overall_status'].upper()}[/{status_color}]"
        )
        if total_issues > 0:
            rprint(f"⚠️ Found {total_issues} issues that may need attention")
        else:
            rprint("✅ No issues detected")

        # Exit with appropriate code
        if health_results["overall_status"] == "unhealthy":
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error in health check: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


def _display_validation_results_table(validation_results: dict):
    """Display validation results in table format."""
    table = Table(title="Validation Results", show_header=True)
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Status", style="white", justify="center")
    table.add_column("Rows", style="blue", justify="right")
    table.add_column("Columns", style="blue", justify="right")
    table.add_column("Issues", style="red", justify="right")

    for file_path, result in validation_results.items():
        filename = Path(file_path).name
        status = "✅ PASS" if result["is_valid"] else "❌ FAIL"
        rows = f"{result.get('total_rows', 0):,}" if result.get("total_rows") else "N/A"
        columns = (
            str(result.get("total_columns", 0))
            if result.get("total_columns")
            else "N/A"
        )
        issues = str(len(result.get("violations", [])))

        table.add_row(filename, status, rows, columns, issues)

    console.print(table)


def _display_validation_results_json(validation_results: dict):
    """Display validation results in JSON format."""
    rprint(json.dumps(validation_results, indent=2))


def _display_validation_results_summary(validation_results: dict):
    """Display validation results in summary format."""
    total_files = len(validation_results)
    valid_files = sum(1 for result in validation_results.values() if result["is_valid"])

    rprint(f"📁 Validated {total_files} files")
    rprint(f"✅ Passed: {valid_files}")
    rprint(f"❌ Failed: {total_files - valid_files}")

    if total_files - valid_files > 0:
        rprint("\n[red]Failed files:[/red]")
        for file_path, result in validation_results.items():
            if not result["is_valid"]:
                filename = Path(file_path).name
                issues = len(result.get("violations", []))
                rprint(f"  • {filename} ({issues} issues)")


def _save_validation_report(validation_results: dict, filename: str):
    """Save validation report to file."""
    with open(filename, "w") as f:
        json.dump(validation_results, f, indent=2)


def _check_file_system_health(global_verbose: bool) -> dict:
    """Check file system health."""
    result = {"status": "healthy", "issues": 0, "details": []}

    # Check critical directories
    critical_dirs = ["data", "logs"]
    project_root = Path.cwd()

    for dir_name in critical_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            result["issues"] += 1
            result["details"].append(f"Missing critical directory: {dir_name}")
            result["status"] = "warning"
        elif global_verbose:
            result["details"].append(f"Directory exists: {dir_name}")

    # Check disk space (simplified)
    try:
        import shutil

        total, used, free = shutil.disk_usage(project_root)
        free_gb = free // (1024**3)
        if free_gb < 1:  # Less than 1GB free
            result["issues"] += 1
            result["details"].append(f"Low disk space: {free_gb}GB free")
            result["status"] = "warning"
        elif global_verbose:
            result["details"].append(f"Disk space OK: {free_gb}GB free")
    except Exception as e:
        result["details"].append(f"Could not check disk space: {e}")

    return result


def _check_dependencies_health(global_verbose: bool) -> dict:
    """Check Python dependencies health."""
    result = {"status": "healthy", "issues": 0, "details": []}

    # Check critical imports
    critical_imports = [
        "pandas",
        "polars",
        "typer",
        "rich",
        "pydantic",
        "yfinance",
        "vectorbt",
        "numpy",
    ]

    for module_name in critical_imports:
        try:
            __import__(module_name)
            if global_verbose:
                result["details"].append(f"Module available: {module_name}")
        except ImportError:
            result["issues"] += 1
            result["details"].append(f"Missing module: {module_name}")
            result["status"] = "warning"

    return result


def _check_data_integrity(global_verbose: bool) -> dict:
    """Check data integrity."""
    result = {"status": "healthy", "issues": 0, "details": []}

    project_root = Path.cwd()

    # Check for portfolio files
    portfolio_dir = project_root / "data" / "raw" / "strategies"
    if portfolio_dir.exists():
        csv_files = list(portfolio_dir.glob("*.csv"))
        if len(csv_files) == 0:
            result["issues"] += 1
            result["details"].append("No portfolio CSV files found")
            result["status"] = "warning"
        elif global_verbose:
            result["details"].append(f"Found {len(csv_files)} portfolio files")
    else:
        result["issues"] += 1
        result["details"].append("Portfolio directory missing")
        result["status"] = "warning"

    # Check for price data
    prices_dir = project_root / "data" / "raw" / "prices"
    if prices_dir.exists():
        price_files = list(prices_dir.glob("*.csv"))
        if len(price_files) == 0:
            result["issues"] += 1
            result["details"].append("No price data files found")
            result["status"] = "warning"
        elif global_verbose:
            result["details"].append(f"Found {len(price_files)} price data files")
    else:
        result["issues"] += 1
        result["details"].append("Price data directory missing")
        result["status"] = "warning"

    return result


def _check_configuration_health(global_verbose: bool) -> dict:
    """Check configuration health."""
    result = {"status": "healthy", "issues": 0, "details": []}

    project_root = Path.cwd()

    # Check for CLAUDE.md
    claude_file = project_root / "CLAUDE.md"
    if claude_file.exists():
        if verbose:
            result["details"].append("CLAUDE.md configuration found")
    else:
        result["issues"] += 1
        result["details"].append("CLAUDE.md configuration missing")
        result["status"] = "warning"

    # Check for pyproject.toml
    pyproject_file = project_root / "pyproject.toml"
    if pyproject_file.exists():
        if verbose:
            result["details"].append("pyproject.toml configuration found")
    else:
        result["issues"] += 1
        result["details"].append("pyproject.toml configuration missing")
        result["status"] = "warning"

    return result


def _check_performance_health(global_verbose: bool) -> dict:
    """Check performance health."""
    result = {"status": "healthy", "issues": 0, "details": []}

    # Simple performance check - import time
    import time

    start_time = time.time()
    try:
        import pandas as pd
        import polars as pl
        import vectorbt as vbt

        import_time = time.time() - start_time

        if import_time > 5.0:  # More than 5 seconds
            result["issues"] += 1
            result["details"].append(f"Slow import performance: {import_time:.2f}s")
            result["status"] = "warning"
        elif global_verbose:
            result["details"].append(f"Import performance OK: {import_time:.2f}s")

    except Exception as e:
        result["issues"] += 1
        result["details"].append(f"Performance check failed: {e}")
        result["status"] = "warning"

    return result


def _display_health_results_table(health_results: dict):
    """Display health results in table format."""
    table = Table(title="System Health Check", show_header=True)
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Status", style="white", justify="center")
    table.add_column("Issues", style="red", justify="right")
    table.add_column("Details", style="dim")

    for check_name, check_result in health_results["checks"].items():
        status_icon = "✅" if check_result["status"] == "healthy" else "⚠️"
        status = f"{status_icon} {check_result['status'].upper()}"
        issues = str(check_result["issues"])
        details = "; ".join(check_result["details"][:2])  # Show first 2 details
        if len(check_result["details"]) > 2:
            details += "..."

        table.add_row(check_name.title(), status, issues, details)

    console.print(table)


def _display_health_results_json(health_results: dict):
    """Display health results in JSON format."""
    rprint(json.dumps(health_results, indent=2))


def _display_health_results_summary(health_results: dict):
    """Display health results in summary format."""
    total_checks = len(health_results["checks"])
    healthy_checks = sum(
        1 for check in health_results["checks"].values() if check["status"] == "healthy"
    )

    rprint(f"🔍 Completed {total_checks} health checks")
    rprint(f"✅ Healthy: {healthy_checks}")
    rprint(f"⚠️ Issues: {total_checks - healthy_checks}")

    if total_checks - healthy_checks > 0:
        rprint("\n[yellow]Checks with issues:[/yellow]")
        for check_name, check_result in health_results["checks"].items():
            if check_result["status"] != "healthy":
                rprint(f"  • {check_name.title()}: {check_result['issues']} issues")


def _is_cache_valid(csv_path: str, json_path: str) -> bool:
    """
    Validate both CSV and JSON files exist and JSON contains required structure.

    Args:
        csv_path: Path to CSV file
        json_path: Path to JSON analytics file

    Returns:
        bool: True if cache is valid, False otherwise
    """
    import json
    import os

    # Both files must exist
    if not (os.path.exists(csv_path) and os.path.exists(json_path)):
        return False

    # JSON must be parseable and contain required structure
    try:
        with open(json_path, "r") as f:
            data = json.load(f)

        # Validate required structure
        required_keys = ["metadata", "analytics"]
        return all(key in data for key in required_keys)

    except (json.JSONDecodeError, IOError, KeyError):
        return False


@app.command("export-ma-data")
def export_ma_data(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g., AAPL, BTC-USD)"),
    period: int = typer.Argument(..., help="Moving average period"),
    ma_type: str = typer.Option(
        "SMA", "--ma-type", help="Moving average type: SMA or EMA"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Custom output directory"
    ),
    show_stats: bool = typer.Option(
        True,
        "--show-stats/--no-stats",
        help="Display financial statistics and analytics",
    ),
    stats_format: str = typer.Option(
        "table", "--stats-format", help="Statistics format: table, summary, json"
    ),
    period_detail: str = typer.Option(
        "none",
        "--period-detail",
        help="Period analysis detail level: none, compact, summary, full",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh/--no-refresh",
        help="Force refresh data even if files exist (default: False)",
    ),
):
    """
    Export moving average data as synthetic price data with financial analytics.

    This command exports moving average values as synthetic OHLC price data,
    where the Close price is the moving average value. The output format
    matches standard price data: Date,Open,High,Low,Close,Volume.

    CACHING BEHAVIOR:
    - By default, if both CSV and JSON files exist, uses cached data (faster)
    - Use --refresh to force regeneration even if files exist
    - Cache validation ensures both files exist and JSON contains valid analytics

    Additionally displays comprehensive financial analytics including:
    - Risk metrics (Sharpe Ratio, Sortino Ratio, Max Drawdown, Volatility)
    - Performance metrics (Total Return, CAGR, Calmar Ratio)
    - Trend analysis (Direction, Strength, R-squared)
    - Statistical summary (Mean, Std Dev, Skewness, Kurtosis)

    Period analysis (--period-detail) provides:
    - Weekly and monthly rolling performance metrics (auto-detects crypto vs stock trading days)
    - Seasonality patterns and statistical significance
    - Calendar effects (day of week, month of year)
    - Period comparisons and best/worst performing periods

    Examples:
        trading-cli tools export-ma-data AAPL 20
        trading-cli tools export-ma-data BTC-USD 50 --ma-type EMA
        trading-cli tools export-ma-data MSFT 30 --output-dir ./custom_output/
        trading-cli tools export-ma-data TSLA 25 --no-stats
        trading-cli tools export-ma-data NVDA 15 --stats-format json
        trading-cli tools export-ma-data AAPL 20 --period-detail compact
        trading-cli tools export-ma-data BTC-USD 50 --period-detail full
        trading-cli tools export-ma-data AAPL 20 --refresh  # Force refresh cached data
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Validate MA type
        if ma_type.upper() not in ["SMA", "EMA"]:
            rprint(
                f"[red]Error: Invalid MA type '{ma_type}'. Must be SMA or EMA.[/red]"
            )
            raise typer.Exit(1)

        # Validate stats format
        if stats_format not in ["table", "summary", "json"]:
            rprint(
                f"[red]Error: Invalid stats format '{stats_format}'. Must be table, summary, or json.[/red]"
            )
            raise typer.Exit(1)

        # Validate period detail level
        if period_detail not in ["none", "compact", "summary", "full"]:
            rprint(
                f"[red]Error: Invalid period detail '{period_detail}'. Must be none, compact, summary, or full.[/red]"
            )
            raise typer.Exit(1)

        # Build configuration
        config_data = {
            "ticker": ticker,
            "period": period,
            "ma_type": ma_type.upper(),
            "output_dir": output_dir,
        }

        # Validate configuration using Pydantic model
        try:
            config = ExportMADataConfig(**config_data)
        except Exception as e:
            rprint(f"[red]Configuration error: {e}[/red]")
            raise typer.Exit(1)

        # Import required modules
        import json
        import os
        from datetime import datetime

        # Determine file paths
        output_path = config.output_dir or "data/raw/ma_cross/prices/"
        filename = f"{config.ticker}_{config.period}.csv"
        csv_path = os.path.join(output_path, filename)
        json_path = os.path.join(
            "data/outputs/ma_cross/analysis", f"{config.ticker}_{config.period}.json"
        )

        # Check cache status
        use_cache = _is_cache_valid(csv_path, json_path) and not refresh

        # Initialize metrics variables
        metrics = None
        period_metrics = None

        if use_cache:
            # Load existing data from cache
            rprint(
                f"[yellow]📋 Using cached data for {config.ticker} (period={config.period})[/yellow]"
            )
            rprint(f"[cyan]📁 CSV: {csv_path}[/cyan]")
            rprint(f"[cyan]📊 Analysis: {json_path}[/cyan]")

            try:
                with open(json_path, "r") as f:
                    cached_data = json.load(f)
                metrics = cached_data.get("analytics")
                period_metrics = cached_data.get("period_analysis")
            except Exception as e:
                if global_verbose:
                    rprint(
                        f"[yellow]Warning: Failed to load cached data, forcing refresh: {e}[/yellow]"
                    )
                # Fall through to refresh logic
                use_cache = False

        if not use_cache:
            # Proceed with export and analysis
            if refresh and (_is_cache_valid(csv_path, json_path)):
                rprint(
                    f"[cyan]🔄 Refreshing data for {config.ticker} (period={config.period})[/cyan]"
                )
            elif global_verbose:
                rprint(
                    f"[dim]Exporting {config.ma_type} data for {config.ticker} with period {config.period}[/dim]"
                )

            # Import and call the export function
            from app.tools.export_ma_price_data import export_ma_price_data

            # Call the export function
            export_ma_price_data(config.ticker, config.period, config.ma_type)

            # Success message
            rprint(f"[green]✅ Successfully exported {config.ma_type} data[/green]")
            rprint(f"[cyan]📁 CSV: {csv_path}[/cyan]")

            # Calculate and export analytics to JSON (only when not using cache)
            analysis_export_path = None

            # Calculate financial analytics
            try:
                # Import analytics modules
                import polars as pl

                from app.tools.ma_analytics import analyze_ma_data

                # Read the exported MA data for analysis
                if os.path.exists(csv_path):
                    ma_data = pl.read_csv(csv_path)

                    # Calculate all metrics
                    metrics = analyze_ma_data(
                        ma_data, config.ticker, config.period, config.ma_type
                    )

                    # Calculate period metrics if needed
                    if period_detail != "none":
                        from app.tools.ma_period_analytics import analyze_ma_periods

                        period_metrics = analyze_ma_periods(
                            ma_data, config.ticker, config.period, config.ma_type
                        )

                    # Prepare analysis data for export
                    analysis_data = {
                        "metadata": {
                            "ticker": config.ticker,
                            "period": config.period,
                            "ma_type": config.ma_type,
                            "generated_at": datetime.now().isoformat(),
                            "data_points": len(ma_data),
                            "date_range": {
                                "start": str(ma_data["Date"].min()),
                                "end": str(ma_data["Date"].max()),
                            },
                        },
                        "analytics": metrics,
                    }

                    # Add period analysis if calculated
                    if period_metrics:
                        analysis_data["period_analysis"] = period_metrics

                    # Create analysis output directory
                    analysis_dir = "data/outputs/ma_cross/analysis"
                    os.makedirs(analysis_dir, exist_ok=True)

                    # Save to JSON
                    analysis_filename = f"{config.ticker}_{config.period}.json"
                    analysis_export_path = os.path.join(analysis_dir, analysis_filename)

                    with open(analysis_export_path, "w") as f:
                        json.dump(analysis_data, f, indent=2, default=str)

                    rprint(f"[cyan]📊 Analysis: {analysis_export_path}[/cyan]")

                else:
                    raise Exception(f"CSV export failed - file not found: {csv_path}")

            except Exception as e:
                if global_verbose:
                    rprint(f"[red]Error calculating/exporting analytics: {e}[/red]")
                    raise
                else:
                    rprint(f"[yellow]Warning: Analytics export failed: {e}[/yellow]")

        # Display analytics if requested
        if show_stats and metrics:
            if global_verbose:
                rprint("[dim]Displaying financial analytics...[/dim]")

            try:
                # Import display module
                from app.tools.ma_display import display_ma_analysis

                # Display results based on format
                if stats_format == "json":
                    import json

                    rprint("\n[bold cyan]📊 Financial Analytics (JSON):[/bold cyan]")
                    formatted_json = json.dumps(metrics, indent=2, default=str)
                    rprint(formatted_json)
                elif stats_format == "summary":
                    # Display compact summary
                    summary = metrics["summary"]
                    risk = metrics["risk_metrics"]
                    perf = metrics["performance_metrics"]
                    trend = metrics["trend_metrics"]

                    rprint(f"\n[bold cyan]📊 Analytics Summary:[/bold cyan]")
                    rprint(
                        f"[cyan]Sharpe:[/cyan] {risk['sharpe_ratio']:.3f} | [cyan]Return:[/cyan] {perf['total_return']:+.2f}% | [cyan]Trend:[/cyan] {trend['trend_direction']}"
                    )
                    rprint(
                        f"[cyan]Max DD:[/cyan] {risk['max_drawdown']:.2f}% | [cyan]Volatility:[/cyan] {risk['volatility']:.2f}% | [cyan]R²:[/cyan] {trend['r_squared']:.3f}"
                    )
                else:
                    # Default table format - display complete analysis
                    rprint("")  # Add spacing
                    display_ma_analysis(metrics, console)

            except Exception as e:
                if global_verbose:
                    rprint(f"[red]Error calculating analytics: {e}[/red]")
                    raise
                else:
                    rprint(
                        f"[yellow]Warning: Analytics calculation failed: {e}[/yellow]"
                    )

        # Display period analysis if requested (already calculated if needed)
        if period_detail != "none" and period_metrics:
            if global_verbose:
                rprint("[dim]Displaying period-specific analytics...[/dim]")

            try:
                # Import display module
                from app.tools.ma_display import display_ma_period_analysis

                # Display period analysis based on detail level
                if period_detail == "compact":
                    # Compact display - just the key insights
                    rolling = period_metrics["rolling_performance"]
                    seasonality = period_metrics["seasonality_patterns"]

                    rprint(f"\n[bold cyan]📅 Period Analysis (Compact):[/bold cyan]")

                    if "weekly" in rolling:
                        weekly = rolling["weekly"]
                        rprint(
                            f"[cyan]Weekly Avg Return:[/cyan] {weekly['avg_return']:+.2f}% | [cyan]Win Rate:[/cyan] {weekly['win_rate']:.1f}%"
                        )

                    if "monthly" in rolling:
                        monthly = rolling["monthly"]
                        rprint(
                            f"[cyan]Monthly Avg Return:[/cyan] {monthly['avg_return']:+.2f}% | [cyan]Win Rate:[/cyan] {monthly['win_rate']:.1f}%"
                        )

                    if seasonality.get("strongest_pattern"):
                        pattern = seasonality["strongest_pattern"]
                        rprint(
                            f"[cyan]Strongest Pattern:[/cyan] {pattern['period']} ({pattern['avg_return']:+.2f}%)"
                        )

                elif period_detail == "summary":
                    # Summary display - key tables without full details
                    rprint(f"\n[bold cyan]📅 Period Analysis (Summary):[/bold cyan]")
                    display_ma_period_analysis(period_metrics, console)

                else:
                    # Full display - all tables and details
                    rprint(
                        f"\n[bold cyan]📅 Period Analysis (Full Details):[/bold cyan]"
                    )
                    display_ma_period_analysis(period_metrics, console)

            except Exception as e:
                if global_verbose:
                    rprint(f"[red]Error calculating period analytics: {e}[/red]")
                    raise
                else:
                    rprint(
                        f"[yellow]Warning: Period analytics calculation failed: {e}[/yellow]"
                    )

    except Exception as e:
        if global_verbose:
            rprint(f"[red]Detailed error: {e}[/red]")
            raise
        else:
            rprint(f"[red]Error exporting MA data: {e}[/red]")
            raise typer.Exit(1)


@app.command("export-ma-data-sweep")
def export_ma_data_sweep(
    ctx: typer.Context,
    tickers: str = typer.Option(
        ...,
        "--ticker",
        help="Comma-separated ticker symbols (e.g., 'AAPL,BTC-USD,ETH-USD')",
    ),
    period_min: int = typer.Option(
        ..., "--period-min", help="Minimum MA period for sweep"
    ),
    period_max: int = typer.Option(
        ..., "--period-max", help="Maximum MA period for sweep"
    ),
    period_step: int = typer.Option(
        1, "--period-step", help="Step size for period sweep"
    ),
    ma_type: str = typer.Option(
        "SMA", "--ma-type", help="Moving average type: SMA or EMA"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Custom output directory"
    ),
    show_stats: bool = typer.Option(
        False,
        "--show-stats/--no-stats",
        help="Display financial statistics for each export",
    ),
    stats_format: str = typer.Option(
        "summary", "--stats-format", help="Statistics format: table, summary, json"
    ),
    period_detail: str = typer.Option(
        "none",
        "--period-detail",
        help="Period analysis detail level: none, compact, summary, full",
    ),
):
    """
    Perform parameter sweep analysis for moving average data export.

    This command exports moving average data across multiple tickers and periods,
    generating comprehensive datasets for parameter optimization and analysis.

    The sweep generates all combinations of:
    - Tickers: Each symbol in the comma-separated list
    - Periods: Range from period_min to period_max by period_step

    Each combination exports:
    - CSV: data/raw/ma_cross/prices/{TICKER}_{PERIOD}.csv
    - JSON Analytics: data/outputs/ma_cross/analysis/{TICKER}_{PERIOD}.json

    Examples:
    # Basic crypto sweep
    trading-cli tools export-ma-data-sweep --ticker BTC-USD,ETH-USD --period-min 20 --period-max 200 --period-step 10

    # Single ticker deep analysis
    trading-cli tools export-ma-data-sweep --ticker AAPL --period-min 5 --period-max 100 --period-step 5

    # EMA sweep with statistics
    trading-cli tools export-ma-data-sweep --ticker BTC-USD --period-min 10 --period-max 50 --period-step 5 --ma-type EMA --show-stats
    """
    # Get global verbose flag
    global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

    try:
        # Parse comma-separated tickers
        ticker_list = [
            ticker.strip() for ticker in tickers.split(",") if ticker.strip()
        ]

        # Create and validate configuration
        from app.cli.models.tools import ExportMADataSweepConfig

        config = ExportMADataSweepConfig(
            tickers=ticker_list,
            period_min=period_min,
            period_max=period_max,
            period_step=period_step,
            ma_type=ma_type,
            output_dir=output_dir,
            show_stats=show_stats,
            stats_format=stats_format,
            period_detail=period_detail,
        )

        # Display sweep summary
        total_combinations = config.get_total_combinations()
        period_range = config.get_period_range()

        rprint(f"\n[bold cyan]📊 MA Export Sweep Analysis[/bold cyan]")
        rprint(f"[cyan]Tickers:[/cyan] {', '.join(config.tickers)}")
        rprint(
            f"[cyan]Period Range:[/cyan] {config.period_min} to {config.period_max} (step: {config.period_step})"
        )
        rprint(f"[cyan]MA Type:[/cyan] {config.ma_type}")
        rprint(f"[cyan]Total Combinations:[/cyan] {total_combinations}")
        rprint(
            f"[cyan]Expected Files:[/cyan] {total_combinations * 2} (CSV + JSON per combination)"
        )
        rprint("")

        # Import required modules for the sweep
        import json
        import time
        from datetime import datetime

        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
            TimeElapsedColumn,
        )

        # Initialize tracking variables
        successful_exports = 0
        failed_exports = 0
        export_details = []
        sweep_start_time = time.time()

        # Create output directories
        csv_output_dir = output_dir if output_dir else "data/raw/ma_cross/prices"
        analysis_output_dir = "data/outputs/ma_cross/analysis"
        import os

        os.makedirs(csv_output_dir, exist_ok=True)
        os.makedirs(analysis_output_dir, exist_ok=True)

        # Execute sweep with progress tracking
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                "Exporting MA data sweep...", total=total_combinations
            )

            for ticker in config.tickers:
                for period in period_range:
                    try:
                        # Update progress description
                        progress.update(
                            task, description=f"Processing {ticker} (period={period})"
                        )

                        # Call the existing export_ma_data logic
                        from app.cli.models.tools import ExportMADataConfig
                        from app.tools.export_ma_price_data import export_ma_price_data

                        # Create single export config
                        single_config = ExportMADataConfig(
                            ticker=ticker,
                            period=period,
                            ma_type=config.ma_type,
                            output_dir=config.output_dir,
                        )

                        # Export the data
                        export_ma_price_data(
                            ticker=single_config.ticker,
                            period=single_config.period,
                            ma_type=single_config.ma_type,
                        )

                        # Construct the output path manually (function doesn't return it)
                        output_filename = f"{ticker}_{period}.csv"
                        output_path = os.path.join(csv_output_dir, output_filename)

                        # Generate analytics and export to JSON (replicating the existing logic)
                        try:
                            import polars as pl

                            from app.tools.ma_analytics import analyze_ma_data

                            # Read the exported MA data for analysis
                            if os.path.exists(output_path):
                                ma_data = pl.read_csv(output_path)

                                # Calculate all metrics
                                metrics = analyze_ma_data(
                                    ma_data, ticker, period, config.ma_type
                                )

                                # Calculate period metrics if needed
                                period_metrics = None
                                if config.period_detail != "none":
                                    from app.tools.ma_period_analytics import (
                                        analyze_ma_periods,
                                    )

                                    period_metrics = analyze_ma_periods(
                                        ma_data, ticker, period, config.ma_type
                                    )

                                # Prepare analysis data for export
                                analysis_data = {
                                    "metadata": {
                                        "ticker": ticker,
                                        "period": period,
                                        "ma_type": config.ma_type,
                                        "generated_at": datetime.now().isoformat(),
                                        "data_points": len(ma_data),
                                        "date_range": {
                                            "start": str(ma_data["Date"].min()),
                                            "end": str(ma_data["Date"].max()),
                                        },
                                    },
                                    "analytics": metrics,
                                }

                                # Add period analysis if calculated
                                if period_metrics:
                                    analysis_data["period_analysis"] = period_metrics

                                # Save to JSON
                                analysis_filename = f"{ticker}_{period}.json"
                                analysis_export_path = os.path.join(
                                    analysis_output_dir, analysis_filename
                                )

                                with open(analysis_export_path, "w") as f:
                                    json.dump(analysis_data, f, indent=2, default=str)

                                # Track successful export
                                successful_exports += 1
                                export_details.append(
                                    {
                                        "ticker": ticker,
                                        "period": period,
                                        "status": "success",
                                        "csv_path": output_path,
                                        "json_path": analysis_export_path,
                                    }
                                )

                                # Display stats if requested
                                if config.show_stats:
                                    if config.stats_format == "summary":
                                        rprint(
                                            f"[green]✅ {ticker} (period={period}):[/green] "
                                            f"Return: {metrics['performance_metrics']['total_return']:.1f}%, "
                                            f"Sharpe: {metrics['risk_metrics']['sharpe_ratio']:.2f}"
                                        )
                                    elif config.stats_format == "json":
                                        rprint(
                                            f"[green]✅ {ticker} (period={period}):[/green] JSON: {analysis_export_path}"
                                        )

                            else:
                                raise Exception(
                                    f"CSV export failed - file not found: {output_path}"
                                )

                        except Exception as analytics_error:
                            if global_verbose:
                                rprint(
                                    f"[yellow]Warning: Analytics failed for {ticker} (period={period}): {analytics_error}[/yellow]"
                                )
                            # Still count as successful if CSV was exported
                            successful_exports += 1
                            export_details.append(
                                {
                                    "ticker": ticker,
                                    "period": period,
                                    "status": "partial_success",
                                    "csv_path": output_path,
                                    "json_path": None,
                                    "error": str(analytics_error),
                                }
                            )

                    except Exception as e:
                        failed_exports += 1
                        export_details.append(
                            {
                                "ticker": ticker,
                                "period": period,
                                "status": "failed",
                                "csv_path": None,
                                "json_path": None,
                                "error": str(e),
                            }
                        )

                        if global_verbose:
                            rprint(
                                f"[red]❌ Failed {ticker} (period={period}): {e}[/red]"
                            )
                        else:
                            rprint(f"[red]❌ Failed {ticker} (period={period})[/red]")

                    finally:
                        progress.advance(task)

        # Calculate sweep statistics
        sweep_duration = time.time() - sweep_start_time
        success_rate = (
            (successful_exports / total_combinations) * 100
            if total_combinations > 0
            else 0
        )

        # Create sweep summary
        sweep_summary = {
            "sweep_metadata": {
                "timestamp": datetime.now().isoformat(),
                "tickers": config.tickers,
                "period_range": {
                    "min": config.period_min,
                    "max": config.period_max,
                    "step": config.period_step,
                },
                "ma_type": config.ma_type,
                "total_combinations": total_combinations,
                "processing_time_seconds": sweep_duration,
            },
            "results": {
                "successful_exports": successful_exports,
                "failed_exports": failed_exports,
                "success_rate_percent": success_rate,
            },
            "export_details": export_details,
        }

        # Save sweep summary
        summary_filename = (
            f"sweep_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        summary_path = os.path.join(analysis_output_dir, summary_filename)
        with open(summary_path, "w") as f:
            json.dump(sweep_summary, f, indent=2, default=str)

        # Display final summary
        rprint(f"\n[bold green]✅ MA Export Sweep Completed[/bold green]")
        rprint(f"[cyan]Total Combinations:[/cyan] {total_combinations}")
        rprint(f"[green]Successful Exports:[/green] {successful_exports}")
        rprint(f"[red]Failed Exports:[/red] {failed_exports}")
        rprint(f"[cyan]Success Rate:[/cyan] {success_rate:.1f}%")
        rprint(f"[cyan]Processing Time:[/cyan] {sweep_duration:.1f}s")
        rprint(f"[cyan]Summary Report:[/cyan] {summary_path}")

        if failed_exports > 0:
            rprint(
                f"\n[yellow]Warning: {failed_exports} exports failed. Check summary report for details.[/yellow]"
            )

        # Enhanced Financial Analytics
        if successful_exports > 0:
            rprint(f"\n[bold cyan]🚀 Enhanced Financial Analytics[/bold cyan]")
            rprint("[dim]Loading performance data for comprehensive analysis...[/dim]")

            try:
                # Initialize analytics engine
                from app.tools.ma_display import display_sweep_analysis
                from app.tools.sweep_analytics import SweepAnalyticsEngine

                analytics_engine = SweepAnalyticsEngine(analysis_output_dir)

                # Load sweep data
                period_range = config.get_period_range()
                loaded_count = analytics_engine.load_sweep_data(
                    tickers=config.tickers,
                    periods=list(period_range),
                    ma_type=config.ma_type,
                )

                if loaded_count > 0:
                    rprint(
                        f"[green]✅ Loaded analytics for {loaded_count} successful exports[/green]"
                    )
                    rprint("")  # Add spacing before analytics

                    # Display comprehensive sweep analytics
                    display_sweep_analysis(analytics_engine, console)

                    # Save enhanced analytics to sweep summary
                    if analytics_engine.statistics:
                        enhanced_summary = sweep_summary.copy()
                        enhanced_summary["enhanced_analytics"] = {
                            "loaded_analytics_count": loaded_count,
                            "top_performers": {
                                "best_risk_adjusted": {
                                    "period": analytics_engine.get_top_performers(
                                        "risk_adjusted_score", 1
                                    )[0].period,
                                    "score": analytics_engine.get_top_performers(
                                        "risk_adjusted_score", 1
                                    )[0].risk_adjusted_score,
                                }
                                if analytics_engine.performance_data
                                else None,
                                "highest_sharpe": {
                                    "period": analytics_engine.get_top_performers(
                                        "sharpe_ratio", 1
                                    )[0].period,
                                    "sharpe": analytics_engine.get_top_performers(
                                        "sharpe_ratio", 1
                                    )[0].sharpe_ratio,
                                }
                                if analytics_engine.performance_data
                                else None,
                                "highest_return": {
                                    "period": analytics_engine.get_top_performers(
                                        "total_return", 1
                                    )[0].period,
                                    "return": analytics_engine.get_top_performers(
                                        "total_return", 1
                                    )[0].total_return,
                                }
                                if analytics_engine.performance_data
                                else None,
                            },
                            "recommendations": {
                                rec_type: {
                                    "period": data.period,
                                    "sharpe_ratio": data.sharpe_ratio,
                                    "total_return": data.total_return,
                                    "max_drawdown": data.max_drawdown,
                                }
                                for rec_type, data in analytics_engine.get_optimization_recommendations().items()
                            },
                            "statistics_summary": {
                                metric_key: {
                                    "min": stats.min_value,
                                    "max": stats.max_value,
                                    "median": stats.median_value,
                                    "std_dev": stats.std_dev,
                                    "best_period": stats.best_period,
                                }
                                for metric_key, stats in analytics_engine.statistics.items()
                            },
                        }

                        # Re-save enhanced summary
                        enhanced_summary_filename = f"sweep_summary_enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                        enhanced_summary_path = os.path.join(
                            analysis_output_dir, enhanced_summary_filename
                        )
                        with open(enhanced_summary_path, "w") as f:
                            json.dump(enhanced_summary, f, indent=2, default=str)

                        rprint(
                            f"[cyan]📊 Enhanced Summary:[/cyan] {enhanced_summary_path}"
                        )

                else:
                    rprint(
                        f"[yellow]⚠️ No analytics data available for enhanced analysis[/yellow]"
                    )

            except Exception as analytics_error:
                if global_verbose:
                    rprint(f"[red]Error in enhanced analytics: {analytics_error}[/red]")
                    raise
                else:
                    rprint(
                        f"[yellow]Warning: Enhanced analytics failed: {analytics_error}[/yellow]"
                    )

    except Exception as e:
        if global_verbose:
            rprint(f"[red]Detailed error: {e}[/red]")
            raise
        else:
            rprint(f"[red]Error in MA export sweep: {e}[/red]")
            raise typer.Exit(1)


def _save_health_report(health_results: dict, filename: str):
    """Save health report to file."""
    with open(filename, "w") as f:
        json.dump(health_results, f, indent=2)
