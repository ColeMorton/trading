"""
Type definitions for protective stop loss analysis.
"""

from typing import Dict, List, Tuple, TypedDict, NotRequired

class PSLConfig(TypedDict):
    """Configuration type definition for protective stop loss analysis.

    Required Fields:
        SHORT_WINDOW (int): Short moving average window
        LONG_WINDOW (int): Long moving average window
        BASE_DIR (str): Base directory for output files
        TICKER (str): Ticker symbol

    Optional Fields:
        USE_SMA (NotRequired[bool]): Use SMA instead of EMA
        USE_RSI (NotRequired[bool]): Enable RSI filter
        RSI_PERIOD (NotRequired[int]): RSI calculation period
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for signals
        STOP_LOSS (NotRequired[float]): Stop loss percentage
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        REFRESH (NotRequired[bool]): Force refresh of analysis
    """
    SHORT_WINDOW: int
    LONG_WINDOW: int
    BASE_DIR: str
    TICKER: str
    USE_SMA: NotRequired[bool]
    USE_RSI: NotRequired[bool]
    RSI_PERIOD: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
    STOP_LOSS: NotRequired[float]
    DIRECTION: NotRequired[str]
    REFRESH: NotRequired[bool]

class MetricMatrices(TypedDict):
    """Type definition for metric matrices.

    Required Fields:
        trades (np.ndarray): Number of trades for each holding period
        returns (np.ndarray): Total returns for each holding period
        sharpe_ratio (np.ndarray): Sharpe ratios for each holding period
        win_rate (np.ndarray): Win rates for each holding period
    """
    trades: "np.ndarray"
    returns: "np.ndarray"
    sharpe_ratio: "np.ndarray"
    win_rate: "np.ndarray"

AnalysisResult = Tuple[MetricMatrices, "np.ndarray"]
HoldingPeriodResult = List[Tuple[int, float, int, float]]
