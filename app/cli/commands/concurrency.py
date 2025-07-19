"""
Concurrency command implementations.

This module provides CLI commands for concurrency analysis,
trade history export, and portfolio interaction analysis.
"""

import sys
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
    portfolio: Optional[str] = typer.Argument(
        None,
        help="Portfolio filename (JSON or CSV) - uses profile portfolio if not specified",
    ),
    # General configuration options
    base_dir: Optional[str] = typer.Option(
        None, "--base-dir", help="Base directory for logs and outputs"
    ),
    refresh: bool = typer.Option(
        True, "--refresh/--no-refresh", help="Refresh cached market data"
    ),
    csv_use_hourly: bool = typer.Option(
        False, "--hourly/--daily", help="Use hourly timeframe for CSV strategies"
    ),
    sort_by: Optional[str] = typer.Option(
        None,
        "--sort-by",
        help="Field to sort results by (score, win_rate, total_return, sharpe_ratio, allocation)",
    ),
    ensure_counterpart: bool = typer.Option(
        True,
        "--ensure-counterpart/--no-counterpart",
        help="Ensure strategy counterpart validation",
    ),
    initial_value: Optional[float] = typer.Option(
        None, "--initial-value", help="Initial portfolio value for position sizing"
    ),
    target_var: Optional[float] = typer.Option(
        None, "--target-var", help="Target Value at Risk (VaR) threshold (0.0-1.0)"
    ),
    # Risk management options
    max_risk_per_strategy: Optional[float] = typer.Option(
        None, "--max-risk-strategy", help="Maximum risk percentage per strategy"
    ),
    max_risk_total: Optional[float] = typer.Option(
        None, "--max-risk-total", help="Maximum total portfolio risk percentage"
    ),
    risk_calculation_method: Optional[str] = typer.Option(
        None,
        "--risk-method",
        help="Risk calculation method (standard, monte_carlo, bootstrap, var)",
    ),
    # Execution and signal options
    execution_mode: Optional[str] = typer.Option(
        None,
        "--execution-mode",
        help="Signal execution timing mode (same_period, next_period, delayed)",
    ),
    signal_definition_mode: Optional[str] = typer.Option(
        None,
        "--signal-mode",
        help="Signal definition approach (complete_trade, entry_only, exit_only, both)",
    ),
    ratio_based_allocation: bool = typer.Option(
        False,
        "--ratio-allocation/--no-ratio-allocation",
        help="Enable ratio-based allocation",
    ),
    # Analysis options
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
    # Memory optimization options
    memory_optimization: bool = typer.Option(
        False,
        "--memory-optimization",
        help="Enable memory optimization for large portfolios",
    ),
    memory_threshold: int = typer.Option(
        1000, "--memory-threshold", help="Memory threshold in MB for optimization"
    ),
    # Control options
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
        trading-cli concurrency analyze --profile risk_on
        trading-cli concurrency analyze risk_on.csv --profile risk_on
        trading-cli concurrency analyze portfolio.json --no-visualization --dry-run
    """
    try:
        # Load configuration first to determine portfolio
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "visualization": visualization,
            "trade_history": {
                "export_trade_history": export_trade_history,
            },
            "report_includes": {
                "allocation": allocation,
            },
            "memory_optimization": {
                "enable_memory_optimization": memory_optimization,
                "memory_threshold_mb": float(memory_threshold),
            },
            "ratio_based_allocation": ratio_based_allocation,
        }

        # Build general configuration overrides
        general_overrides = {}
        if portfolio is not None:
            general_overrides["portfolio"] = portfolio
        if base_dir is not None:
            general_overrides["base_dir"] = base_dir
        if not refresh:  # Only override if explicitly set to False
            general_overrides["refresh"] = refresh
        if csv_use_hourly:  # Only override if explicitly set to True
            general_overrides["csv_use_hourly"] = csv_use_hourly
        if sort_by is not None:
            general_overrides["sort_by"] = sort_by
        if not ensure_counterpart:  # Only override if explicitly set to False
            general_overrides["ensure_counterpart"] = ensure_counterpart
        if initial_value is not None:
            general_overrides["initial_value"] = initial_value
        if target_var is not None:
            general_overrides["target_var"] = target_var

        # Add general overrides to main overrides if any exist
        if general_overrides:
            overrides["general"] = general_overrides

        # Add risk management overrides if provided
        risk_overrides = {}
        if max_risk_per_strategy is not None:
            risk_overrides["max_risk_per_strategy"] = max_risk_per_strategy
        if max_risk_total is not None:
            risk_overrides["max_risk_total"] = max_risk_total
        if risk_calculation_method is not None:
            risk_overrides["risk_calculation_method"] = risk_calculation_method
        if risk_overrides:
            overrides["risk_management"] = risk_overrides

        # Add execution mode overrides if provided
        if execution_mode is not None:
            overrides["execution_mode"] = execution_mode
        if signal_definition_mode is not None:
            overrides["signal_definition_mode"] = signal_definition_mode

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, ConcurrencyConfig, overrides)
        else:
            template = loader.get_config_template("concurrency")
            config = loader.load_from_dict(template, ConcurrencyConfig, overrides)

        # Validate that we have a portfolio to analyze
        final_portfolio = config.general.portfolio
        if not final_portfolio:
            if profile:
                rprint(
                    f"[red]❌ Error: Profile '{profile}' does not specify a portfolio and no portfolio argument provided[/red]"
                )
                rprint(
                    "Either specify a portfolio argument or use a profile that contains portfolio configuration."
                )
            else:
                rprint(
                    "[red]❌ Error: No portfolio specified and no profile provided[/red]"
                )
                rprint("Usage: trading-cli concurrency analyze PORTFOLIO [OPTIONS]")
                rprint("   or: trading-cli concurrency analyze --profile PROFILE_NAME")
            raise typer.Exit(1)

        # Display which portfolio we're analyzing
        portfolio_source = (
            "from command line"
            if portfolio is not None
            else f"from profile '{profile}'"
            if profile
            else "from default configuration"
        )
        rprint(
            f"[bold]Starting concurrency analysis for: {final_portfolio}[/bold] [dim]({portfolio_source})[/dim]"
        )

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
                "EXPORT_TRADE_HISTORY": config.trade_history.export_trade_history,
                "REFRESH": config.general.refresh,
                "SL_CANDLE_CLOSE": True,  # Default from config_defaults.py
                "RATIO_BASED_ALLOCATION": config.report_includes.allocation,
                "BASE_DIR": str(config.general.base_dir)
                if config.general.base_dir
                else "",
                "ENABLE_MEMORY_OPTIMIZATION": config.memory_optimization.enable_memory_optimization,
                "MEMORY_THRESHOLD_MB": config.memory_optimization.memory_threshold_mb,
                "REPORT_INCLUDES": {
                    "TICKER_METRICS": True,
                    "STRATEGIES": True,
                    "STRATEGY_RELATIONSHIPS": True,
                    "ALLOCATION": config.report_includes.allocation,
                },
            }

            # Execute concurrency analysis
            rprint("🔄 Running concurrency analysis...")
            portfolio_value = config.general.portfolio
            success = run_concurrency_review(portfolio_value, config_overrides)

            if success:
                rprint(f"[green]✅ Concurrency analysis completed successfully![/green]")
                rprint(f"📊 Portfolio: {config.general.portfolio}")

                # Show expected output locations
                from pathlib import Path

                base_dir = (
                    Path(config.general.base_dir)
                    if config.general.base_dir
                    else Path.cwd()
                )
                results_dir = base_dir / "json"
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

                if config.trade_history.export_trade_history:
                    trade_history_dir = base_dir / "json" / "trade_history"
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

    # General configuration
    table.add_row("Portfolio File", str(config.general.portfolio))
    table.add_row(
        "Base Directory",
        str(config.general.base_dir) if config.general.base_dir else "Project Root",
    )
    table.add_row("Refresh Data", str(config.general.refresh))
    table.add_row("CSV Use Hourly", str(config.general.csv_use_hourly))
    table.add_row("Sort By", str(config.general.sort_by))
    table.add_row("Ensure Counterpart", str(config.general.ensure_counterpart))
    table.add_row("Initial Value", f"${config.general.initial_value:,.2f}")
    table.add_row("Target VaR", f"{config.general.target_var:.1%}")

    # Risk management
    table.add_row(
        "Max Risk Per Strategy", f"{config.risk_management.max_risk_per_strategy:.1f}%"
    )
    table.add_row("Max Risk Total", f"{config.risk_management.max_risk_total:.1f}%")
    table.add_row(
        "Risk Calculation Method", str(config.risk_management.risk_calculation_method)
    )

    # Execution modes
    execution_mode_value = (
        config.execution_mode.value
        if hasattr(config.execution_mode, "value")
        else str(config.execution_mode)
    )
    signal_mode_value = (
        config.signal_definition_mode.value
        if hasattr(config.signal_definition_mode, "value")
        else str(config.signal_definition_mode)
    )
    table.add_row("Execution Mode", execution_mode_value)
    table.add_row("Signal Definition Mode", signal_mode_value)
    table.add_row("Ratio-Based Allocation", str(config.ratio_based_allocation))

    # Analysis options
    table.add_row("Visualization", str(config.visualization))
    table.add_row(
        "Export Trade History", str(config.trade_history.export_trade_history)
    )
    table.add_row("Include Allocation", str(config.report_includes.allocation))

    # Memory optimization
    table.add_row(
        "Memory Optimization",
        str(config.memory_optimization.enable_memory_optimization),
    )
    if config.memory_optimization.enable_memory_optimization:
        table.add_row(
            "Memory Threshold", f"{config.memory_optimization.memory_threshold_mb} MB"
        )

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


@app.command()
def optimize(
    portfolio: str = typer.Argument(help="Portfolio filename to optimize"),
    min_strategies: int = typer.Option(
        3, "--min-strategies", "-m", help="Minimum strategies per combination"
    ),
    max_permutations: Optional[int] = typer.Option(
        None, "--max-permutations", help="Maximum permutations to evaluate"
    ),
    allocation_mode: str = typer.Option(
        "EQUAL",
        "--allocation",
        help="Allocation mode: EQUAL, SIGNAL_COUNT, PERFORMANCE, RISK_ADJUSTED",
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Save optimization results to file"
    ),
    visualize: bool = typer.Option(
        True, "--visualize/--no-visualize", help="Generate visualization charts"
    ),
    parallel: bool = typer.Option(
        False, "--parallel", help="Enable parallel processing for faster execution"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Find optimal strategy combinations using permutation analysis.

    This command systematically evaluates different combinations of strategies
    to find the subset that maximizes efficiency while maintaining diversification.

    Examples:
        trading-cli concurrency optimize portfolio.json
        trading-cli concurrency optimize portfolio.csv --min-strategies 5 --parallel
        trading-cli concurrency optimize portfolio.json --allocation RISK_ADJUSTED --output results.json
    """
    try:
        rprint(f"[bold]Starting optimization analysis for: {portfolio}[/bold]")

        # Validate portfolio file exists
        portfolio_path = Path(portfolio)
        if not portfolio_path.exists():
            rprint(f"[red]Portfolio file not found: {portfolio}[/red]")
            raise typer.Exit(1)

        # Import required modules
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
            TimeRemainingColumn,
        )

        from ...concurrency.review import run_concurrency_review
        from ...concurrency.tools.permutation import find_optimal_permutation
        from ...tools.logging_context import logging_context

        with logging_context("cli_optimization", "optimization.log") as log:
            # Configure for optimization
            config_overrides = {
                "PORTFOLIO": str(portfolio_path),
                "OPTIMIZE": True,
                "OPTIMIZE_MIN_STRATEGIES": min_strategies,
                "OPTIMIZE_MAX_PERMUTATIONS": max_permutations,
                "ALLOCATION_MODE": allocation_mode,
                "VISUALIZATION": visualize,
                "PARALLEL_PROCESSING": parallel,
                "REFRESH": True,
            }

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
            ) as progress:
                # Run optimization with progress tracking
                task = progress.add_task(
                    "Optimizing strategy combinations...", total=100
                )

                def update_progress(current: int, total: int):
                    progress.update(task, completed=(current / total) * 100)

                # Execute optimization
                results = run_concurrency_review(
                    str(portfolio_path),
                    config_overrides,
                    progress_callback=update_progress,
                )

                if results and "optimization_results" in results:
                    opt_results = results["optimization_results"]
                    rprint(f"[green]✅ Optimization completed successfully![/green]")
                    rprint(f"📊 Analyzed {opt_results['total_analyzed']} combinations")
                    rprint(
                        f"🏆 Best efficiency score: {opt_results['best_efficiency']:.4f}"
                    )

                    if opt_results.get("best_permutation"):
                        rprint("📈 Optimal strategy combination:")
                        for strategy in opt_results["best_permutation"]:
                            rprint(f"  • {strategy}")

                    if opt_results.get("improvement_percentage"):
                        rprint(
                            f"📊 Improvement over full portfolio: "
                            f"{opt_results['improvement_percentage']:.1f}%"
                        )

                    # Save results if requested
                    if output_file:
                        import json

                        with open(output_file, "w") as f:
                            json.dump(opt_results, f, indent=2)
                        rprint(f"💾 Results saved to: {output_file}")

                    if visualize and opt_results.get("visualization_path"):
                        rprint(
                            f"📊 Visualization saved to: {opt_results['visualization_path']}"
                        )
                else:
                    rprint(f"[red]❌ Optimization failed[/red]")
                    raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error running optimization: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command(name="monte-carlo")
