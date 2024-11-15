# Configuration for EMA Cross Strategy

# General settings
YEARS = 3  # Reduced years since SOFI has limited history
USE_HOURLY_DATA = False
USE_SYNTHETIC = False
TICKER = 'SOFI'
TICKER_1 = 'SOFI'
TICKER_2 = 'SOFI'
SHORT = False
USE_SMA = False  # Keep EMA but with adjusted parameters

# EMA settings - adjusted for SOFI's characteristics
EMA_FAST = 5  # Shorter windows for more responsive signals
EMA_SLOW = 10

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
    "TICKER": TICKER,
    "TICKER_1": TICKER_1,
    "TICKER_2": TICKER_2,
    "SHORT": SHORT,
    "USE_SMA": USE_SMA,
    "EMA_FAST": EMA_FAST,
    "EMA_SLOW": EMA_SLOW,
    "RSI_PERIOD": RSI_PERIOD,
    "RSI_THRESHOLD": RSI_THRESHOLD,
    "USE_RSI": USE_RSI,
    "WINDOWS": 89
}
