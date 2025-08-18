"""
Concrete Strategy Implementations

This module contains concrete implementations of trading strategies
that inherit from the BaseStrategy abstract class.
"""

from typing import Any, Callable, Dict

import polars as pl

from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_rsi import calculate_rsi
from app.tools.signal_conversion import convert_signals_to_positions
from app.tools.strategy.base import BaseStrategy


class SMAStrategy(BaseStrategy):
    """
    Simple Moving Average (SMA) crossover strategy.

    This strategy generates buy/sell signals based on the crossover
    of short and long period simple moving averages.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate SMA crossover signals and positions.

        Args:
            data: Input price data
            fast_period: Fast SMA period
            slow_period: Slow SMA period
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with SMA signals and positions
        """
        # Validate inputs
        if not self.validate_periods(fast_period, slow_period, log):
            raise ValueError("Invalid period parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} SMAs and signals with fast period {fast_period} and slow period {slow_period}"
        )

        try:
            # Calculate simple moving averages (use_sma=True)
            data = calculate_mas(data, fast_period, slow_period, True, log)

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
            strategy_config["STRATEGY_TYPE"] = "SMA"
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period
            # Keep legacy names for backwards compatibility
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period

            data = convert_signals_to_positions(
                data=data, config=strategy_config, log=log
            )

            return data

        except Exception as e:
            log(f"Failed to calculate {direction} SMAs and signals: {e}", "error")
            raise


class EMAStrategy(BaseStrategy):
    """
    Exponential Moving Average (EMA) crossover strategy.

    This strategy generates buy/sell signals based on the crossover
    of short and long period exponential moving averages.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate EMA crossover signals and positions.

        Args:
            data: Input price data
            fast_period: Fast EMA period
            slow_period: Slow EMA period
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with EMA signals and positions
        """
        # Validate inputs
        if not self.validate_periods(fast_period, slow_period, log):
            raise ValueError("Invalid period parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} EMAs and signals with fast period {fast_period} and slow period {slow_period}"
        )

        try:
            # Calculate exponential moving averages (use_sma=False)
            data = calculate_mas(data, fast_period, slow_period, False, log)

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
            strategy_config["STRATEGY_TYPE"] = "EMA"
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period
            # Keep legacy names for backwards compatibility
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period

            data = convert_signals_to_positions(
                data=data, config=strategy_config, log=log
            )

            return data

        except Exception as e:
            log(f"Failed to calculate {direction} EMAs and signals: {e}", "error")
            raise


class MACDStrategy(BaseStrategy):
    """
    MACD (Moving Average Convergence Divergence) strategy.

    This strategy generates buy/sell signals based on MACD line crossovers
    with the signal line, using fast_period as fast EMA, slow_period as slow EMA,
    and signal_period for the signal line.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate MACD signals and positions.

        Args:
            data: Input price data
            fast_period: Fast EMA period for MACD calculation
            slow_period: Slow EMA period for MACD calculation
            config: Configuration dictionary (must include SIGNAL_PERIOD)
            log: Logging function

        Returns:
            DataFrame with MACD signals and positions

        Raises:
            ValueError: If SIGNAL_PERIOD is missing or invalid parameters
        """
        # Validate inputs
        if not self.validate_periods(fast_period, slow_period, log):
            raise ValueError("Invalid period parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        # Get signal period from config
        signal_period = config.get("SIGNAL_PERIOD")
        if signal_period is None or signal_period <= 0:
            raise ValueError(
                f"MACD strategy requires valid SIGNAL_PERIOD, got: {signal_period}"
            )

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} MACD signals with fast={fast_period}, slow={slow_period}, signal={signal_period}"
        )

        try:
            # Calculate MACD components
            data = self._calculate_macd_components(
                data, fast_period, slow_period, signal_period, log
            )

            # Calculate RSI if enabled
            if config.get("USE_RSI", False):
                rsi_period = config.get("RSI_WINDOW", 14)
                data = calculate_rsi(data, rsi_period)
                log(f"Calculated RSI with period {rsi_period}", "info")

            # Generate MACD signals
            entries, exits = self._calculate_macd_signals(data, config)

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
            strategy_config["STRATEGY_TYPE"] = "MACD"
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period
            strategy_config["SIGNAL_PERIOD"] = signal_period
            # Keep legacy names for backwards compatibility
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period
            strategy_config["SIGNAL_PERIOD"] = signal_period

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
        alpha_fast = 2.0 / (fast_period + 1)
        alpha_slow = 2.0 / (slow_period + 1)
        alpha_signal = 2.0 / (signal_period + 1)

        # Calculate EMAs using exponential smoothing
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
        """Calculate MACD entry and exit signals based on MACD line crossing signal line."""

        # MACD crossover signals: MACD line crosses above/below signal line
        # Entry: MACD line crosses above signal line (bullish)
        # Exit: MACD line crosses below signal line (bearish)

        # Calculate crossovers
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
