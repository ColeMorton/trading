#!/usr/bin/env python3
"""
Detailed Analysis Results Display

This script demonstrates the loaded data structures and provides detailed
quantitative analysis examples for the strategy backtest data.
"""

import numpy as np
import pandas as pd

from analyze_strategy_data import StrategyDataAnalyzer


def display_correlation_analysis(analysis_data):
    """Display correlation analysis results."""
    print("\n" + "=" * 80)
    print("CORRELATION ANALYSIS")
    print("=" * 80)

    if not analysis_data["correlation_data"]:
        print("No correlation data available")
        return

    corr_matrix = analysis_data["correlation_data"]["correlation_matrix"]
    print("\nCorrelation Matrix (Key Metrics):")
    print("-" * 50)

    # Display correlation matrix with formatted output
    key_metrics = [
        "Total Return [%]",
        "Win Rate [%]",
        "Sharpe Ratio",
        "Max Drawdown [%]",
    ]
    available_metrics = [
        metric for metric in key_metrics if metric in corr_matrix.columns
    ]

    if available_metrics:
        subset_corr = corr_matrix.loc[available_metrics, available_metrics]
        print(subset_corr.round(3).to_string())

        # Highlight strongest correlations
        print("\nStrongest Positive Correlations:")
        for i in range(len(available_metrics)):
            for j in range(i + 1, len(available_metrics)):
                corr_val = subset_corr.iloc[i, j]
                if corr_val > 0.5:
                    print(
                        f"  {available_metrics[i]} <-> {available_metrics[j]}: {corr_val:.3f}"
                    )

        print("\nStrongest Negative Correlations:")
        for i in range(len(available_metrics)):
            for j in range(i + 1, len(available_metrics)):
                corr_val = subset_corr.iloc[i, j]
                if corr_val < -0.3:
                    print(
                        f"  {available_metrics[i]} <-> {available_metrics[j]}: {corr_val:.3f}"
                    )


def display_risk_analysis(analysis_data):
    """Display risk analysis results."""
    print("\n" + "=" * 80)
    print("RISK ANALYSIS")
    print("=" * 80)

    if not analysis_data["risk_data"]:
        print("No risk data available")
        return

    risk_metrics = analysis_data["risk_data"]["risk_metrics"]
    risk_summary = analysis_data["risk_data"]["risk_summary"]

    print("\nRisk Metrics Summary:")
    print("-" * 50)

    # Key risk metrics to highlight
    key_risk_cols = ["Max Drawdown [%]", "Sharpe Ratio", "Annualized Volatility"]
    available_risk_cols = [col for col in key_risk_cols if col in risk_summary.columns]

    if available_risk_cols:
        for col in available_risk_cols:
            stats = risk_summary[col]
            print(f"\n{col}:")
            print(f"  Mean: {stats['mean']:.2f}")
            print(f"  Std:  {stats['std']:.2f}")
            print(f"  Min:  {stats['min']:.2f}")
            print(f"  Max:  {stats['max']:.2f}")
            print(f"  25%:  {stats['25%']:.2f}")
            print(f"  75%:  {stats['75%']:.2f}")

    # High-risk strategies
    high_risk = analysis_data["risk_data"]["high_risk_strategies"]
    if not high_risk.empty:
        print(f"\nHigh-Risk Strategies (Max Drawdown > 50%):")
        print("-" * 50)
        print(f"Number of high-risk strategies: {len(high_risk)}")
        if "Ticker" in high_risk.columns:
            high_risk_tickers = high_risk["Ticker"].tolist()
            print(f"Tickers: {', '.join(high_risk_tickers[:10])}")  # Show first 10
            if len(high_risk_tickers) > 10:
                print(f"... and {len(high_risk_tickers) - 10} more")


