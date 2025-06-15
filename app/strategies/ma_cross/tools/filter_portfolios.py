"""
Portfolio Filtering Module

This module handles the filtering and analysis of portfolio metrics,
creating summaries of extreme values.
"""

from typing import Callable, Dict, List

import polars as pl

from app.tools.export_csv import ExportConfig

# Import export_portfolios inside functions to avoid circular imports
from app.tools.portfolio.collection import sort_portfolios
from app.tools.portfolio.metrics import (
    DURATION_METRICS,
    NUMERIC_METRICS,
    create_metric_result,
    get_metric_rows,
)
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    ensure_allocation_sum_100_percent,
    normalize_portfolio_data,
)


def _process_metrics(
    df: pl.DataFrame, metrics: List[str], columns: List[str]
) -> List[Dict]:
    """Process a list of metrics and create result rows.

    Args:
        df: DataFrame containing portfolio data
        metrics: List of metrics to process
        columns: DataFrame columns

    Returns:
        List of result dictionaries
    """
    result_rows = []
    for metric in metrics:
        if metric in df.columns:
            rows = get_metric_rows(df, metric)
            result_rows.extend(create_metric_result(metric, rows, columns))
    return result_rows


def _prepare_result_df(result_rows: List[Dict], config: ExportConfig) -> pl.DataFrame:
    """Prepare and format the result DataFrame.

    Args:
        result_rows: List of result dictionaries
        config: Configuration dictionary

    Returns:
        Formatted Polars DataFrame
    """
    if not result_rows:
        return pl.DataFrame()

    result_df = pl.DataFrame(result_rows)

    # Use centralized sorting function
    result_df = sort_portfolios(result_df, config)

    # Reorder columns to put Metric Type first
    cols = ["Metric Type"] + [col for col in result_df.columns if col != "Metric Type"]
    return result_df.select(cols)


def filter_portfolios(
    df: pl.DataFrame, config: ExportConfig, log: Callable
) -> pl.DataFrame:
    """Filter and analyze portfolio metrics, creating a summary of extreme values.

    Args:
        df: DataFrame containing portfolio data
        config: Configuration dictionary
        log: Logging function for recording events and errors

    Returns:
        DataFrame containing filtered and analyzed portfolio data
    """
    try:
        # Check if DataFrame is empty
        if len(df) == 0:
            log("No portfolios to filter - returning empty DataFrame", "warning")
            return df

        # Apply strategy type filtering specifically for portfolios_filtered export
        # This ensures each strategy type gets its own filtered file
        strategy_type = config.get("STRATEGY_TYPE")
        if strategy_type and "Strategy Type" in df.columns:
            original_count = len(df)
            df = df.filter(pl.col("Strategy Type") == strategy_type)
            log(
                f"Filtered portfolios_filtered from {original_count} to {len(df)} for strategy type: {strategy_type}",
                "info",
            )

            # Check if filtering removed all portfolios
            if len(df) == 0:
                log(
                    f"No portfolios found for strategy type: {strategy_type}", "warning"
                )
                return df

        # Process metrics
        result_rows = []
        result_rows.extend(_process_metrics(df, NUMERIC_METRICS, df.columns))
        result_rows.extend(_process_metrics(df, DURATION_METRICS, df.columns))

        # Prepare result DataFrame
        result_df = _prepare_result_df(result_rows, config)
        if len(result_df) == 0:
            log("No results generated - returning empty DataFrame", "warning")
            return result_df

        # Log configuration details
        log(f"Filtering results for {config.get('TICKER', '')}")
        log(f"USE_HOURLY: {config.get('USE_HOURLY', False)}")
        log(f"STRATEGY_TYPE: {config.get('STRATEGY_TYPE', 'EMA')}")
        log(f"USE_CURRENT: {config.get('USE_CURRENT', False)}")

        # Check for allocation and stop loss values in config
        if "ALLOCATION" in config:
            log(f"ALLOCATION: {config.get('ALLOCATION')}%", "info")
        if "STOP_LOSS" in config:
            log(f"STOP_LOSS: {config.get('STOP_LOSS')}%", "info")

        # Convert to dictionaries and normalize schema
        portfolio_dicts = result_df.to_dicts()

        # Detect schema version
        schema_version = detect_schema_version(portfolio_dicts)
        log(
            f"Detected schema version for filtered portfolios: {schema_version.name}",
            "info",
        )

        # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
        normalized_portfolios = normalize_portfolio_data(
            portfolio_dicts, schema_version, log
        )

        # Ensure allocation values sum to 100% if they exist
        if schema_version == SchemaVersion.EXTENDED:
            normalized_portfolios = ensure_allocation_sum_100_percent(
                normalized_portfolios, log
            )

        # Import export_portfolios here to avoid circular imports
        from app.tools.strategy.export_portfolios import export_portfolios

        # Export filtered results using export_portfolios
        export_portfolios(
            portfolios=normalized_portfolios,
            config=config,
            export_type="portfolios_filtered",
            log=log,
        )

        print(f"Analysis complete. Total rows in output: {len(result_rows)}")
        return result_df

    except Exception as e:
        log(f"Failed to filter portfolios: {e}", "error")
        raise
