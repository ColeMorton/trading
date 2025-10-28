"""Visualization utilities for concurrency analysis."""

from collections.abc import Callable


# Complete Color Palette Constants
PRIMARY_DATA = "#26c6da"  # Cyan - Primary data
SECONDARY_DATA = "#7e57c2"  # Purple - Secondary data/negative
TERTIARY_DATA = "#3179f5"  # Blue - Tertiary data/warnings
BACKGROUND = "#fff"  # Pure white
PRIMARY_TEXT = "#121212"  # Near black
BODY_TEXT = "#444444"  # Dark gray
MUTED_TEXT = "#717171"  # Medium gray

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import polars as pl

from app.concurrency.tools.plot_config import STRATEGY_COLORS, get_heatmap_config
from app.concurrency.tools.stats_visualization import create_stats_annotation
from app.concurrency.tools.types import ConcurrencyStats
from app.tools.portfolio import StrategyConfig


def create_strategy_traces(
    data: pl.DataFrame,
    config: StrategyConfig,
    color: str,
    log: Callable[[str, str], None],
) -> list[go.Scatter]:
    """Create price and position traces for a single strategy.

    Args:
        data (pl.DataFrame): Strategy data
        config (StrategyConfig): Strategy configuration
        color (str): Color for position highlighting
        log (Callable[[str, str], None]): Logging function

    Returns:
        List[go.Scatter]: List of traces for the strategy subplot
    """
    try:
        ticker = config["TICKER"]
        log(f"Creating traces for {ticker}", "info")

        traces = [
            go.Scatter(
                x=data["Date"],
                y=data["Close"],
                name=f"{ticker} Price",
                line={"color": PRIMARY_TEXT, "width": 1},
                hovertemplate="%{x|%d/%m/%Y}, %{y:.4f}k<extra></extra>",
            ),
        ]

        # Add position highlighting for both long and short positions
        long_positions = data.filter(pl.col("Position") == 1)
        short_positions = data.filter(pl.col("Position") == -1)

        log(
            f"Found {len(long_positions)} long positions and {len(short_positions)} short positions for {ticker}",
            "info",
        )

        # Highlight long positions
        for date, close in zip(
            long_positions["Date"],
            long_positions["Close"],
            strict=False,
        ):
            traces.append(
                go.Scatter(
                    x=[date, date],
                    y=[0, close],
                    mode="lines",
                    line={"color": color, "width": 1},
                    showlegend=False,
                    hovertemplate="%{x|%d/%m/%Y}, %{y:.4f}k<extra></extra>",
                    hoverinfo="text",
                ),
            )

        # Highlight short positions with a different pattern (dashed line)
        for date, close in zip(
            short_positions["Date"],
            short_positions["Close"],
            strict=False,
        ):
            traces.append(
                go.Scatter(
                    x=[date, date],
                    y=[0, close],
                    mode="lines",
                    line={"color": color, "width": 1, "dash": "dash"},
                    showlegend=False,
                    hovertemplate="%{x|%d/%m/%Y}, %{y:.4f}k<extra></extra>",
                    hoverinfo="text",
                ),
            )

        # Add ATR trailing stop visualization for ATR strategies
        strategy_type = config.get("STRATEGY_TYPE", config.get("type", ""))
        log(f"Strategy type for {ticker}: {strategy_type}", "info")
        log(f"Available columns in data: {data.columns}", "info")

        # Check for ATR strategy by type or by presence of ATR columns
        is_atr_strategy = strategy_type == "ATR" or "ATR_Trailing_Stop" in data.columns

        if is_atr_strategy:
            log(f"Detected ATR strategy for {ticker}", "info")

            # Check if ATR_Trailing_Stop column exists
            if "ATR_Trailing_Stop" in data.columns:
                log(f"Adding ATR trailing stop visualization for {ticker}", "info")

                try:
                    # Count non-null values in polars DataFrame
                    non_null_count = data.filter(
                        ~pl.col("ATR_Trailing_Stop").is_null(),
                    ).height
                    log(
                        f"ATR_Trailing_Stop column has {non_null_count} non-null values in polars DataFrame",
                        "info",
                    )

                    if non_null_count > 0:
                        # Convert to pandas for easier handling of NaN values
                        pandas_data = data.to_pandas()
                        log(
                            f"Pandas columns after conversion: {list(pandas_data.columns)}",
                            "info",
                        )

                        # Filter out NaN values for the trailing stop
                        valid_stops = pandas_data[
                            pandas_data["ATR_Trailing_Stop"].notna()
                        ]

                        if not valid_stops.empty:
                            # Create a continuous line by connecting segments
                            # Sort by date to ensure proper line connection
                            valid_stops = valid_stops.sort_values("Date")

                            traces.append(
                                go.Scatter(
                                    x=valid_stops["Date"],
                                    y=valid_stops["ATR_Trailing_Stop"],
                                    name=f"{ticker} ATR Trailing Stop",
                                    line={
                                        "color": SECONDARY_DATA,
                                        "width": 1.5,
                                        "dash": "dot",
                                    },
                                    hovertemplate="%{x|%d/%m/%Y}, Stop: %{y:.4f}k<extra></extra>",
                                    connectgaps=False,  # Don't connect across gaps
                                ),
                            )
                            log(
                                f"Added ATR trailing stop trace with {len(valid_stops)} points",
                                "info",
                            )
                        else:
                            log(
                                f"WARNING: No valid ATR_Trailing_Stop values found for {ticker} after filtering",
                                "warning",
                            )
                    else:
                        log(
                            f"WARNING: ATR_Trailing_Stop column exists but has no non-null values for {ticker}",
                            "warning",
                        )
                except Exception as e:
                    log(
                        f"Error processing ATR_Trailing_Stop for {ticker}: {e!s}",
                        "error",
                    )
            else:
                log(
                    f"WARNING: ATR_Trailing_Stop column not found for {ticker} ATR strategy",
                    "warning",
                )

        # Add legend entries for both long and short positions if they exist
        if len(long_positions) > 0:
            traces.append(
                go.Scatter(
                    x=[data["Date"][0]],
                    y=[data["Close"][0]],
                    name=f"{ticker} Long Positions",
                    mode="lines",
                    line={"color": color, "width": 10},
                    showlegend=True,
                ),
            )

        if len(short_positions) > 0:
            traces.append(
                go.Scatter(
                    x=[data["Date"][0]],
                    y=[data["Close"][0]],
                    name=f"{ticker} Short Positions",
                    mode="lines",
                    line={"color": color, "width": 10, "dash": "dash"},
                    showlegend=True,
                ),
            )

        log(f"Created {len(traces)} traces for {ticker}", "info")
        return traces

    except Exception as e:
        log(
            f"Error creating strategy traces for {config.get('TICKER', 'unknown')}: {e!s}",
            "error",
        )
        raise


