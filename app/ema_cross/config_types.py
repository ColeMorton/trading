"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the EMA cross strategy modules.
"""

from typing import TypedDict, NotRequired, Union, List

class HeatmapConfig(TypedDict, total=False):
    """Configuration type definition for heatmap generation.

    Required Fields:
        TICKER (str): Ticker symbol to analyze (base asset for synthetic pairs)
        WINDOWS (int): Maximum window size for parameter analysis
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to use date subdirectory
        USE_BEST_PORTFOLIO (NotRequired[bool]): Whether to use portfolios_best directory
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        TICKER_2 (NotRequired[str]): Quote asset for synthetic pairs
    """
    TICKER: str
    WINDOWS: int
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_BEST_PORTFOLIO: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    TICKER_2: NotRequired[str]

class PortfolioConfig(TypedDict, total=False):
    """Configuration type definition for portfolio analysis.

    Required Fields:
        TICKER (Union[str, List[str]]): Single ticker or list of tickers to analyze
                                       (base asset for synthetic pairs)
        WINDOWS (int): Maximum window size for parameter analysis
        BASE_DIR (str): Base directory for file operations

    Optional Fields:
        USE_CURRENT (NotRequired[bool]): Whether to emphasize current window combinations
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        REFRESH (NotRequired[bool]): Whether to force regeneration of signals
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        TICKER_2 (NotRequired[str]): Quote asset for synthetic pairs
        MIN_WIN_RATE (NotRequired[float]): Minimum required win rate for portfolio filtering
        MIN_TRADES (NotRequired[int]): Minimum number of trades required for portfolio filtering
    """
    TICKER: Union[str, List[str]]
    WINDOWS: int
    BASE_DIR: str
    USE_CURRENT: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    REFRESH: NotRequired[bool]
    DIRECTION: NotRequired[str]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    TICKER_2: NotRequired[str]
    MIN_WIN_RATE: NotRequired[float]
    MIN_TRADES: NotRequired[int]

qqq_group5 = [
    "ASML",  # ASML Holding
    "MRNA",  # Moderna
    "ORLY",  # O'Reilly Automotive
    "PDD",   # PDD Holdings
    "FTNT",  # Fortinet
    "KDP",   # Keurig Dr Pepper
    "MNST",  # Monster Beverage
    "CTAS",  # Cintas
    "PAYX",  # Paychex
    "MRVL"   # Marvell Technology
]

qqq_group6 = [
    "ODFL",  # Old Dominion Freight Line
    "CHTR",  # Charter Communications
    "IDXX",  # IDEXX Laboratories
    "WDAY",  # Workday
    "ROST",  # Ross Stores
    "CPRT",  # Copart
    "DXCM",  # DexCom
    "PCAR",  # PACCAR
    "SIRI",  # Sirius XM
    "EA"     # Electronic Arts
]

qqq_group7 = [
    "VRSK",  # Verisk Analytics
    "CTSH",  # Cognizant
    "FAST",  # Fastenal
    "DLTR",  # Dollar Tree
    "XEL",   # Xcel Energy
    "CSGP",  # CoStar Group
    "WBD",   # Warner Bros Discovery
    "FANG",  # Diamondback Energy
    "ANSS",  # ANSYS
    "NXPI"   # NXP Semiconductors
]

qqq_group8 = [
    "GFS",   # GLOBALFOUNDRIES
    "BIIB",  # Biogen
    "ADSK",  # Autodesk
    "JD",    # JD.com
    "CRWD",  # CrowdStrike
    "TEAM",  # Atlassian
    "ILMN",  # Illumina
    "ZM",    # Zoom Video
    "ZS",    # Zscaler
    "ALGN"   # Align Technology
]

qqq_group9 = [
    "LCID",  # Lucid Group
    "SWKS",  # Skyworks Solutions
    "RIVN",  # Rivian Automotive
    "EBAY",  # eBay
    "BKR",   # Baker Hughes
    "DDOG",  # Datadog
    "SPLK",  # Splunk
    "CEG",   # Constellation Energy
    "DASH",  # DoorDash
    "GEHC"   # GE HealthCare Technologies
]

qqq_group10 = [
    "ON",    # ON Semiconductor
    "TTD",   # The Trade Desk
    "SGEN",  # Seagen
    "ENPH",  # Enphase Energy
    "ROP",   # Roper Technologies
    "FSLR",  # First Solar
    "MPWR",  # Monolithic Power Systems
    "AEP",   # American Electric Power
    "WBA",   # Walgreens Boots Alliance
    "CSX"    # CSX Corporation
]

# All groups in a list for easy access
qqq_groups = qqq_group5 + qqq_group6 + qqq_group7 + qqq_group8 + qqq_group9 + qqq_group10

# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": qqq_groups,
    "TICKER_1": "AAPL",
    "TICKER_2": "SPY",
    "USE_SYNTHETIC": False,
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_CURRENT": False,
    "BASE_DIR": ".",
    "USE_YEARS": False,
    "YEARS": 15,
    "DIRECTION": "Long",
    # "SORT_BY": "Total Return [%]"
    "SORT_BY": "Expectancy Adjusted",
    "MIN_WIN_RATE": 0.34,  # 50% minimum win rate
    "MIN_TRADES": 34      # Minimum 10 trades required
    # "MIN_WIN_RATE": 0.01,  # 50% minimum win rate
    # "MIN_TRADES": 1      # Minimum 10 trades required
}
