"""
Unified Strategy Implementations

This module contains concrete implementations of all trading strategies
that inherit from the BaseStrategy abstract class and implement the
StrategyInterface for consistency across the trading system.
"""

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List

import polars as pl

from app.core.interfaces.strategy import StrategyInterface

# Import calculation utilities
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_rsi import calculate_rsi
from app.tools.exceptions import StrategyError
from app.tools.signal_conversion import convert_signals_to_positions
from app.tools.strategy.base import BaseStrategy


class UnifiedMAStrategy(BaseStrategy, StrategyInterface):
    """
    Unified Moving Average Strategy supporting both SMA and EMA crossover strategies.

    This strategy consolidates the MA Cross strategy logic and can be configured
    for either Simple Moving Average (SMA) or Exponential Moving Average (EMA).
    """

    def __init__(self, ma_type: str = "SMA"):
        """
        Initialize the MA strategy.

        Args:
            ma_type: Type of moving average - "SMA" or "EMA"
        """
        if ma_type not in ["SMA", "EMA"]:
            raise ValueError(f"Invalid MA type: {ma_type}. Must be 'SMA' or 'EMA'")
        self.ma_type = ma_type

    def calculate(
        self,
        data: pl.DataFrame,
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate MA crossover signals and positions.

        Args:
            data: Input price data
            short_window: Short MA period
            long_window: Long MA period
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with MA signals and positions
        """
        # Validate inputs
        if not self.validate_windows(short_window, long_window, log):
            raise ValueError("Invalid window parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        use_sma = self.ma_type == "SMA"

        log(
            f"Calculating {direction} {self.ma_type}s and signals with short window {short_window} and long window {long_window}"
        )

        try:
            # Calculate moving averages
            data = calculate_mas(data, short_window, long_window, use_sma, log)

            # Calculate RSI if enabled
            if config.get("USE_RSI", False):
                rsi_period = config.get("RSI_WINDOW", 14)
                data = calculate_rsi(data, rsi_period)
                log(f"Calculated RSI with period {rsi_period}", "info")

            # Generate signals based on MA crossovers
            entries, exits = calculate_ma_signals(data, config)

            # Add Signal column (-1 for short entry, 1 for long entry, 0 for no signal)
            if config.get("DIRECTION", "Long") == "Short":
                data = data.with_columns(
                    [pl.when(entries).then(-1).otherwise(0).alias("Signal")]
                )
            else:
                data = data.with_columns(
                    [pl.when(entries).then(1).otherwise(0).alias("Signal")]
                )

            # Convert signals to positions with audit trail
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = self.ma_type
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window

            data = convert_signals_to_positions(
                data=data, config=strategy_config, log=log
            )

            return data

        except Exception as e:
            log(
                f"Failed to calculate {direction} {self.ma_type}s and signals: {e}",
                "error",
            )
            raise

    def validate_parameters(self, config: Dict[str, Any]) -> bool:
        """Validate strategy-specific parameters."""
        required_params = ["SHORT_WINDOW", "LONG_WINDOW"]

        for param in required_params:
            if param not in config:
                return False
            if not isinstance(config[param], int) or config[param] <= 0:
                return False

        if config["SHORT_WINDOW"] >= config["LONG_WINDOW"]:
            return False

        return True

    def execute(self, config: Dict[str, Any], log: Any) -> List[Dict[str, Any]]:
        """Execute the strategy and return portfolio results."""
        try:
            # Import the strategy execution logic from MA Cross
            from app.strategies.ma_cross.tools.strategy_execution import (
                execute_strategy,
            )

            return execute_strategy(config, log)
        except ImportError:
            raise StrategyError(
                f"Failed to import MA Cross strategy execution for {self.ma_type}"
            )

    def get_parameter_ranges(self) -> Dict[str, Any]:
        """Get strategy-specific parameter ranges and defaults."""
        return {
            "SHORT_WINDOW": {"min": 5, "max": 50, "default": 10},
            "LONG_WINDOW": {"min": 20, "max": 200, "default": 50},
            "DIRECTION": {"options": ["Long", "Short"], "default": "Long"},
            "USE_RSI": {"type": "bool", "default": False},
            "RSI_WINDOW": {"min": 10, "max": 30, "default": 14},
            "RSI_THRESHOLD": {"min": 30, "max": 80, "default": 70},
        }

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return self.ma_type


class UnifiedMACDStrategy(BaseStrategy, StrategyInterface):
    """
    Unified MACD Strategy implementation.

    This strategy generates buy/sell signals based on MACD line crossovers
    with the signal line.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate MACD signals and positions.

        Args:
            data: Input price data
            short_window: Fast EMA period for MACD calculation
            long_window: Slow EMA period for MACD calculation
            config: Configuration dictionary (must include SIGNAL_WINDOW)
            log: Logging function

        Returns:
            DataFrame with MACD signals and positions
        """
        # Validate inputs
        if not self.validate_windows(short_window, long_window, log):
            raise ValueError("Invalid window parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        # Get signal window from config
        signal_window = config.get("SIGNAL_WINDOW")
        if signal_window is None or signal_window <= 0:
            raise ValueError(
                f"MACD strategy requires valid SIGNAL_WINDOW, got: {signal_window}"
            )

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} MACD signals with fast={short_window}, slow={long_window}, signal={signal_window}"
        )

        try:
            # Calculate MACD components
            data = self._calculate_macd_components(
                data, short_window, long_window, signal_window, log
            )

            # Calculate RSI if enabled
            if config.get("USE_RSI", False):
                rsi_period = config.get("RSI_WINDOW", 14)
                data = calculate_rsi(data, rsi_period)
                log(f"Calculated RSI with period {rsi_period}", "info")

            # Generate MACD signals
            entries, exits = self._calculate_macd_signals(data, config)

            # Add Signal column
            if config.get("DIRECTION", "Long") == "Short":
                data = data.with_columns(
                    [pl.when(entries).then(-1).otherwise(0).alias("Signal")]
                )
            else:
                data = data.with_columns(
                    [pl.when(entries).then(1).otherwise(0).alias("Signal")]
                )

            # Convert signals to positions
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = "MACD"
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window
            strategy_config["SIGNAL_WINDOW"] = signal_window

            data = convert_signals_to_positions(
                data=data, config=strategy_config, log=log
            )

            return data

        except Exception as e:
            log(f"Failed to calculate {direction} MACD signals: {e}", "error")
            raise

    def _calculate_macd_components(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        signal_period: int,
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """Calculate MACD line, signal line, and histogram."""

        # Calculate fast and slow EMAs
        data = data.with_columns(
            [
                pl.col("Close").ewm_mean(span=fast_period).alias("EMA_Fast"),
                pl.col("Close").ewm_mean(span=slow_period).alias("EMA_Slow"),
            ]
        )

        # Calculate MACD line (fast EMA - slow EMA)
        data = data.with_columns(
            [(pl.col("EMA_Fast") - pl.col("EMA_Slow")).alias("MACD_Line")]
        )

        # Calculate signal line (EMA of MACD line)
        data = data.with_columns(
            [pl.col("MACD_Line").ewm_mean(span=signal_period).alias("MACD_Signal")]
        )

        # Calculate histogram (MACD line - signal line)
        data = data.with_columns(
            [(pl.col("MACD_Line") - pl.col("MACD_Signal")).alias("MACD_Histogram")]
        )

        log(
            f"Calculated MACD components: Fast EMA({fast_period}), Slow EMA({slow_period}), Signal({signal_period})"
        )

        return data

    def _calculate_macd_signals(
        self, data: pl.DataFrame, config: Dict[str, Any]
    ) -> tuple:
        """Calculate MACD entry and exit signals."""

        # MACD crossover signals: MACD line crosses above/below signal line
        macd_above_signal = pl.col("MACD_Line") > pl.col("MACD_Signal")
        macd_above_signal_prev = macd_above_signal.shift(1)

        # Entry signal: MACD line crosses above signal line
        entries = macd_above_signal & ~macd_above_signal_prev.fill_null(False)

        # Exit signal: MACD line crosses below signal line
        exits = ~macd_above_signal & macd_above_signal_prev.fill_null(True)

        # Apply RSI filter if enabled
        if config.get("USE_RSI", False):
            rsi_threshold = config.get("RSI_THRESHOLD", 70)
            rsi_filter = pl.col("RSI") < rsi_threshold
            entries = entries & rsi_filter

        return entries, exits

    def validate_parameters(self, config: Dict[str, Any]) -> bool:
        """Validate strategy-specific parameters."""
        required_params = ["SHORT_WINDOW", "LONG_WINDOW", "SIGNAL_WINDOW"]

        for param in required_params:
            if param not in config:
                return False
            if not isinstance(config[param], int) or config[param] <= 0:
                return False

        if config["SHORT_WINDOW"] >= config["LONG_WINDOW"]:
            return False

        return True

    def execute(self, config: Dict[str, Any], log: Any) -> List[Dict[str, Any]]:
        """Execute the strategy and return portfolio results."""
        try:
            # Import the strategy execution logic from MACD
            from app.strategies.macd.tools.strategy_execution import execute_strategy

            return execute_strategy(config, log)
        except ImportError:
            raise StrategyError("Failed to import MACD strategy execution")

    def get_parameter_ranges(self) -> Dict[str, Any]:
        """Get strategy-specific parameter ranges and defaults."""
        return {
            "SHORT_WINDOW": {"min": 8, "max": 21, "default": 12},
            "LONG_WINDOW": {"min": 21, "max": 35, "default": 26},
            "SIGNAL_WINDOW": {"min": 5, "max": 15, "default": 9},
            "DIRECTION": {"options": ["Long", "Short"], "default": "Long"},
            "USE_RSI": {"type": "bool", "default": False},
            "RSI_WINDOW": {"min": 10, "max": 30, "default": 14},
            "RSI_THRESHOLD": {"min": 30, "max": 80, "default": 70},
        }

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "MACD"


class UnifiedMeanReversionStrategy(BaseStrategy, StrategyInterface):
    """
    Unified Mean Reversion Strategy implementation.

    This strategy generates signals based on mean reversion patterns
    using various indicators like RSI, Bollinger Bands, etc.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate mean reversion signals and positions.

        Args:
            data: Input price data
            short_window: Short period for mean reversion calculation
            long_window: Long period for mean reversion calculation
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with mean reversion signals and positions
        """
        # Validate inputs
        if not self.validate_windows(short_window, long_window, log):
            raise ValueError("Invalid window parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(f"Calculating {direction} Mean Reversion signals")

        try:
            # Import mean reversion logic from existing implementation
            from app.strategies.mean_reversion.tools.strategy_execution import (
                execute_strategy,
            )

            # Execute using existing logic and adapt to unified interface
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = "MEAN_REVERSION"
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window

            # For now, delegate to existing implementation
            # This will be further refined in Phase 3 (Tool Consolidation)
            results = execute_strategy(strategy_config, log)

            # Convert results back to DataFrame format expected by BaseStrategy
            # This is a simplified implementation for Phase 1
            return data.with_columns([pl.lit(0).alias("Signal")])

        except ImportError:
            log(
                "Mean reversion strategy execution not available, using placeholder",
                "warning",
            )
            return data.with_columns([pl.lit(0).alias("Signal")])
        except Exception as e:
            log(f"Failed to calculate mean reversion signals: {e}", "error")
            raise

    def validate_parameters(self, config: Dict[str, Any]) -> bool:
        """Validate strategy-specific parameters."""
        required_params = ["SHORT_WINDOW", "LONG_WINDOW"]

        for param in required_params:
            if param not in config:
                return False
            if not isinstance(config[param], int) or config[param] <= 0:
                return False

        return True

    def execute(self, config: Dict[str, Any], log: Any) -> List[Dict[str, Any]]:
        """Execute the strategy and return portfolio results."""
        try:
            from app.strategies.mean_reversion.tools.strategy_execution import (
                execute_strategy,
            )

            return execute_strategy(config, log)
        except ImportError:
            raise StrategyError("Failed to import Mean Reversion strategy execution")

    def get_parameter_ranges(self) -> Dict[str, Any]:
        """Get strategy-specific parameter ranges and defaults."""
        return {
            "SHORT_WINDOW": {"min": 10, "max": 30, "default": 20},
            "LONG_WINDOW": {"min": 30, "max": 100, "default": 50},
            "DIRECTION": {"options": ["Long", "Short"], "default": "Long"},
            "RSI_WINDOW": {"min": 10, "max": 30, "default": 14},
            "RSI_OVERSOLD": {"min": 20, "max": 40, "default": 30},
            "RSI_OVERBOUGHT": {"min": 60, "max": 80, "default": 70},
        }

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "MEAN_REVERSION"


class UnifiedRangeStrategy(BaseStrategy, StrategyInterface):
    """
    Unified Range Strategy implementation.

    This strategy generates signals based on range-bound trading patterns.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """Calculate range trading signals and positions."""
        # Validate inputs
        if not self.validate_windows(short_window, long_window, log):
            raise ValueError("Invalid window parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(f"Calculating {direction} Range trading signals")

        try:
            # Placeholder implementation for Phase 1
            # Will be fully implemented in Phase 3 (Tool Consolidation)
            return data.with_columns([pl.lit(0).alias("Signal")])

        except Exception as e:
            log(f"Failed to calculate range trading signals: {e}", "error")
            raise

    def validate_parameters(self, config: Dict[str, Any]) -> bool:
        """Validate strategy-specific parameters."""
        required_params = ["SHORT_WINDOW", "LONG_WINDOW"]

        for param in required_params:
            if param not in config:
                return False
            if not isinstance(config[param], int) or config[param] <= 0:
                return False

        return True

    def execute(self, config: Dict[str, Any], log: Any) -> List[Dict[str, Any]]:
        """Execute the strategy and return portfolio results."""
        try:
            from app.strategies.range.tools.strategy_execution import execute_strategy

            return execute_strategy(config, log)
        except ImportError:
            raise StrategyError("Failed to import Range strategy execution")

    def get_parameter_ranges(self) -> Dict[str, Any]:
        """Get strategy-specific parameter ranges and defaults."""
        return {
            "SHORT_WINDOW": {"min": 10, "max": 30, "default": 20},
            "LONG_WINDOW": {"min": 30, "max": 100, "default": 50},
            "DIRECTION": {"options": ["Long", "Short"], "default": "Long"},
        }

    def get_strategy_type(self) -> str:
        """Get the strategy type identifier."""
        return "RANGE"
