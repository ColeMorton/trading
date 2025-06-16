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
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate SMA crossover signals and positions.

        Args:
            data: Input price data
            short_window: Short SMA period
            long_window: Long SMA period
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with SMA signals and positions
        """
        # Validate inputs
        if not self.validate_windows(short_window, long_window, log):
            raise ValueError("Invalid window parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} SMAs and signals with short window {short_window} and long window {long_window}"
        )

        try:
            # Calculate simple moving averages (use_sma=True)
            data = calculate_mas(data, short_window, long_window, True, log)

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
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window

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
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate EMA crossover signals and positions.

        Args:
            data: Input price data
            short_window: Short EMA period
            long_window: Long EMA period
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with EMA signals and positions
        """
        # Validate inputs
        if not self.validate_windows(short_window, long_window, log):
            raise ValueError("Invalid window parameters")

        if not self.validate_data(data, log):
            raise ValueError("Invalid data")

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} EMAs and signals with short window {short_window} and long window {long_window}"
        )

        try:
            # Calculate exponential moving averages (use_sma=False)
            data = calculate_mas(data, short_window, long_window, False, log)

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
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window

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
    with the signal line, using short_window as fast EMA, long_window as slow EMA,
    and signal_window for the signal line.
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

        Raises:
            ValueError: If SIGNAL_WINDOW is missing or invalid parameters
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
