"""
Performance Analyzer Service

Focused service for analyzing trading performance metrics.
Extracted from the larger analysis service for better maintainability.
"""

import logging

import numpy as np
import pandas as pd
import polars as pl

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config
from app.tools.models.statistical_analysis_models import (
    EquityAnalysis,
    StrategyDistributionAnalysis,
    TradeHistoryMetrics,
)


class PerformanceAnalyzer:
    """
    Service for analyzing trading performance and generating insights.

    This service handles:
    - Trade history analysis
    - Equity curve analysis
    - Strategy distribution analysis
    - Performance metric calculation
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the performance analyzer."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def analyze_trade_history(
        self, trades_data: pd.DataFrame | pl.DataFrame,
    ) -> TradeHistoryMetrics:
        """Analyze trade history and calculate performance metrics."""
        if isinstance(trades_data, pl.DataFrame):
            trades_data = trades_data.to_pandas()

        if trades_data.empty:
            return TradeHistoryMetrics(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0.0,
                avg_win=0.0,
                avg_loss=0.0,
                profit_factor=0.0,
                total_return=0.0,
                max_drawdown=0.0,
                sharpe_ratio=0.0,
            )

        # Assume 'pnl' column exists for P&L analysis
        if "pnl" not in trades_data.columns:
            # Try common alternative column names
            pnl_columns = ["P&L", "profit_loss", "return", "returns"]
            pnl_col = None
            for col in pnl_columns:
                if col in trades_data.columns:
                    pnl_col = col
                    break

            if pnl_col is None:
                msg = "No P&L column found in trade data"
                raise ValueError(msg)
        else:
            pnl_col = "pnl"

        pnl_series = trades_data[pnl_col]

        total_trades = len(trades_data)
        winning_trades = len(pnl_series[pnl_series > 0])
        losing_trades = len(pnl_series[pnl_series < 0])

        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        avg_win = pnl_series[pnl_series > 0].mean() if winning_trades > 0 else 0.0
        avg_loss = pnl_series[pnl_series < 0].mean() if losing_trades > 0 else 0.0

        profit_factor = (
            abs(avg_win * winning_trades / (avg_loss * losing_trades))
            if losing_trades > 0 and avg_loss != 0
            else 0.0
        )
        total_return = pnl_series.sum()

        # Calculate maximum drawdown
        cumulative_returns = pnl_series.cumsum()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()

        # Calculate Sharpe ratio
        sharpe_ratio = (
            pnl_series.mean() / pnl_series.std() if pnl_series.std() > 0 else 0.0
        )

        return TradeHistoryMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            total_return=total_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
        )

    def analyze_equity_curve(
        self, equity_data: pd.DataFrame | pl.DataFrame,
    ) -> EquityAnalysis:
        """Analyze equity curve and calculate performance metrics."""
        if isinstance(equity_data, pl.DataFrame):
            equity_data = equity_data.to_pandas()

        if equity_data.empty:
            return EquityAnalysis(
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                calmar_ratio=0.0,
                sortino_ratio=0.0,
            )

        # Assume 'equity' or 'value' column exists
        equity_col = None
        for col in ["equity", "value", "portfolio_value", "balance"]:
            if col in equity_data.columns:
                equity_col = col
                break

        if equity_col is None:
            msg = "No equity column found in equity data"
            raise ValueError(msg)

        equity_series = equity_data[equity_col]

        # Calculate returns
        returns = equity_series.pct_change().dropna()

        if returns.empty:
            return EquityAnalysis(
                total_return=0.0,
                annualized_return=0.0,
                volatility=0.0,
                sharpe_ratio=0.0,
                max_drawdown=0.0,
                calmar_ratio=0.0,
                sortino_ratio=0.0,
            )

        total_return = (equity_series.iloc[-1] / equity_series.iloc[0]) - 1
        annualized_return = (1 + total_return) ** (
            252 / len(equity_series)
        ) - 1  # Assuming daily data
        volatility = returns.std() * np.sqrt(252)  # Annualized volatility

        sharpe_ratio = annualized_return / volatility if volatility > 0 else 0.0

        # Calculate maximum drawdown
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min()

        calmar_ratio = (
            abs(annualized_return / max_drawdown) if max_drawdown != 0 else 0.0
        )

        # Calculate Sortino ratio
        negative_returns = returns[returns < 0]
        downside_std = (
            negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0.0
        )
        sortino_ratio = annualized_return / downside_std if downside_std > 0 else 0.0

        return EquityAnalysis(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            sortino_ratio=sortino_ratio,
        )

    def analyze_strategy_distribution(
        self, strategy_data: pd.DataFrame | pl.DataFrame,
    ) -> StrategyDistributionAnalysis:
        """Analyze strategy performance distribution."""
        if isinstance(strategy_data, pl.DataFrame):
            strategy_data = strategy_data.to_pandas()

        if strategy_data.empty:
            return StrategyDistributionAnalysis(
                strategy_count=0,
                performance_distribution={},
                top_performers=[],
                bottom_performers=[],
                performance_summary={},
            )

        # Assume 'strategy' and 'performance' columns exist
        if "strategy" not in strategy_data.columns:
            msg = "No strategy column found in strategy data"
            raise ValueError(msg)

        performance_col = None
        for col in ["performance", "return", "pnl", "profit_loss"]:
            if col in strategy_data.columns:
                performance_col = col
                break

        if performance_col is None:
            msg = "No performance column found in strategy data"
            raise ValueError(msg)

        strategy_count = strategy_data["strategy"].nunique()

        # Calculate performance distribution
        performance_by_strategy = strategy_data.groupby("strategy")[
            performance_col
        ].agg(["mean", "std", "min", "max"])
        performance_distribution = performance_by_strategy.to_dict("index")

        # Identify top and bottom performers
        mean_performance = performance_by_strategy["mean"].sort_values(ascending=False)
        top_performers = mean_performance.head(5).index.tolist()
        bottom_performers = mean_performance.tail(5).index.tolist()

        # Calculate summary statistics
        performance_summary = {
            "mean_performance": float(strategy_data[performance_col].mean()),
            "std_performance": float(strategy_data[performance_col].std()),
            "min_performance": float(strategy_data[performance_col].min()),
            "max_performance": float(strategy_data[performance_col].max()),
            "median_performance": float(strategy_data[performance_col].median()),
        }

        return StrategyDistributionAnalysis(
            strategy_count=strategy_count,
            performance_distribution=performance_distribution,
            top_performers=top_performers,
            bottom_performers=bottom_performers,
            performance_summary=performance_summary,
        )

    def calculate_risk_metrics(
        self, returns: pd.Series | pl.Series,
    ) -> dict[str, float]:
        """Calculate comprehensive risk metrics."""
        if isinstance(returns, pl.Series):
            returns = returns.to_pandas()

        if returns.empty:
            return {}

        # Value at Risk
        var_95 = float(np.percentile(returns, 5))
        var_99 = float(np.percentile(returns, 1))

        # Conditional VaR (Expected Shortfall)
        cvar_95 = (
            float(returns[returns <= var_95].mean())
            if (returns <= var_95).any()
            else var_95
        )
        cvar_99 = (
            float(returns[returns <= var_99].mean())
            if (returns <= var_99).any()
            else var_99
        )

        # Maximum Drawdown
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = float(drawdown.min())

        return {
            "var_95": var_95,
            "var_99": var_99,
            "cvar_95": cvar_95,
            "cvar_99": cvar_99,
            "max_drawdown": max_drawdown,
            "volatility": float(returns.std()),
            "downside_deviation": (
                float(returns[returns < 0].std()) if (returns < 0).any() else 0.0
            ),
        }
