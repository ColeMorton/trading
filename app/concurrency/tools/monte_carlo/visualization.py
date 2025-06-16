"""
Monte Carlo Visualization Framework for Concurrency Analysis.

Provides visualization capabilities for Monte Carlo parameter robustness analysis
integrated with the concurrency framework, supporting portfolio-level visualization
and concurrent strategy analysis.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.concurrency.tools.monte_carlo.core import (
    MonteCarloPortfolioResult,
    ParameterStabilityResult,
)

# Try to import seaborn for enhanced visualizations
try:
    import seaborn as sns

    HAS_SEABORN = True
except ImportError:
    HAS_SEABORN = False


class MonteCarloVisualizationConfig:
    """Configuration for Monte Carlo visualizations."""

    def __init__(
        self,
        output_dir: str = "png/concurrency/monte_carlo",
        enable_seaborn: bool = True,
        figure_size: Tuple[int, int] = (12, 8),
        dpi: int = 300,
    ):
        """Initialize visualization configuration.

        Args:
            output_dir: Directory to save visualization outputs
            enable_seaborn: Whether to use seaborn styling (if available)
            figure_size: Default figure size for plots
            dpi: DPI for saved figures
        """
        self.output_dir = output_dir
        self.enable_seaborn = enable_seaborn and HAS_SEABORN
        self.figure_size = figure_size
        self.dpi = dpi

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)


class PortfolioMonteCarloVisualizer:
    """Portfolio-level Monte Carlo visualization toolkit.

    Creates visualizations for Monte Carlo parameter robustness analysis
    across multiple tickers in a portfolio, following concurrency patterns.
    """

    def __init__(self, config: Optional[MonteCarloVisualizationConfig] = None):
        """Initialize the portfolio visualizer.

        Args:
            config: Visualization configuration (uses defaults if None)
        """
        self.config = config or MonteCarloVisualizationConfig()
        self._setup_plotting_style()

    def _setup_plotting_style(self) -> None:
        """Setup matplotlib/seaborn plotting style."""
        try:
            if self.config.enable_seaborn:
                plt.style.use("seaborn-v0_8")
                sns.set_palette("husl")
            else:
                plt.style.use("default")
        except Exception:
            plt.style.use("default")

    def create_portfolio_stability_heatmap(
        self,
        monte_carlo_results: Dict[str, MonteCarloPortfolioResult],
        metric: str = "stability_score",
        save_path: Optional[str] = None,
    ) -> str:
        """Create portfolio-wide stability heatmap.

        Args:
            monte_carlo_results: Monte Carlo results for portfolio
            metric: Metric to visualize ('stability_score', 'parameter_robustness', etc.)
            save_path: Custom save path (optional)

        Returns:
            Path to saved visualization
        """
        if not monte_carlo_results:
            raise ValueError("No Monte Carlo results provided")

        # Collect data across all tickers
        portfolio_data = []
        for ticker, result in monte_carlo_results.items():
            for param_result in result.parameter_results:
                short, long = param_result.parameter_combination
                score = getattr(param_result, metric, 0.0)
                portfolio_data.append(
                    {
                        "ticker": ticker,
                        "short_window": short,
                        "long_window": long,
                        "score": score,
                    }
                )

        if not portfolio_data:
            raise ValueError("No parameter results found in Monte Carlo results")

        df = pd.DataFrame(portfolio_data)

        # Create figure with subplots for each ticker
        tickers = sorted(df["ticker"].unique())
        n_tickers = len(tickers)

        # Calculate subplot layout
        cols = min(3, n_tickers)
        rows = (n_tickers + cols - 1) // cols

        fig, axes = plt.subplots(
            rows,
            cols,
            figsize=(
                self.config.figure_size[0] * cols // 2,
                self.config.figure_size[1] * rows // 2,
            ),
        )

        # Handle single subplot case
        if n_tickers == 1:
            axes = [axes]
        elif rows == 1:
            axes = axes if hasattr(axes, "__iter__") else [axes]
        else:
            axes = axes.flatten()

        for i, ticker in enumerate(tickers):
            ticker_data = df[df["ticker"] == ticker]

            # Create pivot table for heatmap
            heatmap_data = ticker_data.pivot(
                index="long_window", columns="short_window", values="score"
            )

            ax = axes[i] if i < len(axes) else None
            if ax is None:
                continue

            # Create heatmap
            if self.config.enable_seaborn:
                sns.heatmap(
                    heatmap_data,
                    annot=True,
                    fmt=".3f",
                    cmap="RdYlGn",
                    center=0.5,
                    ax=ax,
                    cbar_kws={"shrink": 0.8},
                )
            else:
                im = ax.imshow(
                    heatmap_data.values, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1
                )
                ax.set_xticks(range(len(heatmap_data.columns)))
                ax.set_yticks(range(len(heatmap_data.index)))
                ax.set_xticklabels(heatmap_data.columns)
                ax.set_yticklabels(heatmap_data.index)
                plt.colorbar(im, ax=ax, shrink=0.8)

            ax.set_title(f'{ticker} - {metric.replace("_", " ").title()}')
            ax.set_xlabel("Short Window")
            ax.set_ylabel("Long Window")

        # Hide unused subplots
        for i in range(n_tickers, len(axes)):
            axes[i].set_visible(False)

        plt.tight_layout()

        # Save figure
        if save_path is None:
            save_path = os.path.join(
                self.config.output_dir, f"portfolio_{metric}_heatmap.png"
            )

        plt.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        return save_path

    def create_stability_distribution_plot(
        self,
        monte_carlo_results: Dict[str, MonteCarloPortfolioResult],
        save_path: Optional[str] = None,
    ) -> str:
        """Create distribution plot of stability scores across portfolio.

        Args:
            monte_carlo_results: Monte Carlo results for portfolio
            save_path: Custom save path (optional)

        Returns:
            Path to saved visualization
        """
        if not monte_carlo_results:
            raise ValueError("No Monte Carlo results provided")

        # Collect stability scores
        stability_data = []
        for ticker, result in monte_carlo_results.items():
            for param_result in result.parameter_results:
                stability_data.append(
                    {
                        "ticker": ticker,
                        "stability_score": param_result.stability_score,
                        "parameter_robustness": param_result.parameter_robustness,
                        "regime_consistency": param_result.regime_consistency,
                        "is_stable": param_result.is_stable,
                    }
                )

        if not stability_data:
            raise ValueError("No stability data found")

        df = pd.DataFrame(stability_data)

        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 2, figsize=self.config.figure_size)
        fig.suptitle("Portfolio Monte Carlo Stability Analysis", fontsize=16)

        # Stability score distribution
        axes[0, 0].hist(df["stability_score"], bins=20, alpha=0.7, edgecolor="black")
        axes[0, 0].axvline(
            df["stability_score"].mean(),
            color="red",
            linestyle="--",
            label=f'Mean: {df["stability_score"].mean():.3f}',
        )
        axes[0, 0].set_title("Stability Score Distribution")
        axes[0, 0].set_xlabel("Stability Score")
        axes[0, 0].set_ylabel("Frequency")
        axes[0, 0].legend()

        # Parameter robustness distribution
        axes[0, 1].hist(
            df["parameter_robustness"],
            bins=20,
            alpha=0.7,
            edgecolor="black",
            color="orange",
        )
        axes[0, 1].axvline(
            df["parameter_robustness"].mean(),
            color="red",
            linestyle="--",
            label=f'Mean: {df["parameter_robustness"].mean():.3f}',
        )
        axes[0, 1].set_title("Parameter Robustness Distribution")
        axes[0, 1].set_xlabel("Parameter Robustness")
        axes[0, 1].set_ylabel("Frequency")
        axes[0, 1].legend()

        # Regime consistency distribution
        axes[1, 0].hist(
            df["regime_consistency"],
            bins=20,
            alpha=0.7,
            edgecolor="black",
            color="green",
        )
        axes[1, 0].axvline(
            df["regime_consistency"].mean(),
            color="red",
            linestyle="--",
            label=f'Mean: {df["regime_consistency"].mean():.3f}',
        )
        axes[1, 0].set_title("Regime Consistency Distribution")
        axes[1, 0].set_xlabel("Regime Consistency")
        axes[1, 0].set_ylabel("Frequency")
        axes[1, 0].legend()

        # Stability classification pie chart
        stable_counts = df["is_stable"].value_counts()
        axes[1, 1].pie(
            stable_counts.values,
            labels=["Unstable", "Stable"],
            autopct="%1.1f%%",
            colors=["lightcoral", "lightgreen"],
        )
        axes[1, 1].set_title("Parameter Stability Classification")

        plt.tight_layout()

        # Save figure
        if save_path is None:
            save_path = os.path.join(
                self.config.output_dir, "portfolio_stability_distribution.png"
            )

        plt.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        return save_path

    def create_portfolio_summary_plot(
        self,
        monte_carlo_results: Dict[str, MonteCarloPortfolioResult],
        portfolio_metrics: Dict[str, float],
        save_path: Optional[str] = None,
    ) -> str:
        """Create portfolio-level Monte Carlo summary visualization.

        Args:
            monte_carlo_results: Monte Carlo results for portfolio
            portfolio_metrics: Portfolio-level metrics
            save_path: Custom save path (optional)

        Returns:
            Path to saved visualization
        """
        if not monte_carlo_results:
            raise ValueError("No Monte Carlo results provided")

        fig, axes = plt.subplots(2, 2, figsize=self.config.figure_size)
        fig.suptitle("Portfolio Monte Carlo Analysis Summary", fontsize=16)

        # Ticker-level stability scores
        ticker_scores = []
        ticker_names = []
        for ticker, result in monte_carlo_results.items():
            ticker_names.append(ticker)
            ticker_scores.append(result.portfolio_stability_score)

        bars = axes[0, 0].bar(ticker_names, ticker_scores, alpha=0.7)
        axes[0, 0].axhline(
            y=0.7, color="red", linestyle="--", label="Stability Threshold (0.7)"
        )
        axes[0, 0].set_title("Ticker Stability Scores")
        axes[0, 0].set_ylabel("Portfolio Stability Score")
        axes[0, 0].tick_params(axis="x", rotation=45)
        axes[0, 0].legend()

        # Color bars based on stability
        for i, (bar, score) in enumerate(zip(bars, ticker_scores)):
            bar.set_color("green" if score > 0.7 else "red")

        # Portfolio metrics summary
        metrics_text = f"""Portfolio Metrics:

