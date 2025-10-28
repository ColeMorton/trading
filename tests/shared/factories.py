"""
Test data factories for creating consistent test scenarios.
Phase 3: Testing Infrastructure Consolidation - Optimized with intelligent caching
"""

from datetime import datetime, timedelta
import hashlib
import pickle
import random
from typing import Any

import numpy as np
import pandas as pd
import polars as pl


# =============================================================================
# Intelligent caching system for test data factories
# =============================================================================


class TestDataCache:
    """
    Intelligent cache for test data with automatic invalidation and performance optimization.
    """

    def __init__(self, max_size_mb: float = 100.0):
        self._cache: dict[str, Any] = {}
        self._cache_metadata: dict[str, dict[str, Any]] = {}
        self.max_size_mb = max_size_mb
        self._current_size_mb = 0.0

    def _calculate_size_mb(self, obj: Any) -> float:
        """Calculate approximate object size in MB."""
        try:
            size_bytes = len(pickle.dumps(obj))
            return size_bytes / (1024 * 1024)
        except Exception:
            # Fallback estimation for complex objects
            if isinstance(obj, pl.DataFrame | pd.DataFrame):
                return (
                    obj.memory_usage(deep=True).sum() / (1024 * 1024)
                    if hasattr(obj, "memory_usage")
                    else 1.0
                )
            if isinstance(obj, dict):
                return len(str(obj)) / (1024 * 1024)
            return 0.1  # Small default size

    def _generate_cache_key(self, func_name: str, **kwargs) -> str:
        """Generate cache key from function name and parameters."""
        # Create deterministic hash from function name and sorted kwargs
        key_data = f"{func_name}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _evict_if_needed(self, new_size_mb: float):
        """Evict oldest cached items if cache would exceed size limit."""
        if self._current_size_mb + new_size_mb <= self.max_size_mb:
            return

        # Sort by access time (oldest first)
        sorted_items = sorted(
            self._cache_metadata.items(),
            key=lambda x: x[1]["last_accessed"],
        )

        # Evict items until we have enough space
        space_needed = (self._current_size_mb + new_size_mb) - self.max_size_mb
        space_freed = 0.0

        for cache_key, metadata in sorted_items:
            if space_freed >= space_needed:
                break

            item_size = metadata["size_mb"]
            del self._cache[cache_key]
            del self._cache_metadata[cache_key]
            self._current_size_mb -= item_size
            space_freed += item_size

    def get(self, func_name: str, **kwargs) -> Any | None:
        """Get cached result if available."""
        cache_key = self._generate_cache_key(func_name, **kwargs)

        if cache_key in self._cache:
            # Update access time
            self._cache_metadata[cache_key]["last_accessed"] = datetime.now()
            self._cache_metadata[cache_key]["access_count"] += 1
            return self._cache[cache_key]

        return None

    def set(self, func_name: str, result: Any, **kwargs):
        """Cache result with metadata."""
        cache_key = self._generate_cache_key(func_name, **kwargs)

        # Calculate size and evict if needed
        result_size = self._calculate_size_mb(result)
        self._evict_if_needed(result_size)

        # Store result and metadata
        self._cache[cache_key] = result
        self._cache_metadata[cache_key] = {
            "created": datetime.now(),
            "last_accessed": datetime.now(),
            "access_count": 1,
            "size_mb": result_size,
            "func_name": func_name,
            "kwargs": kwargs,
        }

        self._current_size_mb += result_size

    def clear(self):
        """Clear all cached data."""
        self._cache.clear()
        self._cache_metadata.clear()
        self._current_size_mb = 0.0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total_items = len(self._cache)
        total_accesses = sum(
            meta["access_count"] for meta in self._cache_metadata.values()
        )

        return {
            "total_items": total_items,
            "total_size_mb": round(self._current_size_mb, 2),
            "max_size_mb": self.max_size_mb,
            "utilization_pct": round(
                (self._current_size_mb / self.max_size_mb) * 100,
                1,
            ),
            "total_accesses": total_accesses,
            "avg_accesses_per_item": round(total_accesses / max(total_items, 1), 1),
        }


# Global cache instance
_test_data_cache = TestDataCache()


