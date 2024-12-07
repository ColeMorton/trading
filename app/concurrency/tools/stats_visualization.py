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
        f"Efficiency Score: {stats['efficiency_score']:.2f}<br>"
    )

    # Add risk metrics section
    stats_text += "<br><b>Risk Metrics:</b><br>"
    risk_metrics = stats['risk_metrics']
    
    # Add strategy risk contributions
    for key in sorted(risk_metrics.keys()):
        if key.startswith('strategy_'):
            stats_text += f"Strategy {key.split('_')[1]} Risk Contribution: {risk_metrics[key]:.2%}<br>"
    
    # Add risk overlaps
    for key in sorted(risk_metrics.keys()):
        if key.startswith('risk_overlap_'):
            stats_text += f"Risk Overlap {key.split('_')[2]}-{key.split('_')[3]}: {risk_metrics[key]:.2%}<br>"
    
    # Add total portfolio risk
    if 'total_portfolio_risk' in risk_metrics:
        stats_text += f"Total Portfolio Risk: {risk_metrics['total_portfolio_risk']:.4f}<br>"

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