def monte_carlo(
    portfolio: str = typer.Argument(help="Portfolio filename for Monte Carlo analysis"),
    simulations: int = typer.Option(
        10000, "--simulations", "-n", help="Number of Monte Carlo simulations"
    ),
    confidence_levels: str = typer.Option(
        "95,99",
        "--confidence",
        help="Confidence levels for risk metrics (comma-separated)",
    ),
    horizon_days: int = typer.Option(
        252, "--horizon", help="Forecast horizon in days (252 = 1 year)"
    ),
    bootstrap: bool = typer.Option(
        True, "--bootstrap/--no-bootstrap", help="Use bootstrap resampling"
    ),
    save_simulations: bool = typer.Option(
        False, "--save-simulations", help="Save individual simulation paths"
    ),
    output_file: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Save Monte Carlo results to file"
    ),
    visualize: bool = typer.Option(
        True, "--visualize/--no-visualize", help="Generate visualization charts"
    ),
):
    """
    Run Monte Carlo simulations for risk analysis and forecasting.

    This command performs Monte Carlo simulations to analyze potential portfolio
    outcomes, calculate risk metrics, and generate probabilistic forecasts.

    Examples:
        trading-cli concurrency monte-carlo portfolio.json
        trading-cli concurrency monte-carlo portfolio.csv --simulations 50000 --horizon 365
        trading-cli concurrency monte-carlo portfolio.json --confidence 90,95,99 --save-simulations
    """
    try:
        rprint(f"[bold]Starting Monte Carlo analysis for: {portfolio}[/bold]")

        # Parse confidence levels
        confidence_list = [float(cl.strip()) for cl in confidence_levels.split(",")]

        # Validate portfolio file exists
        portfolio_path = Path(portfolio)
        if not portfolio_path.exists():
            rprint(f"[red]Portfolio file not found: {portfolio}[/red]")
            raise typer.Exit(1)

        # Import required modules
        from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

        from ...concurrency.tools.monte_carlo import MonteCarloManager
        from ...tools.logging_context import logging_context

        with logging_context("cli_monte_carlo", "monte_carlo.log") as log:
            rprint(f"🎲 Running {simulations:,} Monte Carlo simulations...")
            rprint(f"📊 Forecast horizon: {horizon_days} days")
            rprint(f"📈 Confidence levels: {confidence_levels}")

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            ) as progress:
                task = progress.add_task(
                    f"Running {simulations:,} simulations...", total=simulations
                )

                # Initialize Monte Carlo manager
                mc_manager = MonteCarloManager(
                    n_simulations=simulations,
                    confidence_levels=confidence_list,
                    horizon_days=horizon_days,
                    use_bootstrap=bootstrap,
                )

                # Load portfolio data
                from ...tools.portfolio import load_portfolio

                portfolio_data = load_portfolio(str(portfolio_path))

                # Run simulations with progress tracking
                def update_progress(completed: int):
                    progress.update(task, completed=completed)

                results = mc_manager.run_portfolio_simulation(
                    portfolio_data, progress_callback=update_progress
                )

                if results:
                    rprint(f"[green]✅ Monte Carlo analysis completed![/green]")

                    # Display key metrics
                    rprint("\n[bold]Risk Metrics:[/bold]")
                    for cl in confidence_list:
                        var = results["risk_metrics"][f"var_{int(cl)}"]
                        cvar = results["risk_metrics"][f"cvar_{int(cl)}"]
                        rprint(f"  • VaR ({cl}%): {var:.2%}")
                        rprint(f"  • CVaR ({cl}%): {cvar:.2%}")

                    rprint("\n[bold]Portfolio Statistics:[/bold]")
                    rprint(f"  • Expected Return: {results['expected_return']:.2%}")
                    rprint(f"  • Volatility: {results['volatility']:.2%}")
                    rprint(f"  • Sharpe Ratio: {results['sharpe_ratio']:.3f}")
                    rprint(f"  • Max Drawdown: {results['max_drawdown']:.2%}")

                    rprint("\n[bold]Forecast Summary:[/bold]")
                    rprint(f"  • Median Outcome: {results['forecast']['median']:.2%}")
                    rprint(
                        f"  • 95% Confidence Interval: "
                        f"[{results['forecast']['lower_95']:.2%}, "
                        f"{results['forecast']['upper_95']:.2%}]"
                    )

                    # Save results if requested
                    if output_file:
                        import json

                        with open(output_file, "w") as f:
                            json.dump(results, f, indent=2, default=str)
                        rprint(f"\n💾 Results saved to: {output_file}")

                    if save_simulations:
                        sim_path = (
                            Path("./monte_carlo_simulations") / f"{portfolio_path.stem}"
                        )
                        mc_manager.save_simulation_paths(sim_path)
                        rprint(f"📊 Simulation paths saved to: {sim_path}")

                    if visualize:
                        viz_path = mc_manager.create_visualization(results)
                        rprint(f"📊 Visualization saved to: {viz_path}")
                else:
                    rprint(f"[red]❌ Monte Carlo analysis failed[/red]")
                    raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error running Monte Carlo analysis: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def health(
    check_dependencies: bool = typer.Option(
        True, "--deps/--no-deps", help="Check system dependencies"
    ),
    check_data: bool = typer.Option(
        True, "--data/--no-data", help="Validate data directories"
    ),
    check_config: bool = typer.Option(
        True, "--config/--no-config", help="Validate configuration files"
    ),
    fix_issues: bool = typer.Option(
        False, "--fix", help="Attempt to fix identified issues"
    ),
):
    """
    Check concurrency analysis system health and validate configurations.

    This command performs comprehensive health checks on the concurrency
    analysis system, including dependencies, data integrity, and configurations.

    Examples:
        trading-cli concurrency health
        trading-cli concurrency health --fix
        trading-cli concurrency health --no-deps --data
    """
    try:
        rprint(f"[bold]Running concurrency system health checks...[/bold]\n")

        issues_found = []
        checks_passed = []

        # Check dependencies
        if check_dependencies:
            rprint("🔍 Checking dependencies...")
            try:
                import numpy
                import pandas
                import plotly
                import polars

                checks_passed.append("✅ All required dependencies installed")
            except ImportError as e:
                issues_found.append(f"❌ Missing dependency: {e.name}")

        # Check data directories
        if check_data:
            rprint("📁 Checking data directories...")
            required_dirs = [
                Path("json/concurrency"),
                Path("json/trade_history"),
                Path("csv/portfolios"),
                Path("logs"),
            ]

            for dir_path in required_dirs:
                if dir_path.exists():
                    checks_passed.append(f"✅ Directory exists: {dir_path}")
                else:
                    issues_found.append(f"❌ Missing directory: {dir_path}")
                    if fix_issues:
                        dir_path.mkdir(parents=True, exist_ok=True)
                        rprint(f"  🔧 Created directory: {dir_path}")

        # Check configuration
        if check_config:
            rprint("⚙️ Checking configuration...")
            try:
                from ...concurrency.config import validate_config
                from ...concurrency.config_defaults import get_default_config

                default_config = get_default_config()
                validate_config(default_config)
                checks_passed.append("✅ Default configuration is valid")
            except Exception as e:
                issues_found.append(f"❌ Configuration error: {e}")

            # Check for profile files
            profile_path = Path("app/cli/profiles/default_concurrency.yaml")
            if profile_path.exists():
                checks_passed.append("✅ Concurrency profile found")
            else:
                issues_found.append("❌ Missing default concurrency profile")

        # Display results
        rprint("\n[bold]Health Check Results:[/bold]")

        if checks_passed:
            rprint("\n[green]Passed Checks:[/green]")
            for check in checks_passed:
                rprint(f"  {check}")

        if issues_found:
            rprint("\n[red]Issues Found:[/red]")
            for issue in issues_found:
                rprint(f"  {issue}")
        else:
            rprint("\n[green]🎉 All health checks passed![/green]")

        # System information
        rprint("\n[bold]System Information:[/bold]")
        rprint(f"  • Python version: {sys.version.split()[0]}")

        try:
            import polars as pl

            rprint(f"  • Polars version: {pl.__version__}")
        except:
            pass

        # Exit with appropriate code
        if issues_found and not fix_issues:
            rprint(
                "\n[yellow]💡 Tip: Run with --fix to attempt automatic fixes[/yellow]"
            )
            raise typer.Exit(1)
        elif issues_found and fix_issues:
            rprint("\n[yellow]⚠️ Some issues remain after fixes[/yellow]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]Error running health check: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def demo(
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Output directory for demo results"
    ),
    strategies: int = typer.Option(
        5, "--strategies", help="Number of strategies to generate"
    ),
    run_analysis: bool = typer.Option(
        True, "--analyze/--no-analyze", help="Run full analysis after generation"
    ),
):
    """
    Run a demo analysis with sample portfolio data.

    This command generates a sample portfolio and runs concurrency analysis
    to demonstrate the system's capabilities.

    Examples:
        trading-cli concurrency demo
        trading-cli concurrency demo --strategies 10 --output ./demo_results
        trading-cli concurrency demo --no-analyze
    """
    try:
        rprint(f"[bold]Running concurrency analysis demo...[/bold]\n")

        # Set up output directory
        if output_dir is None:
            output_dir = Path("./demo_concurrency")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate demo portfolio
        rprint(f"📊 Generating demo portfolio with {strategies} strategies...")

        demo_portfolio = _generate_demo_portfolio(strategies)
        portfolio_file = output_dir / "demo_portfolio.json"

        import json

        with open(portfolio_file, "w") as f:
            json.dump(demo_portfolio, f, indent=2)

        rprint(f"✅ Demo portfolio saved to: {portfolio_file}")

        # Display portfolio summary
        rprint("\n[bold]Demo Portfolio Summary:[/bold]")
        rprint(f"  • Total strategies: {len(demo_portfolio['strategies'])}")
        rprint(
            f"  • Tickers: {', '.join(set(s['ticker'] for s in demo_portfolio['strategies']))}"
        )
        rprint(
            f"  • Strategy types: {', '.join(set(s['strategy_type'] for s in demo_portfolio['strategies']))}"
        )

        if run_analysis:
            rprint("\n🔄 Running concurrency analysis on demo portfolio...")

            # Run the analysis
            from ...concurrency.review import run_concurrency_review
            from ...tools.logging_context import logging_context

            with logging_context("cli_demo", "demo.log") as log:
                config_overrides = {
                    "VISUALIZATION": True,
                    "EXPORT_TRADE_HISTORY": True,
                    "BASE_DIR": str(output_dir),
                    "OPTIMIZE": True,
                    "OPTIMIZE_MIN_STRATEGIES": 3,
                }

                results = run_concurrency_review(str(portfolio_file), config_overrides)

                if results:
                    rprint(f"\n[green]✅ Demo analysis completed successfully![/green]")
                    rprint(f"📁 Results saved to: {output_dir}")

                    # Show key metrics
                    if "portfolio_metrics" in results:
                        metrics = results["portfolio_metrics"]
                        rprint("\n[bold]Key Metrics:[/bold]")
                        rprint(
                            f"  • Efficiency Score: "
                            f"{metrics.get('efficiency', {}).get('score', {}).get('value', 0):.3f}"
                        )
                        rprint(
                            f"  • Concurrent Ratio: "
                            f"{metrics.get('concurrency', {}).get('concurrent_ratio', {}).get('value', 0):.2%}"
                        )
                else:
                    rprint(f"[red]❌ Demo analysis failed[/red]")
        else:
            rprint(
                "\n[yellow]ℹ️ Demo portfolio generated. Run with --analyze to perform analysis.[/yellow]"
            )

    except Exception as e:
        rprint(f"[red]Error running demo: {e}[/red]")
        raise typer.Exit(1)


