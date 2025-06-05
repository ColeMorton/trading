"""
Test data factories for creating consistent test scenarios.
Phase 3: Testing Infrastructure Consolidation
"""

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import polars as pl


def create_test_market_data(
    ticker: str = "TEST",
    days: int = 252,
    start_price: float = 100.0,
    volatility: float = 0.2,
    trend: float = 0.1,
    start_date: Optional[datetime] = None,
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
    data = pl.DataFrame(
        {
            "Date": dates,
            "Ticker": [ticker] * days,
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": prices,
            "Volume": volumes,
            "Adj Close": prices,  # Assume no dividends/splits
        }
    )

    return data


def create_test_signals(
    num_signals: int = 50,
    ticker: str = "TEST",
    signal_types: Optional[List[str]] = None,
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
        }
    )


def create_test_portfolio(
    tickers: Optional[List[str]] = None,
    num_trades: int = 100,
    initial_capital: float = 100000.0,
) -> Dict[str, Any]:
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
            }
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


def create_test_strategy_config(
    strategy_type: str = "MA_CROSS", timeframe: str = "D"
) -> Dict[str, Any]:
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
            }
        )
    elif strategy_type == "MACD":
        base_config.update({"fast_period": 12, "slow_period": 26, "signal_period": 9})
    elif strategy_type == "RSI":
        base_config.update(
            {"rsi_period": 14, "oversold_threshold": 30, "overbought_threshold": 70}
        )

    return base_config


def create_test_backtest_results(
    config: Optional[Dict[str, Any]] = None, num_trades: int = 50
) -> Dict[str, Any]:
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


def create_test_risk_metrics() -> Dict[str, float]:
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
        assets: List[str],
        correlation_matrix: Optional[np.ndarray] = None,
        days: int = 252,
    ) -> Dict[str, pl.DataFrame]:
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
                ticker=asset, days=days, start_price=prices[0]
            )

        return asset_data

    @staticmethod
    def create_stress_test_scenario(
        base_data: pl.DataFrame, scenario_type: str = "crash"
    ) -> pl.DataFrame:
        """Create stress test scenarios for portfolio testing."""
        data = base_data.clone()

        if scenario_type == "crash":
            # Simulate market crash
            crash_start = len(data) // 2
            crash_duration = 20
            crash_magnitude = -0.4

            # Apply crash to prices
            crash_factor = np.linspace(1.0, 1 + crash_magnitude, crash_duration)
            recovery_factor = np.linspace(1 + crash_magnitude, 0.9, 10)

            # This is a simplified implementation
            # In practice, you'd modify the actual price columns

        elif scenario_type == "volatility_spike":
            # Increase volatility by 3x for a period
            pass

        return data
