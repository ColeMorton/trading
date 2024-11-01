import logging
import os
import numpy as np
import polars as pl
from app.utils import get_data
from app.tools.get_config import get_config
from tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from tools.filter_portfolios import filter_portfolios

# Logging setup
log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
logging.basicConfig(filename=os.path.join(log_dir, 'ema_cross.log'), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'AMZN',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BCH-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 100
}

config = get_config(CONFIG)

# Create distinct integer values for windows
short_windows = np.arange(2, config["WINDOWS"] + 1)  # [2, 3, ..., WINDOWS]
long_windows = np.arange(3, config["WINDOWS"] + 1)  # [3, 4, ..., WINDOWS]

portfolios = parameter_sensitivity_analysis(get_data(config), short_windows, long_windows, config)

print(portfolios)

filtered_portfolios = filter_portfolios(pl.DataFrame(portfolios), config)
print(filtered_portfolios)