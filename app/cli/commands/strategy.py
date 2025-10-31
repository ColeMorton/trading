"""
Strategy command implementations.

This module provides CLI commands for executing and analyzing MA Cross
and MACD strategies with various configuration options.
"""

import builtins
import contextlib
from pathlib import Path

import pandas as pd
import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from app.tools.console_logging import ConsoleLogger, PerformanceAwareConsoleLogger
from app.tools.portfolio.csv_generators import generate_csv_output_for_portfolios

from ..config import ConfigLoader
from ..models.strategy import (
    StrategyConfig,
    StrategyExecutionSummary,
    StrategyPortfolioResults,
)
from ..services import StrategyDispatcher
from .strategy_utils import (
    build_configuration_overrides,
    handle_command_error,
    show_config_preview,
    validate_parameter_relationships,
)


# Create strategy sub-app
app = typer.Typer(
    name="strategy",
    help="Execute and analyze trading strategies",
    no_args_is_help=True,
)

console = Console()


@app.command()
def run(
    ticker: str = typer.Argument(
        ...,
        help="Single ticker symbol to test (e.g., AAPL, BTC-USD)",
    ),
    fast: int | None = typer.Option(
        None, "--fast", "-f", help="Fast moving average period"
    ),
    slow: int | None = typer.Option(
        None, "--slow", "-s", help="Slow moving average period"
    ),
    signal: int | None = typer.Option(
        None,
        "--signal",
        help="Signal period (for MACD strategies only)",
    ),
    strategy: str = typer.Option(
        "SMA",
        "--strategy",
        help="Strategy type: SMA, EMA, or MACD",
    ),
    comp: bool = typer.Option(
        False,
        "--comp",
        "-c",
        help="Use COMP (compound) strategy - aggregates all strategies from ticker CSV",
    ),
    years: int | None = typer.Option(
        None,
        "--years",
        "-y",
        help="Number of years of historical data",
    ),
    use_4hour: bool = typer.Option(False, "--use-4hour", help="Use 4-hour timeframe"),
    use_2day: bool = typer.Option(False, "--use-2day", help="Use 2-day timeframe"),
    market_type: str | None = typer.Option(
        None,
        "--market-type",
        help="Market type: crypto, us_stock, or auto",
    ),
    direction: str = typer.Option(
        "Long",
        "--direction",
        "-d",
        help="Trading direction: Long or Short",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview configuration without executing",
    ),
):
    """
    Test a specific parameter combination on a single ticker.

    This command runs a backtest for a single set of parameters and displays
    the results in the terminal without creating any files. Use this to quickly
    test specific parameter combinations before running a full sweep.

    Examples:
        trading-cli strategy run AAPL --fast 20 --slow 50
        trading-cli strategy run BTC-USD --fast 10 --slow 30 --strategy EMA
        trading-cli strategy run AAPL --fast 12 --slow 26 --signal 9 --strategy MACD
        trading-cli strategy run ETH-USD --fast 15 --slow 45 --use-4hour
        trading-cli strategy run TSLA --fast 20 --slow 50 --years 3
        trading-cli strategy run BTC-USD --comp
    """
    try:
        # Handle COMP strategy mode
        if comp:
            strategy = "COMP"
            rprint(
                "\n[bold cyan]COMP Strategy - Compound Strategy Backtest[/bold cyan]",
            )
            rprint(f"[cyan]Ticker:[/cyan] {ticker}")
            rprint("[cyan]Strategy:[/cyan] COMP (Compound)")
            rprint(
                f"[cyan]Component Strategies:[/cyan] Loaded from data/raw/strategies/{ticker}.csv",
            )
            rprint(f"[cyan]Direction:[/cyan] {direction}")
            if years:
                rprint(f"[cyan]History:[/cyan] {years} years")
            if use_4hour:
                rprint("[cyan]Timeframe:[/cyan] 4-hour")
            elif use_2day:
                rprint("[cyan]Timeframe:[/cyan] 2-day")
            rprint("")

            if dry_run:
                rprint("[yellow]Dry run - configuration preview only[/yellow]")
                return

            # Execute COMP strategy directly
            from ...strategies.comp.strategy import run as comp_run
            from ...tools.get_config import get_config
            from ...tools.project_utils import get_project_root

            config = {
                "TICKER": ticker,
                "STRATEGY_TYPE": "COMP",
                "DIRECTION": direction,
                "USE_HOURLY": use_4hour,
                "USE_4HOUR": use_4hour,
                "USE_2DAY": use_2day,
                "BASE_DIR": get_project_root(),
                "REFRESH": True,
            }

            if years:
                config["USE_YEARS"] = True
                config["YEARS"] = years

            if market_type:
                config["MARKET_TYPE"] = market_type

            # Apply config defaults
            ticker_config = get_config(config)

            # Run COMP strategy
            rprint("Executing COMP strategy...")
            success = comp_run(ticker_config)

            if success:
                rprint("[green]✓ COMP strategy completed successfully[/green]")
                output_file = f"{get_project_root()}/data/outputs/compound/{ticker}.csv"
                rprint(f"[cyan]Results saved to:[/cyan] {output_file}")
            else:
                rprint("[red]✗ COMP strategy execution failed[/red]")
                raise typer.Exit(1)

            return

        # Validate parameters for non-COMP strategies
        if fast is None or slow is None:
            rprint(
                "[red]Error: --fast and --slow parameters are required (unless using --comp)[/red]",
            )
            raise typer.Exit(1)

        if fast >= slow:
            rprint("[red]Error: Fast period must be less than slow period[/red]")
            raise typer.Exit(1)

        if strategy.upper() == "MACD" and signal is None:
            rprint("[red]Error: MACD strategy requires --signal parameter[/red]")
            raise typer.Exit(1)

        # Show configuration
        rprint("\n[bold cyan]Strategy Backtest - Single Parameter Test[/bold cyan]")
        rprint(f"[cyan]Ticker:[/cyan] {ticker}")
        rprint(f"[cyan]Strategy:[/cyan] {strategy.upper()}")
        rprint(
            f"[cyan]Parameters:[/cyan] Fast={fast}, Slow={slow}"
            + (f", Signal={signal}" if signal else ""),
        )
        rprint(f"[cyan]Direction:[/cyan] {direction}")
        if years:
            rprint(f"[cyan]History:[/cyan] {years} years")
        if use_4hour:
            rprint("[cyan]Timeframe:[/cyan] 4-hour")
        elif use_2day:
            rprint("[cyan]Timeframe:[/cyan] 2-day")
        rprint("")

        if dry_run:
            rprint("[yellow]Dry run - configuration preview only[/yellow]")
            return

        # Import required modules
        from ...tools.get_config import get_config
        from ...tools.get_data import get_data
        from ...tools.logging_context import logging_context
        from ...tools.project_utils import get_project_root
        from ...tools.strategy.sensitivity_analysis import (
            analyze_parameter_combinations,
        )

        with logging_context("cli_strategy_run", "strategy_run.log") as log:
            # Build configuration
            config = {
                "TICKER": ticker,
                "STRATEGY_TYPE": strategy.upper(),
                "DIRECTION": direction,
                "USE_HOURLY": use_4hour,
                "USE_4HOUR": use_4hour,
                "USE_2DAY": use_2day,
                "BASE_DIR": get_project_root(),
                "REFRESH": True,
            }

            if years:
                config["USE_YEARS"] = True
                config["YEARS"] = years

            if market_type:
                config["MARKET_TYPE"] = market_type

            # Apply config defaults
            ticker_config = get_config(config)

            # Fetch price data
            rprint(f"Fetching price data for {ticker}...")
            data = get_data(ticker, ticker_config, log)
            if data is None or len(data) == 0:
                rprint(f"[red]Failed to fetch price data for {ticker}[/red]")
                raise typer.Exit(1)

            rprint(
                f"Retrieved {len(data)} data points from {data['Date'].min()} to {data['Date'].max()}",
            )

            # Create single parameter set
            if strategy.upper() == "MACD":
                parameter_sets = [
                    {"fast_period": fast, "slow_period": slow, "signal_period": signal},
                ]
            else:
                parameter_sets = [{"fast_period": fast, "slow_period": slow}]

            # Run backtest for single combination
            rprint("\nRunning backtest...")
            portfolios = analyze_parameter_combinations(
                data,
                parameter_sets,
                ticker_config,
                log,
                strategy_type=strategy.upper(),
                parallel=False,  # Single combination, no need for parallel
            )

            if not portfolios or len(portfolios) == 0:
                rprint(
                    "[yellow]No results generated - strategy may not have produced any trades[/yellow]",
                )
                raise typer.Exit(0)

            # Get the single result
            result = portfolios[0]

            # Validate result consistency and clean up metrics for 0 trades
            num_trades = (
                int(result.get("Total Trades", 0))
                if result.get("Total Trades") not in [None, "N/A", ""]
                else 0
            )
            if num_trades == 0:
                rprint("\n[yellow]⚠ Warning: Strategy generated 0 trades[/yellow]")
                rprint(
                    "[dim]This parameter combination never triggered entry signals in the historical data.[/dim]",
                )
                rprint(
                    "[dim]Try adjusting the parameters or using a different timeframe.[/dim]\n",
                )

                # Clean up metrics that shouldn't exist with 0 trades
                for key in [
                    "Win Rate [%]",
                    "Profit Factor",
                    "# Wins",
                    "# Losses",
                    "Best Trade [%]",
                    "Worst Trade [%]",
                    "Expectancy",
                    "Avg. Trade [%]",
                    "Avg. Trade Duration",
                ]:
                    if key in result:
                        result[key] = "N/A"

            # Display results in rich table
            rprint("\n[bold green]Backtest Results[/bold green]")

            # Create main metrics table
            table = Table(
                title="Performance Metrics",
                show_header=True,
                header_style="bold magenta",
            )
            table.add_column("Metric", style="cyan", width=30)
            table.add_column("Value", style="green", justify="right")

            # Helper function to format values
            def format_value(key, value):
                if value == "N/A" or value is None:
                    return "N/A"
                if key in [
                    "Win Rate [%]",
                    "Total Return [%]",
                    "Annual Return [%]",
                    "Max. Drawdown [%]",
                    "Avg. Trade [%]",
                    "Best Trade [%]",
                    "Worst Trade [%]",
                ]:
                    return (
                        f"{value:.2f}%"
                        if isinstance(value, int | float)
                        else str(value)
                    )
                if key in ["Sharpe Ratio", "Sortino Ratio"]:
                    return (
                        f"{value:.3f}" if isinstance(value, int | float) else str(value)
                    )
                if key == "Expectancy":
                    return (
                        f"${value:.2f}"
                        if isinstance(value, int | float)
                        else str(value)
                    )
                if isinstance(value, float):
                    return f"{value:.2f}"
                return str(value)

            # Add key metrics
            table.add_row(
                "Total Return",
                format_value("Total Return [%]", result.get("Total Return [%]", 0)),
            )
            table.add_row(
                "Annual Return",
                format_value("Annual Return [%]", result.get("Annual Return [%]", 0)),
            )
            table.add_row("Number of Trades", str(result.get("Total Trades", 0)))
            table.add_row(
                "Win Rate",
                format_value("Win Rate [%]", result.get("Win Rate [%]", "N/A")),
            )
            table.add_row(
                "Profit Factor",
                format_value("Profit Factor", result.get("Profit Factor", "N/A")),
            )
            table.add_row(
                "Sharpe Ratio",
                format_value("Sharpe Ratio", result.get("Sharpe Ratio", 0)),
            )
            table.add_row(
                "Sortino Ratio",
                format_value("Sortino Ratio", result.get("Sortino Ratio", 0)),
            )
            table.add_row(
                "Max Drawdown",
                format_value("Max. Drawdown [%]", result.get("Max. Drawdown [%]", 0)),
            )
            table.add_row(
                "Max Drawdown Duration",
                str(result.get("Max. Drawdown Duration", "N/A")),
            )
            table.add_row(
                "Avg Trade Return",
                format_value("Avg. Trade [%]", result.get("Avg. Trade [%]", "N/A")),
            )
            table.add_row(
                "Avg Trade Duration",
                str(result.get("Avg. Trade Duration", "N/A")),
            )

            if "Expectancy" in result and num_trades > 0:
                table.add_row(
                    "Expectancy",
                    format_value("Expectancy", result.get("Expectancy", 0)),
                )
            if "Score" in result:
                table.add_row("Strategy Score", f"{result.get('Score', 0):.2f}")

            console.print(table)

            # Display trade statistics if available
            if num_trades > 0:
                rprint("\n[bold]Trade Statistics:[/bold]")
                # Calculate wins/losses from win rate and total trades
                win_rate_val = result.get("Win Rate [%]", 0)
                if win_rate_val not in ["N/A", None] and isinstance(
                    win_rate_val,
                    int | float,
                ):
                    wins = int(num_trades * (win_rate_val / 100))
                    losses = num_trades - wins
                    rprint(f"  Winning Trades: {wins}")
                    rprint(f"  Losing Trades: {losses}")
                rprint(f"  Best Trade: {result.get('Best Trade [%]', 0):.2f}%")
                rprint(f"  Worst Trade: {result.get('Worst Trade [%]', 0):.2f}%")
                if "Avg Winning Trade [%]" in result and result.get(
                    "Avg Winning Trade [%]",
                ) not in ["N/A", None]:
                    rprint(
                        f"  Avg Winning Trade: {result.get('Avg Winning Trade [%]', 0):.2f}%",
                    )
                if "Avg Losing Trade [%]" in result and result.get(
                    "Avg Losing Trade [%]",
                ) not in ["N/A", None]:
                    rprint(
                        f"  Avg Losing Trade: {result.get('Avg Losing Trade [%]', 0):.2f}%",
                    )

            # Display equity curve info
            if "Equity Final [$]" in result:
                rprint("\n[bold]Equity Curve:[/bold]")
                rprint(
                    f"  Starting Equity: ${result.get('Equity Start [$]', 1000):.2f}",
                )
                rprint(f"  Final Equity: ${result.get('Equity Final [$]', 0):.2f}")
                rprint(f"  Peak Equity: ${result.get('Equity Peak [$]', 0):.2f}")

            # Display raw CSV data for copy/paste into portfolio files
            rprint("\n[bold cyan]📋 Raw CSV Data (ready for copy/paste):[/bold cyan]")
            csv_output = generate_csv_output_for_portfolios([result])

            # Use plain print to avoid Rich formatting/wrapping for clean copy/paste
            csv_lines = csv_output.split("\n")
            for line in csv_lines:
                print(line)

            rprint("\n[green]✓ Backtest completed successfully[/green]")
            rprint(
                "[dim]Note: No files were exported. Use 'strategy sweep' to export results.[/dim]\n",
            )

    except typer.Exit:
        raise
    except Exception as e:
        rprint(f"[red]Error running backtest: {e}[/red]")
        if "--verbose" in str(e) or "-v" in str(e):
            import traceback

            rprint(traceback.format_exc())
        raise typer.Exit(1)


