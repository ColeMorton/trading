"""Data alignment utilities for concurrency analysis."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pandas as pd
import polars as pl

from .validation import PortfolioMetricsValidator, ValidationSummary


def resample_hourly_to_daily(
    data: pl.DataFrame, log: Callable[[str, str], None],
) -> pl.DataFrame:
    """Resample hourly data to daily timeframe.

    Args:
        data (pl.DataFrame): Hourly dataframe with Date column
        log (Callable[[str, str], None]): Logging function

    Returns:
        pl.DataFrame: Daily resampled dataframe
    """
    try:
        log("Resampling hourly data to daily timeframe", "info")
        resampled = data.group_by_dynamic("Date", every="1d", closed="right").agg(
            [
                pl.col("Open").first().alias("Open"),
                pl.col("High").max().alias("High"),
                pl.col("Low").min().alias("Low"),
                pl.col("Close").last().alias("Close"),
                pl.col("Volume").sum().alias("Volume"),
                pl.col("Position").last().alias("Position"),
            ],
        )
        log("Hourly data successfully resampled to daily", "info")
        return resampled
    except Exception as e:
        log(f"Error resampling hourly data: {e!s}", "error")
        raise


def prepare_dataframe(
    df: pl.DataFrame, is_hourly: bool, log: Callable[[str, str], None],
) -> pl.DataFrame:
    """Prepare dataframe by resampling if needed and standardizing dates.

    Args:
        df (pl.DataFrame): Input dataframe
        is_hourly (bool): Whether dataframe is hourly
        log (Callable[[str, str], None]): Logging function

    Returns:
        pl.DataFrame: Prepared dataframe

    Raises:
        ValueError: If Date column is missing
    """
    try:
        log(f"Preparing dataframe (hourly: {is_hourly})", "info")

        if "Date" not in df.columns:
            log("DataFrame missing Date column", "error")
            msg = "DataFrame missing Date column"
            raise ValueError(msg)

        # Handle different Date column types
        date_dtype = df.schema["Date"]

        if date_dtype == pl.String:
            log("Converting Date column from string to datetime", "info")
            df = df.with_columns(
                [pl.col("Date").str.to_datetime().cast(pl.Datetime("ns")).alias("Date")],
            )
        elif date_dtype == pl.Date:
            log("Converting Date column from date to datetime", "info")
            df = df.with_columns([pl.col("Date").cast(pl.Datetime("ns")).alias("Date")])
        elif isinstance(date_dtype, pl.Datetime):
            log("Date column is already datetime, applying timezone operations", "info")
            # Only apply timezone operations to datetime columns
            df = df.with_columns(
                [
                    pl.col("Date")
                    .dt.replace_time_zone(None)
                    .dt.truncate("1d")
                    .cast(pl.Datetime("ns")),
                ],
            )
        else:
            log("Converting Date column to datetime", "info")
            df = df.with_columns([pl.col("Date").cast(pl.Datetime("ns")).alias("Date")])
        log("Dates standardized", "info")

        if is_hourly:
            df = resample_hourly_to_daily(df, log)

        log("DataFrame preparation completed", "info")
        return df

    except Exception as e:
        log(f"Error preparing dataframe: {e!s}", "error")
        raise


def find_common_dates(
    dfs: list[pl.DataFrame], log: Callable[[str, str], None],
) -> pl.DataFrame:
    """Find dates common to all dataframes.

    Args:
        dfs (List[pl.DataFrame]): List of dataframes
        log (Callable[[str, str], None]): Logging function

    Returns:
        pl.DataFrame: DataFrame with common dates
    """
    try:
        log("Finding common dates across dataframes", "info")

        min_date = max(df["Date"].min() for df in dfs)
        max_date = min(df["Date"].max() for df in dfs)
        log(f"Date range: {min_date} to {max_date}", "info")

        filtered_dfs = [
            df.filter((pl.col("Date") >= min_date) & (pl.col("Date") <= max_date))
            for df in dfs
        ]

        common_dates = set(filtered_dfs[0]["Date"].to_list())
        for df in filtered_dfs[1:]:
            common_dates.intersection_update(df["Date"].to_list())

        result = pl.DataFrame(
            {"Date": pl.Series(sorted(common_dates), dtype=pl.Datetime("ns"))},
        )

        log(f"Found {len(result)} common dates", "info")
        return result

    except Exception as e:
        log(f"Error finding common dates: {e!s}", "error")
        raise


def align_data(
    data_1: pl.DataFrame,
    data_2: pl.DataFrame,
    log: Callable[[str, str], None],
    is_hourly_1: bool = False,
    is_hourly_2: bool = False,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Align two dataframes by date range and timeframe.

    Args:
        data_1 (pl.DataFrame): First dataframe with Date column
        data_2 (pl.DataFrame): Second dataframe with Date column
        log (Callable[[str, str], None]): Logging function
        is_hourly_1 (bool): Whether first dataframe is hourly
        is_hourly_2 (bool): Whether second dataframe is hourly

    Returns:
        Tuple[pl.DataFrame, pl.DataFrame]: Tuple containing aligned dataframes

    Raises:
        ValueError: If aligned dataframes have different shapes
    """
    try:
        log("Starting alignment of two dataframes", "info")
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]

        # Prepare dataframes
        log("Preparing first dataframe", "info")
        df1 = prepare_dataframe(data_1, is_hourly_1, log)
        log("Preparing second dataframe", "info")
        df2 = prepare_dataframe(data_2, is_hourly_2, log)

        # Find common dates and align
        common_dates = find_common_dates([df1, df2], log)
        aligned_1 = df1.join(common_dates, on="Date", how="inner").select(required_cols)
        aligned_2 = df2.join(common_dates, on="Date", how="inner").select(required_cols)

        if aligned_1.shape != aligned_2.shape:
            log(
                f"Alignment failed: shapes differ {aligned_1.shape} vs {aligned_2.shape}",
                "error",
            )
            msg = f"Aligned dataframes have different shapes: {aligned_1.shape} vs {aligned_2.shape}"
            raise ValueError(
                msg,
            )

        log(f"Successfully aligned dataframes with shape {aligned_1.shape}", "info")
        return aligned_1, aligned_2

    except Exception as e:
        log(f"Error aligning data: {e!s}", "error")
        raise


