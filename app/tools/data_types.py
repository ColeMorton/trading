from typing import TypedDict, NotRequired, Union, List

class DataConfig(TypedDict):
    """Configuration type definition for data retrieval.

    Required Fields:
        TICKER (Union[str, List[str]]): Stock ticker symbol or list of symbols
        BASE_DIR (str): Base directory for data storage

    Optional Fields:
        REFRESH (NotRequired[bool]): Whether to refresh data (default: True)
        USE_CURRENT (NotRequired[bool]): Whether to use current crossovers (default: False)
        MAX_DATA_AGE_SECONDS (NotRequired[int]): Maximum age of data in seconds (default: 300)
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to use specific years of data
        YEARS (NotRequired[float]): Number of years of data to retrieve
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pair
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
    """
    TICKER: Union[str, List[str]]
    BASE_DIR: str
    REFRESH: NotRequired[bool]
    USE_CURRENT: NotRequired[bool]
    MAX_DATA_AGE_SECONDS: NotRequired[int]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

class EnhancedConfig(TypedDict):
    """Enhanced configuration type definition.

    Required Fields:
        TICKER (Union[str, List[str]]): Ticker symbol or list of symbols
        BASE_DIR (str): Base directory for data storage

    Optional Fields:
        REFRESH (NotRequired[bool]): Whether to refresh data (default: True)
        USE_CURRENT (NotRequired[bool]): Whether to use current crossovers (default: False)
        MAX_DATA_AGE_SECONDS (NotRequired[int]): Maximum age of data in seconds (default: 300)
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to use specific years of data
        YEARS (NotRequired[float]): Number of years of data to retrieve
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pair
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
        USE_SMA (NotRequired[bool]): Whether to use SMA instead of EMA
        DIRECTION (NotRequired[str]): Trading direction ('Long' or 'Short')
        USE_RSI (NotRequired[bool]): Whether to use RSI filter
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for entry
        RSI_WINDOW (NotRequired[int]): RSI window size
        SHORT_WINDOW (NotRequired[int]): Short-term window size
        LONG_WINDOW (NotRequired[int]): Long-term window size
        STOP_LOSS (NotRequired[float]): Stop loss as decimal (0-1)
        SL_CANDLE_CLOSE (NotRequired[bool]): Whether to exit at candle close for stop loss
    """
    TICKER: Union[str, List[str]]
    BASE_DIR: str
    REFRESH: NotRequired[bool]
    USE_CURRENT: NotRequired[bool]
    MAX_DATA_AGE_SECONDS: NotRequired[int]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_SMA: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_RSI: NotRequired[bool]
    RSI_THRESHOLD: NotRequired[int]
    RSI_WINDOW: NotRequired[int]
    SHORT_WINDOW: NotRequired[int]
    LONG_WINDOW: NotRequired[int]
    STOP_LOSS: NotRequired[float]
    SL_CANDLE_CLOSE: NotRequired[bool]
