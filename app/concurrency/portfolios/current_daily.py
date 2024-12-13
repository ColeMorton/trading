from app.concurrency.tools.types import StrategyConfig

strategy_1: StrategyConfig = {
    "TICKER": "BTC-USD",
    "SHORT_WINDOW": 27,
    "LONG_WINDOW": 29,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "REFRESH": True,
    "USE_RSI": True,
    "RSI_PERIOD": 14,
    "RSI_THRESHOLD": 50,
    "STOP_LOSS": 0.0911
}

strategy_2: StrategyConfig = {
    "TICKER": "BTC-USD",
    "SHORT_WINDOW": 14,
    "LONG_WINDOW": 23,
    "SIGNAL_PERIOD": 13,
    "BASE_DIR": ".",
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_RSI": True,
    "RSI_PERIOD": 14,
    "RSI_THRESHOLD": 45,    
    "STOP_LOSS": 0.088
}

strategy_4: StrategyConfig = {
    "TICKER": "SOL-USD",
    "SHORT_WINDOW": 14,
    "LONG_WINDOW": 32,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "REFRESH": True,
    "USE_RSI": True,
    "RSI_PERIOD": 26,
    "RSI_THRESHOLD": 43,    
    "STOP_LOSS": 0.125
}

strategy_5: StrategyConfig = {
    "TICKER": "SOL-USD",
    "SHORT_WINDOW": 19,
    "LONG_WINDOW": 33,
    "SIGNAL_PERIOD": 13,
    "BASE_DIR": ".",
    "USE_HOURLY": False,
    "REFRESH": True,
    "USE_RSI": False,
    "RSI_PERIOD": 26,
    "RSI_THRESHOLD": 43,    
    "STOP_LOSS": 0.189
}

portfolio = [strategy_1, strategy_2, strategy_4, strategy_5]