def align_multiple_data(
    data_list: list[pl.DataFrame],
    hourly_flags: list[bool],
    log: Callable[[str, str], None],
) -> list[pl.DataFrame]:
    """Align multiple dataframes by date range and timeframe.

    Args:
        data_list (List[pl.DataFrame]): List of dataframes with Date column
        hourly_flags (List[bool]): List indicating which dataframes are hourly
        log (Callable[[str, str], None]): Logging function

    Returns:
        List[pl.DataFrame]: List of aligned dataframes with matching date ranges

    Raises:
        ValueError: If inputs are invalid or alignment fails
    """
    try:
        log(f"Starting alignment of {len(data_list)} dataframes", "info")

        if len(data_list) != len(hourly_flags):
            log(
                "Mismatched inputs: different number of dataframes and hourly flags",
                "error",
            )
            msg = "Number of dataframes must match number of hourly flags"
            raise ValueError(msg)

        if len(data_list) < 2:
            log("Insufficient input: need at least two dataframes", "error")
            msg = "At least two dataframes are required for alignment"
            raise ValueError(msg)

        # Prepare all dataframes
        log("Preparing dataframes", "info")
        prepared_dfs = [
            prepare_dataframe(df, is_hourly, log)
            for df, is_hourly in zip(data_list, hourly_flags, strict=False)
        ]

        # Find common dates and align all dataframes
        common_dates = find_common_dates(prepared_dfs, log)
        required_cols = ["Date", "Open", "High", "Low", "Close", "Volume", "Position"]

        log("Aligning dataframes to common dates", "info")
        aligned_dfs = []
        for i, df in enumerate(prepared_dfs, 1):
            aligned = df.join(common_dates, on="Date", how="inner").select(
                required_cols,
            )
            aligned = aligned.with_columns(
                [
                    pl.col("Position").fill_null(0),
                    pl.col("Volume").fill_null(0),
                    pl.col(["Open", "High", "Low", "Close"]).forward_fill(),
                ],
            )
            aligned_dfs.append(aligned)
            log(f"Dataframe {i}/{len(prepared_dfs)} aligned", "info")

        # Verify alignment
        shapes = [df.shape for df in aligned_dfs]
        if len(set(shapes)) > 1:
            log(f"Alignment verification failed: inconsistent shapes {shapes}", "error")
            msg = f"Aligned dataframes have different shapes: {shapes}"
            raise ValueError(msg)

        log(
            f"Successfully aligned {len(aligned_dfs)} dataframes with shape {shapes[0]}",
            "info",
        )
        return aligned_dfs

    except Exception as e:
        log(f"Error during multiple data alignment: {e!s}", "error")
        raise


