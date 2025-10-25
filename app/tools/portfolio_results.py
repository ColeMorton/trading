"""Portfolio result processing utilities.

This module provides utilities for processing and displaying portfolio results.
"""

from typing import Any

from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text

from app.tools.formatters import (
    create_section_header,
    format_average_duration,
    format_currency,
    format_duration,
    format_percentage,
    format_ratio,
    format_score,
    format_signal_status,
    format_status,
    format_win_rate,
    parse_duration_to_hours,
)
from app.tools.portfolio.collection import sort_portfolios
from app.tools.portfolio.status_filters import determine_portfolio_status


# Rich console for output
console = Console()


def calculate_comp_status_from_aggregates(
    entry_count: int, exit_count: int, active_count: int, total_count: int
) -> str:
    """Calculate COMP status from aggregated strategy counts.

    The COMP strategy uses a 50% threshold to determine position:
    - In position: When >= 50% of strategies are active
    - Out of position: When < 50% of strategies are active

    Status priority:
    1. Entry: >= 50% active AND has entry signals (entering/in position)
    2. Exit: < 50% active AND has exit signals (exiting/out of position)
    3. Active: >= 50% active AND no entry signals (holding position)
    4. Inactive: < 50% active AND no exit signals (no position)

    Args:
        entry_count: Number of strategies with entry signals
        exit_count: Number of strategies with exit signals
        active_count: Number of active strategies (with open trades)
        total_count: Total number of strategies for this ticker

    Returns:
        Status string: "Entry", "Exit", "Active", or "Inactive"
    """
    # Calculate active percentage
    active_pct = (active_count / total_count * 100) if total_count > 0 else 0

    # COMP is "in position" when active % >= 50%
    comp_in_position = active_pct >= 50.0

    if comp_in_position:
        # COMP would be in position (>= 50% active)
        if entry_count > 0:
            return "Entry"  # Entering or in position with new signals
        return "Active"  # Holding position, no new signals
    # COMP would be out of position (< 50% active)
    if exit_count > 0:
        return "Exit"  # Exiting or out with exit signals
    return "Inactive"  # No position, no signals


def filter_open_trades(
    portfolios: list[dict[str, Any]], log_func=None
) -> list[dict[str, Any]]:
    """Filter portfolios to only include open trades.

    Args:
        portfolios: List of portfolio dictionaries
        log_func: Optional logging function

    Returns:
        Filtered list of portfolio dictionaries
    """
    if not portfolios:
        return []

    # List strategies where Total Open Trades = 1 AND Signal Entry = false (to
    # avoid duplicates)
    open_trades = [
        p
        for p in portfolios
        if (
            p.get("Total Open Trades") == 1
            or (
                isinstance(p.get("Total Open Trades"), str)
                and p.get("Total Open Trades") == "1"
            )
        )
        and str(p.get("Signal Entry", "")).lower() != "true"
    ]

    # Sort open trades by Score
    config = {"SORT_BY": "Score", "SORT_ASC": False}
    open_trades = sort_portfolios(open_trades, config)

    # Rich table display for open trades
    if open_trades:
        create_section_header("Active Portfolio Positions", "🎯")

        table = Table(
            title=f"📈 {len(open_trades)} Open Positions",
            show_header=True,
            header_style="bold magenta",
            title_style="bold green",
        )

        table.add_column("Ticker", style="cyan bold", no_wrap=True)
        table.add_column("Strategy", style="blue", no_wrap=True)
        table.add_column("Periods", style="white", justify="center")
        table.add_column("Score", style="bold", justify="right")
        table.add_column("Win Rate", justify="right")
        table.add_column("Return", justify="right")
        table.add_column("Status", justify="center")

        for p in open_trades:
            ticker = p.get("Ticker", "Unknown")
            strategy_type = p.get("Strategy Type", "Unknown")
            fast_period = p.get("Fast Period", "N/A")
            slow_period = p.get("Slow Period", "N/A")
            signal_period = p.get("Signal Period", "N/A")

            # Format periods
            if str(signal_period).lower() in ["0", "n/a", "none", ""]:
                periods = f"{fast_period}/{slow_period}"
            else:
                periods = f"{fast_period}/{slow_period}/{signal_period}"

            # Get metrics for display
            score = p.get("Score", 0)
            win_rate = p.get("Win Rate [%]", 0)
            total_return = p.get("Total Return [%]", 0)
            signal_entry = str(p.get("Signal Entry", "")).lower() == "true"
            signal_exit = str(p.get("Signal Exit", "")).lower() == "true"
            signal_unconfirmed = p.get("Signal Unconfirmed", "")

            table.add_row(
                ticker,
                strategy_type,
                periods,
                format_score(score),
                format_win_rate(win_rate),
                format_percentage(total_return),
                format_signal_status(signal_entry, signal_exit, signal_unconfirmed),
            )

        console.print(table)

        # Summary statistics for open trades
        if len(open_trades) > 1:
            avg_score = sum(float(p.get("Score", 0)) for p in open_trades) / len(
                open_trades
            )
            avg_win_rate = sum(
                float(p.get("Win Rate [%]", 0)) for p in open_trades
            ) / len(open_trades)
            avg_return = sum(
                float(p.get("Total Return [%]", 0)) for p in open_trades
            ) / len(open_trades)

            rprint("\n💡 [bold yellow]Position Summary:[/bold yellow]")
            rprint(f"   📊 Average Score: {format_score(avg_score)}")
            rprint(f"   🎯 Average Win Rate: {format_win_rate(avg_win_rate)}")
            rprint(f"   💰 Average Return: {format_percentage(avg_return)}")
    else:
        create_section_header("Portfolio Status", "🔍")
        rprint("[yellow]⚠️  No open positions found[/yellow]")
        rprint(
            "[dim]   All strategies are currently in cash or have exited positions[/dim]"
        )

    # Also log to the traditional log function if provided
    if log_func:
        if open_trades:
            log_func("\n=== Open Trades ===")
            log_func(
                "Ticker, Strategy Type, Fast Period, Slow Period, Signal Period, Score"
            )
            for p in open_trades:
                ticker = p.get("Ticker", "Unknown")
                strategy_type = p.get("Strategy Type", "Unknown")
                fast_period = p.get("Fast Period", "N/A")
                slow_period = p.get("Slow Period", "N/A")
                signal_period = p.get("Signal Period", "N/A")
                score = p.get("Score", 0)
                log_func(
                    f"{ticker}, {strategy_type}, {fast_period}, {slow_period}, {signal_period}, {score:.4f}"
                )
        else:
            log_func("\n=== No Open Trades found ===")

    return open_trades


