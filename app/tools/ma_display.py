"""
Moving Average Rich Display Module

This module provides beautiful Rich CLI formatting for moving average analytics results,
including tables, color coding, and visual indicators.
"""

from typing import Any

from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class MADisplayFormatter:
    """Rich CLI formatter for moving average analytics results."""

    def __init__(self, console: Console = None):
        """Initialize formatter with console."""
        self.console = console or Console()

    def display_complete_analysis(self, metrics: dict[str, Any]) -> None:
        """Display complete analysis with all sections."""
        self._display_summary_header(metrics["summary"])
        self._display_risk_metrics_table(metrics["risk_metrics"])
        self._display_performance_metrics_table(metrics["performance_metrics"])
        self._display_trend_analysis_table(metrics["trend_metrics"])
        self._display_statistical_summary(metrics["statistical_metrics"])

    def _display_summary_header(self, summary: dict[str, Any]) -> None:
        """Display summary header panel."""
        start_date = summary["start_date"]
        end_date = summary["end_date"]

        # Format dates
        if hasattr(start_date, "strftime"):
            start_str = start_date.strftime("%Y-%m-%d")
        else:
            start_str = str(start_date)[:10]

        if hasattr(end_date, "strftime"):
            end_str = end_date.strftime("%Y-%m-%d")
        else:
            end_str = str(end_date)[:10]

        summary_text = (
            f"[bold cyan]Ticker:[/bold cyan] {summary['ticker']} | "
            f"[bold cyan]Period:[/bold cyan] {summary['period']} | "
            f"[bold cyan]Type:[/bold cyan] {summary['ma_type']}\n"
            f"[bold cyan]Data Points:[/bold cyan] {summary['data_points']:,} | "
            f"[bold cyan]Date Range:[/bold cyan] {start_str} to {end_str} "
            f"({summary['date_range_days']} days)"
        )

        panel = Panel(
            summary_text,
            title="📊 Moving Average Analysis Summary",
            border_style="blue",
            box=ROUNDED,
        )
        self.console.print(panel)
        self.console.print()  # Add spacing

    def _display_risk_metrics_table(self, risk_metrics: dict[str, float]) -> None:
        """Display risk metrics in a formatted table."""
        table = Table(
            title="⚠️ Risk & Risk-Adjusted Performance Analysis",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="red",
        )
        table.add_column("Metric", style="white", no_wrap=True)
        table.add_column("Value", style="yellow", justify="right")
        table.add_column("Rating", style="green", justify="center")
        table.add_column("Benchmark", style="dim", justify="center")

        # Sharpe Ratio
        sharpe = risk_metrics["sharpe_ratio"]
        sharpe_rating = self._rate_sharpe_ratio(sharpe)
        table.add_row(
            "🔥 Sharpe Ratio",
            f"{sharpe:.3f}",
            sharpe_rating,
            ">1.0 Good, >2.0 Excellent",
        )

        # Sortino Ratio
        sortino = risk_metrics["sortino_ratio"]
        sortino_rating = self._rate_sortino_ratio(sortino)
        table.add_row(
            "📉 Sortino Ratio",
            f"{sortino:.3f}",
            sortino_rating,
            ">1.5 Good, >2.5 Excellent",
        )

        # Max Drawdown
        max_dd = risk_metrics["max_drawdown"]
        dd_rating = self._rate_max_drawdown(max_dd)
        table.add_row(
            "⬇️ Max Drawdown", f"{max_dd:.2f}%", dd_rating, "<10% Low, <20% Moderate",
        )

        # Volatility
        volatility = risk_metrics["volatility"]
        vol_rating = self._rate_volatility(volatility)
        table.add_row(
            "📊 Volatility (Annual)",
            f"{volatility:.2f}%",
            vol_rating,
            "15-25% Moderate",
        )

        # VaR 95%
        var_95 = risk_metrics["var_95"]
        table.add_row(
            "📉 VaR (95%)",
            f"{var_95:.2f}%",
            self._format_var_display(var_95),
            "Daily risk measure",
        )

        # CVaR 95%
        cvar_95 = risk_metrics["cvar_95"]
        table.add_row(
            "⚡ CVaR (95%)",
            f"{cvar_95:.2f}%",
            self._format_var_display(cvar_95),
            "Tail risk measure",
        )

        self.console.print(table)
        self.console.print()  # Add spacing

    def _display_performance_metrics_table(self, performance: dict[str, float]) -> None:
        """Display performance metrics in a formatted table."""
        table = Table(
            title="💰 Performance Metrics",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="green",
        )
        table.add_column("Metric", style="white", no_wrap=True)
        table.add_column("Value", style="yellow", justify="right")
        table.add_column("Status", style="green", justify="center")

        # Total Return
        total_return = performance["total_return"]
        table.add_row(
            "📈 Total Return", f"{total_return:+.2f}%", self._rate_return(total_return),
        )

        # Annualized Return
        annual_return = performance["annualized_return"]
        table.add_row(
            "📅 Annualized Return",
            f"{annual_return:+.2f}%",
            self._rate_annual_return(annual_return),
        )

        # CAGR
        cagr = performance["cagr"]
        table.add_row("📊 CAGR", f"{cagr:+.2f}%", self._rate_annual_return(cagr))

        # Calmar Ratio
        calmar = performance["calmar_ratio"]
        table.add_row(
            "⚖️ Calmar Ratio", f"{calmar:.3f}", self._rate_calmar_ratio(calmar),
        )

        # Information Ratio
        info_ratio = performance["information_ratio"]
        table.add_row(
            "📊 Information Ratio",
            f"{info_ratio:.3f}",
            self._rate_information_ratio(info_ratio),
        )

        self.console.print(table)
        self.console.print()  # Add spacing

    def _display_trend_analysis_table(self, trend_metrics: dict[str, Any]) -> None:
        """Display trend analysis in a formatted table."""
        table = Table(
            title="📈 Trend Analysis",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="blue",
        )
        table.add_column("Metric", style="white", no_wrap=True)
        table.add_column("Value", style="yellow", justify="right")
        table.add_column("Indicator", style="green", justify="center")

        # Trend Direction
        direction = trend_metrics["trend_direction"]
        table.add_row(
            "🎯 Current Trend", direction, self._format_trend_direction(direction),
        )

        # Trend Strength
        strength = trend_metrics["trend_strength"]
        table.add_row(
            "💪 Trend Strength", strength, self._format_trend_strength(strength),
        )

        # R-squared
        r_squared = trend_metrics["r_squared"]
        table.add_row(
            "📊 R² vs Time", f"{r_squared:.3f}", self._rate_r_squared(r_squared),
        )

        # Smoothness Factor
        smoothness = trend_metrics["smoothness_factor"]
        table.add_row(
            "🌊 Smoothness Factor",
            f"{smoothness:.3f}",
            self._rate_smoothness(smoothness),
        )

        # Linear Slope
        slope = trend_metrics["linear_slope"]
        table.add_row(
            "📐 Linear Slope", f"{slope:.6f}", self._format_slope_indicator(slope),
        )

        self.console.print(table)
        self.console.print()  # Add spacing

    def _display_statistical_summary(self, stats: dict[str, float]) -> None:
        """Display statistical summary in a compact format."""
        # Create a summary panel with key statistics
        mean_return = stats["mean_return"] * 100  # Convert to percentage
        std_dev = stats["std_deviation"] * 100  # Convert to percentage

        stats_text = (
            f"[bold cyan]Mean Daily Return:[/bold cyan] {mean_return:+.3f}% | "
            f"[bold cyan]Daily Volatility:[/bold cyan] {std_dev:.3f}%\n"
            f"[bold cyan]Skewness:[/bold cyan] {stats['skewness']:+.3f} | "
            f"[bold cyan]Kurtosis:[/bold cyan] {stats['kurtosis']:+.3f} | "
            f"[bold cyan]Autocorrelation:[/bold cyan] {stats['autocorrelation']:+.3f}\n"
            f"[bold cyan]Price Mean:[/bold cyan] ${stats['price_mean']:.2f} | "
            f"[bold cyan]Price Median:[/bold cyan] ${stats['price_median']:.2f}"
        )

        panel = Panel(
            stats_text,
            title="📊 Statistical Summary",
            border_style="yellow",
            box=ROUNDED,
        )
        self.console.print(panel)

    # Rating and formatting methods
    def _rate_sharpe_ratio(self, sharpe: float) -> Text:
        """Rate Sharpe ratio with color and emoji."""
        if sharpe >= 2.0:
            return Text("🔥 Excellent", style="bright_green")
        if sharpe >= 1.5:
            return Text("📈 Very Good", style="green")
        if sharpe >= 1.0:
            return Text("✅ Good", style="yellow")
        if sharpe >= 0.5:
            return Text("⚖️ Fair", style="yellow")
        return Text("📉 Poor", style="red")

    def _rate_sortino_ratio(self, sortino: float) -> Text:
        """Rate Sortino ratio with color and emoji."""
        if sortino >= 2.5:
            return Text("🔥 Excellent", style="bright_green")
        if sortino >= 2.0:
            return Text("📈 Very Good", style="green")
        if sortino >= 1.5:
            return Text("✅ Good", style="yellow")
        if sortino >= 1.0:
            return Text("⚖️ Fair", style="yellow")
        return Text("📉 Poor", style="red")

    def _rate_max_drawdown(self, drawdown: float) -> Text:
        """Rate max drawdown with color and emoji."""
        if drawdown <= 5:
            return Text("✅ Excellent", style="bright_green")
        if drawdown <= 10:
            return Text("📈 Good", style="green")
        if drawdown <= 20:
            return Text("⚠️ Moderate", style="yellow")
        if drawdown <= 30:
            return Text("📉 High", style="yellow")
        return Text("🚨 Very High", style="red")

    def _rate_volatility(self, volatility: float) -> Text:
        """Rate volatility with color and emoji."""
        if volatility <= 10:
            return Text("😴 Very Low", style="green")
        if volatility <= 20:
            return Text("📈 Low", style="yellow")
        if volatility <= 30:
            return Text("⚖️ Moderate", style="yellow")
        if volatility <= 40:
            return Text("📊 High", style="red")
        return Text("🌪️ Very High", style="bright_red")

    def _format_var_display(self, var: float) -> Text:
        """Format VaR display with appropriate color."""
        if var >= -1:
            return Text("✅ Low Risk", style="green")
        if var >= -3:
            return Text("⚠️ Moderate", style="yellow")
        if var >= -5:
            return Text("📉 High Risk", style="yellow")
        return Text("🚨 Very High", style="red")

    def _rate_return(self, return_pct: float) -> Text:
        """Rate total return with color and emoji."""
        if return_pct >= 50:
            return Text("🔥 Exceptional", style="bright_green")
        if return_pct >= 20:
            return Text("📈 Strong", style="green")
        if return_pct >= 10:
            return Text("✅ Good", style="yellow")
        if return_pct >= 0:
            return Text("⚖️ Positive", style="yellow")
        return Text("📉 Negative", style="red")

    def _rate_annual_return(self, return_pct: float) -> Text:
        """Rate annualized return with color and emoji."""
        if return_pct >= 20:
            return Text("🔥 Excellent", style="bright_green")
        if return_pct >= 15:
            return Text("📈 Very Good", style="green")
        if return_pct >= 10:
            return Text("✅ Good", style="yellow")
        if return_pct >= 5:
            return Text("⚖️ Fair", style="yellow")
        return Text("📉 Poor", style="red")

    def _rate_calmar_ratio(self, calmar: float) -> Text:
        """Rate Calmar ratio with color and emoji."""
        if calmar >= 3:
            return Text("🔥 Excellent", style="bright_green")
        if calmar >= 2:
            return Text("📈 Very Good", style="green")
        if calmar >= 1:
            return Text("✅ Good", style="yellow")
        if calmar >= 0.5:
            return Text("⚖️ Fair", style="yellow")
        return Text("📉 Poor", style="red")

    def _rate_information_ratio(self, info_ratio: float) -> Text:
        """Rate Information ratio with color and emoji."""
        if info_ratio >= 1.0:
            return Text("🔥 Excellent", style="bright_green")
        if info_ratio >= 0.75:
            return Text("📈 Very Good", style="green")
        if info_ratio >= 0.5:
            return Text("✅ Good", style="yellow")
        if info_ratio >= 0.25:
            return Text("⚖️ Fair", style="yellow")
        return Text("📉 Poor", style="red")

    def _format_trend_direction(self, direction: str) -> Text:
        """Format trend direction with appropriate emoji and color."""
        if direction == "Upward":
            return Text("🎯 Bullish", style="green")
        if direction == "Downward":
            return Text("🎯 Bearish", style="red")
        return Text("🎯 Neutral", style="yellow")

    def _format_trend_strength(self, strength: str) -> Text:
        """Format trend strength with emoji and color."""
        if strength in ["Very Strong", "Strong"]:
            return Text("🔥 Strong", style="green")
        if strength == "Moderate":
            return Text("⚖️ Moderate", style="yellow")
        return Text("📊 Weak", style="yellow")

    def _rate_r_squared(self, r_squared: float) -> Text:
        """Rate R-squared with color and emoji."""
        if r_squared >= 0.8:
            return Text("✅ Excellent Fit", style="bright_green")
        if r_squared >= 0.6:
            return Text("📈 Good Fit", style="green")
        if r_squared >= 0.4:
            return Text("⚖️ Moderate Fit", style="yellow")
        if r_squared >= 0.2:
            return Text("📊 Weak Fit", style="yellow")
        return Text("📉 Poor Fit", style="red")

    def _rate_smoothness(self, smoothness: float) -> Text:
        """Rate smoothness factor with color and emoji."""
        if smoothness >= 0.9:
            return Text("🌊 Very Smooth", style="green")
        if smoothness >= 0.8:
            return Text("📈 Smooth", style="yellow")
        if smoothness >= 0.7:
            return Text("⚖️ Moderate", style="yellow")
        return Text("📊 Volatile", style="red")

    def _format_slope_indicator(self, slope: float) -> Text:
        """Format slope indicator with appropriate emoji."""
        if slope > 0.001:
            return Text("📈 Rising", style="green")
        if slope < -0.001:
            return Text("📉 Falling", style="red")
        return Text("➡️ Flat", style="yellow")

    # Period Analysis Display Methods
    def display_period_analysis(self, period_metrics: dict[str, Any]) -> None:
        """Display complete period analysis with all sections."""
        asset_info = period_metrics.get("asset_info", {})
        self._display_rolling_performance_table(
            period_metrics["rolling_performance"], asset_info,
        )
        self._display_seasonality_patterns_table(period_metrics["seasonality_patterns"])
        self._display_period_comparison_summary(
            period_metrics["period_comparison"], asset_info,
        )
        self._display_calendar_patterns_table(period_metrics["calendar_analysis"])

    def _display_rolling_performance_table(
        self,
        rolling_performance: dict[str, dict[str, float]],
        asset_info: dict[str, Any] | None = None,
    ) -> None:
        """Display rolling performance metrics table."""
        # Add asset type note to title if available
        title = "📅 Rolling Performance Analysis"
        if asset_info and asset_info.get("period_labels", {}).get("note"):
            title += f" - {asset_info['period_labels']['note']}"

        table = Table(
            title=title,
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="blue",
        )
        table.add_column("Period", style="white", no_wrap=True)
        table.add_column("Avg Return", style="yellow", justify="right")
        table.add_column("Sharpe Ratio", style="green", justify="right")
        table.add_column("Volatility", style="yellow", justify="right")
        table.add_column("Max DD", style="red", justify="right")
        table.add_column("Win Rate", style="cyan", justify="right")

        # Weekly performance
        if "weekly" in rolling_performance:
            weekly = rolling_performance["weekly"]
            table.add_row(
                (
                    asset_info.get("period_labels", {}).get("weekly", "🗓️ Weekly (5d)")
                    if asset_info
                    else "🗓️ Weekly (5d)"
                ),
                f"{weekly['avg_return']:+.2f}%",
                f"{weekly['avg_sharpe']:.2f}",
                f"{weekly['avg_volatility']:.1f}%",
                f"{weekly['avg_max_drawdown']:.1f}%",
                f"{weekly['win_rate']:.0f}%",
            )

        # Monthly performance
        if "monthly" in rolling_performance:
            monthly = rolling_performance["monthly"]
            table.add_row(
                (
                    asset_info.get("period_labels", {}).get(
                        "monthly", "📅 Monthly (21d)",
                    )
                    if asset_info
                    else "📅 Monthly (21d)"
                ),
                f"{monthly['avg_return']:+.2f}%",
                f"{monthly['avg_sharpe']:.2f}",
                f"{monthly['avg_volatility']:.1f}%",
                f"{monthly['avg_max_drawdown']:.1f}%",
                f"{monthly['win_rate']:.0f}%",
            )

        self.console.print(table)
        self.console.print()  # Add spacing

    def _display_seasonality_patterns_table(self, seasonality: dict[str, Any]) -> None:
        """Display seasonality patterns table."""
        patterns = seasonality.get("patterns", {})

        table = Table(
            title="🗓️ Seasonal Patterns (Moving Average Performance)",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="green",
        )
        table.add_column("Pattern", style="white", no_wrap=True)
        table.add_column("Period", style="cyan", no_wrap=True)
        table.add_column("Avg Return", style="yellow", justify="right")
        table.add_column("Win Rate", style="green", justify="right")
        table.add_column("Strength", style="blue", justify="center")
        table.add_column("P-Value", style="dim", justify="right")

        # Display strongest patterns first
        all_patterns = []

        # Add weekly patterns
        for pattern in patterns.get("weekly", []):
            all_patterns.append(("Weekly", pattern))

        # Add monthly patterns
        for pattern in patterns.get("monthly", []):
            all_patterns.append(("Monthly", pattern))

        # Add quarterly patterns
        for pattern in patterns.get("quarterly", []):
            all_patterns.append(("Quarterly", pattern))

        # Sort by significance/strength
        all_patterns.sort(key=lambda x: x[1].get("significance", 0), reverse=True)

        # Display top patterns (limit to avoid clutter)
        display_count = 0
        for pattern_type, pattern in all_patterns:
            if display_count >= 8:  # Limit display
                break

            # Color code return based on performance
            return_val = pattern["avg_return"]
            if return_val > 0:
                return_display = f"[green]+{return_val:.2f}%[/green]"
                emoji = "🟢"
            else:
                return_display = f"[red]{return_val:.2f}%[/red]"
                emoji = "🔴"

            # Format strength
            significance = pattern.get("significance", 0)
            if significance >= 0.8:
                strength = Text("Strong", style="green")
            elif significance >= 0.6:
                strength = Text("Moderate", style="yellow")
            else:
                strength = Text("Weak", style="yellow")

            # Format p-value
            p_value = pattern.get("p_value")
            p_val_display = f"{p_value:.3f}" if p_value is not None else "N/A"

            table.add_row(
                f"{emoji} {pattern_type}",
                pattern["period"],
                return_display,
                f"{pattern['win_rate']:.0f}%",
                strength,
                p_val_display,
            )
            display_count += 1

        if display_count == 0:
            table.add_row(
                "No significant patterns found", "N/A", "N/A", "N/A", "N/A", "N/A",
            )

        self.console.print(table)
        self.console.print()  # Add spacing

    def _display_period_comparison_summary(
        self, comparison: dict[str, Any], asset_info: dict[str, Any] | None = None,
    ) -> None:
        """Display period comparison summary panel."""
        # Get dynamic labels
        period_labels = asset_info.get("period_labels", {}) if asset_info else {}
        weekly_label = period_labels.get("weekly", "Weekly")
        monthly_label = period_labels.get("monthly", "Monthly")

        weekly_vs_monthly = comparison.get("weekly_vs_monthly", {})
        best_worst = comparison.get("best_worst", {})

        if not weekly_vs_monthly:
            return

        # Create comparison summary
        weekly_avg = weekly_vs_monthly.get("weekly_avg", 0)
        monthly_avg = weekly_vs_monthly.get("monthly_avg", 0)
        weekly_sharpe = weekly_vs_monthly.get("weekly_sharpe", 0)
        monthly_sharpe = weekly_vs_monthly.get("monthly_sharpe", 0)
        correlation = weekly_vs_monthly.get("correlation", 0)

        # Determine better performing period
        if weekly_sharpe > monthly_sharpe:
            better_period = weekly_label
            better_color = "green"
        elif monthly_sharpe > weekly_sharpe:
            better_period = monthly_label
            better_color = "blue"
        else:
            better_period = "Equal"
            better_color = "yellow"

        summary_text = (
            f"[bold cyan]Performance Comparison:[/bold cyan] "
            f"[{better_color}]{better_period} outperforms[/{better_color}] "
            f"(Sharpe: {weekly_label} {weekly_sharpe:.2f} vs {monthly_label} {monthly_sharpe:.2f})\n"
            f"[bold cyan]Returns:[/bold cyan] {weekly_label} {weekly_avg:+.2f}% vs {monthly_label} {monthly_avg:+.2f}% | "
            f"[bold cyan]Correlation:[/bold cyan] {correlation:.2f}\n"
        )

        # Add best/worst periods info
        if "weekly" in best_worst:
            weekly_info = best_worst["weekly"]
            summary_text += (
                f"[bold cyan]Best Week:[/bold cyan] {weekly_info.get('best_week', 'N/A')} "
                f"({weekly_info.get('best_return', 0):+.2f}%) | "
                f"[bold cyan]Worst Week:[/bold cyan] {weekly_info.get('worst_week', 'N/A')} "
                f"({weekly_info.get('worst_return', 0):+.2f}%)\n"
            )

        if "monthly" in best_worst:
            monthly_info = best_worst["monthly"]
            summary_text += (
                f"[bold cyan]Best Month:[/bold cyan] {monthly_info.get('best_month', 'N/A')} "
                f"({monthly_info.get('best_return', 0):+.2f}%) | "
                f"[bold cyan]Worst Month:[/bold cyan] {monthly_info.get('worst_month', 'N/A')} "
                f"({monthly_info.get('worst_return', 0):+.2f}%)"
            )

        panel = Panel(
            summary_text.strip(),
            title="⏰ Period Performance Summary",
            border_style="yellow",
            box=ROUNDED,
        )
        self.console.print(panel)
        self.console.print()  # Add spacing

    def _display_calendar_patterns_table(
        self, calendar_analysis: dict[str, Any],
    ) -> None:
        """Display calendar patterns (day of week, month of year effects)."""
        table = Table(
            title="📅 Calendar Effects Analysis",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="purple",
        )
        table.add_column("Type", style="white", no_wrap=True)
        table.add_column("Period", style="cyan", no_wrap=True)
        table.add_column("Avg Return", style="yellow", justify="right")
        table.add_column("Volatility", style="yellow", justify="right")
        table.add_column("Sample Size", style="dim", justify="right")

        # Day of week effects
        dow_data = calendar_analysis.get("day_of_week", [])
        for day_info in dow_data:
            return_val = day_info["avg_return"]
            if return_val > 0:
                return_display = f"[green]+{return_val:.3f}%[/green]"
            else:
                return_display = f"[red]{return_val:.3f}%[/red]"

            table.add_row(
                "📅 Day of Week",
                day_info["day"],
                return_display,
                f"{day_info['volatility']:.2f}%",
                str(day_info["sample_size"]),
            )

        # Month of year effects
        moy_data = calendar_analysis.get("month_of_year", [])
        for month_info in moy_data:
            return_val = month_info["avg_return"]
            if return_val > 0:
                return_display = f"[green]+{return_val:.3f}%[/green]"
            else:
                return_display = f"[red]{return_val:.3f}%[/red]"

            table.add_row(
                "🗓️ Month of Year",
                month_info["month"],
                return_display,
                f"{month_info['volatility']:.2f}%",
                str(month_info["sample_size"]),
            )

        if not dow_data and not moy_data:
            table.add_row("No calendar effects found", "N/A", "N/A", "N/A", "N/A")

        self.console.print(table)
        self.console.print()  # Add spacing