def validate_aligned_data_quality(
    aligned_data: list[pl.DataFrame],
    csv_path: str | None | None = None,
    json_metrics: dict[str, Any] | None = None,
    log: Callable[[str, str], None] | None = None,
) -> ValidationSummary:
    """
    Validate the quality of aligned data against source data.

    This function performs validation checks to ensure that data alignment
    hasn't introduced calculation errors or data quality issues.

    Args:
        aligned_data: List of aligned DataFrames
        csv_path: Optional path to CSV backtest data for validation
        json_metrics: Optional JSON metrics for cross-validation
        log: Optional logging function

    Returns:
        ValidationSummary with validation results
    """
    if log is None:
        from app.tools.setup_logging import setup_logging

        log, _, _, _ = setup_logging(
            "data_alignment_validator", Path("./logs"), "alignment_validation.log",
        )

    log("Validating aligned data quality", "info")

    # Create validator
    validator = PortfolioMetricsValidator(log)

    try:
        # Basic alignment checks
        if len(aligned_data) < 2:
            log("Warning: Less than 2 aligned dataframes for validation", "warning")
            return ValidationSummary(0, 0, 0, 0, 0, [])

        # Check 1: All dataframes have same length
        lengths = [len(df) for df in aligned_data]
        all_same_length = len(set(lengths)) == 1

        if not all_same_length:
            log(
                f"Alignment error: DataFrames have different lengths: {lengths}",
                "error",
            )

        # Check 2: All dataframes have same date range
        date_ranges = []
        for i, df in enumerate(aligned_data):
            if "Date" in df.columns:
                min_date = df["Date"].min()
                max_date = df["Date"].max()
                date_ranges.append((min_date, max_date))
            else:
                log(f"DataFrame {i} missing Date column", "error")

        all_same_dates = len(set(date_ranges)) == 1 if date_ranges else False

        # Check 3: No missing position data
        position_completeness = []
        for i, df in enumerate(aligned_data):
            if "Position" in df.columns:
                non_null_positions = df["Position"].null_count() == 0
                position_completeness.append(non_null_positions)
            else:
                log(f"DataFrame {i} missing Position column", "error")
                position_completeness.append(False)

        all_positions_complete = (
            all(position_completeness) if position_completeness else False
        )

        # Check 4: Reasonable signal counts
        signal_counts = []
        for i, df in enumerate(aligned_data):
            if "Position" in df.columns:
                # Count position changes as signals
                df_pd = df.to_pandas()
                if len(df_pd) > 1:
                    df_pd["signal"] = df_pd["Position"].diff().fillna(0)
                    signal_count = (df_pd["signal"] != 0).sum()
                    signal_counts.append(signal_count)

                    # Check for reasonable signal frequency (not more than 50% of days)
                    signal_frequency = signal_count / len(df_pd)
                    if signal_frequency > 0.5:
                        log(
                            f"DataFrame {i} has very high signal frequency: {signal_frequency:.2%}",
                            "warning",
                        )

        # Cross-validation with CSV/JSON if available
        cross_validation_passed = True
        if csv_path and json_metrics:
            try:
                csv_data = pd.read_csv(csv_path)
                validation_summary = validator.validate_all(csv_data, json_metrics)
                cross_validation_passed = validation_summary.critical_failures == 0
                log(
                    f"Cross-validation completed: {validation_summary.success_rate:.1%} success rate",
                    "info",
                )
            except Exception as e:
                log(f"Cross-validation failed: {e!s}", "warning")
                cross_validation_passed = False

        # Generate summary
        total_checks = 4 + (1 if csv_path and json_metrics else 0)
        passed_checks = sum(
            [
                all_same_length,
                all_same_dates,
                all_positions_complete,
                len(signal_counts) > 0,  # At least some signals found
                cross_validation_passed,
            ],
        )

        log(
            f"Data alignment validation: {passed_checks}/{total_checks} checks passed",
            "info",
        )

        return ValidationSummary(
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            critical_failures=0 if all_same_length and all_same_dates else 1,
            warning_failures=0,
            results=[],  # Detailed results would be added here in full implementation
        )

    except Exception as e:
        log(f"Error during data alignment validation: {e!s}", "error")
        return ValidationSummary(0, 0, 1, 1, 0, [])


def align_with_validation(
    data_list: list[pl.DataFrame],
    hourly_flags: list[bool],
    csv_path: str | None | None = None,
    json_metrics: dict[str, Any] | None = None,
    log: Callable[[str, str], None] | None = None,
) -> tuple[list[pl.DataFrame], ValidationSummary]:
    """
    Align multiple dataframes with built-in validation.

    This function combines data alignment with validation to ensure
    the aligned data maintains quality and consistency.

    Args:
        data_list: List of dataframes to align
        hourly_flags: List indicating which dataframes are hourly
        csv_path: Optional path to CSV backtest data for validation
        json_metrics: Optional JSON metrics for cross-validation
        log: Optional logging function

    Returns:
        Tuple of (aligned_dataframes, validation_summary)
    """
    if log is None:
        from app.tools.setup_logging import setup_logging

        log, _, _, _ = setup_logging(
            "align_with_validation", Path("./logs"), "alignment.log",
        )

    log("Starting data alignment with validation", "info")

    try:
        # Perform standard alignment
        aligned_data = align_multiple_data(data_list, hourly_flags, log)

        # Validate the aligned data
        validation_summary = validate_aligned_data_quality(
            aligned_data, csv_path, json_metrics, log,
        )

        if validation_summary.critical_failures > 0:
            log("Critical failures detected in aligned data", "error")
        elif validation_summary.failed_checks > 0:
            log(
                f"Data alignment completed with {validation_summary.failed_checks} validation warnings",
                "warning",
            )
        else:
            log(
                "Data alignment completed successfully with all validations passed",
                "info",
            )

        return aligned_data, validation_summary

    except Exception as e:
        log(f"Error during alignment with validation: {e!s}", "error")
        raise
