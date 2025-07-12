"""Statistical Performance Divergence System (SPDS) command implementations.

This module provides CLI commands for comprehensive portfolio statistical analysis,
exit signal generation, and backtesting parameter export.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import ConfigLoader
from ..models.spds import SPDSConfig
from ..utils import resolve_portfolio_path

# Create SPDS sub-app
app = typer.Typer(
    name="spds",
    help="Statistical Performance Divergence System - Portfolio Analysis",
    no_args_is_help=True,
)

console = Console()


def _detect_available_data_sources(portfolio: str) -> dict:
    """
    Detect which data sources are available for the given portfolio.

    Args:
        portfolio: Portfolio filename (e.g., "risk_on.csv")

    Returns:
        Dictionary with availability status for each data source
    """
    try:
        from ...tools.config.statistical_analysis_config import SPDSConfig

        # Create a temporary config to check file paths
        temp_config = SPDSConfig(
            PORTFOLIO=resolve_portfolio_path(portfolio), USE_TRADE_HISTORY=True
        )
        trade_history_path = temp_config.get_trade_history_file_path()

        # Check portfolio file in strategies directory
        portfolio_path = temp_config.get_portfolio_file_path()

        # Check for equity data paths (simplified check)
        has_equity_data = False
        for equity_path in temp_config.EQUITY_DATA_PATHS:
            equity_dir = Path(equity_path)
            if equity_dir.exists():
                # Look for any files that might contain equity data for this portfolio
                potential_files = list(equity_dir.glob("*.csv"))
                if potential_files:
                    has_equity_data = True
                    break

        return {
            "trade_history": trade_history_path.exists(),
            "equity_data": has_equity_data,
            "portfolio_file": portfolio_path.exists(),
        }
    except Exception:
        # If any error occurs during detection, default to safe values
        return {"trade_history": False, "equity_data": False, "portfolio_file": False}


@app.command()
def analyze(
    portfolio: str = typer.Argument(
        ..., help='Portfolio filename (e.g., "risk_on.csv")'
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    data_source: Optional[str] = typer.Option(
        None,
        "--data-source",
        help="Data source mode: 'trade-history', 'equity-curves', 'both', or 'auto' (default: auto)",
    ),
    output_format: str = typer.Option(
        "table", "--output-format", help="Output format: json, table, summary"
    ),
    save_results: Optional[str] = typer.Option(
        None, "--save-results", help="Save results to file (JSON format)"
    ),
    export_backtesting: bool = typer.Option(
        False,
        "--export-backtesting/--no-export-backtesting",
        help="Export deterministic backtesting parameters",
    ),
    percentile_threshold: int = typer.Option(
        95, "--percentile-threshold", help="Percentile threshold for exit signals"
    ),
    dual_layer_threshold: float = typer.Option(
        0.85, "--dual-layer-threshold", help="Dual layer convergence threshold"
    ),
    sample_size_min: int = typer.Option(
        15, "--sample-size-min", help="Minimum sample size for analysis"
    ),
    confidence_level: str = typer.Option(
        "medium", "--confidence-level", help="Confidence level: low, medium, high"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode (errors only)"),
):
    """
    Analyze portfolio using Statistical Performance Divergence System.

    Performs comprehensive statistical analysis on portfolio data to generate
    exit signals and divergence metrics. Automatically detects and uses both
    trade history and equity data when available for maximum analysis depth.

    Examples:
        trading-cli spds analyze risk_on.csv                            # Auto-detects and uses all available data
        trading-cli spds analyze risk_on.csv --data-source both         # Force both data sources
        trading-cli spds analyze risk_on.csv --data-source trade-history # Force trade history only
        trading-cli spds analyze risk_on.csv --data-source equity-curves # Force equity curves only
        trading-cli spds analyze risk_on.csv --export-backtesting --save-results results.json
    """
    try:
        # Auto-detect available data sources if not explicitly specified
        if data_source is None:
            data_source = "auto"

        # Resolve portfolio path
        portfolio = resolve_portfolio_path(portfolio)

        # Detect available data sources
        available_sources = _detect_available_data_sources(portfolio)

        # Determine which data sources to use based on availability and user preference
        if data_source == "auto":
            # Use both sources if available, prioritize trade history if only one is available
            if available_sources["trade_history"] and available_sources["equity_data"]:
                use_trade_history = (
                    True  # Start with trade history, but we'll also use equity
                )
                data_source_status = (
                    "Both Trade History and Equity Data (Auto-detected)"
                )
            elif available_sources["trade_history"]:
                use_trade_history = True
                data_source_status = "Trade History Only (Auto-detected)"
            elif available_sources["equity_data"]:
                use_trade_history = False
                data_source_status = "Equity Curves Only (Auto-detected)"
            else:
                use_trade_history = False
                data_source_status = "No data sources detected - using fallback"
        elif data_source == "both":
            use_trade_history = True  # We'll handle both in the analyzer
            data_source_status = "Both Trade History and Equity Data (Requested)"
        elif data_source == "trade-history":
            use_trade_history = True
            data_source_status = "Trade History Only (Requested)"
        elif data_source == "equity-curves":
            use_trade_history = False
            data_source_status = "Equity Curves Only (Requested)"
        else:
            raise ValueError(
                f"Invalid data source: {data_source}. Must be 'auto', 'both', 'trade-history', or 'equity-curves'"
            )

        if verbose:
            rprint(
                f"[dim]Available sources: TH={available_sources['trade_history']}, EQ={available_sources['equity_data']}[/dim]"
            )
            rprint(f"[dim]Selected: {data_source_status}[/dim]")

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "portfolio": portfolio,
            "trade_history": use_trade_history,
            "output_format": output_format,
            "save_results": save_results,
            "export_backtesting": export_backtesting,
            "percentile_threshold": percentile_threshold,
            "dual_layer_threshold": dual_layer_threshold,
            "sample_size_min": sample_size_min,
            "confidence_level": confidence_level,
            "verbose": verbose,
            "quiet": quiet,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, SPDSConfig, overrides)
        else:
            template = loader.get_config_template("spds")
            config = loader.load_from_dict(template, SPDSConfig, overrides)

        if verbose:
            rprint(f"[dim]Analyzing portfolio: {portfolio}[/dim]")
            rprint(f"[dim]Data source: {data_source_status}[/dim]")

        # Import SPDS modules
        from ...tools.config.statistical_analysis_config import (
            StatisticalAnalysisConfig,
        )
        from ...tools.portfolio_analyzer import (
            PortfolioStatisticalAnalyzer,
            analyze_portfolio,
        )

        # Create SPDS config from CLI config
        spds_config = StatisticalAnalysisConfig.create(portfolio, use_trade_history)

        # Apply overrides
        if percentile_threshold != 95:
            spds_config.PERCENTILE_THRESHOLDS["exit_immediately"] = float(
                percentile_threshold
            )
        if dual_layer_threshold != 0.85:
            spds_config.CONVERGENCE_THRESHOLD = dual_layer_threshold
        if sample_size_min != 15:
            spds_config.MIN_SAMPLE_SIZE = sample_size_min

        rprint(f"📊 Analyzing Portfolio: [cyan]{portfolio}[/cyan]")
        rprint(f"   Data Source: [yellow]{data_source_status}[/yellow]")

        # Add helpful information about what to expect
        if "Both" in data_source_status:
            rprint(
                "[dim]ℹ️  Using comprehensive analysis with trade-level data and equity curves[/dim]"
            )
        elif "Trade History Only" in data_source_status:
            rprint("[dim]ℹ️  Using detailed trade-level analysis[/dim]")
        elif "Equity Curves Only" in data_source_status:
            rprint(
                "[dim]ℹ️  Using equity curve analysis (individual trade data not available)[/dim]"
            )
        elif "fallback" in data_source_status:
            rprint(
                "[dim]ℹ️  Using fallback analysis - this is normal for position-based portfolios[/dim]"
            )

        if not quiet:
            rprint(
                "[dim]📝 Strategy matching messages below are informational - SPDS uses robust fallback analysis[/dim]"
            )

        # Pre-analysis validation for data source mapping
        if verbose and data_source in ["auto", "both", "trade-history"]:
            _validate_data_source_mapping(portfolio, verbose)

        rprint("-" * 60)

        # Run analysis
        if output_format == "json":
            results, summary = asyncio.run(
                _run_portfolio_analysis(portfolio, use_trade_history)
            )
            # Also export all formats for JSON output (including backtesting parameters)
            analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
            asyncio.run(
                _export_all_formats(
                    results,
                    summary,
                    analyzer,
                    portfolio,
                    spds_config,
                    True,  # Always export backtesting parameters
                )
            )
            return _output_json_results(results, summary, save_results)
        else:
            analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
            results = asyncio.run(_run_analyzer_analysis(analyzer))
            summary = analyzer.get_summary_report(results)

            # ALWAYS export to all formats automatically (including backtesting parameters)
            asyncio.run(
                _export_all_formats(
                    results,
                    summary,
                    analyzer,
                    portfolio,
                    spds_config,
                    True,  # Always export backtesting parameters
                )
            )

            if output_format == "summary":
                return _output_summary_results(summary)
            else:  # table format
                return _output_table_results(results, summary, analyzer)

    except FileNotFoundError as e:
        rprint(f"[red]❌ File not found: {e}[/red]")
        rprint(f"[yellow]💡 Available portfolios:[/yellow]")
        list_portfolios()
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]❌ Analysis failed: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def export(
    portfolio: str = typer.Argument(
        ..., help='Portfolio filename (e.g., "risk_on.csv")'
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    data_source: Optional[str] = typer.Option(
        None,
        "--data-source",
        help="Data source mode: 'trade-history', 'equity-curves', 'both', or 'auto' (default: auto)",
    ),
    format: str = typer.Option(
        "all", "--format", help="Export format: all, json, csv, markdown"
    ),
    output_dir: Optional[str] = typer.Option(
        None, "--output-dir", help="Output directory for exports"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Export backtesting parameters and analysis results.

    Exports deterministic backtesting parameters for strategy development
    and comprehensive analysis results in multiple formats. Automatically
    detects and uses both trade history and equity data when available.

    Examples:
        trading-cli spds export risk_on.csv --format all                      # Auto-detects and uses all available data
        trading-cli spds export conservative.csv --format json --output-dir ./exports/
        trading-cli spds export risk_on.csv --data-source both --format all  # Force both data sources
    """
    try:
        # Auto-detect available data sources if not explicitly specified
        if data_source is None:
            data_source = "auto"

        # Resolve portfolio path
        portfolio = resolve_portfolio_path(portfolio)

        # Detect available data sources
        available_sources = _detect_available_data_sources(portfolio)

        # Determine which data sources to use based on availability and user preference
        if data_source == "auto":
            # Use both sources if available, prioritize trade history if only one is available
            if available_sources["trade_history"] and available_sources["equity_data"]:
                use_trade_history = (
                    True  # Start with trade history, but we'll also use equity
                )
                data_source_status = (
                    "Both Trade History and Equity Data (Auto-detected)"
                )
            elif available_sources["trade_history"]:
                use_trade_history = True
                data_source_status = "Trade History Only (Auto-detected)"
            elif available_sources["equity_data"]:
                use_trade_history = False
                data_source_status = "Equity Curves Only (Auto-detected)"
            else:
                use_trade_history = False
                data_source_status = "No data sources detected - using fallback"
        elif data_source == "both":
            use_trade_history = True  # We'll handle both in the analyzer
            data_source_status = "Both Trade History and Equity Data (Requested)"
        elif data_source == "trade-history":
            use_trade_history = True
            data_source_status = "Trade History Only (Requested)"
        elif data_source == "equity-curves":
            use_trade_history = False
            data_source_status = "Equity Curves Only (Requested)"
        else:
            raise ValueError(
                f"Invalid data source: {data_source}. Must be 'auto', 'both', 'trade-history', or 'equity-curves'"
            )

        if verbose:
            rprint(
                f"[dim]Available sources: TH={available_sources['trade_history']}, EQ={available_sources['equity_data']}[/dim]"
            )
            rprint(f"[dim]Selected: {data_source_status}[/dim]")

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "portfolio": portfolio,
            "trade_history": use_trade_history,
            "format": format,
            "output_dir": output_dir,
            "verbose": verbose,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, SPDSConfig, overrides)
        else:
            template = loader.get_config_template("spds")
            config = loader.load_from_dict(template, SPDSConfig, overrides)

        rprint(f"📤 Exporting Analysis Results: [cyan]{portfolio}[/cyan]")
        rprint(f"   Format: [yellow]{format}[/yellow]")
        rprint(f"   Data Source: [yellow]{data_source_status}[/yellow]")
        rprint("-" * 60)

        # Import SPDS modules
        from ...tools.portfolio_analyzer import PortfolioStatisticalAnalyzer
        from ...tools.services.backtesting_parameter_export_service import (
            BacktestingParameterExportService,
        )
        from ...tools.services.divergence_export_service import DivergenceExportService

        # Run analysis
        analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
        results = asyncio.run(_run_analyzer_analysis(analyzer))
        summary = analyzer.get_summary_report(results)

        # Export results
        asyncio.run(_run_export_operations(results, summary, portfolio, format, config))

        rprint(f"[green]📁 All exports completed for {portfolio}[/green]")

    except Exception as e:
        rprint(f"[red]❌ Export failed: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def demo():
    """
    Create demo files and run example analysis.

    Creates sample portfolio files and runs demonstration analysis
    to showcase SPDS capabilities.
    """
    try:
        rprint("🎯 Creating SPDS Demo Files and Running Example Analysis")
        rprint("-" * 60)

        # Import SPDS demo functionality
        from ...tools.statistical_analysis_cli import StatisticalAnalysisCLI

        # Create and run demo
        cli = StatisticalAnalysisCLI()
        result = asyncio.run(cli._handle_demo())

        if result == 0:
            rprint("[green]✅ Demo completed successfully![/green]")
        else:
            rprint("[red]❌ Demo failed[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Demo failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def health():
    """
    Run SPDS system health check.

    Performs comprehensive health check of the SPDS system including
    data integrity, configuration validation, and dependency checks.
    """
    try:
        rprint("🏥 Running SPDS System Health Check")
        rprint("-" * 60)

        health_results = {"checks": {}, "overall_status": "healthy", "issues_found": 0}

        # Check data directories
        health_results["checks"]["data_directories"] = _check_spds_data_directories()

        # Check configuration
        health_results["checks"]["configuration"] = _check_spds_configuration()

        # Check dependencies
        health_results["checks"]["dependencies"] = _check_spds_dependencies()

        # Check portfolio files
        health_results["checks"]["portfolio_files"] = _check_spds_portfolio_files()

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
        _display_spds_health_results(health_results)

        # Overall summary
        status_colors = {"healthy": "green", "warning": "yellow", "unhealthy": "red"}
        status_color = status_colors[health_results["overall_status"]]

        rprint(
            f"\n🏥 SPDS System Health: [{status_color}]{health_results['overall_status'].upper()}[/{status_color}]"
        )

        if total_issues > 0:
            rprint(f"⚠️ Found {total_issues} issues that may need attention")
            raise typer.Exit(1)
        else:
            rprint("✅ No issues detected - SPDS system is healthy")

    except Exception as e:
        rprint(f"[red]❌ Health check failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def configure():
    """
    Interactive SPDS configuration management.

    Provides interactive interface for configuring SPDS analysis parameters,
    thresholds, and system settings.
    """
    try:
        rprint("⚙️ SPDS Configuration Management")
        rprint("-" * 60)

        # Import SPDS configuration
        from ...tools.config.statistical_analysis_config import (
            StatisticalAnalysisConfig,
        )

        # Display current configuration
        config = StatisticalAnalysisConfig.create("default.csv", False)

        table = Table(title="Current SPDS Configuration", show_header=True)
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        table.add_column("Description", style="dim")

        table.add_row(
            "Percentile Threshold",
            f"{config.PERCENTILE_THRESHOLDS['exit_immediately']:.0f}%",
            "Exit immediately signal threshold",
        )
        table.add_row(
            "Convergence Threshold",
            f"{config.CONVERGENCE_THRESHOLD:.2f}",
            "Dual layer convergence threshold",
        )
        table.add_row(
            "Min Sample Size",
            str(config.MIN_SAMPLE_SIZE),
            "Minimum sample size for analysis",
        )
        table.add_row(
            "Bootstrap Iterations",
            str(config.BOOTSTRAP_ITERATIONS),
            "Number of bootstrap iterations",
        )
        table.add_row(
            "Confidence Level", config.CONFIDENCE_LEVEL, "Analysis confidence level"
        )

        console.print(table)

        rprint(
            "\n[dim]Configuration can be modified through profiles or CLI arguments[/dim]"
        )
        rprint("[dim]Use --help with any SPDS command to see available options[/dim]")

    except Exception as e:
        rprint(f"[red]❌ Configuration display failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list_portfolios():
    """
    List available portfolios for analysis.

    Shows all available portfolio files that can be analyzed with SPDS.
    """
    try:
        rprint("📁 Available Portfolios for SPDS Analysis")
        rprint("-" * 60)

        # Import SPDS functionality
        from ...tools.statistical_analysis_cli import StatisticalAnalysisCLI

        # Create CLI instance and list portfolios
        cli = StatisticalAnalysisCLI()
        cli._handle_list_portfolios()

    except Exception as e:
        rprint(f"[red]❌ Failed to list portfolios: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive():
    """
    Interactive SPDS analysis mode.

    Launches interactive mode for guided SPDS analysis with
    step-by-step prompts and recommendations.
    """
    try:
        rprint("🎯 Interactive SPDS Analysis Mode")
        rprint("-" * 60)

        # Import SPDS functionality
        from ...tools.statistical_analysis_cli import StatisticalAnalysisCLI

        # Create CLI instance and run interactive mode
        cli = StatisticalAnalysisCLI()
        result = asyncio.run(cli._handle_interactive_mode())

        if result != 0:
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Interactive mode failed: {e}[/red]")
        raise typer.Exit(1)


# Helper async functions
async def _run_portfolio_analysis(portfolio, trade_history):
    """Run portfolio analysis asynchronously."""
    from ...tools.portfolio_analyzer import analyze_portfolio

    return await analyze_portfolio(portfolio, trade_history)


async def _run_analyzer_analysis(analyzer):
    """Run analyzer analysis asynchronously."""
    return await analyzer.analyze()


async def _run_export_operations(results, summary, portfolio, format, config):
    """Run export operations asynchronously."""
    from ...tools.services.backtesting_parameter_export_service import (
        BacktestingParameterExportService,
    )
    from ...tools.services.divergence_export_service import DivergenceExportService

    export_service = DivergenceExportService(config)
    backtesting_service = BacktestingParameterExportService(config)

    # Convert results dict to list for export service compatibility
    results_list = list(results.values()) if isinstance(results, dict) else results

    # Export based on format
    if format == "all" or format == "json":
        await export_service.export_json(results_list, portfolio)
        rprint("[green]✅ JSON export completed[/green]")

    if format == "all" or format == "csv":
        await export_service.export_csv(results_list, portfolio)
        rprint("[green]✅ CSV export completed[/green]")

    if format == "all" or format == "markdown":
        await export_service.export_markdown(results_list, portfolio)
        rprint("[green]✅ Markdown export completed[/green]")

    # Export backtesting parameters
    await backtesting_service.export_backtesting_parameters(results_list, portfolio)
    rprint("[green]✅ Backtesting parameters exported[/green]")


# Helper functions
async def _export_all_formats(
    results, summary, analyzer, portfolio, config, export_backtesting
):
    """Export results in all formats with validation and fallback"""
    try:
        from ...tools.services.backtesting_parameter_export_service import (
            BacktestingParameterExportService,
        )
        from ...tools.services.divergence_export_service import DivergenceExportService
        from ...tools.services.export_validator import ExportValidator

        export_service = DivergenceExportService(config)

        # Convert results dict to list for export service compatibility
        results_list = list(results.values()) if isinstance(results, dict) else results

        # Export JSON and CSV
        await export_service.export_json(results_list, portfolio)
        await export_service.export_csv(results_list, portfolio)
        await export_service.export_markdown(results_list, portfolio)

        # Always export backtesting parameters for comprehensive analysis
        backtesting_service = BacktestingParameterExportService(config)
        await backtesting_service.export_backtesting_parameters(results_list, portfolio)

        # CRITICAL: Validate exports and use fallback if needed
        validator = ExportValidator()
        is_valid, issues = validator.validate_exports(portfolio)

        if not is_valid:
            rprint(
                f"[yellow]⚠️ Export validation failed: {len(issues)} issues found[/yellow]"
            )
            rprint(f"[yellow]🔧 Generating fallback exports...[/yellow]")

            # Generate fallback exports using position data
            fallback_success = validator.generate_fallback_exports(portfolio)
            if fallback_success:
                rprint(f"[green]✅ Fallback exports generated successfully[/green]")
            else:
                rprint(f"[red]❌ Fallback export generation failed[/red]")
                for issue in issues:
                    rprint(f"[red]   - {issue}[/red]")
        else:
            rprint(f"[green]✅ Export validation passed[/green]")

    except Exception as e:
        rprint(f"[yellow]⚠️ Export warning: {e}[/yellow]")

        # Always attempt fallback on any export failure
        try:
            from ...tools.services.export_validator import ExportValidator

            validator = ExportValidator()
            rprint(f"[yellow]🔧 Attempting fallback export generation...[/yellow]")
            fallback_success = validator.generate_fallback_exports(portfolio)
            if fallback_success:
                rprint(f"[green]✅ Fallback exports generated successfully[/green]")
        except Exception as fallback_error:
            rprint(f"[red]❌ Fallback export failed: {fallback_error}[/red]")


def _output_json_results(results, summary, save_path: Optional[str] = None):
    """Output results in JSON format"""
    output_data = {"summary": summary, "results": results}

    if save_path:
        with open(save_path, "w") as f:
            json.dump(output_data, f, indent=2)
        rprint(f"[green]✅ Results saved to: {save_path}[/green]")
    else:
        rprint(json.dumps(output_data, indent=2))

    return 0


def _output_summary_results(summary):
    """Output summary results"""
    rprint("[bold]📊 SPDS Analysis Summary[/bold]")
    rprint("-" * 40)

    for key, value in summary.items():
        rprint(f"[cyan]{key}[/cyan]: {value}")

    return 0


def _output_table_results(results, summary, analyzer):
    """Output results in table format"""
    # Create results table
    table = Table(title="SPDS Analysis Results", show_header=True)
    table.add_column("Strategy", style="cyan", no_wrap=True)
    table.add_column("Ticker", style="white")
    table.add_column("Exit Signal", style="yellow")
    table.add_column("Confidence", style="green")
    table.add_column("P-Value", style="blue")

    for name, result in results.items():
        strategy_name = getattr(result, "strategy_name", name)
        ticker = getattr(result, "ticker", "Unknown")
        exit_signal = getattr(result, "exit_signal", "HOLD")
        # Fix confidence extraction - try multiple fields
        confidence = "N/A"
        if hasattr(result, "overall_confidence"):
            confidence = f"{result.overall_confidence:.1f}%"
        elif hasattr(result, "confidence"):
            confidence = f"{result.confidence:.1f}%"
        elif hasattr(result, "exit_signal") and hasattr(
            result.exit_signal, "confidence"
        ):
            confidence = f"{result.exit_signal.confidence:.1f}%"

        # Fix p_value extraction
        p_value = "N/A"
        if hasattr(result, "p_value"):
            p_value = f"{result.p_value:.3f}"
        elif hasattr(result, "exit_signal") and hasattr(
            result.exit_signal, "confidence"
        ):
            # Convert confidence to approximate p-value
            conf_val = result.exit_signal.confidence
            p_value = f"{(100 - conf_val) / 100:.3f}"

        if hasattr(exit_signal, "signal_type"):
            exit_signal = exit_signal.signal_type.value

        table.add_row(
            strategy_name, ticker, str(exit_signal), str(confidence), str(p_value)
        )

    console.print(table)

    # Display summary
    rprint("\n[bold]📊 Analysis Summary[/bold]")
    for key, value in summary.items():
        rprint(f"[cyan]{key}[/cyan]: {value}")

    return 0


def _check_spds_data_directories():
    """Check SPDS data directories"""
    result = {"status": "healthy", "issues": 0, "details": []}

    project_root = Path.cwd()
    spds_dirs = [
        "exports/statistical_analysis",
        "exports/backtesting_parameters",
        "csv/positions",
        "json/trade_history",
    ]

    for dir_name in spds_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            result["issues"] += 1
            result["details"].append(f"Missing SPDS directory: {dir_name}")
            result["status"] = "warning"
        else:
            result["details"].append(f"Directory exists: {dir_name}")

    return result


def _check_spds_configuration():
    """Check SPDS configuration"""
    result = {"status": "healthy", "issues": 0, "details": []}

    try:
        from ...tools.config.statistical_analysis_config import (
            StatisticalAnalysisConfig,
        )

        config = StatisticalAnalysisConfig.create("test.csv", False)
        result["details"].append("SPDS configuration loaded successfully")
    except Exception as e:
        result["issues"] += 1
        result["details"].append(f"SPDS configuration error: {e}")
        result["status"] = "warning"

    return result


def _check_spds_dependencies():
    """Check SPDS dependencies"""
    result = {"status": "healthy", "issues": 0, "details": []}

    spds_modules = [
        "app.tools.portfolio_analyzer",
        "app.tools.services.divergence_export_service",
        "app.tools.services.backtesting_parameter_export_service",
    ]

    for module_name in spds_modules:
        try:
            __import__(module_name)
            result["details"].append(f"Module available: {module_name}")
        except ImportError as e:
            result["issues"] += 1
            result["details"].append(f"Missing SPDS module: {module_name}")
            result["status"] = "warning"

    return result


def _check_spds_portfolio_files():
    """Check SPDS portfolio files"""
    result = {"status": "healthy", "issues": 0, "details": []}

    project_root = Path.cwd()
    positions_dir = project_root / "csv" / "positions"

    if positions_dir.exists():
        csv_files = list(positions_dir.glob("*.csv"))
        if len(csv_files) > 0:
            result["details"].append(f"Found {len(csv_files)} position files")
        else:
            result["issues"] += 1
            result["details"].append("No position CSV files found")
            result["status"] = "warning"
    else:
        result["issues"] += 1
        result["details"].append("Positions directory missing")
        result["status"] = "warning"

    return result


def _display_spds_health_results(health_results):
    """Display SPDS health results"""
    table = Table(title="SPDS System Health Check", show_header=True)
    table.add_column("Check", style="cyan", no_wrap=True)
    table.add_column("Status", style="white", justify="center")
    table.add_column("Issues", style="red", justify="right")
    table.add_column("Details", style="dim")

    for check_name, check_result in health_results["checks"].items():
        status_icon = "✅" if check_result["status"] == "healthy" else "⚠️"
        status = f"{status_icon} {check_result['status'].upper()}"
        issues = str(check_result["issues"])
        details = "; ".join(check_result["details"][:2])
        if len(check_result["details"]) > 2:
            details += "..."

        table.add_row(check_name.replace("_", " ").title(), status, issues, details)

    console.print(table)


def _validate_data_source_mapping(portfolio: str, verbose: bool = False):
    """
    Validate Position_UUID to trade history file mapping.

    Provides detailed feedback about which strategies will use trade history
    vs fallback to equity curve analysis.
    """
    try:
        from pathlib import Path

        import pandas as pd

        rprint("[dim]🔍 Validating data source mapping...[/dim]")

        # Load position data
        portfolio_path = Path(f"csv/positions/{portfolio}")
        if not portfolio_path.exists():
            rprint(f"[yellow]⚠️  Portfolio file not found: {portfolio_path}[/yellow]")
            return

        positions_df = pd.read_csv(portfolio_path)

        if "Position_UUID" not in positions_df.columns:
            rprint("[yellow]⚠️  No Position_UUID column found in portfolio[/yellow]")
            return

        # Check trade history directory
        trade_history_dir = Path("./json/trade_history/")
        if not trade_history_dir.exists():
            rprint(
                f"[yellow]⚠️  Trade history directory not found: {trade_history_dir}[/yellow]"
            )
            return

        # Get all trade history files
        trade_history_files = {f.stem for f in trade_history_dir.glob("*.json")}

        validation_results = {
            "matched_strategies": [],
            "fallback_strategies": [],
            "total_strategies": len(positions_df),
        }

        # Parse each Position_UUID and check for matching trade history
        for _, position in positions_df.iterrows():
            position_uuid = position["Position_UUID"]
            ticker = position.get("Ticker", "UNKNOWN")

            # Simulate the parsing logic from TradeHistoryAnalyzer
            parsed_strategy = _parse_uuid_for_validation(position_uuid, ticker)

            # Check for matching trade history files
            potential_files = [
                f"{ticker}_D_{parsed_strategy}",
                f"{ticker}_{parsed_strategy}",
            ]

            found_match = any(
                pattern in trade_history_files for pattern in potential_files
            )

            if found_match:
                validation_results["matched_strategies"].append(
                    {
                        "position_uuid": position_uuid,
                        "ticker": ticker,
                        "parsed_strategy": parsed_strategy,
                        "status": "✅ Trade History",
                    }
                )
            else:
                validation_results["fallback_strategies"].append(
                    {
                        "position_uuid": position_uuid,
                        "ticker": ticker,
                        "parsed_strategy": parsed_strategy,
                        "status": "📈 Equity Fallback",
                    }
                )

        # Display results
        matched_count = len(validation_results["matched_strategies"])
        fallback_count = len(validation_results["fallback_strategies"])
        total_count = validation_results["total_strategies"]

        rprint(f"[dim]Data Source Mapping Results:[/dim]")
        rprint(
            f"[dim]  • Trade History Available: {matched_count}/{total_count} strategies[/dim]"
        )
        rprint(
            f"[dim]  • Equity Fallback: {fallback_count}/{total_count} strategies[/dim]"
        )

        if verbose and fallback_count > 0:
            rprint(f"[dim]📈 Strategies using equity fallback (first 5):[/dim]")
            for strategy in validation_results["fallback_strategies"][:5]:
                rprint(
                    f"[dim]  • {strategy['ticker']} ({strategy['parsed_strategy']}) - {strategy['status']}[/dim]"
                )
            if fallback_count > 5:
                rprint(f"[dim]  • ... and {fallback_count - 5} more[/dim]")

        if verbose and matched_count > 0:
            rprint(f"[dim]✅ Strategies with trade history (first 3):[/dim]")
            for strategy in validation_results["matched_strategies"][:3]:
                rprint(
                    f"[dim]  • {strategy['ticker']} ({strategy['parsed_strategy']}) - {strategy['status']}[/dim]"
                )

    except Exception as e:
        rprint(f"[yellow]⚠️  Validation error: {e}[/yellow]")


def _parse_uuid_for_validation(position_uuid: str, ticker: str) -> str:
    """
    Simplified version of Position_UUID parsing for validation.

    Mirrors the logic in TradeHistoryAnalyzer._parse_position_uuid
    """
    import re

    # If it's already a simple strategy format, return as-is
    if not position_uuid.startswith(ticker + "_"):
        return position_uuid

    # Remove ticker prefix if present
    if position_uuid.startswith(ticker + "_"):
        remaining = position_uuid[len(ticker) + 1 :]

        # Remove date suffix if present (format: YYYYMMDD)
        date_pattern = r"_\d{8}$"
        remaining = re.sub(date_pattern, "", remaining)

        # Remove any trailing numeric signal window (often 0)
        signal_pattern = r"_\d+$"
        # Only remove if it's a single digit (likely signal window, not strategy parameter)
        if re.search(r"_\d{1}$", remaining):
            remaining = re.sub(signal_pattern, "", remaining)

        return remaining

    return position_uuid
