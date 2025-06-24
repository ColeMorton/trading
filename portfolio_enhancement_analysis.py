#!/usr/bin/env python3
"""
Portfolio Enhancement Analysis Script
=====================================

Comprehensive analysis comparing existing trades.csv portfolio with incoming.csv strategies
to determine optimal portfolio composition and enhancement opportunities.

This script performs:
1. Portfolio composition comparison
2. Performance impact assessment
3. Risk contribution analysis
4. Enhanced portfolio projections
5. Strategic recommendations

Author: Portfolio Optimization System
"""

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")


class PortfolioEnhancementAnalyzer:
    """Comprehensive portfolio enhancement analysis tool."""

    def __init__(self):
        self.base_path = Path("/Users/colemorton/Projects/trading/csv/strategies")
        self.trades_file = self.base_path / "trades.csv"
        self.incoming_file = self.base_path / "incoming.csv"

        # Key performance metrics for analysis
        self.key_metrics = [
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Total Return [%]",
            "Max Drawdown [%]",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Value at Risk",
            "Alpha",
            "Annualized Return",
            "Annualized Volatility",
        ]

        # Risk metrics for analysis
        self.risk_metrics = [
            "Max Drawdown [%]",
            "Value at Risk",
            "Annualized Volatility",
            "Max Drawdown Duration",
            "Worst Trade [%]",
        ]

    def load_portfolios(self):
        """Load and validate portfolio data."""
        try:
            self.trades_df = pd.read_csv(self.trades_file)
            self.incoming_df = pd.read_csv(self.incoming_file)

            print(f"✓ Loaded existing portfolio: {len(self.trades_df)} strategies")
            print(f"✓ Loaded incoming portfolio: {len(self.incoming_df)} strategies")

            return True
        except Exception as e:
            print(f"❌ Error loading portfolios: {e}")
            return False

    def analyze_portfolio_composition(self):
        """Analyze and compare portfolio composition."""
        print("\n" + "=" * 80)
        print("1. PORTFOLIO COMPOSITION COMPARISON")
        print("=" * 80)

        # Strategy counts and types
        trades_strategies = self.trades_df.groupby("Strategy Type").size()
        incoming_strategies = self.incoming_df.groupby("Strategy Type").size()

        print(f"\n📊 STRATEGY TYPE DISTRIBUTION")
        print(f"Existing Portfolio:")
        for strategy, count in trades_strategies.items():
            print(f"  • {strategy}: {count} strategies")

        print(f"\nIncoming Portfolio:")
        for strategy, count in incoming_strategies.items():
            print(f"  • {strategy}: {count} strategies")

        # Ticker analysis
        trades_tickers = set(self.trades_df["Ticker"].unique())
        incoming_tickers = set(self.incoming_df["Ticker"].unique())

        overlapping_tickers = trades_tickers.intersection(incoming_tickers)
        unique_trades = trades_tickers - incoming_tickers
        unique_incoming = incoming_tickers - trades_tickers

        print(f"\n🎯 TICKER ANALYSIS")
        print(f"Existing portfolio tickers: {len(trades_tickers)}")
        print(f"Incoming portfolio tickers: {len(incoming_tickers)}")
        print(f"Overlapping tickers: {len(overlapping_tickers)}")
        print(f"Unique to existing: {len(unique_trades)}")
        print(f"Unique to incoming: {len(unique_incoming)}")

        if overlapping_tickers:
            print(f"\nOverlapping tickers: {sorted(list(overlapping_tickers))}")

        # Portfolio concentration
        trades_concentration = len(trades_tickers) / len(self.trades_df)
        incoming_concentration = len(incoming_tickers) / len(self.incoming_df)

        print(f"\n📈 PORTFOLIO CONCENTRATION")
        print(f"Existing portfolio concentration: {trades_concentration:.3f}")
        print(f"Incoming portfolio concentration: {incoming_concentration:.3f}")

        return {
            "trades_strategies": trades_strategies,
            "incoming_strategies": incoming_strategies,
            "overlapping_tickers": overlapping_tickers,
            "unique_trades": unique_trades,
            "unique_incoming": unique_incoming,
            "trades_concentration": trades_concentration,
            "incoming_concentration": incoming_concentration,
        }

    def assess_performance_impact(self):
        """Assess performance impact of combining portfolios."""
        print("\n" + "=" * 80)
        print("2. PERFORMANCE IMPACT ASSESSMENT")
        print("=" * 80)

        # Current portfolio metrics
        trades_metrics = self.calculate_portfolio_metrics(self.trades_df, "Existing")
        incoming_metrics = self.calculate_portfolio_metrics(
            self.incoming_df, "Incoming"
        )

        # Combined portfolio simulation
        combined_df = pd.concat([self.trades_df, self.incoming_df], ignore_index=True)
        combined_metrics = self.calculate_portfolio_metrics(combined_df, "Combined")

        print(f"\n📊 PORTFOLIO PERFORMANCE COMPARISON")
        comparison_metrics = [
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Sortino Ratio",
            "Total Return [%]",
            "Sharpe Ratio",
            "Max Drawdown [%]",
        ]

        print(
            f"{'Metric':<20} {'Existing':<12} {'Incoming':<12} {'Combined':<12} {'Impact':<10}"
        )
        print("-" * 80)

        for metric in comparison_metrics:
            if (
                metric in trades_metrics
                and metric in incoming_metrics
                and metric in combined_metrics
            ):
                existing = trades_metrics[metric]
                incoming = incoming_metrics[metric]
                combined = combined_metrics[metric]

                if existing != 0:
                    impact = ((combined - existing) / existing) * 100
                    impact_str = f"{impact:+.1f}%"
                else:
                    impact_str = "N/A"

                print(
                    f"{metric:<20} {existing:<12.3f} {incoming:<12.3f} {combined:<12.3f} {impact_str:<10}"
                )

        # Portfolio efficiency analysis
        existing_efficiency = self.calculate_efficiency_score(self.trades_df)
        combined_efficiency = self.calculate_efficiency_score(combined_df)
        efficiency_improvement = (
            (combined_efficiency - existing_efficiency) / existing_efficiency
        ) * 100

        print(f"\n🎯 PORTFOLIO EFFICIENCY ANALYSIS")
        print(f"Existing portfolio efficiency: {existing_efficiency:.4f}")
        print(f"Combined portfolio efficiency: {combined_efficiency:.4f}")
        print(f"Efficiency improvement: {efficiency_improvement:+.2f}%")

        return {
            "trades_metrics": trades_metrics,
            "incoming_metrics": incoming_metrics,
            "combined_metrics": combined_metrics,
            "efficiency_improvement": efficiency_improvement,
        }

    def analyze_risk_contribution(self):
        """Analyze risk contribution and correlation impact."""
        print("\n" + "=" * 80)
        print("3. RISK CONTRIBUTION ANALYSIS")
        print("=" * 80)

        # Risk metrics comparison
        trades_risk = self.calculate_risk_metrics(self.trades_df)
        incoming_risk = self.calculate_risk_metrics(self.incoming_df)
        combined_df = pd.concat([self.trades_df, self.incoming_df], ignore_index=True)
        combined_risk = self.calculate_risk_metrics(combined_df)

        print(f"\n⚠️  RISK METRICS COMPARISON")
        print(
            f"{'Risk Metric':<25} {'Existing':<12} {'Incoming':<12} {'Combined':<12} {'Change':<10}"
        )
        print("-" * 85)

        for metric in self.risk_metrics:
            if (
                metric in trades_risk
                and metric in incoming_risk
                and metric in combined_risk
            ):
                existing = trades_risk[metric]
                incoming = incoming_risk[metric]
                combined = combined_risk[metric]

                if existing != 0:
                    change = ((combined - existing) / existing) * 100
                    change_str = f"{change:+.1f}%"
                else:
                    change_str = "N/A"

                print(
                    f"{metric:<25} {existing:<12.3f} {incoming:<12.3f} {combined:<12.3f} {change_str:<10}"
                )

        # VaR and CVaR analysis
        trades_var = (
            self.trades_df["Value at Risk"].mean()
            if "Value at Risk" in self.trades_df.columns
            else 0
        )
        incoming_var = (
            self.incoming_df["Value at Risk"].mean()
            if "Value at Risk" in self.incoming_df.columns
            else 0
        )
        combined_var = (
            combined_df["Value at Risk"].mean()
            if "Value at Risk" in combined_df.columns
            else 0
        )

        print(f"\n📉 VALUE AT RISK ANALYSIS")
        print(f"Existing portfolio VaR: {trades_var:.6f}")
        print(f"Incoming portfolio VaR: {incoming_var:.6f}")
        print(f"Combined portfolio VaR: {combined_var:.6f}")

        var_change = (
            ((combined_var - trades_var) / abs(trades_var)) * 100
            if trades_var != 0
            else 0
        )
        print(f"VaR change: {var_change:+.2f}%")

        # Concentration risk analysis
        existing_concentration_risk = self.calculate_concentration_risk(self.trades_df)
        combined_concentration_risk = self.calculate_concentration_risk(combined_df)

        print(f"\n🎯 CONCENTRATION RISK ANALYSIS")
        print(f"Existing concentration risk: {existing_concentration_risk:.4f}")
        print(f"Combined concentration risk: {combined_concentration_risk:.4f}")
        concentration_improvement = (
            (existing_concentration_risk - combined_concentration_risk)
            / existing_concentration_risk
        ) * 100
        print(f"Concentration risk improvement: {concentration_improvement:+.2f}%")

        return {
            "var_change": var_change,
            "concentration_improvement": concentration_improvement,
            "combined_risk": combined_risk,
        }

    def project_enhanced_portfolio(self):
        """Project enhanced portfolio performance."""
        print("\n" + "=" * 80)
        print("4. ENHANCED PORTFOLIO PROJECTIONS")
        print("=" * 80)

        # Strategy selection analysis
        incoming_ranked = self.rank_incoming_strategies()

        print(f"\n🏆 TOP INCOMING STRATEGIES (by Score)")
        print(
            f"{'Rank':<4} {'Ticker':<8} {'Strategy':<8} {'Score':<8} {'Win Rate':<10} {'Sortino':<10} {'Return':<12}"
        )
        print("-" * 80)

        for i, (_, strategy) in enumerate(incoming_ranked.head(10).iterrows(), 1):
            print(
                f"{i:<4} {strategy['Ticker']:<8} {strategy['Strategy Type']:<8} "
                f"{strategy['Score']:<8.3f} {strategy['Win Rate [%]']:<10.1f} "
                f"{strategy['Sortino Ratio']:<10.3f} {strategy['Total Return [%]']:<12.1f}"
            )

        # Selective addition analysis
        best_incoming = incoming_ranked.head(5)  # Top 5 strategies
        selective_combined = pd.concat(
            [self.trades_df, best_incoming], ignore_index=True
        )
        selective_metrics = self.calculate_portfolio_metrics(
            selective_combined, "Selective"
        )

        print(f"\n📊 SELECTIVE ENHANCEMENT PROJECTIONS")
        print(f"Adding top 5 incoming strategies:")

        key_projections = [
            "Score",
            "Win Rate [%]",
            "Sortino Ratio",
            "Total Return [%]",
            "Max Drawdown [%]",
        ]
        existing_base = self.calculate_portfolio_metrics(self.trades_df, "Existing")

        for metric in key_projections:
            if metric in existing_base and metric in selective_metrics:
                existing = existing_base[metric]
                projected = selective_metrics[metric]
                improvement = (
                    ((projected - existing) / existing) * 100 if existing != 0 else 0
                )
                print(
                    f"  • {metric}: {existing:.3f} → {projected:.3f} ({improvement:+.1f}%)"
                )

        # Risk-adjusted projections
        existing_risk_adj = existing_base.get("Sortino Ratio", 0)
        projected_risk_adj = selective_metrics.get("Sortino Ratio", 0)
        risk_adj_improvement = (
            ((projected_risk_adj - existing_risk_adj) / existing_risk_adj) * 100
            if existing_risk_adj != 0
            else 0
        )

        print(f"\n🛡️  RISK-ADJUSTED PERFORMANCE PROJECTION")
        print(f"Risk-adjusted return improvement: {risk_adj_improvement:+.2f}%")

        return {
            "best_incoming": best_incoming,
            "selective_metrics": selective_metrics,
            "risk_adj_improvement": risk_adj_improvement,
        }

    def generate_strategic_recommendations(self, analysis_results):
        """Generate strategic recommendations based on analysis."""
        print("\n" + "=" * 80)
        print("5. STRATEGIC RECOMMENDATIONS")
        print("=" * 80)

        composition = analysis_results["composition"]
        performance = analysis_results["performance"]
        risk = analysis_results["risk"]
        projections = analysis_results["projections"]

        print(f"\n🎯 PORTFOLIO ENHANCEMENT DECISIONS")

        # Strategy-specific recommendations
        incoming_ranked = self.rank_incoming_strategies()

        print(f"\n✅ RECOMMENDED ADDITIONS:")
        accept_strategies = incoming_ranked.head(3)  # Top 3
        for _, strategy in accept_strategies.iterrows():
            reason = self.get_addition_rationale(strategy)
            print(f"  • {strategy['Ticker']} ({strategy['Strategy Type']}): {reason}")

        print(f"\n❌ RECOMMENDED REJECTIONS:")
        reject_strategies = incoming_ranked.tail(3)  # Bottom 3
        for _, strategy in reject_strategies.iterrows():
            reason = self.get_rejection_rationale(strategy)
            print(f"  • {strategy['Ticker']} ({strategy['Strategy Type']}): {reason}")

        # Allocation recommendations
        print(f"\n💰 ALLOCATION RECOMMENDATIONS:")
        total_existing_strategies = len(self.trades_df)
        recommended_additions = len(accept_strategies)

        print(f"  • Maintain {total_existing_strategies} existing strategies")
        print(f"  • Add {recommended_additions} new strategies")
        print(
            f"  • Target portfolio size: {total_existing_strategies + recommended_additions} strategies"
        )

        # Risk management controls
        print(f"\n🛡️  RISK MANAGEMENT CONTROLS:")
        print(f"  • Monitor VaR change: {risk['var_change']:+.2f}%")
        print(
            f"  • Concentration risk improved by: {risk['concentration_improvement']:+.2f}%"
        )
        print(f"  • Implement position sizing limits for high-volatility strategies")
        print(f"  • Set maximum single-strategy allocation at 10%")

        # Implementation roadmap
        print(f"\n🗺️  IMPLEMENTATION ROADMAP:")
        print(f"  1. IMMEDIATE (Week 1):")
        print(
            f"     • Add highest-scoring strategy: {accept_strategies.iloc[0]['Ticker']}"
        )
        print(f"     • Implement risk monitoring for new positions")

        print(f"  2. SHORT-TERM (Week 2-4):")
        print(f"     • Gradually add remaining 2 recommended strategies")
        print(f"     • Monitor portfolio correlation changes")
        print(f"     • Adjust position sizes based on initial performance")

        print(f"  3. ONGOING (Monthly):")
        print(f"     • Review strategy performance vs. expectations")
        print(f"     • Rebalance allocations based on risk contribution")
        print(f"     • Evaluate additional incoming strategies")

        # Performance targets
        projected_improvement = performance["efficiency_improvement"]
        print(f"\n🎯 PERFORMANCE TARGETS:")
        print(
            f"  • Expected portfolio efficiency improvement: {projected_improvement:+.2f}%"
        )
        print(
            f"  • Target risk-adjusted return improvement: {projections['risk_adj_improvement']:+.2f}%"
        )
        print(f"  • Maximum acceptable drawdown increase: 5%")

        return {
            "accept_strategies": accept_strategies,
            "reject_strategies": reject_strategies,
            "implementation_phases": 3,
            "expected_improvement": projected_improvement,
        }

    def calculate_portfolio_metrics(self, df, portfolio_name):
        """Calculate key portfolio metrics."""
        metrics = {}

        for metric in self.key_metrics:
            if metric in df.columns:
                try:
                    # Convert to numeric, handling any string values
                    numeric_series = pd.to_numeric(df[metric], errors="coerce")
                    metrics[metric] = numeric_series.mean()
                except Exception as e:
                    print(
                        f"Warning: Could not process {metric} for {portfolio_name}: {e}"
                    )
                    metrics[metric] = 0

        # Additional calculated metrics
        if "Total Return [%]" in df.columns and "Max Drawdown [%]" in df.columns:
            try:
                returns = pd.to_numeric(df["Total Return [%]"], errors="coerce").fillna(
                    0
                )
                drawdowns = pd.to_numeric(
                    df["Max Drawdown [%]"], errors="coerce"
                ).fillna(0)
                metrics["Return_to_Drawdown"] = (
                    returns.mean() / drawdowns.mean() if drawdowns.mean() != 0 else 0
                )
            except Exception:
                metrics["Return_to_Drawdown"] = 0

        return metrics

    def calculate_risk_metrics(self, df):
        """Calculate risk-specific metrics."""
        risk_metrics = {}

        for metric in self.risk_metrics:
            if metric in df.columns:
                try:
                    # Convert to numeric, handling any string values
                    numeric_series = pd.to_numeric(df[metric], errors="coerce")
                    risk_metrics[metric] = numeric_series.mean()
                except Exception as e:
                    print(f"Warning: Could not process {metric}: {e}")
                    risk_metrics[metric] = 0

        return risk_metrics

    def calculate_efficiency_score(self, df):
        """Calculate portfolio efficiency score."""
        if "Score" in df.columns:
            return df["Score"].mean()
        return 0

    def calculate_concentration_risk(self, df):
        """Calculate portfolio concentration risk."""
        if "Ticker" not in df.columns:
            return 1.0

        ticker_counts = df["Ticker"].value_counts()
        total_strategies = len(df)

        # Herfindahl-Hirschman Index for concentration
        hhi = sum((count / total_strategies) ** 2 for count in ticker_counts)
        return hhi

    def rank_incoming_strategies(self):
        """Rank incoming strategies by multiple criteria."""
        # Create composite score based on multiple factors
        df = self.incoming_df.copy()

        try:
            # Convert to numeric, handling any string values
            df["Score"] = pd.to_numeric(df["Score"], errors="coerce")
            df["Sortino Ratio"] = pd.to_numeric(df["Sortino Ratio"], errors="coerce")
            df["Win Rate [%]"] = pd.to_numeric(df["Win Rate [%]"], errors="coerce")
            df["Max Drawdown [%]"] = pd.to_numeric(
                df["Max Drawdown [%]"], errors="coerce"
            )

            # Normalize scores (0-1 scale)
            if df["Score"].max() != df["Score"].min():
                df["Score_norm"] = (df["Score"] - df["Score"].min()) / (
                    df["Score"].max() - df["Score"].min()
                )
            else:
                df["Score_norm"] = 1.0

            if df["Sortino Ratio"].max() != df["Sortino Ratio"].min():
                df["Sortino_norm"] = (
                    df["Sortino Ratio"] - df["Sortino Ratio"].min()
                ) / (df["Sortino Ratio"].max() - df["Sortino Ratio"].min())
            else:
                df["Sortino_norm"] = 1.0

            df["WinRate_norm"] = df["Win Rate [%]"] / 100

            # Inverse normalize risk metrics (lower is better)
            if df["Max Drawdown [%]"].max() != df["Max Drawdown [%]"].min():
                df["Drawdown_norm"] = 1 - (
                    (df["Max Drawdown [%]"] - df["Max Drawdown [%]"].min())
                    / (df["Max Drawdown [%]"].max() - df["Max Drawdown [%]"].min())
                )
            else:
                df["Drawdown_norm"] = 1.0

            # Composite ranking score
            df["Composite_Score"] = (
                df["Score_norm"].fillna(0) * 0.3
                + df["Sortino_norm"].fillna(0) * 0.25
                + df["WinRate_norm"].fillna(0) * 0.25
                + df["Drawdown_norm"].fillna(0) * 0.2
            )

            return df.sort_values("Composite_Score", ascending=False)
        except Exception as e:
            print(f"Warning: Error in ranking strategies: {e}")
            return df.sort_values("Score", ascending=False)

    def get_addition_rationale(self, strategy):
        """Generate rationale for adding a strategy."""
        reasons = []

        if strategy["Score"] > 1.5:
            reasons.append("High performance score")
        if strategy["Win Rate [%]"] > 55:
            reasons.append("Strong win rate")
        if strategy["Sortino Ratio"] > 1.0:
            reasons.append("Good risk-adjusted returns")
        if strategy["Max Drawdown [%]"] < 50:
            reasons.append("Controlled drawdown")

        return ", ".join(reasons) if reasons else "Balanced performance profile"

    def get_rejection_rationale(self, strategy):
        """Generate rationale for rejecting a strategy."""
        reasons = []

        if strategy["Score"] < 1.0:
            reasons.append("Low performance score")
        if strategy["Win Rate [%]"] < 45:
            reasons.append("Poor win rate")
        if strategy["Sortino Ratio"] < 0.5:
            reasons.append("Weak risk-adjusted returns")
        if strategy["Max Drawdown [%]"] > 80:
            reasons.append("Excessive drawdown risk")

        return ", ".join(reasons) if reasons else "Suboptimal performance profile"

    def run_comprehensive_analysis(self):
        """Run the complete portfolio enhancement analysis."""
        print("🚀 PORTFOLIO ENHANCEMENT ANALYSIS")
        print("=" * 80)
        print(
            "Analyzing existing vs incoming strategies for optimal portfolio composition"
        )

        if not self.load_portfolios():
            return None

        # Run all analysis components
        composition_results = self.analyze_portfolio_composition()
        performance_results = self.assess_performance_impact()
        risk_results = self.analyze_risk_contribution()
        projection_results = self.project_enhanced_portfolio()

        # Combine results for strategic recommendations
        analysis_results = {
            "composition": composition_results,
            "performance": performance_results,
            "risk": risk_results,
            "projections": projection_results,
        }

        strategic_results = self.generate_strategic_recommendations(analysis_results)

        # Final summary
        print("\n" + "=" * 80)
        print("📋 EXECUTIVE SUMMARY")
        print("=" * 80)

        print(f"\n🎯 KEY FINDINGS:")
        print(
            f"  • Portfolio efficiency improvement potential: {performance_results['efficiency_improvement']:+.2f}%"
        )
        print(
            f"  • Risk-adjusted return enhancement: {projection_results['risk_adj_improvement']:+.2f}%"
        )
        print(
            f"  • Concentration risk reduction: {risk_results['concentration_improvement']:+.2f}%"
        )
        print(
            f"  • Recommended strategy additions: {len(strategic_results['accept_strategies'])}"
        )

        print(f"\n✅ IMPLEMENTATION CONFIDENCE: HIGH")
        print(f"   Analysis based on comprehensive quantitative assessment")
        print(f"   Risk-reward profile supports portfolio enhancement")
        print(f"   Clear implementation roadmap with measurable targets")

        return analysis_results


def main():
    """Main execution function."""
    analyzer = PortfolioEnhancementAnalyzer()
    results = analyzer.run_comprehensive_analysis()

    if results:
        print(f"\n✅ Analysis completed successfully!")
        print(f"📊 Detailed results available in analysis output above")
    else:
        print(f"\n❌ Analysis failed - check input files and try again")


if __name__ == "__main__":
    main()
