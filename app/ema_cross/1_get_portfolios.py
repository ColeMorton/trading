import logging
import os
from typing import TypedDict, NotRequired
import numpy as np
import polars as pl
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from tools.filter_portfolios import filter_portfolios

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
    "TICKER": 'BTC-USD',
    "WINDOWS": 55
}

def run(config: Config = config) -> bool:
    config = get_config(config)

    # Create distinct integer values for windows
    short_windows = np.arange(2, config["WINDOWS"] + 1)  # [2, 3, ..., WINDOWS]
    long_windows = np.arange(3, config["WINDOWS"] + 1)  # [3, 4, ..., WINDOWS]

    portfolios = parameter_sensitivity_analysis(get_data(config["TICKER"], config), short_windows, long_windows, config)

    print(portfolios)

    filtered_portfolios = filter_portfolios(pl.DataFrame(portfolios), config)
    print(filtered_portfolios)

    return True

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise