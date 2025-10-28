"""
Data Processing Module.

This module provides optimized functions for data processing,
minimizing conversions between polars and pandas and implementing
efficient batch processing techniques.
"""

from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
import time
from typing import Any, TypeVar

import numpy as np
import pandas as pd
import polars as pl

from app.tools.error_handling import ErrorHandler
from app.tools.setup_logging import setup_logging


# Type variable for generic functions
T = TypeVar("T")


class DataProcessor:
    """Class for optimized data processing."""

    def __init__(self, log: Callable[[str, str], None] | None = None):
        """Initialize the DataProcessor class.

        Args:
            log: Optional logging function. If not provided, a default logger will be created.
        """
        if log is None:
            # Create a default logger if none provided
            try:
                self.log, _, _, _ = setup_logging(
                    "data_processor",
                    Path("./logs"),
                    "data_processor.log",
                )
            except Exception:
                # Fallback to a simple print-based logger if setup fails
                self.log = lambda msg, level="info": print(f"[{level.upper()}] {msg}")
        else:
            self.log = log

        # Create error handler
        self.error_handler = ErrorHandler(log)

        # Initialize cache for intermediate results
        self._cache: dict[str, Any] = {}

    def ensure_polars(self, df: pd.DataFrame | pl.DataFrame) -> pl.DataFrame:
        """Ensure a DataFrame is a polars DataFrame.

        Args:
            df: DataFrame to convert

        Returns:
            pl.DataFrame: Polars DataFrame
        """
        if isinstance(df, pd.DataFrame):
            self.log("Converting pandas DataFrame to polars", "debug")
            return pl.from_pandas(df)
        return df

    def ensure_pandas(self, df: pd.DataFrame | pl.DataFrame) -> pd.DataFrame:
        """Ensure a DataFrame is a pandas DataFrame.

        Args:
            df: DataFrame to convert

        Returns:
            pd.DataFrame: Pandas DataFrame
        """
        if isinstance(df, pl.DataFrame):
            self.log("Converting polars DataFrame to pandas", "debug")
            return df.to_pandas()
        return df

    def process_in_native_format(
        self,
        df: pd.DataFrame | pl.DataFrame,
        process_pandas: Callable[[pd.DataFrame], pd.DataFrame],
        process_polars: Callable[[pl.DataFrame], pl.DataFrame],
    ) -> pd.DataFrame | pl.DataFrame:
        """Process a DataFrame using the appropriate function for its type.

        This avoids unnecessary conversions between pandas and polars.

        Args:
            df: DataFrame to process
            process_pandas: Function to process pandas DataFrame
            process_polars: Function to process polars DataFrame

        Returns:
            Processed DataFrame of the same type as input
        """
        try:
            if isinstance(df, pd.DataFrame):
                self.log("Processing in pandas format", "debug")
                return process_pandas(df)
            if isinstance(df, pl.DataFrame):
                self.log("Processing in polars format", "debug")
                return process_polars(df)
            msg = f"Unsupported DataFrame type: {type(df)}"
            raise TypeError(msg)
        except Exception as e:
            self.log(f"Error in process_in_native_format: {e!s}", "error")
            # Return the original DataFrame on error
            return df

    def batch_process(
        self,
        dfs: list[pd.DataFrame | pl.DataFrame],
        process_func: Callable[
            [pd.DataFrame | pl.DataFrame],
            pd.DataFrame | pl.DataFrame,
        ],
        batch_size: int = 10,
        parallel: bool = False,
    ) -> list[pd.DataFrame | pl.DataFrame]:
        """Process a list of DataFrames in batches.

        Args:
            dfs: List of DataFrames to process
            process_func: Function to process each DataFrame
            batch_size: Number of DataFrames to process in each batch
            parallel: Whether to process batches in parallel

        Returns:
            List[Union[pd.DataFrame, pl.DataFrame]]: List of processed DataFrames
        """
        try:
            self.log(
                f"Batch processing {len(dfs)} DataFrames with batch size {batch_size}",
                "info",
            )

            # Process in batches
            results = []

            if parallel:
                # Import only when needed to avoid dependency issues
                try:
                    from concurrent.futures import ThreadPoolExecutor

                    # Process batches in parallel
                    with ThreadPoolExecutor() as executor:
                        # Submit batches
                        futures = []
                        for i in range(0, len(dfs), batch_size):
                            batch = dfs[i : i + batch_size]
                            futures.append(
                                executor.submit(
                                    self._process_batch,
                                    batch,
                                    process_func,
                                ),
                            )

                        # Collect results
                        for future in futures:
                            results.extend(future.result())
                except ImportError:
                    self.log(
                        "ThreadPoolExecutor not available, falling back to sequential processing",
                        "warning",
                    )
                    # Fall back to sequential processing
                    for i in range(0, len(dfs), batch_size):
                        batch = dfs[i : i + batch_size]
                        results.extend(self._process_batch(batch, process_func))
            else:
                # Process batches sequentially
                for i in range(0, len(dfs), batch_size):
                    batch = dfs[i : i + batch_size]
                    results.extend(self._process_batch(batch, process_func))

            return results
        except Exception as e:
            self.log(f"Error in batch_process: {e!s}", "error")
            # Return the original DataFrames on error
            return dfs

    def _process_batch(
        self,
        batch: list[pd.DataFrame | pl.DataFrame],
        process_func: Callable[
            [pd.DataFrame | pl.DataFrame],
            pd.DataFrame | pl.DataFrame,
        ],
    ) -> list[pd.DataFrame | pl.DataFrame]:
        """Process a batch of DataFrames.

        Args:
            batch: List of DataFrames to process
            process_func: Function to process each DataFrame

        Returns:
            List[Union[pd.DataFrame, pl.DataFrame]]: List of processed DataFrames
        """
        return [process_func(df) for df in batch]

    @lru_cache(maxsize=128)
    def cached_calculation(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Cache the result of a calculation function.

        Args:
            func: Function to cache
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            T: Result of the function
        """
        self.log(f"Cached calculation: {func.__name__}", "debug")
        return func(*args, **kwargs)

    def cache_intermediate_result(self, key: str, result: Any) -> None:
        """Cache an intermediate result for reuse.

        Args:
            key: Cache key
            result: Result to cache
        """
        self.log(f"Caching intermediate result with key: {key}", "debug")
        self._cache[key] = result

    def get_cached_result(self, key: str, default: T | None | None = None) -> T | None:
        """Get a cached intermediate result.

        Args:
            key: Cache key
            default: Default value to return if key not found

        Returns:
            Optional[T]: Cached result or default
        """
        if key in self._cache:
            self.log(f"Using cached result for key: {key}", "debug")
            return self._cache[key]
        return default

    def clear_cache(self) -> None:
        """Clear the cache of intermediate results."""
        self.log("Clearing cache", "debug")
        self._cache.clear()

    def optimize_dataframe(
        self,
        df: pd.DataFrame | pl.DataFrame,
        categorical_threshold: int = 50,
        date_columns: list[str] | None | None = None,
    ) -> pd.DataFrame | pl.DataFrame:
        """Optimize a DataFrame for memory usage.

        Args:
            df: DataFrame to optimize
            categorical_threshold: Maximum number of unique values for categorical conversion
            date_columns: List of column names to convert to datetime

        Returns:
            Union[pd.DataFrame, pl.DataFrame]: Optimized DataFrame
        """
        try:
            # Process based on DataFrame type
            return self.process_in_native_format(
                df,
                lambda pandas_df: self._optimize_pandas_dataframe(
                    pandas_df,
                    categorical_threshold,
                    date_columns,
                ),
                lambda polars_df: self._optimize_polars_dataframe(
                    polars_df,
                    categorical_threshold,
                    date_columns,
                ),
            )
        except Exception as e:
            self.log(f"Error optimizing DataFrame: {e!s}", "error")
            # Return the original DataFrame on error
            return df

    def _optimize_pandas_dataframe(
        self,
        df: pd.DataFrame,
        categorical_threshold: int = 50,
        date_columns: list[str] | None | None = None,
    ) -> pd.DataFrame:
        """Optimize a pandas DataFrame for memory usage.

        Args:
            df: Pandas DataFrame to optimize
            categorical_threshold: Maximum number of unique values for categorical conversion
            date_columns: List of column names to convert to datetime

        Returns:
            pd.DataFrame: Optimized pandas DataFrame
        """
        # Create a copy to avoid modifying the original
        result = df.copy()

        # Convert date columns
        if date_columns:
            for col in date_columns:
                if col in result.columns:
                    result[col] = pd.to_datetime(result[col])

        # Optimize numeric columns
        for col in result.select_dtypes(include=["int"]).columns:
            # Get column min and max
            col_min = result[col].min()
            col_max = result[col].max()

            # Convert to smallest possible integer type
            if col_min >= 0:
                if col_max < 256:
                    result[col] = result[col].astype(np.uint8)
                elif col_max < 65536:
                    result[col] = result[col].astype(np.uint16)
                elif col_max < 4294967296:
                    result[col] = result[col].astype(np.uint32)
            elif col_min > -128 and col_max < 128:
                result[col] = result[col].astype(np.int8)
            elif col_min > -32768 and col_max < 32768:
                result[col] = result[col].astype(np.int16)
            elif col_min > -2147483648 and col_max < 2147483648:
                result[col] = result[col].astype(np.int32)

        # Optimize float columns
        for col in result.select_dtypes(include=["float"]).columns:
            result[col] = result[col].astype(np.float32)

        # Convert string columns to categorical if they have few unique values
        for col in result.select_dtypes(include=["object"]).columns:
            num_unique = result[col].nunique()
            if num_unique < categorical_threshold:
                result[col] = result[col].astype("category")

        return result

    def _optimize_polars_dataframe(
        self,
        df: pl.DataFrame,
        categorical_threshold: int = 50,
        date_columns: list[str] | None | None = None,
    ) -> pl.DataFrame:
        """Optimize a polars DataFrame for memory usage.

        Args:
            df: Polars DataFrame to optimize
            categorical_threshold: Maximum number of unique values for categorical conversion
            date_columns: List of column names to convert to datetime

        Returns:
            pl.DataFrame: Optimized polars DataFrame
        """
        # Create expressions for optimizing columns
        expressions = []

        # Process each column
        for col in df.columns:
            col_expr = pl.col(col)

            # Convert date columns
            if date_columns and col in date_columns:
                expressions.append(col_expr.cast(pl.Datetime))
                continue

            # Get column data type
            dtype = df[col].dtype

            # Optimize numeric columns
            if dtype in [pl.Int64, pl.Int32, pl.Int16, pl.Int8]:
                # Get column min and max
                col_min = df[col].min()
                col_max = df[col].max()

                # Convert to smallest possible integer type
                if col_min >= 0:
                    if col_max < 256:
                        expressions.append(col_expr.cast(pl.UInt8))
                    elif col_max < 65536:
                        expressions.append(col_expr.cast(pl.UInt16))
                    elif col_max < 4294967296:
                        expressions.append(col_expr.cast(pl.UInt32))
                    else:
                        expressions.append(col_expr)
                elif col_min > -128 and col_max < 128:
                    expressions.append(col_expr.cast(pl.Int8))
                elif col_min > -32768 and col_max < 32768:
                    expressions.append(col_expr.cast(pl.Int16))
                elif col_min > -2147483648 and col_max < 2147483648:
                    expressions.append(col_expr.cast(pl.Int32))
                else:
                    expressions.append(col_expr)

            # Optimize float columns
            elif dtype in [pl.Float64, pl.Float32]:
                expressions.append(col_expr.cast(pl.Float32))

            # Convert string columns to categorical if they have few unique values
            elif dtype == pl.Utf8:
                num_unique = df[col].n_unique()
                if num_unique < categorical_threshold:
                    expressions.append(col_expr.cast(pl.Categorical))
                else:
                    expressions.append(col_expr)

            # Keep other columns as is
            else:
                expressions.append(col_expr)

        # Apply all optimizations
        return df.select(expressions)

    def efficient_join(
        self,
        left: pd.DataFrame | pl.DataFrame,
        right: pd.DataFrame | pl.DataFrame,
        on: str | list[str],
        how: str = "inner",
    ) -> pd.DataFrame | pl.DataFrame:
        """Efficiently join two DataFrames.

        Args:
            left: Left DataFrame
            right: Right DataFrame
            on: Column(s) to join on
            how: Join type ('inner', 'left', 'right', 'outer')

        Returns:
            Union[pd.DataFrame, pl.DataFrame]: Joined DataFrame
        """
        try:
            # Convert both to the same type for joining
            if isinstance(left, pd.DataFrame) and isinstance(right, pd.DataFrame):
                # Both are pandas, use pandas join
                self.log("Joining pandas DataFrames", "debug")
                return left.merge(right, on=on, how=how)
            if isinstance(left, pl.DataFrame) and isinstance(right, pl.DataFrame):
                # Both are polars, use polars join
                self.log("Joining polars DataFrames", "debug")
                return left.join(right, on=on, how=how)
            if isinstance(left, pd.DataFrame):
                # Convert right to pandas
                self.log("Converting right DataFrame to pandas for join", "debug")
                right_pd = self.ensure_pandas(right)
                return left.merge(right_pd, on=on, how=how)
            # Convert left to polars
            self.log("Converting left DataFrame to polars for join", "debug")
            left_pl = self.ensure_polars(left)
            return left_pl.join(right, on=on, how=how)
        except Exception as e:
            self.log(f"Error in efficient_join: {e!s}", "error")
            # Return the left DataFrame on error
            return left

    def extract_signals_and_returns(
        self,
        data: pd.DataFrame | pl.DataFrame,
        signal_column: str = "Signal",
        return_column: str = "Return",
        date_column: str = "Date",
    ) -> tuple[np.ndarray, np.ndarray]:
        """Efficiently extract signals and returns from a DataFrame.

        Args:
            data: DataFrame containing signals and returns
            signal_column: Name of the signal column
            return_column: Name of the return column
            date_column: Name of the date column

        Returns:
            Tuple[np.ndarray, np.ndarray]: Tuple of (signals, returns) as numpy arrays
        """
        try:
            # Validate DataFrame
            self.error_handler.validate_dataframe(
                data,
                [signal_column, return_column],
                "Data for signal extraction",
            )

            # Extract based on DataFrame type
            if isinstance(data, pd.DataFrame):
                signals = data[signal_column].to_numpy()
                returns = data[return_column].to_numpy()
            else:  # polars DataFrame
                signals = data[signal_column].to_numpy()
                returns = data[return_column].to_numpy()

            # Validate arrays
            self.error_handler.validate_numeric_array(signals, "Signals array")
            self.error_handler.validate_numeric_array(returns, "Returns array")

            return signals, returns
        except Exception as e:
            self.log(f"Error extracting signals and returns: {e!s}", "error")
            # Return empty arrays on error
            return np.array([]), np.array([])

    def convert_hourly_to_4hour(
        self,
        df: pd.DataFrame | pl.DataFrame,
        ticker: str | None = None,
    ) -> pd.DataFrame | pl.DataFrame:
        """Convert 1-hour OHLC data to 4-hour OHLC bars with market-aware logic.

        Args:
            df: DataFrame with 1-hour OHLC data containing Date, Open, High, Low, Close, Volume columns
            ticker: Optional ticker symbol for market type detection

        Returns:
            Union[pd.DataFrame, pl.DataFrame]: DataFrame with 4-hour OHLC bars of the same type as input
        """
        try:
            # Use market-aware conversion if ticker is provided
            if ticker:
                from app.tools.market_hours import detect_market_type

                market_type = detect_market_type(ticker)
                return self.convert_hourly_to_4hour_market_aware(df, market_type)
            # Legacy conversion for backward compatibility
            return self.process_in_native_format(
                df,
                lambda pandas_df: self._convert_pandas_hourly_to_4hour(pandas_df),
                lambda polars_df: self._convert_polars_hourly_to_4hour(polars_df),
            )
        except Exception as e:
            self.log(f"Error converting hourly to 4-hour data: {e!s}", "error")
            # Return the original DataFrame on error
            return df

    def convert_hourly_to_4hour_market_aware(
        self,
        df: pd.DataFrame | pl.DataFrame,
        market_type,
    ) -> pd.DataFrame | pl.DataFrame:
        """Convert 1-hour OHLC data to 4-hour OHLC bars with market-specific logic.

        Args:
            df: DataFrame with 1-hour OHLC data containing Date, Open, High, Low, Close, Volume columns
            market_type: MarketType enum indicating the market type

        Returns:
            Union[pd.DataFrame, pl.DataFrame]: DataFrame with market-appropriate 4-hour OHLC bars
        """
        try:
            from app.tools.market_hours import MarketType, filter_trading_hours

            if market_type == MarketType.US_STOCK:
                # For stocks: filter to trading hours first, then create 4-hour bars
                self.log(
                    "Applying stock market hours filtering for 4-hour conversion",
                    "info",
                )
                df_filtered = filter_trading_hours(df, market_type)

                # Use trading session aligned conversion for stocks
                return self.process_in_native_format(
                    df_filtered,
                    lambda pandas_df: self._convert_pandas_stock_to_4hour(pandas_df),
                    lambda polars_df: self._convert_polars_stock_to_4hour(polars_df),
                )
            # CRYPTO or other 24/7 markets
            # For crypto: use standard UTC-aligned 4-hour conversion
            self.log("Using standard 4-hour conversion for 24/7 market", "info")
            return self.process_in_native_format(
                df,
                lambda pandas_df: self._convert_pandas_hourly_to_4hour(pandas_df),
                lambda polars_df: self._convert_polars_hourly_to_4hour(polars_df),
            )
        except Exception as e:
            self.log(f"Error in market-aware 4-hour conversion: {e!s}", "error")
            # Return the original DataFrame on error
            return df

    def _convert_pandas_hourly_to_4hour(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert pandas DataFrame from 1-hour to 4-hour OHLC bars.

        Args:
            df: Pandas DataFrame with 1-hour OHLC data

        Returns:
            pd.DataFrame: DataFrame with 4-hour OHLC bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Create a copy to avoid modifying the original
        result = df.copy()

        # Ensure Date column is datetime
        result["Date"] = pd.to_datetime(result["Date"])

        # Set Date as index for resampling
        result = result.set_index("Date")

        # Resample to 4-hour bars using OHLC aggregation
        four_hour_data = (
            result.resample("4H")
            .agg(
                {
                    "Open": "first",  # First value in the 4-hour period
                    "High": "max",  # Maximum value in the 4-hour period
                    "Low": "min",  # Minimum value in the 4-hour period
                    "Close": "last",  # Last value in the 4-hour period
                    "Volume": "sum",  # Sum of volume in the 4-hour period
                },
            )
            .dropna()
        )  # Remove any rows with NaN values

        # Reset index to make Date a column again
        four_hour_data = four_hour_data.reset_index()

        self.log(
            f"Converted {len(df)} 1-hour bars to {len(four_hour_data)} 4-hour bars",
            "info",
        )

        return four_hour_data

    def _convert_polars_hourly_to_4hour(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert polars DataFrame from 1-hour to 4-hour OHLC bars.

        Args:
            df: Polars DataFrame with 1-hour OHLC data

        Returns:
            pl.DataFrame: DataFrame with 4-hour OHLC bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Ensure Date column is datetime (handle both string and existing datetime types)
        try:
            # Try to convert from string first
            df_with_datetime = df.with_columns(
                [pl.col("Date").str.to_datetime().alias("Date")],
            )
        except Exception:
            # If that fails, assume it's already datetime and just use it as-is
            df_with_datetime = df

        # Create 4-hour groups by truncating datetime to 4-hour intervals
        df_grouped = df_with_datetime.with_columns(
            [pl.col("Date").dt.truncate("4h").alias("Date_4H")],
        )

        # Group by 4-hour intervals and aggregate OHLC data
        four_hour_data = (
            df_grouped.group_by("Date_4H")
            .agg(
                [
                    pl.col("Open")
                    .first()
                    .alias("Open"),  # First value in the 4-hour period
                    pl.col("High")
                    .max()
                    .alias("High"),  # Maximum value in the 4-hour period
                    pl.col("Low")
                    .min()
                    .alias("Low"),  # Minimum value in the 4-hour period
                    pl.col("Close")
                    .last()
                    .alias("Close"),  # Last value in the 4-hour period
                    pl.col("Volume")
                    .sum()
                    .alias("Volume"),  # Sum of volume in the 4-hour period
                ],
            )
            .select(
                [
                    pl.col("Date_4H").alias("Date"),
                    pl.col("Open"),
                    pl.col("High"),
                    pl.col("Low"),
                    pl.col("Close"),
                    pl.col("Volume"),
                ],
            )
            .sort("Date")
        )

        # Remove any rows with null values
        four_hour_data = four_hour_data.drop_nulls()

        self.log(
            f"Converted {len(df)} 1-hour bars to {len(four_hour_data)} 4-hour bars",
            "info",
        )

        return four_hour_data

    def _convert_pandas_stock_to_4hour(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert pandas DataFrame from 1-hour stock data to trading-session-aligned 4-hour bars.

        Args:
            df: Pandas DataFrame with 1-hour stock OHLC data (already filtered to trading hours)

        Returns:
            pd.DataFrame: DataFrame with trading-session-aligned 4-hour bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Create a copy to avoid modifying the original
        result = df.copy()

        # Ensure Date column is datetime and convert to ET timezone
        result["Date"] = pd.to_datetime(result["Date"])
        result["Date"] = result["Date"].dt.tz_convert("America/New_York")

        # Set Date as index for resampling
        result = result.set_index("Date")

        # Create 4-hour bars aligned to trading sessions
        # For now, use standard 4H resampling but only on trading hours data
        # This creates bars like: 9:30-13:30, 13:30-16:00 (last bar is 2.5 hours)
        four_hour_data = (
            result.resample("4H", origin="start")
            .agg(
                {
                    "Open": "first",  # First value in the period
                    "High": "max",  # Maximum value in the period
                    "Low": "min",  # Minimum value in the period
                    "Close": "last",  # Last value in the period
                    "Volume": "sum",  # Sum of volume in the period
                },
            )
            .dropna()
        )  # Remove any rows with NaN values

        # Reset index to make Date a column again
        four_hour_data = four_hour_data.reset_index()

        # Convert back to UTC for consistency with rest of system
        four_hour_data["Date"] = four_hour_data["Date"].dt.tz_convert("UTC")

        self.log(
            f"Converted {len(df)} 1-hour stock bars to {len(four_hour_data)} trading-session-aligned bars",
            "info",
        )

        return four_hour_data

    def _convert_polars_stock_to_4hour(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert polars DataFrame from 1-hour stock data to trading-session-aligned 4-hour bars.

        Args:
            df: Polars DataFrame with 1-hour stock OHLC data (already filtered to trading hours)

        Returns:
            pl.DataFrame: DataFrame with trading-session-aligned 4-hour bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Ensure Date column is datetime (handle both string and existing datetime types)
        try:
            # Try to convert from string first
            df_with_datetime = df.with_columns(
                [pl.col("Date").str.to_datetime().alias("Date")],
            )
        except Exception:
            # If that fails, assume it's already datetime and just use it as-is
            df_with_datetime = df

        # Convert to ET timezone for stock market alignment
        df_et = df_with_datetime.with_columns(
            [pl.col("Date").dt.convert_time_zone("America/New_York").alias("Date")],
        )

        # Create 4-hour groups by truncating datetime to 4-hour intervals
        # This will create trading-session aligned bars
        df_grouped = df_et.with_columns(
            [pl.col("Date").dt.truncate("4h").alias("Date_4H")],
        )

        # Group by 4-hour intervals and aggregate OHLC data
        four_hour_data = (
            df_grouped.group_by("Date_4H")
            .agg(
                [
                    pl.col("Open")
                    .first()
                    .alias("Open"),  # First value in the 4-hour period
                    pl.col("High")
                    .max()
                    .alias("High"),  # Maximum value in the 4-hour period
                    pl.col("Low")
                    .min()
                    .alias("Low"),  # Minimum value in the 4-hour period
                    pl.col("Close")
                    .last()
                    .alias("Close"),  # Last value in the 4-hour period
                    pl.col("Volume")
                    .sum()
                    .alias("Volume"),  # Sum of volume in the 4-hour period
                ],
            )
            .select(
                [
                    pl.col("Date_4H")
                    .dt.convert_time_zone("UTC")
                    .alias("Date"),  # Convert back to UTC
                    pl.col("Open"),
                    pl.col("High"),
                    pl.col("Low"),
                    pl.col("Close"),
                    pl.col("Volume"),
                ],
            )
            .sort("Date")
        )

        # Remove any rows with null values
        four_hour_data = four_hour_data.drop_nulls()

        self.log(
            f"Converted {len(df)} 1-hour stock bars to {len(four_hour_data)} trading-session-aligned bars",
            "info",
        )

        return four_hour_data

    def convert_daily_to_2day(
        self,
        df: pd.DataFrame | pl.DataFrame,
        ticker: str | None = None,
    ) -> pd.DataFrame | pl.DataFrame:
        """Convert daily OHLC data to 2-day OHLC bars with market-aware logic.

        Args:
            df: DataFrame with daily OHLC data containing Date, Open, High, Low, Close, Volume columns
            ticker: Optional ticker symbol for market type detection

        Returns:
            Union[pd.DataFrame, pl.DataFrame]: DataFrame with 2-day OHLC bars of the same type as input
        """
        try:
            # Use market-aware conversion if ticker is provided
            if ticker:
                from app.tools.market_hours import detect_market_type

                market_type = detect_market_type(ticker)
                return self.convert_daily_to_2day_market_aware(df, market_type)
            # Standard conversion
            return self.process_in_native_format(
                df,
                lambda pandas_df: self._convert_pandas_daily_to_2day(pandas_df),
                lambda polars_df: self._convert_polars_daily_to_2day(polars_df),
            )
        except Exception as e:
            self.log(f"Error converting daily to 2-day data: {e!s}", "error")
            # Return the original DataFrame on error
            return df

    def convert_daily_to_2day_market_aware(
        self,
        df: pd.DataFrame | pl.DataFrame,
        market_type,
    ) -> pd.DataFrame | pl.DataFrame:
        """Convert daily OHLC data to 2-day OHLC bars with market-specific logic.

        Args:
            df: DataFrame with daily OHLC data containing Date, Open, High, Low, Close, Volume columns
            market_type: MarketType enum indicating the market type

        Returns:
            Union[pd.DataFrame, pl.DataFrame]: DataFrame with market-appropriate 2-day OHLC bars
        """
        try:
            from app.tools.market_hours import MarketType

            if market_type == MarketType.US_STOCK:
                # For stocks: use business day-aware 2-day conversion (skip weekends/holidays)
                self.log(
                    "Applying stock market business day logic for 2-day conversion",
                    "info",
                )
                return self.process_in_native_format(
                    df,
                    lambda pandas_df: self._convert_pandas_stock_to_2day(pandas_df),
                    lambda polars_df: self._convert_polars_stock_to_2day(polars_df),
                )
            # CRYPTO or other 24/7 markets
            # For crypto: use standard calendar day 2-day conversion
            self.log("Using standard 2-day conversion for 24/7 market", "info")
            return self.process_in_native_format(
                df,
                lambda pandas_df: self._convert_pandas_daily_to_2day(pandas_df),
                lambda polars_df: self._convert_polars_daily_to_2day(polars_df),
            )
        except Exception as e:
            self.log(f"Error in market-aware 2-day conversion: {e!s}", "error")
            # Return the original DataFrame on error
            return df

    def _convert_pandas_daily_to_2day(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert pandas DataFrame from daily to 2-day OHLC bars.

        Args:
            df: Pandas DataFrame with daily OHLC data

        Returns:
            pd.DataFrame: DataFrame with 2-day OHLC bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Create a copy to avoid modifying the original
        result = df.copy()

        # Ensure Date column is datetime
        result["Date"] = pd.to_datetime(result["Date"])

        # Set Date as index for resampling
        result = result.set_index("Date")

        # Resample to 2-day bars using OHLC aggregation
        two_day_data = (
            result.resample("2D")
            .agg(
                {
                    "Open": "first",  # First value in the 2-day period
                    "High": "max",  # Maximum value in the 2-day period
                    "Low": "min",  # Minimum value in the 2-day period
                    "Close": "last",  # Last value in the 2-day period
                    "Volume": "sum",  # Sum of volume in the 2-day period
                },
            )
            .dropna()
        )  # Remove any rows with NaN values

        # Reset index to make Date a column again
        two_day_data = two_day_data.reset_index()

        self.log(
            f"Converted {len(df)} daily bars to {len(two_day_data)} 2-day bars",
            "info",
        )

        return two_day_data

    def _convert_polars_daily_to_2day(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert polars DataFrame from daily to 2-day OHLC bars.

        Args:
            df: Polars DataFrame with daily OHLC data

        Returns:
            pl.DataFrame: DataFrame with 2-day OHLC bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Ensure Date column is datetime (handle both string and existing datetime types)
        try:
            # Try to convert from string first
            df_with_datetime = df.with_columns(
                [pl.col("Date").str.to_datetime().alias("Date")],
            )
        except Exception:
            # If that fails, assume it's already datetime and just use it as-is
            df_with_datetime = df

        # Create 2-day groups by truncating datetime to 2-day intervals
        df_grouped = df_with_datetime.with_columns(
            [pl.col("Date").dt.truncate("2d").alias("Date_2D")],
        )

        # Group by 2-day intervals and aggregate OHLC data
        two_day_data = (
            df_grouped.group_by("Date_2D")
            .agg(
                [
                    pl.col("Open")
                    .first()
                    .alias("Open"),  # First value in the 2-day period
                    pl.col("High")
                    .max()
                    .alias("High"),  # Maximum value in the 2-day period
                    pl.col("Low")
                    .min()
                    .alias("Low"),  # Minimum value in the 2-day period
                    pl.col("Close")
                    .last()
                    .alias("Close"),  # Last value in the 2-day period
                    pl.col("Volume")
                    .sum()
                    .alias("Volume"),  # Sum of volume in the 2-day period
                ],
            )
            .select(
                [
                    pl.col("Date_2D").alias("Date"),
                    pl.col("Open"),
                    pl.col("High"),
                    pl.col("Low"),
                    pl.col("Close"),
                    pl.col("Volume"),
                ],
            )
            .sort("Date")
        )

        # Remove any rows with null values
        two_day_data = two_day_data.drop_nulls()

        self.log(
            f"Converted {len(df)} daily bars to {len(two_day_data)} 2-day bars",
            "info",
        )

        return two_day_data

    def _convert_pandas_stock_to_2day(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert pandas DataFrame from daily stock data to business-day-aware 2-day bars.

        Args:
            df: Pandas DataFrame with daily stock OHLC data

        Returns:
            pd.DataFrame: DataFrame with business-day-aware 2-day bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Create a copy to avoid modifying the original
        result = df.copy()

        # Ensure Date column is datetime
        result["Date"] = pd.to_datetime(result["Date"])

        # Set Date as index for resampling
        result = result.set_index("Date")

        # Resample to 2 business days using OHLC aggregation
        two_day_data = (
            result.resample("2B")  # 2B = 2 business days
            .agg(
                {
                    "Open": "first",  # First value in the 2-business-day period
                    "High": "max",  # Maximum value in the 2-business-day period
                    "Low": "min",  # Minimum value in the 2-business-day period
                    "Close": "last",  # Last value in the 2-business-day period
                    "Volume": "sum",  # Sum of volume in the 2-business-day period
                },
            )
            .dropna()
        )  # Remove any rows with NaN values

        # Reset index to make Date a column again
        two_day_data = two_day_data.reset_index()

        self.log(
            f"Converted {len(df)} daily stock bars to {len(two_day_data)} 2-business-day bars",
            "info",
        )

        return two_day_data

    def _convert_polars_stock_to_2day(self, df: pl.DataFrame) -> pl.DataFrame:
        """Convert polars DataFrame from daily stock data to business-day-aware 2-day bars.

        Args:
            df: Polars DataFrame with daily stock OHLC data

        Returns:
            pl.DataFrame: DataFrame with business-day-aware 2-day bars
        """
        # Validate required columns
        required_columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            msg = f"Missing required columns: {missing_columns}"
            raise ValueError(msg)

        # Ensure Date column is datetime
        try:
            df_with_datetime = df.with_columns(
                [pl.col("Date").str.to_datetime().alias("Date")],
            )
        except Exception:
            df_with_datetime = df

        # For business-day grouping in polars, we need to filter out weekends first
        # and then create 2-day groups based on business day sequence
        df_weekdays = df_with_datetime.filter(
            pl.col("Date").dt.weekday()
            < 6,  # Monday=1, Sunday=7, so <6 excludes weekends
        )

        # Create groups of every 2 business days
        # We'll use a custom grouping approach since polars doesn't have direct 2B support
        df_with_business_day_rank = df_weekdays.with_columns(
            [pl.col("Date").rank("ordinal").alias("business_day_rank")],
        )

        # Create groups of 2 business days
        df_grouped = df_with_business_day_rank.with_columns(
            [((pl.col("business_day_rank") - 1) // 2).alias("group_id")],
        )

        # Group by 2-business-day intervals and aggregate OHLC data
        two_day_data = (
            df_grouped.group_by("group_id")
            .agg(
                [
                    pl.col("Date").min().alias("Date"),  # Use first date in the group
                    pl.col("Open")
                    .first()
                    .alias("Open"),  # First value in the 2-business-day period
                    pl.col("High")
                    .max()
                    .alias("High"),  # Maximum value in the 2-business-day period
                    pl.col("Low")
                    .min()
                    .alias("Low"),  # Minimum value in the 2-business-day period
                    pl.col("Close")
                    .last()
                    .alias("Close"),  # Last value in the 2-business-day period
                    pl.col("Volume")
                    .sum()
                    .alias("Volume"),  # Sum of volume in the 2-business-day period
                ],
            )
            .select(
                [
                    pl.col("Date"),
                    pl.col("Open"),
                    pl.col("High"),
                    pl.col("Low"),
                    pl.col("Close"),
                    pl.col("Volume"),
                ],
            )
            .sort("Date")
        )

        # Remove any rows with null values
        two_day_data = two_day_data.drop_nulls()

        self.log(
            f"Converted {len(df)} daily stock bars to {len(two_day_data)} 2-business-day bars",
            "info",
        )

        return two_day_data

    def time_operation(
        self,
        operation: Callable[..., T],
        *args,
        **kwargs,
    ) -> tuple[T, float]:
        """Time the execution of an operation.

        Args:
            operation: Function to time
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Tuple[T, float]: Tuple of (result, execution_time_seconds)
        """
        start_time = time.time()
        result = operation(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time

        self.log(
            f"Operation {operation.__name__} took {execution_time:.4f} seconds",
            "info",
        )

        return result, execution_time


# Convenience functions for backward compatibility


def ensure_polars(
    df: pd.DataFrame | pl.DataFrame,
    log: Callable | None | None = None,
) -> pl.DataFrame:
    """Ensure a DataFrame is a polars DataFrame.

    Args:
        df: DataFrame to convert
        log: Optional logging function

    Returns:
        pl.DataFrame: Polars DataFrame
    """
    processor = DataProcessor(log)
    return processor.ensure_polars(df)


def ensure_pandas(
    df: pd.DataFrame | pl.DataFrame,
    log: Callable | None | None = None,
) -> pd.DataFrame:
    """Ensure a DataFrame is a pandas DataFrame.

    Args:
        df: DataFrame to convert
        log: Optional logging function

    Returns:
        pd.DataFrame: Pandas DataFrame
    """
    processor = DataProcessor(log)
    return processor.ensure_pandas(df)


def optimize_dataframe(
    df: pd.DataFrame | pl.DataFrame,
    log: Callable | None | None = None,
) -> pd.DataFrame | pl.DataFrame:
    """Optimize a DataFrame for memory usage.

    Args:
        df: DataFrame to optimize
        log: Optional logging function

    Returns:
        Union[pd.DataFrame, pl.DataFrame]: Optimized DataFrame
    """
    processor = DataProcessor(log)
    return processor.optimize_dataframe(df)


def convert_hourly_to_4hour(
    df: pd.DataFrame | pl.DataFrame,
    log: Callable | None | None = None,
    ticker: str | None = None,
) -> pd.DataFrame | pl.DataFrame:
    """Convert 1-hour OHLC data to 4-hour OHLC bars with market-aware logic.

    Args:
        df: DataFrame with 1-hour OHLC data containing Date, Open, High, Low, Close, Volume columns
        log: Optional logging function
        ticker: Optional ticker symbol for market type detection

    Returns:
        Union[pd.DataFrame, pl.DataFrame]: DataFrame with 4-hour OHLC bars of the same type as input
    """
    processor = DataProcessor(log)
    return processor.convert_hourly_to_4hour(df, ticker)


def convert_daily_to_2day(
    df: pd.DataFrame | pl.DataFrame,
    log: Callable | None | None = None,
    ticker: str | None = None,
) -> pd.DataFrame | pl.DataFrame:
    """Convert daily OHLC data to 2-day OHLC bars with market-aware logic.

    Args:
        df: DataFrame with daily OHLC data containing Date, Open, High, Low, Close, Volume columns
        log: Optional logging function
        ticker: Optional ticker symbol for market type detection

    Returns:
        Union[pd.DataFrame, pl.DataFrame]: DataFrame with 2-day OHLC bars of the same type as input
    """
    processor = DataProcessor(log)
    return processor.convert_daily_to_2day(df, ticker)


@lru_cache(maxsize=128)
def cached_calculation(func: Callable[..., T], *args, **kwargs) -> T:
    """Cache the result of a calculation function.

    Args:
        func: Function to cache
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        T: Result of the function
    """
    return func(*args, **kwargs)
