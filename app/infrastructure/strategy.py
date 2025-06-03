"""Concrete implementation of strategy interfaces."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import polars as pl

from app.core.interfaces import (
    DataAccessInterface,
    LoggingInterface,
    ProgressTrackerInterface,
    StrategyAnalyzerInterface,
    StrategyConfig,
    StrategyExecutorInterface,
    StrategyResult,
)
from app.core.types import BacktestResult, StrategyParameters


class ConcreteStrategyConfig(StrategyConfig):
    """Concrete implementation of strategy configuration."""

    def __init__(self, config_dict: Dict[str, Any]):
        self._config = config_dict

    def to_dict(self) -> Dict[str, Any]:
        return self._config


class ConcreteStrategyResult(StrategyResult):
    """Concrete implementation of strategy result."""

    def __init__(
        self,
        metrics: Dict[str, float],
        signals: Union[pd.DataFrame, pl.DataFrame],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self._metrics = metrics
        self._signals = signals
        self._metadata = metadata or {}

    @property
    def metrics(self) -> Dict[str, float]:
        return self._metrics

    @property
    def signals(self) -> Union[pd.DataFrame, pl.DataFrame]:
        return self._signals


class StrategyAnalyzer(StrategyAnalyzerInterface):
    """Concrete implementation of strategy analyzer."""

    def __init__(
        self,
        data_access: DataAccessInterface,
        logger: Optional[LoggingInterface] = None,
    ):
        self._data_access = data_access
        self._logger = logger
        self._strategy_implementations = {}
        self._register_strategies()

    def analyze(
        self,
        ticker: str,
        config: StrategyConfig,
        data: Optional[Union[pd.DataFrame, pl.DataFrame]] = None,
    ) -> StrategyResult:
        """Analyze a strategy for a given ticker."""
        # Get data if not provided
        if data is None:
            data = self._data_access.get_price_data(ticker)

        # Validate configuration
        if not self.validate_config(config):
            raise ValueError("Invalid strategy configuration")

        # Get strategy implementation
        config_dict = config.to_dict() if hasattr(config, "to_dict") else {}
        strategy_type = config_dict.get("strategy_type", "ma_cross")

        if strategy_type not in self._strategy_implementations:
            raise ValueError(f"Unknown strategy type: {strategy_type}")

        # Run analysis
        implementation = self._strategy_implementations[strategy_type]
        return implementation(ticker, data, config_dict)

    def validate_config(self, config: StrategyConfig) -> bool:
        """Validate strategy configuration."""
        config_dict = config.to_dict() if hasattr(config, "to_dict") else {}

        # Check required fields
        if "strategy_type" not in config_dict:
            return False

        strategy_type = config_dict["strategy_type"]

        # Validate based on strategy type
        if strategy_type == "ma_cross":
            return all(key in config_dict for key in ["fast_period", "slow_period"])
        elif strategy_type == "macd":
            return all(
                key in config_dict
                for key in ["fast_period", "slow_period", "signal_period"]
            )
        elif strategy_type == "rsi":
            return "period" in config_dict

        return True

    def get_default_config(self) -> StrategyConfig:
        """Get default configuration for the strategy."""
        return ConcreteStrategyConfig(
            {
                "strategy_type": "ma_cross",
                "fast_period": 10,
                "slow_period": 20,
                "ma_type": "EMA",
            }
        )

    def _register_strategies(self) -> None:
        """Register strategy implementations."""
        self._strategy_implementations = {
            "ma_cross": self._analyze_ma_cross,
            "macd": self._analyze_macd,
            "rsi": self._analyze_rsi,
        }

    def _analyze_ma_cross(
        self,
        ticker: str,
        data: Union[pd.DataFrame, pl.DataFrame],
        config: Dict[str, Any],
    ) -> StrategyResult:
        """Analyze MA Cross strategy."""
        # This is a simplified implementation
        # In production, this would call the actual MA Cross analyzer

        fast_period = config.get("fast_period", 10)
        slow_period = config.get("slow_period", 20)

        # Calculate moving averages
        if isinstance(data, pl.DataFrame):
            data = data.with_columns(
                [
                    pl.col("Close")
                    .rolling_mean(fast_period)
                    .alias(f"MA_{fast_period}"),
                    pl.col("Close")
                    .rolling_mean(slow_period)
                    .alias(f"MA_{slow_period}"),
                ]
            )

            # Generate signals
            data = data.with_columns(
                [
                    pl.when(
                        (pl.col(f"MA_{fast_period}") > pl.col(f"MA_{slow_period}"))
                        & (
                            pl.col(f"MA_{fast_period}").shift(1)
                            <= pl.col(f"MA_{slow_period}").shift(1)
                        )
                    )
                    .then(1)
                    .when(
                        (pl.col(f"MA_{fast_period}") < pl.col(f"MA_{slow_period}"))
                        & (
                            pl.col(f"MA_{fast_period}").shift(1)
                            >= pl.col(f"MA_{slow_period}").shift(1)
                        )
                    )
                    .then(-1)
                    .otherwise(0)
                    .alias("Signal")
                ]
            )
        else:
            data[f"MA_{fast_period}"] = data["Close"].rolling(fast_period).mean()
            data[f"MA_{slow_period}"] = data["Close"].rolling(slow_period).mean()

            # Generate signals
            data["Signal"] = 0
            data.loc[
                (data[f"MA_{fast_period}"] > data[f"MA_{slow_period}"])
                & (
                    data[f"MA_{fast_period}"].shift(1)
                    <= data[f"MA_{slow_period}"].shift(1)
                ),
                "Signal",
            ] = 1
            data.loc[
                (data[f"MA_{fast_period}"] < data[f"MA_{slow_period}"])
                & (
                    data[f"MA_{fast_period}"].shift(1)
                    >= data[f"MA_{slow_period}"].shift(1)
                ),
                "Signal",
            ] = -1

        # Calculate basic metrics
        metrics = {
            "total_signals": (
                abs(data["Signal"]).sum()
                if isinstance(data, pd.DataFrame)
                else data.select(pl.col("Signal").abs().sum())[0, 0]
            ),
            "buy_signals": (
                (data["Signal"] == 1).sum()
                if isinstance(data, pd.DataFrame)
                else data.filter(pl.col("Signal") == 1).height
            ),
            "sell_signals": (
                (data["Signal"] == -1).sum()
                if isinstance(data, pd.DataFrame)
                else data.filter(pl.col("Signal") == -1).height
            ),
        }

        return ConcreteStrategyResult(metrics, data)

    def _analyze_macd(
        self,
        ticker: str,
        data: Union[pd.DataFrame, pl.DataFrame],
        config: Dict[str, Any],
    ) -> StrategyResult:
        """Analyze MACD strategy."""
        # Placeholder implementation
        metrics = {"total_signals": 0}
        return ConcreteStrategyResult(metrics, data)

    def _analyze_rsi(
        self,
        ticker: str,
        data: Union[pd.DataFrame, pl.DataFrame],
        config: Dict[str, Any],
    ) -> StrategyResult:
        """Analyze RSI strategy."""
        # Placeholder implementation
        metrics = {"total_signals": 0}
        return ConcreteStrategyResult(metrics, data)


class StrategyExecutor(StrategyExecutorInterface):
    """Concrete implementation of strategy executor."""

    def __init__(
        self,
        analyzer: StrategyAnalyzerInterface,
        progress_tracker: ProgressTrackerInterface,
        logger: Optional[LoggingInterface] = None,
    ):
        self._analyzer = analyzer
        self._progress_tracker = progress_tracker
        self._logger = logger

    async def execute(
        self,
        strategy_type: str,
        tickers: List[str],
        config: Dict[str, Any],
        output_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """Execute a strategy for multiple tickers."""
        task_id = f"{strategy_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Use progress tracking
        return await self.execute_with_progress(
            strategy_type, tickers, config, task_id, self._progress_tracker
        )

    async def execute_with_progress(
        self,
        strategy_type: str,
        tickers: List[str],
        config: Dict[str, Any],
        task_id: str,
        progress_tracker: ProgressTrackerInterface,
    ) -> Dict[str, Any]:
        """Execute a strategy with progress tracking."""
        # Start tracking
        await progress_tracker.track(
            task_id,
            f"Executing {strategy_type} strategy for {len(tickers)} tickers",
            len(tickers),
        )

        results = {}
        errors = []

        # Process each ticker
        for i, ticker in enumerate(tickers):
            try:
                # Update progress
                progress = (i / len(tickers)) * 100
                await progress_tracker.update(
                    task_id, progress, f"Processing {ticker} ({i+1}/{len(tickers)})"
                )

                # Create strategy config
                strategy_config = ConcreteStrategyConfig(
                    {"strategy_type": strategy_type, **config}
                )

                # Analyze strategy
                result = self._analyzer.analyze(ticker, strategy_config)

                results[ticker] = {
                    "metrics": result.metrics,
                    "signal_count": result.metrics.get("total_signals", 0),
                }

            except Exception as e:
                if self._logger:
                    self._logger.get_logger(__name__).error(
                        f"Error processing {ticker}: {e}"
                    )
                errors.append({"ticker": ticker, "error": str(e)})

        # Complete tracking
        if errors:
            await progress_tracker.complete(
                task_id, f"Completed with {len(errors)} errors"
            )
        else:
            await progress_tracker.complete(task_id)

        return {
            "task_id": task_id,
            "strategy_type": strategy_type,
            "results": results,
            "errors": errors,
            "summary": {
                "total_tickers": len(tickers),
                "successful": len(results),
                "failed": len(errors),
            },
        }

    def get_supported_strategies(self) -> List[str]:
        """Get list of supported strategy types."""
        return ["ma_cross", "macd", "rsi", "mean_reversion", "range"]

    def validate_parameters(self, strategy_type: str, config: Dict[str, Any]) -> bool:
        """Validate parameters for a specific strategy."""
        # Create temporary config and validate
        strategy_config = ConcreteStrategyConfig(
            {"strategy_type": strategy_type, **config}
        )

        return self._analyzer.validate_config(strategy_config)
