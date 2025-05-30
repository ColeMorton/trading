"""Concurrency module testing framework.

This package provides comprehensive testing for the MA Cross concurrency analysis module,
including unit tests, integration tests, performance tests, and test utilities.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import tempfile
from datetime import datetime, timedelta

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

# Common test configurations
TEST_CONFIGS = {
    "minimal": {
        "PORTFOLIO": "test_portfolio.json",
        "BASE_DIR": "test_logs",
        "REFRESH": True,
        "VISUALIZATION": False,
    },
    "full": {
        "PORTFOLIO": "test_portfolio.json",
        "BASE_DIR": "test_logs",
        "REFRESH": True,
        "VISUALIZATION": True,
        "OPTIMIZE": True,
        "REPORT_INCLUDES": {
            "TICKER_METRICS": True,
            "STRATEGIES": True,
            "STRATEGY_RELATIONSHIPS": True,
            "ALLOCATION": True,
        },
    },
}


def create_test_portfolio(
    strategies: List[Dict[str, Any]],
    format: str = "json"
) -> str:
    """Create a temporary test portfolio file.
    
    Args:
        strategies: List of strategy configurations
        format: File format ("json" or "csv")
        
    Returns:
        Path to the created temporary file
    """
    with tempfile.NamedTemporaryFile(
        mode='w', 
        suffix=f'.{format}', 
        delete=False
    ) as f:
        if format == "json":
            json.dump(strategies, f, indent=2)
        else:
            # CSV format
            import csv
            if strategies:
                writer = csv.DictWriter(f, fieldnames=strategies[0].keys())
                writer.writeheader()
                writer.writerows(strategies)
        
        return f.name


def create_test_price_data(
    ticker: str,
    days: int = 365,
    start_price: float = 100.0,
    volatility: float = 0.02
) -> Dict[str, List[float]]:
    """Create synthetic price data for testing.
    
    Args:
        ticker: Ticker symbol
        days: Number of days of data
        start_price: Starting price
        volatility: Daily volatility
        
    Returns:
        Price data dictionary with open, high, low, close arrays
    """
    import numpy as np
    
    # Generate random walk
    np.random.seed(42)  # For reproducibility
    returns = np.random.normal(0, volatility, days)
    prices = start_price * np.exp(np.cumsum(returns))
    
    # Generate OHLC data
    opens = prices * (1 + np.random.uniform(-0.005, 0.005, days))
    highs = np.maximum(opens, prices) * (1 + np.random.uniform(0, 0.01, days))
    lows = np.minimum(opens, prices) * (1 - np.random.uniform(0, 0.01, days))
    
    return {
        "open": opens.tolist(),
        "high": highs.tolist(),
        "low": lows.tolist(),
        "close": prices.tolist(),
    }


def create_test_strategies(
    count: int = 3,
    strategy_type: str = "SMA"
) -> List[Dict[str, Any]]:
    """Create test strategy configurations.
    
    Args:
        count: Number of strategies to create
        strategy_type: Type of strategy ("SMA", "EMA", "MACD")
        
    Returns:
        List of strategy configurations
    """
    strategies = []
    
    for i in range(count):
        if strategy_type in ["SMA", "EMA"]:
            strategy = {
                "ticker": f"TEST{i+1}",
                "timeframe": "D",
                "type": strategy_type,
                "direction": "long",
                "short_window": 10 + i * 5,
                "long_window": 30 + i * 10,
                "allocation": (100 / count) if count > 0 else 0,
            }
        else:  # MACD
            strategy = {
                "ticker": f"TEST{i+1}",
                "timeframe": "D",
                "type": "MACD",
                "direction": "long",
                "short_window": 12,
                "long_window": 26,
                "signal_window": 9,
                "allocation": (100 / count) if count > 0 else 0,
            }
        
        strategies.append(strategy)
    
    return strategies


# Export test utilities
__all__ = [
    "TEST_DATA_DIR",
    "TEST_CONFIGS",
    "create_test_portfolio",
    "create_test_price_data",
    "create_test_strategies",
]