from app.concurrency.tools.types import StrategyConfig

strategy_1: StrategyConfig = {
    "TICKER": "FET-USD",
    "SHORT_WINDOW": 42,
    "LONG_WINDOW": 54,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "USE_HOURLY": False,
    "REFRESH": True
}

strategy_2: StrategyConfig = {
    "TICKER": "FTM-USD",
    "SHORT_WINDOW": 65,
    "LONG_WINDOW": 82,
    "BASE_DIR": ".",
    "USE_SMA": False,
    "USE_HOURLY": True,
    "REFRESH": True
}

strategy_3: StrategyConfig = {
    "TICKER": "VIRTUAL-USD",
    "SHORT_WINDOW": 3,
    "LONG_WINDOW": 10,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "USE_HOURLY": False,
    "REFRESH": True
}

strategy_4: StrategyConfig = {
    "TICKER": "NEAR-USD",
    "SHORT_WINDOW": 41,
    "LONG_WINDOW": 54,
    "BASE_DIR": ".",
    "USE_SMA": False,
    "USE_HOURLY": True,
    "REFRESH": True
}

portfolio = [strategy_1, strategy_2, strategy_3, strategy_4]