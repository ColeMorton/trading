#!/usr/bin/env python3
"""
SPDS Health Check Script

Comprehensive health check for the Statistical Performance Divergence System.
Validates system components, data integrity, and export functionality.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import typer
from rich.console import Console
from rich.table import Table

# Setup
console = Console()
logger = logging.getLogger(__name__)


def check_directory_structure() -> Tuple[bool, List[str]]:
    """Check that required directories exist."""
    required_dirs = [
        "data/raw/positions",
        "data/raw/strategies",
        "data/outputs/exports",
        "data/raw/reports",
    ]

    issues = []
    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            issues.append(f"Missing directory: {dir_path}")
        elif not path.is_dir():
            issues.append(f"Not a directory: {dir_path}")

    return len(issues) == 0, issues


def check_portfolio_files() -> Tuple[bool, List[str]]:
    """Check that portfolio files exist and are readable."""
    portfolio_files = [
        "data/raw/positions/live_signals.csv",
        "data/raw/positions/protected.csv",
        "data/raw/positions/risk_on.csv",
        "data/raw/strategies/live_signals.csv",
        "data/raw/strategies/protected.csv",
        "data/raw/strategies/risk_on.csv",
    ]

    issues = []
    found_files = []

    for file_path in portfolio_files:
        path = Path(file_path)
        if path.exists():
            try:
                df = pd.read_csv(path)
                if len(df) == 0:
                    issues.append(f"Empty portfolio file: {file_path}")
                else:
                    found_files.append(file_path)
            except Exception as e:
                issues.append(f"Cannot read {file_path}: {e}")
        else:
            issues.append(f"Missing portfolio file: {file_path}")

    return len(found_files) > 0, issues


def check_export_functionality() -> Tuple[bool, List[str]]:
    """Test export functionality with validation."""
    issues = []

    try:
        from app.tools.services.export_validator import ExportValidator

        validator = ExportValidator()

        # Test with live_signals if it exists
        test_portfolio = "live_signals.csv"
        position_file = Path(f"data/raw/positions/{test_portfolio}")

        if position_file.exists():
            success = validator.generate_fallback_exports(test_portfolio)
            if not success:
                issues.append("Failed to generate test exports")
            else:
                # Validate the test exports
                is_valid, validation_issues = validator.validate_exports(test_portfolio)
                if not is_valid:
                    issues.extend(
                        [
                            f"Export validation failed: {issue}"
                            for issue in validation_issues
                        ]
                    )
        else:
            issues.append("No test portfolio file available for export testing")

    except ImportError as e:
        issues.append(f"Cannot import export validator: {e}")
    except Exception as e:
        issues.append(f"Export test failed: {e}")

    return len(issues) == 0, issues


def check_cli_functionality() -> Tuple[bool, List[str]]:
    """Check CLI functionality."""
    issues = []

    try:
        # Test import of CLI modules
        from app.cli.commands.spds import app as spds_app
        from app.cli.commands.trade_history import app as trade_history_app

        # Check if CLI apps are properly configured
        if not hasattr(spds_app, "commands"):
            issues.append("SPDS CLI app not properly configured")
        if not hasattr(trade_history_app, "commands"):
            issues.append("Trade History CLI app not properly configured")

    except ImportError as e:
        issues.append(f"Cannot import CLI modules: {e}")
    except Exception as e:
        issues.append(f"CLI check failed: {e}")

    return len(issues) == 0, issues


def check_data_quality() -> Tuple[bool, List[str]]:
    """Check data quality in portfolio files."""
    issues = []

    # Check live_signals portfolio specifically
    position_file = Path("data/raw/positions/live_signals.csv")
    if position_file.exists():
        try:
            df = pd.read_csv(position_file)

            # Check required columns
            required_columns = [
                "Status",
                "Current_Unrealized_PnL",
                "Max_Favourable_Excursion",
                "Max_Adverse_Excursion",
                "Days_Since_Entry",
                "Trade_Quality",
            ]

            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                issues.append(
                    f"Missing required columns in live_signals: {missing_columns}"
                )

            # Check for open positions
            if "Status" in df.columns:
                open_positions = df[df["Status"] == "Open"]
                if len(open_positions) == 0:
                    issues.append("No open positions found in live_signals portfolio")
                else:
                    # Check data quality of open positions
                    if open_positions["Current_Unrealized_PnL"].isnull().any():
                        issues.append(
                            "Null values in Current_Unrealized_PnL for open positions"
                        )

                    if open_positions["Max_Favourable_Excursion"].isnull().any():
                        issues.append(
                            "Null values in Max_Favourable_Excursion for open positions"
                        )

        except Exception as e:
            issues.append(f"Error checking live_signals data quality: {e}")

    return len(issues) == 0, issues


def run_comprehensive_health_check() -> Dict[str, Tuple[bool, List[str]]]:
    """Run all health checks."""
    checks = {
        "Directory Structure": check_directory_structure,
        "Portfolio Files": check_portfolio_files,
        "Export Functionality": check_export_functionality,
        "CLI Functionality": check_cli_functionality,
        "Data Quality": check_data_quality,
    }

    results = {}
    for check_name, check_func in checks.items():
        try:
            results[check_name] = check_func()
        except Exception as e:
            results[check_name] = (False, [f"Health check failed: {e}"])

    return results


def display_health_results(results: Dict[str, Tuple[bool, List[str]]]):
    """Display health check results in a nice format."""
    table = Table(title="🏥 SPDS System Health Check", show_header=True)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="white")
    table.add_column("Issues", style="yellow")

    overall_healthy = True

    for component, (is_healthy, issues) in results.items():
        status = "✅ HEALTHY" if is_healthy else "❌ ISSUES"
        if not is_healthy:
            overall_healthy = False

        issue_text = "\n".join(issues) if issues else "None"
        table.add_row(component, status, issue_text)

    console.print(table)
    console.print()

    if overall_healthy:
        console.print("[green]🎉 Overall Status: SYSTEM HEALTHY[/green]")
    else:
        console.print("[red]⚠️  Overall Status: ISSUES DETECTED[/red]")
        console.print("\n[yellow]💡 Recommendations:[/yellow]")
        console.print(
            "1. Run: [code]python -m app.tools.spds_health_check --fix[/code]"
        )
        console.print("2. Check data files and directory structure")
        console.print("3. Verify export functionality manually")

    return overall_healthy


def fix_common_issues():
    """Attempt to fix common issues automatically."""
    console.print("[yellow]🔧 Attempting to fix common issues...[/yellow]")

    # Create missing directories
    required_dirs = [
        "data/raw/positions",
        "data/raw/strategies",
        "data/outputs/spds/statistical_analysis",
        "data/outputs/spds/backtesting_parameters",
        "data/raw/reports/return_distribution",
    ]

    for dir_path in required_dirs:
        path = Path(dir_path)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            console.print(f"✅ Created directory: {dir_path}")

    # Test export functionality
    try:
        from app.tools.services.export_validator import ExportValidator

        validator = ExportValidator()

        # If live_signals exists, regenerate exports
        if Path("data/raw/positions/live_signals.csv").exists():
            success = validator.generate_fallback_exports("live_signals.csv")
            if success:
                console.print("✅ Regenerated live_signals exports")
            else:
                console.print("❌ Failed to regenerate live_signals exports")
    except Exception as e:
        console.print(f"❌ Export fix failed: {e}")

    console.print("[green]🔧 Fix attempt completed[/green]")


def main(
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix common issues"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Run SPDS system health check.

    Validates system components, data integrity, and export functionality.
    """
    if verbose:
        logging.basicConfig(level=logging.INFO)

    console.print("[bold blue]🏥 SPDS System Health Check[/bold blue]")
    console.print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    console.print()

    if fix:
        fix_common_issues()
        console.print()

    # Run health checks
    results = run_comprehensive_health_check()

    # Display results
    is_healthy = display_health_results(results)

    # Exit with appropriate code
    sys.exit(0 if is_healthy else 1)


if __name__ == "__main__":
    typer.run(main)
