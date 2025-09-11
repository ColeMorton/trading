"""
Strategy command implementations.

This module provides CLI commands for executing and analyzing MA Cross
and MACD strategies with various configuration options.
"""

from pathlib import Path
from typing import List, Optional, Union

import pandas as pd
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.tools.console_logging import ConsoleLogger, PerformanceAwareConsoleLogger

from ..config import ConfigLoader
from ..models.strategy import (
    MACDConfig,
    MACrossConfig,
    MarketType,
    StrategyConfig,
    StrategyExecutionSummary,
    StrategyPortfolioResults,
)
from ..services import StrategyDispatcher
from .strategy_utils import (
    build_configuration_overrides,
    convert_to_legacy_config,
    display_results_table,
    display_sweep_results_table,
    handle_command_error,
    show_config_preview,
    show_execution_progress,
    validate_parameter_relationships,
)

# Create strategy sub-app
app = typer.Typer(
    name="strategy", help="Execute and analyze trading strategies", no_args_is_help=True
)

console = Console()


@app.command()
def run(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: Optional[List[str]] = typer.Option(
        None,
        "--ticker",
        "--ticker-1",
        "-t",
        "-t1",
        help="Ticker symbols to analyze (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)",
    ),
    ticker_2: Optional[str] = typer.Option(
        None,
        "--ticker-2",
        "-t2",
        help="Second ticker for synthetic pair analysis (automatically enables synthetic mode)",
    ),
    strategy_type: Optional[List[str]] = typer.Option(
        None,
        "--strategy",
        "-s",
        help="Strategy types: SMA, MACD (default strategies), EMA, ATR (specialized - explicit only, can be used multiple times)",
    ),
    min_trades: Optional[int] = typer.Option(
        None, "--min-trades", help="Minimum number of trades filter"
    ),
    min_win_rate: Optional[float] = typer.Option(
        None, "--min-win-rate", help="Minimum win rate filter (0.0 to 1.0)"
    ),
    years: Optional[int] = typer.Option(
        None,
        "--years",
        "-y",
        help="Number of years of historical data to analyze (omit for complete history)",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview configuration without executing"
    ),
    use_4hour: Optional[bool] = typer.Option(
        None,
        "--use-4hour",
        help="Use 4-hour timeframe data (converted from 1-hour data)",
    ),
    use_2day: Optional[bool] = typer.Option(
        None,
        "--use-2day",
        help="Use 2-day timeframe data (converted from daily data)",
    ),
    market_type: Optional[str] = typer.Option(
        None,
        "--market-type",
        help="Market type: crypto, us_stock, or auto (automatic detection)",
    ),
    direction: Optional[str] = typer.Option(
        None,
        "--direction",
        "-d",
        help="Trading direction: Long or Short (default: Long)",
    ),
    skip_analysis: Optional[bool] = typer.Option(
        None,
        "--skip-analysis",
        help="Skip data download and analysis, assume portfolio files exist in data/raw/portfolios/",
    ),
    fast_min: Optional[int] = typer.Option(
        None, "--fast-min", help="Minimum fast period for analysis"
    ),
    fast_max: Optional[int] = typer.Option(
        None, "--fast-max", help="Maximum fast period for analysis"
    ),
    slow_min: Optional[int] = typer.Option(
        None, "--slow-min", help="Minimum slow period for analysis"
    ),
    slow_max: Optional[int] = typer.Option(
        None, "--slow-max", help="Maximum slow period for analysis"
    ),
    signal_min: Optional[int] = typer.Option(
        None, "--signal-min", help="Minimum signal period for analysis"
    ),
    signal_max: Optional[int] = typer.Option(
        None, "--signal-max", help="Maximum signal period for analysis"
    ),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Filter by entry signals triggered on specific date (YYYYMMDD format, e.g., 20250811). Overrides --current if both specified.",
    ),
    use_current: Optional[bool] = typer.Option(
        None,
        "--use-current",
        help="Filter to only current entry signals (active positions for today). Overridden by --date if both specified.",
    ),
    performance_mode: str = typer.Option(
        "standard",
        "--performance-mode",
        help="Performance monitoring level: minimal (basic timing), standard (phase breakdown + resources), detailed (full profiling + insights), benchmark (compare vs historical)",
    ),
    show_resources: bool = typer.Option(
        False,
        "--show-resources",
        help="Display real-time CPU and memory usage during execution",
    ),
    profile_execution: bool = typer.Option(
        False,
        "--profile-execution",
        help="Enable detailed execution profiling with bottleneck identification",
    ),
    enable_parallel: bool = typer.Option(
        True,
        "--enable-parallel/--disable-parallel",
        help="Enable parallel processing for parameter sweeps (default: enabled)",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Force complete regeneration of all files, bypassing smart resume (default: False)",
    ),
):
    """
    Execute strategy analysis with specified parameters.

    This command runs MA Cross or MACD strategy analysis on the specified
    tickers with the given configuration parameters.

    Examples:
        trading-cli strategy run --profile ma_cross_crypto
        trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA EMA
        trading-cli strategy run --ticker AAPL --ticker MSFT --strategy SMA
        trading-cli strategy run --ticker BTC-USD --min-trades 20
        trading-cli strategy run --ticker BTC-USD,ETH-USD --use-4hour
        trading-cli strategy run --ticker ETH-USD --use-2day
        trading-cli strategy run --profile ma_cross_crypto --skip-analysis
        trading-cli strategy run --ticker IREN --date 20250811
        trading-cli strategy run --ticker AAPL,MSFT --date 20250815 --strategy SMA
    """
    try:
        # Validate date parameter if provided
        if date:
            import re

            # Validate YYYYMMDD format
            if not re.match(r"^\d{8}$", date):
                rprint(
                    "[red]Error: Date must be in YYYYMMDD format (e.g., 20250811)[/red]"
                )
                raise typer.Exit(1)

        # Get global options from context
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False
        global_show_output = ctx.obj.get("show_output", False) if ctx.obj else False
        global_quiet = ctx.obj.get("quiet", False) if ctx.obj else False

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides using shared utility
        overrides = build_configuration_overrides(
            ticker=ticker,
            ticker_2=ticker_2,
            strategy_type=strategy_type,
            min_trades=min_trades,
            min_win_rate=min_win_rate,
            years=years,
            market_type=market_type,
            dry_run=dry_run,
            use_4hour=use_4hour,
            use_2day=use_2day,
            skip_analysis=skip_analysis,
            direction=direction,
            fast_min=fast_min,
            fast_max=fast_max,
            slow_min=slow_min,
            slow_max=slow_max,
            signal_min=signal_min,
            signal_max=signal_max,
            date=date,
            use_current=use_current,
            verbose=global_verbose,
            performance_mode=performance_mode,
            show_resources=show_resources,
            profile_execution=profile_execution,
            enable_parallel=enable_parallel,
            refresh=refresh,
        )

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            # Use default strategy profile
            config = loader.load_from_profile(
                "default_strategy", StrategyConfig, overrides
            )

        # Validate parameter relationships
        validate_parameter_relationships(config)

        if dry_run:
            show_config_preview(config, "Strategy Configuration Preview")
            return

        # Initialize console logger with user preferences and performance options
        # For strategy execution, show rich output unless explicitly quieted
        is_verbose = global_verbose
        is_quiet = global_quiet

        # Always use PerformanceAwareConsoleLogger for strategy execution to ensure
        # consistent progress bar display with parameter combination awareness
        console = PerformanceAwareConsoleLogger(
            verbose=is_verbose,
            quiet=is_quiet,
            performance_mode=performance_mode,
            show_resources=show_resources,
            profile_execution=profile_execution,
        )
        console.start_execution_monitoring("strategy_run")

        if is_verbose:
            console.debug("Loading strategy execution module...")

        # Initialize strategy dispatcher with console logger
        dispatcher = StrategyDispatcher(console=console)

        # Validate strategy compatibility
        if not dispatcher.validate_strategy_compatibility(config.strategy_types):
            console.error("Invalid strategy type configuration")
            return

        # Show execution progress - handle synthetic mode differently
        if config.synthetic.use_synthetic:
            # Synthetic mode: show synthetic ticker name
            synthetic_ticker = (
                f"{config.synthetic.ticker_1}_{config.synthetic.ticker_2}"
            )
            tickers_to_process = [synthetic_ticker]

            console.heading("Strategy Analysis", level=1)

            strategy_types_str = ", ".join(
                [
                    st.value if hasattr(st, "value") else str(st)
                    for st in config.strategy_types
                ]
            )
            console.info(
                f"Processing synthetic pair with {strategy_types_str} strategies: {synthetic_ticker}"
            )
        else:
            # Normal mode: show individual tickers
            if config.ticker is None or (
                isinstance(config.ticker, list) and len(config.ticker) == 0
            ):
                tickers_to_process = []
            else:
                tickers_to_process = (
                    config.ticker
                    if isinstance(config.ticker, list)
                    else [config.ticker]
                )

            console.heading("Strategy Analysis", level=1)

            strategy_types_str = ", ".join(
                [
                    st.value if hasattr(st, "value") else str(st)
                    for st in config.strategy_types
                ]
            )
            ticker_names = ", ".join(tickers_to_process)
            console.info(
                f"Processing {len(tickers_to_process)} tickers with {strategy_types_str} strategies: {ticker_names}"
            )

        # Execute using strategy dispatcher
        # This routes to the appropriate strategy service based on configuration
        execution_summary = dispatcher.execute_strategy(config)

        # Display rich execution summary instead of simple success message
        _display_strategy_summary(execution_summary, console)

        # Complete performance monitoring if enabled
        if isinstance(console, PerformanceAwareConsoleLogger):
            console.complete_execution_monitoring()

    except Exception as e:
        # Create console logger for error handling if not already available
        # For errors, always show output (don't use quiet mode for errors)
        error_console = locals().get("console") or ConsoleLogger(
            verbose=global_verbose, quiet=False
        )
        handle_command_error(e, "strategy run", global_verbose, console=error_console)


