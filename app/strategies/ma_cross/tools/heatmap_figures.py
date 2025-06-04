from typing import Any, Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def create_heatmap_figures(
    profit_factor: pd.Series,
    trades: pd.Series,
    sortino: pd.Series,
    win_rate: pd.Series,
    expectancy: pd.Series,
    score: pd.Series,
    windows: np.ndarray,
    title: str,
    config: Dict[str, Any],
) -> Dict[str, go.Figure]:
    """
    Create separate heatmap figures for profit factor, total trades, Sortino ratio, win rate, expectancy, and score with consistent styling.
    Makes the heatmaps symmetrical by mirroring values across the diagonal.

    Args:
        profit_factor: Series with MultiIndex (slow, fast) containing profit factor values
        trades: Series with MultiIndex (slow, fast) containing total trades values
        sortino: Series with MultiIndex (slow, fast) containing Sortino ratio values
        win_rate: Series with MultiIndex (slow, fast) containing win rate values
        expectancy: Series with MultiIndex (slow, fast) containing expectancy values
        score: Series with MultiIndex (slow, fast) containing score values
        windows: Array of window values for axes
        title: Title/subtitle for the plots
        ticker: Ticker symbol for the plots
        use_sma: Whether to use SMA (True) or EMA (False)

    Returns:
        Dictionary containing six Plotly figure objects - for profit factor, trades, Sortino ratio, win rate, expectancy, and score
    """
    # Create blank heatmap matrices
    size = len(windows)
    profit_factor_heatmap = np.full((size, size), np.nan)
    trades_heatmap = np.full((size, size), np.nan)
    sortino_heatmap = np.full((size, size), np.nan)
    win_rate_heatmap = np.full((size, size), np.nan)
    expectancy_heatmap = np.full((size, size), np.nan)
    score_heatmap = np.full((size, size), np.nan)

    # Create window index mapping
    window_to_idx = {w: i for i, w in enumerate(windows)}

    # Fill in values and mirror them for symmetry
    for (slow, fast), value in profit_factor.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            profit_factor_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                profit_factor_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in trades.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            trades_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                trades_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in sortino.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            sortino_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                sortino_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in win_rate.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            win_rate_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                win_rate_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in expectancy.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            expectancy_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                expectancy_heatmap[fast_idx, slow_idx] = value

    for (slow, fast), value in score.items():
        if slow in window_to_idx and fast in window_to_idx:
            slow_idx = window_to_idx[slow]
            fast_idx = window_to_idx[fast]
            score_heatmap[slow_idx, fast_idx] = value
            # Mirror the same value across diagonal (if not on diagonal)
            if slow != fast:
                score_heatmap[fast_idx, slow_idx] = value

    # Get the actual min and max values from the data (excluding NaN)
    valid_profit_factor = profit_factor_heatmap[~np.isnan(profit_factor_heatmap)]
    profit_factor_zmin = (
        np.min(valid_profit_factor) if len(valid_profit_factor) > 0 else 0
    )
    profit_factor_zmax = (
        np.max(valid_profit_factor) if len(valid_profit_factor) > 0 else 0
    )

    valid_trades = trades_heatmap[~np.isnan(trades_heatmap)]
    trades_zmin = np.min(valid_trades) if len(valid_trades) > 0 else 0
    trades_zmax = 200  # Set maximum value to 200 for trades heatmap

    valid_sortino = sortino_heatmap[~np.isnan(sortino_heatmap)]
    sortino_zmin = np.min(valid_sortino) if len(valid_sortino) > 0 else 0
    sortino_zmax = np.max(valid_sortino) if len(valid_sortino) > 0 else 0

    valid_win_rate = win_rate_heatmap[~np.isnan(win_rate_heatmap)]
    win_rate_zmin = np.min(valid_win_rate) if len(valid_win_rate) > 0 else 0
    win_rate_zmax = np.max(valid_win_rate) if len(valid_win_rate) > 0 else 0

    valid_expectancy = expectancy_heatmap[~np.isnan(expectancy_heatmap)]
    expectancy_zmin = np.min(valid_expectancy) if len(valid_expectancy) > 0 else 0
    expectancy_zmax = np.max(valid_expectancy) if len(valid_expectancy) > 0 else 0

    valid_score = score_heatmap[~np.isnan(score_heatmap)]
    score_zmin = np.min(valid_score) if len(valid_score) > 0 else 0
    score_zmax = np.max(valid_score) if len(valid_score) > 0 else 0

    # Determine MA type for title
    ma_type = config.get("STRATEGY_TYPE", "EMA")

    # Create profit factor figure
    profit_factor_fig = go.Figure()
    profit_factor_fig.add_trace(
        go.Heatmap(
            z=profit_factor_heatmap,
            x=windows,
            y=windows,
            colorbar=dict(title="Profit Factor"),
            zmin=profit_factor_zmin,
            zmax=profit_factor_zmax,
            colorscale="thermal",
        )
    )

    profit_factor_fig.update_layout(
        title=dict(
            text=f'{
    config["TICKER"]} - {ma_type} Cross Strategy Profit Factor<br><sup>{title}</sup>',
            x=0.5,
            xanchor="center",
        ),
        yaxis=dict(title="Long Window"),
        xaxis=dict(title="Short Window"),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    # Create trades figure
    trades_fig = go.Figure()
    trades_fig.add_trace(
        go.Heatmap(
            z=trades_heatmap,
            x=windows,
            y=windows,
            colorbar=dict(title="Total Trades"),
            zmin=trades_zmin,
            zmax=trades_zmax,  # Use fixed maximum of 200
            colorscale="thermal",
        )
    )

    trades_fig.update_layout(
        title=dict(
            text=f'{
    config["TICKER"]} - {ma_type} Cross Strategy Total Trades<br><sup>{title}</sup>',
            x=0.5,
            xanchor="center",
        ),
        yaxis=dict(title="Long Window"),
        xaxis=dict(title="Short Window"),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    # Create Sortino ratio figure
    sortino_fig = go.Figure()
    sortino_fig.add_trace(
        go.Heatmap(
            z=sortino_heatmap,
            x=windows,
            y=windows,
            colorbar=dict(title="Sortino Ratio"),
            zmin=sortino_zmin,
            zmax=sortino_zmax,
            colorscale="thermal",
        )
    )

    sortino_fig.update_layout(
        title=dict(
            text=f'{
    config["TICKER"]} - {ma_type} Cross Strategy Sortino Ratio<br><sup>{title}</sup>',
            x=0.5,
            xanchor="center",
        ),
        yaxis=dict(title="Long Window"),
        xaxis=dict(title="Short Window"),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    # Create Win Rate figure
    win_rate_fig = go.Figure()
    win_rate_fig.add_trace(
        go.Heatmap(
            z=win_rate_heatmap,
            x=windows,
            y=windows,
            colorbar=dict(title="Win Rate", tickformat="%"),
            zmin=win_rate_zmin,
            zmax=win_rate_zmax,
            colorscale="thermal",
        )
    )

    win_rate_fig.update_layout(
        title=dict(
            text=f'{
    config["TICKER"]} - {ma_type} Cross Strategy Win Rate<br><sup>{title}</sup>',
            x=0.5,
            xanchor="center",
        ),
        yaxis=dict(title="Long Window"),
        xaxis=dict(title="Short Window"),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    # Create Expectancy figure
    expectancy_fig = go.Figure()
    expectancy_fig.add_trace(
        go.Heatmap(
            z=expectancy_heatmap,
            x=windows,
            y=windows,
            colorbar=dict(title="Expectancy"),
            zmin=expectancy_zmin,
            zmax=expectancy_zmax,
            colorscale="thermal",
        )
    )

    expectancy_fig.update_layout(
        title=dict(
            text=f'{
    config["TICKER"]} - {ma_type} Cross Strategy Expectancy<br><sup>{title}</sup>',
            x=0.5,
            xanchor="center",
        ),
        yaxis=dict(title="Long Window"),
        xaxis=dict(title="Short Window"),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    # Create Score figure
    score_fig = go.Figure()
    score_fig.add_trace(
        go.Heatmap(
            z=score_heatmap,
            x=windows,
            y=windows,
            colorbar=dict(title="Score"),
            zmin=score_zmin,
            zmax=score_zmax,
            colorscale="thermal",
        )
    )

    score_fig.update_layout(
        title=dict(
            text=f'{
    config["TICKER"]} - {ma_type} Cross Strategy Score<br><sup>{title}</sup>',
            x=0.5,
            xanchor="center",
        ),
        yaxis=dict(title="Long Window"),
        xaxis=dict(title="Short Window"),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=50),
    )

    return {
        "trades": trades_fig,
        "profit_factor": profit_factor_fig,
        "sortino": sortino_fig,
        "win_rate": win_rate_fig,
        "expectancy": expectancy_fig,
        "score": score_fig,
    }
