"""
Portfolio Filtering Service

This module provides a unified filtering service that consolidates the duplicate filtering
logic from ma_cross/1_get_portfolios.py and ma_cross/tools/strategy_execution.py.

Implements the Chain of Responsibility pattern for extensible filtering.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import polars as pl


@dataclass
class FilterConfig:
    """Configuration for a single filter."""

    config_key: str
    column_name: str
    data_type: pl.DataType
    multiplier: float = 1.0
    message_prefix: str = ""


class PortfolioFilter(ABC):
    """Abstract base class for portfolio filters following Chain of Responsibility pattern."""

    def __init__(self, next_filter: Optional["PortfolioFilter"] = None):
        self._next_filter = next_filter

    @abstractmethod
    def apply(
        self,
        df: Union[pl.DataFrame, List[Dict[str, Any]]],
        config: Dict[str, Any],
        log: Callable,
    ) -> Union[pl.DataFrame, List[Dict[str, Any]]]:
        """Apply the filter to the data."""

    def set_next(self, next_filter: "PortfolioFilter") -> "PortfolioFilter":
        """Set the next filter in the chain."""
        self._next_filter = next_filter
        return next_filter

    def _apply_next(
        self,
        df: Union[pl.DataFrame, List[Dict[str, Any]]],
        config: Dict[str, Any],
        log: Callable,
    ) -> Union[pl.DataFrame, List[Dict[str, Any]]]:
        """Apply the next filter in the chain."""
        if self._next_filter:
            return self._next_filter.apply(df, config, log)
        return df


class InvalidMetricsFilter(PortfolioFilter):
    """Filter to remove portfolios with invalid metrics."""

    def apply(
        self,
        df: Union[pl.DataFrame, List[Dict[str, Any]]],
        config: Dict[str, Any],
        log: Callable,
    ) -> Union[pl.DataFrame, List[Dict[str, Any]]]:
        """Apply invalid metrics filtering."""
        # Convert to DataFrame if needed
        if isinstance(df, list):
            if not df:
                return self._apply_next(df, config, log)
            df = pl.DataFrame(df)

        # Apply invalid metrics filtering
        from app.tools.portfolio.filters import filter_invalid_metrics

        filtered_df = filter_invalid_metrics(df, log)

        if filtered_df is None or len(filtered_df) == 0:
            log("No portfolios remain after filtering invalid metrics", "warning")
            return []

        return self._apply_next(filtered_df, config, log)


class MinimumsFilter(PortfolioFilter):
    """Filter portfolios based on MINIMUMS configuration."""

    # Standard filter configurations used across the codebase
    FILTER_CONFIGS = [
        FilterConfig(
            "WIN_RATE",
            "Win Rate [%]",
            pl.Float64,
            100,
            "Filtered portfolios with win rate",
        ),
        FilterConfig(
            "TRADES", "Total Trades", pl.Int64, 1, "Filtered portfolios with at least"
        ),
        FilterConfig(
            "EXPECTANCY_PER_TRADE",
            "Expectancy Per Trade",
            pl.Float64,
            1,
            "Filtered portfolios with expectancy per trade",
        ),
        FilterConfig(
            "PROFIT_FACTOR",
            "Profit Factor",
            pl.Float64,
            1,
            "Filtered portfolios with profit factor",
        ),
        FilterConfig("SCORE", "Score", pl.Float64, 1, "Filtered portfolios with score"),
        FilterConfig(
            "SORTINO_RATIO",
            "Sortino Ratio",
            pl.Float64,
            1,
            "Filtered portfolios with Sortino ratio",
        ),
        FilterConfig(
            "BEATS_BNH",
            "Beats BNH [%]",
            pl.Float64,
            1,
            "Filtered portfolios with Beats BNH percentage",
        ),
    ]

    def apply(
        self,
        df: Union[pl.DataFrame, List[Dict[str, Any]]],
        config: Dict[str, Any],
        log: Callable,
    ) -> Union[pl.DataFrame, List[Dict[str, Any]]]:
        """Apply MINIMUMS filtering."""

        # Check if MINIMUMS configuration exists
        if "MINIMUMS" not in config:
            return self._apply_next(df, config, log)

        # Convert to DataFrame if needed
        was_list = isinstance(df, list)
        if was_list:
            if not df:
                return self._apply_next(df, config, log)
            df = pl.DataFrame(df)

        if len(df) == 0:
            return self._apply_next([] if was_list else df, config, log)

        original_count = len(df)
        minimums = config["MINIMUMS"]

        # Apply each filter from the configuration
        for filter_config in self.FILTER_CONFIGS:
            if (
                filter_config.config_key in minimums
                and filter_config.column_name in df.columns
            ):
                df = self._apply_single_filter(
                    df, filter_config, minimums[filter_config.config_key], log
                )

        # Log filtering results
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            log(
                f"Filtered out {filtered_count} portfolios based on MINIMUMS criteria",
                "info",
            )
            log(f"Remaining portfolios after MINIMUMS filtering: {len(df)}", "info")

        # Convert back to original format
        if was_list:
            result = df.to_dicts() if len(df) > 0 else []
        else:
            result = df

        return self._apply_next(result, config, log)

    def _apply_single_filter(
        self,
        df: pl.DataFrame,
        filter_config: FilterConfig,
        min_value: float,
        log: Callable,
    ) -> pl.DataFrame:
        """Apply a single filter to the DataFrame."""
        adjusted_value = min_value * filter_config.multiplier
        df = df.filter(
            pl.col(filter_config.column_name).cast(filter_config.data_type)
            >= adjusted_value
        )

        # Format the message based on the filter type
        if filter_config.message_prefix:
            if "win rate" in filter_config.message_prefix.lower():
                log(f"{filter_config.message_prefix} >= {adjusted_value}%", "info")
            elif "trades" in filter_config.message_prefix.lower():
                log(f"{filter_config.message_prefix} >= {int(adjusted_value)}", "info")
            else:
                log(f"{filter_config.message_prefix} >= {adjusted_value}", "info")

        return df


class PortfolioFilterService:
    """
    Unified portfolio filtering service that consolidates duplicate filtering logic.

    This service provides a single interface for portfolio filtering that replaces
    the duplicate logic found in ma_cross/1_get_portfolios.py and
    ma_cross/tools/strategy_execution.py.
    """

    def __init__(self):
        """Initialize the filtering service with default filter chain."""
        self._setup_default_chain()

    def _setup_default_chain(self):
        """Set up the default filter chain."""
        # Create filter chain: InvalidMetrics -> Minimums
        self.invalid_metrics_filter = InvalidMetricsFilter()
        self.minimums_filter = MinimumsFilter()

        # Chain the filters
        self.invalid_metrics_filter.set_next(self.minimums_filter)

    def filter_portfolios_dataframe(
        self, df: pl.DataFrame, config: Dict[str, Any], log: Callable
    ) -> Optional[pl.DataFrame]:
        """
        Filter portfolios provided as a Polars DataFrame.

        This method replicates the filtering logic from strategy_execution.py
        where the input is already a DataFrame.

        Args:
            df: Polars DataFrame containing portfolio data
            config: Configuration dictionary
            log: Logging function

        Returns:
            Filtered DataFrame or None if no portfolios remain
        """
        if df is None or len(df) == 0:
            log("No portfolios to filter - returning None", "warning")
            return None

        # Apply the filter chain
        result = self.invalid_metrics_filter.apply(df, config, log)

        # Handle the case where result is empty
        if isinstance(result, list) and not result:
            return None
        elif isinstance(result, pl.DataFrame) and len(result) == 0:
            return None

        return result

    def filter_portfolios_list(
        self, portfolios: List[Dict[str, Any]], config: Dict[str, Any], log: Callable
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Filter portfolios provided as a list of dictionaries.

        This method replicates the filtering logic from 1_get_portfolios.py
        where the input is a list of portfolio dictionaries.

        Args:
            portfolios: List of portfolio dictionaries
            config: Configuration dictionary
            log: Logging function

        Returns:
            Filtered list of dictionaries or None if no portfolios remain
        """
        if not portfolios:
            log("No portfolios to filter - returning None", "warning")
            return None

        # Apply the filter chain starting with list format
        result = self.invalid_metrics_filter.apply(portfolios, config, log)

        # Handle the case where result is empty
        if isinstance(result, list) and not result:
            return None
        elif isinstance(result, pl.DataFrame) and len(result) == 0:
            return None

        # Ensure we return a list
        if isinstance(result, pl.DataFrame):
            return result.to_dicts() if len(result) > 0 else None

        return result

    def create_custom_chain(self, filters: List[PortfolioFilter]) -> PortfolioFilter:
        """
        Create a custom filter chain.

        Args:
            filters: List of filters to chain together

        Returns:
            The first filter in the chain
        """
        if not filters:
            raise ValueError("At least one filter must be provided")

        for i in range(len(filters) - 1):
            filters[i].set_next(filters[i + 1])

        return filters[0]


# Legacy compatibility functions for easy migration
def apply_minimums_filter_to_dataframe(
    df: pl.DataFrame, config: Dict[str, Any], log: Callable
) -> pl.DataFrame:
    """
    Legacy compatibility function for DataFrame filtering.

    This function provides the exact same interface as the apply_filter function
    from strategy_execution.py for easy migration.
    """
    service = PortfolioFilterService()
    result = service.filter_portfolios_dataframe(df, config, log)
    return result if result is not None else pl.DataFrame()


def apply_minimums_filter_to_list(
    portfolios: List[Dict[str, Any]], config: Dict[str, Any], log: Callable
) -> List[Dict[str, Any]]:
    """
    Legacy compatibility function for list filtering.

    This function provides the exact same interface as the filtering logic
    from 1_get_portfolios.py for easy migration.
    """
    service = PortfolioFilterService()
    result = service.filter_portfolios_list(portfolios, config, log)
    return result if result is not None else []
