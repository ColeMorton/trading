import logging
import os
from app.utils import get_data
from app.tools.get_config import get_config
from tools.plot_heatmaps import plot_heatmap
from app.geometric_brownian_motion.get_median import get_median

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
    "TICKER": 'SPY',
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

if config.get('USE_GBM', False) == True:
    data = get_median(config)
else:
    data = get_data(config)

plot_heatmap(data, config)
