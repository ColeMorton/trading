"""
Portfolio Visualization Module

This module handles the creation and display of portfolio analysis plots.
"""

import os

import vectorbt as vbt

from app.tools.plotting import configure_headless_backend, save_portfolio_plots


def create_portfolio_plots(
    portfolio: "vbt.Portfolio", benchmark_portfolio: "vbt.Portfolio", log
):
    """
    Create and display portfolio analysis plots.

    Args:
        portfolio: Strategy portfolio
        benchmark_portfolio: Benchmark portfolio for comparison
        log: Logging function
    """
    # Create comparison plots
    log("Creating portfolio plots")

    # Configure for headless operation
    configure_headless_backend()

    # Create output directory
    output_dir = "data/outputs/portfolio_review/plots"
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Import plotly directly to avoid VectorBT's interactive plotting
        import pandas as pd
        import plotly.graph_objects as go

        # Generate benchmark portfolio value plot manually
        benchmark_value = benchmark_portfolio.value()
        benchmark_fig = go.Figure()
        benchmark_fig.add_trace(
            go.Scatter(
                x=benchmark_value.index,
                y=benchmark_value.values,
                mode="lines",
                name="Benchmark Portfolio Value",
                line=dict(color="blue"),
            )
        )
        benchmark_fig.update_layout(
            title="Benchmark Portfolio Value Over Time",
            xaxis_title="Date",
            yaxis_title="Portfolio Value",
            width=1200,
            height=600,
        )

        benchmark_path = os.path.join(output_dir, "benchmark_portfolio.html")
        benchmark_fig.write_html(benchmark_path)
        log(f"Generated benchmark portfolio plot: {benchmark_path}")

        # Try to save as PNG if possible
        try:
            benchmark_png_path = os.path.join(output_dir, "benchmark_portfolio.png")
            benchmark_fig.write_image(benchmark_png_path, width=1200, height=600)
            log(f"Generated benchmark portfolio PNG: {benchmark_png_path}")
        except Exception:
            # Kaleido might not work, continue with HTML only
            pass

        # Generate strategy portfolio plots manually
        strategy_value = portfolio.value()
        strategy_returns = portfolio.returns()

        # Handle drawdowns safely
        try:
            strategy_drawdowns = portfolio.drawdowns.drawdown
        except:
            # Create a simple drawdown series as fallback
            strategy_drawdowns = strategy_returns * 0  # Zero drawdowns as fallback

        # Create subplot figure
        from plotly.subplots import make_subplots

        strategy_fig = make_subplots(
            rows=4,
            cols=1,
            subplot_titles=[
                "Portfolio Value",
                "Cumulative Returns",
                "Drawdowns",
                "Underwater Curve",
            ],
            vertical_spacing=0.08,
        )

        # Portfolio value
        strategy_fig.add_trace(
            go.Scatter(
                x=strategy_value.index,
                y=strategy_value.values,
                mode="lines",
                name="Portfolio Value",
                line=dict(color="green"),
            ),
            row=1,
            col=1,
        )

        # Cumulative returns
        cum_returns = strategy_returns.cumsum()
        strategy_fig.add_trace(
            go.Scatter(
                x=cum_returns.index,
                y=cum_returns.values,
                mode="lines",
                name="Cumulative Returns",
                line=dict(color="orange"),
            ),
            row=2,
            col=1,
        )

        # Drawdowns - handle both pandas Series and VectorBT objects
        if hasattr(strategy_drawdowns, "index"):
            dd_x = strategy_drawdowns.index
            dd_y = (
                strategy_drawdowns.values
                if hasattr(strategy_drawdowns, "values")
                else strategy_drawdowns
            )
        else:
            # Fallback to strategy_returns index if drawdowns don't have index
            dd_x = strategy_returns.index
            dd_y = [0] * len(strategy_returns)  # Zero drawdowns

        strategy_fig.add_trace(
            go.Scatter(
                x=dd_x,
                y=dd_y,
                mode="lines",
                fill="tonexty",
                name="Drawdowns",
                line=dict(color="red"),
                fillcolor="rgba(255,0,0,0.3)",
            ),
            row=3,
            col=1,
        )

        # Underwater curve (same as drawdowns for now)
        strategy_fig.add_trace(
            go.Scatter(
                x=dd_x,
                y=dd_y,
                mode="lines",
                name="Underwater",
                line=dict(color="darkred"),
            ),
            row=4,
            col=1,
        )

        strategy_fig.update_layout(
            title="Strategy Portfolio Analysis",
            height=1000,
            width=1200,
            showlegend=False,
        )

        strategy_path = os.path.join(output_dir, "strategy_portfolio.html")
        strategy_fig.write_html(strategy_path)
        log(f"Generated strategy portfolio plot: {strategy_path}")

        # Try to save as PNG if possible
        try:
            strategy_png_path = os.path.join(output_dir, "strategy_portfolio.png")
            strategy_fig.write_image(strategy_png_path, width=1200, height=1000)
            log(f"Generated strategy portfolio PNG: {strategy_png_path}")
        except Exception:
            # Kaleido might not work, continue with HTML only
            pass

    except Exception as e:
        log(f"Error generating portfolio plots: {str(e)}", "error")
        # Create fallback message
        log("Portfolio plots generation failed, but analysis continues", "warning")


def print_portfolio_stats(stats: dict, risk_metrics: dict, log):
    """
    Print portfolio statistics and risk metrics.

    Args:
        stats: Dictionary of portfolio statistics
        risk_metrics: Dictionary of risk metrics (VaR, CVaR)
        log: Logging function
    """
    print("\nStrategy Portfolio Statistics:")
    print("===================")
    for key, value in stats.items():
        print(f"{key}: {value}")
        log(f"{key}: {value}")

    print("\nRisk Metrics:")
    print("===================")
    for metric, value in risk_metrics.items():
        print(f"{metric}: {value:.2%}")
        log(f"{metric}: {value:.2%}")


def print_open_positions(open_positions: list):
    """
    Print currently open positions.

    Args:
        open_positions: List of tuples containing (strategy_name, position_size)
    """
    if open_positions:
        print("\nStrategies with Open Positions:")
        print("===================")
        for strategy_name, position in open_positions:
            print(f"{strategy_name}: {position:.2f} units")
