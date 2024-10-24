# Configuration for EMA Cross Strategy

# General settings
YEARS = 30
USE_HOURLY_DATA = False
USE_SYNTHETIC = False
TICKER_1 = 'BTC-USD'
TICKER_2 = 'BTC-USD'
SHORT = False
USE_SMA = False

# EMA settings
EMA_FAST = 11
EMA_SLOW = 17

# RSI settings
RSI_PERIOD = 14
RSI_THRESHOLD = 55
USE_RSI = False

# Stop loss settings
STOP_LOSS_RANGE = (0, 15, 0.01)

# Configuration dictionary
CONFIG = {
    "YEARS": YEARS,
    "USE_HOURLY_DATA": USE_HOURLY_DATA,
    "USE_SYNTHETIC": USE_SYNTHETIC,
    "TICKER_1": TICKER_1,
    "TICKER_2": TICKER_2,
    "SHORT": SHORT,
    "USE_SMA": USE_SMA,
    "EMA_FAST": EMA_FAST,
    "EMA_SLOW": EMA_SLOW,
    "RSI_PERIOD": RSI_PERIOD,
    "RSI_THRESHOLD": RSI_THRESHOLD,
    "USE_RSI": USE_RSI
}
