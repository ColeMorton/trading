"""
Unified Portfolio Filtering Module

This module consolidates portfolio filtering functionality across all trading strategies,
eliminating duplication while maintaining strategy-specific behavior through
configuration and polymorphism.
"""

from collections.abc import Callable
from typing import Any

import polars as pl

from app.tools.export_csv import ExportConfig
from app.tools.portfolio.metrics import DURATION_METRICS, NUMERIC_METRICS
from app.tools.portfolio.schema_detection import (
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)


class PortfolioFilterConfig:
    """Configuration for portfolio filtering operations."""

    def __init__(self, strategy_type: str):
        """Initialize filter configuration for a strategy type.

        Args:
            strategy_type: Type of strategy (SMA, MACD, MEAN_REVERSION, etc.)
        """
        self.strategy_type = strategy_type.upper()
        self._setup_strategy_specific_config()

    def _setup_strategy_specific_config(self):
        """Setup strategy-specific configuration parameters."""
        # Period parameter configurations per strategy (updated naming)
        self.period_params = {
            "SMA": ["Fast Period", "Slow Period"],
            "EMA": ["Fast Period", "Slow Period"],
            "MACD": ["Fast Period", "Slow Period", "Signal Period"],
            "MEAN_REVERSION": ["Change PCT"],
            "RANGE": ["Range Window", "Range Period"],
        }

        # Legacy window parameters for backwards compatibility
        self.window_params = {
            "SMA": ["Fast Period", "Slow Period"],
            "EMA": ["Fast Period", "Slow Period"],
            "MACD": ["Fast Period", "Slow Period", "Signal Period"],
            "MEAN_REVERSION": ["Change PCT"],
            "RANGE": ["Range Window", "Range Period"],
        }

        # Metrics to include in filtering per strategy
        self.relevant_metrics = {
            "SMA": NUMERIC_METRICS + DURATION_METRICS,
            "EMA": NUMERIC_METRICS + DURATION_METRICS,
            "MACD": NUMERIC_METRICS + DURATION_METRICS,
            "MEAN_REVERSION": NUMERIC_METRICS + DURATION_METRICS,
            "RANGE": NUMERIC_METRICS + DURATION_METRICS,
        }

        # Strategy-specific display preferences
        self.display_preferences = {
            "SMA": {"sort_by": "Total Return [%]", "sort_asc": False},
            "EMA": {"sort_by": "Total Return [%]", "sort_asc": False},
            "MACD": {"sort_by": "Score", "sort_asc": False},
            "MEAN_REVERSION": {"sort_by": "Total Return [%]", "sort_asc": False},
            "RANGE": {"sort_by": "Total Return [%]", "sort_asc": False},
        }

    def get_window_parameters(self) -> list[str]:
        """Get window/period parameters for the strategy."""
        # First try new period params, fall back to legacy window params
        period_params = self.period_params.get(self.strategy_type)
        if period_params:
            return period_params
        return self.window_params.get(
            self.strategy_type, ["Fast Period", "Slow Period"],
        )

    def get_relevant_metrics(self) -> list[str]:
        """Get relevant metrics for the strategy."""
        return self.relevant_metrics.get(
            self.strategy_type, NUMERIC_METRICS + DURATION_METRICS,
        )

    def get_display_preferences(self) -> dict[str, Any]:
        """Get display preferences for the strategy."""
        return self.display_preferences.get(
            self.strategy_type, {"sort_by": "Total Return [%]", "sort_asc": False},
        )


def create_metric_result(
    metric: str,
    row_idx: int,
    df: pl.DataFrame,
    label: str,
    window_params: list[str] | None = None,
) -> dict[str, Any]:
    """Create result dictionary for a metric including strategy-specific parameters.

    Args:
        metric: Name of the metric being processed
        row_idx: Index of the row in the DataFrame
        df: Original DataFrame
        label: Label for the metric (Most, Least, Mean, Median)
        window_params: List of window parameter names for the strategy

    Returns:
        Result dictionary
    """
    # Get the full row from the DataFrame
    row = df.row(row_idx, named=True)

    # Use default window params if not provided
    if window_params is None:
        pass

    # Create result with strategy-specific parameters
    result = {"Metric Type": f"{label} {metric}"}

    # Add window parameters that exist in the row
    for param in window_params:
        if param in row:
            result[param] = row[param]
        # Set default values for missing parameters
        elif param == "Signal Period" or "Window" in param:
            result[param] = 0
        elif "PCT" in param:
            result[param] = 0.0

    # Add remaining columns (excluding parameters we already handled)
    handled_columns = {"Metric Type"} | set(window_params)
    for col in df.columns:
        if col not in handled_columns:
            result[col] = row.get(col)

    return result


