"""Service layer for seasonality expectancy analysis."""

from calendar import monthrange
from datetime import datetime, timedelta
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from app.cli.models.seasonality import SeasonalityExpectancyConfig


warnings.filterwarnings("ignore")


class SeasonalityExpectancyService:
    """Service for analyzing seasonality expectancy for specific time periods."""

    def __init__(self, config: SeasonalityExpectancyConfig):
        """Initialize the service.

        Args:
            config: Seasonality expectancy configuration
        """
        self.config = config
        self.console = Console()
        self.seasonality_dir = Path("data/raw/seasonality")
        self.current_dir = self.seasonality_dir / "current"
        self.results: list[dict[str, Any]] = []
        self.skipped_tickers: list[str] = []  # Track filtered tickers

        # Ensure directories exist
        self.current_dir.mkdir(parents=True, exist_ok=True)

    def reset_tracking(self):
        """Reset tracking lists for new analysis."""
        self.results = []
        self.skipped_tickers = []

    def analyze_current_period(self) -> pd.DataFrame:
        """Analyze expectancy for current period based on configuration.

        Returns:
            DataFrame with ranked expectancy analysis
        """
        # Reset tracking for new analysis
        self.reset_tracking()

        # Calculate period details
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=self.config.days)

        self.console.print(
            f"🔍 [cyan]Analyzing expectancy for {self.config.days}-day period[/cyan]",
        )
        self.console.print(
            f"📅 [white]Period: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}[/white]",
        )

        # Calculate time weights for the period
        time_weights = self._calculate_time_weights(start_date, end_date)

        self.console.print(
            f"⚖️  [yellow]Time weights calculated for {len(time_weights)} periods[/yellow]",
        )

        # Process seasonality files
        csv_files = [
            f
            for f in self.seasonality_dir.glob("*.csv")
            if not f.name.endswith("_summary.csv") and f.parent.name != "current"
        ]

        # Filter by specific tickers if provided
        if self.config.tickers:
            ticker_set = set(self.config.tickers)
            csv_files = [
                f for f in csv_files if f.stem.replace("_seasonality", "") in ticker_set
            ]

        self.console.print(
            f"📊 [white]Processing {len(csv_files)} ticker files...[/white]",
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task(
                "[cyan]Analyzing seasonality patterns...", total=len(csv_files),
            )

            for csv_file in csv_files:
                try:
                    ticker = csv_file.stem.replace("_seasonality", "")
                    result = self._analyze_ticker_file(csv_file, ticker, time_weights)
                    if result:
                        self.results.append(result)
                except Exception as e:
                    self.console.print(
                        f"⚠️  [yellow]Warning: Error processing {csv_file.name}: {e!s}[/yellow]",
                    )
                    self.skipped_tickers.append((ticker, f"Processing error: {e!s}"))
                    continue

                progress.advance(task)

        # Convert to DataFrame and rank
        if not self.results:
            self.console.print("❌ [red]No valid results found[/red]")
            return pd.DataFrame()

        df = pd.DataFrame(self.results)
        df = df.sort_values("risk_adjusted_score", ascending=False).reset_index(
            drop=True,
        )
        df["rank"] = df.index + 1

        self.console.print(
            f"✅ [green]Analysis complete! {len(df)} tickers analyzed successfully[/green]",
        )

        # Display filtered ticker information if any
        if self.skipped_tickers:
            self.console.print(
                f"\n⚠️  [yellow]{len(self.skipped_tickers)} ticker(s) filtered out due to quality criteria:[/yellow]",
            )
            for ticker, reason in self.skipped_tickers:
                self.console.print(
                    f"    - [white]{ticker}[/white]: [dim]{reason}[/dim]",
                )

        return df

    def _calculate_time_weights(
        self, start_date: datetime.date, end_date: datetime.date,
    ) -> dict[str, float]:
        """Calculate time weights for different periods based on actual calendar days.

        Args:
            start_date: Start date for the analysis period
            end_date: End date for the analysis period

        Returns:
            Dictionary with period weights
        """
        weights: dict[str, float] = {}
        total_days = (end_date - start_date).days

        # Calculate monthly weights
        current_date = start_date
        while current_date < end_date:
            month_name = current_date.strftime("%B")
            year = current_date.year
            month = current_date.month

            # Find last day of current month in the analysis period
            days_in_month = monthrange(year, month)[1]
            month_end = min(datetime(year, month, days_in_month).date(), end_date)

            # Calculate days in this month that are part of our period
            days_in_period = (month_end - current_date).days + 1
            weight = days_in_period / total_days

            if month_name in weights:
                weights[month_name] += weight
            else:
                weights[month_name] = weight

            # Move to first day of next month
            if month == 12:
                current_date = datetime(year + 1, 1, 1).date()
            else:
                current_date = datetime(year, month + 1, 1).date()

        # Calculate quarterly weights
        quarters = {
            "Q1": ["January", "February", "March"],
            "Q2": ["April", "May", "June"],
            "Q3": ["July", "August", "September"],
            "Q4": ["October", "November", "December"],
        }

        for quarter, months in quarters.items():
            quarter_weight = sum(weights.get(month, 0) for month in months)
            if quarter_weight > 0:
                weights[quarter] = quarter_weight

        return weights

    def _analyze_ticker_file(
        self, csv_file: Path, ticker: str, time_weights: dict[str, float],
    ) -> dict | None:
        """Analyze a single ticker's seasonality file."""

        # Load data
        try:
            df = pd.read_csv(csv_file)
        except Exception as e:
            self.skipped_tickers.append((ticker, f"Failed to read file: {e!s}"))
            return None

        # Calculate weighted return based on time periods
        combined_return = 0
        total_weight = 0
        win_rates = []
        significance_scores = []
        sample_sizes = []
        volatilities = []
        patterns_used = []

        # Process monthly patterns
        for month, weight in time_weights.items():
            if month.startswith("Q"):  # Skip quarterly for now, process separately
                continue

            monthly_data = df[
                (df["Pattern_Type"] == "Monthly") & (df["Period"] == month)
            ]
            if not monthly_data.empty:
                row = monthly_data.iloc[0]

                # Apply quality filters
                if (
                    row["Sample_Size"] >= self.config.min_sample_size
                    and row["Statistical_Significance"] >= self.config.min_significance
                ):
                    combined_return += row["Average_Return"] * weight
                    total_weight += weight

                    win_rates.append(row["Win_Rate"])
                    significance_scores.append(row["Statistical_Significance"])
                    sample_sizes.append(row["Sample_Size"])
                    volatilities.append(row["Std_Dev"])
                    patterns_used.append(f"{month} Monthly")

        # Add quarterly patterns as supplementary signals
        for quarter, weight in time_weights.items():
            if not quarter.startswith("Q"):
                continue

            quarterly_data = df[
                (df["Pattern_Type"] == "Quarterly") & (df["Period"] == quarter)
            ]
            if not quarterly_data.empty:
                row = quarterly_data.iloc[0]

                if (
                    row["Sample_Size"] >= self.config.min_sample_size
                    and row["Statistical_Significance"] >= self.config.min_significance
                ):
                    # Quarterly patterns get reduced weight (supplementary signal)
                    quarterly_weight = weight * 0.3
                    combined_return += row["Average_Return"] * quarterly_weight
                    total_weight += quarterly_weight

                    win_rates.append(row["Win_Rate"])
                    significance_scores.append(row["Statistical_Significance"])
                    sample_sizes.append(row["Sample_Size"])
                    volatilities.append(row["Std_Dev"])
                    patterns_used.append(f"{quarter} Quarterly")

        # Validate sufficient data
        if total_weight == 0 or len(patterns_used) == 0:
            # Determine reason for filtering
            if df.empty:
                reason = "No seasonality data available"
            elif len(patterns_used) == 0:
                # Check if patterns exist but don't meet criteria
                july_exists = not df[
                    (df["Pattern_Type"] == "Monthly") & (df["Period"] == "July")
                ].empty
                aug_exists = not df[
                    (df["Pattern_Type"] == "Monthly") & (df["Period"] == "August")
                ].empty
                q3_exists = not df[
                    (df["Pattern_Type"] == "Quarterly") & (df["Period"] == "Q3")
                ].empty

                if july_exists or aug_exists or q3_exists:
                    reason = f"Patterns below quality thresholds (min samples: {self.config.min_sample_size}, min significance: {self.config.min_significance})"
                else:
                    reason = "No patterns for Jul-Aug period"
            else:
                reason = "Insufficient data quality"

            self.skipped_tickers.append((ticker, reason))
            return None

        # Normalize combined return
        combined_return = combined_return / min(total_weight, 1.0)

        # Calculate aggregate metrics
        avg_win_rate = np.mean(win_rates) if win_rates else 0
        avg_significance = np.mean(significance_scores) if significance_scores else 0
        avg_sample_size = np.mean(sample_sizes) if sample_sizes else 0
        avg_volatility = np.mean(volatilities) if volatilities else 0

        # Calculate risk-adjusted score
        risk_adjusted_score = self._calculate_risk_adjusted_score(
            combined_return, avg_significance, avg_win_rate, avg_volatility,
        )

        # Determine asset class and confidence
        asset_class = self._classify_asset(ticker)
        confidence = self._calculate_confidence(avg_significance, avg_sample_size)

        return {
            "ticker": ticker,
            "expected_return": combined_return,
            "risk_adjusted_score": risk_adjusted_score,
            "win_rate": avg_win_rate,
            "confidence": confidence,
            "asset_class": asset_class,
            "volatility": avg_volatility,
            "sample_size": int(avg_sample_size),
            "statistical_significance": avg_significance,
            "patterns_used": len(patterns_used),
            "pattern_details": ", ".join(patterns_used),
        }

    def _calculate_risk_adjusted_score(
        self,
        expected_return: float,
        significance: float,
        win_rate: float,
        volatility: float,
    ) -> float:
        """Calculate risk-adjusted expectancy score."""

        # Base score from expected return
        score = expected_return

        # Statistical significance multiplier (0.5 to 1.5)
        significance_multiplier = 0.5 + significance
        score *= significance_multiplier

        # Win rate bonus (up to +20% for high win rates)
        win_rate_bonus = (win_rate - 0.5) * 0.4
        score += win_rate_bonus

        # Volatility penalty (penalize high volatility)
        volatility_penalty = min(volatility * 0.1, 0.5)
        score -= volatility_penalty

        return score

    def _classify_asset(self, ticker: str) -> str:
        """Classify ticker into asset class."""
        if "-USD" in ticker:
            return "Crypto"
        if ticker in [
            "SPY",
            "QQQ",
            "IWM",
            "XLK",
            "XLF",
            "XLE",
            "XLI",
            "XLV",
            "XLY",
            "XLP",
            "XLB",
            "XLU",
            "XLRE",
            "XLC",
        ]:
            return "ETF"
        if ticker == "GLD":
            return "Commodity"
        return "Stock"

    def _calculate_confidence(self, significance: float, sample_size: int) -> str:
        """Calculate confidence level."""
        if significance > 0.8 and sample_size > 200:
            return "Very High"
        if significance > 0.7 and sample_size > 100:
            return "High"
        if significance > 0.6 and sample_size > 50:
            return "Medium"
        return "Low"

    def generate_csv_report(self, results_df: pd.DataFrame) -> Path:
        """Generate CSV report and save to current directory.

        Args:
            results_df: Analysis results DataFrame

        Returns:
            Path to saved CSV file
        """
        if results_df.empty:
            msg = "No results available for CSV generation"
            raise ValueError(msg)

        # Generate filename with current date
        current_date = datetime.now().strftime("%Y%m%d")
        csv_filename = f"{current_date}_expectancy_analysis.csv"
        csv_path = self.current_dir / csv_filename

        # Select and order columns for output
        output_columns = [
            "rank",
            "ticker",
            "expected_return",
            "risk_adjusted_score",
            "win_rate",
            "confidence",
            "asset_class",
            "volatility",
            "sample_size",
            "statistical_significance",
            "patterns_used",
            "pattern_details",
        ]

        results_df[output_columns].to_csv(csv_path, index=False)

        self.console.print(f"💾 [green]CSV report saved: {csv_path}[/green]")
        return csv_path

    def generate_markdown_report(self, results_df: pd.DataFrame) -> Path:
        """Generate markdown report and save to current directory.

        Args:
            results_df: Analysis results DataFrame

        Returns:
            Path to saved markdown file
        """
        if results_df.empty:
            msg = "No results available for markdown generation"
            raise ValueError(msg)

        # Generate filename with current date
        current_date = datetime.now().strftime("%Y%m%d")
        md_filename = f"{current_date}_expectancy_report.md"
        md_path = self.current_dir / md_filename

        # Generate report content
        report_content = self._generate_report_content(results_df)

        # Save to file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        self.console.print(f"📝 [green]Markdown report saved: {md_path}[/green]")
        return md_path

    def _generate_report_content(self, results_df: pd.DataFrame) -> str:
        """Generate the markdown report content."""
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=self.config.days)
        top_results = results_df.head(self.config.top_n_results)

        # Build report content
        lines = [
            "# 🎯 SEASONALITY EXPECTANCY ANALYSIS",
            "",
            "## 📊 Analysis Framework",
            "",
            f"- **Period**: {start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')} ({self.config.days}-day hold)",
            f"- **Tickers Analyzed**: {len(results_df)} tickers met quality criteria",
            f"- **Top Opportunities**: {len(top_results)} highest expectancy tickers shown",
            "- **Methodology**: Risk-adjusted expectancy with statistical significance filters",
            f"- **Quality Filters**: Min sample size {self.config.min_sample_size}, min significance {self.config.min_significance}",
            "",
            "---",
            "",
            "## 🏆 TOP OPPORTUNITIES",
            "",
            "| Rank | Ticker | Expected Return | Asset Class | Win Rate | Confidence | Key Insight |",
            "|------|--------|-----------------|-------------|----------|------------|-------------|",
        ]

        # Add top results
        for _, row in top_results.head(10).iterrows():
            insight = self._generate_ticker_insight(row)
            lines.append(
                f"| **{int(row['rank'])}** | **{row['ticker']}** | **{row['expected_return']:+.2f}%** | "
                f"{row['asset_class']} | {row['win_rate']:.1%} | {row['confidence']} | {insight} |",
            )

        lines.extend(
            [
                "",
                "---",
                "",
                "## 📈 KEY FINDINGS",
                "",
                f"### 🥇 Top Performer: {results_df.iloc[0]['ticker']}",
                "",
                f"- **Expected Return**: {results_df.iloc[0]['expected_return']:+.2f}%",
                f"- **Asset Class**: {results_df.iloc[0]['asset_class']}",
                f"- **Win Rate**: {results_df.iloc[0]['win_rate']:.1%}",
                f"- **Confidence**: {results_df.iloc[0]['confidence']}",
                f"- **Volatility**: {results_df.iloc[0]['volatility']:.1f}%",
                "",
                "### 📊 Market Insights",
                "",
                f"- **Average Expected Return**: {results_df['expected_return'].mean():+.2f}%",
                f"- **Median Expected Return**: {results_df['expected_return'].median():+.2f}%",
                f"- **Average Win Rate**: {results_df['win_rate'].mean():.1%}",
                f"- **Best Traditional Stock**: {self._get_best_stock(results_df)}",
                "",
                "### 🏭 Asset Distribution",
                "",
            ],
        )

        # Add asset class distribution
        asset_dist = top_results["asset_class"].value_counts()
        for asset_class, count in asset_dist.items():
            percentage = (count / len(top_results)) * 100
            lines.append(f"- **{asset_class}**: {count} tickers ({percentage:.1f}%)")

        lines.extend(
            [
                "",
                "### ⚠️ Risk Considerations",
                "",
                f"- **Volatility Range**: {results_df['volatility'].min():.1f}% - {results_df['volatility'].max():.1f}%",
                f"- **Statistical Reliability**: Minimum {self.config.min_sample_size} samples required",
                f"- **Significance Filter**: Only patterns with ≥{self.config.min_significance} significance included",
                "",
                "---",
                "",
                "## 💡 IMPLEMENTATION RECOMMENDATIONS",
                "",
                "### 🎯 Primary Strategy",
                "",
                self._generate_primary_strategy_recommendation(results_df.iloc[0]),
                "",
                "### 🛡️ Risk Management",
                "",
                "- **Position Sizing**: Scale positions based on volatility and confidence levels",
                "- **Diversification**: Consider correlation between selected tickers",
                "- **Stop Losses**: Set appropriate stops based on individual volatility",
                "- **Time Horizon**: Honor the analyzed hold period for optimal results",
                "",
                "### ⏰ Timing Considerations",
                "",
                f"- **Analysis Period**: Optimized for {self.config.days}-day hold from current date",
                "- **Pattern Seasonality**: Based on historical calendar effects",
                "- **Market Conditions**: Consider current market environment vs. historical patterns",
                "",
                "---",
                "",
                "## 📋 ANALYSIS METADATA",
                "",
                f"- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"- **Total Tickers Processed**: {len(results_df)}",
                f"- **Average Patterns Per Ticker**: {results_df['patterns_used'].mean():.1f}",
                f"- **Configuration**: {self.config.days}d hold, min_samples={self.config.min_sample_size}, min_sig={self.config.min_significance}",
                "",
                "**⚠️ Important Disclaimer**: Past performance does not guarantee future results. This analysis is based on historical patterns and should be combined with current market analysis, risk management, and proper position sizing.",
                "",
                "---",
                "",
                "*Generated by Seasonality Expectancy Analysis System*",
            ],
        )

        return "\n".join(lines)

    def _generate_ticker_insight(self, row: pd.Series) -> str:
        """Generate insight text for a ticker."""
        if row["asset_class"] == "Crypto":
            return f"🚀 Strong crypto pattern - {row['expected_return']:+.2f}% expected"
        if row["expected_return"] > 0.1:
            return (
                f"📈 Above-average returns with {row['confidence'].lower()} confidence"
            )
        if row["win_rate"] > 0.55:
            return f"✅ High win rate ({row['win_rate']:.1%}) pattern"
        if row["confidence"] in ["High", "Very High"]:
            return "🔒 High statistical confidence"
        return "⚖️ Balanced risk-return profile"

    def _get_best_stock(self, results_df: pd.DataFrame) -> str:
        """Get the best performing traditional stock."""
        stocks = results_df[results_df["asset_class"] == "Stock"]
        if stocks.empty:
            return "None"
        return f"{stocks.iloc[0]['ticker']} ({stocks.iloc[0]['expected_return']:+.2f}%)"

    def _generate_primary_strategy_recommendation(self, top_result: pd.Series) -> str:
        """Generate primary strategy recommendation."""
        lines = [
            f"**Focus on {top_result['ticker']}** for highest expectancy:",
            f"- **Expected Return**: {top_result['expected_return']:+.2f}%",
            f"- **Win Rate**: {top_result['win_rate']:.1%}",
            f"- **Volatility**: {top_result['volatility']:.1f}% (adjust position size accordingly)",
            f"- **Confidence**: {top_result['confidence']} statistical confidence",
        ]

        if top_result["volatility"] > 3.0:
            lines.append(
                "- **Risk Management**: Reduce position size due to higher volatility",
            )

        if top_result["win_rate"] < 0.5:
            lines.append(
                "- **Entry Strategy**: Consider better entry timing given sub-50% win rate",
            )

        return "\n".join(lines)