# Removed duplicate sort_portfolios function - using unified implementation


def _display_portfolio_table_core(
    display_portfolios: list[dict[str, Any]],
    section_title: str,
    title_prefix: str,
    title_style: str,
    log_func=None,
) -> None:
    """Core table display logic shared between portfolio table functions.

    Args:
        display_portfolios: List of portfolio dictionaries to display
        section_title: Title for the section header (e.g., "Portfolio", "Portfolio Entry/Exit")
        title_prefix: Emoji prefix for table title (e.g., "📊", "🎯")
        title_style: Style for table title (e.g., "bold cyan", "bold bright_green")
        log_func: Optional logging function
    """
    if not display_portfolios:
        create_section_header(section_title, title_prefix.strip())
        if "Entry/Exit" in section_title:
            rprint("[blue]📊 No Entry/Exit signals detected[/blue]")
            rprint("[dim]   All strategies are currently Active or Inactive[/dim]")
        else:
            rprint("[yellow]⚠️  No portfolio strategies found[/yellow]")
            rprint("[dim]   Portfolio may be empty or failed to load[/dim]")
        return

    create_section_header(section_title, title_prefix.strip())

    table = Table(
        title=f"{title_prefix} {len(display_portfolios)} {'Entry/Exit Signals' if 'Entry/Exit' in section_title else 'Strategies'}",
        show_header=True,
        header_style="bold magenta",
        title_style=title_style,
    )

    # Define table columns including new Total Trades column
    table.add_column("Ticker", style="cyan bold", no_wrap=True)
    table.add_column("Strategy", style="blue", no_wrap=True)
    table.add_column("Periods", style="white", justify="center")
    table.add_column("Total Trades", justify="right")
    table.add_column("Score", style="bold", justify="right")
    table.add_column("Win Rate", justify="right")
    table.add_column("Profit Factor", style="bold", justify="right", no_wrap=True)
    table.add_column("Expectancy", justify="right", no_wrap=True)
    table.add_column("Sortino", style="bold", justify="right", no_wrap=True)
    table.add_column("Return", justify="right")
    table.add_column("Beats BNH", justify="right", no_wrap=True)
    table.add_column("Duration", justify="center", no_wrap=True)
    table.add_column("Status", justify="center")

    for p in display_portfolios:
        ticker = p.get("Ticker", "Unknown")
        strategy_type = p.get("Strategy Type", "Unknown")
        fast_period = p.get("Fast Period", "N/A")
        slow_period = p.get("Slow Period", "N/A")
        signal_period = p.get("Signal Period", "N/A")

        # Format periods
        if str(signal_period).lower() in ["0", "n/a", "none", ""]:
            periods = f"{fast_period}/{slow_period}"
        else:
            periods = f"{fast_period}/{slow_period}/{signal_period}"

        # Get metrics for display including Total Trades
        total_trades = p.get("Total Trades", 0)
        score = p.get("Score", 0)
        win_rate = p.get("Win Rate [%]", 0)
        profit_factor = p.get("Profit Factor", 0)
        expectancy_per_trade = p.get("Expectancy per Trade", 0)
        sortino_ratio = p.get("Sortino Ratio", 0)
        total_return = p.get("Total Return [%]", 0)
        beats_bnh = p.get("Beats BNH [%]", 0)
        avg_trade_duration = p.get("Avg Trade Duration", "N/A")
        status = determine_portfolio_status(p)

        table.add_row(
            ticker,
            strategy_type,
            periods,
            str(total_trades),
            format_score(score),
            format_win_rate(win_rate),
            format_ratio(profit_factor),
            format_currency(expectancy_per_trade),
            format_ratio(sortino_ratio),
            format_percentage(total_return),
            format_percentage(beats_bnh),
            format_duration(avg_trade_duration),
            format_status(status),
        )

    console.print(table)

    # Summary statistics
    if len(display_portfolios) > 1:
        # Count strategies by status
        status_counts = {"Entry": 0, "Active": 0, "Exit": 0, "Inactive": 0}
        for p in display_portfolios:
            status = determine_portfolio_status(p)
            status_counts[status] = status_counts.get(status, 0) + 1

        avg_score = sum(float(p.get("Score", 0)) for p in display_portfolios) / len(
            display_portfolios
        )
        avg_win_rate = sum(
            float(p.get("Win Rate [%]", 0)) for p in display_portfolios
        ) / len(display_portfolios)
        avg_return = sum(
            float(p.get("Total Return [%]", 0)) for p in display_portfolios
        ) / len(display_portfolios)

        summary_title = (
            "Entry/Exit Summary"
            if "Entry/Exit" in section_title
            else "Portfolio Summary"
        )
        rprint(f"\n💡 [bold yellow]{summary_title}:[/bold yellow]")
        rprint(f"   📊 Average Score: {format_score(avg_score)}")
        rprint(f"   🎯 Average Win Rate: {format_win_rate(avg_win_rate)}")
        rprint(f"   💰 Average Return: {format_percentage(avg_return)}")

        # Status Breakdown with visual bars
        total_strategies = len(display_portfolios)
        breakdown_title = (
            "Signal Breakdown" if "Entry/Exit" in section_title else "Status Breakdown"
        )
        rprint(f"   📈 [bold yellow]{breakdown_title}:[/bold yellow]")

        # Define colors for each status type
        status_colors = {
            "Active": "blue",
            "Entry": "green",
            "Exit": "red",
            "Inactive": "cyan",
        }

        # Filter status_counts to only include relevant statuses for Entry/Exit
        if "Entry/Exit" in section_title:
            relevant_statuses = {
                k: v
                for k, v in status_counts.items()
                if k in ["Entry", "Exit"] and v > 0
            }
        else:
            relevant_statuses = {k: v for k, v in status_counts.items() if v > 0}

        for status, count in sorted(
            relevant_statuses.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total_strategies) * 100
            bar_length = int(percentage / 5)  # Scale for visual bar
            bar = "█" * bar_length + "░" * (20 - bar_length)
            color = status_colors.get(status, "cyan")
            rprint(
                f"     {status}: [{color}]{bar}[/{color}] {count} ({percentage:.1f}%)"
            )

    # Traditional logging if provided
    if log_func:
        if display_portfolios:
            log_title = (
                "Portfolio Entry/Exit Strategies"
                if "Entry/Exit" in section_title
                else "Portfolio Strategies"
            )
            log_func(f"\n=== {log_title} ===")
            log_func(
                "Ticker, Strategy Type, Fast Period, Slow Period, Signal Period, Total Trades, Score, Status"
            )
            for p in display_portfolios:
                ticker = p.get("Ticker", "Unknown")
                strategy_type = p.get("Strategy Type", "Unknown")
                fast_period = p.get("Fast Period", "N/A")
                slow_period = p.get("Slow Period", "N/A")
                signal_period = p.get("Signal Period", "N/A")
                total_trades = p.get("Total Trades", 0)
                score = p.get("Score", 0)
                status = determine_portfolio_status(p)
                log_func(
                    f"{ticker}, {strategy_type}, {fast_period}, {slow_period}, {signal_period}, {total_trades}, {score:.4f}, {status}"
                )
        else:
            not_found_title = (
                "No Entry/Exit Strategies found"
                if "Entry/Exit" in section_title
                else "No Portfolio Strategies found"
            )
            log_func(f"\n=== {not_found_title} ===")


