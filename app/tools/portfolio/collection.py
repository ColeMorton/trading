"""
Portfolio Collection Module

This module handles the collection, sorting, and export of portfolios.
It provides centralized functionality for consistent portfolio operations
across the application.
"""

from typing import Any, Callable, Dict, List, Optional, Union

import polars as pl

from app.strategies.ma_cross.config_types import Config


# Define our own error class to avoid circular imports
class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""


def sort_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame], config: Config
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Sort portfolios using consistent logic across the application.

    Args:
        portfolios: Either a list of portfolio dictionaries or a Polars DataFrame
        config: Configuration dictionary containing sorting preferences

    Returns:
        Sorted portfolios in the same format as input (list or DataFrame)

    Note:
        Uses config['SORT_BY'] to determine sort column, defaults to 'Total Return [%]'
    """
    # Convert to DataFrame if necessary
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios

    # Sort using consistent logic
    sort_by = config.get("SORT_BY", "Total Return [%]")
    sorted_df = df.sort(sort_by, descending=True)

    # Return in original format
    return sorted_df.to_dicts() if input_is_list else sorted_df


def deduplicate_and_aggregate_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    log: Optional[Callable] | None = None,
    desired_metric_types: Optional[List[str]] | None = None,
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """
    Deduplicate portfolios to have exactly ONE row per {ticker,strategy_type} combination.
    Uses get_best_portfolio to find the best configuration for each ticker+strategy,
    then aggregates ALL metric types for that specific best configuration.

    Args:
        portfolios: Portfolio data
        log: Logging function
        desired_metric_types: Optional list of specific Metric Types to keep.
                             If None, keeps all. If provided, filters to only these types.

    Returns:
        Deduplicated portfolios with aggregated metric types (one per ticker+strategy)
    """
    from app.tools.portfolio.selection import get_best_portfolio

    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios

    # Filter to desired Metric Types if specified
    if desired_metric_types is not None and "Metric Type" in df.columns:
        original_count = len(df)
        df = df.filter(pl.col("Metric Type").is_in(desired_metric_types))
        if log:
            log(
                f"Filtered to desired Metric Types: {len(df)}/{original_count} rows kept",
                "info",
            )

    # Verify Score column exists (should be calculated by stats_converter)
    if "Score" not in df.columns:
        if log:
            log("Warning: Score column not found in portfolios", "warning")
        # Use Total Return [%] as fallback
        df = df.with_columns(pl.col("Total Return [%]").cast(pl.Float64).alias("Score"))

    # Check if Metric Type column exists
    if "Metric Type" not in df.columns:
        if log:
            log("No Metric Type column found, skipping aggregation", "warning")
        return df.to_dicts() if input_is_list else df

    # Get unique ticker+strategy combinations
    ticker_strategy_combinations = df.select(["Ticker", "Strategy Type"]).unique()

    result_portfolios = []

    if log:
        log(
            f"Processing {len(ticker_strategy_combinations)} ticker+strategy combinations",
            "info",
        )

    for combination in ticker_strategy_combinations.to_dicts():
        ticker = combination["Ticker"]
        strategy_type = combination["Strategy Type"]

        # Get all portfolios for this ticker+strategy combination
        ticker_strategy_df = df.filter(
            (pl.col("Ticker") == ticker) & (pl.col("Strategy Type") == strategy_type)
        )

        if log:
            log(
                f"Processing {ticker} {strategy_type}: {len(ticker_strategy_df)} portfolios",
                "info",
            )

        # Use get_best_portfolio to find the best configuration
        # Create a mock config for get_best_portfolio
        mock_config = {"SORT_BY": "Score"}
        best_portfolio = get_best_portfolio(ticker_strategy_df, mock_config, log)

        if best_portfolio is None:
            if log:
                log(
                    f"No best portfolio found for {ticker} {strategy_type}, using highest score",
                    "warning",
                )
            # Fallback: use the highest scoring portfolio
            best_row = (
                ticker_strategy_df.sort("Score", descending=True).head(1).to_dicts()[0]
            )
            best_short = best_row["Short Window"]
            best_long = best_row["Long Window"]
            best_signal = best_row.get("Signal Window", 0)
        else:
            # get_best_portfolio may rename columns, so check both formats
            if "Short Window" in best_portfolio:
                best_short = best_portfolio["Short Window"]
                best_long = best_portfolio["Long Window"]
            else:
                # Check for renamed columns (SMA_FAST/EMA_FAST, SMA_SLOW/EMA_SLOW)
                strategy_prefix = "SMA" if strategy_type == "SMA" else "EMA"
                fast_col = f"{strategy_prefix}_FAST"
                slow_col = f"{strategy_prefix}_SLOW"
                best_short = best_portfolio.get(
                    fast_col, best_portfolio.get("Short Window", 0)
                )
                best_long = best_portfolio.get(
                    slow_col, best_portfolio.get("Long Window", 0)
                )
            best_signal = best_portfolio.get("Signal Window", 0)

        # Find ALL metric types for this exact best configuration
        best_config_df = ticker_strategy_df.filter(
            (pl.col("Short Window") == best_short)
            & (pl.col("Long Window") == best_long)
            & (pl.col("Signal Window") == best_signal)
        )

        if len(best_config_df) == 0:
            if log:
                log(
                    f"No portfolios found for best config {ticker} {strategy_type} {best_short}/{best_long}",
                    "warning",
                )
            continue

        # Collect all metric types for this configuration
        metric_types = best_config_df.select("Metric Type").to_series().to_list()

        # Sort metric types by priority: Most → Mean → Median → Least
        def get_priority(metric: str) -> int:
            metric = metric.strip()
            if metric.startswith("Most"):
                return 1
            elif metric.startswith("Mean"):
                return 2
            elif metric.startswith("Median"):
                return 3
            elif metric.startswith("Least"):
                return 4
            else:
                return 5

        sorted_metrics = sorted(metric_types, key=lambda x: (get_priority(x), x))
        aggregated_metric_type = ", ".join(sorted_metrics)

        # Use the best portfolio as the base and update the Metric Type
        final_portfolio = (
            best_config_df.sort("Score", descending=True).head(1).to_dicts()[0]
        )
        final_portfolio["Metric Type"] = aggregated_metric_type

        result_portfolios.append(final_portfolio)

        if log:
            log(
                f"Best config for {ticker} {strategy_type}: {best_short}/{best_long}, {len(metric_types)} metric types",
                "info",
            )

    # Sort result by Score descending
    result_df = pl.DataFrame(result_portfolios).sort("Score", descending=True)

    if log:
        log(
            f"Deduplicated portfolios from {len(df)} to {len(result_df)} rows (one per ticker+strategy)",
            "info",
        )

        # Log sample of results
        for i, row in enumerate(result_df.head(3).to_dicts()):
            ticker = row["Ticker"]
            strategy = row["Strategy Type"]
            short_window = row["Short Window"]
            long_window = row["Long Window"]
            metric_type = row["Metric Type"]
            log(
                f"Result {i+1}: {ticker} {strategy} {short_window}/{long_window} - {metric_type}",
                "info",
            )

    return result_df.to_dicts() if input_is_list else result_df


def export_best_portfolios(
    portfolios: List[Dict[str, Any]], config: Config, log: callable
) -> bool:
    """Export the best portfolios to a CSV file with deduplication.

    Args:
        portfolios: List of portfolio dictionaries to export
        config: Configuration for the export
        log: Logging function

    Returns:
        bool: True if export successful, False otherwise
    """
    if not portfolios:
        log("No portfolios to export", "warning")
        return False

    try:
        # Log configuration for debugging
        log("Configuration for export_best_portfolios:", "info")
        required_fields = ["BASE_DIR", "TICKER"]
        for field in required_fields:
            log(
                f"Field '{field}' present: {field in config}, value: {config.get(field)}",
                "info",
            )

        # Sort by Score instead of Total Return [%]
        original_sort_by = config.get("SORT_BY", "Total Return [%]")
        config["SORT_BY"] = "Score"

        # Sort portfolios
        sorted_portfolios = sort_portfolios(portfolios, config)

        # Use desired metric types from config if provided, otherwise use defaults
        desired_metric_types = config.get(
            "DESIRED_METRIC_TYPES",
            [
                "Most Total Return [%]",
                "Median Total Trades",
                "Mean Avg Winning Trade [%]",
                "Most Sharpe Ratio",
                "Most Omega Ratio",
                "Most Sortino Ratio",
            ],
        )

        # Apply deduplication and metric type aggregation
        deduplicated_portfolios = deduplicate_and_aggregate_portfolios(
            sorted_portfolios, log, desired_metric_types
        )

        # Restore original sort configuration
        config["SORT_BY"] = original_sort_by

        # Import export_portfolios here to avoid circular imports
        if log:
            log("Importing export_portfolios to avoid circular imports", "info")
        try:
            from app.tools.strategy.export_portfolios import export_portfolios
        except ImportError as e:
            log(
                f"Failed to import export_portfolios due to circular import: {str(e)}",
                "error",
            )
            return False

        export_portfolios(
            portfolios=deduplicated_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log,
        )

        log(
            f"Exported {len(deduplicated_portfolios)} unique portfolios sorted by Score"
        )
        return True

    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False


def combine_strategy_portfolios(
    ema_portfolios: List[Dict[str, Any]], sma_portfolios: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Combine portfolios from EMA and SMA strategies.

    Args:
        ema_portfolios (List[Dict[str, Any]]): List of EMA strategy portfolios
        sma_portfolios (List[Dict[str, Any]]): List of SMA strategy portfolios

    Returns:
        List[Dict[str, Any]]: Combined list of portfolios with all required columns
    """
    # Ensure all required columns are present in both sets of portfolios
    required_columns = ["Short Window", "Long Window", "Strategy Type"]

    for portfolio in ema_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "EMA"
                else:
                    portfolio[col] = None

    for portfolio in sma_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "SMA"
                else:
                    portfolio[col] = None

    return ema_portfolios + sma_portfolios


