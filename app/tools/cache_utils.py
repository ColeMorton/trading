"""Utility functions for data caching and retrieval."""

import os
from typing import Generic, TypeVar

import numpy as np
import polars as pl
from typing_extensions import TypedDict


class CacheConfig(TypedDict):
    """Configuration type definition for cache operations.

    Required Fields:
        BASE_DIR (str): Base directory for cache storage
        TICKER (Union[str, List[str]]): Ticker symbol or list of symbols
        FAST_PERIOD (int): Short moving average window
        SLOW_PERIOD (int): Long moving average window

    Optional Fields:
        USE_SMA (NotRequired[bool]): Whether to use SMA instead of EMA
        USE_RSI (NotRequired[bool]): Whether RSI filter is enabled
        RSI_WINDOW (NotRequired[int]): RSI calculation period
        RSI_THRESHOLD (NotRequired[int]): RSI threshold value
        STOP_LOSS (NotRequired[float]): Stop loss percentage
        REFRESH (NotRequired[bool]): Whether to force refresh analysis
        RELATIVE (NotRequired[bool]): When True, all metrics are relative to the baseline analysis; when False, all metrics are absolute.
    """

    BASE_DIR: str
    TICKER: str | list[str]
    FAST_PERIOD: int
    SLOW_PERIOD: int
    USE_SMA: bool
    USE_RSI: bool
    RSI_WINDOW: int
    RSI_THRESHOLD: int
    STOP_LOSS: float
    REFRESH: bool
    RELATIVE: bool


T = TypeVar("T", bound=np.ndarray)


class CacheResult(TypedDict, Generic[T]):
    """Type definition for cache loading results.

    Required Fields:
        trades (T): Array/matrix of trade counts
        returns (T): Array/matrix of return percentages
        sharpe_ratio (T): Array/matrix of Sharpe ratios
        win_rate (T): Array/matrix of win rates
    """

    trades: T
    returns: T
    sharpe_ratio: T
    win_rate: T


def get_ticker_prefix(config: CacheConfig) -> str:
    """
    Extract ticker prefix from config.

    Args:
        config (CacheConfig): Configuration dictionary

    Returns:
        str: Ticker prefix string
    """
    ticker_prefix = config.get("TICKER", "")
    if isinstance(ticker_prefix, list):
        ticker_prefix = ticker_prefix[0] if ticker_prefix else ""
    return ticker_prefix


def get_cache_filepath(config: CacheConfig, analysis_type: str) -> tuple[str, str]:
    """
    Generate filepath for analysis cache.

    Args:
        config (CacheConfig): Configuration dictionary
        analysis_type (str): Type of analysis ('rsi', 'stop_loss', 'protective_stop_loss')

    Returns:
        Tuple[str, str]: Tuple containing (directory_path, filename)
    """
    ticker_prefix = get_ticker_prefix(config)

    # Build suffixes based on config
    rsi_suffix = (
        f"_RSI_{config['RSI_WINDOW']}_{config['RSI_THRESHOLD']}"
        if config.get("USE_RSI", False)
        else ""
    )
    stop_loss_suffix = (
        f"_SL_{config['STOP_LOSS']}" if config.get("STOP_LOSS") is not None else ""
    )

    # Base filename components
    base_name = f"{ticker_prefix}_D_{'SMA' if config.get('USE_SMA', False) else 'EMA'}_{config['FAST_PERIOD']}_{config['SLOW_PERIOD']}"

    # Add appropriate suffixes based on analysis type
    if analysis_type == "rsi":
        filename = f"{base_name}.csv"
        subdir = "rsi"
    elif analysis_type == "stop_loss":
        filename = f"{base_name}{rsi_suffix}.csv"
        subdir = "stop_loss"
    elif analysis_type == "protective_stop_loss":
        filename = f"{base_name}{rsi_suffix}{stop_loss_suffix}.csv"
        subdir = "protective_stop_loss"
    else:
        raise ValueError(f"Unknown analysis type: {analysis_type}")

    directory = os.path.join(config["BASE_DIR"], "csv", "ma_cross", subdir)
    return directory, filename