def plot_concurrency(
    data_list: list[pl.DataFrame],
    stats: ConcurrencyStats,
    config_list: list[StrategyConfig],
    log: Callable[[str, str], None],
    config: dict | None = None,
) -> go.Figure:
    """Create visualization of concurrent positions across multiple strategies.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with signals
        stats (ConcurrencyStats): Concurrency statistics
        config_list (List[StrategyConfig]): List of strategy configurations
        log (Callable[[str, str], None]): Logging function
        config (Optional[Dict]): Configuration dictionary for pagination and layout options

    Returns:
        go.Figure: Plotly figure object containing the visualization

    Raises:
        ValueError: If required columns are missing from dataframes
    """
    try:
        log("Starting concurrency visualization", "info")

        # Validate inputs
        if not data_list or not config_list:
            log("Empty data or config list provided", "error")
            msg = "Data and config lists cannot be empty"
            raise ValueError(msg)

        if len(data_list) != len(config_list):
            log("Mismatched data and config lists", "error")
            msg = "Number of dataframes must match number of configurations"
            raise ValueError(msg)

        required_cols = ["Date", "Close", "Position"]
        for i, df in enumerate(data_list, 1):
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                log(f"Strategy {i} missing required columns: {missing}", "error")
                msg = f"Missing required columns: {missing}"
                raise ValueError(msg)

        n_strategies = len(data_list)
        log(f"Creating visualization for {n_strategies} strategies", "info")

        def format_strategy_title(config):
            ticker = config.get("TICKER", config.get("ticker", "Unknown"))
            strategy_type = config.get(
                "STRATEGY_TYPE",
                config.get("Strategy Type", config.get("type", "Unknown")),
            )
            fast_period = config.get(
                "FAST_PERIOD",
                config.get("Fast Period", config.get("fast_period", "?")),
            )
            slow_period = config.get(
                "SLOW_PERIOD",
                config.get("Slow Period", config.get("slow_period", "?")),
            )

            # Score is stored in nested PORTFOLIO_STATS from CSV data
            portfolio_stats = config.get("PORTFOLIO_STATS", {})
            score = portfolio_stats.get("Score", 0.0)

            # Fallback to top-level keys for other config formats
            if score == 0.0 or score is None:
                score = config.get(
                    "SCORE",
                    config.get("Score", config.get("score", 0.0)),
                )

            if isinstance(score, int | float):
                score_str = f"{score:.2f}"
            else:
                score_str = str(score)

            return f"{ticker} {strategy_type} {fast_period}/{slow_period} | Score: {score_str}"

        subplot_titles = [format_strategy_title(c) for c in config_list] + [
            "Strategy Concurrency",
        ]

        log("Creating subplot layout", "info")

        # Use adaptive vertical spacing based on strategy count to ensure total allocation ≤ 100%
        if n_strategies <= 10:
            vertical_spacing = 0.02  # 2% - comfortable spacing for small portfolios
        elif n_strategies <= 25:
            vertical_spacing = 0.01  # 1% - moderate spacing for medium portfolios
        else:
            vertical_spacing = 0.005  # 0.5% - minimal spacing for large portfolios

        log(
            f"Using adaptive vertical spacing: {vertical_spacing} for {n_strategies} strategies",
            "info",
        )

        # Calculate mathematically correct space allocation to ensure total = 100%
        spacing_total = (
            vertical_spacing * n_strategies
        )  # Total space used by gaps between rows
        available_space = 1.0 - spacing_total  # Space remaining after spacing

        # Allocate remaining space proportionally (88% strategies, 12% heatmap)
        strategy_space_total = available_space * 0.88
        heatmap_space = available_space * 0.12
        strategy_row_height = strategy_space_total / n_strategies
        heatmap_row_height = heatmap_space

        # Log the mathematically correct allocation
        log(
            f"Mathematically correct allocation - Spacing: {spacing_total*100:.1f}%, Available: {available_space*100:.1f}%, Strategy plots: {strategy_space_total*100:.1f}%, Heatmap: {heatmap_space*100:.1f}%",
            "info",
        )
        log(
            f"Per-strategy height: {strategy_row_height*100:.1f}%, Total: {(spacing_total + strategy_space_total + heatmap_space)*100:.1f}%",
            "info",
        )

        fig = make_subplots(
            rows=n_strategies + 1,
            cols=1,
            subplot_titles=subplot_titles,
            vertical_spacing=vertical_spacing,
            row_heights=[strategy_row_height] * n_strategies + [heatmap_row_height],
        )

        # Add strategy subplots
        log("Adding strategy subplots", "info")
        for i, (data, config) in enumerate(
            zip(data_list, config_list, strict=False),
            1,
        ):
            color = STRATEGY_COLORS[(i - 1) % len(STRATEGY_COLORS)]
            log(f"Creating subplot {i}/{n_strategies} for {config['TICKER']}", "info")
            for trace in create_strategy_traces(data, config, color, log):
                fig.add_trace(trace, row=i, col=1)

        # Add concurrency heatmap
        log("Creating concurrency heatmap", "info")
        position_arrays = [df["Position"].fill_null(0) for df in data_list]
        active_strategies = sum(
            abs(pl.Series(arr)) for arr in position_arrays
        )  # Use abs to count both long and short positions
        heatmap_config = get_heatmap_config()
        fig.add_trace(
            go.Heatmap(
                x=data_list[0]["Date"],
                z=[active_strategies],
                **heatmap_config,
                hovertemplate="%{x|%d/%m/%Y}, %{z}<extra></extra>",
            ),
            row=n_strategies + 1,
            col=1,
        )

        # Add statistics and update layout
        log("Adding statistics annotation", "info")
        stats.update(
            {
                "start_date": data_list[0]["Date"].min().strftime("%Y-%m-%d"),
                "end_date": data_list[0]["Date"].max().strftime("%Y-%m-%d"),
            },
        )
        fig.add_annotation(**create_stats_annotation(stats, log))

        log("Updating layout", "info")

        # Calculate figure height: fixed 500px per strategy + 200px for heatmap + 50px overhead
        figure_height = (n_strategies * 500) + 200 + 50

        # Extract portfolio filename from config
        portfolio_name = "portfolio"
        if config and "PORTFOLIO" in config:
            from pathlib import Path

            portfolio_path = Path(config["PORTFOLIO"])
            portfolio_name = portfolio_path.stem

        # Title with portfolio name and strategy count
        title_text = (
            f"Concurrency Analysis: {portfolio_name} ({n_strategies} strategies)"
        )

        fig.update_layout(
            height=figure_height,
            title_text=title_text,
            showlegend=True,
        )

        # Use proper Plotly method to set subplot title font size
        fig.for_each_annotation(lambda a: a.update(font_size=14))

        log(
            f"Layout updated with height={figure_height}px for {n_strategies} strategies",
            "info",
        )

        # Update axes
        log("Updating axes", "info")
        for i in range(1, n_strategies + 1):
            fig.update_yaxes(title="Price", row=i, col=1)
        fig.update_yaxes(
            showticklabels=False,
            showline=False,
            title=None,
            row=n_strategies + 1,
            col=1,
        )

        log("Visualization completed successfully", "info")
        return fig

    except Exception as e:
        log(f"Error creating concurrency visualization: {e!s}", "error")
        raise
