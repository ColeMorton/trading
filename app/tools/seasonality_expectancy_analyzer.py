"""Seasonality expectancy analyzer for specific time periods."""

import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class SeasonalityExpectancyAnalyzer:
    """Analyzes seasonality data to find highest expectancy tickers for specific time periods."""

    def __init__(self, seasonality_dir: str = "data/raw/seasonality"):
        """Initialize the analyzer.

        Args:
            seasonality_dir: Directory containing seasonality CSV files
        """
        self.seasonality_dir = Path(seasonality_dir)
        self.results = []

    def analyze_july_august_expectancy(
        self,
        july_weight: float = 0.258,
        august_weight: float = 0.742,
        min_sample_size: int = 50,
        min_significance: float = 0.5,
        min_years: float = 3.0,
    ) -> pd.DataFrame:
        """Analyze expectancy for July 23 - August 23 time period.

        Args:
            july_weight: Weight for July return (days remaining in July)
            august_weight: Weight for August return (days in August)
            min_sample_size: Minimum sample size for reliable patterns
            min_significance: Minimum statistical significance threshold
            min_years: Minimum years of data required

        Returns:
            DataFrame with ranked expectancy analysis
        """
        print("🔍 Processing seasonality files...")

        # Get all seasonality CSV files (exclude summary files)
        csv_files = [
            f
            for f in self.seasonality_dir.glob("*.csv")
            if not f.name.endswith("_summary.csv")
        ]

        print(f"📊 Found {len(csv_files)} ticker files to analyze")

        for csv_file in csv_files:
            try:
                ticker = csv_file.stem.replace("_seasonality", "")
                result = self._analyze_ticker_file(
                    csv_file,
                    ticker,
                    july_weight,
                    august_weight,
                    min_sample_size,
                    min_significance,
                    min_years,
                )
                if result:
                    self.results.append(result)
            except Exception as e:
                print(f"⚠️  Error processing {csv_file.name}: {str(e)}")
                continue

        # Convert to DataFrame and rank
        if not self.results:
            print("❌ No valid results found")
            return pd.DataFrame()

        df = pd.DataFrame(self.results)
        df = df.sort_values("risk_adjusted_score", ascending=False).reset_index(
            drop=True
        )
        df["rank"] = df.index + 1

        return df

    def _analyze_ticker_file(
        self,
        csv_file: Path,
        ticker: str,
        july_weight: float,
        august_weight: float,
        min_sample_size: int,
        min_significance: float,
        min_years: float,
    ) -> Optional[Dict]:
        """Analyze a single ticker's seasonality file."""

        # Load data
        df = pd.read_csv(csv_file)

        # Extract relevant patterns
        july_monthly = df[(df["Pattern_Type"] == "Monthly") & (df["Period"] == "July")]
        august_monthly = df[
            (df["Pattern_Type"] == "Monthly") & (df["Period"] == "August")
        ]
        q3_quarterly = df[(df["Pattern_Type"] == "Quarterly") & (df["Period"] == "Q3")]

        # Validate data quality
        patterns_found = []
        if not july_monthly.empty:
            patterns_found.append(("July", july_monthly.iloc[0]))
        if not august_monthly.empty:
            patterns_found.append(("August", august_monthly.iloc[0]))
        if not q3_quarterly.empty:
            patterns_found.append(("Q3", q3_quarterly.iloc[0]))

        if len(patterns_found) < 2:  # Need at least July or August data
            return None

        # Calculate time-weighted expectancy
        combined_return = 0
        total_weight = 0
        win_rates = []
        significance_scores = []
        sample_sizes = []
        volatilities = []

        for period, row in patterns_found:
            if row["Sample_Size"] < min_sample_size:
                continue

            if period == "July":
                weight = july_weight
                combined_return += row["Average_Return"] * weight
                total_weight += weight
            elif period == "August":
                weight = august_weight
                combined_return += row["Average_Return"] * weight
                total_weight += weight
            elif period == "Q3" and row["Statistical_Significance"] > min_significance:
                # Q3 as supplementary signal (smaller weight)
                weight = 0.2
                combined_return += row["Average_Return"] * weight
                total_weight += weight

            win_rates.append(row["Win_Rate"])
            significance_scores.append(row["Statistical_Significance"])
            sample_sizes.append(row["Sample_Size"])
            volatilities.append(row["Std_Dev"])

        if total_weight == 0:
            return None

        # Normalize combined return
        combined_return = combined_return / min(total_weight, 1.0)

        # Calculate risk metrics
        avg_win_rate = np.mean(win_rates) if win_rates else 0
        avg_significance = np.mean(significance_scores) if significance_scores else 0
        avg_sample_size = np.mean(sample_sizes) if sample_sizes else 0
        avg_volatility = np.mean(volatilities) if volatilities else 0

        # Apply quality filters
        if avg_significance < min_significance:
            return None
        if avg_sample_size < min_sample_size:
            return None

        # Calculate risk-adjusted score
        risk_adjusted_score = self._calculate_risk_adjusted_score(
            combined_return, avg_significance, avg_win_rate, avg_volatility
        )

        # Determine asset class
        asset_class = self._classify_asset(ticker)

        # Calculate confidence level
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
            "patterns_used": len(patterns_found),
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
        win_rate_bonus = (win_rate - 0.5) * 0.4  # 60% win rate = +4% bonus
        score += win_rate_bonus

        # Volatility penalty (penalize high volatility)
        volatility_penalty = min(volatility * 0.1, 0.5)  # Cap penalty at 50%
        score -= volatility_penalty

        return score

    def _classify_asset(self, ticker: str) -> str:
        """Classify ticker into asset class."""
        if "-USD" in ticker:
            return "Crypto"
        elif ticker in [
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
        elif ticker == "GLD":
            return "Commodity"
        else:
            return "Stock"

    def _calculate_confidence(self, significance: float, sample_size: int) -> str:
        """Calculate confidence level based on statistical significance and sample size."""
        if significance > 0.8 and sample_size > 200:
            return "Very High"
        elif significance > 0.7 and sample_size > 100:
            return "High"
        elif significance > 0.6 and sample_size > 50:
            return "Medium"
        else:
            return "Low"

    def generate_report(self, results_df: pd.DataFrame, top_n: int = 20) -> str:
        """Generate formatted analysis report."""
        if results_df.empty:
            return "No results available for analysis."

        # Get top N results
        top_results = results_df.head(top_n)

        report_lines = [
            "🎯 SEASONALITY EXPECTANCY ANALYSIS",
            "=" * 50,
            f"📅 Analysis Period: July 23 - August 23, 2025",
            f"📊 Total Tickers Analyzed: {len(results_df)}",
            f"🏆 Top {top_n} Opportunities Shown",
            "",
            "📈 HIGHEST EXPECTANCY TICKERS",
            "-" * 50,
        ]

        # Add table header
        report_lines.append(
            f"{'Rank':<4} {'Ticker':<12} {'Exp Return':<11} {'Risk Score':<11} {'Win Rate':<9} {'Confidence':<11} {'Asset Class':<12}"
        )
        report_lines.append("-" * 80)

        # Add top results
        for _, row in top_results.iterrows():
            report_lines.append(
                f"{int(row['rank']):<4} "
                f"{row['ticker']:<12} "
                f"{row['expected_return']:+7.2f}%    "
                f"{row['risk_adjusted_score']:7.3f}     "
                f"{row['win_rate']:6.1%}   "
                f"{row['confidence']:<11} "
                f"{row['asset_class']:<12}"
            )

        # Add summary statistics
        report_lines.extend(
            [
                "",
                "📊 SUMMARY STATISTICS",
                "-" * 30,
                f"Average Expected Return: {results_df['expected_return'].mean():+.2f}%",
                f"Median Expected Return:  {results_df['expected_return'].median():+.2f}%",
                f"Best Opportunity:        {results_df.iloc[0]['ticker']} ({results_df.iloc[0]['expected_return']:+.2f}%)",
                f"Average Win Rate:        {results_df['win_rate'].mean():.1%}",
                "",
                "🏭 SECTOR DISTRIBUTION",
                "-" * 25,
            ]
        )

        # Add sector distribution
        sector_dist = top_results["asset_class"].value_counts()
        for asset_class, count in sector_dist.items():
            percentage = (count / len(top_results)) * 100
            report_lines.append(f"{asset_class}: {count} tickers ({percentage:.1f}%)")

        report_lines.extend(
            [
                "",
                "⚠️  RISK CONSIDERATIONS",
                "-" * 25,
                "• Past performance does not guarantee future results",
                "• Consider position sizing based on volatility",
                "• Monitor correlations for concentration risk",
                "• Seasonality patterns can change over time",
                "",
                f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ]
        )

        return "\n".join(report_lines)

    def save_detailed_results(
        self, results_df: pd.DataFrame, filename: str = None
    ) -> str:
        """Save detailed results to CSV file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"seasonality_expectancy_analysis_{timestamp}.csv"

        output_path = self.seasonality_dir / filename

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
        ]

        results_df[output_columns].to_csv(output_path, index=False)
        return str(output_path)


def main():
    """Main function to run the analysis."""
    print("🚀 Starting Seasonality Expectancy Analysis for July 23 - August 23, 2025")
    print("=" * 70)

    analyzer = SeasonalityExpectancyAnalyzer()

    # Run analysis
    results_df = analyzer.analyze_july_august_expectancy()

    if results_df.empty:
        print("❌ No valid results found. Check data availability and quality filters.")
        return

    # Generate and display report
    report = analyzer.generate_report(results_df, top_n=20)
    print(report)

    # Save detailed results
    csv_path = analyzer.save_detailed_results(results_df)
    print(f"\n💾 Detailed results saved to: {csv_path}")


if __name__ == "__main__":
    main()
