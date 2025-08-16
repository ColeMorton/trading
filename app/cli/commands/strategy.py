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

from ..config import ConfigLoader
from ..models.strategy import MACDConfig, MACrossConfig, MarketType, StrategyConfig
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
        help="Strategy types: SMA, EMA, MACD (can be used multiple times)",
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
    market_type: Optional[str] = typer.Option(
        None,
        "--market-type",
        help="Market type: crypto, us_stock, or auto (automatic detection)",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
    skip_analysis: Optional[bool] = typer.Option(
        None,
        "--skip-analysis",
        help="Skip data download and analysis, assume portfolio files exist in data/raw/portfolios/",
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
        trading-cli strategy run --profile ma_cross_crypto --skip-analysis
    """
    try:
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
            skip_analysis=skip_analysis,
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

        if verbose:
            rprint("[dim]Loading strategy execution module...[/dim]")

        # Initialize strategy dispatcher
        dispatcher = StrategyDispatcher()

        # Validate strategy compatibility
        if not dispatcher.validate_strategy_compatibility(config.strategy_types):
            rprint("[red]Invalid strategy type configuration[/red]")
            return

        # Show execution progress - handle synthetic mode differently
        if config.synthetic.use_synthetic:
            # Synthetic mode: show synthetic ticker name
            synthetic_ticker = (
                f"{config.synthetic.ticker_1}_{config.synthetic.ticker_2}"
            )
            tickers_to_process = [synthetic_ticker]
            show_execution_progress(
                "Executing synthetic ticker analysis", ticker_count=1
            )

            strategy_types_str = ", ".join(
                [
                    st.value if hasattr(st, "value") else str(st)
                    for st in config.strategy_types
                ]
            )
            rprint(
                f"[bold]Processing synthetic pair with {strategy_types_str} strategies:[/bold] {synthetic_ticker}"
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
            show_execution_progress(
                "Executing strategy analysis", ticker_count=len(tickers_to_process)
            )

            strategy_types_str = ", ".join(
                [
                    st.value if hasattr(st, "value") else str(st)
                    for st in config.strategy_types
                ]
            )
            rprint(
                f"[bold]Processing {len(tickers_to_process)} tickers with {strategy_types_str} strategies:[/bold] {', '.join(tickers_to_process)}"
            )

        # Execute using strategy dispatcher
        # This routes to the appropriate strategy service based on configuration
        success = dispatcher.execute_strategy(config)

        if success:
            rprint(f"[green]Strategy analysis completed successfully![/green]")
        else:
            rprint(
                "[yellow]No strategies found matching the specified criteria[/yellow]"
            )

    except Exception as e:
        handle_command_error(e, "strategy run", verbose)


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
        handle_command_error(e, "strategy sweep", verbose=False)


@app.command()
def analyze(
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
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Analyze and aggregate portfolio data from CSV files (dry-run analysis).

    This command aggregates portfolio data for tickers defined in a profile,
    removes the Metric Type column, sorts the results, and displays them
    in both table format and raw CSV format ready for copy/paste.

    Examples:
        trading-cli strategy analyze --profile asia_top_50 --best
        trading-cli strategy analyze --profile asia_top_50 --best --current
        trading-cli strategy analyze --profile asia_top_50 --best --current --top-n 25
        trading-cli strategy analyze --profile asia_top_50 --best --output-format raw
        trading-cli strategy analyze --profile asia_top_50 --best --sort-by "Total Return [%]"
        trading-cli strategy analyze --best --current --ticker AAPL,MSFT,GOOGL
        trading-cli strategy analyze --profile asia_top_50 --best --ticker TAL,META,SYF
    """
    try:
        # Process ticker input if provided
        if ticker:
            from .strategy_utils import process_ticker_input

            ticker_list = process_ticker_input(ticker)
            ticker_filtering_active = True

            if verbose:
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
                "[dim]  Profile mode: trading-cli strategy analyze --profile asia_top_50 --best[/dim]"
            )
            rprint(
                "[dim]  Auto-discovery: trading-cli strategy analyze --best --current[/dim]"
            )
            rprint(
                "[dim]  Ticker filtering: trading-cli strategy analyze --best --current --ticker AAPL,MSFT[/dim]"
            )
            raise typer.Exit(1)

        if not best:
            rprint(
                "[red]Error: --best flag is required (only portfolios_best analysis is currently supported)[/red]"
            )
            rprint(
                "[dim]Example: trading-cli strategy analyze --profile asia_top_50 --best[/dim]"
            )
            raise typer.Exit(1)

        # Handle profile loading vs auto-discovery mode vs ticker filtering
        if ticker_filtering_active:
            # Ticker filtering mode - use provided ticker list regardless of profile
            if verbose:
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

            if verbose:
                rprint(
                    f"[dim]Loaded profile '{profile}' with {len(ticker_list)} tickers[/dim]"
                )
        else:
            # Auto-discovery mode (profile is None, best=True, current=True)
            ticker_list = ["Auto-discovered"]  # For display purposes

            if verbose:
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

        # Show analysis type with current date if applicable
        from datetime import datetime

        if current:
            current_date = datetime.now().strftime("%Y%m%d")
            if ticker_filtering_active:
                rprint(
                    f"📊 [white]Analysis Type: portfolios_best (current: {current_date}, filtered)[/white]"
                )
            elif profile:
                rprint(
                    f"📊 [white]Analysis Type: portfolios_best (current: {current_date})[/white]"
                )
            else:
                rprint(
                    f"📊 [white]Analysis Type: portfolios_best (current: {current_date}, auto-discovery)[/white]"
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

        analysis_service = PortfolioAnalysisService(use_current=current)

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
            rprint("\n[bold cyan]📋 Raw CSV Data (Ready for Copy/Paste):[/bold cyan]")
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
            rprint(f"\n[bold cyan]📋 Raw CSV Data (Ready for Copy/Paste):[/bold cyan]")
            csv_output = analysis_service.generate_csv_output(
                display_data["all_results"]
            )

            # Use print() instead of rprint() to avoid Rich's line wrapping
            # Each CSV line should be displayed as one complete line for proper copy/paste
            csv_lines = csv_output.split("\n")
            for line in csv_lines:
                print(line)  # Plain print without Rich formatting/wrapping

    except Exception as e:
        handle_command_error(e, "strategy analyze", verbose)


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
