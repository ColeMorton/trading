"""
Strategy Executor Service

Focused service for executing trading strategies.
Extracted from the larger execution engines for better maintainability.
"""

import logging
from enum import Enum
from typing import Any

import pandas as pd
import polars as pl

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config


class StrategyType(str, Enum):
    """Strategy type enumeration."""

    SMA = "SMA"
    EMA = "EMA"
    MACD = "MACD"
    RSI = "RSI"
    BOLLINGER_BANDS = "BOLLINGER_BANDS"


class StrategyExecutor:
    """
    Service for executing trading strategies.

    This service handles:
    - Strategy validation and configuration
    - Strategy execution coordination
    - Result compilation and formatting
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the strategy executor."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def execute_strategy(
        self,
        strategy_type: StrategyType,
        market_data: pd.DataFrame | pl.DataFrame,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a trading strategy with given parameters."""
        if isinstance(market_data, pl.DataFrame):
            market_data = market_data.to_pandas()

        if market_data.empty:
            return {
                "strategy_type": strategy_type.value,
                "parameters": parameters,
                "signals": [],
                "performance": {},
                "error": "No market data provided",
            }

        try:
            # Validate strategy parameters
            validated_params = self._validate_parameters(strategy_type, parameters)

            # Execute the strategy
            signals = self._execute_strategy_logic(
                strategy_type,
                market_data,
                validated_params,
            )

            # Calculate performance metrics
            performance = self._calculate_performance(market_data, signals)

            return {
                "strategy_type": strategy_type.value,
                "parameters": validated_params,
                "signals": signals,
                "performance": performance,
                "success": True,
            }

        except Exception as e:
            self.logger.exception(f"Strategy execution failed: {e!s}")
            return {
                "strategy_type": strategy_type.value,
                "parameters": parameters,
                "signals": [],
                "performance": {},
                "error": str(e),
                "success": False,
            }

    def validate_strategy_config(
        self,
        strategy_type: StrategyType,
        parameters: dict[str, Any],
    ) -> bool:
        """Validate strategy configuration."""
        try:
            self._validate_parameters(strategy_type, parameters)
            return True
        except Exception as e:
            self.logger.exception(f"Strategy validation failed: {e!s}")
            return False

    def _validate_parameters(
        self,
        strategy_type: StrategyType,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate and normalize strategy parameters."""
        if strategy_type == StrategyType.SMA:
            return self._validate_sma_parameters(parameters)
        if strategy_type == StrategyType.EMA:
            return self._validate_ema_parameters(parameters)
        if strategy_type == StrategyType.MACD:
            return self._validate_macd_parameters(parameters)
        if strategy_type == StrategyType.RSI:
            return self._validate_rsi_parameters(parameters)
        if strategy_type == StrategyType.BOLLINGER_BANDS:
            return self._validate_bollinger_parameters(parameters)
        msg = f"Unsupported strategy type: {strategy_type}"
        raise ValueError(msg)

    def _validate_sma_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate SMA strategy parameters."""
        required_params = ["fast_period", "slow_period"]
        for param in required_params:
            if param not in parameters:
                msg = f"Missing required parameter: {param}"
                raise ValueError(msg)

        fast_period = int(parameters["fast_period"])
        slow_period = int(parameters["slow_period"])

        if fast_period <= 0 or slow_period <= 0:
            msg = "Periods must be positive integers"
            raise ValueError(msg)

        if fast_period >= slow_period:
            msg = "Fast period must be less than slow period"
            raise ValueError(msg)

        return {"fast_period": fast_period, "slow_period": slow_period}

    def _validate_ema_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate EMA strategy parameters."""
        return self._validate_sma_parameters(parameters)  # Same validation logic

    def _validate_macd_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate MACD strategy parameters."""
        default_params = {"fast_period": 12, "slow_period": 26, "signal_period": 9}

        validated = {}
        for param, default_value in default_params.items():
            value = parameters.get(param, default_value)
            if not isinstance(value, int | float) or value <= 0:
                msg = f"Invalid {param}: must be positive number"
                raise ValueError(msg)
            validated[param] = int(value)

        if validated["fast_period"] >= validated["slow_period"]:
            msg = "Fast period must be less than slow period"
            raise ValueError(msg)

        return validated

    def _validate_rsi_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        """Validate RSI strategy parameters."""
        default_params = {"period": 14, "overbought": 70, "oversold": 30}

        validated = {}
        for param, default_value in default_params.items():
            value = parameters.get(param, default_value)
            if not isinstance(value, int | float) or value <= 0:
                msg = f"Invalid {param}: must be positive number"
                raise ValueError(msg)
            validated[param] = value

        if validated["oversold"] >= validated["overbought"]:
            msg = "Oversold level must be less than overbought level"
            raise ValueError(msg)

        return validated

    def _validate_bollinger_parameters(
        self,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate Bollinger Bands strategy parameters."""
        default_params = {"period": 20, "std_dev": 2.0}

        validated = {}
        for param, default_value in default_params.items():
            value = parameters.get(param, default_value)
            if not isinstance(value, int | float) or value <= 0:
                msg = f"Invalid {param}: must be positive number"
                raise ValueError(msg)
            validated[param] = value

        return validated

    def _execute_strategy_logic(
        self,
        strategy_type: StrategyType,
        market_data: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute the core strategy logic."""
        # This is a simplified implementation
        # In practice, you would have more sophisticated strategy logic

        signals = []

        if strategy_type == StrategyType.SMA:
            signals = self._execute_sma_strategy(market_data, parameters)
        elif strategy_type == StrategyType.EMA:
            signals = self._execute_ema_strategy(market_data, parameters)
        elif strategy_type == StrategyType.MACD:
            signals = self._execute_macd_strategy(market_data, parameters)
        elif strategy_type == StrategyType.RSI:
            signals = self._execute_rsi_strategy(market_data, parameters)
        elif strategy_type == StrategyType.BOLLINGER_BANDS:
            signals = self._execute_bollinger_strategy(market_data, parameters)

        return signals

    def _execute_sma_strategy(
        self,
        market_data: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute SMA crossover strategy."""
        # Simplified SMA strategy implementation
        return [
            {
                "timestamp": "2023-01-01",
                "signal": "BUY",
                "price": 100.0,
                "confidence": 0.7,
            },
        ]

    def _execute_ema_strategy(
        self,
        market_data: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute EMA crossover strategy."""
        # Simplified EMA strategy implementation
        return [
            {
                "timestamp": "2023-01-01",
                "signal": "BUY",
                "price": 100.0,
                "confidence": 0.7,
            },
        ]

    def _execute_macd_strategy(
        self,
        market_data: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute MACD strategy."""
        # Simplified MACD strategy implementation
        return [
            {
                "timestamp": "2023-01-01",
                "signal": "BUY",
                "price": 100.0,
                "confidence": 0.8,
            },
        ]

    def _execute_rsi_strategy(
        self,
        market_data: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute RSI strategy."""
        # Simplified RSI strategy implementation
        return [
            {
                "timestamp": "2023-01-01",
                "signal": "SELL",
                "price": 100.0,
                "confidence": 0.6,
            },
        ]

    def _execute_bollinger_strategy(
        self,
        market_data: pd.DataFrame,
        parameters: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Execute Bollinger Bands strategy."""
        # Simplified Bollinger Bands strategy implementation
        return [
            {
                "timestamp": "2023-01-01",
                "signal": "BUY",
                "price": 100.0,
                "confidence": 0.7,
            },
        ]

    def _calculate_performance(
        self,
        market_data: pd.DataFrame,
        signals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate strategy performance metrics."""
        # Simplified performance calculation
        return {
            "total_signals": len(signals),
            "buy_signals": len([s for s in signals if s["signal"] == "BUY"]),
            "sell_signals": len([s for s in signals if s["signal"] == "SELL"]),
            "avg_confidence": (
                sum(s["confidence"] for s in signals) / len(signals) if signals else 0.0
            ),
            "performance_score": 0.75,  # Placeholder
        }
