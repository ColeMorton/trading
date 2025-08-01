"""
Position command implementations.

This module provides CLI commands for position management and equity curve generation
from position-level data.
"""

from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.tools.equity_data_extractor import MetricType
from app.tools.position_equity_generator import (
    PositionEquityGenerator,
    generate_position_equity,
)
from app.tools.position_equity_validator import (
    PositionEquityValidator,
    ValidationConfig,
    ValidationStatus,
    validate_all_portfolios,
    validate_portfolio_equity,
)
from app.tools.project_utils import get_project_root

# Create positions sub-app
app = typer.Typer(
    name="positions",
    help="Position management and equity generation",
    no_args_is_help=True,
)

console = Console()


def _log_function(message: str, level: str = "info") -> None:
    """Logging function for position operations."""
    level_colors = {
        "debug": "dim",
        "info": "green",
        "warning": "yellow",
        "error": "red",
    }
    color = level_colors.get(level.lower(), "white")
    rprint(f"[{color}][{level.upper()}][/{color}] {message}")


@app.command()
def list(
    show_stats: bool = typer.Option(False, "--stats", help="Show position statistics"),
) -> None:
    """List available position files and basic statistics."""
    try:
        positions_dir = Path(get_project_root()) / "csv" / "positions"

        if not positions_dir.exists():
            rprint("[red]Positions directory not found[/red]")
            return

        # Find all position CSV files
        position_files = list(positions_dir.glob("*.csv"))

        if not position_files:
            rprint("[yellow]No position files found[/yellow]")
            return

        # Create table
        table = Table(title="Available Position Files")
        table.add_column("Portfolio", style="cyan")
        table.add_column("File Size", justify="right")

        if show_stats:
            table.add_column("Positions", justify="right")
            table.add_column("Open", justify="right")
            table.add_column("Closed", justify="right")

        for file_path in sorted(position_files):
            portfolio_name = file_path.stem
            file_size = f"{file_path.stat().st_size / 1024:.1f} KB"

            row = [portfolio_name, file_size]

            if show_stats:
                try:
                    import pandas as pd

                    df = pd.read_csv(file_path)
                    total_positions = len(df)
                    open_positions = len(df[df["Status"] == "Open"])
                    closed_positions = len(df[df["Status"] == "Closed"])

                    row.extend(
                        [
                            str(total_positions),
                            str(open_positions),
                            str(closed_positions),
                        ]
                    )
                except Exception:
                    row.extend(["?", "?", "?"])

            table.add_row(*row)

        console.print(table)

    except Exception as e:
        rprint(f"[red]Error listing position files: {str(e)}[/red]")


