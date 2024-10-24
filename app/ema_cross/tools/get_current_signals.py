import logging
import polars as pl
from typing import List
from app.utils import get_data
from app.ema_cross.tools.calculate_ma_and_signals import calculate_ma_and_signals

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
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

def is_signal_current(signals: pl.DataFrame) -> bool:
    """
    Check if there is a current entry signal (Signal = 1 and Position = 0 in the last row).
    
    Args:
        signals: DataFrame containing Signal and Position columns
    
    Returns:
        bool: True if there is a current entry signal, False otherwise
    """
    last_row = signals.tail(1)
    return (last_row.get_column("Signal") == 1).item() and (last_row.get_column("Position") == 0).item()

def get_current_signals(data: pl.DataFrame, short_windows: List[int], long_windows: List[int], config: dict) -> List[pl.DataFrame]:
    try:
        signals = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(temp_data, short, long, config)
                    current = is_signal_current(temp_data)

                    if current:
                        signal = {
                            "Short Window": short,
                            "Long Window": long
                        }

                        signals.append(signal)

        return pl.DataFrame(signals)
    except Exception as e:
        raise

def test_is_signal_current() -> None:
    """Main execution method."""

    data = get_data(CONFIG)
    signals = calculate_ma_and_signals(data, CONFIG["SHORT_WINDOW"], CONFIG["LONG_WINDOW"], CONFIG)
    current = is_signal_current(signals)

    print(current)

if __name__ == "__main__":
    try:
        test_is_signal_current()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
