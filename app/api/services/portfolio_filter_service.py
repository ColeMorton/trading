"""
Portfolio Filter Service

Handles portfolio filtering logic with configurable criteria.
This service is responsible for applying filters to portfolio results based on performance metrics.
"""

from typing import Any, Dict, List, Optional

import polars as pl

from app.core.interfaces import LoggingInterface


class PortfolioFilterService:
    """Service for filtering portfolio results based on criteria."""

    def __init__(self, logger: LoggingInterface):
        """
        Initialize the portfolio filter service.

        Args:
            logger: Logging interface
        """
        self.logger = logger

    def filter_portfolios(
        self,
        portfolios: List[Dict[str, Any]],
        filter_criteria: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Filter portfolios based on specified criteria.

        Args:
            portfolios: List of portfolio dictionaries
            filter_criteria: Dictionary of filter criteria

        Returns:
            Filtered list of portfolios
        """
        if not portfolios:
            return []

        # Convert to DataFrame for efficient filtering
        df = pl.DataFrame(portfolios)
        initial_count = len(df)

        self.logger.log(f"Filtering {initial_count} portfolios", "info")

        # Apply filters
        df = self._apply_minimum_filters(df, filter_criteria)
        df = self._apply_metric_filters(df, filter_criteria)
        df = self._apply_custom_filters(df, filter_criteria)

        # Convert back to list of dicts
        filtered_portfolios = df.to_dicts() if len(df) > 0 else []

        self.logger.log(
            f"Filtered from {initial_count} to {len(filtered_portfolios)} portfolios",
            "info",
        )

        return filtered_portfolios

    def _apply_minimum_filters(
        self,
        df: pl.DataFrame,
        criteria: Dict[str, Any],
    ) -> pl.DataFrame:
        """Apply minimum threshold filters."""
        minimums = criteria.get("minimums", {})

        # Win rate filter
        if "win_rate" in minimums and minimums["win_rate"] is not None:
            min_win_rate = minimums["win_rate"]
            if "Win Rate [%]" in df.columns:
                df = df.filter(pl.col("Win Rate [%]") >= min_win_rate * 100)
            elif "win_rate" in df.columns:
                df = df.filter(pl.col("win_rate") >= min_win_rate)

        # Total trades filter
        if "trades" in minimums and minimums["trades"] is not None:
            min_trades = minimums["trades"]
            if "Total Trades" in df.columns:
                df = df.filter(pl.col("Total Trades") >= min_trades)
            elif "total_trades" in df.columns:
                df = df.filter(pl.col("total_trades") >= min_trades)

        # Expectancy per trade filter
        if (
            "expectancy_per_trade" in minimums
            and minimums["expectancy_per_trade"] is not None
        ):
            min_expectancy = minimums["expectancy_per_trade"]
            if "Expectancy Per Trade" in df.columns:
                df = df.filter(pl.col("Expectancy Per Trade") >= min_expectancy)
            elif "expectancy_per_trade" in df.columns:
                df = df.filter(pl.col("expectancy_per_trade") >= min_expectancy)

        # Profit factor filter
        if "profit_factor" in minimums and minimums["profit_factor"] is not None:
            min_pf = minimums["profit_factor"]
            if "Profit Factor" in df.columns:
                df = df.filter(pl.col("Profit Factor") >= min_pf)
            elif "profit_factor" in df.columns:
                df = df.filter(pl.col("profit_factor") >= min_pf)

        # Sortino ratio filter
        if "sortino_ratio" in minimums and minimums["sortino_ratio"] is not None:
            min_sortino = minimums["sortino_ratio"]
            if "Sortino Ratio" in df.columns:
                df = df.filter(pl.col("Sortino Ratio") >= min_sortino)
            elif "sortino_ratio" in df.columns:
                df = df.filter(pl.col("sortino_ratio") >= min_sortino)

        # Score filter
        if "score" in minimums and minimums["score"] is not None:
            min_score = minimums["score"]
            if "Score" in df.columns:
                df = df.filter(pl.col("Score") >= min_score)
            elif "score" in df.columns:
                df = df.filter(pl.col("score") >= min_score)

        # Beats BNH filter
        if "beats_bnh" in minimums and minimums["beats_bnh"] is not None:
            min_beats = minimums["beats_bnh"]
            if "Beats BNH [%]" in df.columns:
                df = df.filter(pl.col("Beats BNH [%]") >= min_beats)
            elif "beats_bnh" in df.columns:
                df = df.filter(pl.col("beats_bnh") >= min_beats)

        return df

    def _apply_metric_filters(
        self,
        df: pl.DataFrame,
        criteria: Dict[str, Any],
    ) -> pl.DataFrame:
        """Apply metric-based filters."""
        # Filter by metric type if specified
        metric_types = criteria.get("metric_types", [])
        if metric_types and "Metric Type" in df.columns:
            df = df.filter(pl.col("Metric Type").is_in(metric_types))

        # Filter by signal status
        if criteria.get("require_signal_entry", False):
            if "Signal Entry" in df.columns:
                df = df.filter(pl.col("Signal Entry") == True)
            elif "has_signal_entry" in df.columns:
                df = df.filter(pl.col("has_signal_entry") == True)

        # Filter by open trade status
        if criteria.get("exclude_open_trades", False):
            if "Total Open Trades" in df.columns:
                df = df.filter(pl.col("Total Open Trades") == 0)
            elif "has_open_trade" in df.columns:
                df = df.filter(pl.col("has_open_trade") == False)

        return df

    def _apply_custom_filters(
        self,
        df: pl.DataFrame,
        criteria: Dict[str, Any],
    ) -> pl.DataFrame:
        """Apply custom filters based on additional criteria."""
        # Max drawdown filter
        max_drawdown = criteria.get("max_drawdown")
        if max_drawdown is not None:
            if "Max Drawdown [%]" in df.columns:
                df = df.filter(pl.col("Max Drawdown [%]").abs() <= abs(max_drawdown))
            elif "max_drawdown" in df.columns:
                df = df.filter(pl.col("max_drawdown").abs() <= abs(max_drawdown))

        # Annual return filter
        min_annual_return = criteria.get("min_annual_return")
        if min_annual_return is not None:
            if "Ann. Return [%]" in df.columns:
                df = df.filter(pl.col("Ann. Return [%]") >= min_annual_return)
            elif "annual_return" in df.columns:
                df = df.filter(pl.col("annual_return") >= min_annual_return)

        # Sharpe ratio filter
        min_sharpe = criteria.get("min_sharpe_ratio")
        if min_sharpe is not None:
            if "Sharpe Ratio" in df.columns:
                df = df.filter(pl.col("Sharpe Ratio") >= min_sharpe)
            elif "sharpe_ratio" in df.columns:
                df = df.filter(pl.col("sharpe_ratio") >= min_sharpe)

        return df

    def get_best_portfolios_by_metric(
        self,
        portfolios: List[Dict[str, Any]],
        metric: str,
        top_n: int = 10,
        ascending: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get the best portfolios sorted by a specific metric.

        Args:
            portfolios: List of portfolio dictionaries
            metric: Metric to sort by
            top_n: Number of top portfolios to return
            ascending: Sort in ascending order (default: False)

        Returns:
            Top N portfolios sorted by metric
        """
        if not portfolios:
            return []

        df = pl.DataFrame(portfolios)

        # Check if metric exists
        if metric not in df.columns:
            self.logger.log(f"Metric '{metric}' not found in portfolios", "warning")
            return portfolios[:top_n]

        # Sort and get top N
        df_sorted = df.sort(metric, descending=not ascending)
        df_top = df_sorted.head(top_n)

        return df_top.to_dicts()

    def group_portfolios_by_ticker(
        self,
        portfolios: List[Dict[str, Any]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group portfolios by ticker symbol.

        Args:
            portfolios: List of portfolio dictionaries

        Returns:
            Dictionary mapping ticker to list of portfolios
        """
        grouped = {}

        for portfolio in portfolios:
            ticker = portfolio.get("Ticker") or portfolio.get("ticker")
            if ticker:
                if ticker not in grouped:
                    grouped[ticker] = []
                grouped[ticker].append(portfolio)

        return grouped

    def get_filter_statistics(
        self,
        original_portfolios: List[Dict[str, Any]],
        filtered_portfolios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Get statistics about the filtering process.

        Args:
            original_portfolios: Original list of portfolios
            filtered_portfolios: Filtered list of portfolios

        Returns:
            Dictionary with filter statistics
        """
        original_count = len(original_portfolios)
        filtered_count = len(filtered_portfolios)

        stats = {
            "original_count": original_count,
            "filtered_count": filtered_count,
            "removed_count": original_count - filtered_count,
            "retention_rate": filtered_count / original_count
            if original_count > 0
            else 0,
        }

        # Get ticker distribution
        if filtered_portfolios:
            grouped = self.group_portfolios_by_ticker(filtered_portfolios)
            stats["tickers_retained"] = list(grouped.keys())
            stats["portfolios_per_ticker"] = {
                ticker: len(portfolios) for ticker, portfolios in grouped.items()
            }
        else:
            stats["tickers_retained"] = []
            stats["portfolios_per_ticker"] = {}

        return stats