def display_portfolio_table(
    portfolios: list[dict[str, Any]], log_func=None
) -> list[dict[str, Any]]:
    """Display all portfolios in a comprehensive table.

    Args:
        portfolios: List of portfolio dictionaries
        log_func: Optional logging function

    Returns:
        List of all portfolio dictionaries (no filtering)
    """
    if not portfolios:
        return []

    # Sort portfolios by Ticker (ascending), then Score (descending)
    def sort_key(portfolio):
        ticker = portfolio.get("Ticker", "")
        score = float(portfolio.get("Score", 0))
        return (ticker, -score)  # negative score for descending order

    display_portfolios = sorted(portfolios, key=sort_key)

    # Use shared core function for table display
    _display_portfolio_table_core(
        display_portfolios=display_portfolios,
        section_title="Portfolio",
        title_prefix="📊",
        title_style="bold cyan",
        log_func=log_func,
    )

    return display_portfolios


def display_portfolio_entry_exit_table(
    portfolios: list[dict[str, Any]], log_func=None
) -> list[dict[str, Any]]:
    """Display only Entry/Exit portfolios in a comprehensive table.

    Args:
        portfolios: List of portfolio dictionaries
        log_func: Optional logging function

    Returns:
        List of filtered Entry/Exit portfolio dictionaries
    """
    if not portfolios:
        return []

    # Filter portfolios to only include Entry and Exit status
    filtered_portfolios = []
    for portfolio in portfolios:
        status = determine_portfolio_status(portfolio)
        if status in ["Entry", "Exit"]:
            filtered_portfolios.append(portfolio)

    # Sort portfolios by Ticker (ascending), then Score (descending)
    def sort_key(portfolio):
        ticker = portfolio.get("Ticker", "")
        score = float(portfolio.get("Score", 0))
        return (ticker, -score)  # negative score for descending order

    display_portfolios = sorted(filtered_portfolios, key=sort_key)

    # Use shared core function for table display
    _display_portfolio_table_core(
        display_portfolios=display_portfolios,
        section_title="Portfolio Entry/Exit",
        title_prefix="🎯",
        title_style="bold bright_green",
        log_func=log_func,
    )

    return display_portfolios


