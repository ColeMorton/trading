"""
Shared utilities for strategy commands.

This module provides common functions used across all strategy sub-commands
to ensure consistency and eliminate code duplication.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..models.strategy import StrategyConfig

console = Console()


def _calculate_windows_from_ranges(config) -> int:
    """
    Calculate WINDOWS value from fast_period_range and slow_period_range.

    For legacy compatibility, returns the maximum slow period range value,
    or a sensible default if ranges are not specified.
    """
    if hasattr(config, "slow_period_range") and config.slow_period_range:
        return config.slow_period_range[1]  # Use max slow period
    elif hasattr(config, "fast_period_range") and config.fast_period_range:
        return config.fast_period_range[1] * 2  # Estimate reasonable slow max
    else:
        return 89  # Default fallback


def process_ticker_input(ticker: Optional[List[str]]) -> List[str]:
    """
    Process ticker input handling comma-separated values and multiple arguments.

    Args:
        ticker: List of ticker strings (may contain comma-separated values)

    Returns:
        Flattened list of ticker symbols in uppercase

    Examples:
        process_ticker_input(["AAPL,MSFT", "GOOGL"]) -> ["AAPL", "MSFT", "GOOGL"]
        process_ticker_input(["BTC-USD"]) -> ["BTC-USD"]
    """
    if not ticker:
        return []

    flattened_tickers = []
    for t in ticker:
        if "," in t:
            # Split comma-separated values and add to list
            flattened_tickers.extend(
                [tick.strip().upper() for tick in t.split(",") if tick.strip()]
            )
        else:
            # Single ticker value
            flattened_tickers.append(t.strip().upper())

    return flattened_tickers


def build_configuration_overrides(
    ticker: Optional[List[str]] = None,
    strategy_type: Optional[List[str]] = None,
    min_trades: Optional[int] = None,
    min_win_rate: Optional[float] = None,
    fast_min: Optional[int] = None,
    fast_max: Optional[int] = None,
    slow_min: Optional[int] = None,
    slow_max: Optional[int] = None,
    fast_period: Optional[int] = None,
    slow_period: Optional[int] = None,
    dry_run: bool = False,
    **additional_overrides,
) -> Dict[str, Any]:
    """
    Build configuration overrides from CLI arguments.

    Args:
        ticker: Ticker symbols
        strategy_type: Strategy types
        min_trades: Minimum trades filter
        min_win_rate: Minimum win rate filter
        fast_min: Fast period minimum for sweep
        fast_max: Fast period maximum for sweep
        slow_min: Slow period minimum for sweep
        slow_max: Slow period maximum for sweep
        fast_period: Fast period for single analysis
        slow_period: Slow period for single analysis
        dry_run: Dry run flag
        **additional_overrides: Additional override parameters

    Returns:
        Dictionary of configuration overrides
    """
    overrides = {}

    # Process ticker input
    if ticker:
        overrides["ticker"] = process_ticker_input(ticker)

    # Strategy types
    if strategy_type:
        overrides["strategy_types"] = strategy_type

    # Minimums configuration
    if min_trades or min_win_rate:
        minimums = {}
        if min_trades:
            minimums["trades"] = min_trades
        if min_win_rate:
            minimums["win_rate"] = min_win_rate
        overrides["minimums"] = minimums

    # Parameter sweep ranges
    if fast_min and fast_max:
        overrides["fast_period_range"] = (fast_min, fast_max)
    if slow_min and slow_max:
        overrides["slow_period_range"] = (slow_min, slow_max)

    # Single analysis periods
    if fast_period:
        overrides["fast_period"] = fast_period
    if slow_period:
        overrides["slow_period"] = slow_period

    # System flags
    overrides["dry_run"] = dry_run

    # Add any additional overrides
    overrides.update(additional_overrides)

    return overrides


def convert_to_legacy_config(
    config: StrategyConfig, **additional_params
) -> Dict[str, Any]:
    """
    Convert Pydantic StrategyConfig to legacy config format.

    Maps lowercase field names to uppercase field names expected by
    existing strategy execution modules. This replaces both
    _convert_to_legacy_config and _convert_sweep_to_legacy_config.

    Args:
        config: Pydantic StrategyConfig object
        **additional_params: Additional parameters to include in legacy config

    Returns:
        Dictionary in legacy config format
    """
    legacy_config = {
        # Core fields - these are required
        "TICKER": config.ticker,  # Pass the full list or string
        "FAST_PERIOD_RANGE": config.fast_period_range,
        "SLOW_PERIOD_RANGE": config.slow_period_range,
        "BASE_DIR": str(config.base_dir),
        # Strategy execution fields
        "STRATEGY_TYPES": config.strategy_types,
        "DIRECTION": config.direction,
        "USE_HOURLY": config.use_hourly,
        "USE_YEARS": config.use_years,
        "YEARS": config.years,
        "REFRESH": config.refresh,
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

    # Add minimums if they exist - only add non-empty MINIMUMS dict to avoid unwanted filtering
    minimums_dict = {}
    if config.minimums.win_rate is not None:
        minimums_dict["WIN_RATE"] = config.minimums.win_rate
    if config.minimums.trades is not None:
        minimums_dict["TRADES"] = config.minimums.trades
    if config.minimums.expectancy_per_trade is not None:
        minimums_dict["EXPECTANCY_PER_TRADE"] = config.minimums.expectancy_per_trade
    if config.minimums.profit_factor is not None:
        minimums_dict["PROFIT_FACTOR"] = config.minimums.profit_factor
    if config.minimums.sortino_ratio is not None:
        minimums_dict["SORTINO_RATIO"] = config.minimums.sortino_ratio
    if config.minimums.beats_bnh is not None:
        minimums_dict["BEATS_BNH"] = config.minimums.beats_bnh

    # Only set MINIMUMS if there are actual minimum values to avoid unwanted filtering
    if minimums_dict:
        legacy_config["MINIMUMS"] = minimums_dict

    # Handle synthetic ticker configuration
    if config.synthetic.use_synthetic:
        if config.synthetic.ticker_1:
            legacy_config["TICKER_1"] = config.synthetic.ticker_1
        if config.synthetic.ticker_2:
            legacy_config["TICKER_2"] = config.synthetic.ticker_2

    # Add additional parameters for specific command types
    legacy_config.update(additional_params)

    return legacy_config


def handle_command_error(
    error: Exception, command_name: str, verbose: bool = False
) -> None:
    """
    Handle command errors consistently across all strategy sub-commands.

    Args:
        error: The exception that occurred
        command_name: Name of the command for error reporting
        verbose: Whether to show detailed error information
    """
    rprint(f"[red]Error executing {command_name}: {error}[/red]")

    if verbose:
        import traceback

        traceback.print_exc()
        raise

    raise typer.Exit(1)


def show_config_preview(
    config: StrategyConfig, title: str = "Configuration Preview"
) -> None:
    """
    Display configuration preview for dry run mode.

    Args:
        config: Configuration to preview
        title: Table title
    """
    table = Table(title=title, show_header=True)
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    table.add_row("Ticker(s)", str(config.ticker))
    table.add_row("Strategy Types", ", ".join(config.strategy_types))
    table.add_row("Direction", config.direction)
    table.add_row("Use Hourly", str(config.use_hourly))

    if config.minimums.win_rate:
        table.add_row("Min Win Rate", f"{config.minimums.win_rate:.2%}")
    if config.minimums.trades:
        table.add_row("Min Trades", str(config.minimums.trades))

    # Show sweep-specific parameters if available
    if hasattr(config, "fast_period_range") and config.fast_period_range:
        table.add_row("Fast Period Range", str(config.fast_period_range))
    if hasattr(config, "slow_period_range") and config.slow_period_range:
        table.add_row("Slow Period Range", str(config.slow_period_range))

    # Show single analysis parameters if available
    if hasattr(config, "fast_period") and config.fast_period:
        table.add_row("Fast Period", str(config.fast_period))
    if hasattr(config, "slow_period") and config.slow_period:
        table.add_row("Slow Period", str(config.slow_period))

    console.print(table)
    rprint("\n[yellow]This is a dry run. Use --no-dry-run to execute.[/yellow]")


def display_results_table(
    results: List[Dict[str, Any]],
    title: str = "Strategy Analysis Results",
    max_results: int = 20,
) -> None:
    """
    Display strategy analysis results in a consistent table format.

    Args:
        results: List of result dictionaries
        title: Table title
        max_results: Maximum number of results to display
    """
    if not results:
        rprint("[yellow]No results to display[/yellow]")
        return

    # Create results table
    table = Table(title=title, show_header=True)
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Strategy", style="blue", no_wrap=True)
    table.add_column("Score", style="green", justify="right")
    table.add_column("Win Rate", style="yellow", justify="right")
    table.add_column("Trades", style="white", justify="right")
    table.add_column("Return %", style="magenta", justify="right")

    # Sort results by score if available
    sorted_results = sorted(results, key=lambda x: x.get("Score", 0), reverse=True)

    # Display results
    for result in sorted_results[:max_results]:
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

    if len(sorted_results) > max_results:
        rprint(
            f"\n[dim]Showing top {max_results} results of {len(sorted_results)} total[/dim]"
        )


def display_sweep_results_table(
    results: List[Dict[str, Any]],
    title: str = "Parameter Sweep Results",
    max_results: int = 50,
) -> None:
    """
    Display parameter sweep results with MA period information.

    Args:
        results: List of sweep result dictionaries
        title: Table title
        max_results: Maximum number of results to display
    """
    if not results:
        rprint("[yellow]No sweep results to display[/yellow]")
        return

    # Create sweep results table
    table = Table(title=title, show_header=True)
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
    for i, result in enumerate(results[:max_results], 1):
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


def show_execution_progress(
    message: str, ticker_count: int = None, combination_count: int = None
) -> None:
    """
    Display consistent execution progress messages.

    Args:
        message: Progress message to display
        ticker_count: Number of tickers being processed
        combination_count: Number of combinations being analyzed
    """
    rprint(f"[bold]{message}[/bold]")

    if ticker_count:
        rprint(f"Processing {ticker_count} ticker(s)...")

    if combination_count:
        rprint(f"Analyzing {combination_count} parameter combinations...")


def validate_parameter_relationships(config: StrategyConfig) -> None:
    """
    Validate parameter relationships across the configuration.

    Args:
        config: Configuration to validate

    Raises:
        ValueError: If parameter relationships are invalid
    """
    # Validate period ranges for sweeps
    if hasattr(config, "fast_period_range") and hasattr(config, "slow_period_range"):
        if config.fast_period_range and config.slow_period_range:
            if config.fast_period_range[1] >= config.slow_period_range[0]:
                rprint(
                    "[yellow]Warning: Fast period range overlaps with slow period range[/yellow]"
                )

    # Validate single periods
    if hasattr(config, "fast_period") and hasattr(config, "slow_period"):
        if config.fast_period and config.slow_period:
            if config.fast_period >= config.slow_period:
                raise ValueError("Fast period must be less than slow period")

    # Validate minimums
    if config.minimums.win_rate is not None:
        if not 0 <= config.minimums.win_rate <= 1:
            raise ValueError("Win rate must be between 0 and 1")

    if config.minimums.trades is not None:
        if config.minimums.trades < 0:
            raise ValueError("Minimum trades must be non-negative")
