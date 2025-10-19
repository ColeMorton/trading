"""Service for portfolio-based seasonality analysis."""

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from app.cli.models.seasonality import PortfolioSeasonalityConfig, SeasonalityConfig
from app.cli.utils.portfolio_path import resolve_portfolio_path
from app.tools.services.seasonality_service import SeasonalityService


class PortfolioSeasonalityService:
    """Service for analyzing seasonal patterns from portfolio strategy data."""

    def __init__(self, config: PortfolioSeasonalityConfig):
        """Initialize the service.

        Args:
            config: Portfolio seasonality configuration
        """
        self.config = config
        self.console = Console()
        self.strategies_dir = Path("data/raw/strategies")

    def run_analysis(self) -> Dict[str, any]:
        """Run seasonality analysis for tickers in the specified portfolio.

        Returns:
            Dictionary containing analysis results and metadata
        """
        # Load and validate portfolio
        portfolio_df = self._load_portfolio()
        ticker_periods = self._determine_ticker_periods(portfolio_df)

        # Display analysis plan
        self._display_analysis_plan(ticker_periods)

        # Run seasonality analysis for each ticker
        results = {}
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(
                "Analyzing seasonality patterns...", total=len(ticker_periods)
            )

            for ticker, time_period_days in ticker_periods.items():
                progress.update(task, description=f"Analyzing {ticker}...")

                # Create seasonality config for this ticker
                seasonality_config = SeasonalityConfig(
                    tickers=[ticker],
                    confidence_level=self.config.confidence_level,
                    output_format=self.config.output_format,
                    include_holidays=self.config.include_holidays,
                    detrend_data=self.config.detrend_data,
                    min_sample_size=self.config.min_sample_size,
                )

                # Run analysis for this ticker with custom time period (directly without saving files)
                try:
                    service = SeasonalityService(seasonality_config)
                    # Override the analyzer with custom time period
                    from datetime import datetime

                    from app.tools.seasonality_analyzer import SeasonalityAnalyzer

                    service.analyzer = SeasonalityAnalyzer(
                        confidence_level=self.config.confidence_level,
                        min_sample_size=self.config.min_sample_size,
                        time_period_days=time_period_days,
                        current_date=datetime.now(),
                    )
                    ticker_result = service._analyze_ticker(ticker)
                    # Determine analysis source
                    if self.config.time_period_days is not None:
                        analysis_source = "override"
                    elif time_period_days != self.config.default_time_period_days:
                        analysis_source = "signal_entry"
                    else:
                        analysis_source = "default"

                    results[ticker] = {
                        "results": ticker_result,
                        "time_period_days": time_period_days,
                        "analysis_source": analysis_source,
                    }
                except Exception as e:
                    self.console.print(f"[red]Error analyzing {ticker}: {str(e)}[/red]")
                    # Determine analysis source
                    if self.config.time_period_days is not None:
                        analysis_source = "override"
                    elif time_period_days != self.config.default_time_period_days:
                        analysis_source = "signal_entry"
                    else:
                        analysis_source = "default"

                    results[ticker] = {
                        "error": str(e),
                        "time_period_days": time_period_days,
                        "analysis_source": analysis_source,
                    }

                progress.advance(task)

        # Create consolidated summary and save to file
        self._save_portfolio_summary(results)

        return {
            "portfolio": self.config.portfolio,
            "ticker_results": results,
            "total_tickers": len(ticker_periods),
            "successful_analyses": len(
                [r for r in results.values() if "error" not in r]
            ),
            "display_data": self._prepare_display_data(results),
        }

    def _load_portfolio(self) -> pd.DataFrame:
        """Load and validate the portfolio CSV file.

        Returns:
            DataFrame containing portfolio data

        Raises:
            ValueError: If portfolio file doesn't exist or is invalid
        """
        # Resolve portfolio path with .csv extension
        portfolio_filename = resolve_portfolio_path(self.config.portfolio)
        portfolio_path = self.strategies_dir / portfolio_filename

        # Check if file exists
        if not portfolio_path.exists():
            available_files = [f.name for f in self.strategies_dir.glob("*.csv")]
            raise ValueError(
                f"Portfolio file not found: {portfolio_path}\n"
                f"Available files: {', '.join(available_files)}"
            )

        # Load CSV
        try:
            df = pd.read_csv(portfolio_path)
        except Exception as e:
            raise ValueError(f"Error reading portfolio CSV: {str(e)}")

        # Validate required columns
        required_columns = ["Ticker", "Signal Entry", "Avg Trade Duration"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in portfolio CSV: {', '.join(missing_columns)}\n"
                f"Available columns: {', '.join(df.columns)}"
            )

        return df

    def _determine_ticker_periods(self, portfolio_df: pd.DataFrame) -> Dict[str, int]:
        """Determine time period for each ticker based on signal entry status.

        Args:
            portfolio_df: Portfolio dataframe

        Returns:
            Dictionary mapping ticker to time period in days
        """
        ticker_periods = {}

        # Check if time_period override is set - if so, use it for ALL tickers
        if self.config.time_period_days is not None:
            for ticker in portfolio_df["Ticker"].unique():
                ticker_periods[ticker] = self.config.time_period_days
            return ticker_periods

        # Group by ticker to analyze each one
        for ticker in portfolio_df["Ticker"].unique():
            ticker_data = portfolio_df[portfolio_df["Ticker"] == ticker]

            # Check if any strategy for this ticker has Signal Entry = true
            has_signal_entry = (
                ticker_data["Signal Entry"].astype(str).str.lower().eq("true").any()
            )

            if has_signal_entry:
                # Use average trade duration from strategies with signal entry
                signal_strategies = ticker_data[
                    ticker_data["Signal Entry"].astype(str).str.lower() == "true"
                ]

                # Extract days from Avg Trade Duration
                durations = []
                for duration_str in signal_strategies["Avg Trade Duration"].dropna():
                    days = self._parse_duration_to_days(duration_str)
                    if days is not None:
                        durations.append(days)

                if durations:
                    # Use average duration across all signal entry strategies
                    avg_duration = int(round(sum(durations) / len(durations)))
                    ticker_periods[ticker] = max(
                        1, avg_duration
                    )  # Ensure at least 1 day
                else:
                    # Fallback to default if duration parsing failed
                    ticker_periods[ticker] = self.config.default_time_period_days
            else:
                # Use default time period
                ticker_periods[ticker] = self.config.default_time_period_days

        return ticker_periods

    def _parse_duration_to_days(self, duration_str: str) -> Optional[int]:
        """Parse duration string to extract days.

        Args:
            duration_str: Duration string like "56 days 00:20:34.285714285"

        Returns:
            Number of days or None if parsing failed
        """
        if pd.isna(duration_str) or not isinstance(duration_str, str):
            return None

        try:
            # Try to extract days using regex
            # Pattern matches "X days" or "X day"
            match = re.search(r"(\d+)\s*days?", str(duration_str).lower())
            if match:
                return int(match.group(1))

            # If no explicit "days", check if it's just a number
            if duration_str.strip().isdigit():
                return int(duration_str.strip())

        except (ValueError, AttributeError):
            pass

        return None

    def _display_analysis_plan(self, ticker_periods: Dict[str, int]) -> None:
        """Display the analysis plan showing tickers and their time periods.

        Args:
            ticker_periods: Dictionary mapping ticker to time period in days
        """
        self.console.print(
            f"\n[bold cyan]Portfolio Seasonality Analysis Plan[/bold cyan]"
        )
        self.console.print(f"Portfolio: [yellow]{self.config.portfolio}[/yellow]")
        self.console.print(f"Total tickers: [green]{len(ticker_periods)}[/green]")

        # Show override message if applicable
        if self.config.time_period_days is not None:
            self.console.print(
                f"[bold red]⚠️  Using OVERRIDE time period: {self.config.time_period_days} days for ALL tickers[/bold red]"
            )

        self.console.print()

        # Create summary table
        table = Table(
            title="Ticker Analysis Plan",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Ticker", style="cyan", no_wrap=True)
        table.add_column("Time Period", style="yellow", justify="right")
        table.add_column("Source", style="white")

        # Group tickers by time period for summary
        signal_based = [
            t
            for t, d in ticker_periods.items()
            if d != self.config.default_time_period_days
        ]
        default_based = [
            t
            for t, d in ticker_periods.items()
            if d == self.config.default_time_period_days
        ]

        # Add rows to table (limit to first 20 for readability)
        displayed_tickers = list(ticker_periods.items())[:20]
        for ticker, days in displayed_tickers:
            if self.config.time_period_days is not None:
                source = f"Override ({days} days)"
            else:
                source = (
                    "Signal Entry"
                    if days != self.config.default_time_period_days
                    else f"Default ({self.config.default_time_period_days} days)"
                )
            table.add_row(ticker, f"{days} days", source)

        if len(ticker_periods) > 20:
            table.add_row("...", "...", f"[dim]({len(ticker_periods) - 20} more)[/dim]")

        self.console.print(table)

        # Print summary
        self.console.print()
        if self.config.time_period_days is not None:
            # All tickers use override
            self.console.print(
                f"[red]• {len(ticker_periods)} tickers using OVERRIDE {self.config.time_period_days}-day period[/red]"
            )
        else:
            # Normal mode with signal-based and default
            self.console.print(
                f"[green]• {len(signal_based)} tickers using signal-based time periods[/green]"
            )
            self.console.print(
                f"[yellow]• {len(default_based)} tickers using default {self.config.default_time_period_days}-day period[/yellow]"
            )
        self.console.print()

    def _save_portfolio_summary(self, results: Dict[str, Dict]) -> None:
        """Save consolidated portfolio summary to file.

        Args:
            results: Dictionary of ticker results
        """
        from datetime import datetime

        # Create output directory
        output_dir = Path("data/raw/seasonality")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare summary data
        summary_data = []
        for ticker, result_info in results.items():
            if "error" in result_info:
                continue

            result = result_info.get("results")
            if not result:
                continue

            # Find best pattern (highest expectancy)
            strongest_pattern = result.strongest_pattern
            if strongest_pattern:
                summary_data.append(
                    {
                        "Ticker": ticker,
                        "Years": round(
                            (result.data_end_date - result.data_start_date).days
                            / 365.25,
                            1,
                        ),
                        "Seasonal_Strength": round(result.overall_seasonal_strength, 3),
                        "Best_Pattern": strongest_pattern.pattern_type,
                        "Period": strongest_pattern.period,
                        "Avg_Return_Percent": round(
                            strongest_pattern.average_return, 2
                        ),
                        "Win_Rate": round(strongest_pattern.win_rate, 3),
                        "Expectancy": round(
                            strongest_pattern.average_return
                            * strongest_pattern.win_rate,
                            2,
                        ),
                        "Sample_Size": strongest_pattern.sample_size,
                        "Statistical_Significance": round(
                            strongest_pattern.statistical_significance, 3
                        ),
                        "Time_Period_Days": result_info["time_period_days"],
                        "Analysis_Source": result_info["analysis_source"],
                    }
                )

        if summary_data:
            # Save as CSV
            portfolio_name = self.config.portfolio.replace(".csv", "")
            filename = f"{portfolio_name}_portfolio_seasonality.csv"
            filepath = output_dir / filename

            df = pd.DataFrame(summary_data)
            df = df.sort_values("Expectancy", ascending=False)
            df.to_csv(filepath, index=False)

            self.console.print(f"[green]✓ Portfolio summary saved: {filename}[/green]")

            # Save as JSON if requested
            if self.config.output_format == "json":
                json_filename = f"{portfolio_name}_portfolio_seasonality.json"
                json_filepath = output_dir / json_filename

                summary_dict = {
                    "portfolio": self.config.portfolio,
                    "analysis_date": datetime.now().isoformat(),
                    "total_tickers": len(results),
                    "successful_analyses": len(summary_data),
                    "tickers": summary_data,
                }

                import json

                with open(json_filepath, "w") as f:
                    json.dump(summary_dict, f, indent=2)

                self.console.print(
                    f"[green]✓ Portfolio JSON saved: {json_filename}[/green]"
                )

    def _prepare_display_data(self, results: Dict[str, Dict]) -> List[Dict]:
        """Prepare data for table display.

        Args:
            results: Dictionary of ticker results

        Returns:
            List of dictionaries ready for table display
        """
        display_data = []

        for ticker, result_info in results.items():
            if "error" in result_info:
                display_data.append(
                    {
                        "ticker": ticker,
                        "years": "N/A",
                        "seasonal_strength": "Error",
                        "strongest_pattern": "Error",
                        "period": "N/A",
                        "avg_return": "N/A",
                        "time_period_days": result_info["time_period_days"],
                        "analysis_source": result_info["analysis_source"],
                    }
                )
                continue

            result = result_info.get("results")
            if not result:
                continue

            strongest_pattern = result.strongest_pattern
            if strongest_pattern:
                display_data.append(
                    {
                        "ticker": ticker,
                        "years": round(
                            (result.data_end_date - result.data_start_date).days
                            / 365.25,
                            1,
                        ),
                        "seasonal_strength": round(result.overall_seasonal_strength, 3),
                        "strongest_pattern": strongest_pattern.pattern_type,
                        "period": strongest_pattern.period,
                        "avg_return": round(strongest_pattern.average_return, 2),
                        "win_rate": round(strongest_pattern.win_rate, 3),
                        "expectancy": round(
                            strongest_pattern.average_return
                            * strongest_pattern.win_rate,
                            2,
                        ),
                        "sample_size": strongest_pattern.sample_size,
                        "statistical_significance": round(
                            strongest_pattern.statistical_significance, 3
                        ),
                        "time_period_days": result_info["time_period_days"],
                        "analysis_source": result_info["analysis_source"],
                    }
                )

        # Sort by expectancy (highest first)
        display_data.sort(
            key=lambda x: x.get("expectancy", -999)
            if isinstance(x.get("expectancy"), (int, float))
            else -999,
            reverse=True,
        )
        return display_data
