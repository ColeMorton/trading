from typing import TypedDict

from typing_extensions import NotRequired


class DataConfig(TypedDict):
    """Configuration type definition for data retrieval.

    Required Fields:
        TICKER (str): Stock ticker symbol

    Optional Fields:
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to use specific years of data
        YEARS (NotRequired[float]): Number of years of data to retrieve
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pair
        TICKER_1 (NotRequired[str]): First ticker for synthetic pair
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pair
        BASE_DIR (NotRequired[str]): Base directory for data storage
        REFRESH (NotRequired[bool]): Whether to force refresh of cached data
    """

    TICKER: str
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    BASE_DIR: NotRequired[str]
    REFRESH: NotRequired[bool]
