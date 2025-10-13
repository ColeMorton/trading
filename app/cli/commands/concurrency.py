"""
Concurrency command implementations.

This module provides CLI commands for concurrency analysis,
trade history export, and portfolio interaction analysis.
"""

import sys
from pathlib import Path
from typing import List, Optional

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


def resolve_portfolio_from_profile(profile_name: str, loader) -> tuple[str, str]:
    """Resolve portfolio definition from any profile type.

    Args:
        profile_name: Name of the profile to load
        loader: ConfigLoader instance

    Returns:
        tuple: (portfolio_path, resolution_type)
            portfolio_path: Path to portfolio file or definition
            resolution_type: "concurrency" | "portfolio_reference" | "portfolio_definition"
    """
    try:
        # Load the profile to check its type and configuration
        profile = loader.profile_manager.load_profile(profile_name)

        if profile.config_type == "concurrency":
            # Direct concurrency profile - use as-is
            return profile_name, "concurrency"

        elif profile.config_type == "portfolio_review":
            # Extract portfolio reference from portfolio_review profile
            config_dict = loader.profile_manager.resolve_inheritance(profile)
            portfolio_ref = config_dict.get("portfolio_reference")

            if portfolio_ref:
                # Use referenced portfolio with default concurrency config
                return portfolio_ref, "portfolio_reference"
            else:
                # Fallback to profile name as portfolio definition
                return f"{profile_name}.yaml", "portfolio_definition"

        else:
            # For other types, assume it's a portfolio name
            return f"{profile_name}.yaml", "portfolio_definition"

    except Exception as e:
        # If profile loading fails, assume it's a portfolio name
        return f"{profile_name}.yaml", "portfolio_definition"


