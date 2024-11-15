import logging
from typing import TypedDict, NotRequired
from app.ema_cross.tools.generate_current_signals import generate_current_signals

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
    "TICKER": 'SUI20947-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False
}

# Logging setup
logging.basicConfig(filename='./logs/ma_cross/1_get_current_signals.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def run(config: Config = config) -> bool:
    generate_current_signals(config)

    return True

if __name__ == "__main__":
    try:
        result = run()

        logging.info(f"Execution Success!")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
