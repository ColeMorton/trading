#!/usr/bin/env python3
"""
Example: Custom Chart Generation from Exported Portfolio Data

This script demonstrates how to create custom charts using the raw data
exported from VectorBT portfolios. It provides examples for different
chart types and analysis approaches.

Prerequisites:
    pip install pandas plotly matplotlib seaborn

Usage:
    1. Export raw data using the CLI:
       trading-cli portfolio review --ticker AAPL --export-raw-data

    2. Run this script in the raw data directory:
       python example_custom_charts.py

    3. Charts will be saved as HTML files that you can open in a browser
"""

import glob
import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from plotly.subplots import make_subplots


class PortfolioChartGenerator:
    """Generator for custom portfolio analysis charts."""

    def __init__(self, data_directory="."):
        """Initialize with data directory containing exported files."""
        self.data_dir = Path(data_directory)
        self.portfolio_data = {}
        self.charts_output_dir = self.data_dir / "custom_charts"
        self.charts_output_dir.mkdir(exist_ok=True)

    def load_data(self, portfolio_name_pattern="*"):
        """Load all available data files for analysis."""
        print(f"Loading data from {self.data_dir}...")

        # Find all data files matching the pattern
        data_files = {
            "portfolio_value": list(
                self.data_dir.glob(f"{portfolio_name_pattern}_portfolio_value.csv")
            ),
            "returns": list(
                self.data_dir.glob(f"{portfolio_name_pattern}_returns.csv")
            ),
            "cumulative_returns": list(
                self.data_dir.glob(f"{portfolio_name_pattern}_cumulative_returns.csv")
            ),
            "drawdowns": list(
                self.data_dir.glob(f"{portfolio_name_pattern}_drawdowns.csv")
            ),
            "trades": list(self.data_dir.glob(f"{portfolio_name_pattern}_trades.json")),
            "statistics": list(
                self.data_dir.glob(f"{portfolio_name_pattern}_statistics.csv")
            ),
        }

        # Load each data type
        for data_type, files in data_files.items():
            self.portfolio_data[data_type] = {}
            for file_path in files:
                portfolio_name = file_path.stem.replace(f"_{data_type}", "")
                try:
                    if data_type == "trades":
                        df = pd.read_json(file_path)
                        if not df.empty and "Entry Timestamp" in df.columns:
                            df["Entry Timestamp"] = pd.to_datetime(
                                df["Entry Timestamp"]
                            )
                            df["Exit Timestamp"] = pd.to_datetime(df["Exit Timestamp"])
                    else:
                        df = pd.read_csv(file_path)
                        if "Date" in df.columns:
                            df["Date"] = pd.to_datetime(df["Date"])
                            df.set_index("Date", inplace=True)

                    self.portfolio_data[data_type][portfolio_name] = df
                    print(f"  ✓ Loaded {data_type} for {portfolio_name}")
                except Exception as e:
                    print(f"  ✗ Error loading {file_path}: {e}")

        print(
            f"Data loading complete. Found {len([p for dt in self.portfolio_data.values() for p in dt.keys()])} portfolio datasets."
        )
        return self.portfolio_data

    def create_portfolio_performance_chart(self, portfolio_name=None):
        """Create an enhanced portfolio performance chart."""
        if portfolio_name is None:
            portfolio_name = list(self.portfolio_data["portfolio_value"].keys())[0]

        if portfolio_name not in self.portfolio_data["portfolio_value"]:
            print(f"Portfolio {portfolio_name} not found in portfolio_value data")
            return None

        print(f"Creating portfolio performance chart for {portfolio_name}...")

        # Get data
        portfolio_df = self.portfolio_data["portfolio_value"][portfolio_name]

        # Create subplot with secondary y-axis
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=[
                "Portfolio Value & Normalized Performance",
                "Daily Returns",
            ],
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3],
        )

        # Portfolio value
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df["Portfolio_Value"],
                name="Portfolio Value",
                line=dict(color="#26c6da", width=2),
                hovertemplate="Date: %{x}<br>Value: $%{y:,.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # Normalized performance
        fig.add_trace(
            go.Scatter(
                x=portfolio_df.index,
                y=portfolio_df["Normalized_Value"],
                name="Normalized Performance",
                line=dict(color="#7e57c2", width=2, dash="dash"),
                yaxis="y2",
                hovertemplate="Date: %{x}<br>Normalized: %{y:.3f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # Add returns if available
        if portfolio_name in self.portfolio_data["returns"]:
            returns_df = self.portfolio_data["returns"][portfolio_name]
            fig.add_trace(
                go.Scatter(
                    x=returns_df.index,
                    y=returns_df["Returns_Pct"],
                    name="Daily Returns",
                    line=dict(color="#3179f5", width=1),
                    hovertemplate="Date: %{x}<br>Return: %{y:.2f}%<extra></extra>",
                ),
                row=2,
                col=1,
            )

        # Update layout
        fig.update_layout(
            title=f'{portfolio_name.replace("_", " ").title()} - Portfolio Performance Analysis',
            height=700,
            template="plotly_white",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        # Update y-axes
        fig.update_yaxes(
            title_text="Portfolio Value ($)", secondary_y=False, row=1, col=1
        )
        fig.update_yaxes(title_text="Normalized Value", secondary_y=True, row=1, col=1)
        fig.update_yaxes(title_text="Returns (%)", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=1)

        # Save chart
        output_path = self.charts_output_dir / f"{portfolio_name}_performance.html"
        fig.write_html(output_path)
        print(f"  ✓ Saved to {output_path}")

        return fig

    def create_drawdown_analysis_chart(self, portfolio_name=None):
        """Create a comprehensive drawdown analysis chart."""
        if portfolio_name is None:
            portfolio_name = list(self.portfolio_data["drawdowns"].keys())[0]

        if portfolio_name not in self.portfolio_data["drawdowns"]:
            print(f"Portfolio {portfolio_name} not found in drawdowns data")
            return None

        print(f"Creating drawdown analysis chart for {portfolio_name}...")

        # Get data
        drawdown_df = self.portfolio_data["drawdowns"][portfolio_name]

        # Create subplots
        fig = make_subplots(
            rows=3,
            cols=1,
            subplot_titles=[
                "Portfolio Value vs Peak Values",
                "Drawdown Percentage",
                "Underwater Curve",
            ],
            vertical_spacing=0.08,
            row_heights=[0.4, 0.3, 0.3],
        )

        # Portfolio value and peaks
        fig.add_trace(
            go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df["Current_Value"],
                name="Portfolio Value",
                line=dict(color="#26c6da", width=2),
                fill=None,
            ),
            row=1,
            col=1,
        )

        fig.add_trace(
            go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df["Peak_Value"],
                name="Peak Value",
                line=dict(color="#7e57c2", width=2, dash="dash"),
                fill="tonexty",
                fillcolor="rgba(126, 87, 194, 0.1)",
            ),
            row=1,
            col=1,
        )

        # Drawdown percentage with fill
        fig.add_trace(
            go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df["Drawdown_Pct"],
                name="Drawdown %",
                line=dict(color="#ff4444", width=2),
                fill="tonexty",
                fillcolor="rgba(255, 68, 68, 0.3)",
            ),
            row=2,
            col=1,
        )

        # Underwater curve (same as drawdown but styled differently)
        fig.add_trace(
            go.Scatter(
                x=drawdown_df.index,
                y=drawdown_df["Drawdown_Pct"],
                name="Underwater",
                line=dict(color="#1f77b4", width=1),
                fill="tozeroy",
                fillcolor="rgba(31, 119, 180, 0.4)",
            ),
            row=3,
            col=1,
        )

        # Add horizontal line at 0 for reference
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=3, col=1)

        # Update layout
        fig.update_layout(
            title=f'{portfolio_name.replace("_", " ").title()} - Drawdown Analysis',
            height=800,
            template="plotly_white",
            showlegend=True,
        )

        # Update axes
        fig.update_yaxes(title_text="Value ($)", row=1, col=1)
        fig.update_yaxes(title_text="Drawdown (%)", row=2, col=1)
        fig.update_yaxes(title_text="Underwater (%)", row=3, col=1)
        fig.update_xaxes(title_text="Date", row=3, col=1)

        # Calculate and add max drawdown annotation
        max_drawdown = drawdown_df["Drawdown_Pct"].min()
        max_dd_date = drawdown_df["Drawdown_Pct"].idxmin()

        fig.add_annotation(
            x=max_dd_date,
            y=max_drawdown,
            text=f"Max DD: {max_drawdown:.2f}%",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            row=2,
            col=1,
        )

        # Save chart
        output_path = (
            self.charts_output_dir / f"{portfolio_name}_drawdown_analysis.html"
        )
        fig.write_html(output_path)
        print(f"  ✓ Saved to {output_path}")

        return fig

    def create_returns_analysis_chart(self, portfolio_name=None):
        """Create a comprehensive returns analysis with distribution."""
        if portfolio_name is None:
            portfolio_name = list(self.portfolio_data["returns"].keys())[0]

        if portfolio_name not in self.portfolio_data["returns"]:
            print(f"Portfolio {portfolio_name} not found in returns data")
            return None

        print(f"Creating returns analysis chart for {portfolio_name}...")

        # Get data
        returns_df = self.portfolio_data["returns"][portfolio_name]

        # Handle different column names for returns percentage
        if "Returns_Pct" in returns_df.columns:
            returns_pct = returns_df["Returns_Pct"].dropna()
        elif "Cumulative_Returns_Pct" in returns_df.columns:
            returns_pct = returns_df["Cumulative_Returns_Pct"].dropna()
        elif "Returns" in returns_df.columns:
            returns_pct = returns_df["Returns"].dropna() * 100  # Convert to percentage
        else:
            raise KeyError("No suitable returns column found")

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                "Returns Time Series",
                "Returns Distribution",
                "Rolling Volatility (30-day)",
                "Returns Q-Q Plot vs Normal",
            ],
            specs=[[{"colspan": 2}, None], [{}, {}]],
            vertical_spacing=0.1,
        )

        # Returns time series
        fig.add_trace(
            go.Scatter(
                x=returns_df.index,
                y=returns_pct,
                name="Daily Returns",
                line=dict(color="#26c6da", width=1),
                mode="lines",
            ),
            row=1,
            col=1,
        )

        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)

        # Returns histogram
        fig.add_trace(
            go.Histogram(
                x=returns_pct,
                name="Returns Distribution",
                nbinsx=50,
                marker_color="#7e57c2",
                opacity=0.7,
            ),
            row=2,
            col=1,
        )

        # Rolling volatility
        rolling_vol = returns_df["Returns"].rolling(window=30).std() * 100
        fig.add_trace(
            go.Scatter(
                x=rolling_vol.index,
                y=rolling_vol,
                name="30-day Volatility",
                line=dict(color="#ff6b6b", width=2),
            ),
            row=2,
            col=2,
        )

        # Calculate summary statistics
        mean_return = returns_pct.mean()
        std_return = returns_pct.std()
        sharpe_ratio = mean_return / std_return * (252**0.5) if std_return > 0 else 0
        skewness = returns_pct.skew()
        kurtosis = returns_pct.kurtosis()

        # Add statistics annotation
        stats_text = f"""
        Mean: {mean_return:.3f}%
        Std: {std_return:.3f}%
        Sharpe: {sharpe_ratio:.3f}
        Skewness: {skewness:.3f}
        Kurtosis: {kurtosis:.3f}
        """

        fig.add_annotation(
            text=stats_text,
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
        )

        # Update layout
        fig.update_layout(
            title=f'{portfolio_name.replace("_", " ").title()} - Returns Analysis',
            height=700,
            template="plotly_white",
            showlegend=False,
        )

        # Update axes
        fig.update_yaxes(title_text="Returns (%)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        fig.update_yaxes(title_text="Volatility (%)", row=2, col=2)
        fig.update_xaxes(title_text="Date", row=1, col=1)
        fig.update_xaxes(title_text="Returns (%)", row=2, col=1)
        fig.update_xaxes(title_text="Date", row=2, col=2)

        # Save chart
        output_path = self.charts_output_dir / f"{portfolio_name}_returns_analysis.html"
        fig.write_html(output_path)
        print(f"  ✓ Saved to {output_path}")

        return fig

    def create_trade_analysis_chart(self, portfolio_name=None):
        """Create trade analysis charts if trade data is available."""
        if not self.portfolio_data["trades"]:
            print("No trade data available for analysis")
            return None

        if portfolio_name is None:
            portfolio_name = list(self.portfolio_data["trades"].keys())[0]

        if portfolio_name not in self.portfolio_data["trades"]:
            print(f"Portfolio {portfolio_name} not found in trades data")
            return None

        print(f"Creating trade analysis chart for {portfolio_name}...")

        # Get data
        trades_df = self.portfolio_data["trades"][portfolio_name]

        if trades_df.empty:
            print(f"No trades found for {portfolio_name}")
            return None

        # Create subplots
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=[
                "Trade P&L Over Time",
                "Trade Duration Distribution",
                "P&L Distribution",
                "Cumulative P&L",
            ],
        )

        # Trade P&L scatter plot
        colors = ["green" if pnl > 0 else "red" for pnl in trades_df["PnL"]]
        fig.add_trace(
            go.Scatter(
                x=trades_df["Entry Timestamp"],
                y=trades_df["PnL"],
                mode="markers",
                marker=dict(color=colors, size=8, opacity=0.7),
                name="Trade P&L",
                hovertemplate="Entry: %{x}<br>P&L: $%{y:.2f}<extra></extra>",
            ),
            row=1,
            col=1,
        )

        # Trade duration histogram
        if "Duration" in trades_df.columns:
            fig.add_trace(
                go.Histogram(
                    x=trades_df["Duration"],
                    name="Duration",
                    marker_color="#26c6da",
                    opacity=0.7,
                ),
                row=1,
                col=2,
            )

        # P&L distribution
        fig.add_trace(
            go.Histogram(
                x=trades_df["PnL"],
                name="P&L Distribution",
                marker_color="#7e57c2",
                opacity=0.7,
            ),
            row=2,
            col=1,
        )

        # Cumulative P&L
        cumulative_pnl = trades_df["PnL"].cumsum()
        fig.add_trace(
            go.Scatter(
                x=trades_df["Entry Timestamp"],
                y=cumulative_pnl,
                name="Cumulative P&L",
                line=dict(color="#3179f5", width=2),
                mode="lines",
            ),
            row=2,
            col=2,
        )

        # Add zero lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=2)

        # Calculate trade statistics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df["PnL"] > 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_win = trades_df[trades_df["PnL"] > 0]["PnL"].mean()
        avg_loss = trades_df[trades_df["PnL"] < 0]["PnL"].mean()
        profit_factor = abs(avg_win / avg_loss) if avg_loss < 0 else float("inf")

        # Add statistics annotation
        stats_text = f"""
        Total Trades: {total_trades}
        Win Rate: {win_rate:.1%}
        Avg Win: ${avg_win:.2f}
        Avg Loss: ${avg_loss:.2f}
        Profit Factor: {profit_factor:.2f}
        """

        fig.add_annotation(
            text=stats_text,
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top",
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
        )

        # Update layout
        fig.update_layout(
            title=f'{portfolio_name.replace("_", " ").title()} - Trade Analysis',
            height=700,
            template="plotly_white",
            showlegend=False,
        )

        # Update axes labels
        fig.update_yaxes(title_text="P&L ($)", row=1, col=1)
        fig.update_yaxes(title_text="Frequency", row=1, col=2)
        fig.update_yaxes(title_text="Frequency", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative P&L ($)", row=2, col=2)
        fig.update_xaxes(title_text="Entry Date", row=1, col=1)
        fig.update_xaxes(title_text="Duration", row=1, col=2)
        fig.update_xaxes(title_text="P&L ($)", row=2, col=1)
        fig.update_xaxes(title_text="Entry Date", row=2, col=2)

        # Save chart
        output_path = self.charts_output_dir / f"{portfolio_name}_trade_analysis.html"
        fig.write_html(output_path)
        print(f"  ✓ Saved to {output_path}")

        return fig

    def create_portfolio_comparison_chart(self):
        """Create a comparison chart for multiple portfolios."""
        portfolio_names = list(self.portfolio_data["portfolio_value"].keys())

        if len(portfolio_names) < 2:
            print("Need at least 2 portfolios for comparison")
            return None

        print(
            f"Creating portfolio comparison chart for {len(portfolio_names)} portfolios..."
        )

        # Create figure
        fig = go.Figure()

        # Add each portfolio's normalized performance
        colors = ["#26c6da", "#7e57c2", "#3179f5", "#ff6b6b", "#4ecdc4", "#45b7d1"]

        for i, portfolio_name in enumerate(portfolio_names):
            df = self.portfolio_data["portfolio_value"][portfolio_name]
            color = colors[i % len(colors)]

            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df["Normalized_Value"],
                    name=portfolio_name.replace("_", " ").title(),
                    line=dict(color=color, width=2),
                    hovertemplate=f"{portfolio_name}<br>Date: %{{x}}<br>Normalized: %{{y:.3f}}<extra></extra>",
                )
            )

        # Update layout
        fig.update_layout(
            title="Portfolio Performance Comparison (Normalized)",
            xaxis_title="Date",
            yaxis_title="Normalized Value",
            template="plotly_white",
            height=600,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        # Add horizontal line at 1.0 for reference
        fig.add_hline(
            y=1.0, line_dash="dash", line_color="gray", annotation_text="Break Even"
        )

        # Save chart
        output_path = self.charts_output_dir / "portfolio_comparison.html"
        fig.write_html(output_path)
        print(f"  ✓ Saved to {output_path}")

        return fig

    def generate_all_charts(self):
        """Generate all available chart types."""
        print("\n" + "=" * 60)
        print("GENERATING CUSTOM PORTFOLIO CHARTS")
        print("=" * 60)

        # Load data
        self.load_data()

        if not any(self.portfolio_data.values()):
            print("No data found. Please export raw data first using:")
            print("trading-cli portfolio review --ticker SYMBOL --export-raw-data")
            return

        # Generate charts for each portfolio
        portfolio_names = set()
        for data_type in self.portfolio_data.values():
            portfolio_names.update(data_type.keys())

        print(f"\nGenerating charts for {len(portfolio_names)} portfolios...")

        chart_count = 0

        for portfolio_name in portfolio_names:
            print(f"\n--- Processing {portfolio_name} ---")

            # Portfolio performance chart
            if portfolio_name in self.portfolio_data["portfolio_value"]:
                self.create_portfolio_performance_chart(portfolio_name)
                chart_count += 1

            # Drawdown analysis
            if portfolio_name in self.portfolio_data["drawdowns"]:
                self.create_drawdown_analysis_chart(portfolio_name)
                chart_count += 1

            # Returns analysis
            if portfolio_name in self.portfolio_data["returns"]:
                try:
                    self.create_returns_analysis_chart(portfolio_name)
                    chart_count += 1
                except KeyError as e:
                    print(
                        f"  ⚠ Skipping returns analysis for {portfolio_name}: missing column {e}"
                    )
                except Exception as e:
                    print(f"  ✗ Error creating returns chart for {portfolio_name}: {e}")

            # Trade analysis
            if portfolio_name in self.portfolio_data["trades"]:
                self.create_trade_analysis_chart(portfolio_name)
                chart_count += 1

        # Portfolio comparison (if multiple portfolios)
        if len(portfolio_names) > 1:
            print(f"\n--- Creating Portfolio Comparison ---")
            self.create_portfolio_comparison_chart()
            chart_count += 1

        print(f"\n" + "=" * 60)
        print(f"CHART GENERATION COMPLETE")
        print(f"Generated {chart_count} charts in {self.charts_output_dir}")
        print(f"Open the HTML files in your browser to view the charts")
        print("=" * 60)

        return chart_count


def main():
    """Main execution function."""
    print("Portfolio Raw Data Chart Generator")
    print("==================================")

    # Initialize generator
    generator = PortfolioChartGenerator()

    # Generate all charts
    chart_count = generator.generate_all_charts()

    if chart_count > 0:
        print(f"\n✓ Successfully generated {chart_count} custom charts!")
        print(f"Charts saved to: {generator.charts_output_dir}")
        print("\nTo view charts, open the HTML files in your web browser.")
    else:
        print(
            "\n✗ No charts generated. Please ensure you have exported raw data first."
        )
        print("\nTo export raw data, run:")
        print("  trading-cli portfolio review --ticker SYMBOL --export-raw-data")


if __name__ == "__main__":
    main()
