"""Statistics visualization utilities for concurrency analysis."""

from typing import Dict
import plotly.graph_objects as go
from app.concurrency.tools.types import ConcurrencyStats

def create_stats_annotation(stats: ConcurrencyStats) -> Dict:
    """Create annotation with concurrency statistics.

    Args:
        stats (ConcurrencyStats): Dictionary containing concurrency statistics

    Returns:
        Dict: Plotly annotation configuration
    """
    stats_text = (
        f"Analysis Period: {stats['start_date']} to {stats['end_date']}<br>"
        f"<br><b>Concurrency Metrics:</b><br>"
        f"Total Periods: {stats['total_periods']}<br>"
        f"Concurrent Periods: {stats['total_concurrent_periods']}<br>"
        f"Concurrency Ratio: {stats['concurrency_ratio']:.2%}<br>"
        f"Exclusive Ratio: {stats['exclusive_ratio']:.2%}<br>"
        f"Inactive (Remaining): {stats['inactive_ratio']:.2%}<br>"
        f"Avg Concurrent Strategies: {stats['avg_concurrent_strategies']:.2f}<br>"
        f"Max Concurrent Strategies: {stats['max_concurrent_strategies']}<br>"
        f"Risk Concentration Index: {stats['risk_concentration_index']:.2f}<br>"
    )

    # Add efficiency metrics section
    stats_text += "<br><b>Efficiency Metrics:</b><br>"
    stats_text += f"Total Expectancy: {float(stats['total_expectancy']):.4f}<br>"
    stats_text += f"Diversification Multiplier: {float(stats['diversification_multiplier']):.2f}<br>"
    stats_text += f"Independence Multiplier: {float(stats['independence_multiplier']):.2f}<br>"
    stats_text += f"Activity Multiplier: {float(stats['activity_multiplier']):.2f}<br>"
    stats_text += f"Efficiency Score: {float(stats['efficiency_score']):.2f}<br>"

    # Add risk metrics section
    stats_text += "<br><b>Risk Metrics:</b><br>"
    risk_metrics = stats['risk_metrics']
    
    # Add strategy risk contributions and alpha values
    strategy_nums = sorted(list({k.split('_')[1] for k in risk_metrics.keys() 
                               if k.startswith('strategy_') and 
                               (k.endswith('_risk_contrib') or k.endswith('_alpha'))}))
    
    for strategy_num in strategy_nums:
        risk_key = f"strategy_{strategy_num}_risk_contrib"
        alpha_key = f"strategy_{strategy_num}_alpha"
        
        if risk_key in risk_metrics:
            stats_text += f"Strategy {strategy_num} Risk Contribution: {risk_metrics[risk_key]:.2%}<br>"
        if alpha_key in risk_metrics:
            stats_text += f"Strategy {strategy_num} Alpha: {risk_metrics[alpha_key]:.4%}<br>"
    
    # Add risk overlaps
    overlap_keys = [k for k in sorted(risk_metrics.keys()) if k.startswith('risk_overlap_')]
    for key in overlap_keys:
        strat1, strat2 = key.split('_')[2:4]
        stats_text += f"Risk Overlap {strat1}-{strat2}: {risk_metrics[key]:.2%}<br>"
    
    # Add total portfolio risk and benchmark return
    if 'total_portfolio_risk' in risk_metrics:
        stats_text += f"Total Portfolio Risk: {risk_metrics['total_portfolio_risk']:.4f}<br>"
    if 'benchmark_return' in risk_metrics:
        stats_text += f"Benchmark Return: {risk_metrics['benchmark_return']:.4%}<br>"

    return {
        "xref": "paper",
        "yref": "paper",
        "x": 1.0,
        "y": 1.0,
        "text": stats_text,
        "showarrow": False,
        "font": dict(size=10),
        "align": "right",
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "black",
        "borderwidth": 1
    }
