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

from app.tools.console_logging import ConsoleLogger

from ..models.strategy import StrategyConfig

console = Console()


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
    ticker_2: Optional[str] = None,
    strategy_type: Optional[List[str]] = None,
    min_trades: Optional[int] = None,
    min_win_rate: Optional[float] = None,
    fast_min: Optional[int] = None,
    fast_max: Optional[int] = None,
    slow_min: Optional[int] = None,
    slow_max: Optional[int] = None,
    signal_min: Optional[int] = None,
    signal_max: Optional[int] = None,
    fast_period: Optional[int] = None,
    slow_period: Optional[int] = None,
    years: Optional[int] = None,
    market_type: Optional[str] = None,
    use_4hour: Optional[bool] = None,
    direction: Optional[str] = None,
    date: Optional[str] = None,
    dry_run: bool = False,
    skip_analysis: bool = False,
    verbose: bool = False,
    performance_mode: str = "minimal",
    show_resources: bool = False,
    profile_execution: bool = False,
    **additional_overrides,
) -> Dict[str, Any]:
    """
    Build configuration overrides from CLI arguments.

    Args:
        ticker: Ticker symbols
        ticker_2: Second ticker for synthetic pair analysis
        strategy_type: Strategy types
        min_trades: Minimum trades filter
        min_win_rate: Minimum win rate filter
        fast_min: Fast period minimum for sweep
        fast_max: Fast period maximum for sweep
        slow_min: Slow period minimum for sweep
        slow_max: Slow period maximum for sweep
        signal_min: Signal period minimum for sweep
        signal_max: Signal period maximum for sweep
        fast_period: Fast period for single analysis
        slow_period: Slow period for single analysis
        years: Number of years of historical data to analyze (enables year-based analysis when provided)
        market_type: Market type for trading hours (crypto, us_stock, auto)
        date: Filter by entry signals triggered on specific date (YYYYMMDD format)
        dry_run: Dry run flag
        skip_analysis: Skip data download and analysis, assume portfolio files exist
        performance_mode: Performance monitoring level (minimal/standard/detailed/benchmark)
        show_resources: Display real-time CPU and memory usage during execution
        profile_execution: Enable detailed execution profiling with bottleneck identification
        **additional_overrides: Additional override parameters

    Returns:
        Dictionary of configuration overrides
    """
    overrides = {}

    # Handle ticker input - different behavior for synthetic vs normal mode
    if ticker_2:
        # Synthetic mode: don't set ticker field at all to allow synthetic processing
        # The synthetic ticker will be created by process_synthetic_config
        synthetic_config = {"use_synthetic": True, "ticker_2": ticker_2.strip().upper()}
        # If ticker is provided, use the first one as ticker_1
        if ticker:
            processed_tickers = process_ticker_input(ticker)
            if processed_tickers:
                synthetic_config["ticker_1"] = processed_tickers[0]
        overrides["synthetic"] = synthetic_config
    elif ticker:
        # Normal mode: process ticker input as usual
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

    # Track which CLI parameters were provided for accurate source detection
    cli_params_provided = {
        "fast": fast_min is not None and fast_max is not None,
        "slow": slow_min is not None and slow_max is not None,
        "signal": signal_min is not None and signal_max is not None,
    }
    overrides["_cli_params_provided"] = cli_params_provided

    # Parameter sweep ranges - use new min/max structure primarily
    if fast_min is not None:
        overrides["fast_period_min"] = fast_min
    if fast_max is not None:
        overrides["fast_period_max"] = fast_max
    if fast_min and fast_max:
        # Also set legacy range for backwards compatibility
        overrides["fast_period_range"] = (fast_min, fast_max)

    if slow_min is not None:
        overrides["slow_period_min"] = slow_min
    if slow_max is not None:
        overrides["slow_period_max"] = slow_max
    if slow_min and slow_max:
        # Also set legacy range for backwards compatibility
        overrides["slow_period_range"] = (slow_min, slow_max)

    if signal_min is not None:
        overrides["signal_period_min"] = signal_min
    if signal_max is not None:
        overrides["signal_period_max"] = signal_max
    if signal_min and signal_max:
        # Also set legacy range for backwards compatibility
        overrides["signal_period_range"] = (signal_min, signal_max)

    # Single analysis periods
    if fast_period:
        overrides["fast_period"] = fast_period
    if slow_period:
        overrides["slow_period"] = slow_period

    # Time configuration
    if years is not None:
        if years <= 0:
            raise ValueError("Years parameter must be a positive integer")
        # When years is provided, enable year-based analysis
        overrides["use_years"] = True
        overrides["years"] = years
    else:
        # When years is omitted, use complete history (disable year-based analysis)
        overrides["use_years"] = False

    # Market type configuration
    if market_type:
        overrides["market_type"] = market_type

    # Direction configuration
    if direction:
        overrides["direction"] = direction

    # Timeframe configuration
    if use_4hour is not None:
        overrides["use_4hour"] = use_4hour

    # Filter configuration
    if date is not None:
        filter_overrides = {}
        filter_overrides["date_filter"] = date
        # Override use_current if date is specified
        filter_overrides["use_current"] = False
        overrides["filter"] = filter_overrides

    # System flags
    overrides["dry_run"] = dry_run
    if skip_analysis is not None:
        overrides["skip_analysis"] = skip_analysis
    overrides["verbose"] = verbose

    # Performance monitoring flags
    overrides["performance_mode"] = performance_mode
    overrides["show_resources"] = show_resources
    overrides["profile_execution"] = profile_execution

    # Add any additional overrides, but filter out None values for optional CLI parameters
    filtered_overrides = {
        k: v for k, v in additional_overrides.items() if v is not None
    }
    overrides.update(filtered_overrides)

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
        "BASE_DIR": str(config.base_dir),
    }

    # Parameter range mapping - prioritize strategy-specific params, then global params, then legacy
    # Priority: strategy-specific params > individual min/max fields > legacy range fields > legacy window fields

    def get_strategy_params_for_active_strategies():
        """Get strategy-specific parameters for the first available strategy type."""
        if not config.strategy_params:
            return None

        # Check strategy types in order of precedence
        for strategy_type in config.strategy_types:
            strategy_name = (
                strategy_type.value
                if hasattr(strategy_type, "value")
                else str(strategy_type)
            )
            if hasattr(config.strategy_params, strategy_name):
                strategy_params = getattr(config.strategy_params, strategy_name)
                if strategy_params:
                    return strategy_params
        return None

    strategy_params = get_strategy_params_for_active_strategies()

    # Fast period range mapping - CLI overrides take precedence over strategy-specific parameters
    if config.fast_period_min is not None and config.fast_period_max is not None:
        fast_range = (config.fast_period_min, config.fast_period_max)
    elif (
        strategy_params
        and strategy_params.fast_period_min is not None
        and strategy_params.fast_period_max is not None
    ):
        fast_range = (strategy_params.fast_period_min, strategy_params.fast_period_max)
    elif config.fast_period_range is not None:
        fast_range = config.fast_period_range
    elif config.short_window_start is not None and config.short_window_end is not None:
        # Legacy MACD window mapping to fast period
        fast_range = (config.short_window_start, config.short_window_end)
    else:
        fast_range = None

    if fast_range:
        legacy_config["FAST_PERIOD_RANGE"] = fast_range
        # Legacy MACD parameter mapping
        legacy_config["SHORT_WINDOW_START"] = fast_range[0]
        legacy_config["SHORT_WINDOW_END"] = fast_range[1]

    # Slow period range mapping - CLI overrides take precedence over strategy-specific parameters
    if config.slow_period_min is not None and config.slow_period_max is not None:
        slow_range = (config.slow_period_min, config.slow_period_max)
    elif (
        strategy_params
        and strategy_params.slow_period_min is not None
        and strategy_params.slow_period_max is not None
    ):
        slow_range = (strategy_params.slow_period_min, strategy_params.slow_period_max)
    elif config.slow_period_range is not None:
        slow_range = config.slow_period_range
    elif config.long_window_start is not None and config.long_window_end is not None:
        # Legacy MACD window mapping to slow period
        slow_range = (config.long_window_start, config.long_window_end)
    else:
        slow_range = None

    if slow_range:
        legacy_config["SLOW_PERIOD_RANGE"] = slow_range
        # Legacy MACD parameter mapping
        legacy_config["LONG_WINDOW_START"] = slow_range[0]
        legacy_config["LONG_WINDOW_END"] = slow_range[1]

    # Signal period range mapping - CLI overrides take precedence over strategy-specific parameters
    if config.signal_period_min is not None and config.signal_period_max is not None:
        signal_range = (config.signal_period_min, config.signal_period_max)
    elif (
        strategy_params
        and strategy_params.signal_period_min is not None
        and strategy_params.signal_period_max is not None
    ):
        signal_range = (
            strategy_params.signal_period_min,
            strategy_params.signal_period_max,
        )
    elif (
        hasattr(config, "signal_period_range")
        and config.signal_period_range is not None
    ):
        signal_range = config.signal_period_range
    elif (
        config.signal_window_start is not None and config.signal_window_end is not None
    ):
        # Legacy MACD window mapping to signal period
        signal_range = (config.signal_window_start, config.signal_window_end)
    else:
        signal_range = None

    if signal_range:
        legacy_config["SIGNAL_PERIOD_RANGE"] = signal_range
        # Legacy MACD parameter mapping
        legacy_config["SIGNAL_WINDOW_START"] = signal_range[0]
        legacy_config["SIGNAL_WINDOW_END"] = signal_range[1]

    # Add strategy-specific step parameter if available
    if strategy_params and strategy_params.step is not None:
        legacy_config["STEP"] = strategy_params.step

    # Individual period values
    if config.fast_period is not None:
        legacy_config["FAST_PERIOD"] = config.fast_period
    if config.slow_period is not None:
        legacy_config["SLOW_PERIOD"] = config.slow_period
    if config.signal_period is not None:
        legacy_config["SIGNAL_PERIOD"] = config.signal_period

    # MACD step parameter
    if config.step is not None:
        legacy_config["STEP"] = config.step

    legacy_config.update(
        {
            # Strategy execution fields
            "STRATEGY_TYPES": config.strategy_types,
            "DIRECTION": config.direction,
            "USE_HOURLY": config.use_hourly,
            "USE_4HOUR": config.use_4hour,
            "USE_2DAY": config.use_2day,
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
            "USE_DATE": config.filter.date_filter,
        }
    )

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
    error: Exception, command_name: str, verbose: bool = False, console=None
) -> None:
    """
    Handle command errors consistently across all strategy sub-commands.

    Args:
        error: The exception that occurred
        command_name: Name of the command for error reporting
        verbose: Whether to show detailed error information
        console: Console logger instance (optional)
    """
    if console:
        console.error(f"Error executing {command_name}: {error}")
        if verbose:
            console.debug("Full traceback available with --verbose flag")
    else:
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
    table.add_row("Use 4-Hour", str(config.use_4hour))
    table.add_row("Use 2-Day", str(config.use_2day))
    table.add_row("Skip Analysis", str(config.skip_analysis))

    if config.minimums.win_rate:
        table.add_row("Min Win Rate", f"{config.minimums.win_rate:.2%}")
    if config.minimums.trades:
        table.add_row("Min Trades", str(config.minimums.trades))

    # Show sweep-specific parameters - prioritize strategy-specific params over global params
    def get_active_strategy_params():
        """Get strategy-specific parameters for the first available strategy type."""
        if not config.strategy_params:
            return None

        # Check strategy types in order of precedence
        for strategy_type in config.strategy_types:
            strategy_name = (
                strategy_type.value
                if hasattr(strategy_type, "value")
                else str(strategy_type)
            )
            if hasattr(config.strategy_params, strategy_name):
                strategy_params = getattr(config.strategy_params, strategy_name)
                if strategy_params:
                    return strategy_params, strategy_name
        return None

    # Check CLI overrides first, then fall back to strategy-specific parameters
    cli_params_provided = getattr(config, "_cli_params_provided", {})
    has_cli_fast = cli_params_provided.get("fast", False)
    has_cli_slow = cli_params_provided.get("slow", False)
    has_cli_signal = cli_params_provided.get("signal", False)

    active_strategy_result = get_active_strategy_params()
    has_strategy_params = active_strategy_result is not None

    # Display CLI overrides with highest priority
    if has_cli_fast or has_cli_slow or has_cli_signal:
        table.add_row("Parameter Source", "CLI overrides")

        if has_cli_fast:
            table.add_row(
                "Fast Period Range",
                f"{config.fast_period_min}-{config.fast_period_max}",
            )
        elif has_strategy_params:
            strategy_params, _ = active_strategy_result
            if (
                strategy_params.fast_period_min is not None
                and strategy_params.fast_period_max is not None
            ):
                table.add_row(
                    "Fast Period Range",
                    f"{strategy_params.fast_period_min}-{strategy_params.fast_period_max}",
                )
        elif hasattr(config, "fast_period_range") and config.fast_period_range:
            table.add_row("Fast Period Range", str(config.fast_period_range))

        if has_cli_slow:
            table.add_row(
                "Slow Period Range",
                f"{config.slow_period_min}-{config.slow_period_max}",
            )
        elif has_strategy_params:
            strategy_params, _ = active_strategy_result
            if (
                strategy_params.slow_period_min is not None
                and strategy_params.slow_period_max is not None
            ):
                table.add_row(
                    "Slow Period Range",
                    f"{strategy_params.slow_period_min}-{strategy_params.slow_period_max}",
                )
        elif hasattr(config, "slow_period_range") and config.slow_period_range:
            table.add_row("Slow Period Range", str(config.slow_period_range))

        if has_cli_signal:
            table.add_row(
                "Signal Period Range",
                f"{config.signal_period_min}-{config.signal_period_max}",
            )
        elif has_strategy_params:
            strategy_params, _ = active_strategy_result
            if (
                strategy_params.signal_period_min is not None
                and strategy_params.signal_period_max is not None
            ):
                table.add_row(
                    "Signal Period Range",
                    f"{strategy_params.signal_period_min}-{strategy_params.signal_period_max}",
                )
        elif hasattr(config, "signal_period_range") and getattr(
            config, "signal_period_range", None
        ):
            table.add_row("Signal Period Range", str(config.signal_period_range))

    elif has_strategy_params:
        # Fall back to strategy-specific parameters
        strategy_params, strategy_name = active_strategy_result
        table.add_row("Parameter Source", f"Strategy-specific ({strategy_name})")

        if (
            strategy_params.fast_period_min is not None
            and strategy_params.fast_period_max is not None
        ):
            table.add_row(
                "Fast Period Range",
                f"{strategy_params.fast_period_min}-{strategy_params.fast_period_max}",
            )
        if (
            strategy_params.slow_period_min is not None
            and strategy_params.slow_period_max is not None
        ):
            table.add_row(
                "Slow Period Range",
                f"{strategy_params.slow_period_min}-{strategy_params.slow_period_max}",
            )
        if (
            strategy_params.signal_period_min is not None
            and strategy_params.signal_period_max is not None
        ):
            table.add_row(
                "Signal Period Range",
                f"{strategy_params.signal_period_min}-{strategy_params.signal_period_max}",
            )
        if strategy_params.step is not None:
            table.add_row("Step", str(strategy_params.step))
    else:
        # Fall back to global configuration
        table.add_row("Parameter Source", "Global configuration")

        if hasattr(config, "fast_period_range") and config.fast_period_range:
            table.add_row("Fast Period Range", str(config.fast_period_range))
        if hasattr(config, "slow_period_range") and config.slow_period_range:
            table.add_row("Slow Period Range", str(config.slow_period_range))
        if hasattr(config, "signal_period_range") and getattr(
            config, "signal_period_range", None
        ):
            table.add_row("Signal Period Range", str(config.signal_period_range))

    # Show single analysis parameters if available
    if hasattr(config, "fast_period") and config.fast_period:
        table.add_row("Fast Period", str(config.fast_period))
    if hasattr(config, "slow_period") and config.slow_period:
        table.add_row("Slow Period", str(config.slow_period))
    if hasattr(config, "signal_period") and config.signal_period:
        table.add_row("Signal Period", str(config.signal_period))

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
        fast_period = result.get("Fast Period", 0)
        slow_period = result.get("Slow Period", 0)
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


def show_execution_progress_console(
    console: ConsoleLogger,
    message: str,
    ticker_count: int = None,
    combination_count: int = None,
) -> None:
    """
    Display consistent execution progress messages using console logger.

    Args:
        console: Console logger instance
        message: Progress message to display
        ticker_count: Number of tickers being processed
        combination_count: Number of combinations being analyzed
    """
    console.progress(message)

    if ticker_count:
        console.info(f"Processing {ticker_count} ticker(s)...")

    if combination_count:
        console.info(f"Analyzing {combination_count} parameter combinations...")


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
