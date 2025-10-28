"""
Headless plotting utilities for VectorBT portfolios.

This module provides alternatives to VectorBT's interactive plotting that work
in headless environments without requiring anywidget or Jupyter widgets.
"""

from collections.abc import Callable
import os

import matplotlib
import matplotlib.pyplot as plt


def configure_headless_backend():
    """Configure matplotlib for headless operation."""
    matplotlib.use("Agg")


def save_portfolio_plots(
    portfolio,
    output_dir: str,
    filename_prefix: str = "portfolio",
    subplots: list[str] | None = None,
    **kwargs,
) -> list[str]:
    """
    Save portfolio plots to files instead of displaying them interactively.

    Args:
        portfolio: VectorBT portfolio object
        output_dir: Directory to save plots
        filename_prefix: Prefix for plot filenames
        subplots: List of subplot types to generate
        **kwargs: Additional arguments passed to portfolio.plot()

    Returns:
        List of created file paths
    """
    if subplots is None:
        subplots = [
            "value",
            "drawdowns",
            "cum_returns",
            "assets",
            "orders",
            "trades",
            "trade_pnl",
            "asset_flow",
            "cash_flow",
            "asset_value",
            "cash",
            "underwater",
            "gross_exposure",
            "net_exposure",
        ]

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    created_files = []

    try:
        # Configure for headless operation
        configure_headless_backend()

        # Create the plot with plotly backend
        fig = portfolio.plot(subplots=subplots, show_titles=True, **kwargs)

        # Save as HTML (plotly's native format)
        html_path = os.path.join(output_dir, f"{filename_prefix}.html")
        fig.write_html(html_path)
        created_files.append(html_path)

        # Try to save as PNG if kaleido is available
        try:
            png_path = os.path.join(output_dir, f"{filename_prefix}.png")
            fig.write_image(png_path, width=1200, height=10000)
            created_files.append(png_path)
        except Exception:
            # Kaleido might not be available, continue with HTML only
            pass

    except Exception:
        # Fallback: create individual matplotlib plots
        created_files.extend(
            _create_matplotlib_fallback(portfolio, output_dir, filename_prefix),
        )

    return created_files


def create_portfolio_plot_files(
    portfolio,
    config: dict,
    log_func: Callable,
) -> list[str]:
    """
    Create portfolio plot files based on strategy configuration.

    Args:
        portfolio: VectorBT portfolio object
        config: Strategy configuration dictionary
        log_func: Logging function

    Returns:
        List of created file paths
    """
    # Determine output directory based on strategy type
    strategy_type = config.get("STRATEGY_TYPE", "SMA")
    strategy_type_dir = "macd" if strategy_type == "MACD" else "ma_cross"

    output_dir = f'data/outputs/{strategy_type_dir}/plots/{config["TICKER"]}'

    try:
        created_files = save_portfolio_plots(
            portfolio=portfolio,
            output_dir=output_dir,
            filename_prefix=f'{config["TICKER"]}_portfolio_analysis',
            width=1200,
            height=10000,
            autosize=True,
        )

        for file_path in created_files:
            log_func(f"Generated portfolio plot: {file_path}")

        return created_files

    except Exception as e:
        log_func(f"Error generating portfolio plots: {e!s}", "error")
        return []


def _create_matplotlib_fallback(
    portfolio,
    output_dir: str,
    filename_prefix: str,
) -> list[str]:
    """
    Fallback method using matplotlib for basic portfolio plots.

    Args:
        portfolio: VectorBT portfolio object
        output_dir: Directory to save plots
        filename_prefix: Prefix for plot filenames

    Returns:
        List of created file paths
    """
    created_files = []

    try:
        # Configure matplotlib
        configure_headless_backend()

        # Create value plot
        plt.figure(figsize=(12, 8))
        value_series = portfolio.value()
        plt.plot(value_series.index, value_series.values)
        plt.title("Portfolio Value Over Time")
        plt.xlabel("Date")
        plt.ylabel("Portfolio Value")
        plt.grid(True)

        value_path = os.path.join(output_dir, f"{filename_prefix}_value.png")
        plt.savefig(value_path, dpi=150, bbox_inches="tight")
        plt.close()
        created_files.append(value_path)

        # Create drawdown plot
        plt.figure(figsize=(12, 6))
        drawdowns = portfolio.drawdowns.drawdown
        plt.fill_between(drawdowns.index, drawdowns.values, 0, alpha=0.3, color="red")
        plt.title("Portfolio Drawdowns")
        plt.xlabel("Date")
        plt.ylabel("Drawdown")
        plt.grid(True)

        drawdown_path = os.path.join(output_dir, f"{filename_prefix}_drawdowns.png")
        plt.savefig(drawdown_path, dpi=150, bbox_inches="tight")
        plt.close()
        created_files.append(drawdown_path)

    except Exception:
        # Even fallback failed, but don't raise - just return empty list
        pass

    return created_files
