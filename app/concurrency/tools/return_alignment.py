"""Return Series Alignment for Portfolio Risk Calculation.

This module provides utilities for aligning return series across multiple trading strategies
to enable accurate covariance matrix calculation for portfolio risk metrics. Follows the
fail-fast approach with meaningful exceptions instead of fallback mechanisms.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import polars as pl

from app.tools.error_context import error_context
from app.tools.error_decorators import handle_errors
from app.tools.exceptions import DataAlignmentError, RiskCalculationError

from .data_alignment import find_common_dates, prepare_dataframe


@handle_errors(
    "Return series alignment validation",
    {
        ValueError: DataAlignmentError,
        KeyError: DataAlignmentError,
        Exception: RiskCalculationError,
    },
)
def validate_return_series_data(
    portfolios: List[Dict[str, Any]], log: Callable[[str, str], None]
) -> None:
    """Validate portfolio data for return series alignment.

    Args:
        portfolios: List of portfolio dictionaries with strategy data
        log: Logging function

    Raises:
        DataAlignmentError: If validation fails
    """
    if not portfolios:
        raise DataAlignmentError("No portfolios provided for return series alignment")

    required_fields = ["ticker", "strategy_type", "period"]
    missing_fields = []

    for i, portfolio in enumerate(portfolios):
        for field in required_fields:
            if field not in portfolio:
                missing_fields.append(f"Portfolio {i}: missing {field}")

    if missing_fields:
        error_details = "; ".join(missing_fields)
        raise DataAlignmentError(f"Portfolio validation failed: {error_details}")

    log(f"Validated {len(portfolios)} portfolios for return series alignment", "info")


@handle_errors(
    "Return series calculation",
    {
        ValueError: DataAlignmentError,
        KeyError: DataAlignmentError,
        Exception: RiskCalculationError,
    },
)
def calculate_return_series(
    df: pl.DataFrame, log: Callable[[str, str], None]
) -> pl.DataFrame:
    """Calculate return series from position data.

    Args:
        df: DataFrame with Date, Close, and Position columns
        log: Logging function

    Returns:
        DataFrame with Date and Returns columns

    Raises:
        DataAlignmentError: If calculation fails due to invalid data
    """
    required_columns = ["Date", "Close", "Position"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise DataAlignmentError(
            f"Missing required columns for return calculation: {missing_columns}"
        )

    if len(df) < 2:
        raise DataAlignmentError(
            f"Insufficient data for return calculation: {len(df)} rows (minimum 2 required)"
        )

    try:
        # Calculate price returns
        df_with_returns = df.with_columns(
            [(pl.col("Close").pct_change().fill_null(0)).alias("price_return")]
        )

        # Calculate strategy returns (price return * position)
        df_with_returns = df_with_returns.with_columns(
            [(pl.col("price_return") * pl.col("Position")).alias("strategy_return")]
        )

        # Ensure Date column is in consistent format (nanoseconds)
        df_with_returns = df_with_returns.with_columns(
            [pl.col("Date").cast(pl.Datetime("ns"))]
        )

        # Select relevant columns and remove first row (NaN return)
        result = df_with_returns.select(["Date", "strategy_return"]).slice(1)

        if len(result) == 0:
            raise DataAlignmentError("No valid returns calculated after processing")

        log(f"Calculated {len(result)} return observations", "info")
        return result

    except Exception as e:
        raise DataAlignmentError(f"Return series calculation failed: {str(e)}")


@handle_errors(
    "Return series alignment",
    {
        ValueError: DataAlignmentError,
        KeyError: DataAlignmentError,
        Exception: RiskCalculationError,
    },
)
def align_return_series(
    portfolio_returns: List[Tuple[str, pl.DataFrame]],
    log: Callable[[str, str], None],
    min_observations: int = 30,
) -> Tuple[pl.DataFrame, List[str]]:
    """Align return series across multiple strategies to common time periods.

    Args:
        portfolio_returns: List of (strategy_id, returns_df) tuples
        log: Logging function
        min_observations: Minimum number of observations required

    Returns:
        Tuple of (aligned_returns_matrix, strategy_names)

    Raises:
        DataAlignmentError: If alignment fails or insufficient data
    """
    if len(portfolio_returns) < 2:
        raise DataAlignmentError(
            f"Need at least 2 strategies for alignment, got {len(portfolio_returns)}"
        )

    strategy_names = [strategy_id for strategy_id, _ in portfolio_returns]
    return_dfs = [returns_df for _, returns_df in portfolio_returns]

    # Find common dates across all return series
    with error_context(
        "Finding common dates for return alignment",
        log,
        {Exception: DataAlignmentError},
        reraise=True,
    ):
        common_dates = find_common_dates(return_dfs, log)

        if len(common_dates) < min_observations:
            raise DataAlignmentError(
                f"Insufficient common observations: {len(common_dates)} < {min_observations} required"
            )

    # Align all return series to common dates
    aligned_returns = []
    for strategy_id, returns_df in portfolio_returns:
        with error_context(
            f"Aligning returns for {strategy_id}",
            log,
            {Exception: DataAlignmentError},
            reraise=True,
        ):
            aligned = returns_df.join(common_dates, on="Date", how="inner")

            if len(aligned) != len(common_dates):
                raise DataAlignmentError(
                    f"Alignment failed for {strategy_id}: expected {len(common_dates)} rows, got {len(aligned)}"
                )

            # Rename the column to be unique for this strategy
            aligned_return_col = aligned.select("strategy_return").rename(
                {"strategy_return": strategy_id}
            )
            aligned_returns.append(aligned_return_col)

    # Combine into matrix format
    try:
        returns_matrix = pl.concat(aligned_returns, how="horizontal")

        # Add date column back
        returns_matrix = returns_matrix.with_columns(common_dates.select("Date"))
        returns_matrix = returns_matrix.select(["Date"] + strategy_names)

        log(
            f"Successfully aligned {len(strategy_names)} return series with {len(returns_matrix)} observations",
            "info",
        )
        return returns_matrix, strategy_names

    except Exception as e:
        raise DataAlignmentError(f"Failed to create aligned returns matrix: {str(e)}")


@handle_errors(
    "Return matrix validation",
    {ValueError: DataAlignmentError, Exception: RiskCalculationError},
)
def validate_return_matrix(
    returns_matrix: pl.DataFrame,
    strategy_names: List[str],
    log: Callable[[str, str], None],
) -> None:
    """Validate aligned return matrix for quality and completeness.

    Args:
        returns_matrix: Aligned returns matrix
        strategy_names: List of strategy names
        log: Logging function

    Raises:
        DataAlignmentError: If validation fails
    """
    # Check matrix dimensions
    expected_cols = len(strategy_names) + 1  # +1 for Date column
    if len(returns_matrix.columns) != expected_cols:
        raise DataAlignmentError(
            f"Return matrix column count mismatch: expected {expected_cols}, got {len(returns_matrix.columns)}"
        )

    # Check for missing values
    null_counts = returns_matrix.select(strategy_names).null_count()
    total_nulls = sum(null_counts.row(0))

    if total_nulls > 0:
        raise DataAlignmentError(f"Return matrix contains {total_nulls} null values")

    # Check for infinite values
    for strategy in strategy_names:
        strategy_returns = returns_matrix.select(strategy).to_numpy().flatten()

        if np.any(np.isinf(strategy_returns)):
            raise DataAlignmentError(
                f"Strategy {strategy} contains infinite return values"
            )

        if np.any(np.isnan(strategy_returns)):
            raise DataAlignmentError(f"Strategy {strategy} contains NaN return values")

    # Check return variance (must be > 0 for valid covariance calculation)
    for strategy in strategy_names:
        strategy_returns = returns_matrix.select(strategy).to_numpy().flatten()
        variance = np.var(strategy_returns, ddof=1)

        if variance <= 0:
            raise DataAlignmentError(
                f"Strategy {strategy} has zero or negative variance: {variance}"
            )

    log(f"Return matrix validation passed for {len(strategy_names)} strategies", "info")


@handle_errors(
    "Portfolio return alignment",
    {
        ValueError: DataAlignmentError,
        KeyError: DataAlignmentError,
        Exception: RiskCalculationError,
    },
)
def align_portfolio_returns(
    portfolios: List[Dict[str, Any]],
    log: Callable[[str, str], None],
    min_observations: int = 30,
) -> Tuple[pl.DataFrame, List[str]]:
    """Main function to align return series across portfolio strategies.

    Args:
        portfolios: List of portfolio dictionaries with strategy data
        log: Logging function
        min_observations: Minimum number of observations required

    Returns:
        Tuple of (aligned_returns_matrix, strategy_names)

    Raises:
        DataAlignmentError: If alignment process fails
        RiskCalculationError: If general calculation error occurs
    """
    # Validate input data
    validate_return_series_data(portfolios, log)

    # Calculate return series for each strategy
    portfolio_returns = []

    for portfolio in portfolios:
        strategy_id = (
            f"{portfolio['ticker']}_{portfolio['strategy_type']}_{portfolio['period']}"
        )

        with error_context(
            f"Processing returns for {strategy_id}",
            log,
            {Exception: DataAlignmentError},
            reraise=True,
        ):
            # Load strategy data - assuming portfolio contains path or data reference
            if "data_path" in portfolio:
                # Load from CSV file
                try:
                    df = pl.read_csv(portfolio["data_path"])
                except Exception as e:
                    raise DataAlignmentError(
                        f"Failed to load data from {portfolio['data_path']}: {str(e)}"
                    )
            elif "data" in portfolio:
                # Use provided DataFrame
                df = portfolio["data"]
            else:
                raise DataAlignmentError(f"No data source found for {strategy_id}")

            # Calculate returns
            returns_df = calculate_return_series(df, log)
            portfolio_returns.append((strategy_id, returns_df))

    # Align all return series
    returns_matrix, strategy_names = align_return_series(
        portfolio_returns, log, min_observations
    )

    # Validate final result
    validate_return_matrix(returns_matrix, strategy_names, log)

    log(f"Portfolio return alignment completed successfully", "info")
    return returns_matrix, strategy_names


def get_alignment_summary(
    returns_matrix: pl.DataFrame,
    strategy_names: List[str],
    log: Callable[[str, str], None],
) -> Dict[str, Any]:
    """Generate summary statistics for aligned return matrix.

    Args:
        returns_matrix: Aligned returns matrix
        strategy_names: List of strategy names
        log: Logging function

    Returns:
        Dictionary with alignment summary statistics
    """
    summary = {
        "num_strategies": len(strategy_names),
        "num_observations": len(returns_matrix),
        "date_range": {
            "start": returns_matrix["Date"].min(),
            "end": returns_matrix["Date"].max(),
        },
        "strategy_statistics": {},
    }

    for strategy in strategy_names:
        strategy_returns = returns_matrix.select(strategy).to_numpy().flatten()
        summary["strategy_statistics"][strategy] = {
            "mean_return": float(np.mean(strategy_returns)),
            "std_return": float(np.std(strategy_returns, ddof=1)),
            "min_return": float(np.min(strategy_returns)),
            "max_return": float(np.max(strategy_returns)),
        }

    log(f"Generated alignment summary for {len(strategy_names)} strategies", "info")
    return summary
