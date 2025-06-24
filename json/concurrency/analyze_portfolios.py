#!/usr/bin/env python3
"""
Comprehensive Portfolio Analysis Tool
Analyzes trades.csv and incoming.csv for quantitative insights
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

# File paths
TRADES_CSV = "/Users/colemorton/Projects/trading/csv/strategies/trades.csv"
INCOMING_CSV = "/Users/colemorton/Projects/trading/csv/strategies/incoming.csv"
OUTPUT_DIR = "/Users/colemorton/Projects/trading/json/concurrency/analysis"


def load_portfolios():
    """Load both portfolio CSV files"""
    trades_df = pd.read_csv(TRADES_CSV)
    incoming_df = pd.read_csv(INCOMING_CSV)

    # Clean numeric columns
    for df in [trades_df, incoming_df]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return trades_df, incoming_df


def calculate_strategy_rankings(df, portfolio_name):
    """Calculate strategy performance rankings by multiple metrics"""
    ranking_metrics = {
        "Score": "Score",
        "Win Rate": "Win Rate [%]",
        "Total Return": "Total Return [%]",
        "Sortino Ratio": "Sortino Ratio",
        "Sharpe Ratio": "Sharpe Ratio",
        "Calmar Ratio": "Calmar Ratio",
        "Profit Factor": "Profit Factor",
        "Expectancy per Trade": "Expectancy per Trade",
    }

    rankings = {}
    for metric_name, column in ranking_metrics.items():
        if column in df.columns:
            df_sorted = df.sort_values(column, ascending=False, na_position="last")
            rankings[metric_name] = (
                df_sorted[
                    ["Ticker", "Strategy Type", "Short Window", "Long Window", column]
                ]
                .head(10)
                .to_dict("records")
            )

    return rankings


def analyze_risk_metrics(df):
    """Analyze risk-adjusted performance metrics"""
    risk_metrics = {
        "sharpe_ratio": {
            "mean": df["Sharpe Ratio"].mean(),
            "median": df["Sharpe Ratio"].median(),
            "std": df["Sharpe Ratio"].std(),
            "min": df["Sharpe Ratio"].min(),
            "max": df["Sharpe Ratio"].max(),
            "percentiles": {
                "25th": df["Sharpe Ratio"].quantile(0.25),
                "75th": df["Sharpe Ratio"].quantile(0.75),
                "90th": df["Sharpe Ratio"].quantile(0.90),
            },
        },
        "sortino_ratio": {
            "mean": df["Sortino Ratio"].mean(),
            "median": df["Sortino Ratio"].median(),
            "std": df["Sortino Ratio"].std(),
            "min": df["Sortino Ratio"].min(),
            "max": df["Sortino Ratio"].max(),
            "percentiles": {
                "25th": df["Sortino Ratio"].quantile(0.25),
                "75th": df["Sortino Ratio"].quantile(0.75),
                "90th": df["Sortino Ratio"].quantile(0.90),
            },
        },
        "calmar_ratio": {
            "mean": df["Calmar Ratio"].mean(),
            "median": df["Calmar Ratio"].median(),
            "std": df["Calmar Ratio"].std(),
            "min": df["Calmar Ratio"].min(),
            "max": df["Calmar Ratio"].max(),
            "percentiles": {
                "25th": df["Calmar Ratio"].quantile(0.25),
                "75th": df["Calmar Ratio"].quantile(0.75),
                "90th": df["Calmar Ratio"].quantile(0.90),
            },
        },
    }

    # Add correlation matrix between risk metrics
    risk_cols = ["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio", "Omega Ratio"]
    available_cols = [col for col in risk_cols if col in df.columns]
    if len(available_cols) > 1:
        risk_metrics["correlations"] = df[available_cols].corr().to_dict()

    return risk_metrics


def analyze_drawdowns(df):
    """Analyze drawdown statistics"""
    drawdown_analysis = {
        "max_drawdown": {
            "mean": df["Max Drawdown [%]"].mean(),
            "median": df["Max Drawdown [%]"].median(),
            "std": df["Max Drawdown [%]"].std(),
            "min": df["Max Drawdown [%]"].min(),
            "max": df["Max Drawdown [%]"].max(),
            "above_50_pct": len(df[df["Max Drawdown [%]"] > 50]),
            "above_75_pct": len(df[df["Max Drawdown [%]"] > 75]),
        },
        "recovery_analysis": {},
    }

    # Analyze recovery periods (if duration data available)
    if "Max Drawdown Duration" in df.columns:
        # Convert duration strings to days (simplified parsing)
        durations = []
        for dur in df["Max Drawdown Duration"]:
            if pd.notna(dur) and "days" in str(dur):
                try:
                    days = int(str(dur).split(" days")[0])
                    durations.append(days)
                except:
                    pass

        if durations:
            drawdown_analysis["recovery_analysis"] = {
                "mean_days": np.mean(durations),
                "median_days": np.median(durations),
                "max_days": np.max(durations),
                "strategies_over_365_days": sum(1 for d in durations if d > 365),
            }

    return drawdown_analysis


def analyze_trade_frequency_expectancy(df):
    """Analyze trade frequency and expectancy metrics"""
    analysis = {
        "trade_frequency": {
            "total_trades": {
                "mean": df["Total Trades"].mean(),
                "median": df["Total Trades"].median(),
                "std": df["Total Trades"].std(),
                "min": df["Total Trades"].min(),
                "max": df["Total Trades"].max(),
            },
            "trades_per_month": {
                "mean": df["Trades per Month"].mean(),
                "median": df["Trades per Month"].median(),
                "std": df["Trades per Month"].std(),
            },
        },
        "expectancy": {
            "expectancy_per_trade": {
                "mean": df["Expectancy per Trade"].mean(),
                "median": df["Expectancy per Trade"].median(),
                "positive_expectancy": len(df[df["Expectancy per Trade"] > 0]),
                "negative_expectancy": len(df[df["Expectancy per Trade"] < 0]),
            },
            "expectancy_per_month": {
                "mean": df["Expectancy per Month"].mean(),
                "median": df["Expectancy per Month"].median(),
                "top_10_pct": df["Expectancy per Month"].quantile(0.90),
            },
        },
        "win_metrics": {
            "avg_win_rate": df["Win Rate [%]"].mean(),
            "strategies_above_50_pct": len(df[df["Win Rate [%]"] > 50]),
            "avg_profit_factor": df["Profit Factor"].mean(),
            "strategies_pf_above_2": len(df[df["Profit Factor"] > 2]),
        },
    }

    return analysis


def statistical_significance_analysis(trades_df, incoming_df):
    """Test statistical significance of performance differences"""
    tests = {}

    # Metrics to test
    test_metrics = [
        "Score",
        "Win Rate [%]",
        "Total Return [%]",
        "Sharpe Ratio",
        "Sortino Ratio",
        "Calmar Ratio",
    ]

    for metric in test_metrics:
        if metric in trades_df.columns and metric in incoming_df.columns:
            trades_vals = trades_df[metric].dropna()
            incoming_vals = incoming_df[metric].dropna()

            # T-test
            t_stat, t_pval = stats.ttest_ind(trades_vals, incoming_vals)

            # Mann-Whitney U test (non-parametric)
            u_stat, u_pval = stats.mannwhitneyu(
                trades_vals, incoming_vals, alternative="two-sided"
            )

            # Effect size (Cohen's d)
            pooled_std = np.sqrt(
                (trades_vals.std() ** 2 + incoming_vals.std() ** 2) / 2
            )
            cohens_d = (
                (trades_vals.mean() - incoming_vals.mean()) / pooled_std
                if pooled_std > 0
                else 0
            )

            tests[metric] = {
                "trades_mean": trades_vals.mean(),
                "incoming_mean": incoming_vals.mean(),
                "difference": trades_vals.mean() - incoming_vals.mean(),
                "t_test": {
                    "statistic": t_stat,
                    "p_value": t_pval,
                    "significant_at_0.05": t_pval < 0.05,
                },
                "mann_whitney": {
                    "statistic": u_stat,
                    "p_value": u_pval,
                    "significant_at_0.05": u_pval < 0.05,
                },
                "effect_size_cohens_d": cohens_d,
            }

    return tests


def analyze_strategy_distribution(df):
    """Analyze strategy type distribution and parameters"""
    analysis = {
        "strategy_types": df["Strategy Type"].value_counts().to_dict(),
        "signal_entry_exit": {
            "using_signals": len(
                df[(df["Signal Entry"] == True) | (df["Signal Exit"] == True)]
            ),
            "no_signals": len(
                df[(df["Signal Entry"] == False) & (df["Signal Exit"] == False)]
            ),
        },
        "window_parameters": {
            "short_window": {
                "mean": df["Short Window"].mean(),
                "median": df["Short Window"].median(),
                "min": df["Short Window"].min(),
                "max": df["Short Window"].max(),
                "most_common": df["Short Window"].mode().values[0]
                if len(df["Short Window"].mode()) > 0
                else None,
            },
            "long_window": {
                "mean": df["Long Window"].mean(),
                "median": df["Long Window"].median(),
                "min": df["Long Window"].min(),
                "max": df["Long Window"].max(),
                "most_common": df["Long Window"].mode().values[0]
                if len(df["Long Window"].mode()) > 0
                else None,
            },
            "window_spread": {
                "mean": (df["Long Window"] - df["Short Window"]).mean(),
                "median": (df["Long Window"] - df["Short Window"]).median(),
            },
        },
    }

    return analysis


def identify_top_bottom_performers(df, n=5):
    """Identify top and bottom performers by multiple metrics"""
    performers = {"top_performers": {}, "bottom_performers": {}}

    key_metrics = ["Score", "Total Return [%]", "Sharpe Ratio", "Win Rate [%]"]

    for metric in key_metrics:
        if metric in df.columns:
            # Top performers
            top_df = df.nlargest(n, metric)[
                ["Ticker", "Strategy Type", "Short Window", "Long Window", metric]
            ]
            performers["top_performers"][metric] = top_df.to_dict("records")

            # Bottom performers
            bottom_df = df.nsmallest(n, metric)[
                ["Ticker", "Strategy Type", "Short Window", "Long Window", metric]
            ]
            performers["bottom_performers"][metric] = bottom_df.to_dict("records")

    return performers


def calculate_portfolio_metrics(df):
    """Calculate portfolio-level metrics"""
    # Assuming equal weighting for simplicity
    n_strategies = len(df)
    weight = 1.0 / n_strategies if n_strategies > 0 else 0

    metrics = {
        "portfolio_size": n_strategies,
        "equal_weight": weight,
        "weighted_metrics": {
            "total_return": (df["Total Return [%]"] * weight).sum(),
            "sharpe_ratio": (df["Sharpe Ratio"] * weight).sum(),
            "sortino_ratio": (df["Sortino Ratio"] * weight).sum(),
            "win_rate": (df["Win Rate [%]"] * weight).sum(),
            "max_drawdown": df["Max Drawdown [%]"].max(),  # Worst case
            "avg_drawdown": df["Max Drawdown [%]"].mean(),
        },
        "diversification": {
            "unique_tickers": df["Ticker"].nunique(),
            "unique_strategies": df["Strategy Type"].nunique(),
            "ticker_concentration": df["Ticker"].value_counts().to_dict(),
        },
    }

    return metrics


def analyze_risk_contribution(df):
    """Analyze risk contribution of each strategy"""
    # Calculate contribution metrics
    df["return_contribution"] = (
        df["Total Return [%]"] / df["Total Return [%]"].sum() * 100
    )
    df["risk_score"] = df["Max Drawdown [%]"] * (
        1 / (df["Sharpe Ratio"] + 1)
    )  # Higher is worse
    df["risk_contribution"] = df["risk_score"] / df["risk_score"].sum() * 100

    risk_analysis = {
        "highest_risk_contributors": df.nlargest(10, "risk_contribution")[
            [
                "Ticker",
                "Strategy Type",
                "risk_contribution",
                "Max Drawdown [%]",
                "Sharpe Ratio",
            ]
        ].to_dict("records"),
        "lowest_risk_contributors": df.nsmallest(10, "risk_contribution")[
            [
                "Ticker",
                "Strategy Type",
                "risk_contribution",
                "Max Drawdown [%]",
                "Sharpe Ratio",
            ]
        ].to_dict("records"),
        "risk_return_analysis": {
            "high_return_low_risk": df[
                (df["Total Return [%]"] > df["Total Return [%]"].median())
                & (df["risk_score"] < df["risk_score"].median())
            ][["Ticker", "Strategy Type", "Total Return [%]", "risk_score"]].to_dict(
                "records"
            ),
            "low_return_high_risk": df[
                (df["Total Return [%]"] < df["Total Return [%]"].median())
                & (df["risk_score"] > df["risk_score"].median())
            ][["Ticker", "Strategy Type", "Total Return [%]", "risk_score"]].to_dict(
                "records"
            ),
        },
    }

    return risk_analysis


def sector_correlation_analysis(df):
    """Analyze correlations between tickers if sector data available"""
    # For now, analyze ticker performance correlations
    ticker_returns = df.pivot_table(
        values="Total Return [%]",
        index="Ticker",
        columns="Strategy Type",
        aggfunc="first",
    )

    if not ticker_returns.empty and ticker_returns.shape[0] > 1:
        correlation_matrix = ticker_returns.T.corr()

        # Find highly correlated pairs
        high_correlations = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i + 1, len(correlation_matrix.columns)):
                corr = correlation_matrix.iloc[i, j]
                if not pd.isna(corr) and abs(corr) > 0.7:
                    high_correlations.append(
                        {
                            "ticker1": correlation_matrix.columns[i],
                            "ticker2": correlation_matrix.columns[j],
                            "correlation": corr,
                        }
                    )

        return {
            "correlation_matrix": correlation_matrix.to_dict(),
            "high_correlations": high_correlations,
            "avg_correlation": correlation_matrix.values[
                np.triu_indices_from(correlation_matrix.values, k=1)
            ].mean(),
        }

    return {"message": "Insufficient data for correlation analysis"}


def generate_comprehensive_report(trades_df, incoming_df):
    """Generate comprehensive analysis report"""
    report = {
        "metadata": {
            "analysis_date": datetime.now().isoformat(),
            "trades_portfolio_size": len(trades_df),
            "incoming_portfolio_size": len(incoming_df),
        },
        "trades_portfolio": {
            "rankings": calculate_strategy_rankings(trades_df, "trades"),
            "risk_metrics": analyze_risk_metrics(trades_df),
            "drawdown_analysis": analyze_drawdowns(trades_df),
            "trade_frequency_expectancy": analyze_trade_frequency_expectancy(trades_df),
            "strategy_distribution": analyze_strategy_distribution(trades_df),
            "top_bottom_performers": identify_top_bottom_performers(trades_df),
            "portfolio_metrics": calculate_portfolio_metrics(trades_df),
            "risk_contribution": analyze_risk_contribution(trades_df),
            "correlations": sector_correlation_analysis(trades_df),
        },
        "incoming_portfolio": {
            "rankings": calculate_strategy_rankings(incoming_df, "incoming"),
            "risk_metrics": analyze_risk_metrics(incoming_df),
            "drawdown_analysis": analyze_drawdowns(incoming_df),
            "trade_frequency_expectancy": analyze_trade_frequency_expectancy(
                incoming_df
            ),
            "strategy_distribution": analyze_strategy_distribution(incoming_df),
            "top_bottom_performers": identify_top_bottom_performers(incoming_df),
            "portfolio_metrics": calculate_portfolio_metrics(incoming_df),
            "risk_contribution": analyze_risk_contribution(incoming_df),
            "correlations": sector_correlation_analysis(incoming_df),
        },
        "comparative_analysis": {
            "statistical_significance": statistical_significance_analysis(
                trades_df, incoming_df
            ),
            "portfolio_comparison": {
                "trades_vs_incoming": {
                    "total_return_diff": trades_df["Total Return [%]"].mean()
                    - incoming_df["Total Return [%]"].mean(),
                    "sharpe_diff": trades_df["Sharpe Ratio"].mean()
                    - incoming_df["Sharpe Ratio"].mean(),
                    "win_rate_diff": trades_df["Win Rate [%]"].mean()
                    - incoming_df["Win Rate [%]"].mean(),
                    "max_dd_diff": trades_df["Max Drawdown [%]"].mean()
                    - incoming_df["Max Drawdown [%]"].mean(),
                }
            },
        },
    }

    return report


def save_analysis_results(report):
    """Save analysis results to JSON files"""
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save full report
    with open(output_dir / "comprehensive_analysis.json", "w") as f:
        json.dump(report, f, indent=2, default=str)

    # Save summary statistics
    summary = {
        "trades_portfolio": {
            "avg_score": report["trades_portfolio"]["portfolio_metrics"][
                "weighted_metrics"
            ],
            "top_performers": report["trades_portfolio"]["top_bottom_performers"][
                "top_performers"
            ],
            "risk_summary": {
                "avg_sharpe": report["trades_portfolio"]["risk_metrics"][
                    "sharpe_ratio"
                ]["mean"],
                "avg_sortino": report["trades_portfolio"]["risk_metrics"][
                    "sortino_ratio"
                ]["mean"],
                "avg_max_dd": report["trades_portfolio"]["drawdown_analysis"][
                    "max_drawdown"
                ]["mean"],
            },
        },
        "incoming_portfolio": {
            "avg_score": report["incoming_portfolio"]["portfolio_metrics"][
                "weighted_metrics"
            ],
            "top_performers": report["incoming_portfolio"]["top_bottom_performers"][
                "top_performers"
            ],
            "risk_summary": {
                "avg_sharpe": report["incoming_portfolio"]["risk_metrics"][
                    "sharpe_ratio"
                ]["mean"],
                "avg_sortino": report["incoming_portfolio"]["risk_metrics"][
                    "sortino_ratio"
                ]["mean"],
                "avg_max_dd": report["incoming_portfolio"]["drawdown_analysis"][
                    "max_drawdown"
                ]["mean"],
            },
        },
        "key_insights": report["comparative_analysis"],
    }

    with open(output_dir / "summary_analysis.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"Analysis results saved to {output_dir}")

    # Print key insights
    print("\n=== KEY INSIGHTS ===")
    print(f"\nTrades Portfolio ({len(report['metadata'])} strategies):")
    print(
        f"  Avg Total Return: {report['trades_portfolio']['portfolio_metrics']['weighted_metrics']['total_return']:.2f}%"
    )
    print(
        f"  Avg Sharpe Ratio: {report['trades_portfolio']['risk_metrics']['sharpe_ratio']['mean']:.3f}"
    )
    print(
        f"  Avg Win Rate: {report['trades_portfolio']['portfolio_metrics']['weighted_metrics']['win_rate']:.2f}%"
    )

    print(
        f"\nIncoming Portfolio ({report['metadata']['incoming_portfolio_size']} strategies):"
    )
    print(
        f"  Avg Total Return: {report['incoming_portfolio']['portfolio_metrics']['weighted_metrics']['total_return']:.2f}%"
    )
    print(
        f"  Avg Sharpe Ratio: {report['incoming_portfolio']['risk_metrics']['sharpe_ratio']['mean']:.3f}"
    )
    print(
        f"  Avg Win Rate: {report['incoming_portfolio']['portfolio_metrics']['weighted_metrics']['win_rate']:.2f}%"
    )


def main():
    """Main analysis function"""
    print("Loading portfolio data...")
    trades_df, incoming_df = load_portfolios()

    print(f"Loaded {len(trades_df)} strategies from trades.csv")
    print(f"Loaded {len(incoming_df)} strategies from incoming.csv")

    print("\nPerforming comprehensive analysis...")
    report = generate_comprehensive_report(trades_df, incoming_df)

    print("\nSaving results...")
    save_analysis_results(report)

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
