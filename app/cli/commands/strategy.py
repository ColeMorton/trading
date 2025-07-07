"""
Strategy command implementations.

This module provides CLI commands for executing and analyzing MA Cross
and MACD strategies with various configuration options.
"""

from pathlib import Path
from typing import List, Optional, Union

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import ConfigLoader
from ..models.strategy import MACDConfig, MACrossConfig, StrategyConfig

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
        "-t",
        help="Ticker symbols to analyze (can be used multiple times)",
    ),
    strategy_type: Optional[List[str]] = typer.Option(
        None,
        "--strategy",
        "-s",
        help="Strategy types: SMA, EMA, MACD (can be used multiple times)",
    ),
    windows: Optional[int] = typer.Option(
        None, "--windows", "-w", help="Look-back window for analysis"
    ),
    min_trades: Optional[int] = typer.Option(
        None, "--min-trades", help="Minimum number of trades filter"
    ),
    min_win_rate: Optional[float] = typer.Option(
        None, "--min-win-rate", help="Minimum win rate filter (0.0 to 1.0)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview configuration without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Execute strategy analysis with specified parameters.

    This command runs MA Cross or MACD strategy analysis on the specified
    tickers with the given configuration parameters.

    Examples:
        trading-cli strategy run --profile ma_cross_crypto
        trading-cli strategy run --ticker AAPL MSFT --strategy SMA EMA
        trading-cli strategy run --ticker BTC-USD --windows 55 --min-trades 20
    """
    try:
        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {}
        if ticker:
            overrides["ticker"] = ticker
        if strategy_type:
            overrides["strategy_types"] = strategy_type
        if windows:
            overrides["windows"] = windows
        if min_trades or min_win_rate:
            minimums = {}
            if min_trades:
                minimums["trades"] = min_trades
            if min_win_rate:
                minimums["win_rate"] = min_win_rate
            overrides["minimums"] = minimums

        overrides["dry_run"] = dry_run

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            # Use default strategy template
            template = loader.get_config_template("strategy")
            config = loader.load_from_dict(template, StrategyConfig, overrides)

        if dry_run:
            _show_config_preview(config)
            return

        if verbose:
            rprint("[dim]Loading strategy execution module...[/dim]")

        # Import and execute strategy
        # TODO: Integrate with existing strategy execution logic
        from ...strategies.ma_cross.tools.strategy_execution import execute_strategy
        from ...tools.logging_context import logging_context

        with logging_context("cli_strategy", "strategy_run.log") as log:
            rprint("[bold]Executing strategy analysis...[/bold]")

            # Convert Pydantic model to legacy config format
            legacy_config = _convert_to_legacy_config(config)

            # Execute each strategy type
            all_results = []

            # Debug: Show all tickers that will be processed
            tickers_to_process = legacy_config.get("TICKER", [])
            if isinstance(tickers_to_process, str):
                tickers_to_process = [tickers_to_process]
            rprint(
                f"[bold]Processing {len(tickers_to_process)} tickers:[/bold] {', '.join(tickers_to_process)}"
            )

            for strategy_type in config.strategy_types:
                rprint(f"Running {strategy_type} analysis...")

                strategy_config = legacy_config.copy()
                strategy_config["STRATEGY_TYPE"] = strategy_type

                results = execute_strategy(strategy_config, strategy_type, log)
                if results:
                    all_results.extend(
                        results if isinstance(results, list) else [results]
                    )

            if all_results:
                _display_results(all_results, config)
                rprint(f"[green]Strategy analysis completed successfully![/green]")
                rprint(f"Found {len(all_results)} strategies matching criteria")
            else:
                rprint(
                    "[yellow]No strategies found matching the specified criteria[/yellow]"
                )

    except Exception as e:
        rprint(f"[red]Error executing strategy: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def sweep(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: Optional[str] = typer.Option(
        None, "--ticker", "-t", help="Single ticker symbol for parameter sweep"
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

    Examples:
        trading-cli strategy sweep --ticker AAPL --fast-min 5 --fast-max 50 --slow-min 20 --slow-max 200
        trading-cli strategy sweep --profile ma_cross_crypto --max-results 20
    """
    try:
        loader = ConfigLoader()

        # Build overrides for sweep parameters
        overrides = {}
        if ticker:
            overrides["ticker"] = ticker
        if fast_min and fast_max:
            overrides["fast_period_range"] = (fast_min, fast_max)
        if slow_min and slow_max:
            overrides["slow_period_range"] = (slow_min, slow_max)

        # Load MA Cross configuration
        if profile:
            config = loader.load_from_profile(profile, MACrossConfig, overrides)
        else:
            template = loader.get_config_template("ma_cross")
            config = loader.load_from_dict(template, MACrossConfig, overrides)

        if dry_run:
            _show_sweep_preview(config)
            return

        rprint("[bold]Starting parameter sweep analysis...[/bold]")
        rprint(f"Ticker: {config.ticker}")
        rprint(f"Fast period range: {config.fast_period_range}")
        rprint(f"Slow period range: {config.slow_period_range}")

        rprint("[bold]Executing parameter sweep...[/bold]")

        # Import required modules for parameter sweep
        from ...strategies.ma_cross.tools.parameter_sensitivity import (
            analyze_parameter_sensitivity,
        )
        from ...tools.get_data import get_data
        from ...tools.logging_context import logging_context

        with logging_context("cli_parameter_sweep", "parameter_sweep.log") as log:
            # Convert config to legacy format
            legacy_config = _convert_sweep_to_legacy_config(config)

            # Get price data
            rprint(f"Fetching price data for {config.ticker}...")
            data = get_data(config.ticker, legacy_config, log)
            if data is None:
                rprint("[red]Failed to fetch price data[/red]")
                raise typer.Exit(1)

            # Generate parameter combinations
            short_windows = list(
                range(config.fast_period_range[0], config.fast_period_range[1] + 1)
            )
            long_windows = list(
                range(config.slow_period_range[0], config.slow_period_range[1] + 1)
            )

            # Filter combinations where short < long
            total_combinations = sum(
                1 for s in short_windows for l in long_windows if s < l
            ) * len(config.strategy_types)
            rprint(f"Analyzing {total_combinations} parameter combinations...")

            all_results = []
            for strategy_type in config.strategy_types:
                rprint(f"Running {strategy_type} parameter sweep...")

                # Set strategy type in legacy config
                strategy_config = legacy_config.copy()
                strategy_config["STRATEGY_TYPE"] = strategy_type

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
                        f"Found {len(strategy_results)} valid {strategy_type} combinations"
                    )

            if all_results:
                # Sort by score and display top results
                sorted_results = sorted(
                    all_results, key=lambda x: x.get("Score", 0), reverse=True
                )

                _display_sweep_results(sorted_results[:max_results], config)
                rprint(f"\n[green]Parameter sweep completed![/green]")
                rprint(
                    f"Found {len(all_results)} total combinations, showing top {min(max_results, len(sorted_results))}"
                )

                # Show export location
                portfolio_dir = legacy_config["BASE_DIR"] + "/csv/portfolios/"
                rprint(f"[dim]Full results exported to: {portfolio_dir}[/dim]")
            else:
                rprint("[yellow]No valid parameter combinations found[/yellow]")

    except Exception as e:
        rprint(f"[red]Error performing parameter sweep: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze(
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    ticker: str = typer.Argument(help="Ticker symbol to analyze"),
    strategy_type: str = typer.Option(
        "SMA", "--strategy", "-s", help="Strategy type: SMA, EMA, or MACD"
    ),
    fast_period: Optional[int] = typer.Option(
        None, "--fast", help="Fast period parameter"
    ),
    slow_period: Optional[int] = typer.Option(
        None, "--slow", help="Slow period parameter"
    ),
    show_trades: bool = typer.Option(
        False, "--show-trades", help="Show individual trade details"
    ),
):
    """
    Analyze a single strategy configuration in detail.

    This command provides detailed analysis of a specific strategy
    configuration including performance metrics and trade details.

    Examples:
        trading-cli strategy analyze AAPL --strategy SMA --fast 20 --slow 50
        trading-cli strategy analyze BTC-USD --strategy EMA --show-trades
    """
    try:
        rprint(f"[bold]Analyzing {strategy_type} strategy for {ticker}...[/bold]")

        # Import required modules for single strategy analysis
        from ...strategies.ma_cross.tools.strategy_execution import (
            execute_single_strategy,
        )
        from ...tools.get_data import get_data
        from ...tools.logging_context import logging_context

        with logging_context("cli_strategy_analyze", "strategy_analyze.log") as log:
            # Build configuration for single strategy analysis
            config_dict = {
                "TICKER": ticker,
                "STRATEGY_TYPE": strategy_type,
                "SHORT_WINDOW": fast_period or 20,  # Default values if not provided
                "LONG_WINDOW": slow_period or 50,
                "BASE_DIR": str(Path.cwd()),
                "REFRESH": True,
                "USE_HOURLY": False,
                "USE_YEARS": False,
                "YEARS": [],
                "DIRECTION": "BOTH",
                "USE_CURRENT": False,
                "USE_SYNTHETIC": False,
                "USE_GBM": False,
                "USE_SCANNER": False,
                "SCANNER_LIST": [],
                "SORT_BY": "Score",
                "SORT_ASC": False,
                "MINIMUMS": {},
            }

            rprint(f"Configuration:")
            rprint(f"  Ticker: {ticker}")
            rprint(f"  Strategy: {strategy_type}")
            rprint(f"  Fast Period: {config_dict['SHORT_WINDOW']}")
            rprint(f"  Slow Period: {config_dict['LONG_WINDOW']}")

            # Execute single strategy analysis
            result = execute_single_strategy(ticker, config_dict, log)

            if result:
                _display_detailed_analysis(result, ticker, strategy_type, show_trades)
                rprint(f"\n[green]Strategy analysis completed successfully![/green]")
            else:
                rprint(
                    "[red]Strategy analysis failed - no valid results generated[/red]"
                )

    except Exception as e:
        rprint(f"[red]Error analyzing strategy: {e}[/red]")
        raise typer.Exit(1)