@app.command()
def sweep(
    ctx: typer.Context,
    profile: str | None = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: list[str] | None = typer.Option(
        None,
        "--ticker",
        "--ticker-1",
        "-t",
        "-t1",
        help="Ticker symbols to analyze (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)",
    ),
    ticker_2: str | None = typer.Option(
        None,
        "--ticker-2",
        "-t2",
        help="Second ticker for synthetic pair analysis (automatically enables synthetic mode)",
    ),
    strategy_type: list[str] | None = typer.Option(
        None,
        "--strategy",
        "-s",
        help="Strategy types: SMA, MACD (default strategies), EMA, ATR (specialized - explicit only, can be used multiple times)",
    ),
    min_trades: int | None = typer.Option(
        None, "--min-trades", help="Minimum number of trades filter"
    ),
    min_win_rate: float | None = typer.Option(
        None,
        "--min-win-rate",
        help="Minimum win rate filter (0.0 to 1.0)",
    ),
    years: int | None = typer.Option(
        None,
        "--years",
        "-y",
        help="Number of years of historical data to analyze (omit for complete history)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview configuration without executing",
    ),
    use_4hour: bool | None = typer.Option(
        None,
        "--use-4hour",
        help="Use 4-hour timeframe data (converted from 1-hour data)",
    ),
    use_2day: bool | None = typer.Option(
        None,
        "--use-2day",
        help="Use 2-day timeframe data (converted from daily data)",
    ),
    market_type: str | None = typer.Option(
        None,
        "--market-type",
        help="Market type: crypto, us_stock, or auto (automatic detection)",
    ),
    direction: str | None = typer.Option(
        None,
        "--direction",
        "-d",
        help="Trading direction: Long or Short (default: Long)",
    ),
    skip_analysis: bool | None = typer.Option(
        None,
        "--skip-analysis",
        help="Skip data download and analysis, assume portfolio files exist in data/raw/portfolios/",
    ),
    fast_min: int | None = typer.Option(
        None, "--fast-min", help="Minimum fast period for sweep"
    ),
    fast_max: int | None = typer.Option(
        None, "--fast-max", help="Maximum fast period for sweep"
    ),
    slow_min: int | None = typer.Option(
        None, "--slow-min", help="Minimum slow period for sweep"
    ),
    slow_max: int | None = typer.Option(
        None, "--slow-max", help="Maximum slow period for sweep"
    ),
    signal_min: int | None = typer.Option(
        None, "--signal-min", help="Minimum signal period for sweep"
    ),
    signal_max: int | None = typer.Option(
        None, "--signal-max", help="Maximum signal period for sweep"
    ),
    entry_fast: int | None = typer.Option(
        None,
        "--entry-fast",
        "-ef",
        help="Lock entry strategy fast period to specific value (sets both min and max)",
    ),
    entry_slow: int | None = typer.Option(
        None,
        "--entry-slow",
        "-esl",
        help="Lock entry strategy slow period to specific value (sets both min and max)",
    ),
    entry_signal: int | None = typer.Option(
        None,
        "--entry-signal",
        "-esi",
        help="Lock entry strategy signal period to specific value (sets both min and max, MACD only)",
    ),
    date: str | None = typer.Option(
        None,
        "--date",
        "-d",
        help="Filter by entry signals triggered on specific date (YYYYMMDD format, e.g., 20250811). Overrides --current if both specified.",
    ),
    use_current: bool | None = typer.Option(
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
        "--refresh/--no-refresh",
        help="Force complete regeneration of all files, bypassing smart resume (default: False)",
    ),
    batch: bool = typer.Option(
        False,
        "--batch/--no-batch",
        help="Enable batch processing mode for large ticker lists",
    ),
    batch_size: int | None = typer.Option(
        None,
        "--batch-size",
        help="Maximum number of tickers to process per execution when batch mode is enabled",
    ),
    database: bool = typer.Option(
        False,
        "--database",
        "-db",
        help="Persist sweep results to PostgreSQL database",
    ),
):
    """
    Perform parameter sweep analysis across parameter ranges.

    This command runs comprehensive parameter sweep analysis across different
    moving average periods to find optimal combinations. It tests all parameter
    combinations within the specified ranges and exports results to multiple
    directories for filtering and analysis.

    Examples:
        trading-cli strategy sweep --profile ma_cross_crypto
        trading-cli strategy sweep --ticker AAPL,MSFT,GOOGL --strategy SMA EMA
        trading-cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 100
        trading-cli strategy sweep --ticker BTC-USD --min-trades 20 --fast-min 10 --fast-max 30
        trading-cli strategy sweep --ticker GOOGL --strategy SMA_ATR --entry-fast 8 --entry-slow 31
        trading-cli strategy sweep --profile minimum --strategy SMA_ATR --entry-fast 20 --entry-slow 50 --ticker BTC-USD
        trading-cli strategy sweep --ticker BTC-USD,ETH-USD --use-4hour
        trading-cli strategy sweep --ticker ETH-USD --use-2day
        trading-cli strategy sweep --profile ma_cross_crypto --skip-analysis
        trading-cli strategy sweep --ticker IREN --date 20250811
        trading-cli strategy sweep --ticker AAPL,MSFT --date 20250815 --strategy SMA
        trading-cli strategy sweep --profile daily_full --batch --batch-size 30
        trading-cli strategy sweep --ticker AAPL,MSFT,GOOGL --batch --batch-size 2
    """
    try:
        # Validate date parameter if provided
        if date:
            import re

            # Validate YYYYMMDD format
            if not re.match(r"^\d{8}$", date):
                rprint(
                    "[red]Error: Date must be in YYYYMMDD format (e.g., 20250811)[/red]",
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
            entry_fast=entry_fast,
            entry_slow=entry_slow,
            entry_signal=entry_signal,
            date=date,
            use_current=use_current,
            verbose=global_verbose,
            performance_mode=performance_mode,
            show_resources=show_resources,
            profile_execution=profile_execution,
            enable_parallel=enable_parallel,
            refresh=refresh,
            batch=batch,
            batch_size=batch_size,
            database=database,
        )

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            # Use default strategy profile
            config = loader.load_from_profile(
                "default_strategy",
                StrategyConfig,
                overrides,
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
                ],
            )
            console.info(
                f"Processing synthetic pair with {strategy_types_str} strategies: {synthetic_ticker}",
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
                ],
            )
            ticker_names = ", ".join(tickers_to_process)
            console.info(
                f"Processing {len(tickers_to_process)} tickers with {strategy_types_str} strategies: {ticker_names}",
            )

        # Execute using strategy dispatcher
        # This routes to the appropriate strategy service based on configuration
        execution_summary = dispatcher.execute_strategy(config)

        # Display rich execution summary instead of simple success message
        _display_strategy_summary(execution_summary, console)

        # Persist results to database if requested
        if config.database and execution_summary.successful_strategies > 0:
            import asyncio

            asyncio.run(
                _persist_sweep_results_to_database(
                    execution_summary=execution_summary,
                    config=config,
                    console=console,
                ),
            )

        # Complete performance monitoring if enabled
        if isinstance(console, PerformanceAwareConsoleLogger):
            console.complete_execution_monitoring()

    except Exception as e:
        # Create console logger for error handling if not already available
        # For errors, always show output (don't use quiet mode for errors)
        error_console = locals().get("console") or ConsoleLogger(
            verbose=global_verbose,
            quiet=False,
        )
        handle_command_error(e, "strategy sweep", global_verbose, console=error_console)


