"""
Slippage Plotting Module

This module contains functions for visualizing slippage analysis results through plots.
"""

from collections.abc import Callable

import matplotlib.pyplot as plt
import polars as pl

from app.utils import add_peak_labels, find_prominent_peaks


def plot_results(ticker: str, results_df: pl.DataFrame, log: Callable) -> None:
    """
    Plot sensitivity analysis results.

    Args:
        ticker (str): Ticker symbol
        results_df (pl.DataFrame): Results dataframe
        log (Callable): Logging function
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16), sharex=True)

    # Plot total return and win rate
    ax1.plot(
        results_df["Slippage Percentage"],
        results_df["Total Return"],
        label="Total Return",
    )
    ax1.set_ylabel("Return %")
    ax1.grid(True)

    # Calculate max Total Return and target levels
    max_return = results_df["Total Return"].max()
    target_levels = {
        "5%": max_return * 0.95,
        "10%": max_return * 0.90,
        "15%": max_return * 0.85,
    }

    # Add vertical lines at target levels
    colors = ["green", "yellow", "red"]
    lines = []  # Store line objects for legend
    for (label, target), color in zip(target_levels.items(), colors, strict=False):
        # Find the first slippage percentage where Total Return drops below target
        mask = results_df["Total Return"] <= target
        if mask.any():
            slippage_at_target = results_df.filter(mask)["Slippage Percentage"][0]
            line = ax1.axvline(
                x=slippage_at_target,
                color=color,
                linestyle="--",
                alpha=0.5,
            )
            lines.append(
                (line, f"{label} below max at {slippage_at_target:.2f}% slippage"),
            )
            ax1.text(
                slippage_at_target,
                ax1.get_ylim()[1],
                f"{slippage_at_target:.2f}%",
                rotation=90,
                va="top",
            )

    ax1_twin = ax1.twinx()
    ax1_twin.plot(
        results_df["Slippage Percentage"],
        results_df["Win Rate"],
        color="tab:red",
        label="Win Rate",
    )
    ax1_twin.set_ylabel("Win Rate %", color="tab:red")
    ax1_twin.tick_params(axis="y", labelcolor="tab:red")

    # Create combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_twin.get_legend_handles_labels()

    # Extract vertical lines and labels
    vertical_lines = [line for line, _ in lines]
    vertical_labels = [label for _, label in lines]

    all_lines = lines1 + lines2 + vertical_lines
    all_labels = labels1 + labels2 + vertical_labels
    ax1.legend(all_lines, all_labels, loc="center left", bbox_to_anchor=(1.15, 0.5))

    # Add peak labels for Total Return
    total_return_peaks = find_prominent_peaks(
        results_df["Slippage Percentage"].to_numpy(),
        results_df["Total Return"].to_numpy(),
    )
    add_peak_labels(
        ax1,
        results_df["Slippage Percentage"].to_numpy(),
        results_df["Total Return"].to_numpy(),
        total_return_peaks,
    )

    # Plot expectancy
    ax2.plot(
        results_df["Slippage Percentage"],
        results_df["Expectancy"],
        label="Expectancy",
        color="tab:green",
    )
    ax2.set_xlabel("Slippage Percentage")
    ax2.set_ylabel("Expectancy %")
    ax2.legend()
    ax2.grid(True)

    fig.suptitle(
        f"{ticker} Total Return, Win Rate, and Expectancy vs Slippage Percentage",
    )
    plt.tight_layout()

    # Save the plot
    plot_filename = f"png/ma_cross/parameter_sensitivity/{ticker}_slippage.png"
    plt.savefig(plot_filename, bbox_inches="tight")
    log(f"Plot saved as {plot_filename}")

    plt.show()
