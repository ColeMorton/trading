from typing import Dict, TypedDict, NotRequired

class StrategyConfig(TypedDict):
    symbol: str
    short_window: int
    long_window: int
    stop_loss: NotRequired[float]
    position_size: float
    use_sma: bool

class Config(TypedDict):
    strategies: Dict[str, StrategyConfig]
    start_date: str
    end_date: str
    init_cash: float
    fees: float

# Configuration for the strategy
config_default: Config = {
    "strategies": {
        "BTC_Strategy_1": {
            "symbol": "BTC-USD",
            "short_window": 27,
            "long_window": 29,
            "stop_loss": 9.11,
            "position_size": 1,
            "use_sma": True
        },
        "BTC_Strategy_2": {
            "symbol": "BTC-USD",
            "short_window": 8,
            "long_window": 44,
            "stop_loss": 4.12,
            "position_size": 1,
            "use_sma": True
        },
        "BTC_Strategy_3": {
            "symbol": "BTC-USD",
            "short_window": 3,
            "long_window": 11,
            "stop_loss": 2.75,
            "position_size": 1,
            "use_sma": False
        },
        "BTC_Strategy_4": {
            "symbol": "BTC-USD",
            "short_window": 11,
            "long_window": 17,
            "stop_loss": 3.64,
            "position_size": 1,
            "use_sma": False
        },
        "SOL_Strategy_1": {
            "symbol": "SOL-USD",
            "short_window": 14,
            "long_window": 32,
            "stop_loss": 12.5,
            "position_size": 1,
            "use_sma": True
        },
        "SOL_Strategy_2": {
            "symbol": "SOL-USD",
            "short_window": 26,
            "long_window": 32,
            "position_size": 1,
            "use_sma": True
        },
        "SOL_Strategy_3": {
            "symbol": "SOL-USD",
            "short_window": 27,
            "long_window": 30,
            "stop_loss": 8.8,
            "position_size": 1,
            "use_sma": True
        },
        "SOL_Strategy_4": {
            "symbol": "SOL-USD",
            "short_window": 16,
            "long_window": 18,
            "position_size": 1,
            "use_sma": False
        }
    },
    # 'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    'start_date': '2020-01-01',  # Updated start date to ensure SOL-USD data availability
    'end_date': '2024-10-29',
    'init_cash': 10000,
    'fees': 0.001
}

# Configuration for the strategy
config_mstr: Config = {
    'strategies': {
        'BTC_Strategy_1': {
            'symbol': 'BTC-USD',
            'short_window': 2,
            'long_window': 25,
            'stop_loss': 5.43,
            'position_size': 1,
            'use_sma': True
        },
        'BTC_Strategy_2': {
            'symbol': 'BTC-USD',
            'short_window': 27,
            'long_window': 29,
            'stop_loss': 9.11,
            'position_size': 1,
            'use_sma': True
        },
        'SOL_Strategy_1': {
            'symbol': 'SOL-USD',
            'short_window': 14,
            'long_window': 32,
            'stop_loss': 12.5,
            'position_size': 1,
            'use_sma': True
        },
        'SOL_Strategy_2': {
            'symbol': 'SOL-USD',
            'short_window': 27,
            'long_window': 30,
            'stop_loss': 8.8,
            'position_size': 1,
            'use_sma': True
        },
        'MSTR_Strategy_1': {
            'symbol': 'SOL-USD',
            'short_window': 4,
            'long_window': 12,
            'stop_loss': 16.9,
            'position_size': 1,
            'use_sma': True
        }
    },
    # 'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    'start_date': '2020-01-01',  # Updated start date to ensure SOL-USD data availability
    'end_date': '2024-10-29',
    'init_cash': 10000,
    'fees': 0.001
}

# Configuration for the strategy
config_btc_sol: Config = {
    "strategies": {
        "BTC_Strategy_1": {
            "symbol": "BTC-USD",
            "short_window": 27,
            "long_window": 29,
            "position_size": 1,
            "use_sma": True
        },
        "BTC_Strategy_2": {
            "symbol": "BTC-USD",
            "short_window": 8,
            "long_window": 44,
            "position_size": 1,
            "use_sma": True
        },
        "BTC_Strategy_3": {
            "symbol": "BTC-USD",
            "short_window": 3,
            "long_window": 11,
            "position_size": 1,
            "use_sma": False
        },
        "BTC_Strategy_4": {
            "symbol": "BTC-USD",
            "short_window": 11,
            "long_window": 17,
            "position_size": 1,
            "use_sma": False
        },
        "SOL_Strategy_1": {
            "symbol": "SOL-USD",
            "short_window": 14,
            "long_window": 32,
            "position_size": 1,
            "use_sma": True
        },
        "SOL_Strategy_2": {
            "symbol": "SOL-USD",
            "short_window": 26,
            "long_window": 32,
            "position_size": 1,
            "use_sma": True
        },
        "SOL_Strategy_3": {
            "symbol": "SOL-USD",
            "short_window": 27,
            "long_window": 30,
            "position_size": 1,
            "use_sma": True
        },
        "SOL_Strategy_4": {
            "symbol": "SOL-USD",
            "short_window": 16,
            "long_window": 18,
            "position_size": 1,
            "use_sma": False
        }
    },
    # 'start_date': '2014-01-01',  # Updated start date to ensure SOL-USD data availability
    'start_date': '2020-01-01',  # Updated start date to ensure SOL-USD data availability
    'end_date': '2024-10-29',
    'init_cash': 10000,
    'fees': 0.001
}

config = config_btc_sol