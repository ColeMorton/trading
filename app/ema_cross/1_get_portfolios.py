import logging
import os
import numpy as np
import polars as pl
from app.utils import get_data
from tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from tools.filter_portfolios import filter_portfolios
from tools.plot_heatmaps import plot_heatmap

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
    "USE_SYNTHETIC": False,
    "TICKER_1": 'SOL-USD',
    "TICKER_2": 'BTC-USD',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": 'C:/Projects/trading',
    "SHORT_WINDOWS": 100,
    "LONG_WINDOWS": 100
}

# Create distinct integer values for windows
short_windows = np.arange(2, CONFIG["SHORT_WINDOWS"] + 1)  # [2, 3, ..., SHORT_WINDOWS]
long_windows = np.arange(3, CONFIG["LONG_WINDOWS"] + 1)  # [3, 4, ..., LONG_WINDOWS]

portfolios = parameter_sensitivity_analysis(get_data(CONFIG), short_windows, long_windows, CONFIG)

print(portfolios)

filtered_portfolios = filter_portfolios(pl.DataFrame(portfolios), CONFIG)
print(filtered_portfolios)

# plot_heatmap(get_data(CONFIG), CONFIG["TICKER_1"], CONFIG)