@app.command()
def sweep(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: Optional[List[str]] = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Ticker symbols for parameter sweep (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)",
    ),
    fast_min: Optional[int] = typer.Option(
        None, "--fast-min", help="Minimum fast period for sweep"
    ),
    fast_max: Optional[int] = typer.Option(
        None, "--fast-max", help="Maximum fast period for sweep"
    ),
    slow_min: Optional[int] = typer.Option(
        None, "--slow-min", help="Minimum slow period for sweep"
    ),
    slow_max: Optional[int] = typer.Option(
        None, "--slow-max", help="Maximum slow period for sweep"
    ),
    signal_min: Optional[int] = typer.Option(
        None, "--signal-min", help="Minimum signal period for sweep"
    ),
    signal_max: Optional[int] = typer.Option(
        None, "--signal-max", help="Maximum signal period for sweep"
    ),
    max_results: int = typer.Option(
        50, "--max-results", help="Maximum number of results to display"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview sweep parameters without executing"
    ),
):
    """
    Perform parameter sweep analysis for MA Cross strategies.

    This command runs a comprehensive parameter sweep across different
    fast and slow moving average periods to find optimal combinations.
    Supports multiple tickers for comparative analysis.

    Examples:
        trading-cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 200
        trading-cli strategy sweep --ticker AAPL,MSFT,GOOGL --fast-min 10 --fast-max 30 --slow-min 40 --slow-max 80
        trading-cli strategy sweep --profile ma_cross_crypto --max-results 20
    """
    try:
        loader = ConfigLoader()

        # Build configuration overrides using shared utility
        overrides = build_configuration_overrides(
            ticker=ticker,
            fast_min=fast_min,
            fast_max=fast_max,
            slow_min=slow_min,
            slow_max=slow_max,
            signal_min=signal_min,
            signal_max=signal_max,
            dry_run=dry_run,
        )

        # Load configuration (use StrategyConfig instead of MACrossConfig for consistency)
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            # Use default strategy profile
            config = loader.load_from_profile(
                "default_strategy", StrategyConfig, overrides
            )

        # Validate parameter relationships
        validate_parameter_relationships(config)

        if dry_run:
            show_config_preview(config, "Parameter Sweep Preview")
            return

        # Show configuration summary
        ticker_display = (
            ", ".join(config.ticker)
            if isinstance(config.ticker, list)
            else config.ticker
        )
        fast_range_display = config.fast_period_range or (5, 50)
        slow_range_display = config.slow_period_range or (20, 200)

        show_execution_progress("Starting parameter sweep analysis")
        rprint(f"Ticker(s): {ticker_display}")
        rprint(f"Fast period range: {fast_range_display}")
        rprint(f"Slow period range: {slow_range_display}")

        # Import required modules for parameter sweep
        from ...strategies.ma_cross.tools.parameter_sensitivity import (
            analyze_parameter_sensitivity,
        )
        from ...tools.get_data import get_data
        from ...tools.logging_context import logging_context

        with logging_context("cli_parameter_sweep", "parameter_sweep.log") as log:
            # Convert config to legacy format using shared utility
            legacy_config = convert_to_legacy_config(config)

            # Generate parameter combinations with defaults if not specified
            if config.fast_period_range is None or config.slow_period_range is None:
                rprint(
                    "[yellow]Warning: No period ranges specified in profile. Using defaults.[/yellow]"
                )
                rprint(
                    "[dim]For custom ranges, use: --fast-min X --fast-max Y --slow-min Z --slow-max W[/dim]"
                )
                fast_range = config.fast_period_range or (5, 50)
                slow_range = config.slow_period_range or (20, 200)
            else:
                fast_range = config.fast_period_range
                slow_range = config.slow_period_range

            short_windows = list(range(fast_range[0], fast_range[1] + 1))
            long_windows = list(range(slow_range[0], slow_range[1] + 1))

            # Handle multiple tickers
            ticker_list = (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            )

            # Calculate total combinations
            total_combinations = (
                sum(1 for s in short_windows for l in long_windows if s < l)
                * len(config.strategy_types)
                * len(ticker_list)
            )

            show_execution_progress(
                "Executing parameter sweep",
                ticker_count=len(ticker_list),
                combination_count=total_combinations,
            )

            all_results = []

            # Process each ticker individually
            for single_ticker in ticker_list:
                rprint(
                    f"\n[bold]Processing parameter sweep for {single_ticker}...[/bold]"
                )

                # Get price data for single ticker
                rprint(f"Fetching price data for {single_ticker}...")
                data = get_data(single_ticker, legacy_config, log)
                if data is None:
                    rprint(f"[red]Failed to fetch price data for {single_ticker}[/red]")
                    continue

                for strategy_type in config.strategy_types:
                    rprint(
                        f"Running {strategy_type} parameter sweep for {single_ticker}..."
                    )

                    # Set strategy type in legacy config
                    strategy_config = legacy_config.copy()
                    strategy_config["STRATEGY_TYPE"] = strategy_type
                    strategy_config[
                        "TICKER"
                    ] = single_ticker  # Ensure single ticker in config

                    # Run parameter sensitivity analysis
                    results_df = analyze_parameter_sensitivity(
                        data=data,
                        short_windows=short_windows,
                        long_windows=long_windows,
                        config=strategy_config,
                        log=log,
                    )

                    if results_df is not None:
                        # Convert to list of dicts for display
                        strategy_results = results_df.to_dicts()
                        all_results.extend(strategy_results)
                        rprint(
                            f"Found {len(strategy_results)} valid {strategy_type} combinations for {single_ticker}"
                        )

            if all_results:
                # Sort by score and display top results using shared utility
                sorted_results = sorted(
                    all_results, key=lambda x: x.get("Score", 0), reverse=True
                )

                display_sweep_results_table(sorted_results[:max_results])
                rprint(f"\n[green]Parameter sweep completed![/green]")
                rprint(
                    f"Found {len(all_results)} total combinations, showing top {min(max_results, len(sorted_results))}"
                )

                # Show export location
                portfolio_dir = "data/raw/strategies/"
                rprint(f"[dim]Full results exported to: {portfolio_dir}[/dim]")
            else:
                rprint("[yellow]No valid parameter combinations found[/yellow]")

    except Exception as e:
        handle_command_error(e, "strategy sweep", False)