def display_ticker_summary_table(
    portfolios: list[dict[str, Any]], log_func=None
) -> None:
    """Display ticker-level summary when multiple strategies exist per ticker.

    Shows aggregated metrics for each ticker including:
    - Number of active strategies (those with open trades)
    - Total number of strategies
    - Percentage active
    - Count of strategies with entry signals
    - Count of strategies with exit signals

    Only displays tickers that have more than one strategy.

    Args:
        portfolios: List of portfolio dictionaries
        log_func: Optional logging function
    """
    if not portfolios:
        return

    from collections import defaultdict

    # Group strategies by ticker
    ticker_data = defaultdict(
        lambda: {
            "total": 0,
            "active": 0,
            "entry_signal_count": 0,
            "exit_signal_count": 0,
        }
    )

    for portfolio in portfolios:
        ticker = portfolio.get("Ticker", "Unknown")
        ticker_data[ticker]["total"] += 1

        # Check if strategy is active (has open trade)
        total_open_trades = portfolio.get("Total Open Trades")
        if total_open_trades == 1 or (
            isinstance(total_open_trades, str) and total_open_trades == "1"
        ):
            ticker_data[ticker]["active"] += 1

        # Count entry/exit signals
        signal_entry = str(portfolio.get("Signal Entry", "")).lower() == "true"
        signal_exit = str(portfolio.get("Signal Exit", "")).lower() == "true"

        if signal_entry:
            ticker_data[ticker]["entry_signal_count"] += 1
        if signal_exit:
            ticker_data[ticker]["exit_signal_count"] += 1

    # Filter to only show tickers with multiple strategies
    multi_strategy_tickers = {
        ticker: data for ticker, data in ticker_data.items() if data["total"] > 1
    }

    if not multi_strategy_tickers:
        # No tickers with multiple strategies
        return

    # Create Rich table
    table = Table(
        title="📈 Ticker-Level Summary (Multiple Strategies per Ticker)",
        show_header=True,
        header_style="bold magenta",
        border_style="bright_blue",
    )

    # Add columns
    table.add_column("Ticker", style="cyan", no_wrap=True)
    table.add_column("Active Strategies", justify="center")
    table.add_column("Active %", justify="center")
    table.add_column("Entry Signal", justify="center", style="bright_green")
    table.add_column("Exit Signal", justify="center", style="bright_red")
    table.add_column("COMP", justify="center", style="bold")

    # Add rows sorted by Active % (descending), then by ticker
    sorted_tickers = sorted(
        multi_strategy_tickers.items(),
        key=lambda x: (
            (
                -(x[1]["active"] / x[1]["total"] * 100) if x[1]["total"] > 0 else 0
            ),  # Active % descending
            x[0],  # Ticker alphabetically as tiebreaker
        ),
    )

    for ticker, data in sorted_tickers:
        active_pct = (data["active"] / data["total"] * 100) if data["total"] > 0 else 0

        # Determine color based on percentage
        if active_pct == 0:
            color = "red"
        elif active_pct < 50:
            color = "yellow"
        else:
            color = "green"

        # Create styled Text objects
        active_display = Text(f"{data['active']}/{data['total']}", style=color)
        active_pct_display = Text(f"{active_pct:.1f}%", style=color)

        # Display counts for entry/exit signals
        entry_count = data["entry_signal_count"]
        exit_count = data["exit_signal_count"]

        # Calculate COMP status from aggregated strategy data
        comp_status = calculate_comp_status_from_aggregates(
            entry_count=entry_count,
            exit_count=exit_count,
            active_count=data["active"],
            total_count=data["total"],
        )
        comp_display = format_status(comp_status)

        table.add_row(
            ticker,
            active_display,
            active_pct_display,
            str(entry_count),
            str(exit_count),
            comp_display,
        )

    # Display table
    console.print()
    console.print(table)
    console.print()

    if log_func:
        log_func(
            f"Displayed ticker summary for {len(multi_strategy_tickers)} tickers with multiple strategies"
        )


def filter_signal_entries(
    portfolios: list[dict[str, Any]],
    open_trades: list[dict[str, Any]] | None = None,
    log_func=None,
) -> list[dict[str, Any]]:
    """Filter portfolios to only include signal entries.

    Args:
        portfolios: List of portfolio dictionaries
        open_trades: Optional list of open trades for counting
        log_func: Optional logging function

    Returns:
        Filtered list of portfolio dictionaries
    """
    if not portfolios:
        return []

    # List strategies where Signal Entry = true
    signal_entries = [
        p for p in portfolios if str(p.get("Signal Entry", "")).lower() == "true"
    ]

    # Count strategies per ticker if open_trades is provided
    if open_trades:
        ticker_counts: dict[str, int] = {}
        for p in open_trades:
            ticker = p.get("Ticker", "Unknown")
            ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1

        # Add the count to each strategy
        for p in signal_entries:
            ticker = p.get("Ticker", "Unknown")
            p["open_trade_count"] = ticker_counts.get(ticker, 0)

    # Sort signal entry strategies by Score
    config = {"SORT_BY": "Score", "SORT_ASC": False}
    signal_entries = sort_portfolios(signal_entries, config)

    # Rich table display for signal entries
    if signal_entries:
        create_section_header("Market Opportunities", "🎯")

        table = Table(
            title=f"⚡ {len(signal_entries)} Entry Signals Detected",
            show_header=True,
            header_style="bold magenta",
            title_style="bold bright_green",
        )

        table.add_column("Ticker", style="cyan bold", no_wrap=True)
        table.add_column("Strategy", style="blue", no_wrap=True)
        table.add_column("Periods", style="white", justify="center")
        table.add_column("Score", style="bold", justify="right")
        table.add_column("Win Rate", justify="right")
        table.add_column("Expected Return", justify="right")
        table.add_column("Risk Level", justify="center")
        table.add_column("Open Trades", justify="center")

        for p in signal_entries:
            ticker = p.get("Ticker", "Unknown")
            strategy_type = p.get("Strategy Type", "Unknown")
            fast_period = p.get("Fast Period", "N/A")
            slow_period = p.get("Slow Period", "N/A")
            signal_period = p.get("Signal Period", "N/A")

            # Format periods
            if str(signal_period).lower() in ["0", "n/a", "none", ""]:
                periods = f"{fast_period}/{slow_period}"
            else:
                periods = f"{fast_period}/{slow_period}/{signal_period}"

            # Get metrics
            score = p.get("Score", 0)
            win_rate = p.get("Win Rate [%]", 0)
            total_return = p.get("Total Return [%]", 0)
            open_trade_count = p.get("open_trade_count", 0)

            # Determine risk level based on score and win rate
            try:
                score_val = float(score)
                win_rate_val = float(win_rate)
                if score_val >= 1.5 and win_rate_val >= 60:
                    risk_level = Text("🟢 Low", style="green")
                elif score_val >= 1.2 and win_rate_val >= 50:
                    risk_level = Text("🟡 Med", style="yellow")
                elif score_val >= 1.0:
                    risk_level = Text("🟠 High", style="orange")
                else:
                    risk_level = Text("🔴 Very High", style="red")
            except:
                risk_level = Text("❓ Unknown", style="dim")

            # Format open trade count with warning if too many
            if open_trade_count > 2:
                open_trades_text = Text(f"⚠️ {open_trade_count}", style="red")
            elif open_trade_count > 0:
                open_trades_text = Text(f"🔹 {open_trade_count}", style="yellow")
            else:
                open_trades_text = Text("✨ New", style="green")

            table.add_row(
                ticker,
                strategy_type,
                periods,
                format_score(score),
                format_win_rate(win_rate),
                format_percentage(total_return),
                risk_level,
                open_trades_text,
            )

        console.print(table)

        # Signal opportunity analysis
        if len(signal_entries) > 0:
            high_quality_signals = [
                p
                for p in signal_entries
                if float(p.get("Score", 0)) >= 1.2
                and float(p.get("Win Rate [%]", 0)) >= 55
            ]
            avg_score = sum(float(p.get("Score", 0)) for p in signal_entries) / len(
                signal_entries
            )
            avg_win_rate = sum(
                float(p.get("Win Rate [%]", 0)) for p in signal_entries
            ) / len(signal_entries)

            rprint("\n🔍 [bold yellow]Entry Signal Analysis:[/bold yellow]")
            rprint(
                f"   🎯 High Quality Signals: [bold green]{len(high_quality_signals)}[/bold green] of {len(signal_entries)}"
            )
            rprint(f"   📊 Average Score: {format_score(avg_score)}")
            rprint(f"   🎯 Average Win Rate: {format_win_rate(avg_win_rate)}")

            if high_quality_signals:
                rprint(
                    f"   💡 [green]Recommended action: Consider {len(high_quality_signals)} high-quality opportunities[/green]"
                )
            else:
                rprint(
                    "   ⚠️ [yellow]Caution: No high-quality signals detected - wait for better setups[/yellow]"
                )
    else:
        create_section_header("Market Scan", "🔍")
        rprint("[blue]📊 No entry signals detected[/blue]")
        rprint(
            "[dim]   Market is consolidating or trending against strategy parameters[/dim]"
        )
        rprint(
            "[dim]   This could be a good time to wait for better opportunities[/dim]"
        )

    # Also log to the traditional log function if provided
    if log_func:
        if signal_entries:
            log_func("\n=== Signal Entries ===")
            log_func(
                "Ticker, Strategy Type, Fast Period, Slow Period, Signal Period, Score, Total Open Trades"
            )
            for p in signal_entries:
                ticker = p.get("Ticker", "Unknown")
                strategy_type = p.get("Strategy Type", "Unknown")
                fast_period = p.get("Fast Period", "N/A")
                slow_period = p.get("Slow Period", "N/A")
                signal_period = p.get("Signal Period", "N/A")
                score = p.get("Score", 0)
                open_trade_count = p.get("open_trade_count", 0)
                log_func(
                    f"{ticker}, {strategy_type}, {fast_period}, {slow_period}, {signal_period}, {score:.4f}, {open_trade_count}"
                )
        else:
            log_func("Filtered out 7 portfolios with Signal Entry = False")
            log_func("Remaining portfolios: 0")
            log_func("\n=== No Signal Entries found ===")

    return signal_entries


