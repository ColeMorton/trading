"""Service layer for seasonality analysis."""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.table import Table

from app.cli.models.seasonality import (
    SeasonalityConfig,
    SeasonalityPattern,
    SeasonalityResult,
)
from app.tools.seasonality_analyzer import SeasonalityAnalyzer


class SeasonalityService:
    """Service for analyzing and storing seasonality patterns."""

    def __init__(self, config: SeasonalityConfig):
        """Initialize the service.

        Args:
            config: Seasonality configuration
        """
        self.config = config
        self.analyzer = SeasonalityAnalyzer(
            confidence_level=config.confidence_level,
            min_sample_size=config.min_sample_size,
        )
        self.console = Console()
        self.prices_dir = Path("data/raw/prices")
        self.output_dir = Path("data/raw/seasonality")

    def run_analysis(self) -> dict[str, SeasonalityResult]:
        """Run seasonality analysis for configured tickers.

        Returns:
            Dictionary mapping ticker to analysis results
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Get list of tickers to analyze
        tickers = self._get_tickers_to_analyze()

        if not tickers:
            self.console.print("[yellow]No tickers found to analyze[/yellow]")
            return {}

        results = {}

        # Process each ticker with progress bar
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Analyzing seasonality patterns...",
                total=len(tickers),
            )

            for ticker in tickers:
                progress.update(task, description=f"[cyan]Analyzing {ticker}...")

                try:
                    result = self._analyze_ticker(ticker)
                    if result:
                        results[ticker] = result
                        self._save_result(result)
                except Exception as e:
                    self.console.print(f"[red]Error analyzing {ticker}: {e!s}[/red]")

                progress.advance(task)

        # Display comprehensive visualizations for each ticker
        for ticker, result in results.items():
            self._display_statistical_summary(result)
            self._display_monthly_calendar(result)
            self._display_weekly_heatmap(result)
            self._display_week_of_year_highlights(result)
            self._display_week_of_year_calendar(result)

        # Display summary
        self._display_summary(results)

        # Export summary to file
        self._export_summary(results)

        return results

    def _get_tickers_to_analyze(self) -> list[str]:
        """Get list of tickers to analyze."""
        if self.config.tickers:
            # Use specified tickers
            return self.config.tickers
        # Get all available tickers from price data directory
        tickers = []
        for file_path in self.prices_dir.glob("*_D.csv"):
            ticker = file_path.stem.replace("_D", "")
            tickers.append(ticker)
        return sorted(tickers)

    def _analyze_ticker(
        self,
        ticker: str,
        _retry: bool = False,
    ) -> SeasonalityResult | None:
        """Analyze seasonality for a single ticker.

        Args:
            ticker: Ticker symbol
            _retry: Internal flag to track retry attempts (default False)

        Returns:
            Seasonality results or None if insufficient data
        """
        # Load price data
        price_file = self.prices_dir / f"{ticker}_D.csv"

        # Check if file exists and has sufficient data
        should_download = False

        if not price_file.exists():
            self.console.print(f"[yellow]Price data not found for {ticker}[/yellow]")
            should_download = True
        else:
            # Read data
            data = pd.read_csv(price_file, parse_dates=["Date"], index_col="Date")

            # Check if we have enough data
            years_of_data = (data.index[-1] - data.index[0]).days / 365.25
            if years_of_data < self.config.min_years:
                self.console.print(
                    f"[yellow]Insufficient data for {ticker}: "
                    f"{years_of_data:.1f} years < {self.config.min_years} years required[/yellow]",
                )
                should_download = True

        # Download data if needed and not already retried
        if should_download and not _retry:
            self.console.print(
                f"[cyan]Downloading full price history for {ticker}...[/cyan]",
            )
            try:
                # Use existing download_data utility
                from app.tools.data_types import DataConfig
                from app.tools.download_data import download_data

                config = DataConfig(
                    BASE_DIR=".",
                    TICKER=ticker,
                    USE_HOURLY=False,
                    PERIOD="max",
                )

                # Download and save via existing utility
                df = download_data(
                    ticker,
                    config,
                    lambda msg, level="info": self.console.print(f"[dim]{msg}[/dim]"),
                )

                if df is not None and not df.is_empty():
                    self.console.print(
                        f"[green]✓ Successfully downloaded data for {ticker}[/green]",
                    )
                    # Retry analysis with newly downloaded data
                    return self._analyze_ticker(ticker, _retry=True)
                self.console.print(f"[red]No data available for {ticker}[/red]")
                return None

            except Exception as e:
                self.console.print(
                    f"[red]Failed to download data for {ticker}: {e!s}[/red]",
                )
                return None

        # If we've already retried or download wasn't needed, check if we can proceed
        if not price_file.exists():
            return None

        # Read data (again if needed after download)
        data = pd.read_csv(price_file, parse_dates=["Date"], index_col="Date")

        # Final check for sufficient data
        years_of_data = (data.index[-1] - data.index[0]).days / 365.25
        if years_of_data < self.config.min_years:
            self.console.print(
                f"[yellow]Still insufficient data after download: "
                f"{years_of_data:.1f} years < {self.config.min_years} years required[/yellow]",
            )
            return None

        # Analyze patterns
        patterns = self.analyzer.analyze_all_patterns(
            data,
            detrend=self.config.detrend_data,
        )

        # Calculate overall seasonal strength
        seasonal_strength = self.analyzer.calculate_seasonal_strength(patterns)

        # Find best pattern (highest expectancy for trading)
        # Expectancy = average_return * win_rate (profitability, not just significance)
        strongest_pattern = None
        if patterns:
            strongest_pattern = max(
                patterns,
                key=lambda p: p.average_return * p.win_rate,
            )

        # Create result
        return SeasonalityResult(
            ticker=ticker,
            data_start_date=data.index[0],
            data_end_date=data.index[-1],
            total_periods=len(data),
            patterns=patterns,
            overall_seasonal_strength=seasonal_strength,
            strongest_pattern=strongest_pattern,
            metadata={
                "years_of_data": years_of_data,
                "detrended": self.config.detrend_data,
                "confidence_level": self.config.confidence_level,
            },
        )

    def _save_result(self, result: SeasonalityResult) -> None:
        """Save analysis result to file.

        Args:
            result: Seasonality analysis result
        """
        # Always save comprehensive JSON export
        self._export_json(result)

        # Also save CSV for backward compatibility
        if self.config.output_format in ("csv", "both"):
            self._export_csv(result)

    def _export_json(self, result: SeasonalityResult) -> None:
        """Export comprehensive JSON file with all analysis data.

        Args:
            result: Seasonality analysis result
        """
        output_file = self.output_dir / f"{result.ticker}_seasonality.json"

        # Group patterns by type
        monthly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Monthly"
        ]
        weekly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Weekly"
        ]
        quarterly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Quarterly"
        ]
        week_of_year_patterns = [
            p for p in result.patterns if p.pattern_type.value == "WeekOfYear"
        ]
        day_of_month_patterns = [
            p for p in result.patterns if p.pattern_type.value == "DayOfMonth"
        ]

        # Helper function to convert pattern to dict
        def pattern_to_dict(pattern: SeasonalityPattern) -> dict:
            return {
                "period": pattern.period,
                "period_number": pattern.period_number,
                "avg_return_pct": round(pattern.average_return, 4),
                "std_dev_pct": round(pattern.std_dev, 4),
                "win_rate": round(pattern.win_rate, 4),
                "sample_size": pattern.sample_size,
                "sharpe_ratio": (
                    round(pattern.sharpe_ratio, 4) if pattern.sharpe_ratio else None
                ),
                "sortino_ratio": (
                    round(pattern.sortino_ratio, 4) if pattern.sortino_ratio else None
                ),
                "max_drawdown_pct": (
                    round(pattern.max_drawdown, 4) if pattern.max_drawdown else None
                ),
                "statistical_significance": round(pattern.statistical_significance, 4),
                "p_value": round(pattern.p_value, 4) if pattern.p_value else None,
                "confidence_interval": {
                    "lower": (
                        round(pattern.confidence_interval_lower, 4)
                        if pattern.confidence_interval_lower
                        else None
                    ),
                    "upper": (
                        round(pattern.confidence_interval_upper, 4)
                        if pattern.confidence_interval_upper
                        else None
                    ),
                },
                "consistency_score": (
                    round(pattern.consistency_score, 4)
                    if pattern.consistency_score
                    else None
                ),
                "skewness": round(pattern.skewness, 4) if pattern.skewness else None,
                "kurtosis": round(pattern.kurtosis, 4) if pattern.kurtosis else None,
            }

        # Find best/worst patterns
        best_month = (
            max(monthly_patterns, key=lambda p: p.average_return)
            if monthly_patterns
            else None
        )
        worst_month = (
            min(monthly_patterns, key=lambda p: p.average_return)
            if monthly_patterns
            else None
        )
        best_day = (
            max(weekly_patterns, key=lambda p: p.average_return)
            if weekly_patterns
            else None
        )
        worst_day = (
            min(weekly_patterns, key=lambda p: p.average_return)
            if weekly_patterns
            else None
        )

        # Build comprehensive JSON structure
        data = {
            "meta": {
                "ticker": result.ticker,
                "analysis_date": result.analysis_date.isoformat(),
                "data_period": {
                    "start": result.data_start_date.isoformat(),
                    "end": result.data_end_date.isoformat(),
                    "years": round(result.metadata.get("years_of_data", 0), 2),
                    "trading_days": result.total_periods,
                },
                "configuration": {
                    "confidence_level": self.config.confidence_level,
                    "detrended": self.config.detrend_data,
                    "min_sample_size": self.config.min_sample_size,
                },
            },
            "summary_statistics": {
                "seasonal_strength": round(result.overall_seasonal_strength, 4),
                "overall_consistency": (
                    round(
                        sum(p.consistency_score or 0 for p in monthly_patterns)
                        / len(monthly_patterns),
                        4,
                    )
                    if monthly_patterns
                    else None
                ),
                "best_month": (
                    {
                        "period": best_month.period,
                        "avg_return": round(best_month.average_return, 4),
                        "win_rate": round(best_month.win_rate, 4),
                        "sharpe_ratio": (
                            round(best_month.sharpe_ratio, 4)
                            if best_month.sharpe_ratio
                            else None
                        ),
                    }
                    if best_month
                    else None
                ),
                "worst_month": (
                    {
                        "period": worst_month.period,
                        "avg_return": round(worst_month.average_return, 4),
                        "win_rate": round(worst_month.win_rate, 4),
                        "sharpe_ratio": (
                            round(worst_month.sharpe_ratio, 4)
                            if worst_month.sharpe_ratio
                            else None
                        ),
                    }
                    if worst_month
                    else None
                ),
                "best_day": (
                    {
                        "period": best_day.period,
                        "avg_return": round(best_day.average_return, 4),
                        "win_rate": round(best_day.win_rate, 4),
                    }
                    if best_day
                    else None
                ),
                "worst_day": (
                    {
                        "period": worst_day.period,
                        "avg_return": round(worst_day.average_return, 4),
                        "win_rate": round(worst_day.win_rate, 4),
                    }
                    if worst_day
                    else None
                ),
            },
            "monthly_patterns": [pattern_to_dict(p) for p in monthly_patterns],
            "weekly_patterns": [pattern_to_dict(p) for p in weekly_patterns],
            "quarterly_patterns": [pattern_to_dict(p) for p in quarterly_patterns],
            "week_of_year_patterns": [
                pattern_to_dict(p)
                for p in sorted(
                    week_of_year_patterns,
                    key=lambda p: p.period_number or 0,
                )
            ],
            "day_of_month_patterns": [
                pattern_to_dict(p) for p in day_of_month_patterns
            ],
        }

        # Write JSON file
        with open(output_file, "w") as f:
            json.dump(data, f, indent=2)

        self.console.print(f"[dim]✓ JSON exported to {output_file}[/dim]")

    def _export_csv(self, result: SeasonalityResult) -> None:
        """Export CSV file with pattern data.

        Args:
            result: Seasonality analysis result
        """
        output_file = self.output_dir / f"{result.ticker}_seasonality.csv"

        # Convert patterns to DataFrame with all fields
        rows = []
        for pattern in result.patterns:
            rows.append(
                {
                    "Pattern_Type": pattern.pattern_type.value,
                    "Period": pattern.period,
                    "Period_Number": pattern.period_number,
                    "Average_Return": pattern.average_return,
                    "Std_Dev": pattern.std_dev,
                    "Win_Rate": pattern.win_rate,
                    "Sample_Size": pattern.sample_size,
                    "Sharpe_Ratio": pattern.sharpe_ratio,
                    "Sortino_Ratio": pattern.sortino_ratio,
                    "Max_Drawdown": pattern.max_drawdown,
                    "Consistency_Score": pattern.consistency_score,
                    "Statistical_Significance": pattern.statistical_significance,
                    "P_Value": pattern.p_value,
                    "CI_Lower": pattern.confidence_interval_lower,
                    "CI_Upper": pattern.confidence_interval_upper,
                    "Skewness": pattern.skewness,
                    "Kurtosis": pattern.kurtosis,
                },
            )

        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(output_file, index=False)
            self.console.print(f"[dim]✓ CSV exported to {output_file}[/dim]")

    def _display_monthly_calendar(self, result: SeasonalityResult) -> None:
        """Display monthly seasonality calendar with comprehensive metrics."""
        monthly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Monthly"
        ]

        if not monthly_patterns:
            return

        # Create table
        table = Table(
            title=f"📅 Monthly Seasonality Calendar ({result.ticker} - {result.metadata.get('years_of_data', 0):.1f} years)",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Month", style="cyan", no_wrap=True, width=8)
        table.add_column("Avg Return", justify="right", width=11)
        table.add_column("Return Bar", justify="left", width=15)
        table.add_column("Win Rate", justify="right", width=9)
        table.add_column("Win Bar", justify="left", width=12)
        table.add_column("Sharpe", justify="right", width=7)
        table.add_column("Sample", justify="right", style="dim", width=7)
        table.add_column("Risk", justify="center", width=9)

        # Sort by month order
        month_order = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]

        # Find max/min for scaling return bars
        returns = [p.average_return for p in monthly_patterns]
        max_abs_return = max(abs(r) for r in returns) if returns else 1

        for month_name in month_order:
            pattern = next(
                (p for p in monthly_patterns if p.period == month_name),
                None,
            )
            if not pattern:
                continue

            # Color code return
            ret_val = pattern.average_return
            if ret_val > 0:
                ret_color = "green" if ret_val > 1 else "bright_green"
                ret_str = f"[{ret_color}]+{ret_val:.2f}%[/{ret_color}]"
            else:
                ret_color = "red" if ret_val < -1 else "yellow"
                ret_str = f"[{ret_color}]{ret_val:.2f}%[/{ret_color}]"

            # Return visual bar
            bar_length = (
                int(abs(ret_val) / max_abs_return * 10) if max_abs_return > 0 else 0
            )
            bar_char = "█"
            bar_empty = "░"
            if ret_val > 0:
                ret_bar = f"[green]{bar_char * bar_length}{bar_empty * (10 - bar_length)}[/green]"
            else:
                ret_bar = (
                    f"[red]{bar_char * bar_length}{bar_empty * (10 - bar_length)}[/red]"
                )

            # Add significance indicator
            month_display = month_name[:3]
            if pattern.p_value and pattern.p_value < 0.05:
                if ret_val > 0:
                    month_display += " ★"
                else:
                    month_display += " ●"

            # Win rate color and bar
            wr = pattern.win_rate * 100
            wr_color = "green" if wr >= 60 else "yellow" if wr >= 50 else "red"
            wr_str = f"[{wr_color}]{wr:.0f}%[/{wr_color}]"

            # Win rate visual bar (scaled 0-100%)
            win_bar_length = int(wr / 10)  # 10 chars for 100%
            win_bar = f"[{wr_color}]{bar_char * win_bar_length}{bar_empty * (10 - win_bar_length)}[/{wr_color}]"

            # Sharpe ratio
            sharpe = pattern.sharpe_ratio or 0
            sharpe_color = "green" if sharpe > 1 else "yellow" if sharpe > 0 else "red"
            sharpe_str = f"[{sharpe_color}]{sharpe:.2f}[/{sharpe_color}]"

            # Risk level based on std dev
            risk = (
                "Low"
                if pattern.std_dev < 3
                else "Moderate" if pattern.std_dev < 5 else "High"
            )
            risk_color = (
                "green" if risk == "Low" else "yellow" if risk == "Moderate" else "red"
            )
            risk_str = f"[{risk_color}]{risk}[/{risk_color}]"

            table.add_row(
                month_display,
                ret_str,
                ret_bar,
                wr_str,
                win_bar,
                sharpe_str,
                str(pattern.sample_size),
                risk_str,
            )

        self.console.print("\n")
        self.console.print(table)

    def _display_weekly_heatmap(self, result: SeasonalityResult) -> None:
        """Display day-of-week performance analysis with visual bars."""
        weekly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Weekly"
        ]

        if not weekly_patterns:
            return

        # Create table
        table = Table(
            title=f"📊 Day-of-Week Performance Analysis ({result.ticker})",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Day", style="cyan", no_wrap=True, width=12)
        table.add_column("Avg Return", justify="right", width=12)
        table.add_column("Win Rate", justify="right", width=10)
        table.add_column("Trades", justify="right", width=8, style="dim")
        table.add_column("Performance", justify="left", width=20)

        # Sort by day order
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

        # Find max/min for scaling bars
        returns = [p.average_return for p in weekly_patterns if p.period in day_order]
        max_abs_return = max(abs(r) for r in returns) if returns else 1

        for day_name in day_order:
            pattern = next((p for p in weekly_patterns if p.period == day_name), None)
            if not pattern:
                continue

            # Color code return
            ret_val = pattern.average_return
            if ret_val > 0:
                ret_color = "green"
                ret_str = f"[{ret_color}]+{ret_val:.2f}%[/{ret_color}]"
            else:
                ret_color = "red"
                ret_str = f"[{ret_color}]{ret_val:.2f}%[/{ret_color}]"

            # Win rate
            wr = pattern.win_rate * 100
            wr_color = "green" if wr >= 55 else "yellow" if wr >= 50 else "red"
            wr_str = f"[{wr_color}]{wr:.0f}%[/{wr_color}]"

            # Create visual bar
            bar_length = (
                int(abs(ret_val) / max_abs_return * 10) if max_abs_return > 0 else 0
            )
            bar_char = "█" if ret_val > 0 else "▓"
            bar_empty = "░"
            if ret_val > 0:
                bar = f"[green]{bar_char * bar_length}{bar_empty * (10 - bar_length)}[/green]"
            else:
                bar = (
                    f"[red]{bar_char * bar_length}{bar_empty * (10 - bar_length)}[/red]"
                )

            table.add_row(day_name, ret_str, wr_str, str(pattern.sample_size), bar)

        self.console.print("\n")
        self.console.print(table)

    def _display_week_of_year_highlights(self, result: SeasonalityResult) -> None:
        """Display best and worst weeks of the year."""
        week_patterns = [
            p for p in result.patterns if p.pattern_type.value == "WeekOfYear"
        ]

        if not week_patterns or len(week_patterns) < 5:
            return

        # Sort by average return
        sorted_patterns = sorted(
            week_patterns,
            key=lambda p: p.average_return,
            reverse=True,
        )
        best_weeks = sorted_patterns[:3]
        worst_weeks = sorted_patterns[-3:][::-1]  # Reverse to show worst first

        # Create side-by-side display
        table = Table(
            title=f"🏆 Week-of-Year Performance Highlights ({result.ticker})",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Best Performing Weeks", style="green", width=40)
        table.add_column("Worst Performing Weeks", style="red", width=40)

        for i in range(3):
            best = best_weeks[i] if i < len(best_weeks) else None
            worst = worst_weeks[i] if i < len(worst_weeks) else None

            best_str = ""
            if best:
                sig = (
                    f", p={best.p_value:.2f}"
                    if best.p_value and best.p_value < 0.10
                    else ""
                )
                best_str = f"{best.period}: [green]+{best.average_return:.2f}%[/green] ({best.sample_size} obs{sig})"

            worst_str = ""
            if worst:
                sig = (
                    f", p={worst.p_value:.2f}"
                    if worst.p_value and worst.p_value < 0.10
                    else ""
                )
                worst_str = f"{worst.period}: [red]{worst.average_return:.2f}%[/red] ({worst.sample_size} obs{sig})"

            table.add_row(best_str, worst_str)

        self.console.print("\n")
        self.console.print(table)

    def _display_week_of_year_calendar(self, result: SeasonalityResult) -> None:
        """Display full week-of-year calendar with all 52 weeks."""
        week_patterns = [
            p for p in result.patterns if p.pattern_type.value == "WeekOfYear"
        ]

        if not week_patterns or len(week_patterns) < 10:
            return

        # Sort by week number
        sorted_patterns = sorted(week_patterns, key=lambda p: p.period_number or 0)

        # Create table
        table = Table(
            title=f"📅 Week-of-Year Seasonality Calendar ({result.ticker})",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Week", style="cyan", no_wrap=True, width=7)
        table.add_column("Avg Return", justify="right", width=11)
        table.add_column("Return Bar", justify="left", width=15)
        table.add_column("Win Rate", justify="right", width=9)
        table.add_column("Win Bar", justify="left", width=12)
        table.add_column("Sample", justify="right", style="dim", width=7)

        # Find max/min for scaling return bars
        returns = [p.average_return for p in sorted_patterns]
        max_abs_return = max(abs(r) for r in returns) if returns else 1

        # Display in rows of quarters (13 weeks each)
        for i, pattern in enumerate(sorted_patterns):
            # Color code return
            ret_val = pattern.average_return
            if ret_val > 0:
                ret_color = "green"
                ret_str = f"[{ret_color}]+{ret_val:.2f}%[/{ret_color}]"
            else:
                ret_color = "red"
                ret_str = f"[{ret_color}]{ret_val:.2f}%[/{ret_color}]"

            # Return visual bar
            bar_length = (
                int(abs(ret_val) / max_abs_return * 10) if max_abs_return > 0 else 0
            )
            bar_char = "█"
            bar_empty = "░"
            if ret_val > 0:
                ret_bar = f"[green]{bar_char * bar_length}{bar_empty * (10 - bar_length)}[/green]"
            else:
                ret_bar = (
                    f"[red]{bar_char * bar_length}{bar_empty * (10 - bar_length)}[/red]"
                )

            # Week display with significance
            week_display = f"W{pattern.period_number}"
            if pattern.p_value and pattern.p_value < 0.05:
                if ret_val > 0:
                    week_display += " ★"
                else:
                    week_display += " ●"

            # Win rate
            wr = pattern.win_rate * 100
            wr_color = "green" if wr >= 60 else "yellow" if wr >= 50 else "red"
            wr_str = f"[{wr_color}]{wr:.0f}%[/{wr_color}]"

            # Win rate visual bar
            win_bar_length = int(wr / 10)
            win_bar = f"[{wr_color}]{bar_char * win_bar_length}{bar_empty * (10 - win_bar_length)}[/{wr_color}]"

            table.add_row(
                week_display,
                ret_str,
                ret_bar,
                wr_str,
                win_bar,
                str(pattern.sample_size),
            )

            # Add separator every 13 weeks (quarter boundaries)
            if (i + 1) % 13 == 0 and i + 1 < len(sorted_patterns):
                table.add_row("", "", "", "", "", "")  # Empty row as separator

        self.console.print("\n")
        self.console.print(table)

    def _display_statistical_summary(self, result: SeasonalityResult) -> None:
        """Display overall seasonality metrics and insights."""
        from datetime import datetime

        self.console.print("\n")
        self.console.print("[bold cyan]📈 Overall Seasonality Metrics[/bold cyan]")
        self.console.print("=" * 60)

        # Current date context
        now = datetime.now()
        current_month = now.strftime("%B")
        current_day = now.strftime("%A")
        current_week = now.isocalendar()[1]

        self.console.print(
            f"[bold white]Current Position:[/bold white] {current_month} (Week {current_week}, {current_day})",
        )
        self.console.print()

        # Seasonal strength
        strength = result.overall_seasonal_strength
        strength_label = (
            "Very Strong"
            if strength > 0.8
            else (
                "Strong"
                if strength > 0.6
                else (
                    "Moderate"
                    if strength > 0.4
                    else "Weak" if strength > 0.2 else "Very Weak"
                )
            )
        )
        stars = "★" * min(int(strength * 5), 5) + "☆" * (5 - min(int(strength * 5), 5))
        strength_color = (
            "green" if strength > 0.6 else "yellow" if strength > 0.4 else "red"
        )
        self.console.print(
            f"Seasonal Strength: [{strength_color}]{strength:.3f} ({strength_label}) {stars}[/{strength_color}]",
        )

        # Best and worst months
        monthly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Monthly"
        ]
        if monthly_patterns:
            best_month = max(monthly_patterns, key=lambda p: p.average_return)
            worst_month = min(monthly_patterns, key=lambda p: p.average_return)
            self.console.print(
                f"Best Month: [green]{best_month.period} (+{best_month.average_return:.2f}%, {best_month.win_rate*100:.0f}% win rate)[/green]",
            )
            self.console.print(
                f"Worst Month: [red]{worst_month.period} ({worst_month.average_return:.2f}%, {worst_month.win_rate*100:.0f}% win rate)[/red]",
            )

        # Best and worst days
        weekly_patterns = [
            p for p in result.patterns if p.pattern_type.value == "Weekly"
        ]
        if weekly_patterns:
            best_day = max(weekly_patterns, key=lambda p: p.average_return)
            worst_day = min(weekly_patterns, key=lambda p: p.average_return)
            self.console.print(
                f"Best Day: [green]{best_day.period} (+{best_day.average_return:.2f}%, {best_day.win_rate*100:.0f}% win rate)[/green]",
            )
            self.console.print(
                f"Worst Day: [red]{worst_day.period} ({worst_day.average_return:.2f}%, {worst_day.win_rate*100:.0f}% win rate)[/red]",
            )

        # Consistency score (avg of all monthly consistency scores)
        if monthly_patterns:
            avg_consistency = sum(
                p.consistency_score or 0 for p in monthly_patterns
            ) / len(monthly_patterns)
            consistency_pct = avg_consistency * 100
            cons_color = (
                "green"
                if consistency_pct >= 60
                else "yellow" if consistency_pct >= 50 else "red"
            )
            self.console.print(
                f"Overall Consistency: [{cons_color}]{consistency_pct:.0f}% (months with positive returns)[/{cons_color}]",
            )

        self.console.print()

    def _display_summary(self, results: dict[str, SeasonalityResult]) -> None:
        """Display summary of analysis results.

        Args:
            results: Dictionary of analysis results
        """
        if not results:
            return

        # Create summary table
        table = Table(
            title="Seasonality Analysis Summary",
            show_header=True,
            header_style="bold magenta",
        )

        table.add_column("Ticker", style="cyan", no_wrap=True)
        table.add_column("Years", style="green", justify="right")
        table.add_column("Seasonal Strength", style="yellow", justify="right")
        table.add_column("Best Pattern", style="white")
        table.add_column("Period", style="white")
        table.add_column("Avg Return", style="green", justify="right")

        # Add rows
        for ticker, result in sorted(results.items()):
            years = result.metadata.get("years_of_data", 0)

            if result.strongest_pattern:
                pattern = result.strongest_pattern
                table.add_row(
                    ticker,
                    f"{years:.1f}",
                    f"{result.overall_seasonal_strength:.3f}",
                    pattern.pattern_type.value,
                    pattern.period,
                    f"{pattern.average_return:.2f}%",
                )
            else:
                table.add_row(
                    ticker,
                    f"{years:.1f}",
                    f"{result.overall_seasonal_strength:.3f}",
                    "None",
                    "-",
                    "-",
                )

        self.console.print(table)
        self.console.print(
            f"\n[green]✓ Analysis complete. Results saved to {self.output_dir}[/green]",
        )

    def _export_summary(self, results: dict[str, SeasonalityResult]) -> None:
        """Export summary analysis results to CSV file.

        Args:
            results: Dictionary of analysis results
        """
        if not results:
            return

        # Create summary data
        summary_rows = []
        for ticker, result in sorted(results.items()):
            years = result.metadata.get("years_of_data", 0)

            if result.strongest_pattern:
                pattern = result.strongest_pattern
                summary_rows.append(
                    {
                        "Ticker": ticker,
                        "Years": f"{years:.1f}",
                        "Seasonal_Strength": f"{result.overall_seasonal_strength:.3f}",
                        "Strongest_Pattern": pattern.pattern_type.value,
                        "Period": pattern.period,
                        "Avg_Return_Percent": f"{pattern.average_return:.2f}",
                    },
                )
            else:
                summary_rows.append(
                    {
                        "Ticker": ticker,
                        "Years": f"{years:.1f}",
                        "Seasonal_Strength": f"{result.overall_seasonal_strength:.3f}",
                        "Strongest_Pattern": "None",
                        "Period": "-",
                        "Avg_Return_Percent": "-",
                    },
                )

        if summary_rows:
            # Create DataFrame and save to dated CSV file
            summary_df = pd.DataFrame(summary_rows)

            # Generate filename with current date
            current_date = datetime.now().strftime("%Y%m%d")
            summary_file = self.output_dir / f"{current_date}_seasonality_summary.csv"

            summary_df.to_csv(summary_file, index=False)
            self.console.print(f"[green]✓ Summary exported to {summary_file}[/green]")