def get_metric_rows(df: pl.DataFrame, metric: str) -> dict[str, int]:
    """Get row indices for extreme values of a metric.

    Args:
        df: DataFrame containing portfolio data
        metric: Name of the metric column

    Returns:
        Dictionary with row indices for most, least, mean, and median values
    """
    if metric not in df.columns:
        return {}

    # Get series for the metric
    metric_series = df[metric]

    # Handle potential None/null values
    valid_series = metric_series.drop_nulls()
    if len(valid_series) == 0:
        return {}

    # Find extreme values
    max_idx = metric_series.arg_max()
    min_idx = metric_series.arg_min()

    # Calculate mean and find closest value
    try:
        mean_val = valid_series.mean()
        mean_idx = (metric_series - mean_val).abs().arg_min()
    except Exception:
        # Handle string columns or non-numeric data
        mean_idx = None

    # Calculate median and find closest value
    try:
        median_val = valid_series.median()
        median_idx = (metric_series - median_val).abs().arg_min()
    except Exception:
        # Handle string columns or non-numeric data
        median_idx = None

    return {"most": max_idx, "least": min_idx, "mean": mean_idx, "median": median_idx}


def create_metric_result_from_rows(
    metric: str,
    rows: dict[str, int],
    df: pl.DataFrame,
    window_params: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Create result dictionaries from metric row indices.

    Args:
        metric: Name of the metric
        rows: Dictionary with row indices for different statistics
        df: Original DataFrame
        window_params: List of window parameter names

    Returns:
        List of result dictionaries
    """
    results = []
    labels = {"most": "Most", "least": "Least", "mean": "Mean", "median": "Median"}

    for stat, row_idx in rows.items():
        if row_idx is not None:
            label = labels.get(stat, stat.title())
            result = create_metric_result(metric, row_idx, df, label, window_params)
            results.append(result)

    return results


def _process_metrics(
    df: pl.DataFrame, metrics: list[str], window_params: list[str] | None = None,
) -> list[dict]:
    """Process a list of metrics and create result rows.

    Args:
        df: DataFrame containing portfolio data
        metrics: List of metrics to process
        window_params: List of window parameter names for the strategy

    Returns:
        List of result dictionaries
    """
    result_rows = []

    for metric in metrics:
        if metric in df.columns:
            # Get extreme value row indices
            rows = get_metric_rows(df, metric)

            # Create result dictionaries for each extreme value
            metric_results = create_metric_result_from_rows(
                metric, rows, df, window_params,
            )
            result_rows.extend(metric_results)

    return result_rows


def _prepare_result_df(
    result_rows: list[dict], config: ExportConfig, filter_config: PortfolioFilterConfig,
) -> pl.DataFrame:
    """Prepare result DataFrame with proper sorting and schema compliance.

    Args:
        result_rows: List of result dictionaries
        config: Export configuration
        filter_config: Portfolio filter configuration

    Returns:
        Polars DataFrame with filtered results
    """
    if not result_rows:
        return pl.DataFrame()

    # Create DataFrame from results
    result_df = pl.DataFrame(result_rows)

    # Apply strategy-specific sorting preferences
    display_prefs = filter_config.get_display_preferences()
    sort_by = config.get("SORT_BY", display_prefs["sort_by"])
    sort_asc = config.get("SORT_ASC", display_prefs["sort_asc"])

    # Sort if the column exists
    if sort_by in result_df.columns:
        result_df = result_df.sort(sort_by, descending=not sort_asc)

    # Ensure schema compliance
    try:
        # Detect and normalize schema
        schema_version = detect_schema_version(result_df)
        result_df = normalize_portfolio_data(result_df, schema_version)

        # Ensure allocation sums to 100%
        result_df = ensure_allocation_sum_100_percent(result_df)

    except Exception:
        # If schema normalization fails, continue with original DataFrame
        pass

    return result_df


def filter_portfolios(
    portfolios_df: pl.DataFrame,
    config: ExportConfig,
    log: Callable | None = None,
    strategy_type: str | None = None,
) -> pl.DataFrame:
    """Filter portfolios and create extreme value analysis using unified filtering logic.

    Args:
        portfolios_df: DataFrame containing portfolio data
        config: Configuration dictionary
        log: Optional logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        Filtered DataFrame with extreme value analysis
    """
    if portfolios_df.is_empty():
        if log:
            log("No portfolios to filter", "warning")
        return pl.DataFrame()

    # Determine strategy type
    if strategy_type is None:
        strategy_type = config.get("STRATEGY_TYPE", "SMA")

    # Create filter configuration
    filter_config = PortfolioFilterConfig(strategy_type)

    try:
        if log:
            log(
                f"Filtering {len(portfolios_df)} portfolios for {strategy_type} strategy",
            )

        # Get strategy-specific metrics and parameters
        relevant_metrics = filter_config.get_relevant_metrics()
        window_params = filter_config.get_window_parameters()

        # Filter metrics to only those present in the DataFrame
        available_metrics = [
            metric for metric in relevant_metrics if metric in portfolios_df.columns
        ]

        if log:
            log(
                f"Processing {len(available_metrics)} metrics: {', '.join(available_metrics[:5])}{'...' if len(available_metrics) > 5 else ''}",
            )

        # Apply MINIMUMS filtering first if configured
        if "MINIMUMS" in config:
            from app.tools.portfolio.filtering_service import PortfolioFilterService

            filter_service = PortfolioFilterService()
            filtered_portfolios_df = filter_service.filter_portfolios_dataframe(
                portfolios_df, config, log,
            )

            if filtered_portfolios_df is None or len(filtered_portfolios_df) == 0:
                if log:
                    log("No portfolios remain after MINIMUMS filtering", "warning")
                return pl.DataFrame()

            # Use filtered portfolios for extreme value processing
            portfolios_df = filtered_portfolios_df

            if log:
                log(
                    f"Applied MINIMUMS filtering: {len(portfolios_df)} portfolios remain",
                )

        # Process metrics to get extreme values from filtered portfolios
        result_rows = _process_metrics(portfolios_df, available_metrics, window_params)

        if not result_rows:
            if log:
                log("No metric results generated", "warning")
            return pl.DataFrame()

        # Prepare final result DataFrame
        result_df = _prepare_result_df(result_rows, config, filter_config)

        if log:
            log(f"Generated {len(result_df)} filtered portfolio results")

        return result_df

    except Exception as e:
        if log:
            log(f"Error filtering portfolios: {e!s}", "error")
        return pl.DataFrame()


def filter_and_export_portfolios(
    portfolios_df: pl.DataFrame,
    config: ExportConfig,
    log: Callable | None = None,
    strategy_type: str | None = None,
) -> bool:
    """Filter portfolios and export to CSV with unified filtering logic.

    Args:
        portfolios_df: DataFrame containing portfolio data
        config: Configuration dictionary
        log: Optional logging function
        strategy_type: Strategy type (auto-detected if not provided)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Filter portfolios
        filtered_df = filter_portfolios(portfolios_df, config, log, strategy_type)

        if filtered_df.is_empty():
            if log:
                log("No filtered portfolios to export", "warning")
            return False

        # Export using centralized export system
        from app.tools.strategy.export_portfolios import export_portfolios

        # Convert DataFrame to list of dictionaries for export
        portfolio_dicts = filtered_df.to_dicts()

        # Export filtered portfolios
        _, success = export_portfolios(
            portfolios=portfolio_dicts,
            config=config,
            export_type="portfolios_filtered",
            log=log,
            feature_dir="",  # Use standard directories
        )

        if success and log:
            strategy_type = strategy_type or config.get("STRATEGY_TYPE", "SMA")
            log(
                f"Successfully exported {len(portfolio_dicts)} filtered {strategy_type} portfolios",
            )

        return success

    except Exception as e:
        if log:
            log(f"Error filtering and exporting portfolios: {e!s}", "error")
        return False


# Convenience functions for backward compatibility
def create_metric_summary(
    df: pl.DataFrame, metric: str, strategy_type: str = "SMA",
) -> list[dict[str, Any]]:
    """Create metric summary for a specific metric (convenience function).

    Args:
        df: DataFrame containing portfolio data
        metric: Name of the metric to analyze
        strategy_type: Strategy type for parameter extraction

    Returns:
        List of metric summary dictionaries
    """
    filter_config = PortfolioFilterConfig(strategy_type)
    window_params = filter_config.get_window_parameters()

    rows = get_metric_rows(df, metric)
    return create_metric_result_from_rows(metric, rows, df, window_params)


def get_extreme_values(
    df: pl.DataFrame, metrics: list[str] | None = None, strategy_type: str = "SMA",
) -> pl.DataFrame:
    """Get extreme values for specified metrics (convenience function).

    Args:
        df: DataFrame containing portfolio data
        metrics: List of metrics to analyze (uses all relevant metrics if None)
        strategy_type: Strategy type for configuration

    Returns:
        DataFrame with extreme value analysis
    """
    filter_config = PortfolioFilterConfig(strategy_type)

    if metrics is None:
        metrics = filter_config.get_relevant_metrics()

    # Filter to available metrics
    available_metrics = [metric for metric in metrics if metric in df.columns]

    # Process metrics
    window_params = filter_config.get_window_parameters()
    result_rows = _process_metrics(df, available_metrics, window_params)

    return pl.DataFrame(result_rows) if result_rows else pl.DataFrame()
