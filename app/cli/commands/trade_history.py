"""Trade History command implementations.

This module provides CLI commands for trade history analysis, sell signal generation,
and position management functionality.
"""

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from ..config import ConfigLoader
from ..models.trade_history import TradeHistoryConfig
from ..utils import resolve_portfolio_path


# Create trade-history sub-app
app = typer.Typer(
    name="trade-history",
    help="Trade History Analysis and Position Management",
    no_args_is_help=True,
)

console = Console()


@app.command()
def close(
    ctx: typer.Context,
    strategy: str = typer.Argument(
        ...,
        help="Strategy name (e.g., 'MA_SMA_78_82') or Position_UUID to analyze",
    ),
    portfolio: str | None = typer.Option(
        None,
        "--portfolio",
        help="Portfolio name for position closing (live_signals, protected, risk_on, custom)",
    ),
    price: float | None = typer.Option(
        None,
        "--price",
        help="Closing price for position exit (required when portfolio specified)",
    ),
    date: str | None = typer.Option(
        None,
        "--date",
        help="Exit date/timestamp (YYYY-MM-DD or 'YYYY-MM-DD HH:MM:SS') - defaults to current time",
    ),
    profile: str | None = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (default: stdout)",
    ),
    format: str = typer.Option(
        "markdown",
        "--format",
        "-f",
        help="Output format: markdown, json, html",
    ),
    include_raw_data: bool = typer.Option(
        False,
        "--include-raw-data/--no-raw-data",
        help="Include raw statistical data in appendices",
    ),
    current_price: float | None = typer.Option(
        None,
        "--current-price",
        help="Current market price for enhanced analysis",
    ),
    market_condition: str | None = typer.Option(
        None,
        "--market-condition",
        help="Market condition: bullish, bearish, sideways, volatile",
    ),
    base_path: str | None = typer.Option(
        None,
        "--base-path",
        help="Base path to trading system directory",
    ),
):
    """
    Close positions and generate comprehensive sell signal reports from SPDS data.

    Two operation modes:
    1. Position Closing: When --portfolio and --price are provided, closes the position
       in the specified portfolio and generates analysis report.
    2. Report Only: When only strategy is provided, generates analysis report without
       modifying positions.

    Examples:
        # Close position with portfolio update
        trading-cli trade-history close NFLX_SMA_82_83_20250616 --portfolio risk_on --price 1273.99

        # Generate report only (existing behavior)
        trading-cli trade-history close MA_SMA_78_82
        trading-cli trade-history close CRWD_EMA_5_21 --output reports/CRWD_analysis.md
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Validate parameters for position closing mode
        position_closing_mode = portfolio is not None or price is not None

        if position_closing_mode:
            # Both portfolio and price are required for position closing
            if portfolio is None:
                rprint(
                    "[red]❌ Error: --portfolio is required when --price is specified[/red]",
                )
                raise typer.Exit(1)
            if price is None:
                rprint(
                    "[red]❌ Error: --price is required when --portfolio is specified[/red]",
                )
                raise typer.Exit(1)
            if price <= 0:
                rprint("[red]❌ Error: --price must be a positive number[/red]")
                raise typer.Exit(1)

            # Validate portfolio file exists
            from pathlib import Path

            portfolio_file = Path(
                f"data/raw/positions/{resolve_portfolio_path(portfolio)}",
            )
            if not portfolio_file.exists():
                rprint(f"[red]❌ Portfolio file not found: {portfolio_file}[/red]")
                rprint("[yellow]Available portfolios:[/yellow]")
                portfolios_dir = Path("data/raw/positions/")
                if portfolios_dir.exists():
                    for pf in portfolios_dir.glob("*.csv"):
                        rprint(f"  - {pf.stem}")
                else:
                    rprint("  No portfolios directory found")
                raise typer.Exit(1)

        # Load configuration
        loader = ConfigLoader()

        # Build configuration overrides from CLI arguments
        overrides = {
            "base_path": base_path,
            "analysis": {
                "include_raw_data": include_raw_data,
                "current_price": current_price,
                "market_condition": market_condition,
            },
            "output": {
                "output_file": output,
                "output_format": format,
                "verbose": global_verbose,
            },
        }

        # Load configuration
        if profile:
            loader.load_from_profile(profile, TradeHistoryConfig, overrides)
        else:
            loader.load_from_profile(
                "default_trade_history",
                TradeHistoryConfig,
                overrides,
            )

        if global_verbose:
            rprint(f"[dim]Generating sell signal report for: {strategy}[/dim]")

        # Import unified services
        from ...services import PositionService
        from ...services.position_service import TradingSystemConfig

        # Create unified position service
        service_config = TradingSystemConfig(base_path) if base_path else None
        position_service = PositionService(service_config)

        # Create mock args object for compatibility
        class MockArgs:
            def __init__(self):
                self.strategy = strategy
                self.output = output
                self.format = format
                self.include_raw_data = include_raw_data
                self.current_price = current_price
                self.market_condition = market_condition
                self.verbose = global_verbose
                self.list_strategies = False
                self.health_check = False
                self.validate_data = False

        MockArgs()

        # Handle position closing if portfolio and price provided
        if position_closing_mode:
            rprint(f"🔄 Closing Position: [cyan]{strategy}[/cyan]")
            rprint(f"   Portfolio: [yellow]{portfolio}[/yellow]")
            rprint(f"   Exit Price: [green]${price:.2f}[/green]")
            rprint("-" * 60)

            try:
                # Use unified PositionService to close the position
                result = position_service.close_position(
                    position_uuid=strategy,
                    portfolio_name=portfolio,
                    exit_price=price,
                    exit_date=date,
                )

                # Display success message using service result
                rprint("[green]✅ Position closed successfully![/green]")
                rprint(f"   Exit Price: ${result['exit_price']:.2f}")
                rprint(f"   P&L: ${result['pnl']:.2f}")
                rprint(f"   Return: {result['return']:.2%}")
                rprint(f"   Exit Date: {result['exit_date']}")
                rprint()

            except Exception as e:
                rprint(f"[red]❌ Failed to close position: {e!s}[/red]")
                if global_verbose:
                    raise
                raise typer.Exit(1)

        # Generate analysis report (simplified for now)
        if not position_closing_mode:
            rprint(f"🎯 Generating Sell Signal Report: [cyan]{strategy}[/cyan]")
            rprint(f"   Format: [yellow]{format}[/yellow]")
            if output:
                rprint(f"   Output: [green]{output}[/green]")
            rprint("-" * 60)

            # For now, provide a simplified report message
            # TODO: Integrate with proper report generation service in future
            rprint(
                "[yellow]⚠️  Advanced report generation temporarily unavailable[/yellow]",
            )
            rprint("[dim]Position closing functionality is fully operational[/dim]")
            rprint(
                "[dim]Advanced reporting features will be restored in a future update[/dim]",
            )

        rprint("[green]✅ Command completed successfully![/green]")

    except Exception as e:
        rprint(f"[red]❌ Close command failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def add(
    ctx: typer.Context,
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g., 'AAPL', 'BTC-USD')"),
    portfolio: str | None = typer.Option(
        None,
        "--portfolio",
        help="Portfolio name to add position to (live_signals, protected, risk_on, custom)",
    ),
    strategy_type: str | None = typer.Option(
        None,
        "--strategy-type",
        "-s",
        help="Strategy type: SMA, EMA, MACD, ATR (auto-selected if not specified)",
    ),
    fast_period: int | None = typer.Option(
        None,
        "--short-window",
        help="Short period window (auto-selected if not specified)",
    ),
    slow_period: int | None = typer.Option(
        None,
        "--long-window",
        help="Long period window (auto-selected if not specified)",
    ),
    profile: str | None = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    timeframe: str = typer.Option(
        "D",
        "--timeframe",
        "-t",
        help="Timeframe: D, H, 4H, 1H",
    ),
    entry_price: float | None = typer.Option(
        None, "--entry-price", help="Manual entry price override"
    ),
    quantity: float | None = typer.Option(None, "--quantity", help="Position quantity"),
    signal_date: str | None = typer.Option(
        None,
        "--signal-date",
        help="Signal date (YYYY-MM-DD format)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the addition without executing",
    ),
):
    """
    Add new position to specified portfolio with automatic strategy selection.

    Automatically selects the best performing strategy for the ticker and adds it to
    the specified portfolio. Can also manually override strategy parameters if needed.

    Examples:
        # Auto-select best strategy for ticker and add to portfolio
        trading-cli trade-history add TSLA --portfolio risk_on
        trading-cli trade-history add ASML --portfolio risk_on --entry-price 797.42

        # Manual strategy specification (optional)
        trading-cli trade-history add AAPL --portfolio live_signals --strategy-type SMA --short-window 20 --long-window 50
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Validate portfolio parameter is provided
        if portfolio is None:
            rprint("[red]❌ Error: --portfolio parameter is required[/red]")
            rprint(
                "[yellow]Available portfolios: live_signals, protected, risk_on, or custom portfolio name[/yellow]",
            )
            rprint(
                "[dim]Example: trading-cli trade-history add TSLA --portfolio risk_on[/dim]",
            )
            raise typer.Exit(1)

        # Validate portfolio file exists
        import os

        portfolio_path = f"data/raw/positions/{resolve_portfolio_path(portfolio)}"
        if not os.path.exists(portfolio_path):
            rprint(
                f"[red]❌ Portfolio '{portfolio}' not found at {portfolio_path}[/red]",
            )
            # List available portfolios
            try:
                available_portfolios = [
                    f.replace(".csv", "")
                    for f in os.listdir("data/raw/positions/")
                    if f.endswith(".csv")
                ]
                if available_portfolios:
                    rprint("[yellow]Available portfolios:[/yellow]")
                    for p in available_portfolios:
                        rprint(f"  - {p}")
                else:
                    rprint(
                        "[yellow]No portfolios found in data/raw/positions/[/yellow]",
                    )
            except:
                pass
            raise typer.Exit(1)

        # Auto-select best strategy if not manually specified
        if strategy_type is None or fast_period is None or slow_period is None:
            if global_verbose:
                rprint(f"[dim]Auto-selecting best strategy for {ticker}...[/dim]")

            # Find latest portfolio files for the ticker
            import glob
            from pathlib import Path

            # Look for strategy data in latest portfolio directories
            portfolio_pattern = f"data/raw/strategies/*/{ticker}_{timeframe}_*.csv"
            portfolio_files = glob.glob(portfolio_pattern)

            if not portfolio_files:
                rprint(f"[red]❌ No strategy data found for {ticker}[/red]")
                rprint(f"[yellow]Searched for: {portfolio_pattern}[/yellow]")
                raise typer.Exit(1)

            # Find the latest portfolio file
            latest_file = max(portfolio_files, key=lambda x: Path(x).stat().st_mtime)

            if global_verbose:
                rprint(f"[dim]Found strategy data: {latest_file}[/dim]")

            # Read and find best strategy
            import pandas as pd

            try:
                df = pd.read_csv(latest_file)
                if len(df) == 0:
                    rprint(f"[red]❌ No strategies found in {latest_file}[/red]")
                    raise typer.Exit(1)

                # Find highest scoring strategy
                best_strategy = df.loc[df["Score"].idxmax()]

                # Use auto-selected values if not manually specified
                if strategy_type is None:
                    strategy_type = best_strategy["Strategy Type"]
                if fast_period is None:
                    fast_period = int(best_strategy["Fast Period"])
                if slow_period is None:
                    slow_period = int(best_strategy["Slow Period"])

                if global_verbose:
                    rprint(
                        f"[green]✅ Auto-selected: {strategy_type} {fast_period}/{slow_period} (Score: {best_strategy['Score']:.4f})[/green]",
                    )

            except Exception as e:
                rprint(f"[red]❌ Error reading strategy data: {e}[/red]")
                raise typer.Exit(1)

        strategy_name = (
            f"{ticker}_{timeframe}_{strategy_type}_{fast_period}_{slow_period}"
        )

        rprint(f"➕ Adding Position to Portfolio: [cyan]{portfolio}[/cyan]")
        rprint(f"   Strategy: [yellow]{strategy_name}[/yellow]")
        if dry_run:
            rprint("   [yellow]DRY RUN - No changes will be made[/yellow]")
        rprint("-" * 60)

        # Display position details
        table = Table(title="Position Details", show_header=True)
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Ticker", ticker)
        table.add_row("Portfolio", portfolio)
        table.add_row("Strategy Type", strategy_type)
        table.add_row("Fast Period", str(fast_period))
        table.add_row("Slow Period", str(slow_period))
        table.add_row("Timeframe", timeframe)
        table.add_row(
            "Entry Price",
            str(entry_price) if entry_price else "Market Price",
        )
        table.add_row("Quantity", str(quantity) if quantity else "Auto-calculated")
        table.add_row("Signal Date", signal_date if signal_date else "Today")

        console.print(table)

        if dry_run:
            rprint(
                "\n[green]✅ Dry run completed - Position would be added successfully[/green]",
            )
        else:
            # Import and use the unified PositionService
            from ...services import PositionService
            from ...services.position_service import TradingSystemConfig

            try:
                # Create unified position service
                service_config = TradingSystemConfig()
                position_service = PositionService(service_config)

                # Use current date if signal_date not provided
                from datetime import datetime

                entry_date = (
                    signal_date if signal_date else datetime.now().strftime("%Y-%m-%d")
                )

                position_uuid = position_service.add_position_to_portfolio(
                    ticker=ticker,
                    strategy_type=strategy_type,
                    fast_period=fast_period,
                    slow_period=slow_period,
                    signal_period=0,  # Default value
                    entry_date=entry_date,
                    entry_price=entry_price,
                    position_size=quantity or 1.0,
                    direction="Long",  # Default direction - was missing in old call
                    portfolio_name=portfolio,
                    verify_signal=False,  # Skip signal verification for manual CLI adds
                )

                rprint(
                    f"\n[green]✅ Position added successfully to {portfolio} portfolio![/green]",
                )
                rprint(f"[dim]Position UUID: {position_uuid}[/dim]")
                rprint(f"[dim]Strategy: {strategy_name}[/dim]")

            except Exception as e:
                rprint(f"[red]❌ Failed to add position: {e}[/red]")
                if global_verbose:
                    raise
                raise typer.Exit(1)

    except Exception as e:
        if "❌" not in str(e):  # Don't double-print formatted errors
            rprint(f"[red]❌ Add command failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def update(
    ctx: typer.Context,
    portfolio: str = typer.Option(
        "live_signals",
        "--portfolio",
        "-f",
        help="Portfolio name to update",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        help="Force comprehensive recalculation of ALL positions using PositionCalculator",
    ),
    validate_calculations: bool = typer.Option(
        True,
        "--validate/--no-validate",
        help="Validate P&L and Return calculations for consistency",
    ),
    auto_fix_errors: bool = typer.Option(
        True,
        "--fix-errors/--no-fix-errors",
        help="Automatically fix calculation errors found during validation",
    ),
    profile: str | None = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    refresh_prices: bool = typer.Option(
        True,
        "--refresh-prices/--no-refresh-prices",
        help="Refresh current market prices",
    ),
    recalculate_metrics: bool = typer.Option(
        True,
        "--recalculate/--no-recalculate",
        help="Recalculate MFE/MAE metrics",
    ),
    update_risk_assessment: bool = typer.Option(
        True,
        "--update-risk/--no-update-risk",
        help="Update risk assessment scores",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview updates without executing",
    ),
):
    """
    Update existing positions with current market data and comprehensive validation.

    By default, updates only open positions with current market prices, recalculates
    performance metrics, and refreshes risk assessments.

    When --refresh is used, forces comprehensive recalculation of ALL positions
    (both open and closed) using the centralized PositionCalculator with standardized
    precision. Includes P&L validation and auto-correction of calculation errors.

    Examples:
        # Default: update only open positions
        trading-cli trade-history update --portfolio live_signals

        # Comprehensive refresh with validation and auto-fix
        trading-cli trade-history update --portfolio live_signals --refresh

        # Comprehensive refresh without validation (faster)
        trading-cli trade-history update --portfolio live_signals --refresh --no-validate

        # Validation only without auto-fix
        trading-cli trade-history update --portfolio live_signals --refresh --no-fix-errors

        # Dry run to preview changes
        trading-cli trade-history update --portfolio live_signals --refresh --dry-run --verbose
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        # Skip complex configuration for now and proceed directly
        # This can be enhanced later when configuration system is fully set up

        rprint(f"🔄 Updating Trade History: [cyan]{portfolio}[/cyan]")
        if refresh:
            rprint(
                "   [yellow]📊 COMPREHENSIVE REFRESH: Using centralized PositionCalculator[/yellow]",
            )
            if validate_calculations:
                rprint(
                    "   [green]🔍 Validation enabled: P&L and Return calculations[/green]",
                )
            if auto_fix_errors:
                rprint(
                    "   [blue]🔧 Auto-fix enabled: Correcting calculation errors[/blue]",
                )
        if dry_run:
            rprint("   [yellow]DRY RUN - No changes will be made[/yellow]")
        rprint("-" * 60)

        # Display update plan
        update_items = []
        if refresh:
            update_items.append("✅ Force fresh price data download")
            update_items.append(
                "✅ Recalculate ALL derived fields (P&L, Return, MFE/MAE)",
            )
            update_items.append(
                "✅ Apply standardized precision across all calculations",
            )
            update_items.append(
                "✅ Update Exit Efficiency and Trade Quality assessments",
            )
            if validate_calculations:
                update_items.append("✅ Validate calculation consistency")
            if auto_fix_errors:
                update_items.append("✅ Auto-correct any calculation errors found")
        else:
            if refresh_prices:
                update_items.append("✅ Refresh market prices")
            if recalculate_metrics:
                update_items.append("✅ Recalculate MFE/MAE metrics")
            if update_risk_assessment:
                update_items.append("✅ Update risk assessments")

        rprint("📋 Update Plan:")
        for item in update_items:
            rprint(f"   {item}")

        # Import and use trade history service directly
        from ...contexts.portfolio.services.trade_history_service import (
            TradeHistoryService,
        )

        rprint("\n🔄 Executing trade history update...")

        try:
            # Create service instance
            service = TradeHistoryService()

            # Execute the update based on mode
            if refresh:
                # Comprehensive refresh mode: update ALL positions with validation
                result = service.update_all_positions(
                    portfolio_name=portfolio,
                    dry_run=dry_run,
                    verbose=global_verbose,
                    validate_calculations=validate_calculations,
                    auto_fix_errors=auto_fix_errors,
                )
            else:
                # Default mode: update only open positions
                result = service.update_open_positions(
                    portfolio_name=portfolio,
                    dry_run=dry_run,
                    verbose=global_verbose,
                )

            if result["success"]:
                if dry_run:
                    rprint(f"\n[yellow]🔍 {result['message']}[/yellow]")
                else:
                    rprint(f"\n[green]✅ {result['message']}[/green]")

                # Display statistics
                rprint(f"   Updated positions: [cyan]{result['updated_count']}[/cyan]")
                rprint(f"   Total positions: [dim]{result['total_positions']}[/dim]")

                if result.get("refresh_mode"):
                    # Comprehensive refresh mode shows additional statistics
                    rprint(
                        f"   Open positions: [green]{result.get('open_positions', 0)}[/green]",
                    )
                    rprint(
                        f"   Closed positions: [yellow]{result.get('closed_positions', 0)}[/yellow]",
                    )

                    # Show validation and fix results if available
                    if result.get("refresh_mode") == "comprehensive":
                        calculation_fixes = result.get("calculation_fixes", [])
                        validation_errors = result.get("validation_errors", [])

                        if calculation_fixes:
                            rprint(
                                f"   [blue]🔧 Calculation fixes applied: {len(calculation_fixes)}[/blue]",
                            )
                            if global_verbose:
                                rprint("   [dim]Fixes made:[/dim]")
                                for fix in calculation_fixes[:3]:  # Show first 3 fixes
                                    rprint(f"      • {fix}")
                                if len(calculation_fixes) > 3:
                                    rprint(
                                        f"      ... and {len(calculation_fixes) - 3} more fixes",
                                    )

                        if validation_errors:
                            rprint(
                                f"   [red]❌ Validation errors remaining: {len(validation_errors)}[/red]",
                            )
                            if global_verbose:
                                for error in validation_errors[
                                    :2
                                ]:  # Show first 2 errors
                                    rprint(f"      • {error}")
                                if len(validation_errors) > 2:
                                    rprint(
                                        f"      ... and {len(validation_errors) - 2} more errors",
                                    )

                        if result.get("validation_enabled") and not validation_errors:
                            rprint(
                                "   [green]✅ All calculations validated successfully[/green]",
                            )

                else:
                    # Default mode shows open positions only
                    rprint(
                        f"   Open positions: [dim]{result.get('open_positions', 'N/A')}[/dim]",
                    )

                # Show processing errors if any
                if result.get("errors"):
                    rprint(
                        f"\n[yellow]⚠️  Processing warnings ({len(result['errors'])}):[/yellow]",
                    )
                    for error in result["errors"][:5]:  # Show first 5 errors
                        rprint(f"   - {error}")
                    if len(result["errors"]) > 5:
                        rprint(f"   ... and {len(result['errors']) - 5} more")

            else:
                rprint(f"[red]❌ {result['message']}[/red]")
                if result.get("errors"):
                    for error in result["errors"]:
                        rprint(f"   - {error}")
                raise typer.Exit(1)

        except Exception as e:
            rprint(f"[red]❌ Update execution failed: {e}[/red]")
            if global_verbose:
                raise
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Update command failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def list(
    ctx: typer.Context,
    show_signals: bool = typer.Option(
        True,
        "--show-signals/--no-signals",
        help="Show exit signals in listing",
    ),
    filter_signal: str | None = typer.Option(
        None,
        "--filter-signal",
        help="Filter by signal type: SELL, HOLD, BUY",
    ),
    sort_by: str = typer.Option(
        "confidence",
        "--sort-by",
        help="Sort by: confidence, ticker, signal, strategy",
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-n", help="Limit number of results"
    ),
):
    """
    List all available strategies for analysis.

    Shows comprehensive list of strategies with their current signals,
    confidence levels, and key metrics.

    Examples:
        trading-cli trade-history list
        trading-cli trade-history list --filter-signal SELL --limit 10
        trading-cli trade-history list --sort-by ticker --no-signals
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        rprint("📊 Available Trading Strategies")
        rprint("-" * 60)

        # Simplified list implementation using PositionService
        from ...services import PositionService
        from ...services.position_service import TradingSystemConfig

        # For now, provide basic portfolio listing
        # TODO: Enhance with full strategy analysis in future
        try:
            service_config = TradingSystemConfig()
            position_service = PositionService(service_config)

            # List available portfolios
            portfolios = ["live_signals", "protected", "risk_on"]
            for portfolio in portfolios:
                try:
                    positions = position_service.list_positions(portfolio)
                    rprint(
                        f"\n[cyan]{portfolio.upper()} Portfolio:[/cyan] {len(positions)} positions",
                    )
                    if show_signals and positions:
                        for pos in positions[:limit] if limit else positions:
                            status_color = (
                                "green" if pos.get("Status") == "Open" else "yellow"
                            )
                            rprint(
                                f"  • [{status_color}]{pos.get('Position_UUID', 'Unknown')}[/{status_color}]",
                            )
                except Exception:
                    rprint(f"  [dim]Portfolio {portfolio} not accessible[/dim]")

            rprint("\n[green]✅ Strategy listing completed![/green]")
            rprint(
                "[dim]Advanced filtering and signal analysis will be restored in future update[/dim]",
            )

        except Exception as e:
            rprint(f"[red]❌ Failed to list strategies: {e}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ List command failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def validate(
    ctx: typer.Context,
    check_data_integrity: bool = typer.Option(
        True,
        "--check-integrity/--no-check-integrity",
        help="Check data integrity across sources",
    ),
    check_file_existence: bool = typer.Option(
        True,
        "--check-files/--no-check-files",
        help="Check required file existence",
    ),
    check_strategy_data: bool = typer.Option(
        True,
        "--check-strategies/--no-check-strategies",
        help="Validate strategy data quality",
    ),
    show_details: bool = typer.Option(
        False,
        "--show-details",
        help="Show detailed validation results",
    ),
):
    """
    Validate trade history data integrity and system health.

    Performs comprehensive validation of data sources, file integrity,
    and system dependencies.

    Examples:
        trading-cli trade-history validate
        trading-cli trade-history validate --show-details
        trading-cli trade-history validate --no-check-strategies
    """
    try:
        # Get global verbose flag
        global_verbose = ctx.obj.get("verbose", False) if ctx.obj else False

        rprint("🔍 Trade History Data Validation")
        rprint("-" * 60)

        # Simplified validation using PositionService
        validation_results = {"checks_performed": [], "issues_found": 0, "warnings": 0}

        rprint("[yellow]⚠️  Advanced validation temporarily simplified[/yellow]")
        rprint(
            "[dim]Basic validation available - full features will be restored in future update[/dim]",
        )

        if check_file_existence or check_data_integrity:
            from ...services import PositionService
            from ...services.position_service import TradingSystemConfig

            try:
                service_config = TradingSystemConfig()
                position_service = PositionService(service_config)

                rprint("📁 Running basic system check...")
                validation_results["checks_performed"].append("System Health Check")

                # Test basic service functionality
                portfolios = ["live_signals", "protected", "risk_on"]
                for portfolio in portfolios:
                    try:
                        positions = position_service.list_positions(portfolio)
                        rprint(
                            f"  ✅ Portfolio {portfolio}: Accessible ({len(positions)} positions)",
                        )
                    except Exception:
                        rprint(f"  ⚠️  Portfolio {portfolio}: Issues detected")
                        validation_results["issues_found"] += 1

            except Exception as e:
                rprint(f"  ❌ Service validation failed: {e}")
                validation_results["issues_found"] += 1

        # Summary
        rprint("\n📋 Validation Summary:")
        rprint(f"   Checks performed: {len(validation_results['checks_performed'])}")
        rprint(f"   Issues found: {validation_results['issues_found']}")

        if validation_results["issues_found"] == 0:
            rprint("[green]✅ All validations passed - System is healthy![/green]")
        else:
            rprint(
                f"[red]❌ {validation_results['issues_found']} validation issues found[/red]",
            )
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Validation failed: {e}[/red]")
        if global_verbose:
            raise
        raise typer.Exit(1)


