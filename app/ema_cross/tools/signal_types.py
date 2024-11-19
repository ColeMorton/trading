from typing import TypedDict, NotRequired

class Config(TypedDict):
    """Configuration type definition.

    Required Fields:
        TICKER (str): Trading symbol
        WINDOWS (int): Maximum window size to test

    Optional Fields:
        SHORT (NotRequired[bool]): Whether to use short positions
        USE_SMA (NotRequired[bool]): Whether to use SMA instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use GBM simulation
        USE_SYNTHETIC (NotRequired[bool]): Whether to use synthetic data
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
        USE_SCANNER (NotRequired[bool]): Whether to use scanner mode
    """
    TICKER: str
    WINDOWS: int
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    USE_SCANNER: NotRequired[bool]