@app.command()
def review(
    ctx: typer.Context,
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: Optional[List[str]] = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Filter analysis to specific ticker symbols (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)",
    ),
    best: bool = typer.Option(
        False, "--best", help="Analyze portfolios_best files specifically"
    ),
    current: bool = typer.Option(
        False,
        "--current",
        help="Analyze current day signals from date-specific directory",
    ),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        help="Analyze signals from specific date directory (YYYYMMDD format, e.g., 20250816). Overrides --current flag.",
    ),
    top_n: int = typer.Option(
        50, "--top-n", "-n", help="Number of top results to display in table"
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format",
        "-f",
        help="Output format: table (with raw CSV) or raw (CSV only)",
    ),
    sort_by: str = typer.Option(
        "Score", "--sort-by", "-s", help="Column to sort by (default: Score)"
    ),
):
    """
    Analyze and aggregate portfolio data from CSV files (dry-run analysis).

    This command aggregates portfolio data for tickers defined in a profile,
    removes the Metric Type column, sorts the results, and displays them
    in both table format and raw CSV format ready for copy/paste.

    Examples:
        trading-cli strategy review --profile asia_top_50 --best
        trading-cli strategy review --profile asia_top_50 --best --current
        trading-cli strategy review --profile asia_top_50 --best --date 20250816
        trading-cli strategy review --profile asia_top_50 --best --date 20250816 --top-n 25
        trading-cli strategy review --profile asia_top_50 --best --output-format raw
        trading-cli strategy review --profile asia_top_50 --best --sort-by "Total Return [%]"
        trading-cli strategy review --best --current --ticker AAPL,MSFT,GOOGL
        trading-cli strategy review --best --date 20250816 --ticker AAPL,MSFT,GOOGL
        trading-cli strategy review --profile asia_top_50 --best --ticker TAL,META,SYF
    """
    try:
        # Get global options from context
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Validate date parameter if provided
        if date:
            import re
            from pathlib import Path

            # Validate YYYYMMDD format
            if not re.match(r"^\d{8}$", date):
                rprint(
                    "[red]Error: Date must be in YYYYMMDD format (e.g., 20250816)[/red]"
                )
                raise typer.Exit(1)

            # Check if date directory exists
            date_dir = (
                Path("/Users/colemorton/Projects/trading/data/raw/portfolios_best")
                / date
            )
            if not date_dir.exists():
                rprint(f"[red]Error: Date directory not found: {date_dir}[/red]")
                rprint(
                    f"[dim]Available date directories can be found in data/raw/portfolios_best/[/dim]"
                )
                raise typer.Exit(1)

            # Override current flag if date is specified
            if current and global_verbose:
                rprint("[dim]Date parameter specified, overriding --current flag[/dim]")
            current = True  # Enable date-specific search

        # Process ticker input if provided
        if ticker:
            from .strategy_utils import process_ticker_input

            ticker_list = process_ticker_input(ticker)
            ticker_filtering_active = True

            if global_verbose:
                rprint(
                    f"[dim]Ticker filtering enabled with {len(ticker_list)} tickers: {', '.join(ticker_list)}[/dim]"
                )
        else:
            ticker_filtering_active = False

        # Allow auto-discovery mode when both --best and --current are provided
        if not profile and not (best and current) and not ticker_filtering_active:
            rprint(
                "[red]Error: --profile is required unless using --best --current for auto-discovery or --ticker for filtering[/red]"
            )
            rprint("[dim]Examples:[/dim]")
            rprint(
                "[dim]  Profile mode: trading-cli strategy review --profile asia_top_50 --best[/dim]"
            )
            rprint(
                "[dim]  Auto-discovery: trading-cli strategy review --best --current[/dim]"
            )
            rprint(
                "[dim]  Ticker filtering: trading-cli strategy review --best --current --ticker AAPL,MSFT[/dim]"
            )
            raise typer.Exit(1)

        if not best:
            rprint(
                "[red]Error: --best flag is required (only portfolios_best analysis is currently supported)[/red]"
            )
            rprint(
                "[dim]Example: trading-cli strategy review --profile asia_top_50 --best[/dim]"
            )
            raise typer.Exit(1)

        # Handle profile loading vs auto-discovery mode vs ticker filtering
        if ticker_filtering_active:
            # Ticker filtering mode - use provided ticker list regardless of profile
            if global_verbose:
                rprint(
                    f"[dim]Ticker filtering mode: analyzing {len(ticker_list)} specific tickers[/dim]"
                )
        elif profile:
            # Profile-based mode
            loader = ConfigLoader()

            try:
                config = loader.load_from_profile(profile, StrategyConfig, {})
            except Exception as e:
                rprint(f"[red]Error loading profile '{profile}': {e}[/red]")
                raise typer.Exit(1)

            # Get ticker list from config
            ticker_list = (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            )

            if global_verbose:
                rprint(
                    f"[dim]Loaded profile '{profile}' with {len(ticker_list)} tickers[/dim]"
                )
        else:
            # Auto-discovery mode (profile is None, best=True, current=True)
            ticker_list = ["Auto-discovered"]  # For display purposes

            if global_verbose:
                rprint(
                    f"[dim]Auto-discovery mode enabled - will scan current day directory[/dim]"
                )

        # Display configuration
        rprint("\n[bold cyan]📊 Portfolio Analysis Configuration:[/bold cyan]")
        rprint("=" * 50)

        # Show mode and profile information
        if ticker_filtering_active:
            if profile:
                rprint(f"📋 [white]Mode: Ticker Filtering (Profile: {profile})[/white]")
            else:
                rprint(f"📋 [white]Mode: Ticker Filtering[/white]")
        elif profile:
            rprint(f"📋 [white]Profile: {profile}[/white]")
        else:
            rprint(f"📋 [white]Mode: Auto-Discovery[/white]")

        # Show analysis type with date if applicable
        from datetime import datetime

        if current:
            # Use custom date if specified, otherwise current date
            display_date = date if date else datetime.now().strftime("%Y%m%d")
            date_label = f"date: {display_date}" if date else f"current: {display_date}"

            if ticker_filtering_active:
                rprint(
                    f"📊 [white]Analysis Type: portfolios_best ({date_label}, filtered)[/white]"
                )
            elif profile:
                rprint(
                    f"📊 [white]Analysis Type: portfolios_best ({date_label})[/white]"
                )
            else:
                rprint(
                    f"📊 [white]Analysis Type: portfolios_best ({date_label}, auto-discovery)[/white]"
                )
        else:
            rprint(f"📊 [white]Analysis Type: portfolios_best[/white]")

        # Show tickers
        if ticker_filtering_active:
            rprint(
                f"🎯 [white]Tickers: Filtered to {len(ticker_list)} tickers: {', '.join(ticker_list)}[/white]"
            )
        elif profile:
            rprint(f"🎯 [white]Tickers: {', '.join(ticker_list)}[/white]")
        else:
            rprint(f"🎯 [white]Tickers: Auto-discovered from current day files[/white]")

        rprint(f"📈 [white]Display: Top {top_n} results[/white]")
        rprint(f"🔢 [white]Sort By: {sort_by}[/white]")
        rprint()

        # Initialize analysis service
        from ..services.portfolio_analysis_service import PortfolioAnalysisService

        analysis_service = PortfolioAnalysisService(
            use_current=current, custom_date=date
        )

        # Aggregate portfolio data
        rprint("[bold]🔍 Searching for portfolio files...[/bold]")

        if ticker_filtering_active:
            # Ticker filtering mode - always use specific ticker list
            combined_df = analysis_service.aggregate_portfolios_best(ticker_list)
        elif profile:
            # Profile-based analysis
            combined_df = analysis_service.aggregate_portfolios_best(ticker_list)
        else:
            # Auto-discovery analysis
            combined_df = analysis_service.aggregate_all_current_portfolios()

        if combined_df.empty:
            rprint(
                "[yellow]❌ No portfolio data found for the specified tickers[/yellow]"
            )
            rprint(
                "[dim]Make sure portfolios_best files exist in data/raw/portfolios_best/[/dim]"
            )
            raise typer.Exit(1)

        # Remove Metric Type column and sort
        rprint(f"[bold]📝 Processing {len(combined_df)} portfolios...[/bold]")
        processed_df = analysis_service.remove_metric_type_column(combined_df)
        sorted_df = analysis_service.sort_portfolios(processed_df, sort_by=sort_by)

        # Format for display
        display_data = analysis_service.format_for_display(sorted_df, top_n=top_n)

        if output_format == "raw":
            # Raw CSV output only
            rprint("\n[bold cyan]📋 Portfolio Entry Signals: Raw CSV Data:[/bold cyan]")
            csv_output = analysis_service.generate_csv_output(
                display_data["all_results"]
            )
            rprint(csv_output)
        else:
            # Table format with raw CSV
            _display_portfolio_table(
                display_data["top_results"], analysis_service.get_display_columns()
            )

            # Summary statistics
            stats = display_data["stats"]
            rprint(f"\n[bold green]✨ Analysis Complete![/bold green]")
            rprint(
                f"📈 [cyan]{stats['total_portfolios']} portfolios analyzed successfully[/cyan]"
            )

            if stats["total_portfolios"] > 0:
                rprint(f"\n💡 [bold yellow]Key Insights:[/bold yellow]")
                rprint(
                    f"🏆 [white]Best Opportunity: {stats['best_ticker']} ({stats['best_return']:+.2f}%)[/white]"
                )
                rprint(f"📊 [white]Average Score: {stats['avg_score']:.3f}[/white]")
                rprint(
                    f"🎯 [white]Win Rate Range: {stats['win_rate_range'][0]:.1f}% - {stats['win_rate_range'][1]:.1f}%[/white]"
                )

            # Raw CSV output section
            rprint(f"\n[bold cyan]📋 Portfolio Entry Signals: Raw CSV Data:[/bold cyan]")
            csv_output = analysis_service.generate_csv_output(
                display_data["all_results"]
            )

            # Use print() instead of rprint() to avoid Rich's line wrapping
            # Each CSV line should be displayed as one complete line for proper copy/paste
            csv_lines = csv_output.split("\n")
            for line in csv_lines:
                print(line)  # Plain print without Rich formatting/wrapping

    except Exception as e:
        handle_command_error(e, "strategy review", global_verbose)


