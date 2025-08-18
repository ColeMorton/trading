"""Portfolio result processing utilities.

This module provides utilities for processing and displaying portfolio results.
"""

from typing import Any, Dict, List, Optional

from rich import print as rprint
from rich.console import Console
from rich.table import Table
from rich.text import Text

from app.tools.portfolio.collection import sort_portfolios

# Rich console for output
console = Console()


# Rich display helper functions
def format_percentage(value: float, positive_good: bool = True) -> Text:
    """Format percentage with color coding."""
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        color = (
            "green"
            if (val > 0 and positive_good) or (val < 0 and not positive_good)
            else "red"
        )
        if abs(val) < 0.01:  # Very small values
            color = "yellow"
        return Text(f"{val:.2f}%", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_currency(value: float) -> Text:
    """Format currency value with color coding."""
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        color = "green" if val > 0 else "red" if val < 0 else "yellow"
        if abs(val) >= 1000000:
            formatted = f"${val/1000000:.2f}M"
        elif abs(val) >= 1000:
            formatted = f"${val/1000:.1f}K"
        else:
            formatted = f"${val:.2f}"
        return Text(formatted, style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_score(value: float) -> Text:
    """Format score with color coding based on performance thresholds."""
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        if val >= 1.5:
            color = "bright_green"
            emoji = "🔥"
        elif val >= 1.2:
            color = "green"
            emoji = "📈"
        elif val >= 1.0:
            color = "yellow"
            emoji = "⚖️"
        elif val >= 0.8:
            color = "orange"
            emoji = "⚠️"
        else:
            color = "red"
            emoji = "📉"
        return Text(f"{emoji} {val:.4f}", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def format_signal_status(entry: bool, exit: bool, unconfirmed: str = None) -> Text:
    """Format signal status with appropriate icons and colors."""
    if entry:
        return Text("🎯 ENTRY", style="bright_green bold")
    elif exit:
        return Text("🚪 EXIT", style="red bold")
    elif unconfirmed and str(unconfirmed).lower() not in ["none", "n/a", ""]:
        return Text("⏳ PENDING", style="yellow")
    else:
        return Text("🔒 HOLD", style="blue")


def format_win_rate(value: float) -> Text:
    """Format win rate with color coding."""
    if value is None or value == "" or str(value).lower() in ["none", "n/a"]:
        return Text("N/A", style="dim")

    try:
        val = float(value)
        if val >= 70:
            color = "bright_green"
        elif val >= 60:
            color = "green"
        elif val >= 50:
            color = "yellow"
        elif val >= 40:
            color = "orange"
        else:
            color = "red"
        return Text(f"{val:.1f}%", style=color)
    except (ValueError, TypeError):
        return Text(str(value), style="dim")


def create_section_header(title: str, emoji: str = "📊") -> None:
    """Create a styled section header."""
    rprint(f"\n[bold cyan]{emoji} {title}[/bold cyan]")
    rprint("=" * (len(title) + 3))


# Removed duplicate sort_portfolios function - using unified implementation


def filter_open_trades(
    portfolios: List[Dict[str, Any]], log_func=None
) -> List[Dict[str, Any]]:
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

            rprint(f"\n💡 [bold yellow]Position Summary:[/bold yellow]")
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


def filter_signal_entries(
    portfolios: List[Dict[str, Any]],
    open_trades: Optional[List[Dict[str, Any]]] = None,
    log_func=None,
) -> List[Dict[str, Any]]:
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
        ticker_counts: Dict[str, int] = {}
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

            rprint(f"\n🔍 [bold yellow]Entry Signal Analysis:[/bold yellow]")
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
                    f"   ⚠️ [yellow]Caution: No high-quality signals detected - wait for better setups[/yellow]"
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
    portfolios: List[Dict[str, Any]],
    open_trades: Optional[List[Dict[str, Any]]] = None,
    signal_entries: Optional[List[Dict[str, Any]]] = None,
    log_func=None,
) -> Dict[str, float]:
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
    rprint(f"\n💡 [bold yellow]Market Insights:[/bold yellow]")

    if total_signal_entries > total_signal_exits:
        rprint(
            f"   🔥 [green]Bullish setup: {total_signal_entries} entries vs {total_signal_exits} exits[/green]"
        )
    elif total_signal_exits > total_signal_entries:
        rprint(
            f"   ❄️ [red]Bearish setup: {total_signal_exits} exits vs {total_signal_entries} entries[/red]"
        )
    else:
        rprint(f"   ⚖️ [yellow]Balanced market: Equal entry/exit pressure[/yellow]")

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
            f"   🚀 [bright_green]Strong buying momentum - consider position sizing up[/bright_green]"
        )
    elif breadth_momentum < 0.5 and signal_exit_ratio > 0:
        rprint(f"   📉 [red]Selling pressure detected - consider risk management[/red]")
    elif total_signal_entries == 0 and total_signal_exits == 0:
        rprint(
            f"   😴 [yellow]Quiet market - good time for patience and preparation[/yellow]"
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
    portfolios: List[Dict[str, Any]], execution_time: float = None, log_func=None
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
        else "📈 Good"
        if profit_rate >= 60
        else "⚖️ Fair"
        if profit_rate >= 40
        else "📉 Poor"
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
        else "📈 Strong"
        if score_rate >= 50
        else "⚖️ Moderate"
        if score_rate >= 30
        else "📉 Weak"
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

    console.print(perf_table)

    # Top Performers Table
    if top_3_performers:
        rprint(f"\n🏆 [bold yellow]Top 3 Performers:[/bold yellow]")

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
        rprint(f"\n📊 [bold yellow]Strategy Distribution:[/bold yellow]")
        for strategy, count in sorted(
            strategy_types.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / total_strategies) * 100
            bar_length = int(percentage / 5)  # Scale for visual bar
            bar = "█" * bar_length + "░" * (20 - bar_length)
            rprint(f"   {strategy}: [cyan]{bar}[/cyan] {count} ({percentage:.1f}%)")

    # Key Insights
    rprint(f"\n💡 [bold yellow]Key Insights & Recommendations:[/bold yellow]")

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
            f"   📉 [red]Below-average performance - review strategy parameters[/red]"
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
    best_strategy = max(strategy_types.items(), key=lambda x: x[1])
    rprint(
        f"   📊 [blue]Most used strategy: {best_strategy[0]} ({best_strategy[1]} strategies)[/blue]"
    )

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
            f"📊 Processed [bold green]{total_strategies} strategies[/bold green] across [bold blue]{len(set(p.get('Ticker', '') for p in portfolios))} tickers[/bold blue]"
        )

        if execution_time < 5:
            rprint(f"⚡ [green]Lightning fast execution![/green]")
        elif execution_time < 15:
            rprint(f"🏃 [blue]Quick and efficient analysis[/blue]")
        else:
            rprint(f"🐌 [yellow]Consider optimization for faster analysis[/yellow]")

    rprint(f"\n✨ [bold green]Portfolio update completed successfully![/bold green]")
    rprint(
        f"[dim]Use these insights to guide your trading decisions and risk management.[/dim]"
    )