def _generate_demo_portfolio(n_strategies: int) -> dict:
    """Generate a demo portfolio with sample strategies."""
    import random
    from datetime import datetime

    tickers = [
        "AAPL",
        "MSFT",
        "GOOGL",
        "AMZN",
        "TSLA",
        "META",
        "NVDA",
        "BTC-USD",
        "ETH-USD",
    ]
    strategy_types = ["SMA", "EMA", "MACD"]

    strategies = []
    for i in range(n_strategies):
        ticker = random.choice(tickers)
        strategy_type = random.choice(strategy_types)

        if strategy_type in ["SMA", "EMA"]:
            short_window = random.choice([10, 20, 50])
            long_window = short_window + random.choice([20, 50, 100])
            signal_window = 0
        else:  # MACD
            short_window = 12
            long_window = 26
            signal_window = 9

        strategy = {
            "ticker": ticker,
            "strategy_type": strategy_type,
            "short_window": short_window,
            "long_window": long_window,
            "signal_window": signal_window,
            "allocation": round(100 / n_strategies, 2),
            "stop_loss": random.choice([None, 2.0, 5.0, 10.0]),
        }
        strategies.append(strategy)

    return {
        "portfolio_name": "Demo Portfolio",
        "created_at": datetime.now().isoformat(),
        "strategies": strategies,
        "metadata": {
            "description": "Automatically generated demo portfolio for testing",
            "version": "1.0",
        },
    }