def _display_portfolio_table(df, display_columns):
    """Display portfolio analysis results in a formatted table."""
    if df.empty:
        rprint("[yellow]No data to display[/yellow]")
        return

    table = Table(
        title="📊 Top Portfolio Analysis Results",
        show_header=True,
        header_style="bold magenta",
    )

    # Add rank column
    table.add_column("Rank", style="cyan", no_wrap=True, justify="center")

    # Add columns that exist in the dataframe
    available_columns = []
    for col in display_columns:
        if col in df.columns:
            available_columns.append(col)

            # Customize column styling based on content
            if "Rate" in col or "%" in col:
                table.add_column(col, style="yellow", justify="right")
            elif "Return" in col:
                table.add_column(col, style="green", justify="right")
            elif "Score" in col or "Ratio" in col:
                table.add_column(col, style="white", justify="right")
            elif "Drawdown" in col:
                table.add_column(col, style="red", justify="right")
            elif "Ticker" in col:
                table.add_column(col, style="bold white", no_wrap=True)
            else:
                table.add_column(col, style="blue")

    # Add rows to table
    for idx, (_, row) in enumerate(df.head(50).iterrows(), 1):
        row_data = [str(idx)]  # Rank

        for col in available_columns:
            value = row[col]

            # Format specific column types
            if col == "Win Rate [%]" and pd.notna(value):
                try:
                    row_data.append(f"{float(value):.1f}%")
                except:
                    row_data.append(str(value))
            elif "Return" in col and pd.notna(value):
                try:
                    color = "green" if float(value) > 0 else "red"
                    row_data.append(f"[{color}]{float(value):+.2f}%[/{color}]")
                except:
                    row_data.append(str(value))
            elif col == "Max Drawdown [%]" and pd.notna(value):
                try:
                    row_data.append(f"[red]{float(value):.2f}%[/red]")
                except:
                    row_data.append(str(value))
            elif col in [
                "Score",
                "Sharpe Ratio",
                "Profit Factor",
                "Expectancy per Trade",
                "Sortino Ratio",
            ] and pd.notna(value):
                try:
                    row_data.append(f"{float(value):.3f}")
                except:
                    row_data.append(str(value))
            else:
                row_data.append(str(value) if pd.notna(value) else "N/A")

        table.add_row(*row_data)

    console.print(table)


