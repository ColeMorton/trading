#!/usr/bin/env python3
"""
BTC-USD 1093-Day Buy-and-Hold Profitability Analysis

Financial research to determine what percentage of days would result in profit
if a buyer purchased BTC-USD and held for exactly 1093 days.

This analysis performs a rolling buy-and-hold simulation across the entire
historical dataset to answer the question with statistical confidence.

Author: Financial Research Analysis
Date: 2025-09-23
"""

import json
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import bootstrap


warnings.filterwarnings("ignore")


class BTC1093DayHoldAnalyzer:
    """Analyzer for BTC-USD 1093-day buy-and-hold profitability analysis."""

    def __init__(self, data_path: str = "data/raw/prices/BTC-USD_D.csv"):
        """Initialize analyzer with data path."""
        self.data_path = Path(data_path)
        self.hold_period = 1093  # Exactly 1093 days
        self.results = {}

    def load_price_data(self) -> pd.DataFrame | None:
        """Load BTC-USD daily price data."""
        try:
            if not self.data_path.exists():
                print(f"❌ Error: Data file not found at {self.data_path}")
                return None

            df = pd.read_csv(self.data_path)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)

            # Sort by date to ensure chronological order
            df = df.sort_index()

            print(f"✅ Loaded BTC-USD price data: {len(df)} days")
            print(
                f"📅 Date range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}"
            )

            return df

        except Exception as e:
            print(f"❌ Error loading price data: {e}")
            return None

    def calculate_rolling_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate rolling 1093-day buy-and-hold returns for each possible entry date.

        Returns DataFrame with columns: entry_date, exit_date, entry_price, exit_price, return_pct, is_profitable
        """
        results = []

        # Calculate the latest possible entry date (must have 1093 days of future data)
        # If we have N data points, the last entry that allows for 1093-day hold is at index N-1093-1
        latest_entry_idx = len(df) - self.hold_period - 1

        if latest_entry_idx < 0:
            print(
                f"❌ Error: Insufficient data. Need at least {self.hold_period} days."
            )
            return pd.DataFrame()

        print(
            f"🔄 Calculating returns for {latest_entry_idx + 1} possible entry dates..."
        )

        for i in range(latest_entry_idx + 1):
            entry_date = df.index[i]
            exit_date = df.index[i + self.hold_period]

            entry_price = df.iloc[i]["Close"]
            exit_price = df.iloc[i + self.hold_period]["Close"]

            # Calculate return percentage
            return_pct = (exit_price - entry_price) / entry_price * 100
            is_profitable = return_pct > 0

            results.append(
                {
                    "entry_date": entry_date,
                    "exit_date": exit_date,
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "return_pct": return_pct,
                    "is_profitable": is_profitable,
                }
            )

            # Progress indicator for large datasets
            if (i + 1) % 500 == 0 or i == latest_entry_idx:
                print(
                    f"    Processed {i + 1:,} / {latest_entry_idx + 1:,} entry dates ({(i + 1) / (latest_entry_idx + 1) * 100:.1f}%)"
                )

        return pd.DataFrame(results)

    def calculate_statistics(self, returns_df: pd.DataFrame) -> dict:
        """Calculate comprehensive statistics from the rolling returns."""
        if returns_df.empty:
            return {"error": "No data available for analysis"}

        returns = returns_df["return_pct"].values
        profitable_mask = returns_df["is_profitable"].values

        # Basic statistics
        total_periods = len(returns)
        profitable_periods = np.sum(profitable_mask)
        profit_percentage = profitable_periods / total_periods * 100

        # Return statistics
        mean_return = np.mean(returns)
        median_return = np.median(returns)
        std_return = np.std(returns)
        min_return = np.min(returns)
        max_return = np.max(returns)

        # Profitable periods statistics
        profitable_returns = returns[profitable_mask]
        if len(profitable_returns) > 0:
            mean_profitable_return = np.mean(profitable_returns)
            min_profitable_return = np.min(profitable_returns)
        else:
            mean_profitable_return = 0
            min_profitable_return = 0

        # Loss periods statistics
        loss_mask = ~profitable_mask
        loss_returns = returns[loss_mask]
        if len(loss_returns) > 0:
            mean_loss_return = np.mean(loss_returns)
            worst_loss_return = np.min(loss_returns)
            loss_periods = len(loss_returns)
        else:
            mean_loss_return = 0
            worst_loss_return = 0
            loss_periods = 0

        # Percentiles
        percentiles = [5, 10, 25, 75, 90, 95]
        return_percentiles = {f"p{p}": np.percentile(returns, p) for p in percentiles}

        # Risk metrics
        sharpe_ratio = mean_return / std_return if std_return != 0 else 0

        return {
            "total_periods": total_periods,
            "profitable_periods": profitable_periods,
            "loss_periods": loss_periods,
            "profit_percentage": profit_percentage,
            "mean_return_pct": mean_return,
            "median_return_pct": median_return,
            "std_return_pct": std_return,
            "min_return_pct": min_return,
            "max_return_pct": max_return,
            "mean_profitable_return_pct": mean_profitable_return,
            "min_profitable_return_pct": min_profitable_return,
            "mean_loss_return_pct": mean_loss_return,
            "worst_loss_return_pct": worst_loss_return,
            "sharpe_ratio": sharpe_ratio,
            "percentiles": return_percentiles,
            "date_range": {
                "first_entry": returns_df["entry_date"].iloc[0].strftime("%Y-%m-%d"),
                "last_entry": returns_df["entry_date"].iloc[-1].strftime("%Y-%m-%d"),
                "last_exit": returns_df["exit_date"].iloc[-1].strftime("%Y-%m-%d"),
            },
        }

    def calculate_confidence_intervals(
        self, returns_df: pd.DataFrame, confidence_level: float = 0.95
    ) -> dict:
        """Calculate confidence intervals for profit percentage using bootstrap sampling."""
        if returns_df.empty:
            return {"error": "No data available for confidence interval calculation"}

        def profit_percentage_statistic(sample):
            """Calculate profit percentage for a bootstrap sample."""
            return np.mean(sample > 0) * 100

        # Prepare data for bootstrap
        returns = returns_df["return_pct"].values

        # Perform bootstrap sampling
        n_bootstrap = 10000
        rng = np.random.default_rng(42)  # Fixed seed for reproducibility

        # Use scipy.stats.bootstrap for robust confidence intervals
        bootstrap_result = bootstrap(
            (returns,),
            profit_percentage_statistic,
            n_resamples=n_bootstrap,
            confidence_level=confidence_level,
            random_state=rng,
            method="percentile",
        )

        ci_lower = bootstrap_result.confidence_interval.low
        ci_upper = bootstrap_result.confidence_interval.high

        # Additional manual bootstrap for more detailed statistics
        bootstrap_samples = []
        for _ in range(n_bootstrap):
            sample_indices = rng.choice(len(returns), size=len(returns), replace=True)
            sample = returns[sample_indices]
            profit_pct = np.mean(sample > 0) * 100
            bootstrap_samples.append(profit_pct)

        bootstrap_samples = np.array(bootstrap_samples)

        return {
            "confidence_level": confidence_level,
            "confidence_interval": {"lower": ci_lower, "upper": ci_upper},
            "bootstrap_statistics": {
                "mean": np.mean(bootstrap_samples),
                "std": np.std(bootstrap_samples),
                "min": np.min(bootstrap_samples),
                "max": np.max(bootstrap_samples),
            },
            "n_bootstrap_samples": n_bootstrap,
        }

    def analyze_temporal_patterns(self, returns_df: pd.DataFrame) -> dict:
        """Analyze profitability patterns across time periods."""
        if returns_df.empty:
            return {"error": "No data available for temporal analysis"}

        # Add year column for yearly analysis
        returns_df = returns_df.copy()
        returns_df["entry_year"] = returns_df["entry_date"].dt.year

        # Yearly profitability analysis
        yearly_stats = []
        for year in sorted(returns_df["entry_year"].unique()):
            year_data = returns_df[returns_df["entry_year"] == year]
            if len(year_data) > 0:
                profit_pct = np.mean(year_data["is_profitable"]) * 100
                avg_return = np.mean(year_data["return_pct"])
                yearly_stats.append(
                    {
                        "year": year,
                        "entries": len(year_data),
                        "profit_percentage": profit_pct,
                        "avg_return_pct": avg_return,
                    }
                )

        # Market cycle analysis (rough approximation based on years)
        bear_years = [2014, 2015, 2018, 2022]  # Known bear market years
        bull_years = [2016, 2017, 2019, 2020, 2021]  # Known bull market years

        bear_data = returns_df[returns_df["entry_year"].isin(bear_years)]
        bull_data = returns_df[returns_df["entry_year"].isin(bull_years)]

        cycle_analysis = {}
        if len(bear_data) > 0:
            cycle_analysis["bear_market_entries"] = {
                "count": len(bear_data),
                "profit_percentage": np.mean(bear_data["is_profitable"]) * 100,
                "avg_return_pct": np.mean(bear_data["return_pct"]),
            }

        if len(bull_data) > 0:
            cycle_analysis["bull_market_entries"] = {
                "count": len(bull_data),
                "profit_percentage": np.mean(bull_data["is_profitable"]) * 100,
                "avg_return_pct": np.mean(bull_data["return_pct"]),
            }

        return {
            "yearly_analysis": yearly_stats,
            "market_cycle_analysis": cycle_analysis,
        }

    def run_full_analysis(self) -> dict:
        """Run the complete 1093-day buy-and-hold analysis."""
        print("🚀 Starting BTC-USD 1093-Day Buy-and-Hold Profitability Analysis")
        print("=" * 80)

        # Load data
        price_data = self.load_price_data()
        if price_data is None:
            return {"error": "Failed to load price data"}

        # Calculate rolling returns
        print("\n📊 Calculating rolling 1093-day returns...")
        returns_df = self.calculate_rolling_returns(price_data)
        if returns_df.empty:
            return {"error": "Failed to calculate rolling returns"}

        # Calculate statistics
        print("\n🔢 Calculating comprehensive statistics...")
        statistics = self.calculate_statistics(returns_df)

        # Calculate confidence intervals
        print("\n📈 Calculating confidence intervals...")
        confidence_intervals = self.calculate_confidence_intervals(returns_df)

        # Analyze temporal patterns
        print("\n📅 Analyzing temporal patterns...")
        temporal_analysis = self.analyze_temporal_patterns(returns_df)

        # Compile results
        results = {
            "analysis_metadata": {
                "hold_period_days": self.hold_period,
                "analysis_date": datetime.now().isoformat(),
                "data_source": str(self.data_path),
            },
            "statistics": statistics,
            "confidence_intervals": confidence_intervals,
            "temporal_analysis": temporal_analysis,
            "raw_data_summary": {
                "total_price_data_points": len(price_data),
                "total_analysis_periods": len(returns_df),
                "data_utilization_pct": len(returns_df) / len(price_data) * 100,
            },
        }

        print("\n✅ Analysis complete!")
        return results

    def generate_report(self, analysis_results: dict) -> str:
        """Generate a comprehensive financial research report."""
        if "error" in analysis_results:
            return f"❌ Analysis Error: {analysis_results['error']}"

        stats = analysis_results["statistics"]
        ci = analysis_results["confidence_intervals"]

        report = []
        report.append("=" * 100)
        report.append("BTC-USD 1093-DAY BUY-AND-HOLD PROFITABILITY ANALYSIS")
        report.append("=" * 100)
        report.append("")

        # Executive Summary
        report.append("🎯 EXECUTIVE SUMMARY")
        report.append("-" * 50)
        profit_pct = stats["profit_percentage"]
        ci_lower = ci["confidence_interval"]["lower"]
        ci_upper = ci["confidence_interval"]["upper"]

        report.append(
            f"✅ PRIMARY ANSWER: {profit_pct:.1f}% of days would be profitable"
        )
        report.append(
            f"📊 CONFIDENCE INTERVAL: {ci_lower:.1f}% - {ci_upper:.1f}% (95% confidence)"
        )
        report.append(
            f"🎲 TOTAL ANALYZED PERIODS: {stats['total_periods']:,} entry dates"
        )
        report.append(f"💰 PROFITABLE PERIODS: {stats['profitable_periods']:,} days")
        report.append(f"📉 LOSS PERIODS: {stats['loss_periods']:,} days")
        report.append("")

        # Key Financial Metrics
        report.append("📈 KEY FINANCIAL METRICS")
        report.append("-" * 50)
        report.append(f"Average Return: {stats['mean_return_pct']:+.1f}%")
        report.append(f"Median Return: {stats['median_return_pct']:+.1f}%")
        report.append(f"Standard Deviation: {stats['std_return_pct']:.1f}%")
        report.append(f"Best Case Return: {stats['max_return_pct']:+.1f}%")
        report.append(f"Worst Case Return: {stats['min_return_pct']:+.1f}%")
        report.append(f"Sharpe Ratio: {stats['sharpe_ratio']:.2f}")
        report.append("")

        # Risk Analysis
        report.append("⚠️ RISK ANALYSIS")
        report.append("-" * 50)
        if stats["loss_periods"] > 0:
            report.append(
                f"Average Loss When Unprofitable: {stats['mean_loss_return_pct']:+.1f}%"
            )
            report.append(f"Maximum Loss: {stats['worst_loss_return_pct']:+.1f}%")
        else:
            report.append("No loss periods identified in the analysis")

        report.append(f"5th Percentile Return: {stats['percentiles']['p5']:+.1f}%")
        report.append(f"10th Percentile Return: {stats['percentiles']['p10']:+.1f}%")
        report.append("")

        # Profitable Periods Analysis
        if stats["profitable_periods"] > 0:
            report.append("💰 PROFITABLE PERIODS ANALYSIS")
            report.append("-" * 50)
            report.append(
                f"Average Profit When Successful: {stats['mean_profitable_return_pct']:+.1f}%"
            )
            report.append(f"Minimum Profit: {stats['min_profitable_return_pct']:+.1f}%")
            report.append(
                f"75th Percentile Return: {stats['percentiles']['p75']:+.1f}%"
            )
            report.append(
                f"90th Percentile Return: {stats['percentiles']['p90']:+.1f}%"
            )
            report.append(
                f"95th Percentile Return: {stats['percentiles']['p95']:+.1f}%"
            )
            report.append("")

        # Data Coverage
        report.append("📅 DATA COVERAGE & METHODOLOGY")
        report.append("-" * 50)
        date_range = stats["date_range"]
        report.append(
            f"Analysis Period: {date_range['first_entry']} to {date_range['last_entry']}"
        )
        report.append(f"Final Exit Date: {date_range['last_exit']}")
        report.append(
            f"Hold Period: {analysis_results['analysis_metadata']['hold_period_days']} days (~3.0 years)"
        )
        report.append(
            f"Bootstrap Samples: {ci['n_bootstrap_samples']:,} for confidence intervals"
        )
        report.append("")

        # Temporal Analysis
        if (
            "temporal_analysis" in analysis_results
            and "yearly_analysis" in analysis_results["temporal_analysis"]
        ):
            temporal = analysis_results["temporal_analysis"]
            report.append("📊 TEMPORAL PATTERNS")
            report.append("-" * 50)

            # Show best and worst years
            yearly_data = temporal["yearly_analysis"]
            if yearly_data:
                yearly_data_sorted = sorted(
                    yearly_data, key=lambda x: x["profit_percentage"]
                )
                worst_year = yearly_data_sorted[0]
                best_year = yearly_data_sorted[-1]

                report.append(
                    f"Best Entry Year: {best_year['year']} ({best_year['profit_percentage']:.1f}% profitable)"
                )
                report.append(
                    f"Worst Entry Year: {worst_year['year']} ({worst_year['profit_percentage']:.1f}% profitable)"
                )

            # Market cycle analysis
            if "market_cycle_analysis" in temporal:
                cycle = temporal["market_cycle_analysis"]
                if "bear_market_entries" in cycle:
                    bear = cycle["bear_market_entries"]
                    report.append(
                        f"Bear Market Entries: {bear['profit_percentage']:.1f}% profitable ({bear['count']} periods)"
                    )
                if "bull_market_entries" in cycle:
                    bull = cycle["bull_market_entries"]
                    report.append(
                        f"Bull Market Entries: {bull['profit_percentage']:.1f}% profitable ({bull['count']} periods)"
                    )
            report.append("")

        # Conclusions
        report.append("💡 KEY CONCLUSIONS")
        report.append("-" * 50)
        report.append(
            f"1. PROFITABILITY: {profit_pct:.1f}% of 1093-day holding periods resulted in profit"
        )
        report.append(
            f"2. CONFIDENCE: 95% confidence interval is {ci_lower:.1f}% - {ci_upper:.1f}%"
        )
        report.append(
            f"3. RISK-RETURN: Average {stats['mean_return_pct']:+.1f}% return with {stats['std_return_pct']:.1f}% volatility"
        )

        if stats["loss_periods"] == 0:
            report.append(
                "4. REMARKABLE: No loss periods identified over the analysis timeframe"
            )
        else:
            loss_rate = stats["loss_periods"] / stats["total_periods"] * 100
            report.append(
                f"4. RISK: {loss_rate:.1f}% chance of loss with worst case {stats['worst_loss_return_pct']:+.1f}%"
            )

        report.append("")
        report.append("=" * 100)

        return "\n".join(report)


def main():
    """Main execution function."""
    print("🚀 BTC-USD 1093-Day Buy-and-Hold Profitability Analysis")
    print(
        "📊 Analyzing what percentage of days would be profitable after 1093-day hold"
    )
    print()

    # Initialize analyzer
    analyzer = BTC1093DayHoldAnalyzer()

    # Run analysis
    results = analyzer.run_full_analysis()

    # Generate and display report
    print("\n")
    report = analyzer.generate_report(results)
    print(report)

    # Save results to JSON
    output_file = (
        f"btc_1093_day_hold_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
