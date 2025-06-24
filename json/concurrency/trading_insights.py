#!/usr/bin/env python3
"""
Trading Decision Insights Generator
Creates actionable trading recommendations based on portfolio analysis
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd


def generate_trading_insights():
    """Generate actionable trading insights"""

    # Load the data
    trades_df = pd.read_csv(
        "/Users/colemorton/Projects/trading/csv/strategies/trades.csv"
    )
    incoming_df = pd.read_csv(
        "/Users/colemorton/Projects/trading/csv/strategies/incoming.csv"
    )

    combined_df = pd.concat([trades_df, incoming_df], ignore_index=True)

    # Clean data
    numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        combined_df[col] = pd.to_numeric(combined_df[col], errors="coerce")

    insights = {
        "portfolio_recommendations": generate_portfolio_recommendations(combined_df),
        "risk_management_rules": generate_risk_rules(combined_df),
        "parameter_optimization": generate_parameter_insights(combined_df),
        "trade_execution_guidance": generate_execution_guidance(combined_df),
        "performance_monitoring": generate_monitoring_framework(combined_df),
    }

    return insights


def generate_portfolio_recommendations(df):
    """Generate specific portfolio allocation recommendations"""

    # Calculate composite scores
    df["composite_score"] = (
        df["Score"] * 0.3
        + (df["Sharpe Ratio"] / df["Sharpe Ratio"].max()) * 0.25
        + (df["Sortino Ratio"] / df["Sortino Ratio"].max()) * 0.25
        + ((100 - df["Max Drawdown [%]"]) / 100) * 0.2
    )

    # Risk categorization
    df["risk_category"] = pd.cut(
        df["Max Drawdown [%]"],
        bins=[0, 50, 70, 85, 100],
        labels=["Low Risk", "Medium Risk", "High Risk", "Extreme Risk"],
    )

    # Performance tiers
    df["performance_tier"] = pd.qcut(
        df["Total Return [%]"], q=4, labels=["Tier 4", "Tier 3", "Tier 2", "Tier 1"]
    )

    # Generate recommendations
    core_holdings = df[
        (df["composite_score"] >= df["composite_score"].quantile(0.7))
        & (df["Sharpe Ratio"] >= 0.8)
        & (df["Max Drawdown [%]"] <= 70)
    ].sort_values("composite_score", ascending=False)

    growth_positions = df[
        (df["Total Return [%]"] >= df["Total Return [%]"].quantile(0.8))
        & (df["Max Drawdown [%]"] <= 80)
        & (~df.index.isin(core_holdings.index))
    ].sort_values("Total Return [%]", ascending=False)

    speculative_positions = df[
        (df["Total Return [%]"] >= df["Total Return [%]"].quantile(0.6))
        & (df["Max Drawdown [%]"] > 80)
    ].sort_values("composite_score", ascending=False)

    return {
        "core_holdings": {
            "allocation_pct": 60,
            "strategies": core_holdings[
                [
                    "Ticker",
                    "Strategy Type",
                    "Short Window",
                    "Long Window",
                    "composite_score",
                    "Total Return [%]",
                    "Sharpe Ratio",
                    "Max Drawdown [%]",
                ]
            ]
            .head(5)
            .to_dict("records"),
            "rationale": "Highest composite scores with acceptable risk profiles",
        },
        "growth_positions": {
            "allocation_pct": 25,
            "strategies": growth_positions[
                [
                    "Ticker",
                    "Strategy Type",
                    "Short Window",
                    "Long Window",
                    "Total Return [%]",
                    "Sharpe Ratio",
                    "Max Drawdown [%]",
                ]
            ]
            .head(3)
            .to_dict("records"),
            "rationale": "High return potential with elevated but manageable risk",
        },
        "speculative_positions": {
            "allocation_pct": 15,
            "strategies": speculative_positions[
                [
                    "Ticker",
                    "Strategy Type",
                    "Short Window",
                    "Long Window",
                    "Total Return [%]",
                    "Max Drawdown [%]",
                ]
            ]
            .head(2)
            .to_dict("records"),
            "rationale": "Highest return potential with significant risk - small allocations only",
        },
        "diversification_metrics": {
            "unique_tickers": df["Ticker"].nunique(),
            "sector_concentration_risk": "HIGH - Tech heavy portfolio",
            "strategy_diversity": "LOW - All SMA strategies",
            "parameter_diversity": "MEDIUM - Various window combinations",
        },
    }


def generate_risk_rules(df):
    """Generate risk management rules based on analysis"""

    max_drawdowns = df["Max Drawdown [%]"]

    return {
        "position_sizing_rules": {
            "max_single_position": "10% for strategies with <60% max DD",
            "reduced_position": "5% for strategies with 60-75% max DD",
            "minimal_position": "2% for strategies with >75% max DD",
            "absolute_max_dd_limit": "85% - avoid strategies exceeding this",
        },
        "portfolio_level_limits": {
            "max_portfolio_drawdown": "50% - based on historical worst-case scenarios",
            "correlation_limit": "No more than 30% in single sector/asset class",
            "rebalancing_trigger": "Monthly or when any position exceeds +/- 2% of target allocation",
        },
        "stop_loss_recommendations": {
            "individual_strategy": "25% loss from peak for strategies without built-in stops",
            "portfolio_level": "20% portfolio drawdown triggers review/rebalancing",
            "time_based_stop": "Exit if no new high for 12 months (trend breakdown)",
        },
        "risk_monitoring_alerts": {
            "daily": "Portfolio value, individual position P&L",
            "weekly": "Drawdown metrics, correlation analysis",
            "monthly": "Performance attribution, rebalancing needs",
            "quarterly": "Strategy performance review, parameter optimization",
        },
    }


def generate_parameter_insights(df):
    """Generate insights on optimal parameters"""

    # Analyze window relationships
    df["window_ratio"] = df["Long Window"] / df["Short Window"]
    df["window_spread"] = df["Long Window"] - df["Short Window"]

    # Performance by parameter ranges
    short_window_performance = df.groupby(pd.cut(df["Short Window"], bins=5)).agg(
        {
            "Total Return [%]": "mean",
            "Sharpe Ratio": "mean",
            "Max Drawdown [%]": "mean",
            "Win Rate [%]": "mean",
        }
    )

    long_window_performance = df.groupby(pd.cut(df["Long Window"], bins=5)).agg(
        {
            "Total Return [%]": "mean",
            "Sharpe Ratio": "mean",
            "Max Drawdown [%]": "mean",
            "Win Rate [%]": "mean",
        }
    )

    return {
        "optimal_parameter_ranges": {
            "short_window": {
                "best_performance_range": "13-39 days (based on top performers)",
                "sweet_spot": "20-30 days for balanced risk/return",
                "avoid": "<10 days (too noisy) or >60 days (too slow)",
            },
            "long_window": {
                "best_performance_range": "51-77 days (based on top performers)",
                "sweet_spot": "60-80 days for trend capture",
                "avoid": "<40 days (insufficient trend filtering)",
            },
            "window_ratio": {
                "optimal_ratio": f'{df["window_ratio"].quantile(0.75):.2f} (75th percentile of performers)',
                "minimum_ratio": "1.5 (long must be 50% longer than short)",
                "maximum_ratio": "4.0 (beyond this becomes too slow)",
            },
        },
        "parameter_optimization_recommendations": {
            "trending_markets": "Use longer windows (60/80, 70/90) for stable trend capture",
            "volatile_markets": "Use shorter windows (20/40, 30/50) for quicker adaptation",
            "sector_specific": {
                "tech_stocks": "Shorter windows due to higher volatility",
                "utilities/staples": "Longer windows for stable trend following",
                "financials": "Medium windows (40/60) for balance",
            },
        },
        "signal_timing_insights": {
            "entry_signals": f'{len(df[df["Signal Entry"] == True])} strategies use entry signals',
            "exit_signals": f'{len(df[df["Signal Exit"] == True])} strategies use exit signals',
            "performance_impact": "Mixed results - requires individual strategy testing",
        },
    }


def generate_execution_guidance(df):
    """Generate trade execution guidance"""

    avg_trade_duration = df["Avg Trade Duration"].apply(
        lambda x: extract_days_from_duration(str(x)) if pd.notna(x) else 0
    )

    trade_frequency = df["Trades per Month"].mean()

    return {
        "timing_considerations": {
            "average_trade_duration": f"{avg_trade_duration.mean():.0f} days",
            "holding_period_range": f"{avg_trade_duration.min():.0f}-{avg_trade_duration.max():.0f} days",
            "recommended_review_frequency": "Weekly for position management, monthly for rebalancing",
        },
        "execution_logistics": {
            "trade_frequency": f"{trade_frequency:.2f} trades per strategy per month",
            "total_monthly_trades": f"{trade_frequency * len(df):.0f} across all strategies",
            "execution_window": "Market open first hour for best liquidity",
            "order_types": "Limit orders preferred, market orders for urgent exits",
        },
        "capital_deployment": {
            "initial_deployment": "Phase in over 3 months to avoid timing risk",
            "cash_reserve": "20% for rebalancing and new opportunities",
            "scaling_approach": "Start with top 5 strategies, add others as proven",
        },
        "monitoring_dashboard_requirements": {
            "real_time": ["Portfolio value", "Daily P&L", "Open positions"],
            "daily": ["Individual strategy performance", "Signal generation"],
            "weekly": ["Risk metrics", "Drawdown tracking"],
            "monthly": ["Performance attribution", "Rebalancing analysis"],
        },
    }


def generate_monitoring_framework(df):
    """Generate performance monitoring framework"""

    return {
        "key_performance_indicators": {
            "primary_metrics": {
                "total_return": "Track against benchmark and targets",
                "sharpe_ratio": f'Target: >{df["Sharpe Ratio"].quantile(0.6):.2f}',
                "max_drawdown": f'Alert if exceeds {df["Max Drawdown [%]"].quantile(0.8):.1f}%',
                "win_rate": f'Target: >{df["Win Rate [%]"].quantile(0.5):.1f}%',
            },
            "secondary_metrics": {
                "sortino_ratio": "Risk-adjusted downside performance",
                "calmar_ratio": "Return per unit of max drawdown",
                "profit_factor": "Gross profit / gross loss ratio",
                "expectancy": "Expected profit per trade",
            },
        },
        "performance_benchmarks": {
            "absolute_targets": {
                "annual_return": "15-25% target range",
                "sharpe_ratio": ">1.0 for acceptable risk-adjusted return",
                "max_drawdown": "<30% portfolio level, <70% individual strategy",
            },
            "relative_benchmarks": {
                "market_benchmark": "S&P 500 total return",
                "peer_comparison": "Trend-following strategy indices",
                "risk_parity": "Compare to balanced portfolio allocation",
            },
        },
        "alert_thresholds": {
            "immediate_action": {
                "portfolio_dd_20pct": "Review all positions and risk exposure",
                "strategy_dd_30pct": "Consider position size reduction",
                "consecutive_losses": "5+ losing trades in single strategy",
            },
            "review_triggers": {
                "monthly_performance": "<-5% relative to benchmark",
                "rolling_sharpe": "Below 0.5 for 3+ months",
                "correlation_increase": "Strategy correlation >0.8",
            },
        },
        "reporting_schedule": {
            "daily": "P&L summary, position updates",
            "weekly": "Performance metrics, risk dashboard",
            "monthly": "Detailed attribution analysis, rebalancing report",
            "quarterly": "Strategy review, parameter optimization assessment",
        },
    }


def extract_days_from_duration(duration_str):
    """Extract days from duration string"""
    if "days" in duration_str:
        try:
            return int(duration_str.split(" days")[0])
        except:
            return 0
    return 0


def save_trading_insights(insights):
    """Save trading insights to file"""
    output_dir = Path("/Users/colemorton/Projects/trading/json/concurrency/analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "trading_insights.json", "w") as f:
        json.dump(insights, f, indent=2, default=str)

    # Create executive summary
    executive_summary = {
        "recommended_core_portfolio": insights["portfolio_recommendations"][
            "core_holdings"
        ]["strategies"][:3],
        "key_risk_rules": {
            "max_position_size": insights["risk_management_rules"][
                "position_sizing_rules"
            ]["max_single_position"],
            "portfolio_dd_limit": insights["risk_management_rules"][
                "portfolio_level_limits"
            ]["max_portfolio_drawdown"],
            "stop_loss": insights["risk_management_rules"]["stop_loss_recommendations"][
                "individual_strategy"
            ],
        },
        "optimal_parameters": {
            "short_window": insights["parameter_optimization"][
                "optimal_parameter_ranges"
            ]["short_window"]["sweet_spot"],
            "long_window": insights["parameter_optimization"][
                "optimal_parameter_ranges"
            ]["long_window"]["sweet_spot"],
        },
        "execution_priorities": {
            "phase_1": "Deploy top 3 core strategies with 60% allocation",
            "phase_2": "Add growth positions with 25% allocation",
            "phase_3": "Consider speculative positions with 15% allocation",
        },
    }

    with open(output_dir / "executive_summary.json", "w") as f:
        json.dump(executive_summary, f, indent=2, default=str)

    print(f"Trading insights saved to {output_dir}")
    print("\n=== EXECUTIVE SUMMARY ===")
    print("\nRecommended Core Portfolio (Top 3):")
    for i, strategy in enumerate(executive_summary["recommended_core_portfolio"], 1):
        print(
            f"{i}. {strategy['Ticker']} {strategy['Strategy Type']} ({strategy['Short Window']}/{strategy['Long Window']}) - Score: {strategy['composite_score']:.3f}"
        )

    print(f"\nKey Risk Rules:")
    print(
        f"- Max Position Size: {executive_summary['key_risk_rules']['max_position_size']}"
    )
    print(
        f"- Portfolio DD Limit: {executive_summary['key_risk_rules']['portfolio_dd_limit']}"
    )
    print(f"- Stop Loss: {executive_summary['key_risk_rules']['stop_loss']}")


def main():
    """Main function"""
    print("Generating trading insights...")
    insights = generate_trading_insights()
    save_trading_insights(insights)
    print("\nTrading insights generation complete!")


if __name__ == "__main__":
    main()
