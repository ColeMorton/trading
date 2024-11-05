import logging
import os
from typing import TypedDict, NotRequired
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from tools.plot_heatmaps import plot_heatmap
from app.geometric_brownian_motion.get_median import get_median

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

# Default Configuration
config: Config = {
    "USE_SMA": True,
    "TICKER": 'MSTR',
    "USE_SYNTHETIC": True,
    "TICKER_1": 'MSTR',
    "TICKER_2": 'BTC-USD',
    "WINDOWS": 100
}

def run(config: Config = config) -> bool:
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