def display_ma_analysis(metrics: dict[str, Any], console: Console = None) -> None:
    """
    Convenience function to display complete MA analysis.

    Args:
        metrics: Dictionary containing all calculated metrics
        console: Optional Rich console instance
    """
    formatter = MADisplayFormatter(console)
    formatter.display_complete_analysis(metrics)


def display_ma_period_analysis(
    period_metrics: dict[str, Any], console: Console = None,
) -> None:
    """
    Convenience function to display period-specific MA analysis.

    Args:
        period_metrics: Dictionary containing all calculated period metrics
        console: Optional Rich console instance
    """
    formatter = MADisplayFormatter(console)
    formatter.display_period_analysis(period_metrics)


class SweepAnalyticsDisplayer:
    """Rich CLI display for sweep analytics results."""

    def __init__(self, console: Console = None):
        """Initialize displayer with console."""
        self.console = console or Console()

    def display_complete_sweep_analysis(self, analytics_engine) -> None:
        """Display complete sweep analysis with all sections."""
        from app.tools.sweep_analytics import SweepAnalyticsEngine

        if not isinstance(analytics_engine, SweepAnalyticsEngine):
            self.console.print("[red]Error: Invalid analytics engine[/red]")
            return

        if not analytics_engine.performance_data:
            self.console.print(
                "[yellow]No performance data available for analysis[/yellow]",
            )
            return

        # Display all sections
        self._display_executive_summary(analytics_engine)
        self._display_performance_leaderboard(analytics_engine)
        self._display_risk_analysis(analytics_engine)
        self._display_optimization_recommendations(analytics_engine)
        self._display_statistical_distribution(analytics_engine)

    def _display_executive_summary(self, engine) -> None:
        """Display executive summary dashboard."""
        # Get top performers by different metrics
        top_sharpe = (
            engine.get_top_performers("sharpe_ratio", 1)[0]
            if engine.performance_data
            else None
        )
        top_return = (
            engine.get_top_performers("total_return", 1)[0]
            if engine.performance_data
            else None
        )
        top_calmar = (
            engine.get_top_performers("calmar_ratio", 1)[0]
            if engine.performance_data
            else None
        )
        best_risk_adjusted = (
            engine.get_top_performers("risk_adjusted_score", 1)[0]
            if engine.performance_data
            else None
        )

        if not top_sharpe:
            return

        # Get key statistics
        sharpe_stats = engine.statistics.get("sharpe_ratio")
        return_stats = engine.statistics.get("total_return")
        dd_stats = engine.statistics.get("max_drawdown")

        summary_text = f"""[bold yellow]🏆 TOP PERFORMERS[/bold yellow]
[cyan]Best Risk-Adjusted:[/cyan] Period {best_risk_adjusted.period} (Score: {best_risk_adjusted.risk_adjusted_score:.2f})
[cyan]Highest Sharpe:[/cyan] Period {top_sharpe.period} (Sharpe: {top_sharpe.sharpe_ratio:.2f})
[cyan]Highest Return:[/cyan] Period {top_return.period} (Return: {top_return.total_return:+.1f}%)
[cyan]Best Calmar:[/cyan] Period {top_calmar.period} (Calmar: {top_calmar.calmar_ratio:.2f})

[bold yellow]📊 PERFORMANCE RANGES[/bold yellow]
[cyan]Sharpe Ratio:[/cyan] {sharpe_stats.min_value:.2f} to {sharpe_stats.max_value:.2f} (Median: {sharpe_stats.median_value:.2f})
[cyan]Total Return:[/cyan] {return_stats.min_value:+.1f}% to {return_stats.max_value:+.1f}% (Median: {return_stats.median_value:+.1f}%)
[cyan]Max Drawdown:[/cyan] {dd_stats.min_value:.1f}% to {dd_stats.max_value:.1f}% (Median: {dd_stats.median_value:.1f}%)

[bold yellow]🎯 ANALYSIS SUMMARY[/bold yellow]
[cyan]Total Periods Analyzed:[/cyan] {len(engine.performance_data)}
[cyan]Data Quality:[/cyan] {len([d for d in engine.performance_data if d.data_points > 1000]):,} periods with >1000 data points"""

        panel = Panel(
            summary_text,
            title="🚀 MA Sweep Analysis Executive Summary",
            border_style="green",
            box=ROUNDED,
        )
        self.console.print(panel)
        self.console.print()

    def _display_performance_leaderboard(self, engine) -> None:
        """Display performance leaderboard table."""
        ranked_data = engine.get_ranked_performance()

        table = Table(
            title="🏆 Performance Leaderboard (Ranked by Risk-Adjusted Score)",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="gold1",
        )
        table.add_column("Rank", style="yellow", justify="center", width=4)
        table.add_column("Period", style="cyan", justify="center", width=6)
        table.add_column("Score", style="green", justify="right", width=6)
        table.add_column("Sharpe", style="blue", justify="right", width=6)
        table.add_column("Return", style="magenta", justify="right", width=8)
        table.add_column("Max DD", style="red", justify="right", width=7)
        table.add_column("Volatility", style="yellow", justify="right", width=9)
        table.add_column("Trend", style="white", justify="center", width=8)

        # Show top 15 performers
        for i, data in enumerate(ranked_data[:15], 1):
            # Color coding based on rank
            if i <= 3:
                rank_style = "bold gold1"
                medal = ["🥇", "🥈", "🥉"][i - 1]
                rank_display = f"{medal} {i}"
            elif i <= 5:
                rank_style = "green"
                rank_display = f"⭐ {i}"
            else:
                rank_style = "white"
                rank_display = str(i)

            # Color code performance metrics
            score_color = (
                "green"
                if data.risk_adjusted_score > 1.5
                else "yellow"
                if data.risk_adjusted_score > 1.0
                else "white"
            )
            sharpe_color = (
                "green"
                if data.sharpe_ratio > 1.5
                else "yellow"
                if data.sharpe_ratio > 1.0
                else "white"
            )
            return_color = (
                "green"
                if data.total_return > 100
                else "yellow"
                if data.total_return > 50
                else "white"
            )
            dd_color = (
                "green"
                if data.max_drawdown < 20
                else "yellow"
                if data.max_drawdown < 40
                else "red"
            )

            # Trend direction emoji
            trend_emoji = (
                "📈"
                if data.trend_direction == "Upward"
                else "📉"
                if data.trend_direction == "Downward"
                else "➡️"
            )

            table.add_row(
                f"[{rank_style}]{rank_display}[/{rank_style}]",
                str(data.period),
                f"[{score_color}]{data.risk_adjusted_score:.2f}[/{score_color}]",
                f"[{sharpe_color}]{data.sharpe_ratio:.2f}[/{sharpe_color}]",
                f"[{return_color}]{data.total_return:+.1f}%[/{return_color}]",
                f"[{dd_color}]{data.max_drawdown:.1f}%[/{dd_color}]",
                f"{data.volatility:.1f}%",
                f"{trend_emoji} {data.trend_strength[:3]}",
            )

        self.console.print(table)
        self.console.print()

    def _display_risk_analysis(self, engine) -> None:
        """Display risk analysis section."""
        risk_categories = engine.get_risk_categories()
        outliers = engine.get_outlier_analysis()

        # Risk categories table
        table = Table(
            title="⚠️ Risk Analysis by Volatility Categories",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="red",
        )
        table.add_column("Risk Level", style="white", no_wrap=True)
        table.add_column("Period Count", style="cyan", justify="center")
        table.add_column("Avg Sharpe", style="green", justify="right")
        table.add_column("Avg Return", style="yellow", justify="right")
        table.add_column("Avg Max DD", style="red", justify="right")
        table.add_column("Best Period", style="blue", justify="center")

        for risk_level, data_list in risk_categories.items():
            if not data_list:
                continue

            avg_sharpe = sum(d.sharpe_ratio for d in data_list) / len(data_list)
            avg_return = sum(d.total_return for d in data_list) / len(data_list)
            avg_dd = sum(d.max_drawdown for d in data_list) / len(data_list)
            best_period = max(data_list, key=lambda x: x.risk_adjusted_score)

            # Risk level styling
            if risk_level == "low":
                level_display = "🟢 Low Risk"
                level_color = "green"
            elif risk_level == "medium":
                level_display = "🟡 Medium Risk"
                level_color = "yellow"
            else:
                level_display = "🔴 High Risk"
                level_color = "red"

            table.add_row(
                f"[{level_color}]{level_display}[/{level_color}]",
                str(len(data_list)),
                f"{avg_sharpe:.2f}",
                f"{avg_return:+.1f}%",
                f"{avg_dd:.1f}%",
                str(best_period.period),
            )

        self.console.print(table)

        # Outliers summary
        if outliers["exceptional"] or outliers["underperforming"]:
            self.console.print()
            outlier_text = "[bold yellow]🎯 OUTLIER ANALYSIS[/bold yellow]\n"

            if outliers["exceptional"]:
                periods = [str(d.period) for d in outliers["exceptional"]]
                outlier_text += f"[green]⭐ Exceptional Performers:[/green] Periods {', '.join(periods)}\n"

            if outliers["underperforming"]:
                periods = [str(d.period) for d in outliers["underperforming"]]
                outlier_text += (
                    f"[red]⚠️ Underperformers:[/red] Periods {', '.join(periods)}"
                )

            panel = Panel(
                outlier_text.strip(),
                title="📊 Statistical Outliers",
                border_style="yellow",
                box=ROUNDED,
            )
            self.console.print(panel)

        self.console.print()

    def _display_optimization_recommendations(self, engine) -> None:
        """Display optimization recommendations."""
        recommendations = engine.get_optimization_recommendations()

        if not recommendations:
            return

        table = Table(
            title="🎯 Strategy Optimization Recommendations",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="blue",
        )
        table.add_column("Strategy Type", style="white", no_wrap=True)
        table.add_column("Recommended Period", style="cyan", justify="center")
        table.add_column("Sharpe Ratio", style="green", justify="right")
        table.add_column("Total Return", style="yellow", justify="right")
        table.add_column("Max Drawdown", style="red", justify="right")
        table.add_column("Rationale", style="blue", no_wrap=False)

        strategy_map = {
            "balanced": ("🎯 Balanced", "Highest risk-adjusted score"),
            "aggressive": ("🚀 Aggressive", "Highest return (high volatility)"),
            "conservative": ("🛡️ Conservative", "Best Sharpe with low drawdown"),
            "consistent": ("📊 Consistent", "Stable performance over time"),
        }

        for strategy_key, data in recommendations.items():
            if strategy_key in strategy_map:
                strategy_name, rationale = strategy_map[strategy_key]

                # Color code the metrics
                sharpe_color = "green" if data.sharpe_ratio > 1.5 else "yellow"
                return_color = "green" if data.total_return > 100 else "yellow"
                dd_color = (
                    "green"
                    if data.max_drawdown < 20
                    else "yellow"
                    if data.max_drawdown < 40
                    else "red"
                )

                table.add_row(
                    strategy_name,
                    str(data.period),
                    f"[{sharpe_color}]{data.sharpe_ratio:.2f}[/{sharpe_color}]",
                    f"[{return_color}]{data.total_return:+.1f}%[/{return_color}]",
                    f"[{dd_color}]{data.max_drawdown:.1f}%[/{dd_color}]",
                    rationale,
                )

        self.console.print(table)
        self.console.print()

    def _display_statistical_distribution(self, engine) -> None:
        """Display statistical distribution summary."""
        key_metrics = [
            "sharpe_ratio",
            "total_return",
            "max_drawdown",
            "volatility",
            "risk_adjusted_score",
        ]

        table = Table(
            title="📈 Statistical Distribution Summary",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            border_style="purple",
        )
        table.add_column("Metric", style="white", no_wrap=True)
        table.add_column("Min", style="red", justify="right")
        table.add_column("Q1", style="yellow", justify="right")
        table.add_column("Median", style="cyan", justify="right")
        table.add_column("Q3", style="yellow", justify="right")
        table.add_column("Max", style="green", justify="right")
        table.add_column("Std Dev", style="blue", justify="right")
        table.add_column("Best Period", style="green", justify="center")

        for metric_key in key_metrics:
            stats = engine.statistics.get(metric_key)
            if not stats:
                continue

            # Format values based on metric type
            if "return" in metric_key.lower():
                min_val = f"{stats.min_value:+.1f}%"
                q1_val = f"{stats.q1:+.1f}%"
                med_val = f"{stats.median_value:+.1f}%"
                q3_val = f"{stats.q3:+.1f}%"
                max_val = f"{stats.max_value:+.1f}%"
                std_val = f"{stats.std_dev:.1f}%"
            elif "drawdown" in metric_key.lower() or "volatility" in metric_key.lower():
                min_val = f"{stats.min_value:.1f}%"
                q1_val = f"{stats.q1:.1f}%"
                med_val = f"{stats.median_value:.1f}%"
                q3_val = f"{stats.q3:.1f}%"
                max_val = f"{stats.max_value:.1f}%"
                std_val = f"{stats.std_dev:.1f}%"
            else:
                min_val = f"{stats.min_value:.2f}"
                q1_val = f"{stats.q1:.2f}"
                med_val = f"{stats.median_value:.2f}"
                q3_val = f"{stats.q3:.2f}"
                max_val = f"{stats.max_value:.2f}"
                std_val = f"{stats.std_dev:.2f}"

            table.add_row(
                stats.metric_name,
                min_val,
                q1_val,
                med_val,
                q3_val,
                max_val,
                std_val,
                str(stats.best_period),
            )

        self.console.print(table)
        self.console.print()


def display_sweep_analysis(analytics_engine, console: Console = None) -> None:
    """
    Convenience function to display complete sweep analysis.

    Args:
        analytics_engine: SweepAnalyticsEngine instance with loaded data
        console: Optional Rich console instance
    """
    displayer = SweepAnalyticsDisplayer(console)
    displayer.display_complete_sweep_analysis(analytics_engine)
