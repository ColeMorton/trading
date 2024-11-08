import logging
import os
import pandas as pd
from typing import TypedDict, NotRequired
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from tools.plot_heatmaps import plot_heatmap
from app.utils import get_path, get_filename

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
    "USE_SMA": True,  # Changed to True since we're reading TXN_D_SMA.csv
    "TICKER": 'TXN',
    "WINDOWS": 89,
    "USE_CURRENT": True
}

def run(config: Config = config) -> bool:
    config = get_config(config)

    if config.get("USE_CURRENT", False):
        config["BASE_DIR"] = "."

        # Read the CSV file
        filename = get_filename("csv", config)
        path = get_path("csv", "ma_cross", config, 'current_signals')
        fullpath = f"{path}/{filename}"
        
        # Debug prints
        print(f"Generated filename: {filename}")
        print(f"Generated path: {path}")
        print(f"Full path: {fullpath}")
        print(f"File exists: {os.path.exists(fullpath)}")
        
        if not os.path.exists(fullpath):
            raise FileNotFoundError(f"CSV file not found at: {fullpath}")

        df = pd.read_csv(fullpath)

        print(f"Loaded DataFrame shape: {df.shape}")

    data = get_data(config["TICKER"], config)

    plot_heatmap(data, config)

    return True

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
