"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files for the
MACD cross strategy using the centralized export functionality.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import polars as pl

from app.tools.export_csv import ExportConfig, export_csv


class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""


VALID_EXPORT_TYPES = {
    "portfolios",
    "portfolios_scanner",
    "portfolios_filtered",
    "portfolios_best",  # Added portfolios_best for consistency with ma_cross
}


def _fix_precision(df: pl.DataFrame) -> pl.DataFrame:
    """Fix precision for numeric columns.

    Args:
        df (pl.DataFrame): DataFrame to process

    Returns:
        pl.DataFrame: DataFrame with fixed precision
    """
    # Round window parameters to integers
    for col in ["Short Window", "Long Window", "Signal Window"]:
        if col in df.columns:
            df = df.with_columns(pl.col(col).cast(pl.Int32).alias(col))
    return df


def sort_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame], config: Dict
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Sort portfolios using consistent logic across the application.

    Args:
        portfolios: Either a list of portfolio dictionaries or a Polars DataFrame
        config: Configuration dictionary containing sorting preferences

    Returns:
        Sorted portfolios in the same format as input (list or DataFrame)

    Note:
        Uses config['SORT_BY'] to determine sort column, defaults to 'Total Return [%]'
        Uses config['SORT_ASC'] to determine sort order, defaults to False (descending)
    """
    # Convert to DataFrame if necessary
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios

    # Sort using consistent logic
    sort_by = config.get("SORT_BY", "Total Return [%]")
    sort_asc = config.get("SORT_ASC", False)
    descending = not sort_asc  # If sort_asc is True, descending should be False

    sorted_df = df.sort(sort_by, descending=descending)

    # Return in original format
    return sorted_df.to_dicts() if input_is_list else sorted_df


def _reorder_columns(
    df: pl.DataFrame, export_type: str, config: ExportConfig = None
) -> pl.DataFrame:
    """Reorder columns based on export type.

    Args:
        df (pl.DataFrame): DataFrame to reorder
        export_type (str): Type of export
        config (ExportConfig, optional): Configuration dictionary

    Returns:
        pl.DataFrame: DataFrame with reordered columns
    """
    # Fix precision first
    df = _fix_precision(df)

    # Add required columns for consistency with ma_cross/strategies exports

    # Add Ticker column if missing
    if "Ticker" not in df.columns and config and "TICKER" in config:
        ticker = config["TICKER"]
        if isinstance(ticker, str):
            df = df.with_columns(pl.lit(ticker).alias("Ticker"))

    # Add Strategy Type column if missing
    if "Strategy Type" not in df.columns:
        df = df.with_columns(pl.lit("MACD").alias("Strategy Type"))

    # Add Signal Entry and Signal Exit columns if missing
    if "Signal Entry" not in df.columns:
        df = df.with_columns(pl.lit(False).alias("Signal Entry"))
    if "Signal Exit" not in df.columns:
        df = df.with_columns(pl.lit(False).alias("Signal Exit"))

    # Add Total Open Trades if missing
    if "Total Open Trades" not in df.columns:
        df = df.with_columns(pl.lit(0).alias("Total Open Trades"))

    if export_type in [
        "portfolios_best",
        "portfolios",
        "",
    ]:  # Include empty string for strategies export
        # Define standard column order to match ma_cross/strategies exports
        ordered_cols = [
            "Ticker",
            "Strategy Type",
            "Short Window",
            "Long Window",
            "Signal Window",
            "Signal Entry",
            "Signal Exit",
            "Total Open Trades",
            "Total Trades",
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Beats BNH [%]",
            "Avg Trade Duration",
            "Trades Per Day",
            "Trades per Month",
            "Signals per Month",
            "Expectancy per Month",
            "Start",
            "End",
            "Period",
            "Start Value",
            "End Value",
            "Total Return [%]",
            "Benchmark Return [%]",
            "Max Gross Exposure [%]",
            "Total Fees Paid",
            "Max Drawdown [%]",
            "Max Drawdown Duration",
            "Total Closed Trades",
            "Open Trade PnL",
            "Best Trade [%]",
            "Worst Trade [%]",
            "Avg Winning Trade [%]",
            "Avg Losing Trade [%]",
            "Avg Winning Trade Duration",
            "Avg Losing Trade Duration",
            "Expectancy",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Omega Ratio",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Signal Count",
            "Position Count",
            "Total Period",
        ]

        # Select only columns that exist in the DataFrame
        existing_cols = [col for col in ordered_cols if col in df.columns]

        # Add any remaining columns that weren't in our ordered list
        remaining_cols = [col for col in df.columns if col not in ordered_cols]
        existing_cols.extend(remaining_cols)

        return df.select(existing_cols)

    elif export_type == "portfolios_filtered":
        # For filtered portfolios, we need to keep Metric Type as the first column
        # but otherwise use the same column order as other export types

        # Start with Metric Type if it exists
        ordered_cols = []
        if "Metric Type" in df.columns:
            ordered_cols.append("Metric Type")

        # Add the standard columns in the correct order (except Metric Type)
        standard_cols = [
            "Ticker",
            "Strategy Type",
            "Short Window",
            "Long Window",
            "Signal Window",
            "Signal Entry",
            "Signal Exit",
            "Total Open Trades",
            "Total Trades",
            "Score",
            "Win Rate [%]",
            "Profit Factor",
            "Expectancy per Trade",
            "Sortino Ratio",
            "Beats BNH [%]",
            "Avg Trade Duration",
            "Trades Per Day",
            "Trades per Month",
            "Signals per Month",
            "Expectancy per Month",
            "Start",
            "End",
            "Period",
            "Start Value",
            "End Value",
            "Total Return [%]",
            "Benchmark Return [%]",
            "Max Gross Exposure [%]",
            "Total Fees Paid",
            "Max Drawdown [%]",
            "Max Drawdown Duration",
            "Total Closed Trades",
            "Open Trade PnL",
            "Best Trade [%]",
            "Worst Trade [%]",
            "Avg Winning Trade [%]",
            "Avg Losing Trade [%]",
            "Avg Winning Trade Duration",
            "Avg Losing Trade Duration",
            "Expectancy",
            "Sharpe Ratio",
            "Calmar Ratio",
            "Omega Ratio",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Signal Count",
            "Position Count",
            "Total Period",
        ]

        # Add standard columns that exist in the DataFrame
        for col in standard_cols:
            if (
                col in df.columns and col != "Metric Type"
            ):  # Skip Metric Type as it's already added
                ordered_cols.append(col)

        # Add any remaining columns that weren't in our ordered list
        remaining_cols = [
            col
            for col in df.columns
            if col not in ordered_cols and col != "Metric Type"
        ]
        ordered_cols.extend(remaining_cols)

        return df.select(ordered_cols)

    return df


def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] = None,
    log: Optional[Callable] = None,
    feature_dir: str = "",  # Added feature_dir parameter for consistency with ma_cross
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered)
        csv_filename (Optional[str]): Optional custom filename for the CSV
        log (Optional[Callable]): Optional logging function

    Returns:
        Tuple[pl.DataFrame, bool]: (DataFrame of exported data, success status)

    Raises:
        PortfolioExportError: If export fails or invalid export type provided
        ValueError: If portfolios list is empty
    """
    if not portfolios:
        if log:
            log("No portfolios to export", "warning")
        raise ValueError("Cannot export empty portfolio list")

    # Allow empty string for direct export to strategies directory
    if export_type != "" and export_type not in VALID_EXPORT_TYPES:
        error_msg = f"Invalid export type: {export_type}. Must be one of: {', '.join(VALID_EXPORT_TYPES)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg)

    if log:
        log(f"Exporting {len(portfolios)} portfolios as {export_type}...", "info")

    try:
        # Convert to DataFrame
        df = pl.DataFrame(portfolios)

        # Sort portfolios if SORT_BY is specified in config
        if "SORT_BY" in config:
            log(
                f"Sorting portfolios by {config.get('SORT_BY')} in {'ascending' if config.get('SORT_ASC', False) else 'descending'} order",
                "info",
            )
            df = sort_portfolios(df, config)

        # Reorder columns
        df = _reorder_columns(df, export_type, config)

        # Determine feature1 (directory) based on export_type and feature_dir
        if feature_dir:
            # If feature_dir is provided, use it directly
            feature1 = feature_dir
        else:
            # Otherwise use the default logic
            if export_type == "portfolios_best":
                # For portfolios_best, export to csv/portfolios_best/
                feature1 = ""
            elif export_type in ["portfolios", "portfolios_scanner"]:
                # For portfolios and portfolios_scanner, export to csv/portfolios/ or csv/portfolios_scanner/
                feature1 = ""
            else:
                # For other types, export to csv/macd_next/[export_type]/
                feature1 = "macd_next"

        # Ensure config has STRATEGY_TYPE set to MACD and USE_MA set to True
        # This will add the _MACD suffix to the exported CSV filenames
        export_config = config.copy()
        export_config["STRATEGY_TYPE"] = "MACD"
        export_config["USE_MA"] = True

        # Export with correct directory structure
        return export_csv(
            data=df,
            feature1=feature1,
            config=export_config,
            feature2=export_type,
            filename=csv_filename,
            log=log,
        )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e


def export_best_portfolios(
    portfolios: List[Dict[str, Any]], config: Dict, log: callable
) -> bool:
    """Export the best portfolios to a CSV file.

    The portfolios are sorted by the metric specified in config['SORT_BY'],
    defaulting to 'Total Return [%]' if not specified.

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
        # Sort portfolios using centralized function
        log(
            f"Sorting portfolios by {config.get('SORT_BY', 'Total Return [%]')} in {'ascending' if config.get('SORT_ASC', False) else 'descending'} order",
            "info",
        )
        sorted_portfolios = sort_portfolios(portfolios, config)

        # Export to portfolios_best directory
        export_portfolios(
            portfolios=sorted_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log,
        )

        # Get sort parameters from config
        sort_by = config.get("SORT_BY", "Total Return [%]")
        sort_asc = config.get("SORT_ASC", False)

        log(
            f"Exported {len(sorted_portfolios)} portfolios sorted by {sort_by} in {'ascending' if sort_asc else 'descending'} order"
        )
        return True
    except Exception as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False
