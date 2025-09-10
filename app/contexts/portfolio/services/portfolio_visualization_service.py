"""
Portfolio Visualization Service

Unified service for creating portfolio analysis visualizations,
integrating with the existing headless plotting system.
"""

import os
from dataclasses import dataclass, field
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
class ChartStyleConfig:
    """Configuration for chart styling and colors - Complete Color Palette compliant."""

    # Complete Color Palette - Primary Data Colors
    primary_data: str = "#26c6da"  # Cyan
    secondary_data: str = "#7e57c2"  # Purple
    tertiary_data: str = "#3179f5"  # Blue

    # Complete Color Palette - Light Mode Colors
    background: str = "#fff"  # Pure white
    card_background: str = "#f6f6f6"  # Light gray
    primary_text: str = "#121212"  # Near black
    body_text: str = "#444444"  # Dark gray
    muted_text: str = "#717171"  # Medium gray
    borders: str = "#eaeaea"  # Light gray borders

    # Complete Color Palette - Dark Mode Colors (for future use)
    dark_background: str = "#202124"  # Dark gray
    dark_card_background: str = "#222222"  # Slightly lighter dark gray
    dark_primary_text: str = "#fff"  # Pure white
    dark_body_text: str = "#B4AFB6"  # Light purple-gray
    dark_muted_text: str = "#B4AFB6"  # Light purple-gray
    dark_borders: str = "#3E3E3E"  # Medium dark gray

    # Financial Semantic Colors (mapped to Complete Color Palette)
    positive_color: str = "#26c6da"  # Primary Data - Cyan (gains, portfolio value)
    negative_color: str = "#7e57c2"  # Secondary Data - Purple (losses, drawdowns)
    neutral_color: str = "#717171"  # Muted Text - Gray (benchmarks)
    warning_color: str = "#3179f5"  # Tertiary Data - Blue (alerts)

    # Typography
    font_family: str = "sans-serif"
    regular_weight: int = 400
    semibold_weight: int = 600

    # Line/marker styling
    primary_line_width: int = 2
    secondary_line_width: int = 1
    marker_size: int = 4
    fill_opacity: float = 0.3

    def get_financial_color(self, semantic_type: str) -> str:
        """Get color for financial semantic meaning."""
        color_map = {
            "positive": self.positive_color,
            "negative": self.negative_color,
            "neutral": self.neutral_color,
            "warning": self.warning_color,
            "gains": self.positive_color,
            "losses": self.negative_color,
            "profit": self.positive_color,
            "loss": self.negative_color,
            "drawdown": self.negative_color,
            "benchmark": self.neutral_color,
            "alert": self.warning_color,
        }
        return color_map.get(semantic_type.lower(), self.primary_data)

    def get_text_color(self, level: str = "primary") -> str:
        """Get text color for different hierarchy levels."""
        text_map = {
            "primary": self.primary_text,
            "body": self.body_text,
            "muted": self.muted_text,
        }
        return text_map.get(level.lower(), self.primary_text)

    def get_ui_color(self, element: str) -> str:
        """Get UI element color."""
        ui_map = {
            "background": self.background,
            "card": self.card_background,
            "border": self.borders,
        }
        return ui_map.get(element.lower(), self.background)

    def hex_to_rgba(self, hex_color: str, opacity: float) -> str:
        """Convert hex color to rgba format with specified opacity."""
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r},{g},{b},{opacity})"

    def get_fill_color(self, semantic_type: str, opacity: float = None) -> str:
        """Get fill color with opacity for semantic meaning."""
        base_color = self.get_financial_color(semantic_type)
        opacity = opacity or self.fill_opacity
        return self.hex_to_rgba(base_color, opacity)


