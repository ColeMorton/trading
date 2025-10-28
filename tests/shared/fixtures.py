"""
Shared test fixtures for trading system testing infrastructure.
Phase 3: Testing Infrastructure Consolidation
"""

from collections.abc import Generator
from pathlib import Path
import tempfile
from typing import Any

import pandas as pd
import polars as pl


def mock_yfinance_data(ticker: str = "TEST", days: int = 100) -> pd.DataFrame:
    """
    Create mock yfinance data for testing.

    Args:
        ticker: Stock ticker symbol
        days: Number of days of data

    Returns:
        Pandas DataFrame mimicking yfinance structure
    """
    from datetime import datetime, timedelta

    import numpy as np

    # Generate dates
    dates = pd.date_range(
        start=datetime.now() - timedelta(days=days), periods=days, freq="D",
    )

    # Generate realistic OHLCV data
    base_price = 100.0
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * np.cumprod(1 + returns)

    # Create OHLC from close prices
    opens = np.roll(prices, 1)
    opens[0] = base_price

    highs = prices * (1 + np.abs(np.random.normal(0, 0.01, days)))
    lows = prices * (1 - np.abs(np.random.normal(0, 0.01, days)))

    # Ensure OHLC relationships
    highs = np.maximum(highs, np.maximum(opens, prices))
    lows = np.minimum(lows, np.minimum(opens, prices))

    volumes = np.random.lognormal(15, 0.5, days).astype(int)

    # Create DataFrame with multi-level columns (yfinance format)
    data = pd.DataFrame(
        {
            ("Open", ticker): opens,
            ("High", ticker): highs,
            ("Low", ticker): lows,
            ("Close", ticker): prices,
            ("Adj Close", ticker): prices,
            ("Volume", ticker): volumes,
        },
        index=dates,
    )

    # Set column names
    data.columns = pd.MultiIndex.from_tuples(data.columns)

    return data