@app.command()
def equity(
    portfolio: Optional[str] = typer.Option(
        None, "--portfolio", "-p", help="Portfolio name (e.g., live_signals, risk_on)"
    ),
    all_portfolios: bool = typer.Option(
        False, "--all", help="Generate equity for all position files"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", "-o", help="Custom output directory"
    ),
    metric_type: str = typer.Option(
        "mean", "--metric", help="Metric type: mean, median, best, worst"
    ),
    init_cash: float = typer.Option(
        10000.0, "--init-cash", help="Initial cash for portfolio reconstruction"
    ),
    overwrite: bool = typer.Option(
        True, "--overwrite/--no-overwrite", help="Overwrite existing equity files"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """Generate equity curves from position data."""
    try:
        if not portfolio and not all_portfolios:
            rprint("[red]Must specify either --portfolio or --all[/red]")
            raise typer.Exit(1)

        if portfolio and all_portfolios:
            rprint("[red]Cannot specify both --portfolio and --all[/red]")
            raise typer.Exit(1)

        # Validate metric type
        try:
            metric_enum = MetricType(metric_type.lower())
        except ValueError:
            rprint(
                f"[red]Invalid metric type: {metric_type}. Valid options: mean, median, best, worst[/red]"
            )
            raise typer.Exit(1)

        # Determine portfolios to process
        portfolios_to_process = []
        if all_portfolios:
            positions_dir = Path(get_project_root()) / "csv" / "positions"
            position_files = list(positions_dir.glob("*.csv"))
            portfolios_to_process = [f.stem for f in position_files]
        else:
            portfolios_to_process = [portfolio]

        if not portfolios_to_process:
            rprint("[yellow]No portfolios found to process[/yellow]")
            return

        # Process each portfolio
        success_count = 0
        error_count = 0

        with console.status("[bold green]Generating equity curves...") as status:
            for portfolio_name in portfolios_to_process:
                try:
                    status.update(f"[bold green]Processing {portfolio_name}...")

                    # Check if output file already exists
                    if output_dir:
                        output_path = Path(output_dir)
                    else:
                        output_path = (
                            Path(get_project_root()) / "csv" / "positions" / "equity"
                        )

                    output_file = output_path / f"{portfolio_name}_equity.csv"

                    if output_file.exists() and not overwrite:
                        rprint(
                            f"[yellow]Skipping {portfolio_name} - equity file already exists[/yellow]"
                        )
                        continue

                    # Generate equity data
                    success = generate_position_equity(
                        portfolio_name=portfolio_name,
                        output_dir=str(output_path) if output_dir else None,
                        metric_type=metric_enum,
                        init_cash=init_cash,
                        log=_log_function if verbose else None,
                    )

                    if success:
                        success_count += 1
                        if verbose:
                            rprint(
                                f"[green]✓ Generated equity for {portfolio_name}[/green]"
                            )
                    else:
                        error_count += 1
                        rprint(
                            f"[red]✗ Failed to generate equity for {portfolio_name}[/red]"
                        )

                except Exception as e:
                    error_count += 1
                    rprint(f"[red]✗ Error processing {portfolio_name}: {str(e)}[/red]")

        # Summary
        rprint(f"\n[bold]Equity Generation Summary:[/bold]")
        rprint(f"[green]✓ Successful: {success_count}[/green]")
        if error_count > 0:
            rprint(f"[red]✗ Errors: {error_count}[/red]")

        # Show output location
        if success_count > 0:
            output_location = output_dir or str(
                Path(get_project_root()) / "csv" / "positions" / "equity"
            )
            rprint(f"\n[blue]Equity files saved to: {output_location}[/blue]")

    except Exception as e:
        rprint(f"[red]Error in equity generation: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def validate(
    portfolio: Optional[str] = typer.Option(
        None, "--portfolio", "-p", help="Portfolio name to validate"
    ),
    all_portfolios: bool = typer.Option(
        False, "--all", help="Validate all position files"
    ),
) -> None:
    """Validate position files for equity generation requirements."""
    try:
        if not portfolio and not all_portfolios:
            rprint("[red]Must specify either --portfolio or --all[/red]")
            raise typer.Exit(1)

        # Determine portfolios to validate
        portfolios_to_validate = []
        if all_portfolios:
            positions_dir = Path(get_project_root()) / "csv" / "positions"
            position_files = list(positions_dir.glob("*.csv"))
            portfolios_to_validate = [f.stem for f in position_files]
        else:
            portfolios_to_validate = [portfolio]

        # Validate each portfolio
        validation_results = []

        for portfolio_name in portfolios_to_validate:
            try:
                from app.tools.position_equity_generator import PositionDataLoader

                loader = PositionDataLoader(log=_log_function)
                positions = loader.load_position_file(portfolio_name)

                # Basic validation checks
                total_positions = len(positions)
                open_positions = len([p for p in positions if p.status == "Open"])
                closed_positions = len([p for p in positions if p.status == "Closed"])
                unique_tickers = len(set(p.ticker for p in positions))

                # Check for required price data
                missing_prices = []
                prices_dir = Path(get_project_root()) / "data" / "raw" / "prices"

                for ticker in set(p.ticker for p in positions):
                    price_file = prices_dir / f"{ticker}_D.csv"
                    if not price_file.exists():
                        missing_prices.append(ticker)

                validation_results.append(
                    {
                        "portfolio": portfolio_name,
                        "valid": len(missing_prices) == 0,
                        "total_positions": total_positions,
                        "open_positions": open_positions,
                        "closed_positions": closed_positions,
                        "unique_tickers": unique_tickers,
                        "missing_prices": missing_prices,
                    }
                )

            except Exception as e:
                validation_results.append(
                    {
                        "portfolio": portfolio_name,
                        "valid": False,
                        "error": str(e),
                    }
                )

        # Display results
        table = Table(title="Position File Validation Results")
        table.add_column("Portfolio", style="cyan")
        table.add_column("Valid", justify="center")
        table.add_column("Positions", justify="right")
        table.add_column("Open", justify="right")
        table.add_column("Closed", justify="right")
        table.add_column("Tickers", justify="right")
        table.add_column("Issues", style="red")

        for result in validation_results:
            if "error" in result:
                table.add_row(
                    result["portfolio"],
                    "[red]✗[/red]",
                    "?",
                    "?",
                    "?",
                    "?",
                    result["error"],
                )
            else:
                status_icon = "[green]✓[/green]" if result["valid"] else "[red]✗[/red]"
                issues = ""
                if result["missing_prices"]:
                    issues = (
                        f"Missing price data: {', '.join(result['missing_prices'])}"
                    )

                table.add_row(
                    result["portfolio"],
                    status_icon,
                    str(result["total_positions"]),
                    str(result["open_positions"]),
                    str(result["closed_positions"]),
                    str(result["unique_tickers"]),
                    issues,
                )

        console.print(table)

        # Summary
        valid_count = sum(1 for r in validation_results if r.get("valid", False))
        total_count = len(validation_results)

        if valid_count == total_count:
            rprint(
                f"\n[green]✓ All {total_count} portfolio(s) are valid for equity generation[/green]"
            )
        else:
            rprint(
                f"\n[yellow]⚠ {valid_count}/{total_count} portfolio(s) are valid for equity generation[/yellow]"
            )

    except Exception as e:
        rprint(f"[red]Error in validation: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def validate_equity(
    portfolio: Optional[str] = typer.Option(
        None, "--portfolio", "-p", help="Portfolio name to validate"
    ),
    all_portfolios: bool = typer.Option(
        False, "--all", help="Validate all portfolio equity curves"
    ),
    output_format: str = typer.Option(
        "console", "--format", help="Output format: console, json, csv"
    ),
    output_file: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (for json/csv formats)"
    ),
    excellent_threshold: float = typer.Option(
        1.0, "--excellent", help="Error percentage threshold for EXCELLENT status"
    ),
    good_threshold: float = typer.Option(
        5.0, "--good", help="Error percentage threshold for GOOD status"
    ),
    warning_threshold: float = typer.Option(
        10.0, "--warning", help="Error percentage threshold for WARNING status"
    ),
    enable_size_adjustment: bool = typer.Option(
        True,
        "--size-adjustment/--no-size-adjustment",
        help="Enable size-based threshold adjustment",
    ),
) -> None:
    """Validate mathematical consistency between position P&L and equity curves."""
    try:
        if not portfolio and not all_portfolios:
            rprint("[red]Must specify either --portfolio or --all[/red]")
            raise typer.Exit(1)

        if portfolio and all_portfolios:
            rprint("[red]Cannot specify both --portfolio and --all[/red]")
            raise typer.Exit(1)

        # Create validation config
        config = ValidationConfig(
            excellent_threshold=excellent_threshold,
            good_threshold=good_threshold,
            warning_threshold=warning_threshold,
            enable_size_adjustment=enable_size_adjustment,
        )

        # Create validator
        validator = PositionEquityValidator(config=config, log=_log_function)

        # Perform validation
        if all_portfolios:
            results = validator.validate_all_portfolios()
        else:
            result = validator.validate_portfolio(portfolio)
            results = {portfolio: result}

        # Generate and display report
        if output_format == "console":
            validator.generate_validation_report(results, "console")
        else:
            report_content = validator.generate_validation_report(
                results, output_format
            )

            if output_file:
                with open(output_file, "w") as f:
                    f.write(report_content)
                rprint(f"[green]Report saved to: {output_file}[/green]")
            else:
                print(report_content)

        # Exit with appropriate code based on worst status
        worst_status = ValidationStatus.EXCELLENT
        for result in results.values():
            if result.status == ValidationStatus.CRITICAL:
                worst_status = ValidationStatus.CRITICAL
                break
            elif (
                result.status == ValidationStatus.WARNING
                and worst_status != ValidationStatus.CRITICAL
            ):
                worst_status = ValidationStatus.WARNING
            elif (
                result.status == ValidationStatus.GOOD
                and worst_status == ValidationStatus.EXCELLENT
            ):
                worst_status = ValidationStatus.GOOD

        if worst_status == ValidationStatus.CRITICAL:
            raise typer.Exit(2)  # Critical issues
        elif worst_status == ValidationStatus.WARNING:
            raise typer.Exit(1)  # Warning issues

    except Exception as e:
        rprint(f"[red]Error in equity validation: {str(e)}[/red]")
        raise typer.Exit(1)


@app.command()
def info(
    portfolio: str = typer.Argument(..., help="Portfolio name to show information for"),
) -> None:
    """Show detailed information about a position file."""
    try:
        from app.tools.position_equity_generator import PositionDataLoader

        loader = PositionDataLoader(log=_log_function)
        positions = loader.load_position_file(portfolio)

        if not positions:
            rprint(f"[yellow]No positions found in {portfolio}[/yellow]")
            return

        # Calculate statistics
        total_positions = len(positions)
        open_positions = [p for p in positions if p.status == "Open"]
        closed_positions = [p for p in positions if p.status == "Closed"]

        unique_tickers = set(p.ticker for p in positions)
        strategy_types = set(p.strategy_type for p in positions)

        # Date range
        min_date = min(p.entry_timestamp for p in positions)
        max_date = max(
            p.exit_timestamp if p.exit_timestamp else p.entry_timestamp
            for p in positions
        )

        # P&L statistics for closed positions
        closed_pnl = [p.pnl for p in closed_positions if p.pnl is not None]
        total_pnl = sum(closed_pnl) if closed_pnl else 0

        # Display information
        rprint(f"\n[bold cyan]Portfolio Information: {portfolio}[/bold cyan]")
        rprint(f"[bold]Date Range:[/bold] {min_date.date()} to {max_date.date()}")
        rprint(f"[bold]Total Positions:[/bold] {total_positions}")
        rprint(f"[bold]Open Positions:[/bold] {len(open_positions)}")
        rprint(f"[bold]Closed Positions:[/bold] {len(closed_positions)}")
        rprint(f"[bold]Unique Tickers:[/bold] {len(unique_tickers)}")
        rprint(f"[bold]Strategy Types:[/bold] {', '.join(strategy_types)}")

        if closed_pnl:
            avg_pnl = total_pnl / len(closed_pnl)
            win_rate = (
                len([pnl for pnl in closed_pnl if pnl > 0]) / len(closed_pnl) * 100
            )
            rprint(f"[bold]Total P&L (Closed):[/bold] ${total_pnl:.2f}")
            rprint(f"[bold]Average P&L:[/bold] ${avg_pnl:.2f}")
            rprint(f"[bold]Win Rate:[/bold] {win_rate:.1f}%")

        # Show tickers
        if len(unique_tickers) <= 10:
            rprint(f"[bold]Tickers:[/bold] {', '.join(sorted(unique_tickers))}")
        else:
            rprint(
                f"[bold]Sample Tickers:[/bold] {', '.join(sorted(list(unique_tickers)[:10]))}... ({len(unique_tickers)} total)"
            )

    except Exception as e:
        rprint(f"[red]Error showing portfolio info: {str(e)}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