@dataclass
class PlotConfig:
    """Configuration for plot generation."""

    output_dir: str = "data/outputs/portfolio/plots"
    width: int = 1200
    height: int = 800
    save_html: bool = True
    save_png: bool = True
    include_benchmark: bool = True
    include_risk_metrics: bool = True
    chart_style: ChartStyleConfig = field(default_factory=ChartStyleConfig)


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
    
    Uses unified 3-layer directory structure: portfolio/{type}/{name}/charts/

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

    def _get_line_style(self, color: str, width: int = None, dash: str = None) -> dict:
        """Get consistent line styling."""
        style = {
            "color": color,
            "width": width or self.config.chart_style.primary_line_width,
        }
        if dash:
            style["dash"] = dash
        return style

    def _get_marker_style(self, color: str, size: int = None) -> dict:
        """Get consistent marker styling."""
        return {"color": color, "size": size or self.config.chart_style.marker_size}

    def _get_layout_style(
        self, title: str, height: int = None, width: int = None
    ) -> dict:
        """Get consistent layout styling."""
        return {
            "title": {
                "text": title,
                "font": {
                    "family": self.config.chart_style.font_family,
                    "weight": self.config.chart_style.semibold_weight,
                },
            },
            "font": {
                "family": self.config.chart_style.font_family,
                "weight": self.config.chart_style.regular_weight,
            },
            "height": height or self.config.height,
            "width": width or self.config.width,
            "template": "plotly_white",
        }

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

            # Create output directory using unified 3-layer structure
            os.makedirs(self.config.output_dir, exist_ok=True)
            self._log(f"Using unified directory structure for charts: {self.config.output_dir}")

            generated_files = []

            # 1. Individual portfolio performance charts (4 separate files)
            # Portfolio value chart
            portfolio_value_files = self._create_portfolio_value_chart(
                portfolio, title_prefix
            )
            generated_files.extend(portfolio_value_files)

            # Cumulative returns chart
            cumulative_returns_files = self._create_cumulative_returns_chart(
                portfolio, title_prefix
            )
            generated_files.extend(cumulative_returns_files)

            # Drawdowns chart (with fixed calculation)
            drawdowns_files = self._create_drawdowns_chart(portfolio, title_prefix)
            generated_files.extend(drawdowns_files)

            # Underwater curve chart (with fixed calculation)
            underwater_files = self._create_underwater_curve_chart(
                portfolio, title_prefix
            )
            generated_files.extend(underwater_files)

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

            # 5. Returns analysis (separate histogram and Q-Q plot)
            # Returns histogram chart
            histogram_files = self._create_returns_histogram_chart(
                portfolio, title_prefix
            )
            generated_files.extend(histogram_files)

            # Q-Q plot chart
            qq_plot_files = self._create_qq_plot_chart(portfolio, title_prefix)
            generated_files.extend(qq_plot_files)

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

    def _create_portfolio_value_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create portfolio value chart."""
        try:
            portfolio_value = portfolio.value()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=portfolio_value.index,
                    y=portfolio_value.values,
                    mode="lines",
                    name="Portfolio Value",
                    line=self._get_line_style(self.config.chart_style.positive_color),
                )
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} - Portfolio Value", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Date",
                    "yaxis_title": "Portfolio Value",
                }
            )
            fig.update_layout(**layout_style)

            return self._save_plot(fig, "portfolio_value")

        except Exception as e:
            self._log(f"Error creating portfolio value chart: {str(e)}", "error")
            return []

    def _create_cumulative_returns_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create cumulative returns chart."""
        try:
            portfolio_returns = portfolio.returns()
            cum_returns = portfolio_returns.cumsum()

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=cum_returns.index,
                    y=cum_returns.values,
                    mode="lines",
                    name="Cumulative Returns",
                    line=self._get_line_style(self.config.chart_style.secondary_data),
                )
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} - Cumulative Returns", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Date",
                    "yaxis_title": "Cumulative Returns",
                }
            )
            fig.update_layout(**layout_style)

            return self._save_plot(fig, "cumulative_returns")

        except Exception as e:
            self._log(f"Error creating cumulative returns chart: {str(e)}", "error")
            return []

    def _create_drawdowns_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create drawdowns chart with correct calculation."""
        try:
            # Use proven drawdown calculation from _create_drawdown_analysis_chart
            portfolio_value = portfolio.value()
            cummax = portfolio_value.expanding().max()
            drawdowns = (portfolio_value - cummax) / cummax

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=drawdowns.index,
                    y=drawdowns.values,
                    mode="lines",
                    fill="tonexty",
                    name="Drawdowns",
                    line=self._get_line_style(
                        self.config.chart_style.negative_color,
                        width=self.config.chart_style.secondary_line_width,
                    ),
                    fillcolor=self.config.chart_style.get_fill_color("negative"),
                )
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} - Drawdowns", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Date",
                    "yaxis_title": "Drawdown",
                }
            )
            fig.update_layout(**layout_style)

            return self._save_plot(fig, "drawdowns")

        except Exception as e:
            self._log(f"Error creating drawdowns chart: {str(e)}", "error")
            return []

    def _create_underwater_curve_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create underwater curve chart with correct calculation."""
        try:
            # Use proven drawdown calculation (underwater curve is same as drawdowns)
            portfolio_value = portfolio.value()
            cummax = portfolio_value.expanding().max()
            drawdowns = (portfolio_value - cummax) / cummax

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=drawdowns.index,
                    y=drawdowns.values,
                    mode="lines",
                    name="Underwater Curve",
                    line=self._get_line_style(self.config.chart_style.tertiary_data),
                )
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} - Underwater Curve", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Date",
                    "yaxis_title": "Underwater",
                }
            )
            fig.update_layout(**layout_style)

            return self._save_plot(fig, "underwater_curve")

        except Exception as e:
            self._log(f"Error creating underwater curve chart: {str(e)}", "error")
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
                    line=self._get_line_style(self.config.chart_style.primary_data),
                )
            )

            # Add benchmark line
            fig.add_trace(
                go.Scatter(
                    x=benchmark_normalized.index,
                    y=benchmark_normalized.values,
                    mode="lines",
                    name="Benchmark",
                    line=self._get_line_style(
                        self.config.chart_style.neutral_color, dash="dash"
                    ),
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
                        bgcolor=self.config.chart_style.hex_to_rgba(
                            self.config.chart_style.background, 0.8
                        ),
                        bordercolor=self.config.chart_style.get_text_color("primary"),
                        borderwidth=1,
                    )
                )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                "Portfolio vs Benchmark Comparison", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Date",
                    "yaxis_title": "Normalized Value",
                    "annotations": annotations,
                }
            )
            fig.update_layout(**layout_style)

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

            # 1. VaR metrics (negative risk metrics)
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
                    marker_color=self.config.chart_style.negative_color,
                ),
                row=1,
                col=1,
            )

            # 2. Risk-adjusted returns (positive metrics)
            fig.add_trace(
                go.Bar(
                    x=["Sharpe Ratio", "Sortino Ratio", "Calmar Ratio"],
                    y=[
                        risk_metrics.sharpe_ratio,
                        risk_metrics.sortino_ratio,
                        risk_metrics.calmar_ratio,
                    ],
                    name="Risk-Adjusted Returns",
                    marker_color=self.config.chart_style.positive_color,
                ),
                row=1,
                col=2,
            )

            # 3. Distribution metrics (primary data)
            fig.add_trace(
                go.Bar(
                    x=["Skewness", "Kurtosis", "Hit Ratio %"],
                    y=[
                        risk_metrics.skewness,
                        risk_metrics.kurtosis,
                        risk_metrics.hit_ratio,
                    ],
                    name="Distribution",
                    marker_color=self.config.chart_style.primary_data,
                ),
                row=2,
                col=1,
            )

            # 4. Drawdown metrics (warning/risk metrics)
            fig.add_trace(
                go.Bar(
                    x=["Max Drawdown %", "Avg Drawdown %", "Max DD Duration"],
                    y=[
                        risk_metrics.max_drawdown * 100,
                        risk_metrics.avg_drawdown * 100,
                        risk_metrics.max_drawdown_duration,
                    ],
                    name="Drawdown",
                    marker_color=self.config.chart_style.warning_color,
                ),
                row=2,
                col=2,
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} Risk Metrics Analysis"
            )
            layout_style.update(
                {
                    "showlegend": False,
                }
            )
            fig.update_layout(**layout_style)

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
                    line=self._get_line_style(self.config.chart_style.primary_data),
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
                    line=self._get_line_style(
                        self.config.chart_style.positive_color,
                        width=self.config.chart_style.secondary_line_width,
                        dash="dash",
                    ),
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
                    line=self._get_line_style(
                        self.config.chart_style.negative_color,
                        width=self.config.chart_style.secondary_line_width,
                    ),
                    fillcolor=self.config.chart_style.get_fill_color("negative"),
                ),
                row=2,
                col=1,
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(f"{title_prefix} Drawdown Analysis")
            fig.update_layout(**layout_style)

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
                    marker_color=self.config.chart_style.primary_data,
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
                    marker=dict(color=self.config.chart_style.tertiary_data, size=4),
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
                    line=dict(
                        color=self.config.chart_style.negative_color, dash="dash"
                    ),
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

    def _create_returns_histogram_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create returns distribution histogram chart."""
        try:
            # Get returns
            returns = portfolio.returns().dropna()

            fig = go.Figure()

            # Histogram of returns
            fig.add_trace(
                go.Histogram(
                    x=returns.values * 100,  # Convert to percentage
                    nbinsx=50,
                    name="Returns Distribution",
                    marker_color=self.config.chart_style.primary_data,
                    opacity=0.7,
                )
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} - Returns Distribution", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Returns (%)",
                    "yaxis_title": "Frequency",
                }
            )
            fig.update_layout(**layout_style)

            return self._save_plot(fig, "returns_histogram")

        except Exception as e:
            self._log(f"Error creating returns histogram: {str(e)}", "error")
            return []

    def _create_qq_plot_chart(
        self, portfolio: "vbt.Portfolio", title_prefix: str
    ) -> List[str]:
        """Create Q-Q plot vs normal distribution chart."""
        try:
            # Get returns
            returns = portfolio.returns().dropna()

            # Q-Q plot vs normal distribution
            import scipy.stats as stats

            (osm, osr), (slope, intercept, r) = stats.probplot(
                returns.values, dist="norm", plot=None
            )

            fig = go.Figure()

            # Sample quantiles
            fig.add_trace(
                go.Scatter(
                    x=osm,
                    y=osr,
                    mode="markers",
                    name="Sample Quantiles",
                    marker=self._get_marker_style(
                        self.config.chart_style.secondary_data
                    ),
                )
            )

            # Normal line
            line_x = [osm.min(), osm.max()]
            line_y = [slope * osm.min() + intercept, slope * osm.max() + intercept]
            fig.add_trace(
                go.Scatter(
                    x=line_x,
                    y=line_y,
                    mode="lines",
                    name=f"Normal Line (R²={r**2:.3f})",
                    line=self._get_line_style(
                        self.config.chart_style.negative_color, dash="dash"
                    ),
                )
            )

            # Apply consistent styling
            layout_style = self._get_layout_style(
                f"{title_prefix} - Q-Q Plot vs Normal", height=self.config.height // 2
            )
            layout_style.update(
                {
                    "xaxis_title": "Theoretical Quantiles",
                    "yaxis_title": "Sample Quantiles",
                }
            )
            fig.update_layout(**layout_style)

            return self._save_plot(fig, "qq_plot")

        except Exception as e:
            self._log(f"Error creating Q-Q plot: {str(e)}", "error")
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