Total Tickers: {portfolio_metrics.get('total_tickers_analyzed', 0)}
Stable Tickers: {portfolio_metrics.get('stable_tickers_count', 0)}
Stable %: {portfolio_metrics.get('stable_tickers_percentage', 0):.1f}%
Avg Stability: {portfolio_metrics.get('average_stability_score', 0):.3f}

Simulation Parameters:
Simulations: {portfolio_metrics.get('simulation_parameters', {}).get('num_simulations', 'N/A')}
Confidence: {portfolio_metrics.get('simulation_parameters', {}).get('confidence_level', 'N/A')}
Max Params: {portfolio_metrics.get('simulation_parameters', {}).get('max_parameters_tested', 'N/A')}"""

        axes[0, 1].text(
            0.1,
            0.5,
            metrics_text,
            fontsize=10,
            verticalalignment="center",
            bbox=dict(boxstyle="round", facecolor="lightblue", alpha=0.8),
        )
        axes[0, 1].set_xlim(0, 1)
        axes[0, 1].set_ylim(0, 1)
        axes[0, 1].axis("off")
        axes[0, 1].set_title("Portfolio Summary")

        # Recommended parameters by ticker
        recommendations = []
        for ticker, result in monte_carlo_results.items():
            if result.recommended_parameters:
                short, long = result.recommended_parameters
                recommendations.append(
                    {
                        "ticker": ticker,
                        "short": short,
                        "long": long,
                        "stability": result.portfolio_stability_score,
                    }
                )

        if recommendations:
            rec_df = pd.DataFrame(recommendations)
            scatter = axes[1, 0].scatter(
                rec_df["short"],
                rec_df["long"],
                c=rec_df["stability"],
                cmap="RdYlGn",
                s=100,
                alpha=0.7,
                edgecolors="black",
            )

            # Add ticker labels
            for _, row in rec_df.iterrows():
                axes[1, 0].annotate(
                    row["ticker"],
                    (row["short"], row["long"]),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=8,
                )

            plt.colorbar(scatter, ax=axes[1, 0], shrink=0.8, label="Stability Score")
            axes[1, 0].set_title("Recommended Parameters")
            axes[1, 0].set_xlabel("Short Window")
            axes[1, 0].set_ylabel("Long Window")
        else:
            axes[1, 0].text(
                0.5,
                0.5,
                "No recommendations available",
                ha="center",
                va="center",
                transform=axes[1, 0].transAxes,
            )
            axes[1, 0].set_title("Recommended Parameters")

        # Stability vs robustness scatter
        stability_scores = []
        robustness_scores = []
        ticker_labels = []

        for ticker, result in monte_carlo_results.items():
            if result.parameter_results:
                # Use best parameter result for each ticker
                best_result = max(
                    result.parameter_results, key=lambda x: x.stability_score
                )
                stability_scores.append(best_result.stability_score)
                robustness_scores.append(best_result.parameter_robustness)
                ticker_labels.append(ticker)

        if stability_scores and robustness_scores:
            axes[1, 1].scatter(stability_scores, robustness_scores, alpha=0.7, s=100)

            # Add ticker labels
            for i, ticker in enumerate(ticker_labels):
                axes[1, 1].annotate(
                    ticker,
                    (stability_scores[i], robustness_scores[i]),
                    xytext=(5, 5),
                    textcoords="offset points",
                    fontsize=8,
                )

            axes[1, 1].axvline(
                x=0.7,
                color="red",
                linestyle="--",
                alpha=0.5,
                label="Stability Threshold",
            )
            axes[1, 1].axhline(
                y=0.6,
                color="red",
                linestyle="--",
                alpha=0.5,
                label="Robustness Threshold",
            )
            axes[1, 1].set_title("Stability vs Robustness")
            axes[1, 1].set_xlabel("Stability Score")
            axes[1, 1].set_ylabel("Parameter Robustness")
            axes[1, 1].legend()
        else:
            axes[1, 1].text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=axes[1, 1].transAxes,
            )
            axes[1, 1].set_title("Stability vs Robustness")

        plt.tight_layout()

        # Save figure
        if save_path is None:
            save_path = os.path.join(
                self.config.output_dir, "portfolio_monte_carlo_summary.png"
            )

        plt.savefig(save_path, dpi=self.config.dpi, bbox_inches="tight")
        plt.close()

        return save_path

    def generate_portfolio_visualizations(
        self,
        monte_carlo_results: Dict[str, MonteCarloPortfolioResult],
        portfolio_metrics: Dict[str, float],
    ) -> List[str]:
        """Generate complete set of portfolio Monte Carlo visualizations.

        Args:
            monte_carlo_results: Monte Carlo results for portfolio
            portfolio_metrics: Portfolio-level metrics

        Returns:
            List of paths to saved visualizations
        """
        saved_paths = []

        try:
            # Portfolio stability heatmap
            path = self.create_portfolio_stability_heatmap(monte_carlo_results)
            saved_paths.append(path)
        except Exception as e:
            print(f"Warning: Failed to create stability heatmap: {e}")

        try:
            # Stability distribution plot
            path = self.create_stability_distribution_plot(monte_carlo_results)
            saved_paths.append(path)
        except Exception as e:
            print(f"Warning: Failed to create distribution plot: {e}")

        try:
            # Portfolio summary plot
            path = self.create_portfolio_summary_plot(
                monte_carlo_results, portfolio_metrics
            )
            saved_paths.append(path)
        except Exception as e:
            print(f"Warning: Failed to create summary plot: {e}")

        return saved_paths


def create_monte_carlo_visualizations(
    monte_carlo_results: Dict[str, MonteCarloPortfolioResult],
    portfolio_metrics: Dict[str, float],
    config: Optional[MonteCarloVisualizationConfig] = None,
) -> List[str]:
    """Create Monte Carlo visualizations for portfolio analysis.

    Args:
        monte_carlo_results: Monte Carlo results for portfolio
        portfolio_metrics: Portfolio-level metrics
        config: Visualization configuration (optional)

    Returns:
        List of paths to saved visualizations
    """
    visualizer = PortfolioMonteCarloVisualizer(config)
    return visualizer.generate_portfolio_visualizations(
        monte_carlo_results, portfolio_metrics
    )