def _display_strategy_summary(
    summary: StrategyExecutionSummary, console: ConsoleLogger
) -> None:
    """Display rich strategy execution summary similar to seasonality command."""
    # Use enhanced completion banner if available
    if hasattr(console, "completion_banner"):
        console.completion_banner("Strategy Analysis Complete!")
    else:
        console.heading("Strategy Analysis Complete!", level=1)

    # Basic execution statistics
    ticker_count = len(summary.tickers_processed)
    strategy_types_str = ", ".join(summary.strategy_types)

    if ticker_count == 1:
        console.success(
            f"{ticker_count} ticker analyzed successfully ({', '.join(summary.tickers_processed)})"
        )
    else:
        console.success(f"{ticker_count} tickers analyzed successfully")

    if len(summary.strategy_types) > 1:
        console.info(f"Strategies: {strategy_types_str}")

    # Portfolio Analysis Results section
    if summary.portfolio_results:
        # Use enhanced results summary table if available
        if hasattr(console, "results_summary_table"):
            best_config = None
            if summary.best_opportunity and summary.best_opportunity.best_config:
                best = summary.best_opportunity
                best_config = f"{best.strategy_type} {best.best_config}"

            console.results_summary_table(
                portfolios_generated=summary.total_portfolios_generated,
                best_config=best_config,
                files_exported=summary.total_files_exported,
            )
        else:
            # Fallback to basic display
            console.heading("Portfolio Analysis Results", level=2)

            # Show aggregated statistics
            console.info(
                f"Generated: {summary.total_portfolios_generated:,} portfolios"
            )

            if summary.total_filtered_portfolios > 0:
                pass_rate = summary.filter_pass_rate * 100
                console.info(
                    f"Filtered: {summary.total_filtered_portfolios:,} portfolios ({pass_rate:.1f}% pass rate)"
                )

            # Show best configuration if available
            if summary.best_opportunity:
                best = summary.best_opportunity
                if best.best_config:
                    config_info = f"Optimal: {best.strategy_type} {best.best_config}"
                    if best.best_score:
                        config_info += f" (Score: {best.best_score:.3f})"
                    console.success(config_info)

    # Files Generated section
    if summary.total_files_exported > 0:
        console.heading("Files Generated", level=2)

        # Group files by type for better display
        file_types = {
            "portfolios": [],
            "portfolios_filtered": [],
            "portfolios_metrics": [],
            "portfolios_best": [],
        }

        for result in summary.portfolio_results:
            for file_path in result.files_exported:
                file_name = file_path.split("/")[-1]  # Get just the filename

                if "/portfolios_filtered/" in file_path:
                    file_types["portfolios_filtered"].append(
                        f"{file_name} ({result.filtered_portfolios} rows)"
                    )
                elif "/portfolios_metrics/" in file_path:
                    file_types["portfolios_metrics"].append(f"{file_name} (metrics)")
                elif "/portfolios_best/" in file_path:
                    file_types["portfolios_best"].append(f"{file_name} (best)")
                elif "/portfolios/" in file_path:
                    file_types["portfolios"].append(
                        f"{file_name} ({result.total_portfolios} rows)"
                    )

        # Display files by type with appropriate emojis
        if file_types["portfolios"]:
            console.success(f"Raw portfolios: {', '.join(file_types['portfolios'])}")
        if file_types["portfolios_filtered"]:
            console.success(f"Filtered: {', '.join(file_types['portfolios_filtered'])}")
        if file_types["portfolios_metrics"]:
            console.success(f"Metrics: {', '.join(file_types['portfolios_metrics'])}")
        if file_types["portfolios_best"]:
            console.success(f"Best: {', '.join(file_types['portfolios_best'])}")

    # Key Insights section
    console.heading("Key Insights", level=3)

    if summary.best_opportunity:
        best = summary.best_opportunity
        strategy_display = f"{best.strategy_type}"
        if best.best_config:
            strategy_display += f" {best.best_config}"

        # Add performance metrics if available
        performance_parts = []
        if best.win_rate:
            performance_parts.append(f"Win Rate: {best.win_rate:.1%}")
        if best.best_score:
            performance_parts.append(f"Score: {best.best_score:.3f}")

        best_info = f"Best Strategy: {strategy_display}"
        if performance_parts:
            best_info += f" ({', '.join(performance_parts)})"

        console.success(best_info)

        # Show trade performance if available
        if best.avg_win and best.avg_loss:
            console.info(
                f"Trade Performance: +{best.avg_win:.2f}% avg win vs -{abs(best.avg_loss):.2f}% avg loss"
            )

    # Execution performance
    if summary.execution_time > 60:
        time_display = f"{summary.execution_time/60:.1f} minutes"
    else:
        time_display = f"{summary.execution_time:.1f} seconds"

    console.info(f"Execution Time: {time_display}")

    if summary.total_strategies > 1:
        success_rate_pct = summary.success_rate * 100
        console.info(
            f"Success Rate: {success_rate_pct:.0f}% ({summary.successful_strategies}/{summary.total_strategies} strategies)"
        )


