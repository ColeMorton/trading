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
from ..models.tools import HealthConfig, SchemaConfig, ValidationConfig

# Create tools sub-app
app = typer.Typer(
    name="tools", help="Utility tools and system management", no_args_is_help=True
)

console = Console()


@app.command()
def schema(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
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

        if verbose:
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

                if verbose:
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
                if verbose:
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
                if verbose:
                    raise
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error in schema operations: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def validate(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
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

        if verbose:
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
                if verbose:
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
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def health(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
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
            if verbose:
                rprint("[dim]Checking file system health...[/dim]")
            health_results["checks"]["files"] = _check_file_system_health(verbose)

        # Dependencies check
        if config.check_dependencies:
            if verbose:
                rprint("[dim]Checking Python dependencies...[/dim]")
            health_results["checks"]["dependencies"] = _check_dependencies_health(
                verbose
            )

        # Data integrity check
        if config.check_data:
            if verbose:
                rprint("[dim]Checking data integrity...[/dim]")
            health_results["checks"]["data"] = _check_data_integrity(verbose)

        # Configuration check
        if config.check_config:
            if verbose:
                rprint("[dim]Checking configuration validity...[/dim]")
            health_results["checks"]["config"] = _check_configuration_health(verbose)

        # Performance check
        if config.check_performance:
            if verbose:
                rprint("[dim]Running performance checks...[/dim]")
            health_results["checks"]["performance"] = _check_performance_health(verbose)

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
        if verbose:
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


def _check_file_system_health(verbose: bool) -> dict:
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
        elif verbose:
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
        elif verbose:
            result["details"].append(f"Disk space OK: {free_gb}GB free")
    except Exception as e:
        result["details"].append(f"Could not check disk space: {e}")

    return result


def _check_dependencies_health(verbose: bool) -> dict:
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
            if verbose:
                result["details"].append(f"Module available: {module_name}")
        except ImportError:
            result["issues"] += 1
            result["details"].append(f"Missing module: {module_name}")
            result["status"] = "warning"

    return result


def _check_data_integrity(verbose: bool) -> dict:
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
        elif verbose:
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
        elif verbose:
            result["details"].append(f"Found {len(price_files)} price data files")
    else:
        result["issues"] += 1
        result["details"].append("Price data directory missing")
        result["status"] = "warning"

    return result


def _check_configuration_health(verbose: bool) -> dict:
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


def _check_performance_health(verbose: bool) -> dict:
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
        elif verbose:
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


def _save_health_report(health_results: dict, filename: str):
    """Save health report to file."""
    with open(filename, "w") as f:
        json.dump(health_results, f, indent=2)
