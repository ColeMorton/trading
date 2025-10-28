"""
Monte Carlo Parameter Visualization Tools

This module provides comprehensive visualization capabilities for Monte Carlo
parameter robustness analysis results, including stability heatmaps, confidence
interval plots, and performance distribution analysis.
"""

import os

from matplotlib.gridspec import GridSpec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import polars as pl
from scipy import stats

from app.strategies.monte_carlo.parameter_robustness import ParameterStabilityResult


# Complete Color Palette Constants
PRIMARY_DATA = "#26c6da"  # Cyan - Primary data
SECONDARY_DATA = "#7e57c2"  # Purple - Secondary data/negative
TERTIARY_DATA = "#3179f5"  # Blue - Tertiary data/warnings
BACKGROUND = "#fff"  # Pure white
PRIMARY_TEXT = "#121212"  # Near black
BODY_TEXT = "#444444"  # Dark gray
MUTED_TEXT = "#717171"  # Medium gray

# Try to import seaborn, use matplotlib fallback if not available
try:
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False
    print("Seaborn not available, using matplotlib-only visualizations")


class ParameterStabilityVisualizer:
    """
    Comprehensive visualization toolkit for Monte Carlo parameter stability analysis.

    This class creates various visualizations to help understand parameter robustness,
    stability patterns, and confidence intervals across different market conditions.
    """

    def __init__(self, output_dir: str = "png/monte_carlo/parameter_stability"):
        """
        Initialize the visualizer.

        Args:
            output_dir: Directory to save visualization outputs
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set plotting style
        try:
            plt.style.use("seaborn-v0_8")
        except:
            plt.style.use("default")

        if HAS_SEABORN:
            sns.set_palette("husl")

    def create_stability_heatmap(
        self,
        results: list[ParameterStabilityResult],
        ticker: str,
        metric: str = "stability_score",
    ) -> None:
        """
        Create heatmap showing parameter stability across window combinations.

        Args:
            results: List of parameter stability results
            ticker: Ticker symbol for title
            metric: Metric to visualize ('stability_score', 'parameter_robustness', etc.)
        """
        if not results:
            return

        # Extract parameter combinations and scores
        data_points = []
        for result in results:
            short, long = result.parameter_combination
            score = getattr(result, metric, 0)
            data_points.append((short, long, score))

        if not data_points:
            return

        # Create DataFrame for heatmap
        df = pd.DataFrame(data_points, columns=["Fast_Period", "Slow_Period", metric])

        # Pivot for heatmap
        heatmap_data = df.pivot(
            index="Slow_Period", columns="Fast_Period", values=metric,
        )

        # Create figure
        plt.figure(figsize=(12, 8))

        # Create heatmap
        if HAS_SEABORN:
            ax = sns.heatmap(
                heatmap_data,
                annot=True,
                fmt=".3f",
                cmap="RdYlGn",
                center=0.5,
                square=True,
                linewidths=0.5,
                cbar_kws={"label": metric.replace("_", " ").title()},
            )
        else:
            # Matplotlib-only heatmap
            fig, ax = plt.subplots(figsize=(12, 8))
            im = ax.imshow(heatmap_data.values, cmap="RdYlGn", aspect="auto")

            # Add colorbar
            cbar = plt.colorbar(im, ax=ax)
            cbar.set_label(metric.replace("_", " ").title())

            # Set ticks and labels
            ax.set_xticks(range(len(heatmap_data.columns)))
            ax.set_yticks(range(len(heatmap_data.index)))
            ax.set_xticklabels(heatmap_data.columns)
            ax.set_yticklabels(heatmap_data.index)

            # Add value annotations
            for i in range(len(heatmap_data.index)):
                for j in range(len(heatmap_data.columns)):
                    value = heatmap_data.iloc[i, j]
                    if not pd.isna(value):
                        ax.text(j, i, f"{value:.3f}", ha="center", va="center")

        plt.title(
            f'{ticker} - Parameter {metric.replace("_", " ").title()}\nMonte Carlo Stability Analysis',
        )
        plt.xlabel("Fast Period (Fast MA)")
        plt.ylabel("Slow Period (Slow MA)")

        # Add stability threshold line if applicable
        if metric == "stability_score":
            # Add text annotation for stability threshold
            plt.figtext(
                0.02,
                0.02,
                "Green: Stable (>0.7), Yellow: Moderate (0.4-0.7), Red: Unstable (<0.4)",
                fontsize=8,
                ha="left",
            )

        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, f"{ticker}_{metric}_heatmap.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def create_confidence_interval_plot(
        self,
        results: list[ParameterStabilityResult],
        ticker: str,
        performance_metric: str = "Sharpe Ratio",
    ) -> None:
        """
        Create plot showing confidence intervals for performance metrics.

        Args:
            results: List of parameter stability results
            ticker: Ticker symbol for title
            performance_metric: Performance metric to analyze
        """
        if not results:
            return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Prepare data
        param_labels = []
        base_values = []
        mc_means = []
        ci_lowers = []
        ci_uppers = []
        stability_scores = []

        for result in results:
            short, long = result.parameter_combination
            param_labels.append(f"{short}/{long}")

            base_values.append(result.base_performance.get(performance_metric, 0))
            mc_means.append(result.performance_mean.get(performance_metric, 0))

            ci = result.confidence_intervals.get(performance_metric, (0, 0))
            ci_lowers.append(ci[0])
            ci_uppers.append(ci[1])

            stability_scores.append(result.stability_score)

        if not param_labels:
            return

        x_pos = np.arange(len(param_labels))

        # Plot 1: Confidence intervals
        ax1.errorbar(
            x_pos,
            mc_means,
            yerr=[
                np.array(mc_means) - np.array(ci_lowers),
                np.array(ci_uppers) - np.array(mc_means),
            ],
            fmt="o",
            capsize=5,
            capthick=2,
            label="Monte Carlo Mean ± CI",
        )

        ax1.scatter(
            x_pos,
            base_values,
            color=SECONDARY_DATA,
            s=50,
            alpha=0.7,
            label="Base Performance",
        )

        ax1.set_xlabel("Parameter Combination (Short/Slow Periods)")
        ax1.set_ylabel(performance_metric)
        ax1.set_title(
            f"{ticker} - {performance_metric} Confidence Intervals\nMonte Carlo Analysis",
        )
        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(param_labels, rotation=45)
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Plot 2: Stability scores
        colors = [
            "green" if score > 0.7 else "orange" if score > 0.4 else "red"
            for score in stability_scores
        ]

        ax2.bar(x_pos, stability_scores, color=colors, alpha=0.7)
        ax2.axhline(
            y=0.7,
            color=PRIMARY_DATA,
            linestyle="--",
            alpha=0.7,
            label="Stable Threshold (0.7)",
        )
        ax2.axhline(
            y=0.4,
            color=TERTIARY_DATA,
            linestyle="--",
            alpha=0.7,
            label="Moderate Threshold (0.4)",
        )

        ax2.set_xlabel("Parameter Combination (Short/Slow Periods)")
        ax2.set_ylabel("Stability Score")
        ax2.set_title("Parameter Stability Scores")
        ax2.set_xticks(x_pos)
        ax2.set_xticklabels(param_labels, rotation=45)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, 1)

        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, f"{ticker}_confidence_intervals.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def create_performance_distribution_plot(
        self,
        result: ParameterStabilityResult,
        ticker: str,
        performance_metric: str = "Sharpe Ratio",
    ) -> None:
        """
        Create distribution plot for a specific parameter combination.

        Args:
            result: Single parameter stability result
            ticker: Ticker symbol
            performance_metric: Performance metric to analyze
        """
        if not result.monte_carlo_results:
            return

        short, long = result.parameter_combination

        # Extract performance values
        values = [
            r.get(performance_metric, 0)
            for r in result.monte_carlo_results
            if r.get(performance_metric) is not None
        ]

        if not values:
            return

        values = np.array(values)
        base_value = result.base_performance.get(performance_metric, 0)

        # Create figure with subplots
        fig = plt.figure(figsize=(15, 10))
        gs = GridSpec(2, 2, figure=fig)

        # Main distribution plot
        ax1 = fig.add_subplot(gs[0, :])

        # Plot histogram
        n_bins = min(50, len(values) // 10)
        ax1.hist(
            values,
            bins=n_bins,
            density=True,
            alpha=0.7,
            color=TERTIARY_DATA,
            edgecolor=PRIMARY_TEXT,
        )

        # Fit and plot normal distribution
        mu, sigma = stats.norm.fit(values)
        x_norm = np.linspace(values.min(), values.max(), 100)
        ax1.plot(
            x_norm,
            stats.norm.pdf(x_norm, mu, sigma),
            "r-",
            linewidth=2,
            label=f"Normal Fit (μ={mu:.3f}, σ={sigma:.3f})",
        )

        # Add base performance line
        ax1.axvline(
            base_value,
            color=PRIMARY_DATA,
            linestyle="--",
            linewidth=2,
            label=f"Base Performance: {base_value:.3f}",
        )

        # Add confidence intervals
        ci = result.confidence_intervals.get(performance_metric, (0, 0))
        ax1.axvline(
            ci[0],
            color=TERTIARY_DATA,
            linestyle=":",
            alpha=0.7,
            label=f"95% CI Lower: {ci[0]:.3f}",
        )
        ax1.axvline(
            ci[1],
            color=TERTIARY_DATA,
            linestyle=":",
            alpha=0.7,
            label=f"95% CI Upper: {ci[1]:.3f}",
        )

        ax1.set_xlabel(performance_metric)
        ax1.set_ylabel("Density")
        ax1.set_title(
            f"{ticker} - {performance_metric} Distribution\nParameter: {short}/{long} Windows, {len(values)} Simulations",
        )
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Q-Q plot
        ax2 = fig.add_subplot(gs[1, 0])
        stats.probplot(values, dist="norm", plot=ax2)
        ax2.set_title("Q-Q Plot (Normality Check)")
        ax2.grid(True, alpha=0.3)

        # Box plot
        ax3 = fig.add_subplot(gs[1, 1])
        box_data = [values]
        bp = ax3.boxplot(box_data, patch_artist=True)
        bp["boxes"][0].set_facecolor(TERTIARY_DATA)
        ax3.axhline(
            base_value, color=PRIMARY_DATA, linestyle="--", label="Base Performance",
        )
        ax3.set_ylabel(performance_metric)
        ax3.set_title("Distribution Summary")
        ax3.legend()
        ax3.grid(True, alpha=0.3)

        # Add statistics text
        stats_text = f"""
        Statistics:
        Mean: {np.mean(values):.3f}
        Median: {np.median(values):.3f}
        Std: {np.std(values):.3f}
        Min: {np.min(values):.3f}
        Max: {np.max(values):.3f}

        Stability Score: {result.stability_score:.3f}
        Parameter Robustness: {result.parameter_robustness:.3f}
        """

        fig.text(
            0.02,
            0.02,
            stats_text,
            fontsize=9,
            verticalalignment="bottom",
            bbox={"boxstyle": "round", "facecolor": BACKGROUND, "alpha": 0.5},
        )

        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, f"{ticker}_{short}_{long}_distribution.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def create_parameter_landscape_3d(
        self, results: list[ParameterStabilityResult], ticker: str,
    ) -> None:
        """
        Create 3D landscape plot of parameter stability.

        Args:
            results: List of parameter stability results
            ticker: Ticker symbol
        """
        if not results:
            return

        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection="3d")

        # Extract data
        short_windows = []
        long_windows = []
        stability_scores = []

        for result in results:
            short, long = result.parameter_combination
            short_windows.append(short)
            long_windows.append(long)
            stability_scores.append(result.stability_score)

        if not short_windows:
            return

        # Create scatter plot
        colors = plt.cm.RdYlGn(np.array(stability_scores))
        scatter = ax.scatter(
            short_windows, long_windows, stability_scores, c=colors, s=60, alpha=0.8,
        )

        # Add surface if we have enough points
        if len(results) > 10:
            try:
                from scipy.interpolate import griddata

                # Create grid
                short_grid = np.linspace(min(short_windows), max(short_windows), 20)
                long_grid = np.linspace(min(long_windows), max(long_windows), 20)
                short_mesh, long_mesh = np.meshgrid(short_grid, long_grid)

                # Interpolate stability scores
                points = list(zip(short_windows, long_windows, strict=False))
                stability_mesh = griddata(
                    points, stability_scores, (short_mesh, long_mesh), method="cubic",
                )

                # Plot surface
                ax.plot_surface(
                    short_mesh, long_mesh, stability_mesh, alpha=0.3, cmap="RdYlGn",
                )

            except Exception:
                # If interpolation fails, skip surface
                pass

        ax.set_xlabel("Fast Period")
        ax.set_ylabel("Slow Period")
        ax.set_zlabel("Stability Score")
        ax.set_title(f"{ticker} - Parameter Stability Landscape\n3D Visualization")

        # Add colorbar
        plt.colorbar(scatter, ax=ax, shrink=0.5, aspect=5, label="Stability Score")

        plt.savefig(
            os.path.join(self.output_dir, f"{ticker}_stability_landscape_3d.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def create_regime_consistency_plot(
        self, results: list[ParameterStabilityResult], ticker: str,
    ) -> None:
        """
        Create plot showing regime consistency across parameters.

        Args:
            results: List of parameter stability results
            ticker: Ticker symbol
        """
        if not results:
            return

        # Filter results with regime data
        regime_results = [r for r in results if hasattr(r, "regime_consistency")]

        if not regime_results:
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Plot 1: Stability vs Regime Consistency scatter
        stability_scores = [r.stability_score for r in regime_results]
        regime_scores = [r.regime_consistency for r in regime_results]
        param_labels = [
            f"{r.parameter_combination[0]}/{r.parameter_combination[1]}"
            for r in regime_results
        ]

        ax1.scatter(
            stability_scores,
            regime_scores,
            c=range(len(regime_results)),
            cmap="viridis",
            s=60,
            alpha=0.7,
        )

        # Add parameter labels for top performers
        top_indices = np.argsort(
            [s + r for s, r in zip(stability_scores, regime_scores, strict=False)],
        )[-5:]
        for i in top_indices:
            ax1.annotate(
                param_labels[i],
                (stability_scores[i], regime_scores[i]),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=8,
            )

        ax1.set_xlabel("Stability Score")
        ax1.set_ylabel("Regime Consistency")
        ax1.set_title("Parameter Stability vs Regime Consistency")
        ax1.grid(True, alpha=0.3)

        # Add quadrant lines
        ax1.axhline(y=0.5, color=MUTED_TEXT, linestyle="--", alpha=0.5)
        ax1.axvline(x=0.7, color=MUTED_TEXT, linestyle="--", alpha=0.5)

        # Plot 2: Combined score ranking
        combined_scores = [
            0.7 * s + 0.3 * r
            for s, r in zip(stability_scores, regime_scores, strict=False)
        ]
        sorted_indices = np.argsort(combined_scores)[::-1]

        sorted_labels = [param_labels[i] for i in sorted_indices]
        sorted_scores = [combined_scores[i] for i in sorted_indices]

        # Show top 10
        top_10 = min(10, len(sorted_labels))
        colors = plt.cm.RdYlGn(np.array(sorted_scores[:top_10]))

        bars = ax2.barh(range(top_10), sorted_scores[:top_10], color=colors)
        ax2.set_yticks(range(top_10))
        ax2.set_yticklabels(sorted_labels[:top_10])
        ax2.set_xlabel("Combined Score (0.7×Stability + 0.3×Regime)")
        ax2.set_title("Top Parameter Combinations")
        ax2.grid(True, alpha=0.3)

        # Add score values on bars
        for i, (bar, score) in enumerate(
            zip(bars, sorted_scores[:top_10], strict=False),
        ):
            ax2.text(
                score + 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{score:.3f}",
                va="center",
                fontsize=8,
            )

        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, f"{ticker}_regime_consistency.png"),
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()

    def create_comprehensive_report(
        self, all_results: dict[str, list[ParameterStabilityResult]],
    ) -> None:
        """
        Create comprehensive visualization report for all tickers.

        Args:
            all_results: Dictionary mapping tickers to their stability results
        """
        for ticker, results in all_results.items():
            if not results:
                continue

            print(f"Creating visualizations for {ticker}...")

            # Create all visualization types
            self.create_stability_heatmap(results, ticker, "stability_score")
            self.create_stability_heatmap(results, ticker, "parameter_robustness")
            self.create_confidence_interval_plot(results, ticker, "Sharpe Ratio")
            self.create_confidence_interval_plot(results, ticker, "Total Return [%]")
            self.create_parameter_landscape_3d(results, ticker)
            self.create_regime_consistency_plot(results, ticker)

            # Create distribution plots for top 3 parameter combinations
            sorted_results = sorted(
                results, key=lambda x: x.stability_score, reverse=True,
            )
            for i, result in enumerate(sorted_results[:3]):
                self.create_performance_distribution_plot(
                    result, f"{ticker}_top_{i+1}", "Sharpe Ratio",
                )

        print(f"All visualizations saved to {self.output_dir}")


def visualize_monte_carlo_results(
    results_file: str, output_dir: str | None = None,
) -> None:
    """
    Convenience function to create visualizations from saved results.

    Args:
        results_file: Path to CSV file with Monte Carlo results
        output_dir: Output directory for visualizations
    """
    if output_dir is None:
        output_dir = "png/monte_carlo/parameter_stability"

    ParameterStabilityVisualizer(output_dir)

    # Load results
    try:
        df = pl.read_csv(results_file)

        # Group by ticker
        ticker_results = {}
        for ticker in df["Ticker"].unique():
            ticker_df = df.filter(pl.col("Ticker") == ticker)
            ticker_results[ticker] = ticker_df.to_dicts()

        # Create mock ParameterStabilityResult objects for visualization
        # This is a simplified version - in practice, you'd load full result objects

        print(f"Creating visualizations from {results_file}")

        # For now, create basic heatmaps from the available data
        for ticker, data in ticker_results.items():
            if data:
                # Create stability heatmap from summary data
                fig, ax = plt.subplots(figsize=(10, 8))

                # Extract data for heatmap
                short_windows = [d.get("Fast_Period", 0) for d in data]
                long_windows = [d.get("Slow_Period", 0) for d in data]
                stability_scores = [
                    d.get("Stability_Score", 0)
                    for d in data
                    if d.get("Stability_Score") is not None
                ]

                if stability_scores:
                    # Create DataFrame for heatmap
                    heatmap_df = pd.DataFrame(
                        {
                            "Fast_Period": short_windows[: len(stability_scores)],
                            "Slow_Period": long_windows[: len(stability_scores)],
                            "Stability_Score": stability_scores,
                        },
                    )

                    # Pivot for heatmap
                    heatmap_data = heatmap_df.pivot(
                        index="Slow_Period",
                        columns="Fast_Period",
                        values="Stability_Score",
                    )

                    # Create heatmap
                    if HAS_SEABORN:
                        sns.heatmap(
                            heatmap_data,
                            annot=True,
                            fmt=".3f",
                            cmap="RdYlGn",
                            center=0.5,
                        )
                    else:
                        # Matplotlib-only heatmap
                        im = plt.imshow(
                            heatmap_data.values, cmap="RdYlGn", aspect="auto",
                        )
                        plt.colorbar(im)

                        # Set ticks and labels
                        plt.xticks(
                            range(len(heatmap_data.columns)), heatmap_data.columns,
                        )
                        plt.yticks(range(len(heatmap_data.index)), heatmap_data.index)

                        # Add value annotations
                        for i in range(len(heatmap_data.index)):
                            for j in range(len(heatmap_data.columns)):
                                value = heatmap_data.iloc[i, j]
                                if not pd.isna(value):
                                    plt.text(
                                        j, i, f"{value:.3f}", ha="center", va="center",
                                    )
                    plt.title(f"{ticker} - Parameter Stability Scores")
                    plt.xlabel("Fast Period")
                    plt.ylabel("Slow Period")

                    plt.tight_layout()
                    plt.savefig(
                        os.path.join(output_dir, f"{ticker}_stability_from_csv.png"),
                        dpi=300,
                        bbox_inches="tight",
                    )
                    plt.close()

        print(f"Basic visualizations created in {output_dir}")

    except Exception as e:
        print(f"Error creating visualizations: {e!s}")


if __name__ == "__main__":
    # Example usage
    output_dir = "png/monte_carlo/parameter_stability"
    visualizer = ParameterStabilityVisualizer(output_dir)

    print(f"Parameter stability visualizer initialized. Output directory: {output_dir}")
    print("Use the visualizer methods to create specific plots, or run:")
    print("visualize_monte_carlo_results('path/to/results.csv')")
