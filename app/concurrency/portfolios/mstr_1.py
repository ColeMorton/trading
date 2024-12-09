from app.concurrency.tools.types import StrategyConfig

strategy_1: StrategyConfig = {
    "TICKER": "MSTR",
    "SHORT_WINDOW": 28,
    "LONG_WINDOW": 54,
    "BASE_DIR": ".",
    "USE_SMA": False,
    "USE_HOURLY": True,
    "REFRESH": True
}

strategy_2: StrategyConfig = {
    "TICKER": "MSTR",
    "SHORT_WINDOW": 68,
    "LONG_WINDOW": 82,
    "BASE_DIR": ".",
    "USE_SMA": True,
    "USE_HOURLY": True,
    "REFRESH": True
}

portfolio = [strategy_1, strategy_2]