def _show_config_preview(config: StrategyConfig):
    """Display configuration preview for dry run."""
    table = Table(title="Strategy Configuration Preview", show_header=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Ticker(s)", str(config.ticker))
    table.add_row("Strategy Types", ", ".join(config.strategy_types))
    table.add_row("Windows", str(config.windows))
    table.add_row("Direction", config.direction)
    table.add_row("Use Hourly", str(config.use_hourly))

    if config.minimums.win_rate:
        table.add_row("Min Win Rate", f"{config.minimums.win_rate:.2%}")
    if config.minimums.trades:
        table.add_row("Min Trades", str(config.minimums.trades))

    console.print(table)
    rprint("\n[yellow]This is a dry run. Use --no-dry-run to execute.[/yellow]")


def _show_sweep_preview(config: MACrossConfig):
    """Display parameter sweep preview."""
    table = Table(title="Parameter Sweep Preview", show_header=True)
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Ticker", str(config.ticker))
    table.add_row("Strategy Types", ", ".join(config.strategy_types))
    table.add_row("Fast Period Range", str(config.fast_period_range))
    table.add_row("Slow Period Range", str(config.slow_period_range))

    if config.fast_period_range and config.slow_period_range:
        fast_count = config.fast_period_range[1] - config.fast_period_range[0] + 1
        slow_count = config.slow_period_range[1] - config.slow_period_range[0] + 1
        total_combinations = fast_count * slow_count * len(config.strategy_types)
        table.add_row("Total Combinations", str(total_combinations))

    console.print(table)
    rprint("\n[yellow]This is a dry run. Use --no-dry-run to execute.[/yellow]")


def _convert_to_legacy_config(config: StrategyConfig) -> dict:
    """Convert Pydantic StrategyConfig to legacy config format.

    Maps lowercase field names to uppercase field names expected by
    existing strategy execution modules.
    """
    legacy_config = {
        # Core fields - these are required
        "TICKER": config.ticker,  # Pass the full list or string
        "WINDOWS": config.windows,
        "BASE_DIR": str(config.base_dir),
        # Strategy execution fields
        "STRATEGY_TYPES": config.strategy_types,
        "DIRECTION": config.direction,
        "USE_HOURLY": config.use_hourly,
        "USE_YEARS": config.use_years,
        "YEARS": config.years,
        "REFRESH": config.refresh,
        # Filtering minimums
        "MINIMUMS": {},
        # Synthetic ticker support
        "USE_SYNTHETIC": config.synthetic.use_synthetic,
        # Additional features
        "USE_GBM": config.use_gbm,
        "USE_SCANNER": config.use_scanner,
        "SCANNER_LIST": config.scanner_list,
        # Display and sorting
        "SORT_BY": config.sort_by,
        "SORT_ASC": config.sort_ascending,
        "USE_CURRENT": config.filter.use_current,
    }

    # Add minimums if they exist
    if config.minimums.win_rate is not None:
        legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
    if config.minimums.trades is not None:
        legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
    if config.minimums.expectancy_per_trade is not None:
        legacy_config["MINIMUMS"][
            "EXPECTANCY_PER_TRADE"
        ] = config.minimums.expectancy_per_trade
    if config.minimums.profit_factor is not None:
        legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
    if config.minimums.sortino_ratio is not None:
        legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
    if config.minimums.beats_bnh is not None:
        legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh

    # Handle synthetic ticker configuration
    if config.synthetic.use_synthetic:
        if config.synthetic.ticker_1:
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
        if config.synthetic.ticker_2:
            legacy_config["TICKER_2"] = config.synthetic.ticker_2

    return legacy_config


def _convert_sweep_to_legacy_config(config) -> dict:
    """Convert MACrossConfig to legacy config format for parameter sweep."""
    legacy_config = {
        # Core fields
        "TICKER": config.ticker,
        "BASE_DIR": str(config.base_dir),
        "REFRESH": config.refresh,
        # Strategy execution fields
        "STRATEGY_TYPES": config.strategy_types,
        "DIRECTION": config.direction,
        "USE_HOURLY": config.use_hourly,
        "USE_YEARS": config.use_years,
        "YEARS": config.years,
        # Filtering minimums
        "MINIMUMS": {},
        # Synthetic ticker support (inherited from base config)
        "USE_SYNTHETIC": getattr(config, "use_synthetic", False),
        # Additional features (inherited from base config)
        "USE_GBM": getattr(config, "use_gbm", False),
        "USE_SCANNER": getattr(config, "use_scanner", False),
        "SCANNER_LIST": getattr(config, "scanner_list", []),
        # Display and sorting
        "SORT_BY": config.sort_by,
        "SORT_ASC": config.sort_ascending,
        "USE_CURRENT": config.filter.use_current,
        # Parameter sweep specific
        "FAST_PERIOD_RANGE": config.fast_period_range,
        "SLOW_PERIOD_RANGE": config.slow_period_range,
    }

    # Add minimums if they exist
    if config.minimums.win_rate is not None:
        legacy_config["MINIMUMS"]["WIN_RATE"] = config.minimums.win_rate
    if config.minimums.trades is not None:
        legacy_config["MINIMUMS"]["TRADES"] = config.minimums.trades
    if config.minimums.expectancy_per_trade is not None:
        legacy_config["MINIMUMS"][
            "EXPECTANCY_PER_TRADE"
        ] = config.minimums.expectancy_per_trade
    if config.minimums.profit_factor is not None:
        legacy_config["MINIMUMS"]["PROFIT_FACTOR"] = config.minimums.profit_factor
    if config.minimums.sortino_ratio is not None:
        legacy_config["MINIMUMS"]["SORTINO_RATIO"] = config.minimums.sortino_ratio
    if config.minimums.beats_bnh is not None:
        legacy_config["MINIMUMS"]["BEATS_BNH"] = config.minimums.beats_bnh

    return legacy_config


def _display_results(results: List, config: StrategyConfig):
    """Display strategy analysis results."""
    if not results:
        return

    # Create results table
    table = Table(title="Strategy Analysis Results", show_header=True)
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Strategy", style="blue", no_wrap=True)
    table.add_column("Score", style="green", justify="right")
    table.add_column("Win Rate", style="yellow", justify="right")
    table.add_column("Trades", style="white", justify="right")
    table.add_column("Return %", style="magenta", justify="right")

    # Sort results by score if available
    sorted_results = sorted(results, key=lambda x: x.get("Score", 0), reverse=True)

    # Display top results
    for result in sorted_results[:20]:  # Show top 20
        ticker = result.get("Ticker", "N/A")
        strategy = result.get("Strategy", "N/A")
        score = result.get("Score", 0)
        win_rate = result.get("Win Rate [%]", 0)
        trades = result.get("Total Trades", 0)
        total_return = result.get("Total Return [%]", 0)

        table.add_row(
            ticker,
            strategy,
            f"{score:.2f}",
            f"{win_rate:.1f}%",
            str(int(trades)),
            f"{total_return:.1f}%",
        )

    console.print(table)

    if len(sorted_results) > 20:
        rprint(f"\n[dim]Showing top 20 results of {len(sorted_results)} total[/dim]")


def _display_sweep_results(results: List, config):
    """Display parameter sweep results with MA period information."""
    if not results:
        return

    # Create sweep results table
    table = Table(title="Parameter Sweep Results", show_header=True)
    table.add_column("Rank", style="white", no_wrap=True, justify="right")
    table.add_column("Strategy", style="blue", no_wrap=True)
    table.add_column("Fast", style="cyan", justify="right")
    table.add_column("Slow", style="cyan", justify="right")
    table.add_column("Score", style="green", justify="right")
    table.add_column("Win Rate", style="yellow", justify="right")
    table.add_column("Trades", style="white", justify="right")
    table.add_column("Return %", style="magenta", justify="right")
    table.add_column("Sharpe", style="bright_blue", justify="right")

    # Display results with rank
    for i, result in enumerate(results, 1):
        strategy = result.get("Strategy Type", "N/A")
        fast_period = result.get("Short Window", 0)
        slow_period = result.get("Long Window", 0)
        score = result.get("Score", 0)
        win_rate = result.get("Win Rate [%]", 0)
        trades = result.get("Total Trades", 0)
        total_return = result.get("Total Return [%]", 0)
        sharpe = result.get("Sharpe Ratio", 0)

        table.add_row(
            str(i),
            strategy,
            str(int(fast_period)),
            str(int(slow_period)),
            f"{score:.2f}",
            f"{win_rate:.1f}%",
            str(int(trades)),
            f"{total_return:.1f}%",
            f"{sharpe:.2f}",
        )

    console.print(table)


def _display_detailed_analysis(
    result: dict, ticker: str, strategy_type: str, show_trades: bool
):
    """Display detailed analysis of a single strategy configuration."""

    # Strategy Overview Table
    overview_table = Table(
        title=f"Strategy Analysis: {ticker} - {strategy_type}", show_header=True
    )
    overview_table.add_column("Metric", style="cyan", no_wrap=True)
    overview_table.add_column("Value", style="green")

    # Core Performance Metrics
    overview_table.add_row("Strategy Type", result.get("Strategy Type", "N/A"))
    overview_table.add_row("Fast Period", str(result.get("Short Window", "N/A")))
    overview_table.add_row("Slow Period", str(result.get("Long Window", "N/A")))
    overview_table.add_row("Overall Score", f"{result.get('Score', 0):.2f}")

    # Separator
    overview_table.add_section()

    # Performance Metrics
    overview_table.add_row("Total Return", f"{result.get('Total Return [%]', 0):.2f}%")
    overview_table.add_row(
        "Buy & Hold Return", f"{result.get('Buy & Hold Return [%]', 0):.2f}%"
    )
    overview_table.add_row("Win Rate", f"{result.get('Win Rate [%]', 0):.1f}%")
    overview_table.add_row("Total Trades", str(int(result.get("Total Trades", 0))))
    overview_table.add_row("Profit Factor", f"{result.get('Profit Factor', 0):.2f}")

    # Separator
    overview_table.add_section()

    # Risk Metrics
    overview_table.add_row("Sharpe Ratio", f"{result.get('Sharpe Ratio', 0):.2f}")
    overview_table.add_row("Sortino Ratio", f"{result.get('Sortino Ratio', 0):.2f}")
    overview_table.add_row("Max Drawdown", f"{result.get('Max Drawdown [%]', 0):.2f}%")
    overview_table.add_row("Volatility", f"{result.get('Volatility [%]', 0):.2f}%")

    # Separator
    overview_table.add_section()

    # Additional Metrics
    overview_table.add_row(
        "Expectancy per Trade", f"{result.get('Expectancy per Trade', 0):.2f}"
    )
    overview_table.add_row("Average Win", f"{result.get('Avg. Win [%]', 0):.2f}%")
    overview_table.add_row("Average Loss", f"{result.get('Avg. Loss [%]', 0):.2f}%")
    overview_table.add_row("Largest Win", f"{result.get('Best Trade [%]', 0):.2f}%")
    overview_table.add_row("Largest Loss", f"{result.get('Worst Trade [%]', 0):.2f}%")

    # Signal Information
    if result.get("Signal Entry") is not None:
        overview_table.add_section()
        signal_status = "🟢 BUY" if result.get("Signal Entry") else "🔴 NO SIGNAL"
        overview_table.add_row("Current Signal", signal_status)

    console.print(overview_table)

    # Performance Summary
    total_return = result.get("Total Return [%]", 0)
    bnh_return = result.get("Buy & Hold Return [%]", 0)
    outperformance = total_return - bnh_return

    rprint(f"\n[bold]Performance Summary:[/bold]")
    if outperformance > 0:
        rprint(
            f"📈 Strategy outperformed Buy & Hold by [green]{outperformance:.2f}%[/green]"
        )
    else:
        rprint(
            f"📉 Strategy underperformed Buy & Hold by [red]{abs(outperformance):.2f}%[/red]"
        )

    # Risk Assessment
    sharpe = result.get("Sharpe Ratio", 0)
    max_dd = result.get("Max Drawdown [%]", 0)

    rprint(f"\n[bold]Risk Assessment:[/bold]")
    if sharpe > 1.0:
        rprint(f"🎯 Good risk-adjusted returns (Sharpe: {sharpe:.2f})")
    elif sharpe > 0.5:
        rprint(f"⚖️ Moderate risk-adjusted returns (Sharpe: {sharpe:.2f})")
    else:
        rprint(f"⚠️ Poor risk-adjusted returns (Sharpe: {sharpe:.2f})")

    if max_dd < 10:
        rprint(f"✅ Low maximum drawdown ({max_dd:.1f}%)")
    elif max_dd < 25:
        rprint(f"⚠️ Moderate maximum drawdown ({max_dd:.1f}%)")
    else:
        rprint(f"🚨 High maximum drawdown ({max_dd:.1f}%)")

    # Trade Analysis
    if show_trades:
        _display_trade_summary(result)


def _display_trade_summary(result: dict):
    """Display detailed trade statistics."""
    rprint(f"\n[bold]Trade Analysis:[/bold]")

    # Trade Statistics Table
    trade_table = Table(title="Trade Statistics", show_header=True)
    trade_table.add_column("Metric", style="cyan")
    trade_table.add_column("Value", style="white")

    total_trades = int(result.get("Total Trades", 0))
    win_rate = result.get("Win Rate [%]", 0)
    winning_trades = int(total_trades * win_rate / 100)
    losing_trades = total_trades - winning_trades

    trade_table.add_row("Total Trades", str(total_trades))
    trade_table.add_row("Winning Trades", f"{winning_trades} ({win_rate:.1f}%)")
    trade_table.add_row("Losing Trades", f"{losing_trades} ({100-win_rate:.1f}%)")

    trade_table.add_section()

    # Win/Loss Analysis
    avg_win = result.get("Avg. Win [%]", 0)
    avg_loss = result.get("Avg. Loss [%]", 0)
    best_trade = result.get("Best Trade [%]", 0)
    worst_trade = result.get("Worst Trade [%]", 0)

    trade_table.add_row("Average Win", f"{avg_win:.2f}%")
    trade_table.add_row("Average Loss", f"{avg_loss:.2f}%")
    trade_table.add_row(
        "Win/Loss Ratio", f"{abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}"
    )

    trade_table.add_section()

    trade_table.add_row("Best Trade", f"{best_trade:.2f}%")
    trade_table.add_row("Worst Trade", f"{worst_trade:.2f}%")

    console.print(trade_table)

    # Trading Frequency Analysis
    total_days = result.get("Total Period [Days]", 1)
    trades_per_year = (total_trades / total_days) * 365
    avg_holding_period = total_days / total_trades if total_trades > 0 else 0

    rprint(f"\n[bold]Trading Frequency:[/bold]")
    rprint(f"📊 Average trades per year: {trades_per_year:.1f}")
    rprint(f"⏱️ Average holding period: {avg_holding_period:.1f} days")