def temp_csv_file(
    data: pl.DataFrame, filename: str = "test_data.csv",
) -> Generator[Path, None, None]:
    """
    Create temporary CSV file for testing.

    Args:
        data: Polars DataFrame to write
        filename: Name of the temporary file

    Yields:
        Path to temporary CSV file
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / filename
        data.write_csv(file_path)
        yield file_path


def test_database_session():
    """
    Create test database session.

    Returns:
        Mock database session for testing
    """

    class MockDBSession:
        def __init__(self):
            self.data = {}
            self.committed = False
            self.rolled_back = False

        def add(self, obj):
            """Add object to session."""
            if not hasattr(obj, "id"):
                obj.id = len(self.data) + 1
            self.data[obj.id] = obj

        def commit(self):
            """Commit transaction."""
            self.committed = True

        def rollback(self):
            """Rollback transaction."""
            self.data.clear()
            self.rolled_back = True

        def query(self, model):
            """Query objects."""
            return MockQuery(self.data, model)

        def close(self):
            """Close session."""

    class MockQuery:
        def __init__(self, data, model):
            self.data = data
            self.model = model

        def filter(self, *args):
            """Filter query."""
            return self

        def first(self):
            """Get first result."""
            if self.data:
                return next(iter(self.data.values()))
            return None

        def all(self):
            """Get all results."""
            return list(self.data.values())

        def count(self):
            """Count results."""
            return len(self.data)

    return MockDBSession()


def mock_strategy_executor():
    """
    Create mock strategy executor for testing.

    Returns:
        Mock strategy executor
    """

    class MockStrategyExecutor:
        def __init__(self):
            self.executed_strategies = []
            self.results = {}

        def execute(self, strategy_config: dict[str, Any]) -> dict[str, Any]:
            """Execute strategy with mock results."""
            strategy_id = strategy_config.get("strategy_id", "test_strategy")
            self.executed_strategies.append(strategy_config)

            # Generate mock results
            mock_result = {
                "strategy_id": strategy_id,
                "total_return": 0.15,
                "sharpe_ratio": 1.2,
                "max_drawdown": 0.08,
                "win_rate": 0.65,
                "num_trades": 50,
                "execution_time": 1.5,
            }

            self.results[strategy_id] = mock_result
            return mock_result

        def get_result(self, strategy_id: str) -> dict[str, Any]:
            """Get strategy execution result."""
            return self.results.get(strategy_id, {})

        def clear_results(self):
            """Clear all results."""
            self.executed_strategies.clear()
            self.results.clear()

    return MockStrategyExecutor()


def mock_data_provider():
    """
    Create mock data provider for testing.

    Returns:
        Mock data provider
    """

    class MockDataProvider:
        def __init__(self):
            self.cache = {}

        def get_price_data(
            self, ticker: str, period: str = "1y", interval: str = "1d",
        ) -> pl.DataFrame:
            """Get mock price data."""
            cache_key = f"{ticker}_{period}_{interval}"

            if cache_key not in self.cache:
                from .factories import create_test_market_data

                # Convert period to days
                days_map = {"1y": 252, "6mo": 126, "3mo": 63, "1mo": 21}
                days = days_map.get(period, 252)

                self.cache[cache_key] = create_test_market_data(
                    ticker=ticker, days=days,
                )

            return self.cache[cache_key]

        def get_fundamentals(self, ticker: str) -> dict[str, Any]:
            """Get mock fundamental data."""
            return {
                "market_cap": 1_000_000_000,
                "pe_ratio": 15.5,
                "debt_to_equity": 0.3,
                "roe": 0.18,
                "revenue_growth": 0.12,
                "profit_margin": 0.15,
            }

        def clear_cache(self):
            """Clear data cache."""
            self.cache.clear()

    return MockDataProvider()


def mock_risk_calculator():
    """
    Create mock risk calculator for testing.

    Returns:
        Mock risk calculator
    """

    class MockRiskCalculator:
        def calculate_var(
            self, returns: pl.Series, confidence_level: float = 0.95,
        ) -> float:
            """Calculate Value at Risk."""
            import numpy as np

            return np.percentile(returns.to_numpy(), (1 - confidence_level) * 100)

        def calculate_cvar(
            self, returns: pl.Series, confidence_level: float = 0.95,
        ) -> float:
            """Calculate Conditional Value at Risk."""
            var = self.calculate_var(returns, confidence_level)
            return returns.filter(returns <= var).mean()

        def calculate_sharpe_ratio(
            self, returns: pl.Series, risk_free_rate: float = 0.02,
        ) -> float:
            """Calculate Sharpe ratio."""
            excess_returns = returns.mean() - risk_free_rate / 252
            return excess_returns / returns.std()

        def calculate_max_drawdown(self, prices: pl.Series) -> float:
            """Calculate maximum drawdown."""
            import numpy as np

            peak = np.maximum.accumulate(prices.to_numpy())
            drawdown = (prices.to_numpy() - peak) / peak
            return abs(drawdown.min())

    return MockRiskCalculator()


def mock_portfolio_optimizer():
    """
    Create mock portfolio optimizer for testing.

    Returns:
        Mock portfolio optimizer
    """

    class MockPortfolioOptimizer:
        def optimize_weights(
            self,
            expected_returns: pl.Series,
            cov_matrix: pl.DataFrame,
            risk_aversion: float = 1.0,
        ) -> pl.Series:
            """Optimize portfolio weights."""
            # Simple equal weight allocation for testing
            n_assets = len(expected_returns)
            return pl.Series([1.0 / n_assets] * n_assets)

        def calculate_efficient_frontier(
            self,
            expected_returns: pl.Series,
            cov_matrix: pl.DataFrame,
            num_points: int = 100,
        ) -> dict[str, pl.Series]:
            """Calculate efficient frontier."""
            # Mock efficient frontier
            risk_levels = pl.Series(range(num_points)) / num_points * 0.3
            return_levels = risk_levels * 2  # Mock risk-return relationship

            return {"risk": risk_levels, "return": return_levels}

    return MockPortfolioOptimizer()


class MockAPIClient:
    """Mock API client for testing external API calls."""

    def __init__(self):
        self.requests = []
        self.responses = {}

    def get(self, url: str, **kwargs) -> dict[str, Any]:
        """Mock GET request."""
        self.requests.append({"method": "GET", "url": url, "kwargs": kwargs})

        # Return mock response based on URL
        if "market_data" in url:
            return {"status": "success", "data": mock_yfinance_data()}
        if "strategy" in url:
            return {"status": "success", "data": {"result": "executed"}}
        return {"status": "success", "data": {}}

    def post(
        self, url: str, data: dict[str, Any] | None = None, **kwargs,
    ) -> dict[str, Any]:
        """Mock POST request."""
        self.requests.append(
            {"method": "POST", "url": url, "data": data, "kwargs": kwargs},
        )

        return {"status": "success", "data": {"id": "test_execution_123"}}

    def set_response(self, url_pattern: str, response: dict[str, Any]):
        """Set custom response for URL pattern."""
        self.responses[url_pattern] = response

    def clear_requests(self):
        """Clear request history."""
        self.requests.clear()


def mock_cache_service():
    """
    Create mock cache service for testing.

    Returns:
        Mock cache service
    """

    class MockCacheService:
        def __init__(self):
            self._cache = {}

        def get(self, key: str) -> Any:
            """Get value from cache."""
            return self._cache.get(key)

        def set(self, key: str, value: Any, ttl: int = 3600):
            """Set value in cache."""
            self._cache[key] = value

        def delete(self, key: str):
            """Delete value from cache."""
            self._cache.pop(key, None)

        def clear(self):
            """Clear entire cache."""
            self._cache.clear()

        def exists(self, key: str) -> bool:
            """Check if key exists in cache."""
            return key in self._cache

    return MockCacheService()
