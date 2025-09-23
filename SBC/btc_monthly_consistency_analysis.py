#!/usr/bin/env python3
"""
BTC-USD Monthly Consistency Analysis

Financial research to identify the lowest MA period where BTC-USD price
has never decreased month over month.

Author: Financial Research Analysis
Date: 2025-09-21
"""

import json
import warnings
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class BTCMonthlyConsistencyAnalyzer:
    """Analyzer for finding optimal MA period with consistent monthly growth."""

    def __init__(self, data_dir: str = "data/raw/ma_cross/prices"):
        """Initialize analyzer with data directory."""
        self.data_dir = Path(data_dir)
        self.results = {}

    def load_ma_data(self, period: int) -> Optional[pd.DataFrame]:
        """Load MA data for specific period."""
        try:
            file_path = self.data_dir / f"BTC-USD_{period}.csv"
            if not file_path.exists():
                return None

            df = pd.read_csv(file_path)
            df["Date"] = pd.to_datetime(df["Date"])
            df.set_index("Date", inplace=True)
            return df

        except Exception as e:
            print(f"Error loading period {period}: {e}")
            return None

    def calculate_monthly_changes(self, df: pd.DataFrame) -> pd.Series:
        """Calculate month-over-month percentage changes."""
        # Resample to month-end prices using the Close price (MA value)
        monthly_prices = df["Close"].resample("M").last()

        # Calculate month-over-month percentage changes
        monthly_returns = monthly_prices.pct_change().dropna()

        return monthly_returns

    def analyze_period_consistency(self, period: int) -> Dict:
        """Analyze monthly consistency for a specific MA period."""
        # Load data
        df = self.load_ma_data(period)
        if df is None:
            return {
                "period": period,
                "status": "data_error",
                "error": "Could not load data",
            }

        # Calculate monthly changes
        monthly_returns = self.calculate_monthly_changes(df)

        if len(monthly_returns) == 0:
            return {
                "period": period,
                "status": "insufficient_data",
                "error": "No monthly data available",
            }

        # Analyze consistency
        negative_months = monthly_returns[monthly_returns < 0]
        declining_count = len(negative_months)
        total_months = len(monthly_returns)

        # Calculate statistics
        worst_decline = negative_months.min() if len(negative_months) > 0 else 0.0
        consistency_ratio = (total_months - declining_count) / total_months
        monthly_volatility = monthly_returns.std()
        avg_monthly_return = monthly_returns.mean()

        # Determine if consistent (no declining months)
        is_consistent = declining_count == 0

        return {
            "period": period,
            "status": "analyzed",
            "is_consistent": is_consistent,
            "declining_months": declining_count,
            "total_months": total_months,
            "worst_decline_pct": worst_decline * 100,
            "consistency_ratio": consistency_ratio,
            "monthly_volatility": monthly_volatility * 100,
            "avg_monthly_return_pct": avg_monthly_return * 100,
            "data_start": df.index[0].strftime("%Y-%m-%d"),
            "data_end": df.index[-1].strftime("%Y-%m-%d"),
            "data_points": len(df),
        }

    def get_available_periods(self) -> List[int]:
        """Get list of available MA periods."""
        periods = []
        for file_path in self.data_dir.glob("BTC-USD_*.csv"):
            try:
                period = int(file_path.stem.split("_")[1])
                periods.append(period)
            except (ValueError, IndexError):
                continue

        return sorted(periods)

    def find_first_consistent_period(self, max_periods_to_test: int = None) -> Dict:
        """Find the first (lowest) period with consistent monthly growth."""
        available_periods = self.get_available_periods()

        if max_periods_to_test:
            available_periods = available_periods[:max_periods_to_test]

        print(
            f"🔍 Analyzing {len(available_periods)} MA periods for monthly consistency..."
        )
        print(f"📊 Period range: {min(available_periods)} to {max(available_periods)}")
        print("=" * 80)

        results = []
        first_consistent = None

        for i, period in enumerate(available_periods, 1):
            print(
                f"[{i:3d}/{len(available_periods):3d}] Testing Period {period:4d}...",
                end=" ",
            )

            result = self.analyze_period_consistency(period)
            results.append(result)

            if result["status"] == "analyzed":
                if result["is_consistent"]:
                    print(f"✅ CONSISTENT (0 declining months)")
                    if first_consistent is None:
                        first_consistent = result
                        print(f"🎯 FIRST CONSISTENT PERIOD FOUND: {period}")
                        break
                else:
                    declining = result["declining_months"]
                    worst = result["worst_decline_pct"]
                    print(f"❌ {declining:2d} declining months (worst: {worst:+6.2f}%)")
            else:
                print(f"⚠️  {result['status']}")

        return {
            "first_consistent_period": first_consistent,
            "all_results": results,
            "total_periods_tested": len(results),
            "analysis_date": datetime.now().isoformat(),
        }

    def generate_detailed_report(self, analysis_results: Dict) -> str:
        """Generate detailed financial research report."""
        report = []
        report.append("=" * 100)
        report.append("BTC-USD MONTHLY CONSISTENCY RESEARCH ANALYSIS")
        report.append("=" * 100)
        report.append("")

        # Executive Summary
        first_consistent = analysis_results["first_consistent_period"]
        total_tested = analysis_results["total_periods_tested"]

        if first_consistent:
            optimal_period = first_consistent["period"]
            report.append("🎯 EXECUTIVE SUMMARY")
            report.append("-" * 50)
            report.append(f"✅ OPTIMAL MA PERIOD FOUND: {optimal_period} days")
            report.append(
                f"📊 This is the lowest period achieving 100% monthly consistency"
            )
            report.append(f"🔍 Tested {total_tested} different MA periods")
            report.append("")

            # Key Metrics for Optimal Period
            report.append("📈 KEY METRICS FOR OPTIMAL PERIOD")
            report.append("-" * 50)
            report.append(f"Period: {optimal_period} days")
            report.append(f"Total Months Analyzed: {first_consistent['total_months']}")
            report.append(
                f"Declining Months: {first_consistent['declining_months']} (0%)"
            )
            report.append(
                f"Consistency Ratio: {first_consistent['consistency_ratio']:.1%}"
            )
            report.append(
                f"Average Monthly Return: {first_consistent['avg_monthly_return_pct']:+.2f}%"
            )
            report.append(
                f"Monthly Volatility: {first_consistent['monthly_volatility']:.2f}%"
            )
            report.append(
                f"Data Period: {first_consistent['data_start']} to {first_consistent['data_end']}"
            )
            report.append(f"Data Points: {first_consistent['data_points']:,} days")
            report.append("")
        else:
            report.append("❌ NO CONSISTENT PERIOD FOUND")
            report.append(
                f"🔍 Tested {total_tested} periods, none achieved 100% monthly consistency"
            )
            report.append("")

        # Detailed Analysis Results
        report.append("📋 DETAILED ANALYSIS RESULTS")
        report.append("-" * 50)
        report.append(
            f"{'Period':<8} {'Status':<12} {'Declining':<10} {'Worst Drop':<12} {'Consistency':<12} {'Volatility':<10}"
        )
        report.append("-" * 80)

        analyzed_results = [
            r for r in analysis_results["all_results"] if r["status"] == "analyzed"
        ]

        for result in analyzed_results[:20]:  # Show first 20 for readability
            period = result["period"]
            declining = result["declining_months"]
            worst = result["worst_decline_pct"]
            consistency = result["consistency_ratio"]
            volatility = result["monthly_volatility"]
            status = "✅ PASS" if result["is_consistent"] else "❌ FAIL"

            report.append(
                f"{period:<8} {status:<12} {declining:<10} {worst:+6.2f}%     {consistency:<11.1%} {volatility:<9.2f}%"
            )

        if len(analyzed_results) > 20:
            report.append(f"... and {len(analyzed_results) - 20} more periods analyzed")

        report.append("")

        # Financial Insights
        report.append("💡 FINANCIAL INSIGHTS")
        report.append("-" * 50)

        if first_consistent:
            optimal_period = first_consistent["period"]
            avg_return = first_consistent["avg_monthly_return_pct"]
            volatility = first_consistent["monthly_volatility"]

            report.append(
                f"• Minimum Smoothing Required: {optimal_period} days (~{optimal_period/30:.1f} months)"
            )
            report.append(
                f"• Monthly Performance: {avg_return:+.2f}% average return with {volatility:.2f}% volatility"
            )
            report.append(
                f"• Risk Profile: Eliminates all monthly drawdowns while preserving trend"
            )
            report.append(
                f"• Strategic Value: Optimal for monthly rebalancing strategies"
            )
            report.append(
                f"• Market Insight: Bitcoin requires {optimal_period}-day smoothing for consistent monthly appreciation"
            )
        else:
            report.append(
                "• No period achieved perfect monthly consistency in the tested range"
            )
            report.append("• Consider testing longer MA periods (>1460 days)")
            report.append(
                "• Bitcoin's volatility may require extreme smoothing for perfect consistency"
            )

        report.append("")
        report.append("=" * 100)

        return "\n".join(report)


def main():
    """Main execution function."""
    print("🚀 Starting BTC-USD Monthly Consistency Analysis")
    print("📁 Data source: data/raw/ma_cross/prices/")
    print()

    # Initialize analyzer
    analyzer = BTCMonthlyConsistencyAnalyzer()

    # Run analysis
    results = analyzer.find_first_consistent_period()

    # Generate and display report
    print("\n")
    report = analyzer.generate_detailed_report(results)
    print(report)

    # Save results to JSON
    output_file = f"btc_monthly_consistency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed results saved to: {output_file}")


if __name__ == "__main__":
    main()