def display_performance_analysis(analysis_data):
    """Display performance analysis results."""
    print("\n" + "=" * 80)
    print("PERFORMANCE ANALYSIS")
    print("=" * 80)

    if not analysis_data["performance_data"]:
        print("No performance data available")
        return

    perf_summary = analysis_data["performance_data"]["performance_summary"]
    top_performers = analysis_data["performance_data"]["top_performers"]
    strategy_type_perf = analysis_data["performance_data"]["strategy_type_performance"]

    print("\nPerformance Metrics Summary:")
    print("-" * 50)

    # Key performance metrics
    key_perf_cols = ["Total Return [%]", "Win Rate [%]", "Score", "Total Trades"]
    available_perf_cols = [col for col in key_perf_cols if col in perf_summary.columns]

    if available_perf_cols:
        for col in available_perf_cols:
            stats = perf_summary[col]
            print(f"\n{col}:")
            print(f"  Mean: {stats['mean']:.2f}")
            print(f"  Std:  {stats['std']:.2f}")
            print(f"  Min:  {stats['min']:.2f}")
            print(f"  Max:  {stats['max']:.2f}")

    # Top performers
    if not top_performers.empty:
        print(f"\nTop 5 Performing Strategies (by Score):")
        print("-" * 50)
        top_5 = top_performers.head(5)
        for idx, row in top_5.iterrows():
            ticker = row.get("Ticker", "N/A")
            strategy_type = row.get("Strategy Type", "N/A")
            score = row.get("Score", 0)
            win_rate = row.get("Win Rate [%]", 0)
            total_return = row.get("Total Return [%]", 0)
            print(
                f"  {ticker} ({strategy_type}): Score={score:.3f}, Win Rate={win_rate:.1f}%, Return={total_return:.1f}%"
            )

    # Strategy type performance comparison
    if not strategy_type_perf.empty:
        print(f"\nPerformance by Strategy Type:")
        print("-" * 50)
        for strategy_type, metrics in strategy_type_perf.iterrows():
            print(f"\n{strategy_type}:")
            if "Score" in metrics:
                print(f"  Avg Score: {metrics['Score']:.3f}")
            if "Win Rate [%]" in metrics:
                print(f"  Avg Win Rate: {metrics['Win Rate [%]']:.1f}%")
            if "Total Return [%]" in metrics:
                print(f"  Avg Return: {metrics['Total Return [%]']:.1f}%")


def display_data_structure_details(analysis_data):
    """Display detailed information about available data structures."""
    print("\n" + "=" * 80)
    print("DETAILED DATA STRUCTURE INFORMATION")
    print("=" * 80)

    # DataFrame details
    print("\nDataFrame Details:")
    print("-" * 50)
    for name, df in analysis_data["dataframes"].items():
        print(f"\n{name.upper()} DataFrame:")
        print(f"  Shape: {df.shape}")
        print(f"  Columns: {len(df.columns)}")
        print(f"  Memory usage: {df.memory_usage(deep=True).sum() / 1024:.1f} KB")

        # Show column names by category
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        text_cols = df.select_dtypes(include=["object"]).columns.tolist()
        datetime_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        print(
            f"  Numeric columns ({len(numeric_cols)}): {numeric_cols[:5]}{'...' if len(numeric_cols) > 5 else ''}"
        )
        print(
            f"  Text columns ({len(text_cols)}): {text_cols[:5]}{'...' if len(text_cols) > 5 else ''}"
        )
        if datetime_cols:
            print(f"  DateTime columns ({len(datetime_cols)}): {datetime_cols}")

    # Metrics details
    if analysis_data["metrics"]:
        print("\nExtracted Metrics:")
        print("-" * 50)
        metrics = analysis_data["metrics"]

        if "portfolio_summary" in metrics:
            summary = metrics["portfolio_summary"]
            print(f"Portfolio Summary Metrics: {len(summary)} metrics")
            for key, value in list(summary.items())[:5]:
                print(f"  {key}: {value}")
            if len(summary) > 5:
                print(f"  ... and {len(summary) - 5} more")

        if "ticker_metrics" in metrics:
            ticker_metrics = metrics["ticker_metrics"]
            print(f"Ticker-level Metrics: {len(ticker_metrics)} tickers")
            sample_ticker = list(ticker_metrics.keys())[0] if ticker_metrics else None
            if sample_ticker:
                sample_metrics = ticker_metrics[sample_ticker]
                print(
                    f"  Sample ticker ({sample_ticker}): {len(sample_metrics)} metrics"
                )
                for key, value in list(sample_metrics.items())[:3]:
                    print(f"    {key}: {value}")


