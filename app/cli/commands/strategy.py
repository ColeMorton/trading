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
        None, "--years", "-y", help="Number of years of historical data to analyze (omit for complete history)"
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
        trading-cli strategy run --ticker BTC-USD --min-trades 20
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
            dry_run=dry_run,
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

        # Show execution progress
        tickers_to_process = (
            config.ticker if isinstance(config.ticker, list) else [config.ticker]
        )
        show_execution_progress(
            "Executing strategy analysis", ticker_count=len(tickers_to_process)
        )

        # Debug: Show all tickers that will be processed
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
