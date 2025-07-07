"""
Concurrency command implementations.

This module provides CLI commands for concurrency analysis,
trade history export, and portfolio interaction analysis.
"""

from pathlib import Path
from typing import Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import ConfigLoader
from ..models.concurrency import ConcurrencyConfig

# Create concurrency sub-app
app = typer.Typer(
    name="concurrency",
    help="Concurrency analysis and trade history",
    no_args_is_help=True,
)

console = Console()


@app.command()
def analyze(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    portfolio: str = typer.Argument(help="Portfolio filename (JSON or CSV)"),
    visualization: bool = typer.Option(
        True,
        "--visualization/--no-visualization",
        help="Enable visualization of results",
    ),
    export_trade_history: bool = typer.Option(
        True, "--export-trade-history/--no-export", help="Export trade history data"
    ),
    allocation: bool = typer.Option(
        True, "--allocation/--no-allocation", help="Include allocation analysis"
    ),
    stop_loss: bool = typer.Option(
        True, "--stop-loss/--no-stop-loss", help="Include stop loss analysis"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview configuration without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Run comprehensive concurrency analysis on a portfolio.

    This command analyzes concurrent exposure between multiple trading
    strategies, calculates risk concentration, and finds optimal combinations.

    Examples:
        trading-cli concurrency analyze crypto_portfolio.json
        trading-cli concurrency analyze --profile default_concurrency risk_on.csv
        trading-cli concurrency analyze portfolio.json --no-visualization --dry-run
    """
    try:
        rprint(f"[bold]Starting concurrency analysis for: {portfolio}[/bold]")

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "portfolio": portfolio,
            "visualization": visualization,
            "export_trade_history": export_trade_history,
            "allocation": allocation,
            "stop_loss": stop_loss,
            "dry_run": dry_run,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, ConcurrencyConfig, overrides)
        else:
            template = loader.get_config_template("concurrency")
            config = loader.load_from_dict(template, ConcurrencyConfig, overrides)

        if dry_run:
            _show_concurrency_config_preview(config)
            return

        if verbose:
            rprint("[dim]Loading concurrency analysis module...[/dim]")

        # Import and execute concurrency analysis
        from ...concurrency.review import run_concurrency_review
        from ...tools.logging_context import logging_context

        with logging_context("cli_concurrency", "concurrency_analyze.log") as log:
            # Convert Pydantic model to dict for existing functions
            config_overrides = {
                "VISUALIZATION": config.visualization,
                "EXPORT_TRADE_HISTORY": config.export_trade_history,
                "REFRESH": config.refresh,
                "SL_CANDLE_CLOSE": config.stop_loss,
                "RATIO_BASED_ALLOCATION": config.allocation,
                "BASE_DIR": str(config.base_dir),
                "REPORT_INCLUDES": {
                    "TICKER_METRICS": True,
                    "STRATEGIES": True,
                    "STRATEGY_RELATIONSHIPS": True,
                    "ALLOCATION": config.allocation,
                },
            }

            # Execute concurrency analysis
            rprint("🔄 Running concurrency analysis...")
            success = run_concurrency_review(config.portfolio, config_overrides)

            if success:
                rprint(f"[green]✅ Concurrency analysis completed successfully![/green]")
                rprint(f"📊 Portfolio: {config.portfolio}")

                # Show expected output locations
                results_dir = config.base_dir / "json"
                if results_dir.exists():
                    rprint(f"📁 Results saved to: {results_dir}")

                    # List key output files
                    json_files = list(results_dir.glob("*.json"))
                    if json_files:
                        rprint("📄 Generated files:")
                        for json_file in json_files[:5]:  # Show first 5
                            rprint(f"  • {json_file.name}")
                        if len(json_files) > 5:
                            rprint(f"  • ... and {len(json_files) - 5} more files")

                if config.export_trade_history:
                    trade_history_dir = config.base_dir / "json" / "trade_history"
                    if trade_history_dir.exists():
                        rprint(f"📈 Trade history exported to: {trade_history_dir}")

                if config.visualization:
                    rprint("📊 Visualization charts generated")

            else:
                rprint(f"[red]❌ Concurrency analysis failed[/red]")
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error running concurrency analysis: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def export(
    portfolio: str = typer.Argument(
        help="Portfolio filename to export trade history from"
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Output directory for trade history files"
    ),
    format: str = typer.Option(
        "json", "--format", "-f", help="Export format: json, csv"
    ),
    include_analytics: bool = typer.Option(
        True, "--analytics/--no-analytics", help="Include trade analytics and metrics"
    ),
):
    """
    Export trade history data from portfolio analysis.

    This command exports detailed trade history including entry/exit points,
    P&L data, and trade analytics for further analysis.

    Examples:
        trading-cli concurrency export crypto_portfolio.json
        trading-cli concurrency export portfolio.csv --output-dir ./exports --format csv
    """
    try:
        rprint(f"[bold]Exporting trade history from: {portfolio}[/bold]")

        # Validate portfolio file exists
        portfolio_path = Path(portfolio)
        if not portfolio_path.exists():
            rprint(f"[red]Portfolio file not found: {portfolio}[/red]")
            raise typer.Exit(1)

        # Set up output directory
        if output_dir is None:
            output_dir = Path("./trade_history_exports")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Import required modules
        from ...concurrency.review import run_concurrency_review
        from ...tools.logging_context import logging_context

        with logging_context("cli_trade_export", "trade_export.log") as log:
            # Configure for trade history export only
            config_overrides = {
                "EXPORT_TRADE_HISTORY": True,
                "VISUALIZATION": False,  # Disable to focus on export
                "BASE_DIR": str(output_dir.parent),
                "REFRESH": True,
                "REPORT_INCLUDES": {
                    "TICKER_METRICS": include_analytics,
                    "STRATEGIES": True,
                    "STRATEGY_RELATIONSHIPS": False,
                    "ALLOCATION": False,
                },
            }

            rprint("📊 Running analysis to generate trade history...")
            success = run_concurrency_review(str(portfolio_path), config_overrides)

            if success:
                # Check for generated trade history files
                trade_history_dir = output_dir.parent / "json" / "trade_history"

                if trade_history_dir.exists():
                    trade_files = list(trade_history_dir.glob("*.json"))

                    if trade_files:
                        rprint(f"[green]✅ Trade history export completed![/green]")
                        rprint(f"📁 Exported {len(trade_files)} trade history files")
                        rprint(f"📂 Location: {trade_history_dir}")

                        # Copy files to requested output directory if different
                        if output_dir != trade_history_dir:
                            import shutil

                            for trade_file in trade_files:
                                dest_file = output_dir / trade_file.name
                                shutil.copy2(trade_file, dest_file)
                                rprint(f"  • {trade_file.name}")
                            rprint(f"📁 Files copied to: {output_dir}")
                        else:
                            for trade_file in trade_files:
                                rprint(f"  • {trade_file.name}")

                        # Convert to CSV if requested
                        if format.lower() == "csv":
                            _convert_trade_history_to_csv(trade_files, output_dir)
                    else:
                        rprint(
                            "[yellow]⚠️ No trade history files were generated[/yellow]"
                        )
                        rprint(
                            "This may indicate no trades were executed in the analysis"
                        )
                else:
                    rprint("[yellow]⚠️ Trade history directory not found[/yellow]")
                    rprint("The analysis may not have generated trade data")
            else:
                rprint(f"[red]❌ Trade history export failed[/red]")
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error exporting trade history: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def review(
    portfolio: str = typer.Argument(help="Portfolio filename to review"),
    focus: str = typer.Option(
        "all", "--focus", help="Analysis focus: all, relationships, allocation, metrics"
    ),
    output_format: str = typer.Option(
        "table", "--output", help="Output format: table, json, summary"
    ),
    save_report: Optional[str] = typer.Option(
        None, "--save-report", help="Save detailed report to file"
    ),
):
    """
    Review portfolio interactions and strategy relationships.

    This command provides a quick overview of portfolio composition,
    strategy relationships, and key metrics without full analysis.

    Examples:
        trading-cli concurrency review crypto_portfolio.json
        trading-cli concurrency review portfolio.csv --focus allocation
        trading-cli concurrency review portfolio.json --output json --save-report report.json
    """
    try:
        rprint(f"[bold]Reviewing portfolio: {portfolio}[/bold]")

        # Validate portfolio file exists
        portfolio_path = Path(portfolio)
        if not portfolio_path.exists():
            rprint(f"[red]Portfolio file not found: {portfolio}[/red]")
            raise typer.Exit(1)

        # Import required modules
        from ...tools.logging_context import logging_context
        from ...tools.portfolio.enhanced_loader import load_portfolio_with_context

        with logging_context("cli_portfolio_review", "portfolio_review.log") as log:
            rprint("📊 Loading portfolio data...")

            # Load portfolio using the enhanced loader
            portfolio_data = load_portfolio_with_context(str(portfolio_path), log)

            if portfolio_data:
                # Generate portfolio review
                review_data = _generate_portfolio_review(portfolio_data, focus)

                # Display results based on output format
                if output_format == "table":
                    _display_portfolio_review_table(review_data)
                elif output_format == "json":
                    _display_portfolio_review_json(review_data)
                else:  # summary
                    _display_portfolio_review_summary(review_data)

                # Save report if requested
                if save_report:
                    _save_portfolio_review_report(review_data, save_report)
                    rprint(f"📄 Detailed report saved to: {save_report}")

                rprint(f"[green]✅ Portfolio review completed![/green]")
            else:
                rprint(f"[red]❌ Failed to load portfolio data[/red]")
                raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error reviewing portfolio: {e}[/red]")
        raise typer.Exit(1)


def _show_concurrency_config_preview(config: ConcurrencyConfig):
    """Display concurrency configuration preview for dry run."""
    table = Table(title="Concurrency Analysis Configuration Preview", show_header=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Portfolio File", str(config.portfolio))
    table.add_row("Base Directory", str(config.base_dir))
    table.add_row("Refresh Data", str(config.refresh))
    table.add_row("Visualization", str(config.visualization))
    table.add_row("Export Trade History", str(config.export_trade_history))
    table.add_row("Include Allocation", str(config.allocation))
    table.add_row("Include Stop Loss", str(config.stop_loss))

    console.print(table)
    rprint("\n[yellow]This is a dry run. Remove --dry-run to execute.[/yellow]")


def _convert_trade_history_to_csv(json_files: list, output_dir: Path):
    """Convert JSON trade history files to CSV format."""
    import json

    import pandas as pd

    rprint("🔄 Converting trade history to CSV format...")

    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                data = json.load(f)

            # Convert to DataFrame and save as CSV
            if isinstance(data, list) and data:
                df = pd.DataFrame(data)
                csv_file = output_dir / f"{json_file.stem}.csv"
                df.to_csv(csv_file, index=False)
                rprint(f"  • Converted {json_file.name} → {csv_file.name}")
        except Exception as e:
            rprint(f"  ⚠️ Failed to convert {json_file.name}: {e}")


def _generate_portfolio_review(portfolio_data: list, focus: str) -> dict:
    """Generate portfolio review data based on focus area."""
    review = {
        "total_strategies": len(portfolio_data),
        "strategies": [],
        "allocation_summary": {},
        "performance_summary": {},
        "risk_summary": {},
        "focus_area": focus,
    }

    total_allocation = 0
    total_score = 0
    total_win_rate = 0
    total_return = 0
    valid_strategies = 0

    for i, strategy in enumerate(portfolio_data):
        strategy_info = {
            "index": i + 1,
            "ticker": strategy.get("Ticker", strategy.get("TICKER", "Unknown")),
            "strategy_type": strategy.get(
                "Strategy Type", strategy.get("STRATEGY_TYPE", "Unknown")
            ),
            "score": strategy.get("Score", 0),
            "win_rate": strategy.get("Win Rate [%]", 0),
            "total_return": strategy.get("Total Return [%]", 0),
            "allocation": strategy.get(
                "Allocation [%]", strategy.get("ALLOCATION", None)
            ),
            "stop_loss": strategy.get("Stop Loss [%]", strategy.get("STOP_LOSS", None)),
        }

        review["strategies"].append(strategy_info)

        # Aggregate metrics
        if strategy_info["allocation"]:
            total_allocation += float(strategy_info["allocation"])

        if strategy_info["score"]:
            total_score += float(strategy_info["score"])
            valid_strategies += 1

        if strategy_info["win_rate"]:
            total_win_rate += float(strategy_info["win_rate"])

        if strategy_info["total_return"]:
            total_return += float(strategy_info["total_return"])

    # Calculate summaries
    if valid_strategies > 0:
        review["performance_summary"] = {
            "avg_score": total_score / valid_strategies,
            "avg_win_rate": total_win_rate / valid_strategies,
            "avg_return": total_return / valid_strategies,
            "total_allocation": total_allocation,
        }

    # Count allocations and stop losses
    allocated_strategies = sum(
        1 for s in review["strategies"] if s["allocation"] is not None
    )
    stop_loss_strategies = sum(
        1 for s in review["strategies"] if s["stop_loss"] is not None
    )

    review["allocation_summary"] = {
        "total_allocation": total_allocation,
        "allocated_strategies": allocated_strategies,
        "unallocated_strategies": len(portfolio_data) - allocated_strategies,
        "allocation_percentage": (allocated_strategies / len(portfolio_data)) * 100
        if portfolio_data
        else 0,
    }

    review["risk_summary"] = {
        "stop_loss_strategies": stop_loss_strategies,
        "unprotected_strategies": len(portfolio_data) - stop_loss_strategies,
        "stop_loss_coverage": (stop_loss_strategies / len(portfolio_data)) * 100
        if portfolio_data
        else 0,
    }

    return review


def _display_portfolio_review_table(review_data: dict):
    """Display portfolio review in table format."""

    # Portfolio Summary
    summary_table = Table(title="Portfolio Summary", show_header=True)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Value", style="green")

    summary_table.add_row("Total Strategies", str(review_data["total_strategies"]))
    if review_data["performance_summary"]:
        perf = review_data["performance_summary"]
        summary_table.add_row("Average Score", f"{perf['avg_score']:.2f}")
        summary_table.add_row("Average Win Rate", f"{perf['avg_win_rate']:.1f}%")
        summary_table.add_row("Average Return", f"{perf['avg_return']:.1f}%")

    alloc = review_data["allocation_summary"]
    summary_table.add_row("Total Allocation", f"{alloc['total_allocation']:.1f}%")
    summary_table.add_row(
        "Allocated Strategies",
        f"{alloc['allocated_strategies']}/{review_data['total_strategies']}",
    )

    risk = review_data["risk_summary"]
    summary_table.add_row("Stop Loss Coverage", f"{risk['stop_loss_coverage']:.1f}%")

    console.print(summary_table)

    # Strategy Details
    if review_data["focus_area"] in ["all", "strategies"]:
        rprint("\n[bold]Strategy Details:[/bold]")
        strategy_table = Table(show_header=True)
        strategy_table.add_column("#", style="white", justify="right", no_wrap=True)
        strategy_table.add_column("Ticker", style="cyan", no_wrap=True)
        strategy_table.add_column("Strategy", style="blue", no_wrap=True)
        strategy_table.add_column("Score", style="green", justify="right")
        strategy_table.add_column("Win Rate", style="yellow", justify="right")
        strategy_table.add_column("Return %", style="magenta", justify="right")
        strategy_table.add_column("Allocation", style="bright_green", justify="right")
        strategy_table.add_column("Stop Loss", style="red", justify="right")

        for strategy in review_data["strategies"][:10]:  # Show top 10
            strategy_table.add_row(
                str(strategy["index"]),
                strategy["ticker"],
                strategy["strategy_type"],
                f"{strategy['score']:.2f}" if strategy["score"] else "N/A",
                f"{strategy['win_rate']:.1f}%" if strategy["win_rate"] else "N/A",
                f"{strategy['total_return']:.1f}%"
                if strategy["total_return"]
                else "N/A",
                f"{strategy['allocation']:.1f}%" if strategy["allocation"] else "None",
                f"{strategy['stop_loss']:.1f}%" if strategy["stop_loss"] else "None",
            )

        console.print(strategy_table)

        if len(review_data["strategies"]) > 10:
            rprint(
                f"\n[dim]Showing top 10 of {len(review_data['strategies'])} strategies[/dim]"
            )


def _display_portfolio_review_json(review_data: dict):
    """Display portfolio review in JSON format."""
    import json

    rprint(json.dumps(review_data, indent=2))


def _display_portfolio_review_summary(review_data: dict):
    """Display portfolio review in summary format."""
    total = review_data["total_strategies"]
    alloc = review_data["allocation_summary"]
    risk = review_data["risk_summary"]

    rprint(f"📊 Portfolio contains {total} trading strategies")
    rprint(
        f"💰 Allocation: {alloc['allocated_strategies']}/{total} strategies ({alloc['allocation_percentage']:.1f}%), Total: {alloc['total_allocation']:.1f}%"
    )
    rprint(
        f"🛡️ Risk Protection: {risk['stop_loss_strategies']}/{total} strategies ({risk['stop_loss_coverage']:.1f}%) have stop losses"
    )

    if review_data["performance_summary"]:
        perf = review_data["performance_summary"]
        rprint(
            f"📈 Performance: Avg Score {perf['avg_score']:.2f}, Win Rate {perf['avg_win_rate']:.1f}%, Return {perf['avg_return']:.1f}%"
        )


def _save_portfolio_review_report(review_data: dict, filename: str):
    """Save portfolio review report to file."""
    import json

    with open(filename, "w") as f:
        json.dump(review_data, f, indent=2)