def calculate_breadth_metrics(
    portfolios: list[dict[str, Any]],
    open_trades: list[dict[str, Any]] | None = None,
    signal_entries: list[dict[str, Any]] | None = None,
    log_func=None,
) -> dict[str, float]:
    """Calculate breadth metrics for a set of portfolios.

    Args:
        portfolios: List of portfolio dictionaries
        open_trades: Optional list of open trades
        signal_entries: Optional list of signal entries
        log_func: Optional logging function

    Returns:
        Dictionary of breadth metrics
    """
    if not portfolios:
        return {}

    # Get total number of strategies
    total_strategies = len(portfolios)

    # Count open trades
    total_open_trades = (
        len(open_trades)
        if open_trades is not None
        else len(
            [
                p
                for p in portfolios
                if (
                    p.get("Total Open Trades") == 1
                    or (
                        isinstance(p.get("Total Open Trades"), str)
                        and p.get("Total Open Trades") == "1"
                    )
                )
                and str(p.get("Signal Entry", "")).lower() != "true"
            ]
        )
    )

    # Count signal entries
    total_signal_entries = (
        len(signal_entries)
        if signal_entries is not None
        else len(
            [p for p in portfolios if str(p.get("Signal Entry", "")).lower() == "true"]
        )
    )

    # Count signal exits
    signal_exit_strategies = [
        p for p in portfolios if str(p.get("Signal Exit", "")).lower() == "true"
    ]
    total_signal_exits = len(signal_exit_strategies)

    # Calculate breadth ratio (open trades to total strategies)
    breadth_ratio = total_open_trades / total_strategies if total_strategies > 0 else 0

    # Calculate signal entry ratio
    signal_entry_ratio = (
        total_signal_entries / total_strategies if total_strategies > 0 else 0
    )

    # Calculate signal exit ratio
    signal_exit_ratio = (
        total_signal_exits / total_strategies if total_strategies > 0 else 0
    )

    # Calculate breadth momentum (signal entry ratio / signal exit ratio)
    breadth_momentum = (
        signal_entry_ratio / signal_exit_ratio
        if signal_exit_ratio > 0
        else 0.0  # When no exit signals, momentum is 0 (no selling pressure)
    )

    metrics = {
        "total_strategies": total_strategies,
        "total_open_trades": total_open_trades,
        "total_signal_entries": total_signal_entries,
        "total_signal_exits": total_signal_exits,
        "breadth_ratio": breadth_ratio,
        "signal_entry_ratio": signal_entry_ratio,
        "signal_exit_ratio": signal_exit_ratio,
        "breadth_momentum": breadth_momentum,
    }

    # Rich visual dashboard for breadth metrics
    create_section_header("Portfolio Breadth Analysis", "📊")

    # Market Sentiment Overview
    if breadth_ratio >= 0.7:
        sentiment_emoji = "🔥"
        sentiment_text = "Strong Bullish"
        sentiment_color = "bright_green"
    elif breadth_ratio >= 0.5:
        sentiment_emoji = "📈"
        sentiment_text = "Moderately Bullish"
        sentiment_color = "green"
    elif breadth_ratio >= 0.3:
        sentiment_emoji = "⚖️"
        sentiment_text = "Neutral"
        sentiment_color = "yellow"
    elif breadth_ratio >= 0.1:
        sentiment_emoji = "📉"
        sentiment_text = "Moderately Bearish"
        sentiment_color = "orange"
    else:
        sentiment_emoji = "❄️"
        sentiment_text = "Bearish"
        sentiment_color = "red"

    rprint(
        f"\n🌡️  [bold]Market Sentiment: {sentiment_emoji} [{sentiment_color}]{sentiment_text}[/{sentiment_color}][/bold]"
    )

    # Breadth Dashboard Table
    breadth_table = Table(
        title="📊 Portfolio Breadth Dashboard",
        show_header=True,
        header_style="bold magenta",
        title_style="bold cyan",
    )

    breadth_table.add_column("Metric", style="cyan", no_wrap=True)
    breadth_table.add_column("Count", style="bold white", justify="right")
    breadth_table.add_column("Ratio", style="bold", justify="right")
    breadth_table.add_column("Interpretation", style="white")

    # Format breadth ratio
    breadth_ratio_text = Text(f"{breadth_ratio:.1%}", style=sentiment_color)

    # Format signal ratios
    entry_ratio_color = (
        "green"
        if signal_entry_ratio > 0.1
        else "yellow"
        if signal_entry_ratio > 0
        else "red"
    )
    entry_ratio_text = Text(f"{signal_entry_ratio:.1%}", style=entry_ratio_color)

    exit_ratio_color = (
        "red"
        if signal_exit_ratio > 0.1
        else "yellow"
        if signal_exit_ratio > 0
        else "green"
    )
    exit_ratio_text = Text(f"{signal_exit_ratio:.1%}", style=exit_ratio_color)

    # Momentum interpretation
    if breadth_momentum > 2.0:
        momentum_interp = "🚀 Very Strong Buying"
        momentum_color = "bright_green"
    elif breadth_momentum > 1.0:
        momentum_interp = "📈 Buying Pressure"
        momentum_color = "green"
    elif breadth_momentum == 0.0:
        momentum_interp = "⚖️ Neutral Momentum"
        momentum_color = "yellow"
    elif breadth_momentum < 0.5:
        momentum_interp = "📉 Selling Pressure"
        momentum_color = "red"
    else:
        momentum_interp = "🔄 Mixed Signals"
        momentum_color = "orange"

    momentum_text = Text(f"{breadth_momentum:.2f}", style=momentum_color)

    breadth_table.add_row(
        "Total Strategies", str(total_strategies), "100%", "Universe size"
    )
    breadth_table.add_row(
        "🎯 Open Positions",
        str(total_open_trades),
        breadth_ratio_text,
        f"{sentiment_text} market",
    )
    breadth_table.add_row(
        "⚡ Entry Signals",
        str(total_signal_entries),
        entry_ratio_text,
        "New opportunities" if total_signal_entries > 0 else "No new signals",
    )
    breadth_table.add_row(
        "🚪 Exit Signals",
        str(total_signal_exits),
        exit_ratio_text,
        "Take profit signals" if total_signal_exits > 0 else "No exit pressure",
    )
    breadth_table.add_row("📊 Market Momentum", "-", momentum_text, momentum_interp)

    console.print(breadth_table)

    # Market insights and recommendations
    rprint("\n💡 [bold yellow]Market Insights:[/bold yellow]")

    if total_signal_entries > total_signal_exits:
        rprint(
            f"   🔥 [green]Bullish setup: {total_signal_entries} entries vs {total_signal_exits} exits[/green]"
        )
    elif total_signal_exits > total_signal_entries:
        rprint(
            f"   ❄️ [red]Bearish setup: {total_signal_exits} exits vs {total_signal_entries} entries[/red]"
        )
    else:
        rprint("   ⚖️ [yellow]Balanced market: Equal entry/exit pressure[/yellow]")

    # Portfolio concentration analysis
    if total_open_trades > 0:
        concentration = total_open_trades / total_strategies
        if concentration > 0.8:
            rprint(
                f"   ⚠️ [red]High concentration risk: {concentration:.1%} of strategies active[/red]"
            )
        elif concentration < 0.2:
            rprint(
                f"   🛡️ [green]Conservative positioning: {concentration:.1%} exposure[/green]"
            )
        else:
            rprint(
                f"   ✅ [blue]Balanced exposure: {concentration:.1%} of strategies active[/blue]"
            )

    # Momentum analysis
    if breadth_momentum > 1.5:
        rprint(
            "   🚀 [bright_green]Strong buying momentum - consider position sizing up[/bright_green]"
        )
    elif breadth_momentum < 0.5 and signal_exit_ratio > 0:
        rprint("   📉 [red]Selling pressure detected - consider risk management[/red]")
    elif total_signal_entries == 0 and total_signal_exits == 0:
        rprint(
            "   😴 [yellow]Quiet market - good time for patience and preparation[/yellow]"
        )

    # Also log to the traditional log function if provided
    if log_func:
        log_func("\n=== Breadth Metrics ===")
        log_func(f"Total Strategies: {total_strategies}")
        log_func(f"Total Open Trades: {total_open_trades}")
        log_func(f"Total Signal Entries: {total_signal_entries}")
        log_func(f"Total Signal Exits: {total_signal_exits}")
        log_func(f"Breadth Ratio: {breadth_ratio:.4f} (Open Trades / Total Strategies)")
        log_func(
            f"Signal Entry Ratio: {signal_entry_ratio:.4f} (Signal Entries / Total Strategies)"
        )
        log_func(
            f"Signal Exit Ratio: {signal_exit_ratio:.4f} (Signal Exits / Total Strategies)"
        )
        momentum_msg = (
            f"Breadth Momentum: {breadth_momentum:.4f} (Signal Entry Ratio / Signal Exit Ratio)"
            if signal_exit_ratio > 0
            else f"Breadth Momentum: {breadth_momentum:.4f} (No exit signals - momentum neutral)"
        )
        log_func(momentum_msg)

    return metrics