@app.command()
def sector_compare(
    format: str = typer.Option(
        "table", "--format", "-f", help="Output format: table, json, csv"
    ),
    export: Optional[str] = typer.Option(
        None, "--export", "-e", help="Export results to file"
    ),
    date: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Specific date in YYYYMMDD format (default: latest available)",
    ),
    list_dates: bool = typer.Option(
        False, "--list-dates", help="List available dates and exit"
    ),
    explain_columns: bool = typer.Option(
        False, "--explain-columns", help="Explain all column meanings and exit"
    ),
    vs_benchmark: Optional[str] = typer.Option(
        None,
        "--vs-benchmark",
        help="Compare against benchmark (SPY, BTC-USD, or any ticker)",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Force regeneration of sector data (equivalent to: trading-cli strategy run -p sectors_current --refresh)",
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """
    Compare sector ETF performance using SMA strategy scores.

    Generates a cross-comparison matrix of all 11 sector ETFs (XLK, XLY, etc.)
    ranked by their best SMA Score values across all parameter combinations.
    """
    from pathlib import Path

    from app.tools.sector_comparison import SectorComparisonEngine

    from .strategy_utils import display_sector_comparison_table

    try:
        console = Console()

        # Smart data refresh logic (only when not using specific date)
        if not date:  # Only auto-refresh for current/latest data
            temp_engine = SectorComparisonEngine()

            if temp_engine.needs_data_refresh(force_refresh=refresh):
                console.print("[yellow]Generating sector data...[/yellow]")

                try:
                    # Execute sectors_current profile to generate/refresh data
                    loader = ConfigLoader()

                    # Build overrides with refresh flag
                    overrides = {"refresh": refresh} if refresh else {}

                    # Load sectors_current profile
                    profile_config = loader.load_from_profile(
                        "sectors_current", StrategyConfig, overrides
                    )

                    # Execute strategy with existing StrategyDispatcher
                    console.print(
                        "[dim]Running: trading-cli strategy run -p sectors_current"
                        + (" --refresh" if refresh else "")
                        + "[/dim]"
                    )

                    # Initialize strategy dispatcher with console logger
                    console_logger = ConsoleLogger()
                    dispatcher = StrategyDispatcher(console=console_logger)

                    # Validate strategy compatibility
                    if not dispatcher.validate_strategy_compatibility(
                        profile_config.strategy_types
                    ):
                        console.print(
                            "[red]✗[/red] Invalid strategy configuration in sectors_current profile"
                        )
                        console.print(
                            "[yellow]Continuing with existing data...[/yellow]"
                        )
                    else:
                        # Execute the strategy
                        dispatcher.execute_strategy(profile_config)
                        console.print(
                            "[green]✓[/green] Sector data generated successfully"
                        )

                except Exception as e:
                    console.print(
                        f"[red]✗[/red] Error during sector data generation: {str(e)}"
                    )
                    console.print("[yellow]Continuing with existing data...[/yellow]")
                    if verbose:
                        console.print(f"[red]Full error: {str(e)}[/red]")

        # Initialize sector comparison engine
        engine = SectorComparisonEngine(date=date, benchmark_ticker=vs_benchmark)

        # Handle list-dates option
        if list_dates:
            available_dates = engine.get_available_dates()
            if available_dates:
                console.print("[cyan]Available dates in portfolios_best:[/cyan]")
                for date_str in available_dates:
                    console.print(f"  • {date_str}")
            else:
                console.print(
                    "[yellow]No dated directories found in portfolios_best[/yellow]"
                )
                console.print(
                    "[dim]Run 'trading-cli strategy run -p sectors_current' to generate data[/dim]"
                )
            return

        # Handle explain-columns option
        if explain_columns:
            console.print(
                "[bold cyan]🔍 Sector Comparison Table - Column Explanations:[/bold cyan]\n"
            )

            explanations = [
                ("Rank", "Overall ranking based on Score (1 = highest score)"),
                ("Sector", "ETF ticker symbol for the sector"),
                ("Name", "Full sector name (e.g., Technology, Healthcare)"),
                (
                    "Score",
                    "Composite performance metric: Win Rate ×2.5 + Total Trades ×1.5 + Sortino ×1.2 + Profit Factor ×1.2 + Expectancy ×1.0 + Beats BNH ×0.6",
                ),
                (
                    "vs Top",
                    "Percentage relative to top-ranked sector: (sector_score / top_score) × 100%",
                ),
                (
                    "SMA",
                    "Optimal Simple Moving Average window combination (Fast/Slow periods)",
                ),
                (
                    "Win Rate",
                    "Percentage of profitable trades for the optimal strategy",
                ),
                ("Return", "Total return percentage for the optimal strategy"),
                ("Max DD", "Maximum drawdown percentage (worst peak-to-trough loss)"),
                ("Sharpe", "Risk-adjusted return metric (higher = better risk/reward)"),
                (
                    "P.Factor",
                    "Profit Factor: Gross profit divided by gross loss (>1.0 = profitable)",
                ),
                ("Trades", "Total number of trades executed by the optimal strategy"),
                ("Risk Level", "Color-coded risk assessment based on Max Drawdown:"),
            ]

            for label, description in explanations:
                if label == "Risk Level":
                    console.print(f"• [bold white]{label}:[/bold white] {description}")
                    console.print("    [green]• Low Risk: <10% Max Drawdown[/green]")
                    console.print(
                        "    [yellow]• Medium Risk: 10-20% Max Drawdown[/yellow]"
                    )
                    console.print("    [red]• High Risk: >20% Max Drawdown[/red]")
                else:
                    console.print(f"• [bold white]{label}:[/bold white] {description}")

            console.print(f"\n[bold yellow]💡 Key Insights:[/bold yellow]")
            console.print(
                "• Higher Score values indicate better overall strategy performance"
            )
            console.print(
                "• 'vs Top' shows relative performance - 100% = best performing sector"
            )
            console.print(
                "• Consider both Score and Max Drawdown for risk-adjusted decisions"
            )
            console.print("• Win Rate and Profit Factor validate strategy consistency")
            console.print(
                "• Minimum 44+ trades recommended for statistical significance"
            )
            return

        if verbose:
            target_date = engine.resolve_target_date()
            if target_date:
                console.print(
                    f"[dim]Loading sector ETF data for date: {target_date}[/dim]"
                )
            else:
                console.print(
                    "[dim]Loading sector ETF data from fallback directory[/dim]"
                )

        # Generate comparison matrix
        comparison_data = engine.generate_comparison_matrix()

        if not comparison_data:
            console.print("[red]No sector data found.[/red]")
            console.print(
                "[yellow]First run: trading-cli strategy run -p sectors_current[/yellow]"
            )
            available_dates = engine.get_available_dates()
            if available_dates:
                console.print(
                    f"[dim]Or try a specific date: --date {available_dates[0]}[/dim]"
                )
            return

        # Display results based on format
        if format == "table":
            display_sector_comparison_table(
                comparison_data, console, engine.benchmark_data
            )
        elif format == "json":
            import json

            console.print(json.dumps(comparison_data, indent=2))
        elif format == "csv":
            import pandas as pd

            df = pd.DataFrame(comparison_data)
            console.print(df.to_csv(index=False))
        else:
            console.print(
                f"[red]Unknown format: {format}. Use: table, json, or csv[/red]"
            )
            return

        # Export if requested
        if export:
            export_path = Path(export)
            if format == "json" or export_path.suffix == ".json":
                success = engine.export_to_json(comparison_data, export)
            elif format == "csv" or export_path.suffix == ".csv":
                success = engine.export_to_csv(comparison_data, export)
            else:
                # Default to JSON
                success = engine.export_to_json(comparison_data, export)

            if success:
                console.print(f"[green]Results exported to: {export}[/green]")
            else:
                console.print(f"[red]Failed to export results to: {export}[/red]")

        if verbose:
            console.print(f"[dim]Analyzed {len(comparison_data)} sectors[/dim]")

    except Exception as e:
        handle_command_error(e, "strategy sector-compare", verbose)