@app.command()
def review(
    ctx: typer.Context,
    profile: str | None = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: list[str] | None = typer.Option(
        None,
        "--ticker",
        "-t",
        help="Filter analysis to specific ticker symbols (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)",
    ),
    best: bool = typer.Option(
        False,
        "--best",
        help="Analyze portfolios_best files specifically",
    ),
    current: bool = typer.Option(
        False,
        "--current",
        help="Analyze current day signals from date-specific directory",
    ),
    date: str | None = typer.Option(
        None,
        "--date",
        help="Analyze signals from specific date directory (YYYYMMDD format, e.g., 20250816). Overrides --current flag.",
    ),
    top_n: int = typer.Option(
        50,
        "--top-n",
        "-n",
        help="Number of top results to display in table",
    ),
    output_format: str = typer.Option(
        "table",
        "--output-format",
        "-f",
        help="Output format: table (with raw CSV) or raw (CSV only)",
    ),
    sort_by: str = typer.Option(
        "Score",
        "--sort-by",
        "-s",
        help="Column to sort by (default: Score)",
    ),
    batch: bool = typer.Option(
        False,
        "--batch",
        help="Use tickers from batch file (data/raw/batch.csv) for non-current analysis",
    ),
    export: bool = typer.Option(
        False,
        "--export",
        help="Export CSV output to ./data/outputs/review/{YYYYMMDD_HHmmss}.csv",
    ),
    comp: bool = typer.Option(
        False,
        "--comp",
        help="Analyze COMP (compound) strategy results from data/outputs/compound/",
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
        trading-cli strategy review --best --batch
        trading-cli strategy review --best --batch --top-n 25
        trading-cli strategy review --best --batch --sort-by "Total Return [%]"
        trading-cli strategy review --best --batch --export
        trading-cli strategy review --profile asia_top_50 --best --export
        trading-cli strategy review --best --current --ticker AAPL,MSFT --export
        trading-cli strategy review --comp --ticker BTC-USD
        trading-cli strategy review --comp --ticker BTC-USD,NVDA,PLTR
        trading-cli strategy review --comp --ticker BTC-USD --export
        trading-cli strategy review --comp --ticker BTC-USD --sort-by "Sharpe Ratio"
    """
    try:
        # Get global options from context
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Validate mutually exclusive flags for COMP mode
        if comp:
            if profile:
                rprint("[red]Error: --comp cannot be used with --profile[/red]")
                rprint(
                    "[dim]COMP mode analyzes compound strategy results independently[/dim]",
                )
                raise typer.Exit(1)
            if best:
                rprint("[red]Error: --comp cannot be used with --best[/red]")
                rprint(
                    "[dim]COMP mode analyzes compound strategy results independently[/dim]",
                )
                raise typer.Exit(1)
            if current or date:
                rprint(
                    "[red]Error: --comp cannot be used with --current or --date[/red]",
                )
                rprint("[dim]COMP strategies are not date-specific[/dim]")
                raise typer.Exit(1)
            if batch:
                rprint("[red]Error: --comp cannot be used with --batch[/red]")
                raise typer.Exit(1)
            if not ticker:
                rprint("[red]Error: --comp requires --ticker to be specified[/red]")
                rprint(
                    "[dim]Example: trading-cli strategy review --comp --ticker BTC-USD[/dim]",
                )
                raise typer.Exit(1)

        # Validate date parameter if provided
        if date:
            import re
            from pathlib import Path

            # Validate YYYYMMDD format
            if not re.match(r"^\d{8}$", date):
                rprint(
                    "[red]Error: Date must be in YYYYMMDD format (e.g., 20250816)[/red]",
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
                    "[dim]Available date directories can be found in data/raw/portfolios_best/[/dim]",
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
                    f"[dim]Ticker filtering enabled with {len(ticker_list)} tickers: {', '.join(ticker_list)}[/dim]",
                )
        elif batch:
            # Batch mode - read tickers from batch file
            from ..services.batch_processing_service import BatchProcessingService

            try:
                batch_service = BatchProcessingService()
                if not batch_service.validate_batch_file():
                    rprint("[red]Error: Batch file validation failed[/red]")
                    raise typer.Exit(1)

                batch_tickers = batch_service.get_batch_tickers()
                if not batch_tickers:
                    rprint("[yellow]Warning: No tickers found in batch file[/yellow]")
                    raise typer.Exit(1)

                ticker_list = batch_tickers
                ticker_filtering_active = True

                # Force non-current mode for batch processing
                if current or date:
                    rprint(
                        "[yellow]Warning: Batch mode forces non-current analysis, ignoring --current/--date flags[/yellow]",
                    )
                current = False
                date = None

                if global_verbose:
                    rprint(
                        f"[dim]Batch mode enabled with {len(ticker_list)} tickers from batch file: {', '.join(ticker_list)}[/dim]",
                    )

            except Exception as e:
                rprint(f"[red]Error processing batch file: {e}[/red]")
                raise typer.Exit(1)
        else:
            ticker_filtering_active = False

        # Handle COMP mode - load from compound strategy outputs
        if comp:
            from pathlib import Path

            from .strategy_utils import process_ticker_input

            # Process ticker input
            ticker_list = process_ticker_input(ticker)

            rprint("\n[bold cyan]📊 COMP Strategy Analysis:[/bold cyan]")
            rprint("=" * 50)
            rprint(f"🎯 [white]Tickers: {', '.join(ticker_list)}[/white]")
            rprint(f"📈 [white]Display: Top {top_n} results[/white]")
            rprint(f"🔢 [white]Sort By: {sort_by}[/white]")
            rprint()

            # Load COMP strategy results
            rprint("[bold]🔍 Loading COMP strategy files...[/bold]")

            compound_dir = Path("data/outputs/compound")
            all_portfolios = []
            loaded_count = 0

            for ticker_symbol in ticker_list:
                compound_file = compound_dir / f"{ticker_symbol}.csv"

                if not compound_file.exists():
                    if global_verbose:
                        rprint(
                            f"[yellow]⚠ Warning: COMP file not found for {ticker_symbol}: {compound_file}[/yellow]",
                        )
                    continue

                try:
                    import pandas as pd

                    df = pd.read_csv(compound_file)

                    # Convert DataFrame to list of dicts
                    portfolios = df.to_dict("records")
                    all_portfolios.extend(portfolios)
                    loaded_count += 1

                    if global_verbose:
                        rprint(
                            f"[green]✓ Loaded COMP results for {ticker_symbol}: {len(portfolios)} record(s)[/green]",
                        )

                except Exception as e:
                    rprint(
                        f"[red]✗ Error loading COMP file for {ticker_symbol}: {e}[/red]",
                    )
                    continue

            if not all_portfolios:
                rprint(
                    "[red]Error: No COMP strategy results found for specified tickers[/red]",
                )
                rprint(f"[dim]Searched in: {compound_dir.absolute()}[/dim]")
                rprint(
                    "[dim]Hint: Run 'trading-cli strategy run {TICKER} --comp' to generate COMP results first[/dim]",
                )
                raise typer.Exit(1)

            rprint(
                f"[green]✓ Successfully loaded {loaded_count} COMP strategy file(s) with {len(all_portfolios)} total record(s)[/green]\n",
            )

            # Convert to DataFrame for processing
            import pandas as pd

            combined_df = pd.DataFrame(all_portfolios)

            # Skip to display logic (jump past the normal portfolio loading)
            # We'll use a flag to indicate COMP mode
            comp_mode_active = True
        else:
            comp_mode_active = False

        # Skip validation for COMP mode
        if not comp_mode_active:
            # Allow auto-discovery mode when both --best and --current are provided
            if (
                not profile
                and not (best and current)
                and not ticker_filtering_active
                and not batch
            ):
                rprint(
                    "[red]Error: --profile is required unless using --best --current for auto-discovery, --ticker for filtering, or --batch for batch mode[/red]",
                )
                rprint("[dim]Examples:[/dim]")
                rprint(
                    "[dim]  Profile mode: trading-cli strategy review --profile asia_top_50 --best[/dim]",
                )
                rprint(
                    "[dim]  Auto-discovery: trading-cli strategy review --best --current[/dim]",
                )
                rprint(
                    "[dim]  Ticker filtering: trading-cli strategy review --best --current --ticker AAPL,MSFT[/dim]",
                )
                rprint(
                    "[dim]  Batch mode: trading-cli strategy review --best --batch[/dim]",
                )
                raise typer.Exit(1)

            if not best:
                rprint(
                    "[red]Error: --best flag is required (only portfolios_best analysis is currently supported)[/red]",
                )
                rprint(
                    "[dim]Example: trading-cli strategy review --profile asia_top_50 --best[/dim]",
                )
                raise typer.Exit(1)

        # Skip normal portfolio loading for COMP mode
        if not comp_mode_active:
            # Handle profile loading vs auto-discovery mode vs ticker filtering
            if ticker_filtering_active:
                # Ticker filtering mode - use provided ticker list regardless of profile
                if global_verbose:
                    rprint(
                        f"[dim]Ticker filtering mode: analyzing {len(ticker_list)} specific tickers[/dim]",
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
                    config.ticker
                    if isinstance(config.ticker, list)
                    else [config.ticker]
                )

                if global_verbose:
                    rprint(
                        f"[dim]Loaded profile '{profile}' with {len(ticker_list)} tickers[/dim]",
                    )
            else:
                # Auto-discovery mode (profile is None, best=True, current=True)
                ticker_list = ["Auto-discovered"]  # For display purposes

                if global_verbose:
                    rprint(
                        "[dim]Auto-discovery mode enabled - will scan current day directory[/dim]",
                    )

            # Display configuration
            rprint("\n[bold cyan]📊 Portfolio Analysis Configuration:[/bold cyan]")
            rprint("=" * 50)

            # Show mode and profile information
            if ticker_filtering_active:
                if batch:
                    rprint("📋 [white]Mode: Batch Processing[/white]")
                elif profile:
                    rprint(
                        f"📋 [white]Mode: Ticker Filtering (Profile: {profile})[/white]",
                    )
                else:
                    rprint("📋 [white]Mode: Ticker Filtering[/white]")
            elif profile:
                rprint(f"📋 [white]Profile: {profile}[/white]")
            else:
                rprint("📋 [white]Mode: Auto-Discovery[/white]")

            # Show analysis type with date if applicable
            from datetime import datetime

            if current:
                # Use custom date if specified, otherwise current date
                display_date = date if date else datetime.now().strftime("%Y%m%d")
                date_label = (
                    f"date: {display_date}" if date else f"current: {display_date}"
                )

                if ticker_filtering_active:
                    rprint(
                        f"📊 [white]Analysis Type: portfolios_best ({date_label}, filtered)[/white]",
                    )
                elif profile:
                    rprint(
                        f"📊 [white]Analysis Type: portfolios_best ({date_label})[/white]",
                    )
                else:
                    rprint(
                        f"📊 [white]Analysis Type: portfolios_best ({date_label}, auto-discovery)[/white]",
                    )
            else:
                rprint("📊 [white]Analysis Type: portfolios_best[/white]")

            # Show tickers
            if ticker_filtering_active:
                rprint(
                    f"🎯 [white]Tickers: Filtered to {len(ticker_list)} tickers: {', '.join(ticker_list)}[/white]",
                )
            elif profile:
                rprint(f"🎯 [white]Tickers: {', '.join(ticker_list)}[/white]")
            else:
                rprint(
                    "🎯 [white]Tickers: Auto-discovered from current day files[/white]",
                )

            rprint(f"📈 [white]Display: Top {top_n} results[/white]")
            rprint(f"🔢 [white]Sort By: {sort_by}[/white]")
            rprint()

            # Initialize analysis service
            from ..services.portfolio_analysis_service import PortfolioAnalysisService

            analysis_service = PortfolioAnalysisService(
                use_current=current,
                custom_date=date,
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
                    "[yellow]❌ No portfolio data found for the specified tickers[/yellow]",
                )
                rprint(
                    "[dim]Make sure portfolios_best files exist in data/raw/portfolios_best/[/dim]",
                )
                raise typer.Exit(1)

        # Process and sort data
        rprint(f"[bold]📝 Processing {len(combined_df)} portfolios...[/bold]")

        if comp_mode_active:
            # For COMP mode, just sort directly (no Metric Type column to remove)
            sorted_df = combined_df.sort_values(by=sort_by, ascending=False)
        else:
            # For regular mode, remove Metric Type column and sort
            processed_df = analysis_service.remove_metric_type_column(combined_df)
            sorted_df = analysis_service.sort_portfolios(processed_df, sort_by=sort_by)

        # Format for display
        if comp_mode_active:
            # For COMP mode, format manually without analysis_service
            top_results = sorted_df.head(top_n)
            all_results = sorted_df
            display_data = {
                "top_results": top_results,
                "all_results": all_results,
                "stats": {
                    "total_portfolios": len(sorted_df),
                    "top_n": min(top_n, len(sorted_df)),
                },
            }
        else:
            display_data = analysis_service.format_for_display(sorted_df, top_n=top_n)

        if output_format == "raw":
            # Raw CSV output only
            if comp_mode_active:
                rprint(
                    "\n[bold cyan]📋 COMP Strategy Results: Raw CSV Data:[/bold cyan]",
                )
                csv_output = display_data["all_results"].to_csv(index=False)
            else:
                rprint(
                    "\n[bold cyan]📋 Portfolio Entry Signals: Raw CSV Data:[/bold cyan]",
                )
                csv_output = analysis_service.generate_csv_output(
                    display_data["all_results"],
                )
            rprint(csv_output)
        else:
            # Table format with raw CSV
            if comp_mode_active:
                # For COMP mode, use simpler display
                _display_portfolio_table(
                    display_data["top_results"],
                    list(display_data["top_results"].columns),
                )
            else:
                _display_portfolio_table(
                    display_data["top_results"],
                    analysis_service.get_display_columns(),
                )

            # Summary statistics
            stats = display_data["stats"]
            rprint("\n[bold green]✨ Analysis Complete![/bold green]")
            rprint(
                f"📈 [cyan]{stats['total_portfolios']} {'COMP strategies' if comp_mode_active else 'portfolios'} analyzed successfully[/cyan]",
            )

            if stats["total_portfolios"] > 0 and not comp_mode_active:
                rprint("\n💡 [bold yellow]Key Insights:[/bold yellow]")
                rprint(
                    f"🏆 [white]Best Opportunity: {stats['best_ticker']} ({stats['best_return']:+.2f}%)[/white]",
                )
                rprint(f"📊 [white]Average Score: {stats['avg_score']:.3f}[/white]")
                rprint(
                    f"🎯 [white]Win Rate Range: {stats['win_rate_range'][0]:.1f}% - {stats['win_rate_range'][1]:.1f}%[/white]",
                )

            # Raw CSV output section
            if comp_mode_active:
                rprint(
                    "\n[bold cyan]📋 COMP Strategy Results: Raw CSV Data:[/bold cyan]",
                )
                csv_output = display_data["all_results"].to_csv(index=False)
            else:
                rprint(
                    "\n[bold cyan]📋 Portfolio Entry Signals: Raw CSV Data:[/bold cyan]",
                )
                csv_output = analysis_service.generate_csv_output(
                    display_data["all_results"],
                )

            # Use print() instead of rprint() to avoid Rich's line wrapping
            # Each CSV line should be displayed as one complete line for proper copy/paste
            csv_lines = csv_output.split("\n")
            for line in csv_lines:
                print(line)  # Plain print without Rich formatting/wrapping

        # Export to CSV if requested
        if export:
            try:
                from datetime import datetime
                from pathlib import Path

                output_dir = Path("./data/outputs/review")
                output_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{'comp_' if comp_mode_active else ''}{timestamp}.csv"
                file_path = output_dir / file_name

                display_data["all_results"].to_csv(file_path, index=False)
                rprint(f"\n[green]✅ Results exported to: {file_path}[/green]")
            except Exception as export_error:
                rprint(f"\n[red]❌ Export failed: {export_error}[/red]")

    except Exception as e:
        handle_command_error(e, "strategy review", global_verbose)


def _display_portfolio_table(df, display_columns):
    """Display portfolio analysis results in multiple focused tables."""
    if df.empty:
        rprint("[yellow]No data to display[/yellow]")
        return

    # Display 3 focused tables with logical groupings
    _display_summary_table(df)
    rprint()  # Add spacing
    _display_performance_table(df)
    rprint()  # Add spacing
    _display_risk_table(df)


def _display_summary_table(df):
    """Display strategy identification and ranking overview."""
    table = Table(
        title="📊 Strategy Overview & Rankings",
        show_header=True,
        header_style="bold magenta",
    )

    # Define columns for summary table
    table.add_column("Rank", style="cyan", no_wrap=True, justify="center", width=6)
    table.add_column("Ticker", style="bold white", no_wrap=True, width=10)
    table.add_column("Strategy Type", style="blue", no_wrap=True, width=14)
    table.add_column("Score", style="white", justify="right", width=8)
    table.add_column("Total Return [%]", style="green", justify="right", width=16)
    table.add_column("Total Trades", style="yellow", justify="right", width=12)

    # Add rows
    for idx, (_, row) in enumerate(df.head(50).iterrows(), 1):
        ticker = str(row.get("Ticker", "N/A"))
        strategy_type = str(row.get("Strategy Type", "N/A"))
        score = row.get("Score")
        total_return = row.get("Total Return [%]")
        total_trades = row.get("Total Trades")

        # Format values
        score_str = f"{float(score):.3f}" if pd.notna(score) else "N/A"

        if pd.notna(total_return):
            return_val = float(total_return)
            color = "green" if return_val > 0 else "red"
            return_str = f"[{color}]{return_val:+,.2f}%[/{color}]"
        else:
            return_str = "N/A"

        trades_str = str(int(total_trades)) if pd.notna(total_trades) else "N/A"

        table.add_row(
            str(idx),
            ticker,
            strategy_type,
            score_str,
            return_str,
            trades_str,
        )

    console.print(table)


def _display_performance_table(df):
    """Display trade performance and profitability metrics."""
    table = Table(
        title="💰 Trade Performance Metrics",
        show_header=True,
        header_style="bold magenta",
    )

    # Define columns for performance table
    table.add_column("Rank", style="cyan", no_wrap=True, justify="center", width=6)
    table.add_column("Ticker", style="bold white", no_wrap=True, width=10)
    table.add_column("Win Rate [%]", style="yellow", justify="right", width=14)
    table.add_column("Profit Factor", style="green", justify="right", width=14)
    table.add_column("Expectancy/Trade", style="white", justify="right", width=16)

    # Add rows
    for idx, (_, row) in enumerate(df.head(50).iterrows(), 1):
        ticker = str(row.get("Ticker", "N/A"))
        win_rate = row.get("Win Rate [%]")
        profit_factor = row.get("Profit Factor")
        expectancy = row.get("Expectancy per Trade")

        # Format values
        win_rate_str = f"{float(win_rate):.2f}%" if pd.notna(win_rate) else "N/A"
        pf_str = f"{float(profit_factor):.3f}" if pd.notna(profit_factor) else "N/A"

        if pd.notna(expectancy):
            exp_val = float(expectancy)
            color = "green" if exp_val > 0 else "red"
            exp_str = f"[{color}]${exp_val:,.2f}[/{color}]"
        else:
            exp_str = "N/A"

        table.add_row(
            str(idx),
            ticker,
            win_rate_str,
            pf_str,
            exp_str,
        )

    console.print(table)


def _display_risk_table(df):
    """Display risk-adjusted metrics and drawdown analysis."""
    table = Table(
        title="⚠️  Risk Assessment",
        show_header=True,
        header_style="bold magenta",
    )

    # Define columns for risk table
    table.add_column("Rank", style="cyan", no_wrap=True, justify="center", width=6)
    table.add_column("Ticker", style="bold white", no_wrap=True, width=10)
    table.add_column("Sharpe Ratio", style="green", justify="right", width=13)
    table.add_column("Sortino Ratio", style="blue", justify="right", width=14)
    table.add_column("Max Drawdown [%]", style="red", justify="right", width=17)

    # Add rows
    for idx, (_, row) in enumerate(df.head(50).iterrows(), 1):
        ticker = str(row.get("Ticker", "N/A"))
        sharpe = row.get("Sharpe Ratio")
        sortino = row.get("Sortino Ratio")
        max_dd = row.get("Max Drawdown [%]")

        # Format values
        sharpe_str = f"{float(sharpe):.3f}" if pd.notna(sharpe) else "N/A"
        sortino_str = f"{float(sortino):.3f}" if pd.notna(sortino) else "N/A"
        dd_str = f"[red]{float(max_dd):.2f}%[/red]" if pd.notna(max_dd) else "N/A"

        table.add_row(
            str(idx),
            ticker,
            sharpe_str,
            sortino_str,
            dd_str,
        )

    console.print(table)


def _display_basic_best_strategy(
    best: StrategyPortfolioResults,
    console: ConsoleLogger,
) -> None:
    """Fallback display for best strategy when portfolios_best file cannot be read."""
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
            f"Trade Performance: +{best.avg_win:.2f}% avg win vs -{abs(best.avg_loss):.2f}% avg loss",
        )


async def _persist_sweep_results_to_database(
    execution_summary: StrategyExecutionSummary,
    config: StrategyConfig,
    console: ConsoleLogger,
) -> None:
    """
    Persist strategy sweep results to PostgreSQL database.

    Args:
        execution_summary: Summary of strategy execution results
        config: Strategy configuration used for the sweep
        console: Console logger for user-facing output

    Returns:
        None
    """
    import uuid

    from app.database.config import get_db_manager, is_database_available
    from app.database.strategy_sweep_repository import StrategySweepRepository

    try:
        # Get database manager instance
        db_manager = get_db_manager()

        # Initialize database connection if not already initialized
        await db_manager.initialize()

        # Check database availability
        if not await is_database_available():
            console.warning("💾 Database unavailable - results saved to CSV files only")
            await db_manager.close()
            return

        # Generate unique sweep run ID
        sweep_run_id = uuid.uuid4()

        # Build sweep configuration dict
        sweep_config = {
            "tickers": (
                config.ticker if isinstance(config.ticker, list) else [config.ticker]
            ),
            "strategy_types": [
                st.value if hasattr(st, "value") else str(st)
                for st in config.strategy_types
            ],
            "fast_period_min": config.fast_period_min,
            "fast_period_max": config.fast_period_max,
            "slow_period_min": config.slow_period_min,
            "slow_period_max": config.slow_period_max,
            "signal_period_min": config.signal_period_min,
            "signal_period_max": config.signal_period_max,
            "years": config.years,
            "market_type": (
                config.market_type.value
                if hasattr(config.market_type, "value")
                else str(config.market_type)
                if config.market_type
                else None
            ),
            "direction": (
                config.direction.value
                if hasattr(config.direction, "value")
                else str(config.direction)
                if config.direction
                else None
            ),
            "minimums": {
                "win_rate": config.minimums.win_rate,
                "trades": config.minimums.trades,
                "profit_factor": config.minimums.profit_factor,
                "sortino_ratio": config.minimums.sortino_ratio,
            },
        }

        # Read portfolio data from generated CSV files
        from pathlib import Path

        import polars as pl

        results_to_save = []
        data_dir = Path("data/raw/portfolios")

        # Determine tickers to process
        tickers = config.ticker if isinstance(config.ticker, list) else [config.ticker]

        # Iterate through all ticker-strategy combinations
        for ticker in tickers:
            for strategy_type in config.strategy_types:
                strategy_name = (
                    strategy_type.value
                    if hasattr(strategy_type, "value")
                    else str(strategy_type)
                )

                # Determine timeframe suffix
                timeframe_suffix = "_D"  # Default to daily
                if config.use_4hour:
                    timeframe_suffix = "_4H"
                elif config.use_2day:
                    timeframe_suffix = "_2D"

                # Build CSV filename
                csv_filename = f"{ticker}{timeframe_suffix}_{strategy_name}.csv"
                csv_path = data_dir / csv_filename

                if csv_path.exists():
                    try:
                        df = pl.read_csv(csv_path)
                        # Convert each row to a dict
                        for row in df.iter_rows(named=True):
                            results_to_save.append(dict(row))
                    except Exception as e:
                        console.warning(f"Failed to read {csv_filename}: {e}")

        if not results_to_save:
            console.warning("💾 No portfolio data found for database persistence")
            await db_manager.close()
            return

        # Initialize repository and save results
        repository = StrategySweepRepository(db_manager)

        # Display consolidated database persistence message
        console.info(f"💾 Database: Saving {len(results_to_save):,} portfolios...")
        inserted_count = await repository.save_sweep_results(
            sweep_run_id=sweep_run_id,
            results=results_to_save,
            sweep_config=sweep_config,
        )

        # Format sweep_run_id for display (first 8 chars)
        run_id_short = str(sweep_run_id)[:8]
        console.success(
            f"💾 Database: Persisted {inserted_count:,} records (run ID: {run_id_short}...)",
        )

        # Close database connection
        await db_manager.close()

    except Exception as e:
        console.error(f"Failed to persist results to database: {e}")
        console.info("Results are still available in CSV files")
        # Close database connection on error
        with contextlib.suppress(builtins.BaseException):
            await db_manager.close()
        # Don't raise - allow execution to continue


def _display_strategy_summary(
    summary: StrategyExecutionSummary,
    console: ConsoleLogger,
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
            f"{ticker_count} ticker analyzed successfully ({', '.join(summary.tickers_processed)})",
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
                f"Generated: {summary.total_portfolios_generated:,} portfolios",
            )

            if summary.total_filtered_portfolios > 0:
                pass_rate = summary.filter_pass_rate * 100
                console.info(
                    f"Filtered: {summary.total_filtered_portfolios:,} portfolios ({pass_rate:.1f}% pass rate)",
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
        file_types: dict[str, list[str]] = {
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
                        f"{file_name} ({result.filtered_portfolios} rows)",
                    )
                elif "/portfolios_metrics/" in file_path:
                    file_types["portfolios_metrics"].append(f"{file_name} (metrics)")
                elif "/portfolios_best/" in file_path:
                    file_types["portfolios_best"].append(f"{file_name} (best)")
                elif "/portfolios/" in file_path:
                    file_types["portfolios"].append(
                        f"{file_name} ({result.total_portfolios} rows)",
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

    # Key Insights section - Enhanced with comprehensive metrics
    console.heading("Key Insights", level=3)

    if summary.best_opportunity:
        best = summary.best_opportunity

        # Read portfolios_best file for comprehensive metrics including exit parameters
        try:
            from pathlib import Path

            import pandas as pd

            # Build best file path
            ticker = (
                summary.tickers_processed[0]
                if summary.tickers_processed
                else best.ticker
            )
            timeframe = "D"  # Default, could extract from config if needed
            best_file = Path(
                f"data/raw/portfolios_best/{ticker}_{timeframe}_{best.strategy_type}.csv",
            )

            if best_file.exists():
                best_df = pd.read_csv(best_file)
                if len(best_df) > 0:
                    best_row = best_df.iloc[0]

                    # Build comprehensive config string with exit parameters
                    fast = best_row.get("Fast Period", "")
                    slow = best_row.get("Slow Period", "")
                    exit_fast = best_row.get("Exit Fast Period")
                    exit_slow = best_row.get("Exit Slow Period")

                    if (
                        best.strategy_type == "SMA_ATR"
                        and pd.notna(exit_fast)
                        and pd.notna(exit_slow)
                    ):
                        config_str = f"SMA({fast}/{slow}) + ATR({int(exit_fast)}, {exit_slow:.1f})"
                    elif best.strategy_type in ["SMA", "EMA"]:
                        config_str = f"{best.strategy_type}({fast}/{slow})"
                    elif best.strategy_type == "MACD":
                        signal = best_row.get("Signal Period", "")
                        config_str = f"MACD({fast}/{slow}/{signal})"
                    else:
                        config_str = (
                            f"{best.strategy_type} {best.best_config}"
                            if best.best_config
                            else best.strategy_type
                        )

                    # Display comprehensive configuration
                    console.success(f"Best Configuration: {config_str}")

                    # Display key performance metrics
                    total_return = best_row.get("Total Return [%]")
                    if pd.notna(total_return):
                        console.info(f"Total Return: {total_return:.2f}%")

                    win_rate = best_row.get("Win Rate [%]")
                    if pd.notna(win_rate):
                        console.info(f"Win Rate: {win_rate:.1f}%")

                    profit_factor = best_row.get("Profit Factor")
                    if pd.notna(profit_factor):
                        console.info(f"Profit Factor: {profit_factor:.2f}")

                    expectancy = best_row.get("Expectancy")
                    if pd.notna(expectancy):
                        console.info(f"Expectancy: ${expectancy:.2f} per trade")

                    max_dd = best_row.get("Max Drawdown [%]")
                    if pd.notna(max_dd):
                        console.info(f"Max Drawdown: {max_dd:.1f}%")

                    total_trades = best_row.get("Total Trades")
                    if pd.notna(total_trades):
                        console.info(f"Total Trades: {int(total_trades)}")

                    # Show trade performance if available
                    avg_win = best_row.get("Avg Winning Trade [%]")
                    avg_loss = best_row.get("Avg Losing Trade [%]")
                    if pd.notna(avg_win) and pd.notna(avg_loss):
                        console.info(
                            f"Trade Performance: +{avg_win:.2f}% avg win vs {avg_loss:.2f}% avg loss",
                        )
                else:
                    # Fallback to basic display if file is empty
                    _display_basic_best_strategy(best, console)
            else:
                # Fallback to basic display if file doesn't exist
                _display_basic_best_strategy(best, console)

        except Exception as e:
            console.debug(f"Error reading portfolios_best for detailed metrics: {e}")
            # Fallback to basic display
            _display_basic_best_strategy(best, console)

    # Execution performance
    if summary.execution_time > 60:
        time_display = f"{summary.execution_time / 60:.1f} minutes"
    else:
        time_display = f"{summary.execution_time:.1f} seconds"

    console.info(f"Execution Time: {time_display}")

    if summary.total_strategies > 1:
        success_rate_pct = summary.success_rate * 100
        console.info(
            f"Success Rate: {success_rate_pct:.0f}% ({summary.successful_strategies}/{summary.total_strategies} strategies)",
        )


@app.command()
def sector_compare(
    format: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table, json, csv",
    ),
    export: str | None = typer.Option(
        None, "--export", "-e", help="Export results to file"
    ),
    date: str | None = typer.Option(
        None,
        "--date",
        "-d",
        help="Specific date in YYYYMMDD format (default: latest available)",
    ),
    list_dates: bool = typer.Option(
        False,
        "--list-dates",
        help="List available dates and exit",
    ),
    explain_columns: bool = typer.Option(
        False,
        "--explain-columns",
        help="Explain all column meanings and exit",
    ),
    vs_benchmark: str | None = typer.Option(
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
                        "sectors_current",
                        StrategyConfig,
                        overrides,
                    )

                    # Execute strategy with existing StrategyDispatcher
                    console.print(
                        "[dim]Running: trading-cli strategy run -p sectors_current"
                        + (" --refresh" if refresh else "")
                        + "[/dim]",
                    )

                    # Initialize strategy dispatcher with console logger
                    console_logger = ConsoleLogger()
                    dispatcher = StrategyDispatcher(console=console_logger)

                    # Validate strategy compatibility
                    if not dispatcher.validate_strategy_compatibility(
                        profile_config.strategy_types,
                    ):
                        console.print(
                            "[red]✗[/red] Invalid strategy configuration in sectors_current profile",
                        )
                        console.print(
                            "[yellow]Continuing with existing data...[/yellow]",
                        )
                    else:
                        # Execute the strategy
                        dispatcher.execute_strategy(profile_config)
                        console.print(
                            "[green]✓[/green] Sector data generated successfully",
                        )

                except Exception as e:
                    console.print(
                        f"[red]✗[/red] Error during sector data generation: {e!s}",
                    )
                    console.print("[yellow]Continuing with existing data...[/yellow]")
                    if verbose:
                        console.print(f"[red]Full error: {e!s}[/red]")

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
                    "[yellow]No dated directories found in portfolios_best[/yellow]",
                )
                console.print(
                    "[dim]Run 'trading-cli strategy run -p sectors_current' to generate data[/dim]",
                )
            return

        # Handle explain-columns option
        if explain_columns:
            console.print(
                "[bold cyan]🔍 Sector Comparison Table - Column Explanations:[/bold cyan]\n",
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
                        "    [yellow]• Medium Risk: 10-20% Max Drawdown[/yellow]",
                    )
                    console.print("    [red]• High Risk: >20% Max Drawdown[/red]")
                else:
                    console.print(f"• [bold white]{label}:[/bold white] {description}")

            console.print("\n[bold yellow]💡 Key Insights:[/bold yellow]")
            console.print(
                "• Higher Score values indicate better overall strategy performance",
            )
            console.print(
                "• 'vs Top' shows relative performance - 100% = best performing sector",
            )
            console.print(
                "• Consider both Score and Max Drawdown for risk-adjusted decisions",
            )
            console.print("• Win Rate and Profit Factor validate strategy consistency")
            console.print(
                "• Minimum 44+ trades recommended for statistical significance",
            )
            return

        if verbose:
            target_date = engine.resolve_target_date()
            if target_date:
                console.print(
                    f"[dim]Loading sector ETF data for date: {target_date}[/dim]",
                )
            else:
                console.print(
                    "[dim]Loading sector ETF data from fallback directory[/dim]",
                )

        # Generate comparison matrix
        comparison_data = engine.generate_comparison_matrix()

        if not comparison_data:
            console.print("[red]No sector data found.[/red]")
            console.print(
                "[yellow]First run: trading-cli strategy run -p sectors_current[/yellow]",
            )
            available_dates = engine.get_available_dates()
            if available_dates:
                console.print(
                    f"[dim]Or try a specific date: --date {available_dates[0]}[/dim]",
                )
            return

        # Display results based on format
        if format == "table":
            display_sector_comparison_table(
                comparison_data,
                console,
                engine.benchmark_data,
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
                f"[red]Unknown format: {format}. Use: table, json, or csv[/red]",
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
