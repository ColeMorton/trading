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
from .strategy_utils import (
    build_configuration_overrides,
    convert_to_legacy_config,
    handle_command_error,
    show_config_preview,
    display_results_table,
    display_sweep_results_table,
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
        "-t",
        help="Ticker symbols to analyze (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)",
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
        trading-cli strategy run --ticker AAPL,MSFT,GOOGL --strategy SMA EMA
        trading-cli strategy run --ticker AAPL --ticker MSFT --strategy SMA
        trading-cli strategy run --ticker BTC-USD --windows 55 --min-trades 20
    """
    try:
        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides using shared utility
        overrides = build_configuration_overrides(
            ticker=ticker,
            strategy_type=strategy_type,
            windows=windows,
            min_trades=min_trades,
            min_win_rate=min_win_rate,
            dry_run=dry_run
        )

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            # Use default strategy template
            template = loader.get_config_template("strategy")
            config = loader.load_from_dict(template, StrategyConfig, overrides)

        # Validate parameter relationships
        validate_parameter_relationships(config)

        if dry_run:
            show_config_preview(config, "Strategy Configuration Preview")
            return

        if verbose:
            rprint("[dim]Loading strategy execution module...[/dim]")

        # Use the same implementation as direct execution
        import importlib

        ma_cross_module = importlib.import_module(
            "app.strategies.ma_cross.1_get_portfolios"
        )
        run = ma_cross_module.run

        # Show execution progress
        tickers_to_process = config.ticker if isinstance(config.ticker, list) else [config.ticker]
        show_execution_progress(
            "Executing strategy analysis",
            ticker_count=len(tickers_to_process)
        )

        # Convert Pydantic model to legacy config format using shared utility
        legacy_config = convert_to_legacy_config(config)

        # Debug: Show all tickers that will be processed
        rprint(
            f"[bold]Processing {len(tickers_to_process)} tickers:[/bold] {', '.join(tickers_to_process)}"
        )

        # Execute using the same function as direct execution
        # This ensures identical filtering, export, and aggregation behavior
        success = run(legacy_config)

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
        None, "--ticker", "-t", help="Ticker symbols for parameter sweep (multiple args or comma-separated: --ticker AAPL,MSFT or --ticker AAPL --ticker MSFT)"
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
            dry_run=dry_run
        )

        # Load configuration (use StrategyConfig instead of MACrossConfig for consistency)
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            template = loader.get_config_template("strategy")
            config = loader.load_from_dict(template, StrategyConfig, overrides)

        # Validate parameter relationships
        validate_parameter_relationships(config)

        if dry_run:
            show_config_preview(config, "Parameter Sweep Preview")
            return

        # Show configuration summary
        ticker_display = ", ".join(config.ticker) if isinstance(config.ticker, list) else config.ticker
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
                rprint("[yellow]Warning: No period ranges specified in profile. Using defaults.[/yellow]")
                rprint("[dim]For custom ranges, use: --fast-min X --fast-max Y --slow-min Z --slow-max W[/dim]")
                fast_range = config.fast_period_range or (5, 50)
                slow_range = config.slow_period_range or (20, 200)
            else:
                fast_range = config.fast_period_range
                slow_range = config.slow_period_range
            
            short_windows = list(range(fast_range[0], fast_range[1] + 1))
            long_windows = list(range(slow_range[0], slow_range[1] + 1))

            # Handle multiple tickers
            ticker_list = config.ticker if isinstance(config.ticker, list) else [config.ticker]
            
            # Calculate total combinations
            total_combinations = sum(
                1 for s in short_windows for l in long_windows if s < l
            ) * len(config.strategy_types) * len(ticker_list)
            
            show_execution_progress(
                "Executing parameter sweep",
                ticker_count=len(ticker_list),
                combination_count=total_combinations
            )

            all_results = []
            
            # Process each ticker individually
            for single_ticker in ticker_list:
                rprint(f"\n[bold]Processing parameter sweep for {single_ticker}...[/bold]")
                
                # Get price data for single ticker
                rprint(f"Fetching price data for {single_ticker}...")
                data = get_data(single_ticker, legacy_config, log)
                if data is None:
                    rprint(f"[red]Failed to fetch price data for {single_ticker}[/red]")
                    continue

                for strategy_type in config.strategy_types:
                    rprint(f"Running {strategy_type} parameter sweep for {single_ticker}...")

                    # Set strategy type in legacy config
                    strategy_config = legacy_config.copy()
                    strategy_config["STRATEGY_TYPE"] = strategy_type
                    strategy_config["TICKER"] = single_ticker  # Ensure single ticker in config

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
                portfolio_dir = legacy_config["BASE_DIR"] + "/csv/portfolios/"
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
        None, "--ticker", "-t", help="Ticker symbol(s) to analyze (multiple args or comma-separated)"
    ),
    strategy_type: Optional[List[str]] = typer.Option(
        ["SMA", "EMA"], "--strategy", "-s", help="Strategy types: SMA, EMA, MACD (can be used multiple times)"
    ),
    fast_period: Optional[int] = typer.Option(
        None, "--fast", help="Fast period parameter"
    ),
    slow_period: Optional[int] = typer.Option(
        None, "--slow", help="Slow period parameter"
    ),
    show_trades: bool = typer.Option(
        True, "--show-trades/--no-show-trades", help="Show individual trade details (default: True)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview configuration without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Analyze strategy configurations for one or more tickers.

    This command provides detailed analysis of specific strategy
    configurations including performance metrics and trade details.
    By default, analyzes both SMA and EMA strategies with trade details shown.

    Examples:
        trading-cli strategy analyze --ticker AAPL  # Analyzes SMA and EMA with trade details
        trading-cli strategy analyze --ticker AAPL --strategy MACD --fast 12 --slow 26
        trading-cli strategy analyze --ticker AAPL,MSFT,GOOGL --strategy SMA --no-show-trades
        trading-cli strategy analyze --ticker BTC-USD --strategy SMA --strategy EMA
    """
    try:
        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides using shared utility
        overrides = build_configuration_overrides(
            ticker=ticker,
            strategy_type=strategy_type,
            fast_period=fast_period,
            slow_period=slow_period,
            dry_run=dry_run
        )

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, StrategyConfig, overrides)
        else:
            template = loader.get_config_template("strategy")
            config = loader.load_from_dict(template, StrategyConfig, overrides)

        # Validate parameter relationships
        validate_parameter_relationships(config)

        # Handle default ticker if none specified
        if not config.ticker:
            rprint("[red]Error: No ticker specified. Use --ticker option or configure in profile.[/red]")
            raise typer.Exit(1)

        # Ensure ticker is a list for consistent processing
        ticker_list = config.ticker if isinstance(config.ticker, list) else [config.ticker]

        if dry_run:
            show_config_preview(config, "Strategy Analysis Preview")
            return

        show_execution_progress(
            f"Analyzing {', '.join(config.strategy_types)} strategies",
            ticker_count=len(ticker_list)
        )

        # Import required modules for single strategy analysis
        from ...strategies.ma_cross.tools.strategy_execution import (
            execute_single_strategy,
        )
        from ...tools.get_data import get_data
        from ...tools.logging_context import logging_context

        all_results = []

        with logging_context("cli_strategy_analyze", "strategy_analyze.log") as log:
            for single_ticker in ticker_list:
                for single_strategy in config.strategy_types:
                    rprint(f"\n[bold]Processing {single_ticker} with {single_strategy}...[/bold]")
                    
                    # Build configuration for single strategy analysis using shared utility
                    legacy_config = convert_to_legacy_config(config)
                    legacy_config.update({
                        "TICKER": single_ticker,
                        "STRATEGY_TYPE": single_strategy,
                        "SHORT_WINDOW": config.fast_period or 20,  # Default values if not provided
                        "LONG_WINDOW": config.slow_period or 50,
                    })

                    if verbose:
                        rprint(f"Configuration:")
                        rprint(f"  Ticker: {single_ticker}")
                        rprint(f"  Strategy: {single_strategy}")
                        rprint(f"  Fast Period: {legacy_config['SHORT_WINDOW']}")
                        rprint(f"  Slow Period: {legacy_config['LONG_WINDOW']}")

                    # Execute single strategy analysis
                    result = execute_single_strategy(single_ticker, legacy_config, log)

                    if result:
                        all_results.append(result)
                        if len(ticker_list) == 1 and len(config.strategy_types) == 1:
                            # For single ticker and single strategy, show detailed analysis
                            _display_detailed_analysis(result, single_ticker, single_strategy, show_trades)
                    else:
                        rprint(f"[yellow]No valid results for {single_ticker} with {single_strategy}[/yellow]")

        if all_results:
            if len(ticker_list) > 1 or len(config.strategy_types) > 1:
                # For multiple tickers or strategies, show summary table using shared utility
                display_results_table(all_results, "Strategy Analysis Results")
            rprint(f"\n[green]Strategy analysis completed successfully![/green]")
        else:
            rprint(
                "[red]Strategy analysis failed - no valid results generated[/red]"
            )

    except Exception as e:
        handle_command_error(e, "strategy analyze", verbose)


# Legacy display function still needed for detailed analysis
# Will be refactored in a future iteration


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
