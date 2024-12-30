"""
Protective Stop Loss Plotting Module

This module contains functions for visualizing protective stop loss analysis results
through plots and heatmaps.
"""

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np
from typing import List, Tuple, Callable, Dict

def plot_results(
    results: List[Tuple[int, float, int, float]],
    ticker: str,
    config: dict,
    log: Callable
) -> None:
    """
    Plot the results of the holding period analysis.

    Args:
        results (List[Tuple[int, float, int, float]]): Results from holding period analysis
        ticker (str): The ticker symbol being analyzed
        config (dict): The configuration dictionary
        log (Callable): Logging function
    """
    holding_periods, returns, num_positions, expectancies = zip(*results)

    fig, ax1 = plt.subplots(figsize=(12, 6))

    color = 'tab:green'
    ax1.set_xlabel('Holding Period')
    ax1.set_ylabel('Expectancy', color=color)
    ax1.plot(holding_periods, expectancies, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()
    color = 'tab:orange'
    ax2.set_ylabel('Number of Positions', color=color)
    ax2.plot(holding_periods, num_positions, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    strategy_type = "Short-only" if config.get("SHORT", False) else "Long-only"
    rsi_info = f" with RSI({config['RSI_PERIOD']}) >= {config['RSI_THRESHOLD']}" if config.get("USE_RSI", False) else ""
    plt.title(f'{ticker} Parameter Sensitivity: Holding Period vs Expectancy ({strategy_type} Strategy{rsi_info})')
    plt.grid(True)

    # Save the plot
    plot_filename = f'png/ma_cross/parameter_sensitivity/{ticker}_protective_stop_loss.png'
    plt.savefig(plot_filename)
    log(f"Plot saved as {plot_filename}")

    plt.show()

def create_protective_stop_loss_heatmap(
    metric_matrices: Dict[str, np.ndarray],
    holding_period_range: np.ndarray,
    ticker: str
) -> Dict[str, go.Figure]:
    """
    Create heatmap visualizations for protective stop loss parameter analysis.

    Args:
        metric_matrices (Dict[str, np.ndarray]: Dictionary containing metric arrays
        holding_period_range (np.ndarray): Array of holding periods used
        ticker (str): Ticker symbol for plot titles

    Returns:
        Dict[str, go.Figure]: Dictionary containing Plotly figures for each metric
    """
    figures = {}
    
    # Create heatmap for each metric
    for metric_name, array in metric_matrices.items():
        # Ensure no NaN values
        array = np.nan_to_num(array, 0)
        
        # Reshape array for heatmap (add dummy y-axis)
        heatmap_data = array.reshape(1, -1)
        
        fig = go.Figure()
        
        # Add heatmap trace
        fig.add_trace(go.Heatmap(
            z=heatmap_data,
            x=holding_period_range,
            colorscale='ice',
            colorbar=dict(
                title=dict(
                    text=metric_name.capitalize().replace('_', ' '),
                    side='right'
                ),
                thickness=20,
                len=0.9,
                tickformat='.1%' if metric_name in ['returns', 'win_rate'] else None
            ),
            hoverongaps=False,
            hovertemplate=(
                'Holding Period: %{x:.0f} days<br>' +
                f'{metric_name.capitalize().replace("_", " ")}: ' +
                ('%{z:.1%}' if metric_name in ['returns', 'win_rate'] else 
                 '%{z:.2f}' if metric_name == 'sharpe_ratio' else 
                 '%{z:.0f}') +
                '<extra></extra>'
            )
        ))
        
        # Update layout
        title_text = f'{ticker} Protective Stop Loss Sensitivity Analysis<br><sub>{metric_name.capitalize().replace("_", " ")}</sub>'
        
        fig.update_layout(
            title=dict(
                text=title_text,
                x=0.5,
                xanchor='center',
                y=0.95,
                yanchor='top',
                font=dict(size=16)
            ),
            xaxis=dict(
                title=dict(
                    text='Holding Period (Days)',
                    font=dict(size=14)
                ),
                tickmode='array',
                ticktext=[f'{int(x)}' for x in holding_period_range],  # Show all ticks as integers
                tickvals=holding_period_range,
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(128, 128, 128, 0.2)'
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                fixedrange=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            autosize=True,
            margin=dict(l=50, r=50, t=100, b=50)
        )
        
        figures[metric_name] = fig
    
    return figures
