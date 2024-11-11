import logging
import numpy as np
import pandas as pd
from typing import TypedDict, NotRequired, List
from app.tools.get_data import get_data
from app.tools.get_config import get_config
from app.ema_cross.tools.get_current_signals import get_current_signals
from app.utils import save_csv

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
    USE_SCANNER: NotRequired[bool]

def generate_current_signals(config: Config) -> List:
    """Main execution method."""

    config = get_config(config)

    # Create distinct integer values for windows
    short_windows = np.arange(2, config["WINDOWS"])  # [2, 3, ..., WINDOWS]
    long_windows = np.arange(3, config["WINDOWS"])  # [3, 4, ..., WINDOWS]

    data = get_data(config["TICKER"], config)
    current_signals = get_current_signals(data, short_windows, long_windows, config)

    if config.get("USE_SCANNER", False) == False:
        save_csv(current_signals, "ma_cross", config, 'current_signals')
        
        # Display full data
        pd.set_option('display.max_rows', None)
        print("\nFull data table:")
        print(current_signals)

        if len(current_signals) == 0:
            print("No signals found for today")
    
    return current_signals

if __name__ == "__main__":
    try:
        # Default Configuration
        config: Config = {
            "USE_SMA": True,
            "TICKER": 'BTC-USD',
            "WINDOWS": 89
        }

        generate_current_signals(config)
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