def cached_factory(cache_ttl_minutes: int | None = None):
    """
    Decorator for caching factory function results.

    Args:
        cache_ttl_minutes: Time-to-live in minutes (None for no expiration)
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check cache first
            cached_result = _test_data_cache.get(func.__name__, **kwargs)
            if cached_result is not None:
                return cached_result

            # Generate result and cache it
            result = func(*args, **kwargs)
            _test_data_cache.set(func.__name__, result, **kwargs)
            return result

        wrapper._original_func = func
        wrapper.clear_cache = lambda: _test_data_cache.clear()
        wrapper.cache_stats = lambda: _test_data_cache.get_stats()
        return wrapper

    return decorator


@cached_factory()
def create_test_market_data(
    ticker: str = "TEST",
    days: int = 252,
    start_price: float = 100.0,
    volatility: float = 0.2,
    trend: float = 0.1,
    start_date: datetime | None = None,
) -> pl.DataFrame:
    """
    Create realistic market data for testing.

    Args:
        ticker: Stock ticker symbol
        days: Number of trading days
        start_price: Starting price
        volatility: Annual volatility (default 20%)
        trend: Annual trend (default 10%)
        start_date: Start date (defaults to 1 year ago)

    Returns:
        Polars DataFrame with OHLCV data
    """
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)

    # Generate dates (business days only)
    dates = pd.bdate_range(start=start_date, periods=days)

    # Generate price series using geometric Brownian motion
    dt = 1 / 252  # Daily time step
    mu = trend  # Drift
    sigma = volatility  # Volatility

    # Random walk
    random_returns = np.random.normal(mu * dt, sigma * np.sqrt(dt), days)

    # Calculate prices
    log_prices = np.log(start_price) + np.cumsum(random_returns)
    prices = np.exp(log_prices)

    # Generate OHLC from close prices
    opens = np.roll(prices, 1)
    opens[0] = start_price

    # Add some intraday volatility
    highs = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))

    # Ensure OHLC relationships are maintained
    highs = np.maximum(highs, np.maximum(opens, prices))
    lows = np.minimum(lows, np.minimum(opens, prices))

    # Volume (random but realistic)
    base_volume = 1_000_000
    volumes = np.random.lognormal(np.log(base_volume), 0.5, days).astype(int)

    # Create DataFrame
    return pl.DataFrame(
        {
            "Date": dates,
            "Ticker": [ticker] * days,
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": prices,
            "Volume": volumes,
            "Adj Close": prices,  # Assume no dividends/splits
        },
    )


@cached_factory()
def create_test_signals(
    num_signals: int = 50,
    ticker: str = "TEST",
    signal_types: list[str] | None = None,
) -> pl.DataFrame:
    """
    Create test trading signals.

    Args:
        num_signals: Number of signals to generate
        ticker: Ticker symbol
        signal_types: Types of signals (BUY, SELL, HOLD)

    Returns:
        Polars DataFrame with signal data
    """
    if signal_types is None:
        signal_types = ["BUY", "SELL", "HOLD"]

    # Generate dates
    start_date = datetime.now() - timedelta(days=num_signals)
    dates = pd.bdate_range(start=start_date, periods=num_signals)

    # Generate signals
    signals = [random.choice(signal_types) for _ in range(num_signals)]

    # Generate prices and confidence scores
    prices = 100 + np.cumsum(np.random.normal(0, 1, num_signals))
    confidence = np.random.uniform(0.5, 1.0, num_signals)

    # Generate signal strength
    strength = np.random.uniform(0.1, 1.0, num_signals)

    return pl.DataFrame(
        {
            "Date": dates,
            "Ticker": [ticker] * num_signals,
            "Signal": signals,
            "Price": prices,
            "Confidence": confidence,
            "Strength": strength,
            "Source": ["TEST_STRATEGY"] * num_signals,
        },
    )


@cached_factory()
def create_test_portfolio(
    tickers: list[str] | None = None,
    num_trades: int = 100,
    initial_capital: float = 100000.0,
) -> dict[str, Any]:
    """
    Create test portfolio with realistic performance metrics.

    Args:
        tickers: List of ticker symbols
        num_trades: Number of trades to generate
        initial_capital: Starting capital

    Returns:
        Dictionary with portfolio data
    """
    if tickers is None:
        tickers = ["AAPL", "GOOGL", "MSFT", "TSLA", "NVDA"]

    # Generate trades
    trades = []
    current_capital = initial_capital

    for i in range(num_trades):
        ticker = random.choice(tickers)
        entry_date = datetime.now() - timedelta(days=random.randint(1, 365))
        exit_date = entry_date + timedelta(days=random.randint(1, 30))

        entry_price = random.uniform(50, 500)
        exit_price = entry_price * random.uniform(0.8, 1.2)  # +/- 20%

        position_size = random.uniform(0.01, 0.1) * current_capital
        shares = int(position_size / entry_price)

        pnl = shares * (exit_price - entry_price)
        current_capital += pnl

        trades.append(
            {
                "trade_id": i + 1,
                "ticker": ticker,
                "entry_date": entry_date,
                "exit_date": exit_date,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "shares": shares,
                "pnl": pnl,
                "return_pct": (exit_price - entry_price) / entry_price,
            },
        )

    # Calculate portfolio metrics
    total_pnl = sum(trade["pnl"] for trade in trades)
    total_return = (current_capital - initial_capital) / initial_capital

    winning_trades = [t for t in trades if t["pnl"] > 0]
    losing_trades = [t for t in trades if t["pnl"] < 0]

    win_rate = len(winning_trades) / len(trades) if trades else 0

    avg_win = np.mean([t["pnl"] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t["pnl"] for t in losing_trades]) if losing_trades else 0

    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    # Calculate Sharpe ratio (simplified)
    returns = [t["return_pct"] for t in trades]
    sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0

    return {
        "portfolio_id": "TEST_PORTFOLIO",
        "initial_capital": initial_capital,
        "final_capital": current_capital,
        "total_pnl": total_pnl,
        "total_return": total_return,
        "num_trades": len(trades),
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "sharpe_ratio": sharpe_ratio,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "max_drawdown": random.uniform(0.05, 0.2),  # Simplified
        "trades": trades,
    }


@cached_factory()
def create_test_strategy_config(
    strategy_type: str = "MA_CROSS",
    timeframe: str = "D",
) -> dict[str, Any]:
    """
    Create test strategy configuration.

    Args:
        strategy_type: Type of strategy
        timeframe: Trading timeframe

    Returns:
        Strategy configuration dictionary
    """
    base_config = {
        "strategy_id": f"TEST_{strategy_type}_{timeframe}",
        "strategy_type": strategy_type,
        "timeframe": timeframe,
        "enabled": True,
        "risk_management": {
            "max_position_size": 0.1,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.15,
            "max_daily_trades": 5,
        },
        "capital_management": {
            "initial_capital": 100000.0,
            "position_sizing": "FIXED_PCT",
            "position_size_pct": 0.02,
        },
    }

    # Add strategy-specific parameters
    if strategy_type == "MA_CROSS":
        base_config.update(
            {
                "fast_period": random.randint(5, 15),
                "slow_period": random.randint(20, 50),
                "ma_type": random.choice(["SMA", "EMA"]),
            },
        )
    elif strategy_type == "MACD":
        base_config.update({"fast_period": 12, "slow_period": 26, "signal_period": 9})
    elif strategy_type == "RSI":
        base_config.update(
            {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70},
        )

    return base_config


def create_test_backtest_results(
    config: dict[str, Any] | None = None,
    num_trades: int = 50,
) -> dict[str, Any]:
    """
    Create realistic backtest results for testing.

    Args:
        config: Strategy configuration
        num_trades: Number of trades in backtest

    Returns:
        Backtest results dictionary
    """
    if config is None:
        config = create_test_strategy_config()

    # Generate performance metrics
    returns = np.random.normal(0.001, 0.02, 252)  # Daily returns
    cumulative_returns = np.cumprod(1 + returns) - 1

    portfolio = create_test_portfolio(num_trades=num_trades)

    return {
        "strategy_config": config,
        "backtest_id": f"BACKTEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "start_date": datetime.now() - timedelta(days=365),
        "end_date": datetime.now(),
        "initial_capital": config["capital_management"]["initial_capital"],
        "final_capital": portfolio["final_capital"],
        "total_return": portfolio["total_return"],
        "annualized_return": portfolio["total_return"],  # Simplified
        "volatility": np.std(returns) * np.sqrt(252),
        "sharpe_ratio": portfolio["sharpe_ratio"],
        "max_drawdown": portfolio["max_drawdown"],
        "win_rate": portfolio["win_rate"],
        "profit_factor": portfolio["profit_factor"],
        "num_trades": portfolio["num_trades"],
        "avg_trade_duration": random.uniform(1, 10),
        "returns": returns.tolist(),
        "cumulative_returns": cumulative_returns.tolist(),
        "trades": portfolio["trades"],
    }


def create_test_risk_metrics() -> dict[str, float]:
    """
    Create test risk metrics.

    Returns:
        Dictionary of risk metrics
    """
    return {
        "var_95": random.uniform(0.02, 0.05),
        "cvar_95": random.uniform(0.03, 0.08),
        "beta": random.uniform(0.8, 1.2),
        "alpha": random.uniform(-0.01, 0.02),
        "tracking_error": random.uniform(0.01, 0.05),
        "information_ratio": random.uniform(-0.5, 1.5),
        "sortino_ratio": random.uniform(0.5, 2.0),
        "calmar_ratio": random.uniform(0.2, 1.5),
        "omega_ratio": random.uniform(1.0, 2.0),
        "tail_ratio": random.uniform(0.8, 1.2),
    }


# Factory class for more complex test data creation
class TestDataFactory:
    """Factory class for creating complex test data scenarios."""

    @staticmethod
    def create_multi_asset_portfolio(
        assets: list[str],
        correlation_matrix: np.ndarray | None = None,
        days: int = 252,
    ) -> dict[str, pl.DataFrame]:
        """Create correlated multi-asset portfolio data."""
        if correlation_matrix is None:
            # Create random correlation matrix
            n = len(assets)
            correlation_matrix = np.random.uniform(0.1, 0.8, (n, n))
            np.fill_diagonal(correlation_matrix, 1.0)
            correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2

        # Generate correlated returns
        mean_returns = np.random.uniform(0.0005, 0.002, len(assets))
        cov_matrix = correlation_matrix * 0.02  # 2% volatility

        returns = np.random.multivariate_normal(mean_returns, cov_matrix, days)

        # Convert to price data
        asset_data = {}
        for i, asset in enumerate(assets):
            prices = 100 * np.cumprod(1 + returns[:, i])
            asset_data[asset] = create_test_market_data(
                ticker=asset,
                days=days,
                start_price=prices[0],
            )

        return asset_data

    @staticmethod
    def create_stress_test_scenario(
        base_data: pl.DataFrame,
        scenario_type: str = "crash",
    ) -> pl.DataFrame:
        """Create stress test scenarios for portfolio testing."""
        data = base_data.clone()

        if scenario_type == "crash":
            # Simulate market crash
            len(data) // 2
            crash_duration = 20
            crash_magnitude = -0.4

            # Apply crash to prices
            np.linspace(1.0, 1 + crash_magnitude, crash_duration)
            np.linspace(1 + crash_magnitude, 0.9, 10)

            # This is a simplified implementation
            # In practice, you'd modify the actual price columns

        elif scenario_type == "volatility_spike":
            # Increase volatility by 3x for a period
            pass

        return data


# =============================================================================
# API-specific test data factories (moved from tests/api/conftest.py)
# =============================================================================


@cached_factory()
def create_api_portfolio_data() -> dict[str, Any]:
    """
    Create sample portfolio data for API testing.
    Moved from tests/api/conftest.py to eliminate duplication.
    """
    return {
        "AAPL": {
            "symbol": "AAPL",
            "timeframe": "D",
            "ma_type": "SMA",
            "fast_period": 20,
            "slow_period": 50,
            "initial_capital": 100000,
            "allocation": 0.5,
            "num_trades": 12,
            "total_return": 0.25,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.15,
            "win_rate": 0.6,
            "avg_gain": 0.05,
            "avg_loss": -0.02,
            "expectancy": 0.03,
            "profit_factor": 2.5,
            "recovery_factor": 1.67,
            "payoff_ratio": 2.5,
            "final_balance": 125000,
            "roi": 0.25,
        },
        "MSFT": {
            "symbol": "MSFT",
            "timeframe": "D",
            "ma_type": "SMA",
            "fast_period": 20,
            "slow_period": 50,
            "initial_capital": 100000,
            "allocation": 0.5,
            "num_trades": 10,
            "total_return": 0.30,
            "sharpe_ratio": 1.8,
            "max_drawdown": -0.12,
            "win_rate": 0.65,
            "avg_gain": 0.06,
            "avg_loss": -0.018,
            "expectancy": 0.035,
            "profit_factor": 3.0,
            "recovery_factor": 2.5,
            "payoff_ratio": 3.33,
            "final_balance": 130000,
            "roi": 0.30,
        },
    }


@cached_factory()
def create_api_performance_metrics() -> dict[str, Any]:
    """
    Create sample performance metrics for API testing.
    Moved from tests/api/conftest.py to eliminate duplication.
    """
    return {
        "requests_total": 1000,
        "requests_success": 950,
        "requests_failed": 50,
        "avg_response_time": 0.5,
        "cache_hits": 400,
        "cache_misses": 600,
        "cache_hit_rate": 0.4,
        "active_tasks": 5,
        "completed_tasks": 945,
        "failed_tasks": 50,
    }