def load_cached_analysis(
    filepath: str,
    param_range: np.ndarray | None | None = None,
    param_column: str = "Parameter",
    param_range_2: np.ndarray | None | None = None,
    param_column_2: str | None | None = None,
) -> CacheResult[np.ndarray] | None:
    """
    Load cached analysis results from a CSV file.

    Args:
        filepath (str): Path to the cached analysis file
        param_range (Optional[np.ndarray]): Primary parameter range (e.g., RSI thresholds)
        param_column (str): Name of the primary parameter column
        param_range_2 (Optional[np.ndarray]): Secondary parameter range for 2D analysis (e.g., RSI windows)
        param_column_2 (Optional[str]): Name of the secondary parameter column

    Returns:
        Optional[CacheResult[np.ndarray]]: Dictionary containing metric arrays/matrices if cache exists,
                                         None if cache doesn't exist or is invalid
    """
    if not os.path.exists(filepath):
        return None

    try:
        df = pl.read_csv(filepath)

        if param_range_2 is not None and param_column_2 is not None:
            # 2D analysis (e.g., RSI analysis with thresholds and windows)
            num_thresholds = (
                len(param_range)
                if param_range is not None
                else len(df[param_column].unique())
            )
            num_windows = len(param_range_2)

            # Initialize matrices with correct dimensions (thresholds x windows)
            trades_matrix = np.zeros((num_thresholds, num_windows))
            returns_matrix = np.zeros((num_thresholds, num_windows))
            sharpe_matrix = np.zeros((num_thresholds, num_windows))
            win_rate_matrix = np.zeros((num_thresholds, num_windows))

            # Populate matrices with correct indexing
            for i, threshold in enumerate(
                param_range if param_range is not None else df[param_column].unique()
            ):
                for j, window in enumerate(param_range_2):
                    row = df.filter(
                        (pl.col(param_column) == threshold)
                        & (pl.col(param_column_2) == window)
                    ).row(0, named=True)

                    trades_matrix[i, j] = row.get("Total Closed Trades", 0)
                    returns_matrix[i, j] = row.get("Total Return [%]", 0)
                    sharpe_matrix[i, j] = row.get("Sharpe Ratio", 0)
                    win_rate_matrix[i, j] = row.get("Win Rate [%]", 0)

            # Transpose matrices to match the new axis orientation (windows x
            # thresholds)
            return {
                "trades": trades_matrix.T,
                "returns": returns_matrix.T,
                "sharpe_ratio": sharpe_matrix.T,
                "win_rate": win_rate_matrix.T,
            }

        # 1D analysis (e.g., stop loss or protective stop loss)
        csv_params = df.get_column(param_column).unique().sort().to_numpy()

        if param_range is None:
            param_range = csv_params

        # Initialize arrays
        num_params = len(param_range)
        returns_array = np.zeros(num_params)
        win_rate_array = np.zeros(num_params)
        sharpe_ratio_array = np.zeros(num_params)
        trades_array = np.zeros(num_params)

        # For each parameter value, find the closest match in CSV
        for i, target_param in enumerate(param_range):
            closest_param = csv_params[np.abs(csv_params - target_param).argmin()]
            row = df.filter(pl.col(param_column) == closest_param).row(0, named=True)

            returns_array[i] = row.get("Total Return [%]", 0)
            win_rate_array[i] = row.get("Win Rate [%]", 0)
            sharpe_ratio_array[i] = row.get("Sharpe Ratio", 0)
            trades_array[i] = row.get("Total Closed Trades", 0)

        return {
            "trades": trades_array,
            "returns": returns_array,
            "sharpe_ratio": sharpe_ratio_array,
            "win_rate": win_rate_array,
        }

    except Exception as e:
        print(f"Error loading cached analysis: {e!s}")
        return None
