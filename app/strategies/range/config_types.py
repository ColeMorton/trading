"""
Configuration Type Definitions

This module provides centralized TypedDict definitions for configuration
across the Range High Break strategy modules.
"""

from typing import TypedDict

from typing_extensions import NotRequired

from app.core.types.config import BaseStrategyConfig


class PortfolioConfig(BaseStrategyConfig, total=False):
    """
    Configuration for range breakout strategy analysis.
    
    Extends BaseStrategyConfig with range-specific parameter fields.
    
    Range-Specific Fields:
        WINDOWS (int): Maximum window size for parameter analysis
        RANGE_THRESHOLD (float): Threshold for range detection
        BREAKOUT_THRESHOLD (float): Threshold for breakout detection
        USE_GBM (bool): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (bool): Whether to create synthetic pairs
        TICKER_1 (str): First ticker for synthetic pairs
        TICKER_2 (str): Second ticker for synthetic pairs
    """

    # Range-Specific Fields
    WINDOWS: NotRequired[int]
    RANGE_THRESHOLD: NotRequired[float]
    BREAKOUT_THRESHOLD: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]


# Default configuration
DEFAULT_CONFIG: PortfolioConfig = {
    "TICKER": ["BTC-USD"],
    "WINDOWS": 20,  # Maximum window size for parameter analysis
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_CURRENT": False,
    "BASE_DIR": ".",
    "USE_YEARS": False,
    "YEARS": 15,
    "DIRECTION": "Long",
    "SORT_BY": "Score",
}
