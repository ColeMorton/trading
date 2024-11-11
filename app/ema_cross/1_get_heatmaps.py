import logging
import os
import pandas as pd
from typing import TypedDict, NotRequired
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from tools.plot_heatmaps import plot_heatmap

# Logging setup
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, 'ema_cross.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Config(TypedDict):
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
    USE_CURRENT: NotRequired[bool]
    BASE_DIR: NotRequired[str]

# Default Configuration
config: Config = {
    "USE_CURRENT": True,
    "USE_SMA": True,
    "TICKER": 'BTC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": True
}

def run(config: Config = config) -> bool:
    """
    Run the EMA cross strategy analysis.
    When USE_CURRENT is True, only current window combinations are emphasized in the heatmap.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if execution successful
    """
    config = get_config(config)
    data = get_data(config["TICKER"], config)
    plot_heatmap(data, config)
    return True

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
