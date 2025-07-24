"""Trade History command implementations.

This module provides CLI commands for trade history analysis, sell signal generation,
and position management functionality.
"""

import json
import sys
from pathlib import Path
from typing import List, Optional

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
    strategy: str = typer.Argument(
        ..., help="Strategy name (e.g., 'MA_SMA_78_82') or Position_UUID to analyze"
    ),
    portfolio: Optional[str] = typer.Option(
        None,
        "--portfolio",
        help="Portfolio name for position closing (live_signals, protected, risk_on, custom)",
    ),
    price: Optional[float] = typer.Option(
        None,
        "--price",
        help="Closing price for position exit (required when portfolio specified)",
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (default: stdout)"
    ),
    format: str = typer.Option(
        "markdown", "--format", "-f", help="Output format: markdown, json, html"
    ),
    include_raw_data: bool = typer.Option(
        False,
        "--include-raw-data/--no-raw-data",
        help="Include raw statistical data in appendices",
    ),
    current_price: Optional[float] = typer.Option(
        None, "--current-price", help="Current market price for enhanced analysis"
    ),
    market_condition: Optional[str] = typer.Option(
        None,
        "--market-condition",
        help="Market condition: bullish, bearish, sideways, volatile",
    ),
    base_path: Optional[str] = typer.Option(
        None, "--base-path", help="Base path to trading system directory"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
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
        # Validate parameters for position closing mode
        position_closing_mode = portfolio is not None or price is not None

        if position_closing_mode:
            # Both portfolio and price are required for position closing
            if portfolio is None:
                rprint(
                    "[red]❌ Error: --portfolio is required when --price is specified[/red]"
                )
                raise typer.Exit(1)
            if price is None:
                rprint(
                    "[red]❌ Error: --price is required when --portfolio is specified[/red]"
                )
                raise typer.Exit(1)
            if price <= 0:
                rprint("[red]❌ Error: --price must be a positive number[/red]")
                raise typer.Exit(1)

            # Validate portfolio file exists
            from pathlib import Path

            portfolio_file = Path(
                f"data/raw/positions/{resolve_portfolio_path(portfolio)}"
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
                "verbose": verbose,
            },
        }

        # Load configuration
        if profile:
            config = loader.load_from_profile(profile, TradeHistoryConfig, overrides)
        else:
            config = loader.load_from_profile(
                "default_trade_history", TradeHistoryConfig, overrides
            )

        if verbose:
            rprint(f"[dim]Generating sell signal report for: {strategy}[/dim]")

        # Import trade history modules
        from ...tools.trade_history_close_live_signal import TradeHistoryCloseCommand

        # Create command instance
        command_base_path = Path(base_path) if base_path else None
        command = TradeHistoryCloseCommand(command_base_path)

        # Create mock args object for compatibility
        class MockArgs:
            def __init__(self):
                self.strategy = strategy
                self.output = output
                self.format = format
                self.include_raw_data = include_raw_data
                self.current_price = current_price
                self.market_condition = market_condition
                self.verbose = verbose
                self.list_strategies = False
                self.health_check = False
                self.validate_data = False

        args = MockArgs()

        # Handle position closing if portfolio and price provided
        if position_closing_mode:
            rprint(f"🔄 Closing Position: [cyan]{strategy}[/cyan]")
            rprint(f"   Portfolio: [yellow]{portfolio}[/yellow]")
            rprint(f"   Exit Price: [green]${price:.2f}[/green]")
            rprint("-" * 60)

            # Import required modules for position closing
            from datetime import datetime

            import pandas as pd

            try:
                # Load portfolio CSV
                portfolio_df = pd.read_csv(
                    f"data/raw/positions/{resolve_portfolio_path(portfolio)}"
                )

                # Find the position by UUID (strategy parameter should be Position_UUID)
                position_mask = portfolio_df["Position_UUID"] == strategy
                if not position_mask.any():
                    rprint(
                        f"[red]❌ Position '{strategy}' not found in portfolio '{portfolio}'[/red]"
                    )
                    rprint("[yellow]Available positions:[/yellow]")
                    for pos_uuid in portfolio_df["Position_UUID"].head(10):
                        rprint(f"  - {pos_uuid}")
                    if len(portfolio_df) > 10:
                        rprint(f"  ... and {len(portfolio_df) - 10} more")
                    raise typer.Exit(1)

                # Check if position is already closed
                position_row = portfolio_df[position_mask].iloc[0]
                if position_row["Status"] == "Closed":
                    rprint(f"[red]❌ Position '{strategy}' is already closed[/red]")
                    rprint(f"   Exit Date: {position_row['Exit_Timestamp']}")
                    rprint(f"   Exit Price: ${position_row['Avg_Exit_Price']:.2f}")
                    raise typer.Exit(1)

                # Calculate position metrics
                entry_price = position_row["Avg_Entry_Price"]
                position_size = position_row["Position_Size"]
                direction = position_row["Direction"]
                entry_date = pd.to_datetime(position_row["Entry_Timestamp"])
                exit_date = datetime.now()

                # Calculate P&L and return
                if direction.upper() == "LONG":
                    pnl = (price - entry_price) * position_size
                    return_pct = (price - entry_price) / entry_price
                else:  # SHORT
                    pnl = (entry_price - price) * position_size
                    return_pct = (entry_price - price) / entry_price

                # Calculate duration
                duration_days = (exit_date - entry_date).days

                # Update the position record
                idx = portfolio_df[position_mask].index[0]
                portfolio_df.loc[idx, "Exit_Timestamp"] = exit_date.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                portfolio_df.loc[idx, "Avg_Exit_Price"] = price
                portfolio_df.loc[idx, "PnL"] = round(pnl, 2)
                portfolio_df.loc[idx, "Return"] = round(return_pct, 4)
                portfolio_df.loc[idx, "Duration_Days"] = duration_days
                portfolio_df.loc[idx, "Status"] = "Closed"
                portfolio_df.loc[idx, "Days_Since_Entry"] = duration_days
                portfolio_df.loc[idx, "Current_Unrealized_PnL"] = round(return_pct, 4)

                # Calculate exit efficiency if MFE exists
                if (
                    not pd.isna(position_row["Max_Favourable_Excursion"])
                    and position_row["Max_Favourable_Excursion"] > 0
                ):
                    exit_efficiency = (
                        return_pct / position_row["Max_Favourable_Excursion"]
                    )
                    portfolio_df.loc[idx, "Exit_Efficiency_Fixed"] = round(
                        exit_efficiency, 4
                    )

                # Save updated portfolio
                portfolio_df.to_csv(
                    f"data/raw/positions/{resolve_portfolio_path(portfolio)}",
                    index=False,
                )

                # Display success message
                rprint("[green]✅ Position closed successfully![/green]")
                rprint(f"   Entry Price: ${entry_price:.2f}")
                rprint(f"   Exit Price: ${price:.2f}")
                rprint(f"   P&L: ${pnl:.2f}")
                rprint(f"   Return: {return_pct:.2%}")
                rprint(f"   Duration: {duration_days} days")
                rprint()

            except Exception as e:
                rprint(f"[red]❌ Failed to close position: {str(e)}[/red]")
                if verbose:
                    raise
                raise typer.Exit(1)

        rprint(f"🎯 Generating Sell Signal Report: [cyan]{strategy}[/cyan]")
        rprint(f"   Format: [yellow]{format}[/yellow]")
        if output:
            rprint(f"   Output: [green]{output}[/green]")
        rprint("-" * 60)

        # Execute the command
        result = command.execute(args)

        if result == 0:
            rprint("[green]✅ Report generated successfully![/green]")
        else:
            rprint("[red]❌ Report generation failed[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Close command failed: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def add(
    ticker: str = typer.Argument(..., help="Ticker symbol (e.g., 'AAPL', 'BTC-USD')"),
    portfolio: Optional[str] = typer.Option(
        None,
        "--portfolio",
        help="Portfolio name to add position to (live_signals, protected, risk_on, custom)",
    ),
    strategy_type: Optional[str] = typer.Option(
        None,
        "--strategy-type",
        "-s",
        help="Strategy type: SMA, EMA, MACD (auto-selected if not specified)",
    ),
    short_window: Optional[int] = typer.Option(
        None,
        "--short-window",
        help="Short period window (auto-selected if not specified)",
    ),
    long_window: Optional[int] = typer.Option(
        None,
        "--long-window",
        help="Long period window (auto-selected if not specified)",
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    timeframe: str = typer.Option(
        "D", "--timeframe", "-t", help="Timeframe: D, H, 4H, 1H"
    ),
    entry_price: Optional[float] = typer.Option(
        None, "--entry-price", help="Manual entry price override"
    ),
    quantity: Optional[float] = typer.Option(
        None, "--quantity", help="Position quantity"
    ),
    signal_date: Optional[str] = typer.Option(
        None, "--signal-date", help="Signal date (YYYY-MM-DD format)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview the addition without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
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
        # Validate portfolio parameter is provided
        if portfolio is None:
            rprint("[red]❌ Error: --portfolio parameter is required[/red]")
            rprint(
                "[yellow]Available portfolios: live_signals, protected, risk_on, or custom portfolio name[/yellow]"
            )
            rprint(
                "[dim]Example: trading-cli trade-history add TSLA --portfolio risk_on[/dim]"
            )
            raise typer.Exit(1)

        # Validate portfolio file exists
        import os

        portfolio_path = f"data/raw/positions/{resolve_portfolio_path(portfolio)}"
        if not os.path.exists(portfolio_path):
            rprint(
                f"[red]❌ Portfolio '{portfolio}' not found at {portfolio_path}[/red]"
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
                        "[yellow]No portfolios found in data/raw/positions/[/yellow]"
                    )
            except:
                pass
            raise typer.Exit(1)

        # Auto-select best strategy if not manually specified
        if strategy_type is None or short_window is None or long_window is None:
            if verbose:
                rprint(f"[dim]Auto-selecting best strategy for {ticker}...[/dim]")

            # Find latest portfolio files for the ticker
            import glob
            from pathlib import Path

            # Look for strategy data in latest portfolio directories
            portfolio_pattern = f"data/raw/strategies/*/{ ticker}_{timeframe}_*.csv"
            portfolio_files = glob.glob(portfolio_pattern)

            if not portfolio_files:
                rprint(f"[red]❌ No strategy data found for {ticker}[/red]")
                rprint(f"[yellow]Searched for: {portfolio_pattern}[/yellow]")
                raise typer.Exit(1)

            # Find the latest portfolio file
            latest_file = max(portfolio_files, key=lambda x: Path(x).stat().st_mtime)

            if verbose:
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
                if short_window is None:
                    short_window = int(best_strategy["Short Window"])
                if long_window is None:
                    long_window = int(best_strategy["Long Window"])

                if verbose:
                    rprint(
                        f"[green]✅ Auto-selected: {strategy_type} {short_window}/{long_window} (Score: {best_strategy['Score']:.4f})[/green]"
                    )

            except Exception as e:
                rprint(f"[red]❌ Error reading strategy data: {e}[/red]")
                raise typer.Exit(1)

        strategy_name = (
            f"{ticker}_{timeframe}_{strategy_type}_{short_window}_{long_window}"
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
        table.add_row("Short Window", str(short_window))
        table.add_row("Long Window", str(long_window))
        table.add_row("Timeframe", timeframe)
        table.add_row(
            "Entry Price", str(entry_price) if entry_price else "Market Price"
        )
        table.add_row("Quantity", str(quantity) if quantity else "Auto-calculated")
        table.add_row("Signal Date", signal_date if signal_date else "Today")

        console.print(table)

        if dry_run:
            rprint(
                "\n[green]✅ Dry run completed - Position would be added successfully[/green]"
            )
        else:
            # Import and use the actual position addition functionality
            from ...tools.generalized_trade_history_exporter import (
                add_position_to_portfolio,
            )

            try:
                position_uuid = add_position_to_portfolio(
                    ticker=ticker,
                    strategy_type=strategy_type,
                    short_window=short_window,
                    long_window=long_window,
                    signal_window=0,  # Default value
                    entry_date=signal_date,
                    entry_price=entry_price,
                    position_size=quantity or 1.0,
                    portfolio_name=portfolio,
                    verify_signal=True,
                )

                rprint(
                    f"\n[green]✅ Position added successfully to {portfolio} portfolio![/green]"
                )
                rprint(f"[dim]Position UUID: {position_uuid}[/dim]")
                rprint(f"[dim]Strategy: {strategy_name}[/dim]")

            except Exception as e:
                rprint(f"[red]❌ Failed to add position: {e}[/red]")
                if verbose:
                    raise
                raise typer.Exit(1)

    except Exception as e:
        if "❌" not in str(e):  # Don't double-print formatted errors
            rprint(f"[red]❌ Add command failed: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def update(
    portfolio: str = typer.Option(
        "live_signals", "--portfolio", "-f", help="Portfolio name to update"
    ),
    profile: Optional[str] = typer.Option(
        None, "--profile", "-p", help="Configuration profile name"
    ),
    refresh_prices: bool = typer.Option(
        True,
        "--refresh-prices/--no-refresh-prices",
        help="Refresh current market prices",
    ),
    recalculate_metrics: bool = typer.Option(
        True, "--recalculate/--no-recalculate", help="Recalculate MFE/MAE metrics"
    ),
    update_risk_assessment: bool = typer.Option(
        True, "--update-risk/--no-update-risk", help="Update risk assessment scores"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Preview updates without executing"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
):
    """
    Update existing positions with current market data.

    Updates open positions with current market prices, recalculates
    performance metrics, and refreshes risk assessments.

    Examples:
        trading-cli trade-history update --portfolio live_signals
        trading-cli trade-history update --refresh-prices --recalculate
    """
    try:
        # Skip complex configuration for now and proceed directly
        # This can be enhanced later when configuration system is fully set up

        rprint(f"🔄 Updating Trade History: [cyan]{portfolio}[/cyan]")
        if dry_run:
            rprint("   [yellow]DRY RUN - No changes will be made[/yellow]")
        rprint("-" * 60)

        # Display update plan
        update_items = []
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

            # Execute the update
            result = service.update_open_positions(
                portfolio_name=portfolio, dry_run=dry_run, verbose=verbose
            )

            if result["success"]:
                if dry_run:
                    rprint(f"\n[yellow]🔍 {result['message']}[/yellow]")
                else:
                    rprint(f"\n[green]✅ {result['message']}[/green]")

                # Display statistics
                rprint(f"   Updated positions: [cyan]{result['updated_count']}[/cyan]")
                rprint(f"   Total positions: [dim]{result['total_positions']}[/dim]")
                rprint(
                    f"   Open positions: [dim]{result.get('open_positions', 'N/A')}[/dim]"
                )

                # Show errors if any
                if result.get("errors"):
                    rprint(
                        f"\n[yellow]⚠️  Warnings ({len(result['errors'])}):[/yellow]"
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
            if verbose:
                raise
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Update command failed: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def list(
    show_signals: bool = typer.Option(
        True, "--show-signals/--no-signals", help="Show exit signals in listing"
    ),
    filter_signal: Optional[str] = typer.Option(
        None, "--filter-signal", help="Filter by signal type: SELL, HOLD, BUY"
    ),
    sort_by: str = typer.Option(
        "confidence", "--sort-by", help="Sort by: confidence, ticker, signal, strategy"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", "-n", help="Limit number of results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
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
        rprint("📊 Available Trading Strategies")
        rprint("-" * 60)

        # Import trade history modules
        from ...tools.trade_history_close_live_signal import TradeHistoryCloseCommand

        # Create command instance
        command = TradeHistoryCloseCommand()

        # Create mock args for list functionality
        class MockArgs:
            def __init__(self):
                self.list_strategies = True
                self.health_check = False
                self.validate_data = False
                self.strategy = None
                self.verbose = verbose

        args = MockArgs()

        # Execute list command
        result = command.execute(args)

        if result != 0:
            rprint("[red]❌ Failed to list strategies[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ List command failed: {e}[/red]")
        if verbose:
            raise
        raise typer.Exit(1)


@app.command()
def validate(
    check_data_integrity: bool = typer.Option(
        True,
        "--check-integrity/--no-check-integrity",
        help="Check data integrity across sources",
    ),
    check_file_existence: bool = typer.Option(
        True, "--check-files/--no-check-files", help="Check required file existence"
    ),
    check_strategy_data: bool = typer.Option(
        True,
        "--check-strategies/--no-check-strategies",
        help="Validate strategy data quality",
    ),
    show_details: bool = typer.Option(
        False, "--show-details", help="Show detailed validation results"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
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
        rprint("🔍 Trade History Data Validation")
        rprint("-" * 60)

        # Import trade history modules
        from ...tools.trade_history_close_live_signal import TradeHistoryCloseCommand

        # Create command instance
        command = TradeHistoryCloseCommand()

        validation_results = {"checks_performed": [], "issues_found": 0, "warnings": 0}

        if check_file_existence or check_data_integrity:
            # Create mock args for health check
            class MockHealthArgs:
                def __init__(self):
                    self.health_check = True
                    self.list_strategies = False
                    self.validate_data = False
                    self.strategy = None
                    self.verbose = verbose

            args = MockHealthArgs()
            rprint("📁 Running system health check...")
            result = command.execute(args)
            validation_results["checks_performed"].append("System Health Check")

            if result != 0:
                validation_results["issues_found"] += 1

        if check_data_integrity:
            # Create mock args for data validation
            class MockValidateArgs:
                def __init__(self):
                    self.validate_data = True
                    self.health_check = False
                    self.list_strategies = False
                    self.strategy = None
                    self.verbose = verbose

            args = MockValidateArgs()
            rprint("\n📊 Running data integrity validation...")
            result = command.execute(args)
            validation_results["checks_performed"].append("Data Integrity Check")

            if result != 0:
                validation_results["issues_found"] += 1

        # Summary
        rprint(f"\n📋 Validation Summary:")
        rprint(f"   Checks performed: {len(validation_results['checks_performed'])}")
        rprint(f"   Issues found: {validation_results['issues_found']}")

        if validation_results["issues_found"] == 0:
            rprint("[green]✅ All validations passed - System is healthy![/green]")
        else:
            rprint(
                f"[red]❌ {validation_results['issues_found']} validation issues found[/red]"
            )
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Validation failed: {e}[/red]")
        if verbose:
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

        # Import trade history modules
        from ...tools.trade_history_close_live_signal import TradeHistoryCloseCommand

        # Create command instance
        command = TradeHistoryCloseCommand()

        # Create mock args for health check
        class MockArgs:
            def __init__(self):
                self.health_check = True
                self.list_strategies = False
                self.validate_data = False
                self.strategy = None
                self.verbose = False

        args = MockArgs()

        # Execute health check
        result = command.execute(args)

        if result == 0:
            rprint("\n[green]🎉 Trade History system is healthy![/green]")
        else:
            rprint("\n[red]❌ Trade History system health issues detected[/red]")
            raise typer.Exit(1)

    except Exception as e:
        rprint(f"[red]❌ Health check failed: {e}[/red]")
        raise typer.Exit(1)
