from typing import TypedDict

from typing_extensions import NotRequired


class StrategyConfig(TypedDict):
    symbol: str
    fast_period: int
    slow_period: int
    stop_loss: NotRequired[float]
    position_size: float
    use_sma: bool


class Config(TypedDict):
    strategies: dict[str, StrategyConfig]
    start_date: str
    end_date: str
    init_cash: float
    fees: float


# Configuration for the strategy
config_default: Config = {
    "strategies": {
        "BTC_Strategy_1": {
            "symbol": "BTC-USD",
            "fast_period": 27,
            "slow_period": 29,
            "stop_loss": 9.11,
            "position_size": 1,
            "use_sma": True,
        },
        "BTC_Strategy_2": {
            "symbol": "BTC-USD",
            "fast_period": 8,
            "slow_period": 44,
            "stop_loss": 4.12,
            "position_size": 1,
            "use_sma": True,
        },
        "BTC_Strategy_3": {
            "symbol": "BTC-USD",
            "fast_period": 3,
            "slow_period": 11,
            "stop_loss": 2.75,
            "position_size": 1,
            "use_sma": False,
        },
        "BTC_Strategy_4": {
            "symbol": "BTC-USD",
            "fast_period": 11,
            "slow_period": 17,
            "stop_loss": 3.64,
            "position_size": 1,
            "use_sma": False,
        },
        "SOL_Strategy_1": {
            "symbol": "SOL-USD",
            "fast_period": 14,
            "slow_period": 32,
            "stop_loss": 12.5,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_2": {
            "symbol": "SOL-USD",
            "fast_period": 26,
            "slow_period": 32,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_3": {
            "symbol": "SOL-USD",
            "fast_period": 27,
            "slow_period": 30,
            "stop_loss": 8.8,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_4": {
            "symbol": "SOL-USD",
            "fast_period": 16,
            "slow_period": 18,
            "position_size": 1,
            "use_sma": False,
        },
    },
    # 'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    "start_date": "2020-01-01",  # Updated start date to ensure SOL-USD data availability
    "end_date": "2024-10-29",
    "init_cash": 10000,
    "fees": 0.001,
}

# Configuration for the strategy
config_mstr: Config = {
    "strategies": {
        "BTC_Strategy_1": {
            "symbol": "BTC-USD",
            "fast_period": 2,
            "slow_period": 25,
            "stop_loss": 5.43,
            "position_size": 1,
            "use_sma": True,
        },
        "BTC_Strategy_2": {
            "symbol": "BTC-USD",
            "fast_period": 27,
            "slow_period": 29,
            "stop_loss": 9.11,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_1": {
            "symbol": "SOL-USD",
            "fast_period": 14,
            "slow_period": 32,
            "stop_loss": 12.5,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_2": {
            "symbol": "SOL-USD",
            "fast_period": 27,
            "slow_period": 30,
            "stop_loss": 8.8,
            "position_size": 1,
            "use_sma": True,
        },
        "MSTR_Strategy_1": {
            "symbol": "SOL-USD",
            "fast_period": 4,
            "slow_period": 12,
            "stop_loss": 16.9,
            "position_size": 1,
            "use_sma": True,
        },
    },
    # 'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    "start_date": "2020-01-01",  # Updated start date to ensure SOL-USD data availability
    "end_date": "2024-10-29",
    "init_cash": 10000,
    "fees": 0.001,
}

# Configuration for the strategy
config_btc_sol: Config = {
    "strategies": {
        "BTC_Strategy_1": {
            "symbol": "BTC-USD",
            "fast_period": 27,
            "slow_period": 29,
            "position_size": 1,
            "use_sma": True,
        },
        "BTC_Strategy_2": {
            "symbol": "BTC-USD",
            "fast_period": 8,
            "slow_period": 44,
            "position_size": 1,
            "use_sma": True,
        },
        "BTC_Strategy_3": {
            "symbol": "BTC-USD",
            "fast_period": 3,
            "slow_period": 11,
            "position_size": 1,
            "use_sma": False,
        },
        "BTC_Strategy_4": {
            "symbol": "BTC-USD",
            "fast_period": 11,
            "slow_period": 17,
            "position_size": 1,
            "use_sma": False,
        },
        "SOL_Strategy_1": {
            "symbol": "SOL-USD",
            "fast_period": 14,
            "slow_period": 32,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_2": {
            "symbol": "SOL-USD",
            "fast_period": 26,
            "slow_period": 32,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_3": {
            "symbol": "SOL-USD",
            "fast_period": 27,
            "slow_period": 30,
            "position_size": 1,
            "use_sma": True,
        },
        "SOL_Strategy_4": {
            "symbol": "SOL-USD",
            "fast_period": 16,
            "slow_period": 18,
            "position_size": 1,
            "use_sma": False,
        },
    },
    # 'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    "start_date": "2020-01-01",  # Updated start date to ensure SOL-USD data availability
    "end_date": "2024-10-29",
    "init_cash": 10000,
    "fees": 0.001,
}

config = config_btc_sol