def collect_filtered_portfolios_for_export(
    config: Dict[str, Any], strategy_types: List[str], log: Callable
) -> List[Dict[str, Any]]:
    """
    Collect filtered portfolios data (multiple metric types per configuration)
    from portfolios_filtered CSV files for best portfolios export.

    This function reads the portfolios_filtered CSV files that contain multiple
    metric types (Most, Least, Mean, Median) per unique strategy configuration,
    which is what should be used for portfolios_best aggregation.

    Args:
        config: Configuration dictionary
        strategy_types: List of strategy types to collect (e.g., ["SMA", "EMA"])
        log: Logging function

    Returns:
        List of portfolio dictionaries with Metric Type column containing
        multiple metric types per strategy configuration
    """
    from pathlib import Path

    import polars as pl

    all_portfolios = []

    try:
        # Get the ticker(s) from config
        ticker_config = config.get("TICKER", "")
        if not ticker_config:
            log("No ticker found in config for filtered portfolio collection", "error")
            return []

        # Handle both single ticker (string) and multiple tickers (list)
        if isinstance(ticker_config, list):
            tickers = ticker_config
        else:
            tickers = [ticker_config]

        # Get the base directory for CSV files
        base_dir = config.get("BASE_DIR", "/Users/colemorton/Projects/trading")
        csv_base = Path(base_dir) / "csv"

        # Determine the timeframe suffix
        timeframe = "H" if config.get("USE_HOURLY", False) else "D"

        # Process each ticker
        for ticker in tickers:
            for strategy_type in strategy_types:
                # Construct the path to the filtered CSV file
                # portfolios_filtered files contain multiple metric types per
                # configuration
                filtered_file = (
                    csv_base
                    / "portfolios_filtered"
                    / f"{ticker}_{timeframe}_{strategy_type}.csv"
                )

                # Also check in date-based subdirectories (most recent first)
                portfolios_filtered_dir = csv_base / "portfolios_filtered"
                date_dirs = sorted(
                    [
                        d
                        for d in portfolios_filtered_dir.iterdir()
                        if d.is_dir() and d.name.isdigit()
                    ],
                    reverse=True,
                )

                # Try root directory first
                if not filtered_file.exists():
                    # Try date directories
                    for date_dir in date_dirs:
                        date_filtered_file = (
                            date_dir / f"{ticker}_{timeframe}_{strategy_type}.csv"
                        )
                        if date_filtered_file.exists():
                            filtered_file = date_filtered_file
                            log(
                                f"Found filtered file for {ticker} in date directory: {date_dir.name}"
                            )
                            break

                if not filtered_file.exists():
                    log(
                        f"Filtered portfolios file not found: {ticker}_{timeframe}_{strategy_type}.csv",
                        "warning",
                    )
                    continue

                try:
                    # Read the filtered CSV file
                    log(f"Reading filtered portfolios from: {filtered_file}")
                    df = pl.read_csv(str(filtered_file))

                    if len(df) == 0:
                        log(
                            f"Empty filtered portfolios file: {filtered_file}",
                            "warning",
                        )
                        continue

                    # Convert to dictionaries
                    portfolios_data = df.to_dicts()
                    log(
                        f"Found {len(portfolios_data)} filtered portfolios from {ticker} {strategy_type}"
                    )

                    # Verify the data has Metric Type column
                    if len(portfolios_data) > 0:
                        first_portfolio = portfolios_data[0]
                        if "Metric Type" in first_portfolio:
                            log(
                                f"Confirmed Metric Type column present in {ticker} {strategy_type} data"
                            )
                            log(
                                f"Sample metric types: {[p.get('Metric Type', 'N/A') for p in portfolios_data[:3]]}"
                            )
                        else:
                            log(
                                f"WARNING: Metric Type column missing from {ticker} {strategy_type} filtered data",
                                "warning",
                            )

                    all_portfolios.extend(portfolios_data)

                except Exception as e:
                    log(
                        f"Error reading filtered portfolios file {filtered_file}: {str(e)}",
                        "error",
                    )
                    continue

        log(f"Collected total of {len(all_portfolios)} portfolios from filtered data")

        if len(all_portfolios) > 0:
            # Verify we have multiple metric types per configuration
            sample_config_groups = {}
            for portfolio in all_portfolios[:10]:  # Sample first 10
                ticker = portfolio.get("Ticker", "")
                strategy = portfolio.get("Strategy Type", "")
                short_window = portfolio.get("Short Window", "")
                long_window = portfolio.get("Long Window", "")
                metric_type = portfolio.get("Metric Type", "")

                config_key = f"{ticker},{strategy},{short_window},{long_window}"
                if config_key not in sample_config_groups:
                    sample_config_groups[config_key] = []
                sample_config_groups[config_key].append(metric_type)

            for config_key, metric_types in sample_config_groups.items():
                log(
                    f"Config {config_key}: {len(metric_types)} metric types - {', '.join(metric_types[:3])}{'...' if len(metric_types) > 3 else ''}"
                )

        return all_portfolios

    except Exception as e:
        log(f"Error collecting filtered portfolios: {str(e)}", "error")
        return []