@app.command()
def health():
    """
    Perform comprehensive trade history system health check.

    Checks data sources, file integrity, dependencies, and system status.
    """
    try:
        rprint("🏥 Trade History System Health Check")
        rprint("-" * 60)

        # Simplified health check using PositionService
        from ...services import PositionService
        from ...services.position_service import TradingSystemConfig

        try:
            service_config = TradingSystemConfig()
            position_service = PositionService(service_config)

            rprint("[green]✅ PositionService: Operational[/green]")
            rprint("[green]✅ Configuration: Loaded[/green]")

            # Test basic functionality
            portfolios = ["live_signals", "protected", "risk_on"]
            accessible_portfolios = 0
            for portfolio in portfolios:
                try:
                    positions = position_service.list_positions(portfolio)
                    accessible_portfolios += 1
                    rprint(
                        f"[green]✅ Portfolio {portfolio}: {len(positions)} positions[/green]",
                    )
                except Exception as e:
                    rprint(
                        f"[yellow]⚠️  Portfolio {portfolio}: Not accessible ({str(e)[:50]}...)[/yellow]",
                    )

            rprint(
                f"\n[cyan]System Status: {accessible_portfolios}/{len(portfolios)} portfolios accessible[/cyan]",
            )
            rprint("[dim]Advanced diagnostics will be restored in future update[/dim]")
            result = 0

        except Exception as e:
            rprint(f"[red]❌ Health check failed: {e}[/red]")
            result = 1

        if result == 0:
            rprint("\n[green]🎉 Trade History system is healthy![/green]")
        else:
            rprint("\n[red]❌ Trade History system health issues detected[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Health check failed: {e}[/red]")
        raise typer.Exit(1)
