"""Statistical Performance Divergence System (SPDS) command implementations.

This module provides CLI commands for comprehensive portfolio statistical analysis,
exit signal generation, and backtesting parameter export.
"""

import asyncio
import json
import logging
from pathlib import Path

from rich import print as rprint
from rich.console import Console
from rich.table import Table
import typer

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
            PORTFOLIO=resolve_portfolio_path(portfolio), USE_TRADE_HISTORY=True,
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
    ctx: typer.Context,
    parameter: str
    | None = typer.Argument(
        None,
        help='Analysis parameter: portfolio file (e.g., "risk_on.csv"), ticker (e.g., "AMD"), strategy (e.g., "TSLA_SMA_15_25"), or position UUID (e.g., "TSLA_SMA_15_25_20250710")',
    ),
    portfolio: str
    | None = typer.Option(
        None,
        "--portfolio",
        help="Portfolio file name (e.g., 'protected', 'risk_on.csv')",
    ),
    profile: str
    | None = typer.Option(None, "--profile", "-p", help="Configuration profile name"),
    data_source: str
    | None = typer.Option(
        None,
        "--data-source",
        help="Data source mode: 'trade-history', 'equity-curves', 'both', or 'auto' (default: auto)",
    ),
    output_format: str = typer.Option(
        "table", "--output-format", help="Output format: json, table, summary",
    ),
    detailed: bool = typer.Option(
        True,
        "--detailed/--no-detailed",
        help="Show detailed component scores breakdown",
    ),
    components: str
    | None = typer.Option(
        None,
        "--components",
        help="Show specific components: 'risk,momentum,trend,risk-adj,mean-rev,volume' (comma-separated)",
    ),
    save_results: str
    | None = typer.Option(
        None, "--save-results", help="Save results to file (JSON format)",
    ),
    export_backtesting: bool = typer.Option(
        False,
        "--export-backtesting/--no-export-backtesting",
        help="Export deterministic backtesting parameters",
    ),
    percentile_threshold: int = typer.Option(
        95, "--percentile-threshold", help="Percentile threshold for exit signals",
    ),
    dual_layer_threshold: float = typer.Option(
        0.85, "--dual-layer-threshold", help="Dual layer convergence threshold",
    ),
    sample_size_min: int = typer.Option(
        15, "--sample-size-min", help="Minimum sample size for analysis",
    ),
    confidence_level: str = typer.Option(
        "medium", "--confidence-level", help="Confidence level: low, medium, high",
    ),
):
    """
    Analyze using Statistical Performance Divergence System with enhanced parameter support.

    Supports multiple analysis types through intelligent parameter detection:

    • Portfolio Analysis: Analyzes entire portfolio files
    • Asset Distribution Analysis: Analyzes individual tickers
    • Multi-Ticker Analysis: Analyzes multiple tickers in parallel
    • Strategy Analysis: Analyzes specific strategy configurations
    • Multi-Strategy Analysis: Analyzes multiple strategies in parallel
    • Position Analysis: Analyzes individual position UUIDs
    • Multi-Position Analysis: Analyzes multiple positions in parallel
    • Multi-Portfolio Analysis: Analyzes multiple portfolios in parallel

    Examples:
        trading-cli spds analyze risk_on.csv                            # Portfolio analysis (existing)
        trading-cli spds analyze --portfolio protected                  # Portfolio analysis with flag
        trading-cli spds analyze --portfolio risk_on.csv                # Portfolio analysis with flag
        trading-cli spds analyze AMD                                     # Asset distribution analysis
        trading-cli spds analyze NVDA,MSFT,QCOM                        # Multi-ticker parallel analysis
        trading-cli spds analyze TSLA_SMA_15_25                        # Strategy analysis
        trading-cli spds analyze TSLA_SMA_15_25,RJF_SMA_68_77,SMCI_SMA_58_60  # Multi-strategy parallel analysis
        trading-cli spds analyze TSLA_SMA_15_25_20250710               # Position UUID analysis
        trading-cli spds analyze TSLA_SMA_15_25_20250710,TPR_SMA_14_30_20250506,MA_SMA_78_82_20250701  # Multi-position parallel analysis
        trading-cli spds analyze risk_on,live_signals,protected         # Multi-portfolio parallel analysis
        trading-cli spds analyze --portfolio risk_on.csv --data-source both  # Portfolio with flag and data source
        trading-cli spds analyze NVDA,MSFT,QCOM --components risk,trend  # Multi-ticker with component scores (detailed is now default)
    """
    try:
        # Get global verbose and quiet flags
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
        global_quiet = ctx.obj.get("quiet", False) if ctx.obj else False

        # Parameter resolution: handle --portfolio flag or positional parameter
        if portfolio and parameter:
            rprint(
                "[red]❌ Cannot specify both positional parameter and --portfolio flag[/red]",
            )
            rprint(
                "[yellow]💡 Use either: 'trading-cli spds analyze risk_on.csv' OR 'trading-cli spds analyze --portfolio risk_on.csv'[/yellow]",
            )
            raise typer.Exit(1)
        if portfolio:
            parameter = portfolio
            if global_verbose:
                rprint(f"[dim]Using portfolio flag: {portfolio}[/dim]")
        elif not parameter:
            rprint(
                "[red]❌ Must specify either positional parameter or --portfolio flag[/red]",
            )
            rprint("[yellow]💡 Examples:[/yellow]")
            rprint("[yellow]  trading-cli spds analyze risk_on.csv[/yellow]")
            rprint(
                "[yellow]  trading-cli spds analyze --portfolio risk_on.csv[/yellow]",
            )
            rprint("[yellow]  trading-cli spds analyze --portfolio protected[/yellow]")
            raise typer.Exit(1)

        # Import enhanced parameter parsing and analysis components
        from ...tools.parameter_parser import ParameterType, parse_spds_parameter

        # Parse the input parameter to detect type and extract components
        if global_verbose:
            rprint(f"[dim]Parsing input parameter: {parameter}[/dim]")

        try:
            parsed_param = parse_spds_parameter(parameter)
        except ValueError as e:
            rprint(f"[red]❌ Parameter parsing failed: {e}[/red]")
            raise typer.Exit(1)

        parameter_type = parsed_param.parameter_type

        if global_verbose:
            rprint(f"[dim]Detected parameter type: {parameter_type}[/dim]")
            rprint(f"[dim]Parsed components: {parsed_param.dict()}[/dim]")

        # Route to appropriate analysis based on parameter type
        if parameter_type == ParameterType.PORTFOLIO_FILE:
            # Use existing portfolio analysis logic (backward compatibility)
            return asyncio.run(
                _analyze_portfolio_mode(
                    parameter,
                    data_source,
                    profile,
                    output_format,
                    detailed,
                    components,
                    save_results,
                    export_backtesting,
                    percentile_threshold,
                    dual_layer_threshold,
                    sample_size_min,
                    confidence_level,
                    global_verbose,
                    global_quiet,
                ),
            )
        # Use enhanced parameter analysis
        return asyncio.run(
            _analyze_enhanced_parameter_mode(
                parsed_param,
                data_source,
                profile,
                output_format,
                detailed,
                components,
                save_results,
                export_backtesting,
                percentile_threshold,
                dual_layer_threshold,
                sample_size_min,
                confidence_level,
                global_verbose,
                global_quiet,
            ),
        )

    except FileNotFoundError as e:
        rprint(f"[red]❌ File not found: {e}[/red]")
        rprint("[yellow]💡 Available portfolios:[/yellow]")
        list_portfolios()
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]❌ Analysis failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def export(
    ctx: typer.Context,
    portfolio: str = typer.Argument(
        ..., help='Portfolio filename (e.g., "risk_on.csv")',
    ),
    profile: str
    | None = typer.Option(None, "--profile", "-p", help="Configuration profile name"),
    data_source: str
    | None = typer.Option(
        None,
        "--data-source",
        help="Data source mode: 'trade-history', 'equity-curves', 'both', or 'auto' (default: auto)",
    ),
    format: str = typer.Option(
        "all", "--format", help="Export format: all, json, csv, markdown",
    ),
    output_dir: str
    | None = typer.Option(None, "--output-dir", help="Output directory for exports"),
):
    """
    Export backtesting parameters and analysis results.

    Exports deterministic backtesting parameters for strategy development
    and comprehensive analysis results in multiple formats. Automatically
    detects and uses both trade history and equity data when available.

    Examples:
        trading-cli spds export risk_on.csv --format all                      # Auto-detects and uses all available data
        trading-cli spds export conservative.csv --format json --output-dir ./data/outputs/spds/
        trading-cli spds export risk_on.csv --data-source both --format all  # Force both data sources
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

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
            msg = f"Invalid data source: {data_source}. Must be 'auto', 'both', 'trade-history', or 'equity-curves'"
            raise ValueError(
                msg,
            )

        if global_verbose:
            rprint(
                f"[dim]Available sources: TH={available_sources['trade_history']}, EQ={available_sources['equity_data']}[/dim]",
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
            "verbose": global_verbose,
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, SPDSConfig, overrides)
        else:
            # Use default SPDS profile
            config = loader.load_from_profile("spds_default", SPDSConfig, overrides)

        rprint(f"📤 Exporting Analysis Results: [cyan]{portfolio}[/cyan]")
        rprint(f"   Format: [yellow]{format}[/yellow]")
        rprint(f"   Data Source: [yellow]{data_source_status}[/yellow]")
        rprint("-" * 60)

        # Import SPDS modules
        from ...tools.portfolio_analyzer import PortfolioStatisticalAnalyzer

        # Run analysis
        analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
        results = asyncio.run(_run_analyzer_analysis(analyzer))
        summary = analyzer.get_summary_report(results)

        # Export results
        asyncio.run(_run_export_operations(results, summary, portfolio, format, config))

        rprint(f"[green]📁 All exports completed for {portfolio}[/green]")

    except Exception as e:
        rprint(f"[red]❌ Export failed: {e}[/red]")
        if global_verbose:
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
            f"\n🏥 SPDS System Health: [{status_color}]{health_results['overall_status'].upper()}[/{status_color}]",
        )

        if total_issues > 0:
            rprint(f"⚠️ Found {total_issues} issues that may need attention")
            raise typer.Exit(1)
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
            "Confidence Level", config.CONFIDENCE_LEVEL, "Analysis confidence level",
        )

        console.print(table)

        rprint(
            "\n[dim]Configuration can be modified through profiles or CLI arguments[/dim]",
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


# Enhanced parameter analysis functions
async def _analyze_portfolio_mode(
    portfolio: str,
    data_source: str | None,
    profile: str | None,
    output_format: str,
    detailed: bool,
    components: str | None,
    save_results: str | None,
    export_backtesting: bool,
    percentile_threshold: int,
    dual_layer_threshold: float,
    sample_size_min: int,
    confidence_level: str,
    global_verbose: bool,
    global_quiet: bool,
):
    """Handle portfolio-based analysis (backward compatibility)."""
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
            data_source_status = "Both Trade History and Equity Data (Auto-detected)"
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
        msg = f"Invalid data source: {data_source}. Must be 'auto', 'both', 'trade-history', or 'equity-curves'"
        raise ValueError(
            msg,
        )

    if global_verbose:
        rprint(
            f"[dim]Available sources: TH={available_sources['trade_history']}, EQ={available_sources['equity_data']}[/dim]",
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
        "verbose": global_verbose,
        "quiet": global_quiet,
    }

    # Load configuration
    if profile:
        loader.load_from_profile(profile, SPDSConfig, overrides)
    else:
        # Use default SPDS profile
        loader.load_from_profile("spds_default", SPDSConfig, overrides)

    if global_verbose:
        rprint(f"[dim]Analyzing portfolio: {portfolio}[/dim]")
        rprint(f"[dim]Data source: {data_source_status}[/dim]")

    # Import SPDS modules
    from ...tools.config.statistical_analysis_config import StatisticalAnalysisConfig
    from ...tools.portfolio_analyzer import PortfolioStatisticalAnalyzer

    # Create SPDS config from CLI config
    spds_config = StatisticalAnalysisConfig.create(portfolio, use_trade_history)

    # Apply overrides
    if percentile_threshold != 95:
        spds_config.PERCENTILE_THRESHOLDS["exit_immediately"] = float(
            percentile_threshold,
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
            "[dim]ℹ️  Using comprehensive analysis with trade-level data and equity curves[/dim]",
        )
    elif "Trade History Only" in data_source_status:
        rprint("[dim]ℹ️  Using detailed trade-level analysis[/dim]")
    elif "Equity Curves Only" in data_source_status:
        rprint(
            "[dim]ℹ️  Using equity curve analysis (individual trade data not available)[/dim]",
        )
    elif "fallback" in data_source_status:
        rprint(
            "[dim]ℹ️  Using fallback analysis - this is normal for position-based portfolios[/dim]",
        )

    if not global_quiet:
        rprint(
            "[dim]📝 Strategy matching messages below are informational - SPDS uses robust fallback analysis[/dim]",
        )

    # Pre-analysis validation for data source mapping
    if global_verbose and data_source in ["auto", "both", "trade-history"]:
        _validate_data_source_mapping(portfolio, global_verbose)

    rprint("-" * 60)

    # Run analysis
    if output_format == "json":
        results, summary = await _run_portfolio_analysis(portfolio, use_trade_history)
        # Also export all formats for JSON output (including backtesting parameters)
        analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
        await _export_all_formats(
            results,
            summary,
            analyzer,
            portfolio,
            spds_config,
            True,  # Always export backtesting parameters
        )
        return _output_json_results(results, summary, save_results)
    analyzer = PortfolioStatisticalAnalyzer(portfolio, use_trade_history)
    results = await _run_analyzer_analysis(analyzer, detailed)
    summary = analyzer.get_summary_report(results)

    # ALWAYS export to all formats automatically (including backtesting parameters)
    await _export_all_formats(
        results,
        summary,
        analyzer,
        portfolio,
        spds_config,
        True,  # Always export backtesting parameters
    )

    if output_format == "summary":
        return _output_summary_results(summary)
    # table format
    return _output_table_results(results, summary, analyzer, detailed, components)


async def _analyze_enhanced_parameter_mode(
    parsed_param,
    data_source: str | None,
    profile: str | None,
    output_format: str,
    detailed: bool,
    components: str | None,
    save_results: str | None,
    export_backtesting: bool,
    percentile_threshold: int,
    dual_layer_threshold: float,
    sample_size_min: int,
    confidence_level: str,
    global_verbose: bool,
    global_quiet: bool,
):
    """Handle enhanced parameter analysis (ticker, strategy, position UUID)."""
    from ...tools.parameter_parser import ParameterType
    from ...tools.specialized_analyzers import create_analyzer

    parameter_type = parsed_param.parameter_type

    # Display analysis type information
    type_descriptions = {
        ParameterType.TICKER_ONLY: "Asset Distribution Analysis",
        ParameterType.MULTI_TICKER: "Multi-Ticker Parallel Analysis",
        ParameterType.STRATEGY_SPEC: "Strategy Performance Analysis",
        ParameterType.MULTI_STRATEGY_SPEC: "Multi-Strategy Parallel Analysis",
        ParameterType.POSITION_UUID: "Position-Specific Analysis",
        ParameterType.MULTI_POSITION_UUID: "Multi-Position Parallel Analysis",
        ParameterType.MULTI_PORTFOLIO_FILE: "Multi-Portfolio Parallel Analysis",
    }

    analysis_description = type_descriptions.get(parameter_type, "Unknown Analysis")

    rprint(f"🎯 {analysis_description}: [cyan]{parsed_param.original_input}[/cyan]")

    if parameter_type == ParameterType.TICKER_ONLY:
        rprint(f"   Ticker: [yellow]{parsed_param.ticker}[/yellow]")
        rprint("[dim]ℹ️  Analyzing underlying asset distribution characteristics[/dim]")
    elif parameter_type == ParameterType.MULTI_TICKER:
        rprint(
            f"   Tickers: [yellow]{', '.join(parsed_param.tickers)}[/yellow] ({len(parsed_param.tickers)} total)",
        )
        rprint(
            "[dim]ℹ️  Analyzing multiple assets in parallel for comparative distribution analysis[/dim]",
        )
    elif parameter_type == ParameterType.STRATEGY_SPEC:
        rprint(
            f"   Strategy: [yellow]{parsed_param.ticker} {parsed_param.strategy_type} {parsed_param.fast_period}/{parsed_param.slow_period}[/yellow]",
        )
        rprint(
            "[dim]ℹ️  Analyzing strategy-specific performance and equity curves[/dim]",
        )
    elif parameter_type == ParameterType.MULTI_STRATEGY_SPEC:
        strategy_count = len(parsed_param.strategies)
        strategy_list = [
            f"{s['ticker']}_{s['strategy_type']}_{s['fast_period']}_{s['slow_period']}"
            for s in parsed_param.strategies[:3]
        ]
        if strategy_count > 3:
            strategy_display = (
                ", ".join(strategy_list) + f", ... (+{strategy_count-3} more)"
            )
        else:
            strategy_display = ", ".join(strategy_list)
        rprint(
            f"   Strategies: [yellow]{strategy_display}[/yellow] ({strategy_count} total)",
        )
        rprint(
            "[dim]ℹ️  Analyzing multiple strategies in parallel for comparative performance analysis[/dim]",
        )
    elif parameter_type == ParameterType.POSITION_UUID:
        rprint(
            f"   Position: [yellow]{parsed_param.ticker} {parsed_param.strategy_type} {parsed_param.fast_period}/{parsed_param.slow_period} ({parsed_param.entry_date})[/yellow]",
        )
        rprint(
            "[dim]ℹ️  Analyzing individual position with trade history and metrics[/dim]",
        )
    elif parameter_type == ParameterType.MULTI_POSITION_UUID:
        position_count = len(parsed_param.positions)
        position_list = [
            f"{p['ticker']}_{p['strategy_type']}_{p['fast_period']}_{p['slow_period']}_{p['entry_date'].replace('-', '')}"
            for p in parsed_param.positions[:3]
        ]
        if position_count > 3:
            position_display = (
                ", ".join(position_list) + f", ... (+{position_count-3} more)"
            )
        else:
            position_display = ", ".join(position_list)
        rprint(
            f"   Positions: [yellow]{position_display}[/yellow] ({position_count} total)",
        )
        rprint(
            "[dim]ℹ️  Analyzing multiple positions in parallel for comparative trade analysis[/dim]",
        )
    elif parameter_type == ParameterType.MULTI_PORTFOLIO_FILE:
        rprint(
            f"   Portfolios: [yellow]{', '.join(parsed_param.portfolio_files)}[/yellow] ({len(parsed_param.portfolio_files)} total)",
        )
        rprint(
            "[dim]ℹ️  Analyzing multiple portfolios in parallel for comparative portfolio analysis[/dim]",
        )

    if not global_quiet:
        rprint(
            "[dim]📝 Enhanced parameter analysis provides specialized insights for each input type[/dim]",
        )

    rprint("-" * 60)

    # Create appropriate analyzer
    try:
        analyzer = create_analyzer(parsed_param, logger=logging.getLogger(__name__))
    except Exception as e:
        rprint(f"[red]❌ Failed to create analyzer: {e}[/red]")
        raise typer.Exit(1)

    # Run analysis
    try:
        results = await analyzer.analyze()
    except Exception as e:
        rprint(f"[red]❌ Analysis failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)

    # Create summary
    summary = {
        "analysis_type": analysis_description,
        "parameter_type": str(parameter_type),
        "total_results": len(results),
        "input_parameter": parsed_param.original_input,
    }

    if results:
        # Add summary statistics
        exit_signals = [
            getattr(result, "exit_signal", "UNKNOWN") for result in results.values()
        ]
        signal_counts: dict[str, int] = {}
        for signal in exit_signals:
            signal_counts[str(signal)] = signal_counts.get(str(signal), 0) + 1
        summary["exit_signal_distribution"] = signal_counts

        # Average confidence
        confidences = [
            getattr(result, "confidence_level", 0.0) for result in results.values()
        ]
        summary["average_confidence"] = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

    # Export results (using simplified config for enhanced mode)
    try:
        from ...tools.config.statistical_analysis_config import (
            StatisticalAnalysisConfig,
        )

        # Create a minimal config for export compatibility
        # Use special naming for enhanced analysis to distinguish from real portfolios
        virtual_portfolio = f"enhanced_{parsed_param.parameter_type}_{parsed_param.original_input.replace('/', '_').replace('-', '_')}.csv"
        spds_config = StatisticalAnalysisConfig.create(virtual_portfolio, False)

        # Apply parameter overrides
        if percentile_threshold != 95:
            spds_config.PERCENTILE_THRESHOLDS["exit_immediately"] = float(
                percentile_threshold,
            )
        if dual_layer_threshold != 0.85:
            spds_config.CONVERGENCE_THRESHOLD = dual_layer_threshold
        if sample_size_min != 15:
            spds_config.MIN_SAMPLE_SIZE = sample_size_min

        # Export using existing infrastructure
        await _export_all_formats(
            results,
            summary,
            analyzer,
            virtual_portfolio,
            spds_config,
            export_backtesting,
        )

    except Exception as e:
        if global_verbose:
            rprint(f"[yellow]⚠️  Export warning: {e}[/yellow]")

    # Output results
    if output_format == "json":
        return _output_json_results(results, summary, save_results)
    if output_format == "summary":
        return _output_summary_results(summary)
    # table format
    return _output_table_results(results, summary, analyzer, detailed, components)


# Helper async functions
async def _run_portfolio_analysis(portfolio, trade_history):
    """Run portfolio analysis asynchronously."""
    from ...tools.portfolio_analyzer import analyze_portfolio

    return await analyze_portfolio(portfolio, trade_history)


async def _run_analyzer_analysis(analyzer, detailed: bool = False):
    """Run analyzer analysis asynchronously."""
    if (
        hasattr(analyzer, "analyze")
        and "detailed" in analyzer.analyze.__code__.co_varnames
    ):
        return await analyzer.analyze(detailed=detailed)
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
    if format in ("all", "json"):
        await export_service.export_json(results_list, portfolio)
        rprint("[green]✅ JSON export completed[/green]")

    if format in ("all", "csv"):
        await export_service.export_csv(results_list, portfolio)
        rprint("[green]✅ CSV export completed[/green]")

    if format in ("all", "markdown"):
        await export_service.export_markdown(results_list, portfolio)
        rprint("[green]✅ Markdown export completed[/green]")

    # Export backtesting parameters
    await backtesting_service.export_backtesting_parameters(results_list, portfolio)
    rprint("[green]✅ Backtesting parameters exported[/green]")


# Helper functions
async def _export_all_formats(
    results, summary, analyzer, portfolio, config, export_backtesting,
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
                f"[yellow]⚠️ Export validation failed: {len(issues)} issues found[/yellow]",
            )
            rprint("[yellow]🔧 Generating fallback exports...[/yellow]")

            # Generate fallback exports using position data
            fallback_success = validator.generate_fallback_exports(portfolio)
            if fallback_success:
                rprint("[green]✅ Fallback exports generated successfully[/green]")
            else:
                rprint("[red]❌ Fallback export generation failed[/red]")
                for issue in issues:
                    rprint(f"[red]   - {issue}[/red]")
        else:
            rprint("[green]✅ Export validation passed[/green]")

    except Exception as e:
        rprint(f"[yellow]⚠️ Export warning: {e}[/yellow]")

        # Always attempt fallback on any export failure
        try:
            from ...tools.services.export_validator import ExportValidator

            validator = ExportValidator()
            rprint("[yellow]🔧 Attempting fallback export generation...[/yellow]")
            fallback_success = validator.generate_fallback_exports(portfolio)
            if fallback_success:
                rprint("[green]✅ Fallback exports generated successfully[/green]")
        except Exception as fallback_error:
            rprint(f"[red]❌ Fallback export failed: {fallback_error}[/red]")


def _output_json_results(results, summary, save_path: str | None = None):
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


def _output_table_results(
    results, summary, analyzer, detailed: bool = False, components: str | None = None,
):
    """Output results in table format"""
    # Create results table
    table_title = "SPDS Analysis Results"
    if detailed:
        table_title += " (Detailed Component Scores)"

    table = Table(title=table_title, show_header=True)
    table.add_column("Strategy", style="cyan", no_wrap=True)
    table.add_column("Ticker", style="white")
    table.add_column("Recommendation", style="yellow")
    table.add_column("Confidence", style="green")
    table.add_column("P-Value", style="blue")

    # Add component score columns when detailed flag is set
    if detailed:
        # Parse components filter if provided
        component_filter = None
        if components:
            component_filter = [c.strip() for c in components.split(",")]

        # Standard component columns (always show if detailed)
        component_columns = {
            "risk": ("Risk", "red"),
            "momentum": ("Momentum", "magenta"),
            "trend": ("Trend", "bright_green"),
            "risk-adj": ("Risk-Adj", "orange1"),
            "mean-rev": ("Mean-Rev", "purple"),
            "volume": ("Volume", "cyan"),
            "overall": ("Overall", "bold yellow"),
            "regime": ("Regime", "dim white"),
        }

        # Add only requested columns if filter specified, otherwise add all
        # Always include overall and regime for debugging
        for comp_key, (col_name, style) in component_columns.items():
            if (
                not component_filter
                or comp_key in component_filter
                or comp_key in ["overall", "regime"]
            ):
                width = 6 if comp_key == "regime" else 8
                table.add_column(col_name, style=style, justify="right", width=width)

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
            result.exit_signal, "confidence",
        ):
            confidence = f"{result.exit_signal.confidence:.1f}%"

        # Fix p_value extraction
        p_value = "N/A"
        if hasattr(result, "p_value"):
            p_value = f"{result.p_value:.3f}"
        elif hasattr(result, "exit_signal") and hasattr(
            result.exit_signal, "confidence",
        ):
            # Convert confidence to approximate p-value
            conf_val = result.exit_signal.confidence
            p_value = f"{(100 - conf_val) / 100:.3f}"

        if hasattr(exit_signal, "signal_type"):
            exit_signal = exit_signal.signal_type.value

        # Prepare row data
        row_data = [
            strategy_name,
            ticker,
            str(exit_signal),
            str(confidence),
            str(p_value),
        ]

        # Add component scores when detailed mode is enabled
        if detailed:
            # Try to get component scores from the result
            component_scores = {}
            if hasattr(result, "component_scores"):
                component_scores = result.component_scores
            elif (
                hasattr(result, "raw_analysis_data")
                and result.raw_analysis_data
                and "component_scores" in result.raw_analysis_data
            ):
                # Check if component scores are in raw_analysis_data
                component_scores = result.raw_analysis_data["component_scores"]
            elif hasattr(result, "divergence_metrics") and isinstance(
                result.divergence_metrics, dict,
            ):
                # Check if component scores are in divergence_metrics
                metrics = result.divergence_metrics
                if "component_scores" in metrics:
                    component_scores = metrics["component_scores"]

            # Extract individual component scores with proper mapping
            risk_score = component_scores.get("risk_score", 0.0)
            momentum_score = component_scores.get("momentum_score", 0.0)
            trend_score = component_scores.get("trend_score", 0.0)
            risk_adj_score = component_scores.get("risk_adjusted_score", 0.0)
            mean_rev_score = component_scores.get("mean_reversion_score", 0.0)
            volume_score = component_scores.get("volume_liquidity_score", 0.0)

            # Add component scores based on filter
            component_filter = None
            if components:
                component_filter = [c.strip() for c in components.split(",")]

            # Get overall score and regime information for debugging
            overall_score = component_scores.get("overall_score", 0.0)
            volatility_regime = component_scores.get("volatility_regime", "unknown")

            component_values = {
                "risk": f"{risk_score:+.0f}",
                "momentum": f"{momentum_score:+.0f}",
                "trend": f"{trend_score:+.0f}",
                "risk-adj": f"{risk_adj_score:+.0f}",
                "mean-rev": f"{mean_rev_score:+.0f}",
                "volume": f"{volume_score:+.0f}",
                "overall": f"{overall_score:+.1f}",
                "regime": volatility_regime[:4],  # Truncate for display
            }

            for comp_key in [
                "risk",
                "momentum",
                "trend",
                "risk-adj",
                "mean-rev",
                "volume",
                "overall",
                "regime",
            ]:
                if (
                    not component_filter
                    or comp_key in component_filter
                    or comp_key in ["overall", "regime"]
                ):
                    row_data.append(component_values[comp_key])

        table.add_row(*row_data)

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
        "data/outputs/exports",
        "data/raw/positions",
        "data/raw/reports/trade_history",
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

        StatisticalAnalysisConfig.create("test.csv", False)
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
        except ImportError:
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


def _validate_data_source_mapping(portfolio: str, global_verbose: bool = False):
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
        portfolio_path = Path(f"data/raw/positions/{portfolio}")
        if not portfolio_path.exists():
            rprint(f"[yellow]⚠️  Portfolio file not found: {portfolio_path}[/yellow]")
            return

        positions_df = pd.read_csv(portfolio_path)

        if "Position_UUID" not in positions_df.columns:
            rprint("[yellow]⚠️  No Position_UUID column found in portfolio[/yellow]")
            return

        # Check trade history directory
        trade_history_dir = Path("./data/raw/reports/trade_history/")
        if not trade_history_dir.exists():
            rprint(
                f"[yellow]⚠️  Trade history directory not found: {trade_history_dir}[/yellow]",
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
                    },
                )
            else:
                validation_results["fallback_strategies"].append(
                    {
                        "position_uuid": position_uuid,
                        "ticker": ticker,
                        "parsed_strategy": parsed_strategy,
                        "status": "📈 Equity Fallback",
                    },
                )

        # Display results
        matched_count = len(validation_results["matched_strategies"])
        fallback_count = len(validation_results["fallback_strategies"])
        total_count = validation_results["total_strategies"]

        rprint("[dim]Data Source Mapping Results:[/dim]")
        rprint(
            f"[dim]  • Trade History Available: {matched_count}/{total_count} strategies[/dim]",
        )
        rprint(
            f"[dim]  • Equity Fallback: {fallback_count}/{total_count} strategies[/dim]",
        )

        if global_verbose and fallback_count > 0:
            rprint("[dim]📈 Strategies using equity fallback (first 5):[/dim]")
            for strategy in validation_results["fallback_strategies"][:5]:
                rprint(
                    f"[dim]  • {strategy['ticker']} ({strategy['parsed_strategy']}) - {strategy['status']}[/dim]",
                )
            if fallback_count > 5:
                rprint(f"[dim]  • ... and {fallback_count - 5} more[/dim]")

        if global_verbose and matched_count > 0:
            rprint("[dim]✅ Strategies with trade history (first 3):[/dim]")
            for strategy in validation_results["matched_strategies"][:3]:
                rprint(
                    f"[dim]  • {strategy['ticker']} ({strategy['parsed_strategy']}) - {strategy['status']}[/dim]",
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

        # Remove any trailing numeric signal period (often 0)
        signal_pattern = r"_\d+$"
        # Only remove if it's a single digit (likely signal period, not strategy parameter)
        if re.search(r"_\d{1}$", remaining):
            remaining = re.sub(signal_pattern, "", remaining)

        return remaining

    return position_uuid
