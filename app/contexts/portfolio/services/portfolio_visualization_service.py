"""
Portfolio Visualization Service

Unified service for creating portfolio analysis visualizations,
integrating with the existing headless plotting system.
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go
import vectorbt as vbt
from plotly.subplots import make_subplots

from app.contexts.portfolio.services.benchmark_comparison_service import (
    ComparisonMetrics,
)
from app.contexts.portfolio.services.risk_metrics_calculator import RiskMetrics
from app.tools.plotting import configure_headless_backend


@dataclass
class PlotConfig:
    """Configuration for plot generation."""

    output_dir: str = "data/outputs/portfolio_review/plots"
    width: int = 1200
    height: int = 800
    save_html: bool = True
    save_png: bool = True
    include_benchmark: bool = True
    include_risk_metrics: bool = True


@dataclass
class VisualizationResults:
    """Results from visualization generation."""

    plot_paths: List[str]
    html_files: List[str]
    png_files: List[str]
    success: bool
    error_message: Optional[str] = None


class PortfolioVisualizationService:
    """
    Service for creating comprehensive portfolio visualizations.

    Integrates with the existing headless plotting system to create:
    - Portfolio performance charts
    - Benchmark comparison plots
    - Risk metrics visualizations
    - Drawdown analysis
    - Distribution analysis
    """

    def __init__(self, plot_config: PlotConfig = None, logger=None):
        """Initialize portfolio visualization service."""
        self.config = plot_config or PlotConfig()
        self.logger = logger
        self.plot_paths = []

    def create_comprehensive_portfolio_plots(
        self,
        portfolio: "vbt.Portfolio",
        benchmark_portfolio: Optional["vbt.Portfolio"] = None,
        risk_metrics: Optional[RiskMetrics] = None,
        comparison_metrics: Optional[ComparisonMetrics] = None,
        title_prefix: str = "Portfolio",
    ) -> VisualizationResults:
        """
        Create comprehensive portfolio analysis plots.

        Args:
            portfolio: Main portfolio to analyze
            benchmark_portfolio: Optional benchmark portfolio
            risk_metrics: Optional risk metrics
            comparison_metrics: Optional benchmark comparison metrics
            title_prefix: Prefix for plot titles

        Returns:
            VisualizationResults with generated plot information
        """
        try:
            # Configure headless backend
            configure_headless_backend()

            # Create output directory
            os.makedirs(self.config.output_dir, exist_ok=True)

            generated_files = []

            # 1. Main portfolio performance chart
            performance_files = self._create_portfolio_performance_chart(
                portfolio, f"{title_prefix} Performance Analysis"
            )
            generated_files.extend(performance_files)

            # 2. Benchmark comparison if available
            if benchmark_portfolio and self.config.include_benchmark:
                comparison_files = self._create_benchmark_comparison_chart(
                    portfolio, benchmark_portfolio, comparison_metrics
                )
                generated_files.extend(comparison_files)

            # 3. Risk metrics visualization if available
            if risk_metrics and self.config.include_risk_metrics:
                risk_files = self._create_risk_metrics_chart(risk_metrics, title_prefix)
                generated_files.extend(risk_files)

            # 4. Drawdown analysis
            drawdown_files = self._create_drawdown_analysis_chart(
                portfolio, title_prefix
            )
            generated_files.extend(drawdown_files)

            # 5. Returns distribution analysis
            distribution_files = self._create_returns_distribution_chart(
                portfolio, title_prefix
            )
            generated_files.extend(distribution_files)

            # Separate HTML and PNG files
            html_files = [f for f in generated_files if f.endswith(".html")]
            png_files = [f for f in generated_files if f.endswith(".png")]

            return VisualizationResults(
                plot_paths=generated_files,
                html_files=html_files,
                png_files=png_files,
                success=True,
            )

        except Exception as e:
            self._log(f"Error creating portfolio plots: {str(e)}", "error")
            return VisualizationResults(
                plot_paths=[],
                html_files=[],
                png_files=[],
                success=False,
                error_message=str(e),
            )

    def _create_portfolio_performance_chart(
        self, portfolio: "vbt.Portfolio", title: str
    ) -> List[str]:
        """Create main portfolio performance chart with multiple subplots."""
        try:
            # Get portfolio data
            portfolio_value = portfolio.value()
            portfolio_returns = portfolio.returns()

            # Handle drawdowns safely
            try:
                drawdowns = portfolio.drawdowns.drawdown
            except:
                # Create fallback zero drawdowns
                drawdowns = portfolio_returns * 0

            # Create subplot figure with 4 rows
            fig = make_subplots(
                rows=4,
                cols=1,
                subplot_titles=[
                    "Portfolio Value",
                    "Cumulative Returns",
                    "Drawdowns",
                    "Underwater Curve",
                ],
                vertical_spacing=0.08,
                specs=[
                    [{"secondary_y": False}],
                    [{"secondary_y": False}],
                    [{"secondary_y": False}],
                    [{"secondary_y": False}],
                ],
            )

            # 1. Portfolio value
            fig.add_trace(
                go.Scatter(
                    x=portfolio_value.index,
                    y=portfolio_value.values,
                    mode="lines",
                    name="Portfolio Value",
                    line=dict(color="green", width=2),
                ),
                row=1,
                col=1,
            )

            # 2. Cumulative returns
            cum_returns = portfolio_returns.cumsum()
            fig.add_trace(
                go.Scatter(
                    x=cum_returns.index,
                    y=cum_returns.values,
                    mode="lines",
                    name="Cumulative Returns",
                    line=dict(color="orange", width=2),
                ),
                row=2,
                col=1,
            )

            # 3. Drawdowns
            if hasattr(drawdowns, "index"):
                dd_x = drawdowns.index
                dd_y = drawdowns.values if hasattr(drawdowns, "values") else drawdowns
            else:
                dd_x = portfolio_returns.index
                dd_y = [0] * len(portfolio_returns)

            fig.add_trace(
                go.Scatter(
                    x=dd_x,
                    y=dd_y,
                    mode="lines",
                    fill="tonexty",
                    name="Drawdowns",
                    line=dict(color="red", width=1),
                    fillcolor="rgba(255,0,0,0.3)",
                ),
                row=3,
                col=1,
            )

            # 4. Underwater curve (same as drawdowns for now)
            fig.add_trace(
                go.Scatter(
                    x=dd_x,
                    y=dd_y,
                    mode="lines",
                    name="Underwater",
                    line=dict(color="darkred", width=2),
                ),
                row=4,
                col=1,
            )

            # Update layout
            fig.update_layout(
                title=title,
                height=self.config.height,
                width=self.config.width,
                showlegend=False,
                template="plotly_white",
            )

            # Save files
            return self._save_plot(fig, "portfolio_performance")

        except Exception as e:
            self._log(f"Error creating performance chart: {str(e)}", "error")
            return []

    def _create_benchmark_comparison_chart(
        self,
        portfolio: "vbt.Portfolio",
        benchmark_portfolio: "vbt.Portfolio",
        comparison_metrics: Optional[ComparisonMetrics] = None,
    ) -> List[str]:
        """Create benchmark comparison chart."""
        try:
            # Get data
            portfolio_value = portfolio.value()
            benchmark_value = benchmark_portfolio.value()

            # Normalize to same starting point
            portfolio_normalized = portfolio_value / portfolio_value.iloc[0]
            benchmark_normalized = benchmark_value / benchmark_value.iloc[0]

            # Create figure
            fig = go.Figure()

            # Add portfolio line
            fig.add_trace(
                go.Scatter(
                    x=portfolio_normalized.index,
                    y=portfolio_normalized.values,
                    mode="lines",
                    name="Strategy Portfolio",
                    line=dict(color="blue", width=2),
                )
            )

            # Add benchmark line
            fig.add_trace(
                go.Scatter(
                    x=benchmark_normalized.index,
                    y=benchmark_normalized.values,
                    mode="lines",
                    name="Benchmark",
                    line=dict(color="gray", width=2, dash="dash"),
                )
            )

            # Add comparison metrics as annotations if available
            annotations = []
            if comparison_metrics:
                annotations.append(
                    dict(
                        x=0.02,
                        y=0.98,
                        xref="paper",
                        yref="paper",
                        text=f"Excess Return: {comparison_metrics.excess_return:.2%}<br>"
                        f"Information Ratio: {comparison_metrics.information_ratio:.2f}<br>"
                        f"Beta: {comparison_metrics.beta:.2f}",
                        showarrow=False,
                        align="left",
                        bgcolor="rgba(255,255,255,0.8)",
                        bordercolor="black",
                        borderwidth=1,
                    )
                )

            fig.update_layout(
                title="Portfolio vs Benchmark Comparison",
                xaxis_title="Date",
                yaxis_title="Normalized Value",
                height=self.config.height // 2,
                width=self.config.width,
                template="plotly_white",
                annotations=annotations,
            )

            return self._save_plot(fig, "benchmark_comparison")

        except Exception as e:
            self._log(f"Error creating benchmark comparison: {str(e)}", "error")
            return []

    def _create_risk_metrics_chart(
        self, risk_metrics: RiskMetrics, title_prefix: str
    ) -> List[str]:
        """Create risk metrics visualization."""
        try:
            # Create subplots for different risk metrics
            fig = make_subplots(
                rows=2,
                cols=2,
                subplot_titles=[
                    "Value at Risk",
                    "Risk-Adjusted Returns",
                    "Distribution Metrics",
                    "Drawdown Metrics",
                ],
                specs=[
                    [{"type": "bar"}, {"type": "bar"}],
                    [{"type": "bar"}, {"type": "bar"}],
                ],
            )

            # 1. VaR metrics
            fig.add_trace(
                go.Bar(
                    x=["VaR 95%", "VaR 99%", "CVaR 95%", "CVaR 99%"],
                    y=[
                        risk_metrics.var_95,
                        risk_metrics.var_99,
                        risk_metrics.cvar_95,
                        risk_metrics.cvar_99,
                    ],
                    name="VaR Metrics",
                    marker_color="red",
                ),
                row=1,
                col=1,
            )

            # 2. Risk-adjusted returns
            fig.add_trace(
                go.Bar(
                    x=["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio"],
                    y=[
                        risk_metrics.sharpe_ratio,
                        risk_metrics.sortino_ratio,
                        risk_metrics.calmar_ratio,
                    ],
                    name="Risk-Adjusted Returns",
                    marker_color="green",
                ),
                row=1,
                col=2,
            )

            # 3. Distribution metrics
            fig.add_trace(
                go.Bar(
                    x=["Skewness", "Kurtosis", "Hit Ratio %"],
                    y=[
                        risk_metrics.skewness,
                        risk_metrics.kurtosis,
                        risk_metrics.hit_ratio,
                    ],
                    name="Distribution",
                    marker_color="blue",
                ),
                row=2,
                col=1,
            )

            # 4. Drawdown metrics
            fig.add_trace(
                go.Bar(
                    x=["Max Drawdown %", "Avg Drawdown %", "Max DD Duration"],
                    y=[
                        risk_metrics.max_drawdown * 100,
                        risk_metrics.avg_drawdown * 100,
                        risk_metrics.max_drawdown_duration,
                    ],
                    name="Drawdown",
                    marker_color="orange",
                ),
                row=2,
                col=2,
            )

            fig.update_layout(
                title=f"{title_prefix} Risk Metrics Analysis",
                height=self.config.height,
                width=self.config.width,
                showlegend=False,
                template="plotly_white",
            )

            return self._save_plot(fig, "risk_metrics")

        except Exception as e:
            self._log(f"Error creating risk metrics chart: {str(e)}", "error")
            return []

    def _create_drawdown_analysis_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create detailed drawdown analysis chart."""
        try:
            # Get portfolio value and calculate drawdowns
            portfolio_value = portfolio.value()
            cummax = portfolio_value.expanding().max()
            drawdowns = (portfolio_value - cummax) / cummax * 100

            # Create figure
            fig = make_subplots(
                rows=2,
                cols=1,
                subplot_titles=["Portfolio Value with Peak", "Drawdown %"],
                vertical_spacing=0.1,
            )

            # Portfolio value with running maximum
            fig.add_trace(
                go.Scatter(
                    x=portfolio_value.index,
                    y=portfolio_value.values,
                    mode="lines",
                    name="Portfolio Value",
                    line=dict(color="blue", width=2),
                ),
                row=1,
                col=1,
            )

            fig.add_trace(
                go.Scatter(
                    x=cummax.index,
                    y=cummax.values,
                    mode="lines",
                    name="Peak Value",
                    line=dict(color="green", width=1, dash="dash"),
                ),
                row=1,
                col=1,
            )

            # Drawdown percentage
            fig.add_trace(
                go.Scatter(
                    x=drawdowns.index,
                    y=drawdowns.values,
                    mode="lines",
                    fill="tonexty",
                    name="Drawdown %",
                    line=dict(color="red", width=1),
                    fillcolor="rgba(255,0,0,0.3)",
                ),
                row=2,
                col=1,
            )

            fig.update_layout(
                title=f"{title_prefix} Drawdown Analysis",
                height=self.config.height,
                width=self.config.width,
                template="plotly_white",
            )

            return self._save_plot(fig, "drawdown_analysis")

        except Exception as e:
            self._log(f"Error creating drawdown analysis: {str(e)}", "error")
            return []

    def _create_returns_distribution_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create returns distribution analysis chart."""
        try:
            # Get returns
            returns = portfolio.returns().dropna()

            # Create subplots
            fig = make_subplots(
                rows=1,
                cols=2,
                subplot_titles=["Returns Distribution", "Q-Q Plot vs Normal"],
                specs=[[{"type": "histogram"}, {"type": "scatter"}]],
            )

            # Histogram of returns
            fig.add_trace(
                go.Histogram(
                    x=returns.values * 100,  # Convert to percentage
                    nbinsx=50,
                    name="Returns Distribution",
                    marker_color="lightblue",
                    opacity=0.7,
                ),
                row=1,
                col=1,
            )

            # Q-Q plot vs normal distribution
            import scipy.stats as stats

            (osm, osr), (slope, intercept, r) = stats.probplot(
                returns.values, dist="norm", plot=None
            )

            fig.add_trace(
                go.Scatter(
                    x=osm,
                    y=osr,
                    mode="markers",
                    name="Sample Quantiles",
                    marker=dict(color="blue", size=4),
                ),
                row=1,
                col=2,
            )

            # Add normal line
            line_x = [osm.min(), osm.max()]
            line_y = [slope * osm.min() + intercept, slope * osm.max() + intercept]
            fig.add_trace(
                go.Scatter(
                    x=line_x,
                    y=line_y,
                    mode="lines",
                    name=f"Normal Line (R²={r**2:.3f})",
                    line=dict(color="red", dash="dash"),
                ),
                row=1,
                col=2,
            )

            fig.update_layout(
                title=f"{title_prefix} Returns Distribution Analysis",
                height=self.config.height // 2,
                width=self.config.width,
                template="plotly_white",
            )

            return self._save_plot(fig, "returns_distribution")

        except Exception as e:
            self._log(f"Error creating returns distribution: {str(e)}", "error")
            return []

    def _save_plot(self, fig: go.Figure, filename: str) -> List[str]:
        """Save plot in configured formats."""
        saved_files = []

        try:
            # Save HTML if enabled
            if self.config.save_html:
                html_path = os.path.join(self.config.output_dir, f"{filename}.html")
                fig.write_html(html_path)
                saved_files.append(html_path)
                self._log(f"Saved HTML plot: {html_path}")

            # Save PNG if enabled
            if self.config.save_png:
                try:
                    png_path = os.path.join(self.config.output_dir, f"{filename}.png")
                    fig.write_image(
                        png_path, width=self.config.width, height=self.config.height
                    )
                    saved_files.append(png_path)
                    self._log(f"Saved PNG plot: {png_path}")
                except Exception as e:
                    self._log(
                        f"Could not save PNG (Kaleido issue): {str(e)}", "warning"
                    )

        except Exception as e:
            self._log(f"Error saving plot {filename}: {str(e)}", "error")

        return saved_files

    def _log(self, message: str, level: str = "info"):
        """Log message using provided logger or print."""
        if self.logger:
            getattr(self.logger, level)(message)
        else:
            print(f"[{level.upper()}] {message}")