def display_portfolio_summary(
    portfolios: list[dict[str, Any]], execution_time: float | None = None, log_func=None
) -> None:
    """Display comprehensive portfolio summary with market insights and key takeaways.

    Args:
        portfolios: List of all portfolio dictionaries
        execution_time: Optional execution time in seconds
        log_func: Optional logging function
    """
    if not portfolios:
        create_section_header("Portfolio Summary", "📈")
        rprint("[yellow]⚠️  No portfolio data available[/yellow]")
        return

    # Calculate key performance metrics
    total_strategies = len(portfolios)
    profitable_strategies = len(
        [p for p in portfolios if float(p.get("Total Return [%]", 0)) > 0]
    )
    high_score_strategies = len(
        [p for p in portfolios if float(p.get("Score", 0)) >= 1.2]
    )

    # Get top performers
    sorted_portfolios = sorted(
        portfolios, key=lambda x: float(x.get("Score", 0)), reverse=True
    )
    top_3_performers = sorted_portfolios[:3]

    # Calculate average metrics
    avg_score = sum(float(p.get("Score", 0)) for p in portfolios) / total_strategies
    avg_win_rate = (
        sum(float(p.get("Win Rate [%]", 0)) for p in portfolios) / total_strategies
    )
    avg_return = (
        sum(float(p.get("Total Return [%]", 0)) for p in portfolios) / total_strategies
    )

    # Calculate new average metrics
    avg_profit_factor = (
        sum(float(p.get("Profit Factor", 0)) for p in portfolios) / total_strategies
    )

    # Parse expectancy values (remove $ and convert to float)
    def parse_expectancy(value):
        if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
            return 0.0
        try:
            # Remove currency symbols and convert to float
            clean_value = str(value).replace("$", "").replace(",", "").strip()
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    avg_expectancy = (
        sum(parse_expectancy(p.get("Expectancy per Trade", 0)) for p in portfolios)
        / total_strategies
    )

    avg_sortino = (
        sum(float(p.get("Sortino Ratio", 0)) for p in portfolios) / total_strategies
    )

    # Parse Beats BNH percentage values
    def parse_percentage(value):
        if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
            return 0.0
        try:
            # Remove % symbol and convert to float
            clean_value = str(value).replace("%", "").strip()
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0

    avg_beats_bnh = (
        sum(parse_percentage(p.get("Beats BNH [%]", 0)) for p in portfolios)
        / total_strategies
    )

    # Calculate average duration in hours
    total_duration_hours = sum(
        parse_duration_to_hours(p.get("Avg Trade Duration", 0)) for p in portfolios
    )
    avg_duration_hours = total_duration_hours / total_strategies

    # Strategy type distribution
    strategy_types = {}
    for p in portfolios:
        strategy_type = p.get("Strategy Type", "Unknown")
        strategy_types[strategy_type] = strategy_types.get(strategy_type, 0) + 1

    create_section_header("Portfolio Performance Summary", "📈")

    # Performance Overview Table
    perf_table = Table(
        title="🏆 Portfolio Performance Overview",
        show_header=True,
        header_style="bold magenta",
        title_style="bold green",
    )

    perf_table.add_column("Metric", style="cyan", no_wrap=True)
    perf_table.add_column("Value", style="bold white", justify="right")
    perf_table.add_column("Quality", style="bold", justify="center")
    perf_table.add_column("Benchmark", style="dim")

    # Profitability percentage
    profit_rate = (profitable_strategies / total_strategies) * 100
    profit_quality = (
        "🔥 Excellent"
        if profit_rate >= 80
        else (
            "📈 Good"
            if profit_rate >= 60
            else "⚖️ Fair"
            if profit_rate >= 40
            else "📉 Poor"
        )
    )
    profit_color = (
        "bright_green"
        if profit_rate >= 80
        else "green"
        if profit_rate >= 60
        else "yellow"
        if profit_rate >= 40
        else "red"
    )

    # High score percentage
    score_rate = (high_score_strategies / total_strategies) * 100
    score_quality = (
        "🔥 Elite"
        if score_rate >= 70
        else (
            "📈 Strong"
            if score_rate >= 50
            else "⚖️ Moderate"
            if score_rate >= 30
            else "📉 Weak"
        )
    )
    score_color = (
        "bright_green"
        if score_rate >= 70
        else "green"
        if score_rate >= 50
        else "yellow"
        if score_rate >= 30
        else "red"
    )

    perf_table.add_row(
        "Total Strategies",
        str(total_strategies),
        "📊 Universe",
        "All tracked strategies",
    )
    perf_table.add_row(
        "Profitable Strategies",
        f"{profitable_strategies} ({profit_rate:.1f}%)",
        Text(profit_quality, style=profit_color),
        "> 60% is good",
    )
    perf_table.add_row(
        "High Score Strategies",
        f"{high_score_strategies} ({score_rate:.1f}%)",
        Text(score_quality, style=score_color),
        "Score ≥ 1.2",
    )
    perf_table.add_row(
        "Average Score", f"{avg_score:.3f}", format_score(avg_score), "> 1.0 is good"
    )
    perf_table.add_row(
        "Average Win Rate",
        f"{avg_win_rate:.1f}%",
        format_win_rate(avg_win_rate),
        "> 55% is good",
    )
    perf_table.add_row(
        "Average Return",
        f"{avg_return:.1f}%",
        format_percentage(avg_return),
        "Varies by timeframe",
    )
    perf_table.add_row(
        "Average Profit Factor",
        f"{avg_profit_factor:.2f}",
        format_ratio(avg_profit_factor),
        "> 1.5 is good",
    )
    perf_table.add_row(
        "Average Expectancy",
        f"${avg_expectancy:.2f}",
        format_currency(avg_expectancy),
        "> $0 is profitable",
    )
    perf_table.add_row(
        "Average Sortino",
        f"{avg_sortino:.2f}",
        format_ratio(avg_sortino),
        "> 1.0 is good",
    )
    perf_table.add_row(
        "Average Beats BNH",
        f"{avg_beats_bnh:.1f}%",
        format_percentage(avg_beats_bnh),
        "> 0% beats benchmark",
    )
    perf_table.add_row(
        "Average Duration",
        format_average_duration(avg_duration_hours),
        format_duration(format_average_duration(avg_duration_hours)),
        "Trade holding period",
    )

    console.print(perf_table)

    # Top Performers Table
    if top_3_performers:
        rprint("\n🏆 [bold yellow]Top 3 Performers:[/bold yellow]")

        top_table = Table(show_header=True, header_style="bold magenta")

        top_table.add_column("Rank", style="cyan bold", justify="center")
        top_table.add_column("Ticker", style="cyan bold", no_wrap=True)
        top_table.add_column("Strategy", style="blue", no_wrap=True)
        top_table.add_column("Score", style="bold", justify="right")
        top_table.add_column("Win Rate", justify="right")
        top_table.add_column("Return", justify="right")
        top_table.add_column("Status", justify="center")

        for i, p in enumerate(top_3_performers, 1):
            rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            ticker = p.get("Ticker", "Unknown")
            strategy_type = p.get("Strategy Type", "Unknown")
            score = p.get("Score", 0)
            win_rate = p.get("Win Rate [%]", 0)
            total_return = p.get("Total Return [%]", 0)
            signal_entry = str(p.get("Signal Entry", "")).lower() == "true"
            signal_exit = str(p.get("Signal Exit", "")).lower() == "true"
            signal_unconfirmed = p.get("Signal Unconfirmed", "")

            top_table.add_row(
                f"{rank_emoji} #{i}",
                ticker,
                strategy_type,
                format_score(score),
                format_win_rate(win_rate),
                format_percentage(total_return),
                format_signal_status(signal_entry, signal_exit, signal_unconfirmed),
            )

        console.print(top_table)

    # Strategy Distribution
    if strategy_types:
        rprint("\n📊 [bold yellow]Strategy Distribution:[/bold yellow]")
        for strategy, count in sorted(
            strategy_types.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total_strategies) * 100
            bar_length = int(percentage / 5)  # Scale for visual bar
            bar = "█" * bar_length + "░" * (20 - bar_length)
            rprint(f"   {strategy}: [cyan]{bar}[/cyan] {count} ({percentage:.1f}%)")

    # Key Insights
    rprint("\n💡 [bold yellow]Key Insights & Recommendations:[/bold yellow]")

    if avg_score >= 1.3:
        rprint(
            f"   🔥 [bright_green]Exceptional portfolio performance - average score {avg_score:.3f}[/bright_green]"
        )
    elif avg_score >= 1.1:
        rprint(
            f"   📈 [green]Strong portfolio performance - average score {avg_score:.3f}[/green]"
        )
    elif avg_score >= 0.9:
        rprint(
            f"   ⚖️ [yellow]Moderate performance - average score {avg_score:.3f}[/yellow]"
        )
    else:
        rprint(
            "   📉 [red]Below-average performance - review strategy parameters[/red]"
        )

    if profit_rate >= 70:
        rprint(
            f"   💰 [green]Strong profitability: {profit_rate:.1f}% of strategies profitable[/green]"
        )
    elif profit_rate < 50:
        rprint(
            f"   ⚠️ [yellow]Profitability concern: Only {profit_rate:.1f}% strategies profitable[/yellow]"
        )

    # Strategy-specific insights
    if strategy_types:
        best_strategy = max(strategy_types.items(), key=lambda x: x[1])
        rprint(
            f"   📊 [blue]Most used strategy: {best_strategy[0]} ({best_strategy[1]} strategies)[/blue]"
        )
    else:
        rprint("   ⚠️ [yellow]No strategy types detected in portfolio data[/yellow]")

    # Risk and opportunity assessment
    signal_entries = [
        p for p in portfolios if str(p.get("Signal Entry", "")).lower() == "true"
    ]
    signal_exits = [
        p for p in portfolios if str(p.get("Signal Exit", "")).lower() == "true"
    ]

    if len(signal_entries) > len(signal_exits):
        rprint(
            f"   🎯 [green]Opportunity-rich environment: {len(signal_entries)} entries vs {len(signal_exits)} exits[/green]"
        )
    elif len(signal_exits) > len(signal_entries):
        rprint(
            f"   🛡️ [yellow]Risk management mode: {len(signal_exits)} exits vs {len(signal_entries)} entries[/yellow]"
        )

    # Execution summary
    if execution_time:
        create_section_header("Execution Summary", "⚡")
        rprint(
            f"🕐 Analysis completed in [bold cyan]{execution_time:.2f} seconds[/bold cyan]"
        )
        rprint(
            f"📊 Processed [bold green]{total_strategies} strategies[/bold green] across [bold blue]{len({p.get('Ticker', '') for p in portfolios})} tickers[/bold blue]"
        )

        if execution_time < 5:
            rprint("⚡ [green]Lightning fast execution![/green]")
        elif execution_time < 15:
            rprint("🏃 [blue]Quick and efficient analysis[/blue]")
        else:
            rprint("🐌 [yellow]Consider optimization for faster analysis[/yellow]")

    rprint("\n✨ [bold green]Portfolio update completed successfully![/bold green]")
    rprint(
        "[dim]Use these insights to guide your trading decisions and risk management.[/dim]"
    )