@app.command()
def analyze(
    ctx: typer.Context,
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
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

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

        # Load configuration with smart portfolio resolution
        if profile:
            # Use smart portfolio resolution
            portfolio_path, resolution_type = resolve_portfolio_from_profile(
                profile, loader
            )

            if resolution_type == "concurrency":
                # Direct concurrency profile - use as-is
                config = loader.load_from_profile(profile, ConcurrencyConfig, overrides)
            elif resolution_type in ["portfolio_reference", "portfolio_definition"]:
                # Portfolio definition or reference - use default concurrency config with portfolio override
                # Add portfolio path to overrides
                if "general" not in overrides:
                    overrides["general"] = {}
                # Extract filename from full path for portfolio field
                from pathlib import Path as PathClass

                portfolio_filename = PathClass(portfolio_path).name
                overrides["general"]["portfolio"] = portfolio_filename

                config = loader.load_from_profile(
                    "default_concurrency", ConcurrencyConfig, overrides
                )

                rprint(
                    f"[dim]Using portfolio definition: {portfolio_path} (resolved from profile '{profile}')[/dim]"
                )
            else:
                # Fallback to direct profile loading
                config = loader.load_from_profile(profile, ConcurrencyConfig, overrides)
        else:
            config = loader.load_from_profile(
                "default_concurrency", ConcurrencyConfig, overrides
            )

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

        if global_verbose:
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
                # Add missing optimization settings with safe attribute access
                "OPTIMIZE": getattr(
                    getattr(config, "optimization", None), "enable_optimization", False
                ),
                "OPTIMIZE_MIN_STRATEGIES": getattr(
                    getattr(config, "optimization", None), "min_strategies", 3
                ),
                "OPTIMIZE_MAX_PERMUTATIONS": getattr(
                    getattr(config, "optimization", None), "max_permutations", 1000
                ),
                "OPTIMIZE_PARALLEL_PROCESSING": getattr(
                    getattr(config, "optimization", None), "parallel_processing", False
                ),
                "OPTIMIZE_MAX_WORKERS": getattr(
                    getattr(config, "optimization", None), "max_workers", 4
                ),
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
        if global_verbose:
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


def _display_portfolio_size_comparison(size_results: dict, best_size: int) -> None:
    """Display side-by-side comparison of portfolio size metrics.

    Args:
        size_results: Dictionary mapping portfolio size to metrics
        best_size: The portfolio size with the best efficiency score
    """
    if not size_results:
        return

    # Create comparison table
    comparison_table = Table(
        title="📊 Portfolio Size Analysis Results", show_header=True
    )
    comparison_table.add_column("Portfolio\nSize", style="cyan", justify="center")
    comparison_table.add_column("Efficiency\nScore", style="green", justify="right")
    comparison_table.add_column("Diversification", style="yellow", justify="right")
    comparison_table.add_column("Independence", style="blue", justify="right")
    comparison_table.add_column("Activity", style="magenta", justify="right")
    comparison_table.add_column("Avg\nExpectancy", style="bright_cyan", justify="right")
    comparison_table.add_column("Risk\nConcentration", style="red", justify="right")

    # Add rows for each tested size
    for size in sorted(size_results.keys()):
        metrics = size_results[size]

        # Determine if this is the best size
        is_best = size == best_size
        marker = " 🏆" if is_best else ""

        # Format size with marker
        size_str = f"{size} strategies{marker}"

        comparison_table.add_row(
            size_str,
            f"{metrics['efficiency_score']:.4f}",
            f"{metrics['diversification_multiplier']:.3f}",
            f"{metrics['independence_multiplier']:.3f}",
            f"{metrics['activity_multiplier']:.3f}",
            f"{metrics['average_expectancy']:.3f}",
            f"{metrics['risk_concentration_index']:.3f}",
        )

    console.print(comparison_table)

    # Show improvement summary if multiple sizes tested
    if len(size_results) > 1:
        sizes = sorted(size_results.keys())
        baseline_efficiency = size_results[sizes[0]]["efficiency_score"]
        best_efficiency = size_results[best_size]["efficiency_score"]
        improvement_pct = (
            ((best_efficiency - baseline_efficiency) / baseline_efficiency) * 100
            if baseline_efficiency > 0
            else 0
        )

        rprint(
            f"\n[dim]Best: {best_size}-strategy portfolio (+{improvement_pct:+.1f}% efficiency vs {sizes[0]}-strategy)[/dim]\n"
        )


def _display_all_portfolio_compositions(size_results: dict, best_size: int) -> None:
    """Display detailed strategy composition for each tested portfolio size.

    Args:
        size_results: Dictionary mapping portfolio size to metrics and strategies
        best_size: The portfolio size with the best efficiency score
    """
    if not size_results:
        return

    rprint("[bold cyan]📋 Detailed Portfolio Compositions[/bold cyan]\n")

    for size in sorted(size_results.keys()):
        metrics = size_results[size]
        strategies = metrics.get("strategies", [])

        if not strategies:
            continue

        # Determine if this is the best size
        is_best = size == best_size
        marker = " 🏆" if is_best else ""

        # Create table for this portfolio size
        rprint(f"[bold]{size}-Strategy Portfolio{marker}[/bold]")
        rprint(f"[dim]Efficiency Score: {metrics['efficiency_score']:.4f}[/dim]")

        strategy_table = Table(show_header=True, title=None)
        strategy_table.add_column("#", style="white", justify="right")
        strategy_table.add_column("Strategy ID", style="cyan")
        strategy_table.add_column("Score", style="green", justify="right")
        strategy_table.add_column("Sharpe", style="yellow", justify="right")

        for i, strategy in enumerate(strategies[:size], 1):
            strategy_table.add_row(
                str(i),
                strategy["strategy_id"],
                f"{strategy['score']:.2f}",
                f"{strategy['sharpe_ratio']:.3f}",
            )

        console.print(strategy_table)
        rprint("")  # Blank line between tables


def _calculate_strategy_diversification_scores(strategies: list) -> dict:
    """Calculate diversification score for each strategy based on type variety and parameter dissimilarity.

    Higher scores indicate strategies that contribute more to portfolio diversification through:
    - Rare strategy types (less common in the universe)
    - Dissimilar parameter values (different from other strategies)

    Args:
        strategies: List of strategy dictionaries with strategy_id, strategy_type, fast_period, slow_period

    Returns:
        dict: Mapping of strategy_id to diversification_multiplier (1.0-2.0)
    """
    if not strategies:
        return {}

    diversification_scores = {}

    # Count strategy types for rarity calculation
    type_counts = {}
    for s in strategies:
        type_counts[s["strategy_type"]] = type_counts.get(s["strategy_type"], 0) + 1

    for strategy in strategies:
        # Base score starts at 1.0 (neutral)
        div_score = 1.0

        # Bonus for strategy type variety (up to +0.5)
        strategy_type = strategy["strategy_type"]
        # Less common types get higher bonus
        type_rarity = 1.0 - (type_counts[strategy_type] / len(strategies))
        div_score += 0.5 * type_rarity

        # Bonus for parameter dissimilarity (up to +0.5)
        fast = strategy["fast_period"]
        slow = strategy["slow_period"]

        # Calculate average parameter distance from other strategies
        param_distances = []
        for s in strategies:
            if s["strategy_id"] != strategy["strategy_id"]:
                # Euclidean distance in parameter space
                dist = (
                    (s["fast_period"] - fast) ** 2 + (s["slow_period"] - slow) ** 2
                ) ** 0.5
                param_distances.append(dist)

        if param_distances:
            avg_distance = sum(param_distances) / len(param_distances)
            # Normalize to 0-0.5 range (assuming typical max distance of ~100)
            # Use sigmoid-like function for smooth scaling
            param_bonus = 0.5 * (1 - (1 / (1 + avg_distance / 50)))
            div_score += param_bonus

        diversification_scores[strategy["strategy_id"]] = div_score

    return diversification_scores


def _select_diversified_portfolio(
    strategies: list,
    diversification_scores: dict,
    target_size: int,
    verbose: bool = False,
) -> list:
    """Select portfolio with enforced strategy type diversity via stratified sampling.

    Implements hard diversity constraints to ensure robust strategy type representation:
    - If 3+ types available: minimum 1 from each type
    - If 2 types available: minimum 30% allocation to minority type
    - Within each type: select best strategies by (score × diversification_multiplier)

    This prevents regime risk concentration from over-representing a single strategy type.

    Args:
        strategies: List of strategy dictionaries sorted by weighted score
        diversification_scores: Dict mapping strategy_id to diversification multiplier
        target_size: Target portfolio size (5, 7, or 9)
        verbose: Enable detailed logging

    Returns:
        List of selected strategies with enforced diversity
    """
    if not strategies or target_size <= 0:
        return []

    if len(strategies) <= target_size:
        return strategies

    # Group strategies by type (strata)
    strata = {}
    for strategy in strategies:
        stype = strategy["strategy_type"]
        strata.setdefault(stype, []).append(strategy)

    n_types = len(strata)

    if verbose:
        rprint(f"[dim]Stratified selection: {n_types} strategy types available[/dim]")
        for stype, candidates in strata.items():
            rprint(f"[dim]  {stype}: {len(candidates)} candidates[/dim]")

    # Case 1: Single strategy type - no diversity possible
    if n_types == 1:
        if verbose:
            rprint(
                f"[yellow]⚠️ Only one strategy type available - diversity constraints cannot be applied[/yellow]"
            )
        return strategies[:target_size]

    # Case 2: Two strategy types - enforce minimum 30% minority representation
    if n_types == 2:
        types_list = list(strata.keys())
        type1, type2 = types_list[0], types_list[1]

        # Sort each type by weighted score
        for stype in strata:
            strata[stype] = sorted(
                strata[stype],
                key=lambda x: x["score"]
                * diversification_scores.get(x["strategy_id"], 1.0),
                reverse=True,
            )

        # Determine majority and minority types
        if len(strata[type1]) >= len(strata[type2]):
            majority_type, minority_type = type1, type2
        else:
            majority_type, minority_type = type2, type1

        # Enforce minimum 30% allocation to minority type
        min_minority = max(1, int(target_size * 0.3))
        max_majority = target_size - min_minority

        # Select strategies
        portfolio = []
        portfolio.extend(strata[minority_type][:min_minority])
        portfolio.extend(strata[majority_type][:max_majority])

        if verbose:
            rprint(
                f"[green]✓ Diversity enforced: {len(strata[minority_type][:min_minority])} {minority_type} + {len(strata[majority_type][:max_majority])} {majority_type}[/green]"
            )

        return portfolio[:target_size]

    # Case 3: Three or more types - guarantee at least 1 from each type
    if n_types >= 3:
        # Sort each stratum by weighted score
        for stype in strata:
            strata[stype] = sorted(
                strata[stype],
                key=lambda x: x["score"]
                * diversification_scores.get(x["strategy_id"], 1.0),
                reverse=True,
            )

        portfolio = []
        remaining_slots = target_size

        # Round 1: Select best strategy from each type (mandatory diversity)
        mandatory_selections = {}
        for stype in sorted(strata.keys()):
            if strata[stype]:
                best_strategy = strata[stype][0]
                portfolio.append(best_strategy)
                mandatory_selections[stype] = best_strategy["strategy_id"]
                remaining_slots -= 1

                if verbose:
                    div_score = diversification_scores.get(
                        best_strategy["strategy_id"], 1.0
                    )
                    weighted = best_strategy["score"] * div_score
                    rprint(
                        f"[dim]  Round 1: {stype} → {best_strategy['strategy_id']} (weighted: {weighted:.3f})[/dim]"
                    )

        # Round 2: Fill remaining slots from all types by weighted score
        if remaining_slots > 0:
            # Collect all non-selected strategies
            remaining_candidates = []
            for stype, candidates in strata.items():
                for strategy in candidates:
                    # Skip strategies already selected in round 1
                    if strategy["strategy_id"] not in mandatory_selections.values():
                        remaining_candidates.append(strategy)

            # Sort by weighted score
            remaining_candidates = sorted(
                remaining_candidates,
                key=lambda x: x["score"]
                * diversification_scores.get(x["strategy_id"], 1.0),
                reverse=True,
            )

            # Add top remaining candidates
            additional_selections = remaining_candidates[:remaining_slots]
            portfolio.extend(additional_selections)

            if verbose:
                rprint(
                    f"[dim]  Round 2: Added {len(additional_selections)} strategies by weighted score[/dim]"
                )

        # Display final type distribution
        if verbose:
            final_type_counts = {}
            for s in portfolio:
                stype = s["strategy_type"]
                final_type_counts[stype] = final_type_counts.get(stype, 0) + 1

            rprint(f"[green]✓ Final portfolio diversity:[/green]")
            for stype, count in sorted(final_type_counts.items()):
                pct = (count / len(portfolio)) * 100
                rprint(f"[green]    {stype}: {count} ({pct:.1f}%)[/green]")

        return portfolio[:target_size]

    # Fallback (should never reach here)
    return strategies[:target_size]


def _export_strategies_to_file(
    asset: str, strategies: list, force_overwrite: bool = False
) -> None:
    """Export strategies to data/raw/strategies/{asset}.csv.

    Args:
        asset: Asset symbol (e.g., 'PLTR', 'NVDA')
        strategies: List of strategy dictionaries with ticker, strategy_type, fast_period, slow_period
        force_overwrite: If True, overwrite existing file. If False, skip if file exists.
    """
    import pandas as pd

    export_path = Path(f"data/raw/strategies/{asset}.csv")

    # Check overwrite conditions
    if export_path.exists() and not force_overwrite:
        rprint(
            f"[dim]Export skipped: {export_path} already exists (use --export to overwrite)[/dim]"
        )
        return

    # Load strategy data from filtered files
    combined_rows = []
    for strategy in strategies:
        ticker = strategy["ticker"]
        strat_type = strategy["strategy_type"]
        fast = strategy["fast_period"]
        slow = strategy["slow_period"]

        # Read from filtered file
        source_file = Path(f"data/raw/portfolios_filtered/{ticker}_D_{strat_type}.csv")

        if not source_file.exists():
            rprint(f"[yellow]⚠️ Source file not found: {source_file}[/yellow]")
            continue

        try:
            df = pd.read_csv(source_file)

            # Filter to matching strategy
            matching = df[
                (df["Ticker"] == ticker)
                & (df["Strategy Type"] == strat_type)
                & (df["Fast Period"] == fast)
                & (df["Slow Period"] == slow)
            ]

            if not matching.empty:
                combined_rows.append(matching.iloc[0])
            else:
                rprint(
                    f"[yellow]⚠️ Strategy not found in {source_file.name}: {ticker}_{strat_type}_{fast}_{slow}[/yellow]"
                )
        except Exception as e:
            rprint(f"[red]❌ Error reading {source_file}: {e}[/red]")
            continue

    # Combine and export
    if combined_rows:
        result_df = pd.DataFrame(combined_rows)

        # Ensure directory exists
        export_path.parent.mkdir(parents=True, exist_ok=True)

        result_df.to_csv(export_path, index=False)
        rprint(
            f"[green]✓ Exported {len(combined_rows)} strategies to: {export_path}[/green]"
        )
    else:
        rprint(f"[red]❌ No strategies found to export[/red]")


@app.command()
def construct(
    asset: Optional[str] = typer.Argument(
        None,
        help="Asset symbol (e.g., MSFT, NVDA, BTC-USD) - omit when using -t/-t1/-t2",
    ),
    ticker: Optional[List[str]] = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Ticker symbol(s) to construct portfolios for (multiple args or comma-separated: -t AAPL,MSFT or -t AAPL -t MSFT). Overrides ASSET if both provided.",
    ),
    ticker_1: Optional[str] = typer.Option(
        None, "--ticker-1", "-t1", help="First ticker for synthetic pair analysis"
    ),
    ticker_2: Optional[str] = typer.Option(
        None,
        "--ticker-2",
        "-t2",
        help="Second ticker for synthetic pair analysis (automatically enables synthetic mode)",
    ),
    min_score: float = typer.Option(
        1.0, "--min-score", help="Minimum Score threshold for strategy inclusion"
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile to use"
    ),
    output_format: str = typer.Option(
        "table", "--format", help="Output format: table, json, csv"
    ),
    save_portfolio: Optional[str] = typer.Option(
        None, "--save", help="Save optimal portfolio to file"
    ),
    export: bool = typer.Option(
        False,
        "--export",
        "-e",
        help="Export strategies to data/raw/strategies/{TICKER}.csv (overwrites if exists)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """Construct optimal portfolio from asset strategy universe.

    Auto-discovers strategy files for the given asset and constructs the optimal
    portfolio (5, 7, or 9 strategies) with the highest efficiency_score.

    Examples:
        trading-cli concurrency construct MSFT
        trading-cli concurrency construct -t MSFT
        trading-cli concurrency construct -t HIMS,NVDA,SMR,PLTR --export
        trading-cli concurrency construct -t HIMS -t NVDA -t SMR --export
        trading-cli concurrency construct -t1 NVDA -t2 QQQ --verbose
        trading-cli concurrency construct -t1 BTC-USD -t2 ETH-USD --min-score 1.5
    """
    import json
    import os
    import tempfile

    from app.concurrency.tools.asset_strategy_loader import AssetStrategyLoader

    from ...concurrency.review import run_concurrency_review
    from .strategy_utils import process_ticker_input

    # Initialize loader
    loader = AssetStrategyLoader()

    try:
        # Resolve asset name - priority order:
        # 1. Synthetic mode: ticker_2 + ticker_1 (highest priority)
        # 2. Ticker flag: -t / --ticker (overrides asset)
        # 3. Direct asset argument (fallback)

        if ticker_2 is not None:
            # Synthetic mode: ticker_1 + ticker_2
            if ticker_1 is None:
                rprint(
                    "[red]❌ Error: -t1 is required when using -t2 for synthetic pairs[/red]"
                )
                raise typer.Exit(1)

            asset_names = [f"{ticker_1}_{ticker_2}"]
            is_synthetic = True
            rprint(
                f"[bold]Constructing synthetic pair portfolio: {asset_names[0]}[/bold]"
            )
        elif ticker_1 is not None:
            # Single ticker mode via -t1 flag
            asset_names = [ticker_1]
            is_synthetic = False
            rprint(f"[bold]Constructing optimal portfolio for {asset_names[0]}[/bold]")
        elif ticker is not None:
            # Process ticker input (handles comma-separated and multiple args)
            asset_names = process_ticker_input(ticker)
            is_synthetic = False

            if not asset_names:
                rprint("[red]❌ Error: No valid tickers provided via -t flag[/red]")
                raise typer.Exit(1)

            if len(asset_names) == 1:
                rprint(
                    f"[bold]Constructing optimal portfolio for {asset_names[0]}[/bold]"
                )
            else:
                rprint(
                    f"[bold]Constructing optimal portfolios for {len(asset_names)} tickers: {', '.join(asset_names)}[/bold]"
                )
        elif asset is not None:
            # Direct asset argument
            asset_names = [asset]
            is_synthetic = False
            rprint(f"[bold]Constructing optimal portfolio for {asset_names[0]}[/bold]")
        else:
            rprint(
                "[red]❌ Error: Must specify either ASSET argument or use -t/-t1/-t2 flags[/red]"
            )
            rprint("[dim]Examples:[/dim]")
            rprint("[dim]  Single asset: trading-cli concurrency construct NVDA[/dim]")
            rprint(
                "[dim]  Multiple tickers: trading-cli concurrency construct -t HIMS,NVDA,SMR --export[/dim]"
            )
            rprint(
                "[dim]  Synthetic pair: trading-cli concurrency construct -t1 NVDA -t2 QQQ[/dim]"
            )
            raise typer.Exit(1)

        # Track results for multiple tickers
        all_results = []

        # Process each ticker
        for ticker_idx, asset_name in enumerate(asset_names, 1):
            # Show progress for multiple tickers
            if len(asset_names) > 1:
                rprint(f"\n[bold cyan]{'='*60}[/bold cyan]")
                rprint(
                    f"[bold cyan]Processing ticker {ticker_idx}/{len(asset_names)}: {asset_name}[/bold cyan]"
                )
                rprint(f"[bold cyan]{'='*60}[/bold cyan]\n")

            # Validate asset feasibility
            rprint(f"[dim]Filtering criteria: Score >= {min_score}[/dim]")

            feasibility = loader.validate_asset_data(asset_name)

            if not feasibility.get("viable_for_construction", False):
                if "error" in feasibility:
                    rprint(f"[red]❌ Error: {feasibility['error']}[/red]")
                else:
                    rprint(
                        f"[red]❌ Error: Insufficient strategies for portfolio construction[/red]"
                    )
                    rprint(
                        f"Available strategies with Score >= {min_score}: {feasibility.get('score_filtered_strategies', 0)}"
                    )
                    rprint(f"Need at least 5 strategies for portfolio construction")

                # For multiple tickers, continue to next ticker; for single ticker, exit
                if len(asset_names) > 1:
                    rprint(
                        f"[yellow]⚠️ Skipping {asset_name}, continuing with remaining tickers...[/yellow]"
                    )
                    continue
                else:
                    raise typer.Exit(1)

            rprint(f"[green]✓ Feasibility check passed[/green]")
            rprint(f"Available strategies: {feasibility['score_filtered_strategies']}")

            # Load strategies and create temporary portfolio file
            strategies = loader.load_strategies_for_asset(
                asset_name, min_score=min_score
            )

            # Calculate diversification scores for strategy selection
            rprint(f"[dim]Calculating diversification-weighted scores...[/dim]")
            diversification_scores = _calculate_strategy_diversification_scores(
                strategies
            )

            # Sort strategies by score * diversification_multiplier (descending)
            # This prioritizes strategies with high performance AND high diversification contribution
            strategies = sorted(
                strategies,
                key=lambda x: x["score"]
                * diversification_scores.get(x["strategy_id"], 1.0),
                reverse=True,
            )

            if verbose:
                rprint(
                    f"[dim]Loaded {len(strategies)} strategies, sorted by score × diversification (highest first)[/dim]"
                )
                if strategies:
                    top_strat = strategies[0]
                    top_div = diversification_scores.get(top_strat["strategy_id"], 1.0)
                    rprint(
                        f"[dim]Top strategy: {top_strat['strategy_id']} (Score: {top_strat['score']:.3f}, Div: {top_div:.3f}, Weighted: {top_strat['score'] * top_div:.3f})[/dim]"
                    )
                    if len(strategies) >= 5:
                        rprint(f"[dim]Top 5 strategies by weighted score:[/dim]")
                        for i, s in enumerate(strategies[:5], 1):
                            div = diversification_scores.get(s["strategy_id"], 1.0)
                            weighted = s["score"] * div
                            rprint(
                                f"[dim]  {i}. {s['strategy_id']}: Score={s['score']:.3f}, Div={div:.3f}, Weighted={weighted:.3f}[/dim]"
                            )

                        # Show type distribution
                        rprint(f"[dim]Strategy type distribution in top 10:[/dim]")
                        type_counts = {}
                        for s in strategies[:10]:
                            stype = s["strategy_type"]
                            type_counts[stype] = type_counts.get(stype, 0) + 1
                        for stype, count in sorted(type_counts.items()):
                            rprint(f"[dim]  {stype}: {count}[/dim]")

            # Optimization: If we have exactly 5, 7, or 9 strategies, note exact match
            # but still run optimization to calculate efficiency_score
            is_exact_match = len(strategies) in [5, 7, 9]
            if is_exact_match:
                rprint(
                    f"[green]✓ Exact match: {len(strategies)} strategies available[/green]"
                )
                rprint(
                    f"[dim]Running optimization to calculate efficiency metrics...[/dim]"
                )

            # Prepare JSON portfolios directory
            import uuid

            json_portfolios_dir = Path.cwd() / "json" / "portfolios"
            json_portfolios_dir.mkdir(parents=True, exist_ok=True)

            try:
                # Test portfolio sizes 5, 7, 9 and find best efficiency_score
                best_result = None
                best_score = -1
                best_size = None
                size_results = {}  # Track comprehensive metrics for each size
                temp_files_to_cleanup = []  # Track all temp files for cleanup

                # Determine which sizes to test
                # If exact match, only test that single size, otherwise test all viable sizes
                sizes_to_test = [len(strategies)] if is_exact_match else [5, 7, 9]

                for size in sizes_to_test:
                    if len(strategies) >= size:
                        if is_exact_match:
                            rprint(
                                f"[bold]Calculating efficiency metrics for {size} strategies[/bold]"
                            )
                            rprint(
                                f"[dim]Running concurrency analysis (this may take 15-30 seconds)...[/dim]"
                            )
                        else:
                            rprint(f"[bold]Testing portfolio size: {size}[/bold]")
                            rprint(
                                f"[dim]Analyzing {size}-strategy combinations (this may take 30-90 seconds)...[/dim]"
                            )

                        # ===== STRATIFIED SELECTION: Apply diversity constraints =====
                        # Select strategies using stratified sampling for type diversity
                        selected_strategies = _select_diversified_portfolio(
                            strategies=strategies,
                            diversification_scores=diversification_scores,
                            target_size=size,
                            verbose=verbose,
                        )

                        # Convert selected strategies to portfolio format
                        size_portfolio_data = []
                        for strategy in selected_strategies:
                            strategy_dict = {
                                "strategy_id": strategy["strategy_id"],
                                "ticker": strategy["ticker"],
                                "strategy_type": strategy["strategy_type"],
                                "fast_period": strategy["fast_period"],
                                "slow_period": strategy["slow_period"],
                                "allocation": strategy["allocation"],
                                # Add PORTFOLIO_STATS dict to match CSV structure
                                "PORTFOLIO_STATS": {
                                    "Score": strategy["score"],
                                    "Expectancy per Trade": strategy[
                                        "expectancy_per_trade"
                                    ],
                                    "Win Rate [%]": strategy["win_rate"],
                                    "Profit Factor": strategy["profit_factor"],
                                    "Sharpe Ratio": strategy["sharpe_ratio"],
                                    "Total Return [%]": strategy["total_return"],
                                    "Max Drawdown [%]": strategy["max_drawdown"],
                                },
                            }

                            # Add signal_period for MACD strategies if present
                            if (
                                "signal_period" in strategy
                                and strategy["signal_period"] is not None
                            ):
                                strategy_dict["signal_period"] = strategy[
                                    "signal_period"
                                ]

                            size_portfolio_data.append(strategy_dict)

                        # Create temporary portfolio file for THIS SIZE
                        size_temp_filename = (
                            f"construct_temp_{uuid.uuid4().hex[:8]}_size{size}.json"
                        )
                        size_temp_path = json_portfolios_dir / size_temp_filename

                        with open(size_temp_path, "w") as temp_file:
                            json.dump(size_portfolio_data, temp_file, indent=2)

                        temp_files_to_cleanup.append(size_temp_path)

                        if verbose:
                            rprint(
                                f"[dim]Created size-specific temp file: {size_temp_filename} with {len(size_portfolio_data)} strategies[/dim]"
                            )
                        # ===== END BUG FIX =====

                        # Run direct concurrency analysis (no optimization)
                        config_overrides = {
                            "PORTFOLIO": size_temp_filename,  # Use size-specific filename
                            "OPTIMIZE": False,  # Use direct analysis path for consistency with analyze command
                            "VISUALIZATION": False,
                            "PARALLEL_PROCESSING": False,
                            "REFRESH": False,  # Use cached data for performance
                            # Performance optimizations for construct command
                            "MC_INCLUDE_IN_REPORTS": False,  # Disable Monte Carlo (major speedup)
                            "REPORT_INCLUDES": {  # Minimal reporting
                                "TICKER_METRICS": False,
                                "STRATEGIES": False,
                                "STRATEGY_RELATIONSHIPS": False,
                                "ALLOCATION": False,
                            },
                        }

                        # Run direct analysis on THIS SIZE
                        success = run_concurrency_review(
                            size_temp_filename, config_overrides=config_overrides
                        )

                        if success:
                            # Load results from regular JSON report file
                            import json

                            report_file = (
                                Path.cwd()
                                / "json"
                                / "concurrency"
                                / f"{size_temp_filename.replace('.json', '')}.json"
                            )

                            efficiency_score = 0.0
                            metrics_loaded = False

                            if report_file.exists():
                                try:
                                    with open(report_file, "r") as f:
                                        report_data = json.load(f)

                                    # Extract metrics from nested report structure
                                    portfolio_metrics = report_data.get(
                                        "portfolio_metrics", {}
                                    )
                                    efficiency_metrics = portfolio_metrics.get(
                                        "efficiency", {}
                                    )
                                    risk_metrics = portfolio_metrics.get(
                                        "risk", {}
                                    ).get("portfolio_metrics", {})

                                    # Extract efficiency score and multipliers from nested structure
                                    efficiency_score = efficiency_metrics.get(
                                        "efficiency_score", {}
                                    ).get("value", 0.0)
                                    diversification = (
                                        efficiency_metrics.get("multipliers", {})
                                        .get("diversification", {})
                                        .get("value", 0.0)
                                    )
                                    independence = (
                                        efficiency_metrics.get("multipliers", {})
                                        .get("independence", {})
                                        .get("value", 0.0)
                                    )
                                    activity = (
                                        efficiency_metrics.get("multipliers", {})
                                        .get("activity", {})
                                        .get("value", 0.0)
                                    )
                                    total_expectancy = efficiency_metrics.get(
                                        "expectancy", {}
                                    ).get("value", 0.0)
                                    average_expectancy = (
                                        total_expectancy / size if size > 0 else 0.0
                                    )
                                    risk_concentration = risk_metrics.get(
                                        "risk_concentration_index", {}
                                    ).get("value", 0.0)

                                    metrics_loaded = True

                                    # Store comprehensive metrics for this size
                                    size_results[size] = {
                                        "efficiency_score": efficiency_score,
                                        "diversification_multiplier": diversification,
                                        "independence_multiplier": independence,
                                        "activity_multiplier": activity,
                                        "total_expectancy": total_expectancy,
                                        "average_expectancy": average_expectancy,
                                        "weighted_efficiency": efficiency_score,  # Use efficiency_score as weighted_efficiency
                                        "risk_concentration_index": risk_concentration,
                                        "strategies": selected_strategies,  # Include selected strategy list for detailed display
                                    }

                                    if verbose:
                                        rprint(
                                            f"[dim]✓ Loaded metrics from: {report_file.name}[/dim]"
                                        )
                                        rprint(
                                            f"[dim]   Efficiency: {efficiency_score:.4f}, Div: {diversification:.3f}, Ind: {independence:.3f}, Activity: {activity:.3f}[/dim]"
                                        )

                                except Exception as e:
                                    rprint(
                                        f"[yellow]⚠️ Could not load analysis results: {e}[/yellow]"
                                    )
                                    if verbose:
                                        import traceback

                                        rprint(f"[dim]{traceback.format_exc()}[/dim]")
                            else:
                                rprint(
                                    f"[yellow]⚠️ Analysis report not generated: {report_file.name}[/yellow]"
                                )
                                if verbose:
                                    rprint(
                                        f"[dim]   Expected location: {report_file}[/dim]"
                                    )
                                    rprint(
                                        f"[dim]   Checking if directory exists: {report_file.parent.exists()}[/dim]"
                                    )

                            # Only use this result if metrics were successfully loaded
                            if metrics_loaded and efficiency_score > best_score:
                                best_score = efficiency_score
                                best_size = size
                                best_result = {
                                    "size": size,
                                    "efficiency_score": efficiency_score,
                                    "strategies": selected_strategies,  # Diversified strategy selection
                                }
                            elif not metrics_loaded:
                                # If no metrics loaded, still create a result but mark it
                                rprint(
                                    f"[dim]   Using fallback: Will display portfolio without efficiency metrics[/dim]"
                                )
                                if best_result is None:
                                    # Create a basic result without metrics
                                    best_result = {
                                        "size": size,
                                        "efficiency_score": None,  # Explicitly None to distinguish from 0.0
                                        "strategies": selected_strategies,
                                    }

                if best_result:
                    # Display portfolio size comparison if multiple sizes were tested
                    if len(size_results) > 1:
                        rprint("")  # Blank line for spacing
                        _display_portfolio_size_comparison(size_results, best_size)

                        # Display detailed strategy compositions for all portfolio sizes
                        _display_all_portfolio_compositions(size_results, best_size)

                    # Display results
                    rprint(f"[bold green]🏆 Optimal Portfolio Constructed[/bold green]")
                    rprint(f"Asset: {asset_name}")
                    rprint(f"Portfolio Size: {best_result['size']} strategies")

                    # Handle efficiency score display - None means metrics weren't generated
                    if best_result["efficiency_score"] is not None:
                        rprint(
                            f"Efficiency Score: {best_result['efficiency_score']:.4f}"
                        )
                    else:
                        rprint(
                            f"Efficiency Score: [yellow]N/A (optimization metrics not generated)[/yellow]"
                        )

                    rprint(f"Total Strategies Evaluated: {len(strategies)}")

                    # Display strategy composition (simplified)
                    # Note: If multiple sizes were tested, detailed tables are already shown above
                    if output_format == "table":
                        # Skip duplicate table if already displayed above
                        if len(size_results) <= 1:
                            # Only show table if single size (no comparison was done)
                            strategy_table = Table(show_header=True)
                            strategy_table.add_column(
                                "#", style="white", justify="right"
                            )
                            strategy_table.add_column("Strategy ID", style="cyan")
                            strategy_table.add_column(
                                "Score", style="green", justify="right"
                            )
                            strategy_table.add_column(
                                "Sharpe", style="yellow", justify="right"
                            )

                            for i, strategy in enumerate(
                                best_result["strategies"][: best_result["size"]], 1
                            ):
                                strategy_table.add_row(
                                    str(i),
                                    strategy["strategy_id"],
                                    f"{strategy['score']:.2f}",
                                    f"{strategy['sharpe_ratio']:.3f}",
                                )
                            console.print(strategy_table)

                    elif output_format == "json":
                        result_json = {
                            "asset": asset_name,
                            "optimal_size": best_result["size"],
                            "efficiency_score": best_result["efficiency_score"],
                            "strategies": [
                                {
                                    "strategy_id": s["strategy_id"],
                                    "score": s["score"],
                                    "sharpe_ratio": s["sharpe_ratio"],
                                }
                                for s in best_result["strategies"][
                                    : best_result["size"]
                                ]
                            ],
                        }
                        rprint(json.dumps(result_json, indent=2))

                    # Export strategies if requested or if file doesn't exist
                    if export or (
                        not Path(f"data/raw/strategies/{asset_name}.csv").exists()
                    ):
                        _export_strategies_to_file(
                            asset_name,
                            best_result["strategies"][: best_result["size"]],
                            force_overwrite=export,
                        )

                    # Store result for this ticker
                    all_results.append(
                        {
                            "asset": asset_name,
                            "success": True,
                            "portfolio_size": best_result["size"],
                            "efficiency_score": best_result["efficiency_score"],
                            "strategies_evaluated": len(strategies),
                        }
                    )

                else:
                    rprint(
                        f"[red]❌ Failed to construct viable portfolio for {asset_name}[/red]"
                    )
                    all_results.append(
                        {
                            "asset": asset_name,
                            "success": False,
                            "error": "Failed to construct viable portfolio",
                        }
                    )

                    # For single ticker, exit immediately; for multiple, continue
                    if len(asset_names) == 1:
                        raise typer.Exit(1)

            finally:
                # Clean up ALL temporary files
                for temp_file in temp_files_to_cleanup:
                    if temp_file.exists():
                        temp_file.unlink()
                        if verbose:
                            rprint(f"[dim]Cleaned up: {temp_file.name}[/dim]")

        # Display summary for multiple tickers
        if len(asset_names) > 1:
            rprint(f"\n[bold cyan]{'='*60}[/bold cyan]")
            rprint(
                f"[bold cyan]Summary: Processed {len(asset_names)} Tickers[/bold cyan]"
            )
            rprint(f"[bold cyan]{'='*60}[/bold cyan]\n")

            successful = [r for r in all_results if r["success"]]
            failed = [r for r in all_results if not r["success"]]

            if successful:
                rprint(
                    f"[green]✓ Successfully constructed {len(successful)} portfolios:[/green]"
                )
                for result in successful:
                    efficiency_display = (
                        f"{result['efficiency_score']:.4f}"
                        if result["efficiency_score"] is not None
                        else "N/A"
                    )
                    rprint(
                        f"  • {result['asset']}: {result['portfolio_size']} strategies (Efficiency: {efficiency_display})"
                    )

            if failed:
                rprint(f"\n[red]✗ Failed to construct {len(failed)} portfolios:[/red]")
                for result in failed:
                    rprint(
                        f"  • {result['asset']}: {result.get('error', 'Unknown error')}"
                    )

            rprint(
                f"\n[bold]Overall Success Rate: {len(successful)}/{len(asset_names)} ({len(successful)/len(asset_names)*100:.1f}%)[/bold]"
            )

    except Exception as e:
        rprint(f"[red]❌ Construction failed: {e}[/red]")
        if verbose:
            import traceback

            rprint(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def optimize(
    ctx: typer.Context,
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
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

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
        if global_verbose:
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
                Path("data/raw/reports/concurrency"),
                Path("data/raw/reports/trade_history"),
                Path("data/raw/strategies"),
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
    strategy_types = ["SMA", "EMA", "MACD", "ATR"]

    strategies = []
    for i in range(n_strategies):
        ticker = random.choice(tickers)
        strategy_type = random.choice(strategy_types)

        if strategy_type in ["SMA", "EMA"]:
            fast_period = random.choice([10, 20, 50])
            slow_period = fast_period + random.choice([20, 50, 100])
            signal_period = 0
        elif strategy_type == "MACD":
            fast_period = 12
            slow_period = 26
            signal_period = 9
        else:  # ATR
            fast_period = random.choice([5, 10, 14, 20])  # ATR length
            slow_period = (
                random.choice([15, 20, 25, 30]) * 10
            )  # ATR multiplier * 10 for int representation
            signal_period = 0

        strategy = {
            "ticker": ticker,
            "strategy_type": strategy_type,
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_period": signal_period,
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
