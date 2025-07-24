"""Service layer for seasonality analysis."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import polars as pl
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
    PatternType,
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
        self.price_data_dir = Path("data/raw/prices")
        self.output_dir = Path("data/raw/seasonality")

    def run_analysis(self) -> Dict[str, SeasonalityResult]:
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
                "[cyan]Analyzing seasonality patterns...", total=len(tickers)
            )

            for ticker in tickers:
                progress.update(task, description=f"[cyan]Analyzing {ticker}...")

                try:
                    result = self._analyze_ticker(ticker)
                    if result:
                        results[ticker] = result
                        self._save_result(result)
                except Exception as e:
                    self.console.print(f"[red]Error analyzing {ticker}: {str(e)}[/red]")

                progress.advance(task)

        # Display summary
        self._display_summary(results)

        # Export summary to file
        self._export_summary(results)

        return results

    def _get_tickers_to_analyze(self) -> List[str]:
        """Get list of tickers to analyze."""
        if self.config.tickers:
            # Use specified tickers
            return self.config.tickers
        else:
            # Get all available tickers from price data directory
            tickers = []
            for file_path in self.price_data_dir.glob("*_D.csv"):
                ticker = file_path.stem.replace("_D", "")
                tickers.append(ticker)
            return sorted(tickers)

    def _analyze_ticker(self, ticker: str) -> Optional[SeasonalityResult]:
        """Analyze seasonality for a single ticker.

        Args:
            ticker: Ticker symbol

        Returns:
            Seasonality results or None if insufficient data
        """
        # Load price data
        price_file = self.price_data_dir / f"{ticker}_D.csv"
        if not price_file.exists():
            self.console.print(f"[yellow]Price data not found for {ticker}[/yellow]")
            return None

        # Read data
        data = pd.read_csv(price_file, parse_dates=["Date"], index_col="Date")

        # Check if we have enough data
        years_of_data = (data.index[-1] - data.index[0]).days / 365.25
        if years_of_data < self.config.min_years:
            self.console.print(
                f"[yellow]Insufficient data for {ticker}: "
                f"{years_of_data:.1f} years < {self.config.min_years} years required[/yellow]"
            )
            return None

        # Analyze patterns
        patterns = self.analyzer.analyze_all_patterns(
            data, detrend=self.config.detrend_data
        )

        # Calculate overall seasonal strength
        seasonal_strength = self.analyzer.calculate_seasonal_strength(patterns)

        # Find strongest pattern
        strongest_pattern = None
        if patterns:
            strongest_pattern = max(patterns, key=lambda p: p.statistical_significance)

        # Create result
        result = SeasonalityResult(
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

        return result

    def _save_result(self, result: SeasonalityResult) -> None:
        """Save analysis result to file.

        Args:
            result: Seasonality analysis result
        """
        if self.config.output_format == "json":
            # Save as JSON
            output_file = self.output_dir / f"{result.ticker}_seasonality.json"
            with open(output_file, "w") as f:
                json.dump(result.model_dump(), f, indent=2, default=str)
        else:
            # Save as CSV
            output_file = self.output_dir / f"{result.ticker}_seasonality.csv"

            # Convert patterns to DataFrame
            rows = []
            for pattern in result.patterns:
                rows.append(
                    {
                        "Pattern_Type": pattern.pattern_type.value,
                        "Period": pattern.period,
                        "Average_Return": pattern.average_return,
                        "Std_Dev": pattern.std_dev,
                        "Win_Rate": pattern.win_rate,
                        "Sample_Size": pattern.sample_size,
                        "Statistical_Significance": pattern.statistical_significance,
                        "P_Value": pattern.p_value,
                        "CI_Lower": pattern.confidence_interval_lower,
                        "CI_Upper": pattern.confidence_interval_upper,
                    }
                )

            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(output_file, index=False)

    def _display_summary(self, results: Dict[str, SeasonalityResult]) -> None:
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
        table.add_column("Strongest Pattern", style="white")
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
            f"\n[green]✓ Analysis complete. Results saved to {self.output_dir}[/green]"
        )

    def _export_summary(self, results: Dict[str, SeasonalityResult]) -> None:
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
                    }
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
                    }
                )

        if summary_rows:
            # Create DataFrame and save to dated CSV file
            summary_df = pd.DataFrame(summary_rows)

            # Generate filename with current date
            current_date = datetime.now().strftime("%Y%m%d")
            summary_file = self.output_dir / f"{current_date}_seasonality_summary.csv"

            summary_df.to_csv(summary_file, index=False)
            self.console.print(f"[green]✓ Summary exported to {summary_file}[/green]")
