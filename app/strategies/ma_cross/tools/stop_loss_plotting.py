"""
Stop Loss Plotting Module

This module contains functions for creating visualizations of stop loss parameter sensitivity.
"""

import numpy as np
from numpy.typing import NDArray
import plotly.graph_objects as go
from typing_extensions import TypedDict


class MetricFormat(TypedDict):
    """Format configuration for metric visualization."""

    colorscale: str
    format: str
    title_suffix: str


class Config(TypedDict, total=False):
    """Configuration for stop loss visualization.

    Optional Fields:
        RELATIVE: Whether to show metrics relative to baseline (default: True)
    """

    RELATIVE: bool | None


def create_stop_loss_heatmap(
    metric_matrices: dict[str, NDArray[np.float64]],
    stop_loss_range: NDArray[np.float64],
    ticker: str,
    config: Config,
) -> dict[str, go.Figure]:
    """
    Create heatmap visualizations for stop loss parameter analysis.

    Args:
        metric_matrices: Dictionary mapping metric names to their sensitivity arrays
        stop_loss_range: Array of stop loss percentages tested
        ticker: Ticker symbol for plot titles
        config: Strategy configuration including visualization settings

    Returns:
        Dictionary mapping metric names to their interactive heatmap figures
    """
    figures = {}

    metric_formats: dict[str, MetricFormat] = {
        "trades": {
            "colorscale": "RdBu",
            "format": "+.0f",
            "title_suffix": "% vs Baseline",
        },
        "returns": {
            "colorscale": "RdBu",
            "format": "+.1f",
            "title_suffix": "pp vs Baseline",
        },
        "score": {
            "colorscale": "RdBu",
            "format": "+.0f",
            "title_suffix": "% vs Baseline",
        },
        "win_rate": {
            "colorscale": "RdBu",
            "format": "+.1f",
            "title_suffix": "pp vs Baseline",
        },
    }

    # Create heatmap for each metric that has format definitions
    for metric_name, array in metric_matrices.items():
        # Only create heatmaps for metrics we have format definitions for
        if metric_name not in metric_formats:
            continue

        format_info = metric_formats[metric_name]

        # Set visualization parameters
        title_suffix = (
            format_info["title_suffix"] if config.get("RELATIVE", True) else ""
        )
        colorscale = (
            format_info["colorscale"] if config.get("RELATIVE", True) else "ice"
        )

        # Ensure no NaN values and reshape for heatmap
        array = np.nan_to_num(array, 0)
        heatmap_data = array.reshape(1, -1)

        # Use actual data range
        zmin, zmax = heatmap_data.min(), heatmap_data.max()
        print(f"\nDebug - {metric_name} range: {zmin:.2f} to {zmax:.2f}")

        fig = go.Figure()

        # Add heatmap trace
        fig.add_trace(
            go.Heatmap(
                z=heatmap_data,
                x=stop_loss_range,
                colorscale=colorscale,
                zmin=zmin,
                zmax=zmax,
                colorbar={
                    "title": {
                        "text": f"{metric_name.capitalize().replace('_', ' ')} {title_suffix}",
                        "side": "right",
                    },
                    "thickness": 20,
                    "len": 0.9,
                    "tickformat": format_info["format"],
                },
                hoverongaps=False,
                hovertemplate=(
                    "Stop Loss: %{x:.2f}%<br>"
                    + f'{metric_name.capitalize().replace("_", " ")}: '
                    + ("%{z:" + format_info["format"] + "}")
                    + "<extra></extra>"
                ),
            )
        )

        # Update layout
        title_text = f'{ticker} Stop Loss Sensitivity Analysis<br><sub>{metric_name.capitalize().replace("_", " ")}</sub>'

        fig.update_layout(
            title={
                "text": title_text,
                "x": 0.5,
                "xanchor": "center",
                "y": 0.95,
                "yanchor": "top",
                "font": {"size": 16},
            },
            xaxis={
                "title": {"text": "Stop Loss Threshold (%)", "font": {"size": 14}},
                "tickmode": "array",
                "ticktext": [
                    f"{x:.1f}%" for x in stop_loss_range[::50]
                ],  # Show every 50th tick
                "tickvals": stop_loss_range[::50],
                "showgrid": True,
                "gridwidth": 1,
                "gridcolor": "rgba(128, 128, 128, 0.2)",
            },
            yaxis={"showticklabels": False, "showgrid": False, "fixedrange": True},
            plot_bgcolor="white",
            paper_bgcolor="white",
            autosize=True,
            margin={"l": 50, "r": 50, "t": 100, "b": 50},
        )

        figures[metric_name] = fig

    return figures
