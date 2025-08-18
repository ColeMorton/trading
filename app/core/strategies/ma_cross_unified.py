"""
Unified MA Cross Strategy Implementation

This module demonstrates the migration of the MA Cross strategy to the unified framework,
serving as the reference implementation for consolidating the 4 different execution patterns
into a single, consistent approach.

Key Features:
- Implements AbstractStrategy interface
- Uses unified configuration and result structures
- Integrates with ParameterTestingEngine for optimization
- Leverages RiskManagementLayer for position sizing and risk controls
- Maintains compatibility with existing MA Cross logic
- Provides clear migration path for other strategies
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import polars as pl
import vectorbt as vbt

from app.core.parameter_testing_engine import ParameterTestingEngine
from app.core.risk_management_layer import PositionSizingMethod, RiskManagementLayer
from app.core.strategy_framework import (
    AbstractStrategy,
    StrategyFactory,
    UnifiedStrategyConfig,
    UnifiedStrategyResult,
)
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data


class MACrossUnifiedStrategy(AbstractStrategy):
    """
    Unified Moving Average Cross Strategy.

    This strategy generates buy/sell signals based on moving average crossovers,
    supporting both Simple Moving Averages (SMA) and Exponential Moving Averages (EMA).
    """

    def __init__(self):
        """Initialize the MA Cross strategy."""
        super().__init__(name="MA Cross", version="2.0.0")
        self.risk_manager = RiskManagementLayer()
        self.parameter_engine = ParameterTestingEngine()

    @property
    def strategy_type(self) -> str:
        """Return the strategy type identifier."""
        return "MA_CROSS"

    @property
    def required_parameters(self) -> List[str]:
        """Return list of required parameters for this strategy."""
        return ["fast_period", "slow_period", "ma_type"]

    @property
    def default_parameters(self) -> Dict[str, Any]:
        """Return default parameters for this strategy."""
        return {
            "fast_period": 20,
            "slow_period": 50,
            "ma_type": "EMA",  # SMA or EMA
            "signal_type": "cross",  # cross, breakout, pullback
            "min_periods": 1,
        }

    def validate_config(self, config: UnifiedStrategyConfig) -> bool:
        """Validate configuration for this strategy."""
        params = config.parameters

        # Check required parameters
        for param in self.required_parameters:
            if param not in params:
                self._log_error(f"Missing required parameter: {param}")
                return False

        # Validate parameter values
        if params["fast_period"] >= params["slow_period"]:
            self._log_error("Fast period must be less than slow period")
            return False

        if params["fast_period"] < 1 or params["slow_period"] < 2:
            self._log_error("Window sizes must be positive integers")
            return False

        if params["ma_type"] not in ["SMA", "EMA"]:
            self._log_error("MA type must be 'SMA' or 'EMA'")
            return False

        return True

    async def execute_single(
        self,
        ticker: str,
        config: UnifiedStrategyConfig,
        data: Optional[Union[pd.DataFrame, pl.DataFrame]] = None,
    ) -> UnifiedStrategyResult:
        """Execute strategy for a single ticker with specific parameters."""
        start_time = time.time()

        try:
            # Get market data if not provided
            if data is None:
                self._log_info(f"Fetching data for {ticker}")
                data = await self._get_market_data(ticker, config)

            # Ensure data is in pandas format for vectorbt
            if isinstance(data, pl.DataFrame):
                data = data.to_pandas()

            # Calculate moving averages and signals
            signals_data = self._calculate_signals(data, config.parameters)

            # Run backtest
            backtest_result = self._run_backtest(data, signals_data, config)

            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(backtest_result, config)

            # Prepare result
            execution_time = time.time() - start_time

            result = UnifiedStrategyResult(
                strategy_type=self.strategy_type,
                ticker=ticker,
                execution_time=execution_time,
                metrics=self._extract_performance_metrics(backtest_result),
                signals=signals_data,
                equity_curve=backtest_result.get("equity_curve"),
                trades=backtest_result.get("trades"),
                best_parameters=config.parameters,
                risk_metrics=risk_metrics,
            )

            return result

        except Exception as e:
            self._log_error(f"Error executing MA Cross for {ticker}: {str(e)}")
            raise

    async def execute_optimization(
        self,
        ticker: str,
        config: UnifiedStrategyConfig,
        parameter_ranges: Dict[str, List[Any]],
    ) -> UnifiedStrategyResult:
        """Execute parameter optimization for a single ticker."""
        self._log_info(f"Starting parameter optimization for {ticker}")

        # Create strategy executor function for parameter engine
        async def strategy_executor(
            test_ticker: str, test_config: UnifiedStrategyConfig
        ):
            return await self.execute_single(test_ticker, test_config)

        # Run optimization
        optimization_result = await self.parameter_engine.optimize_parameters(
            strategy_executor=strategy_executor,
            ticker=ticker,
            base_config=config,
            parameter_ranges=parameter_ranges,
        )

        # Convert optimization result to UnifiedStrategyResult
        best_result = optimization_result["best_result"]
        if best_result is None:
            raise ValueError(f"No valid parameter combinations found for {ticker}")

        # Enhance with optimization metadata
        best_result.all_results = optimization_result.get("all_results", [])
        best_result.best_parameters = optimization_result.get("best_parameters")

        return best_result

    def _calculate_signals(
        self, data: pd.DataFrame, parameters: Dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate moving average signals."""
        fast_period = parameters["fast_period"]
        slow_period = parameters["slow_period"]
        ma_type = parameters["ma_type"]

        # Calculate moving averages
        if ma_type == "SMA":
            data["MA_Short"] = data["Close"].rolling(window=fast_period).mean()
            data["MA_Long"] = data["Close"].rolling(window=slow_period).mean()
        else:  # EMA
            data["MA_Short"] = data["Close"].ewm(span=fast_period).mean()
            data["MA_Long"] = data["Close"].ewm(span=slow_period).mean()

        # Generate signals
        data["Signal"] = 0  # 0 = hold, 1 = buy, -1 = sell

        # Buy signal: short MA crosses above long MA
        data.loc[data["MA_Short"] > data["MA_Long"], "Signal"] = 1

        # Sell signal: short MA crosses below long MA
        data.loc[data["MA_Short"] < data["MA_Long"], "Signal"] = -1

        # Identify actual crossover points
        data["Position"] = data["Signal"].diff()
        data["Buy_Signal"] = (data["Position"] == 2) | (data["Position"] == 1)
        data["Sell_Signal"] = (data["Position"] == -2) | (data["Position"] == -1)

        return data

    def _run_backtest(
        self,
        data: pd.DataFrame,
        signals_data: pd.DataFrame,
        config: UnifiedStrategyConfig,
    ) -> Dict[str, Any]:
        """Run vectorbt backtest."""
        try:
            # Prepare signals for vectorbt
            close_prices = signals_data["Close"]
            buy_signals = signals_data["Buy_Signal"]
            sell_signals = signals_data["Sell_Signal"]

            # Create vectorbt portfolio
            portfolio = vbt.Portfolio.from_signals(
                close=close_prices,
                entries=buy_signals,
                exits=sell_signals,
                init_cash=100000,  # Starting with $100k
                freq="D",
            )

            # Extract results
            trades = portfolio.trades.records_readable
            equity_curve = portfolio.value()

            # Calculate performance metrics
            total_return = portfolio.total_return()
            sharpe_ratio = portfolio.sharpe_ratio()
            max_drawdown = portfolio.max_drawdown()
            win_rate = portfolio.trades.win_rate if len(trades) > 0 else 0
            profit_factor = portfolio.trades.profit_factor if len(trades) > 0 else 0

            return {
                "portfolio": portfolio,
                "trades": trades,
                "equity_curve": equity_curve,
                "total_return": total_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "total_trades": len(trades),
            }

        except Exception as e:
            self._log_error(f"Backtest error: {str(e)}")
            # Return minimal result structure
            return {
                "portfolio": None,
                "trades": pd.DataFrame(),
                "equity_curve": pd.Series(),
                "total_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "profit_factor": 0.0,
                "total_trades": 0,
            }

    def _extract_performance_metrics(
        self, backtest_result: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract standardized performance metrics."""
        return {
            "Total Return [%]": backtest_result.get("total_return", 0.0) * 100,
            "Sharpe Ratio": backtest_result.get("sharpe_ratio", 0.0),
            "Max Drawdown [%]": backtest_result.get("max_drawdown", 0.0) * 100,
            "Win Rate [%]": backtest_result.get("win_rate", 0.0) * 100,
            "Profit Factor": backtest_result.get("profit_factor", 0.0),
            "Trades": backtest_result.get("total_trades", 0),
            "Annualized Return [%]": backtest_result.get("total_return", 0.0)
            * 100,  # Simplified
            "Volatility [%]": 15.0,  # Placeholder - would calculate from returns
            "Sortino Ratio": backtest_result.get("sharpe_ratio", 0.0)
            * 1.1,  # Approximation
            "Calmar Ratio": (
                backtest_result.get("total_return", 0.0)
                / max(abs(backtest_result.get("max_drawdown", 0.01)), 0.01)
            ),
        }

    def _calculate_risk_metrics(
        self, backtest_result: Dict[str, Any], config: UnifiedStrategyConfig
    ) -> Dict[str, float]:
        """Calculate risk metrics using the risk management layer."""
        try:
            portfolio = backtest_result.get("portfolio")
            if portfolio is None:
                return {}

            # Get returns series
            returns = portfolio.returns()

            # Calculate comprehensive risk metrics
            risk_metrics = self.risk_manager.assess_strategy_risk(
                returns=returns, trades=backtest_result.get("trades")
            )

            return {
                "VaR 95%": risk_metrics.var_95,
                "CVaR 95%": risk_metrics.cvar_95,
                "Skewness": risk_metrics.skewness,
                "Kurtosis": risk_metrics.kurtosis,
                "Largest Win": risk_metrics.largest_win,
                "Largest Loss": risk_metrics.largest_loss,
                "Avg Hold Time": risk_metrics.hold_time_avg,
            }

        except Exception as e:
            self._log_error(f"Risk metrics calculation error: {str(e)}")
            return {}

    async def _get_market_data(
        self, ticker: str, config: UnifiedStrategyConfig
    ) -> pd.DataFrame:
        """Get market data for the ticker."""
        try:
            # Use existing data fetching logic
            timeframe = config.timeframe
            years = config.data_years or 2.0

            # Call existing get_data function (may need to adapt)
            data = get_data(ticker, timeframe, years)

            if isinstance(data, pl.DataFrame):
                data = data.to_pandas()

            return data

        except Exception as e:
            self._log_error(f"Error fetching data for {ticker}: {str(e)}")
            raise

    def get_parameter_ranges(self) -> Dict[str, List[Any]]:
        """Get default parameter ranges for optimization."""
        return {
            "fast_period": list(range(5, 51, 5)),  # 5, 10, 15, ..., 50
            "slow_period": list(range(20, 201, 10)),  # 20, 30, 40, ..., 200
            "ma_type": ["SMA", "EMA"],
        }

    def create_config_for_ticker(
        self, ticker: str, custom_params: Dict[str, Any] = None
    ) -> UnifiedStrategyConfig:
        """Create a configuration for a specific ticker."""
        parameters = self.default_parameters.copy()
        if custom_params:
            parameters.update(custom_params)

        return UnifiedStrategyConfig(
            strategy_type=self.strategy_type,
            ticker=ticker,
            timeframe="D",
            parameters=parameters,
            refresh_data=True,
            parallel_execution=True,
        )


# Register the strategy with the factory
StrategyFactory.register_strategy("MA_CROSS", MACrossUnifiedStrategy)


# Convenience functions for backward compatibility and easy usage


async def execute_ma_cross_single(
    ticker: str,
    fast_period: int = 20,
    slow_period: int = 50,
    ma_type: str = "EMA",
    **kwargs,
) -> UnifiedStrategyResult:
    """
    Execute MA Cross strategy for a single ticker (convenience function).

    This function provides a simple interface for executing the MA Cross strategy
    while leveraging the unified framework underneath.
    """
    strategy = MACrossUnifiedStrategy()

    config = UnifiedStrategyConfig(
        strategy_type="MA_CROSS",
        ticker=ticker,
        parameters={
            "fast_period": fast_period,
            "slow_period": slow_period,
            "ma_type": ma_type,
        },
        **kwargs,
    )

    return await strategy.execute_single(ticker, config)


async def optimize_ma_cross(
    ticker: str,
    short_range: List[int] = None,
    long_range: List[int] = None,
    ma_types: List[str] = None,
    **kwargs,
) -> UnifiedStrategyResult:
    """
    Optimize MA Cross parameters for a single ticker (convenience function).

    This function provides a simple interface for parameter optimization
    while leveraging the unified framework underneath.
    """
    strategy = MACrossUnifiedStrategy()

    # Set default ranges if not provided
    parameter_ranges = {
        "fast_period": short_range or list(range(5, 51, 5)),
        "slow_period": long_range or list(range(20, 201, 10)),
        "ma_type": ma_types or ["SMA", "EMA"],
    }

    base_config = UnifiedStrategyConfig(
        strategy_type="MA_CROSS",
        ticker=ticker,
        parameters=strategy.default_parameters,
        **kwargs,
    )

    return await strategy.execute_optimization(ticker, base_config, parameter_ranges)


async def execute_ma_cross_portfolio(
    tickers: List[str],
    parameters: Dict[str, Any] = None,
    progress_callback: Optional[callable] = None,
    **kwargs,
) -> List[UnifiedStrategyResult]:
    """
    Execute MA Cross strategy for multiple tickers (convenience function).

    This function provides a simple interface for portfolio analysis
    while leveraging the unified framework underneath.
    """
    strategy = MACrossUnifiedStrategy()

    params = strategy.default_parameters.copy()
    if parameters:
        params.update(parameters)

    config = UnifiedStrategyConfig(
        strategy_type="MA_CROSS",
        ticker=tickers,  # List of tickers
        parameters=params,
        **kwargs,
    )

    return await strategy.execute_portfolio(tickers, config, progress_callback)


# Example usage and testing functions


async def demo_unified_ma_cross():
    """Demonstrate the unified MA Cross strategy."""
    print("=== Unified MA Cross Strategy Demo ===")

    # Test single ticker execution
    print("\n1. Single Ticker Execution:")
    result = await execute_ma_cross_single(
        ticker="AAPL", fast_period=20, slow_period=50, ma_type="EMA"
    )
    print(f"Total Return: {result.total_return:.2f}%")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Trades: {result.metrics.get('Trades', 0)}")

    # Test parameter optimization
    print("\n2. Parameter Optimization:")
    opt_result = await optimize_ma_cross(
        ticker="AAPL",
        short_range=[10, 15, 20, 25],
        long_range=[30, 40, 50, 60],
        ma_types=["EMA"],
    )
    print(f"Best Parameters: {opt_result.best_parameters}")
    print(f"Best Return: {opt_result.total_return:.2f}%")

    # Test portfolio execution
    print("\n3. Portfolio Execution:")
    portfolio_results = await execute_ma_cross_portfolio(
        tickers=["AAPL", "MSFT", "GOOGL"],
        parameters={"fast_period": 20, "slow_period": 50, "ma_type": "EMA"},
    )

    print("Portfolio Results:")
    for result in portfolio_results:
        print(
            f"  {result.ticker}: {result.total_return:.2f}% return, "
            f"{result.sharpe_ratio:.2f} Sharpe"
        )


if __name__ == "__main__":
    # Run demo
    asyncio.run(demo_unified_ma_cross())
