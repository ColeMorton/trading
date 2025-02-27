from typing import TypedDict
from app.tools.get_config import get_config as get_base_config

class Config(TypedDict):
    PERIOD: str
    YEARS: float
    USE_YEARS: bool
    USE_HOURLY: bool
    USE_SYNTHETIC: bool
    TICKER: str
    TICKER_1: str
    TICKER_2: str
    SHORT: bool
    USE_GBM: bool
    USE_SMA: bool
    SHORT_PERIOD: bool
    LONG_WINDOW: bool
    SIGNAL_WINDOW: bool
    RSI_PERIOD: bool
    RSI_THRESHOLD: int
    USE_RSI: bool

# Default Configuration
CONFIG: Config = {
    "TICKER": 'QQQ',
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": True,
    "USE_SYNTHETIC": False,
    "TICKER_1": 'MSTR',
    "TICKER_2": 'BTC-USD',
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "SHORT_PERIOD": 28,
    "LONG_WINDOW": 34,
    "SIGNAL_WINDOW": 35,
    "RSI_PERIOD": 14,
    "RSI_THRESHOLD": 45,  # Already an integer value
    "USE_RSI": False
}

config = get_base_config(CONFIG)
