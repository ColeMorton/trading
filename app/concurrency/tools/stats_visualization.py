"""Statistics visualization utilities for concurrency analysis."""

from typing import Callable, Dict

from app.concurrency.tools.types import ConcurrencyStats


def create_stats_annotation(
    stats: ConcurrencyStats, log: Callable[[str, str], None]
) -> Dict:
    """Create annotation with concurrency statistics.

    Args:
        stats (ConcurrencyStats): Dictionary containing concurrency statistics
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict: Plotly annotation configuration

    Raises:
        KeyError: If required statistics are missing
        ValueError: If statistics values are invalid
    """
    try:
        log("Creating statistics annotation", "info")

        # Validate required fields
        required_fields = [
            "start_date",
            "end_date",
            "total_periods",
            "total_concurrent_periods",
            "concurrency_ratio",
            "exclusive_ratio",
            "inactive_ratio",
            "avg_concurrent_strategies",
            "max_concurrent_strategies",
            "risk_concentration_index",
        ]
        missing = [field for field in required_fields if field not in stats]
        if missing:
            log(f"Missing required statistics: {missing}", "error")
            raise KeyError(f"Missing required statistics: {missing}")

        log("Building concurrency metrics section", "info")
        stats_text = (
            f"Analysis Period: {stats['start_date']} to {stats['end_date']}<br>"
            "<br><b>Concurrency Metrics:</b><br>"
            f"Total Periods: {stats['total_periods']}<br>"
            f"Concurrent Periods: {stats['total_concurrent_periods']}<br>"
            f"Concurrency Ratio: {stats['concurrency_ratio']:.2%}<br>"
            f"Exclusive Ratio: {stats['exclusive_ratio']:.2%}<br>"
            f"Inactive Ratio: {stats['inactive_ratio']:.2%}<br>"
            f"Avg Concurrent Strategies: {stats['avg_concurrent_strategies']:.2f}<br>"
            f"Max Concurrent Strategies: {stats['max_concurrent_strategies']}<br>"
            f"Risk Concentration Index: {stats['risk_concentration_index']:.2f}<br>"
        )

        # Add signal metrics section
        log("Adding signal metrics section", "info")
        if "signal_metrics" not in stats:
            log("Missing signal metrics", "error")
            raise KeyError("Missing signal metrics in statistics")

        signal_metrics = stats["signal_metrics"]
        stats_text += "<br><b>Signal Metrics:</b><br>"
        stats_text += f"Mean Signals/Month: {signal_metrics['mean_signals']:.2f}<br>"
        stats_text += (
            f"Median Signals/Month: {signal_metrics['median_signals']:.2f}<br>"
        )
        stats_text += f"Signal Range: {signal_metrics['std_below_mean']:.2f} to {signal_metrics['std_above_mean']:.2f}<br>"
        stats_text += (
            f"Signal Volatility: {signal_metrics['signal_volatility']:.2f}<br>"
        )
        stats_text += f"Monthly Range: {signal_metrics['min_monthly_signals']:.0f} to {signal_metrics['max_monthly_signals']:.0f}<br>"
        stats_text += f"Total Signals: {signal_metrics['total_signals']:.0f}<br>"

        # Add efficiency metrics section
        log("Adding efficiency metrics section", "info")
        efficiency_fields = [
            "total_expectancy",
            "diversification_multiplier",
            "independence_multiplier",
            "activity_multiplier",
            "efficiency_score",
        ]
        missing = [field for field in efficiency_fields if field not in stats]
        if missing:
            log(f"Missing efficiency metrics: {missing}", "error")
            raise KeyError(f"Missing efficiency metrics: {missing}")

        stats_text += "<br><b>Efficiency Metrics:</b><br>"
        stats_text += (
            f"Portfolio Expectancy: {float(stats['total_expectancy']):.4f}<br>"
        )
        stats_text += f"Diversification Multiplier: {float(stats['diversification_multiplier']):.2f}<br>"
        stats_text += f"Independence Multiplier: {float(stats['independence_multiplier']):.2f}<br>"
        stats_text += (
            f"Activity Multiplier: {float(stats['activity_multiplier']):.2f}<br>"
        )
        stats_text += f"Efficiency Score: {float(stats['efficiency_score']):.2f}<br>"

        # Add risk metrics section
        log("Adding risk metrics section", "info")
        if "risk_metrics" not in stats:
            log("Missing risk metrics", "error")
            raise KeyError("Missing risk metrics in statistics")

        risk_metrics = stats["risk_metrics"]
        stats_text += "<br><b>Risk Metrics:</b><br>"

        # Add strategy risk contributions and alpha values
        log("Processing strategy risk contributions and alphas", "info")
        strategy_nums = sorted(
            list(
                {
                    k.split("_")[1]
                    for k in risk_metrics.keys()
                    if k.startswith("strategy_")
                    and (
                        k.endswith("_risk_contrib") or k.endswith("_alpha_to_portfolio")
                    )
                }
            )
        )

        for strategy_num in strategy_nums:
            risk_key = f"strategy_{strategy_num}_risk_contrib"
            alpha_key = f"strategy_{strategy_num}_alpha_to_portfolio"

            if risk_key in risk_metrics:
                stats_text += f"Strategy {strategy_num} Risk Contribution: {risk_metrics[risk_key]:.2%}<br>"
            if alpha_key in risk_metrics:
                stats_text += f"Strategy {strategy_num} Alpha to Portfolio: {risk_metrics[alpha_key]:.4%}<br>"

            # Add VaR and CVaR metrics
            var_95_key = f"strategy_{strategy_num}_var_95"
            cvar_95_key = f"strategy_{strategy_num}_cvar_95"
            var_99_key = f"strategy_{strategy_num}_var_99"
            cvar_99_key = f"strategy_{strategy_num}_cvar_99"

            if var_95_key in risk_metrics:
                stats_text += f"Strategy {strategy_num} VaR 95%: {risk_metrics[var_95_key]:.2%}<br>"
            if cvar_95_key in risk_metrics:
                stats_text += f"Strategy {strategy_num} CVaR 95%: {risk_metrics[cvar_95_key]:.2%}<br>"
            if var_99_key in risk_metrics:
                stats_text += f"Strategy {strategy_num} VaR 99%: {risk_metrics[var_99_key]:.2%}<br>"
            if cvar_99_key in risk_metrics:
                stats_text += f"Strategy {strategy_num} CVaR 99%: {risk_metrics[cvar_99_key]:.2%}<br>"

        # Add risk overlaps
        log("Adding risk overlap metrics", "info")
        overlap_keys = [
            k for k in sorted(risk_metrics.keys()) if k.startswith("risk_overlap_")
        ]
        for key in overlap_keys:
            strat1, strat2 = key.split("_")[2:4]
            stats_text += f"Risk Overlap {strat1}-{strat2}: {risk_metrics[key]:.2%}<br>"

        # Add combined VaR and CVaR metrics
        if "combined_var_95" in risk_metrics:
            stats_text += f"Combined VaR 95%: {risk_metrics['combined_var_95']:.2%}<br>"
        if "combined_cvar_95" in risk_metrics:
            stats_text += (
                f"Combined CVaR 95%: {risk_metrics['combined_cvar_95']:.2%}<br>"
            )
        if "combined_var_99" in risk_metrics:
            stats_text += f"Combined VaR 99%: {risk_metrics['combined_var_99']:.2%}<br>"
        if "combined_cvar_99" in risk_metrics:
            stats_text += (
                f"Combined CVaR 99%: {risk_metrics['combined_cvar_99']:.2%}<br>"
            )

        # Add total portfolio risk and benchmark return
        if "total_portfolio_risk" in risk_metrics:
            stats_text += (
                f"Total Portfolio Risk: {risk_metrics['total_portfolio_risk']:.4f}<br>"
            )
        if "benchmark_return" in risk_metrics:
            stats_text += (
                f"Benchmark Return: {risk_metrics['benchmark_return']:.4%}<br>"
            )

        log("Creating annotation configuration", "info")
        annotation = {
            "xref": "paper",
            "yref": "paper",
            "x": 0.0,
            "y": 1.0,
            "text": stats_text,
            "showarrow": False,
            "font": dict(size=10),
            "align": "left",
            "bgcolor": "rgba(255,255,255,0.8)",
            "bordercolor": "black",
            "borderwidth": 1,
        }

        log("Statistics annotation created successfully", "info")
        return annotation

    except Exception as e:
        log(f"Error creating statistics annotation: {str(e)}", "error")
        raise