def demonstrate_quantitative_analysis(analysis_data):
    """Demonstrate examples of quantitative analysis that can be performed."""
    print("\n" + "=" * 80)
    print("QUANTITATIVE ANALYSIS EXAMPLES")
    print("=" * 80)

    combined_df = analysis_data["dataframes"].get("combined")
    if combined_df is None or combined_df.empty:
        print("No combined data available for analysis")
        return

    # Example 1: Risk-Return Analysis
    print("\n1. RISK-RETURN PROFILE ANALYSIS")
    print("-" * 50)

    if (
        "Total Return [%]" in combined_df.columns
        and "Max Drawdown [%]" in combined_df.columns
    ):
        # Calculate risk-adjusted return metrics
        returns = combined_df["Total Return [%]"]
        max_dd = combined_df["Max Drawdown [%]"]

        # Risk-return ratio (return per unit of max drawdown)
        risk_return_ratio = returns / max_dd

        print(f"Risk-Return Analysis:")
        print(f"  Average Return: {returns.mean():.2f}%")
        print(f"  Average Max Drawdown: {max_dd.mean():.2f}%")
        print(f"  Average Risk-Return Ratio: {risk_return_ratio.mean():.3f}")
        print(f"  Best Risk-Return Ratio: {risk_return_ratio.max():.3f}")

        # Identify strategies with good risk-return profiles
        good_risk_return = combined_df[
            risk_return_ratio > risk_return_ratio.quantile(0.75)
        ]
        if not good_risk_return.empty and "Ticker" in good_risk_return.columns:
            print(f"  Top quartile risk-return strategies: {len(good_risk_return)}")
            print(
                f"  Example tickers: {', '.join(good_risk_return['Ticker'].head(5).tolist())}"
            )

    # Example 2: Strategy Type Comparison
    print("\n2. STRATEGY TYPE EFFECTIVENESS")
    print("-" * 50)

    if "Strategy Type" in combined_df.columns:
        strategy_counts = combined_df["Strategy Type"].value_counts()
        print(f"Strategy Type Distribution:")
        for strategy_type, count in strategy_counts.items():
            print(f"  {strategy_type}: {count} strategies")

        # Performance comparison by strategy type
        if "Score" in combined_df.columns:
            strategy_performance = combined_df.groupby("Strategy Type")["Score"].agg(
                ["mean", "std", "count"]
            )
            print(f"\nScore Performance by Strategy Type:")
            for strategy_type, stats in strategy_performance.iterrows():
                print(
                    f"  {strategy_type}: Mean={stats['mean']:.3f}, Std={stats['std']:.3f}, Count={stats['count']}"
                )

    # Example 3: Trade Frequency Analysis
    print("\n3. TRADE FREQUENCY ANALYSIS")
    print("-" * 50)

    if "Total Trades" in combined_df.columns:
        trades = combined_df["Total Trades"]
        print(f"Trade Volume Statistics:")
        print(f"  Total trades across all strategies: {trades.sum():,}")
        print(f"  Average trades per strategy: {trades.mean():.1f}")
        print(f"  Median trades per strategy: {trades.median():.1f}")
        print(f"  Most active strategy: {trades.max()} trades")
        print(f"  Least active strategy: {trades.min()} trades")

        # High-frequency vs low-frequency strategy performance
        if "Win Rate [%]" in combined_df.columns:
            high_freq = combined_df[trades > trades.median()]
            low_freq = combined_df[trades <= trades.median()]

            print(f"\nHigh-frequency strategies (>{trades.median():.0f} trades):")
            print(f"  Count: {len(high_freq)}")
            print(f"  Avg Win Rate: {high_freq['Win Rate [%]'].mean():.1f}%")

            print(f"Low-frequency strategies (<={trades.median():.0f} trades):")
            print(f"  Count: {len(low_freq)}")
            print(f"  Avg Win Rate: {low_freq['Win Rate [%]'].mean():.1f}%")


def main():
    """Main function to run detailed analysis display."""
    print("Detailed Strategy Data Analysis Results")
    print("=" * 80)

    # Initialize analyzer and load data
    analyzer = StrategyDataAnalyzer()

    csv_files = ["./csv/strategies/trades.csv", "./csv/strategies/incoming.csv"]

    json_files = ["./json/concurrency/trades.json", "./json/concurrency/incoming.json"]

    # Perform analysis
    results = analyzer.analyze_files(csv_files, json_files)
    analysis_data = analyzer.get_data_for_analysis(results)

    # Display detailed analysis results
    display_data_structure_details(analysis_data)
    display_correlation_analysis(analysis_data)
    display_risk_analysis(analysis_data)
    display_performance_analysis(analysis_data)
    demonstrate_quantitative_analysis(analysis_data)

    print("\n" + "=" * 80)
    print("ANALYSIS RECOMMENDATIONS")
    print("=" * 80)

    print("\nNext Steps for Quantitative Analysis:")
    print("1. Portfolio Optimization:")
    print("   - Use correlation matrix to identify diversification opportunities")
    print("   - Apply modern portfolio theory with the risk-return data")
    print("   - Consider strategy allocation based on risk-adjusted performance")

    print("\n2. Risk Management:")
    print("   - Implement position sizing based on max drawdown metrics")
    print("   - Consider correlation-based exposure limits")
    print("   - Monitor strategies exceeding risk thresholds")

    print("\n3. Strategy Selection:")
    print("   - Rank strategies by risk-adjusted returns")
    print("   - Consider trade frequency impact on transaction costs")
    print("   - Evaluate strategy type effectiveness for different market conditions")

    print("\n4. Performance Monitoring:")
    print("   - Set up alerts for strategies deviating from expected performance")
    print("   - Track rolling performance metrics")
    print("   - Monitor correlation changes over time")

    return analysis_data


if __name__ == "__main__":
    analysis_data = main()
