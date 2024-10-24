import logging
import numpy as np
from app.utils import get_data
from app.ema_cross.tools.parameter_sensitivity_analysis import parameter_sensitivity_analysis
from app.ema_cross.tools.get_current_signals import get_current_signals

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "TICKER_1": 'EIX',
    "TICKER_2": 'BTC-USD',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": 'C:/Projects/trading'
}

# Logging setup
logging.basicConfig(filename='./logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run() -> None:
    """Main execution method."""

    # Create distinct integer values for windows
    short_windows = np.arange(2, 101)  # [2, 3, ..., 100]
    long_windows = np.arange(3, 101)  # [3, 4, ..., 100]

    current_signals = get_current_signals(get_data(CONFIG), short_windows, long_windows, CONFIG)

    print(current_signals)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise