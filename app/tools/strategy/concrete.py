"""
Concrete Strategy Implementations

This module contains concrete implementations of trading strategies
that inherit from the BaseStrategy abstract class.
"""

from collections.abc import Callable
from typing import Any

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
        config: dict[str, Any],
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
            msg = "Invalid period parameters"
            raise ValueError(msg)

        if not self.validate_data(data, log):
            msg = "Invalid data"
            raise ValueError(msg)

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} SMA signals: fast={fast_period}, slow={slow_period}",
            "debug",
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
                    [pl.when(entries).then(-1).otherwise(0).alias("Signal")],
                )
            else:
                data = data.with_columns(
                    [pl.when(entries).then(1).otherwise(0).alias("Signal")],
                )

            # Convert signals to positions with audit trail
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = "SMA"
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period
            # Keep legacy names for backwards compatibility
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period

            return convert_signals_to_positions(
                data=data, config=strategy_config, log=log,
            )


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
        config: dict[str, Any],
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
            msg = "Invalid period parameters"
            raise ValueError(msg)

        if not self.validate_data(data, log):
            msg = "Invalid data"
            raise ValueError(msg)

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} EMA signals: fast={fast_period}, slow={slow_period}",
            "debug",
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
                    [pl.when(entries).then(-1).otherwise(0).alias("Signal")],
                )
            else:
                data = data.with_columns(
                    [pl.when(entries).then(1).otherwise(0).alias("Signal")],
                )

            # Convert signals to positions with audit trail
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = "EMA"
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period
            # Keep legacy names for backwards compatibility
            strategy_config["FAST_PERIOD"] = fast_period
            strategy_config["SLOW_PERIOD"] = slow_period

            return convert_signals_to_positions(
                data=data, config=strategy_config, log=log,
            )


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
        config: dict[str, Any],
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
            msg = "Invalid period parameters"
            raise ValueError(msg)

        if not self.validate_data(data, log):
            msg = "Invalid data"
            raise ValueError(msg)

        # Get signal period from config
        signal_period = config.get("SIGNAL_PERIOD")
        if signal_period is None or signal_period <= 0:
            msg = f"MACD strategy requires valid SIGNAL_PERIOD, got: {signal_period}"
            raise ValueError(
                msg,
            )

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} MACD signals: fast={fast_period}, slow={slow_period}, signal={signal_period}",
            "debug",
        )

        try:
            # Calculate MACD components
            data = self._calculate_macd_components(
                data, fast_period, slow_period, signal_period, log,
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
                    [pl.when(entries).then(-1).otherwise(0).alias("Signal")],
                )
            else:
                data = data.with_columns(
                    [pl.when(entries).then(1).otherwise(0).alias("Signal")],
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

            return convert_signals_to_positions(
                data=data, config=strategy_config, log=log,
            )


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
        2.0 / (fast_period + 1)
        2.0 / (slow_period + 1)
        2.0 / (signal_period + 1)

        # Calculate EMAs using exponential smoothing
        data = data.with_columns(
            [
                pl.col("Close").ewm_mean(span=fast_period).alias("EMA_Fast"),
                pl.col("Close").ewm_mean(span=slow_period).alias("EMA_Slow"),
            ],
        )

        # Calculate MACD line (fast EMA - slow EMA)
        data = data.with_columns(
            [(pl.col("EMA_Fast") - pl.col("EMA_Slow")).alias("MACD_Line")],
        )

        # Calculate signal line (EMA of MACD line)
        data = data.with_columns(
            [pl.col("MACD_Line").ewm_mean(span=signal_period).alias("MACD_Signal")],
        )

        # Calculate histogram (MACD line - signal line)
        data = data.with_columns(
            [(pl.col("MACD_Line") - pl.col("MACD_Signal")).alias("MACD_Histogram")],
        )

        log(
            f"Calculated MACD components: Fast EMA({fast_period}), Slow EMA({slow_period}), Signal({signal_period})",
        )

        return data

    def _calculate_macd_signals(
        self, data: pl.DataFrame, config: dict[str, Any],
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


class SMAAtrStrategy(BaseStrategy):
    """
    SMA_ATR strategy combining SMA crossovers for entry and ATR trailing stops for exit.

    This strategy generates entry signals based on SMA crossovers and uses
    ATR (Average True Range) trailing stops for exit signals.
    """

    def calculate(
        self,
        data: pl.DataFrame,
        fast_period: int,
        slow_period: int,
        config: dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Calculate SMA_ATR signals and positions.

        Args:
            data: Input price data
            fast_period: Fast SMA period for entry signals
            slow_period: Slow SMA period for entry signals
            config: Configuration dictionary containing ATR parameters
            log: Logging function

        Returns:
            DataFrame with SMA_ATR signals and positions
        """
        # Validate inputs
        if not self.validate_periods(fast_period, slow_period, log):
            msg = "Invalid period parameters"
            raise ValueError(msg)

        if not self.validate_data(data, log):
            msg = "Invalid data"
            raise ValueError(msg)

        # Get ATR parameters
        atr_length = config.get("ATR_LENGTH", 14)
        atr_multiplier = config.get("ATR_MULTIPLIER", 2.0)

        direction = "Short" if config.get("DIRECTION", "Long") == "Short" else "Long"
        log(
            f"Calculating {direction} SMA_ATR signals: SMA({fast_period},{slow_period}), ATR({atr_length},{atr_multiplier})",
            "debug",
        )

        try:
            # Import required functions
            from app.tools.calculate_atr import calculate_atr
            from app.tools.calculate_ma_signals import calculate_ma_signals
            from app.tools.calculate_mas import calculate_mas

            # Calculate simple moving averages for entry signals
            data = calculate_mas(data, fast_period, slow_period, True, log)

            # Calculate ATR for trailing stops
            atr_series = calculate_atr(data.to_pandas(), atr_length)
            data = data.with_columns([pl.lit(atr_series.values).alias("ATR")])

            # Generate SMA crossover signals for entries
            entries, _ = calculate_ma_signals(data, config)

            # Generate SMA_ATR positions using combined logic
            data = self._generate_sma_atr_positions(
                data, entries, atr_multiplier, direction, config, log,
            )

            # Convert to final strategy format
            strategy_config = config.copy()
            strategy_config.update(
                {
                    "STRATEGY_TYPE": "SMA_ATR",
                    "FAST_PERIOD": fast_period,
                    "SLOW_PERIOD": slow_period,
                    "ATR_LENGTH": atr_length,
                    "ATR_MULTIPLIER": atr_multiplier,
                },
            )

            return data

        except Exception as e:
            log(f"Failed to calculate {direction} SMA_ATR signals: {e}", "error")
            raise

    def _generate_sma_atr_positions(
        self,
        data: pl.DataFrame,
        entries: pl.Series,
        atr_multiplier: float,
        direction: str,
        config: dict[str, Any],
        log: Callable[[str, str], None],
    ) -> pl.DataFrame:
        """
        Generate positions using SMA entries and ATR trailing stops.

        Args:
            data: DataFrame with SMA and ATR data
            entries: Polars Series for entry signals
            atr_multiplier: ATR multiplier for trailing stop calculation
            direction: Trading direction ("Long" or "Short")
            config: Configuration dictionary
            log: Logging function

        Returns:
            DataFrame with positions and signals
        """
        # Convert to pandas for easier position generation logic
        df = data.to_pandas()

        # Add entry signals column
        df["Entry_Signal"] = entries.to_pandas()

        # Initialize tracking columns
        df["Position"] = 0
        df["Signal"] = 0
        df["TrailingStop"] = None
        df["HighestSinceEntry"] = None

        position = 0
        trailing_stop = None
        highest_since_entry = None

        for i in range(1, len(df)):
            current_price = df.iloc[i]["Close"]
            current_atr = df.iloc[i]["ATR"]
            entry_signal = df.iloc[i]["Entry_Signal"]

            if direction == "Long":
                if position == 0:  # Not in position
                    if entry_signal:  # SMA buy signal
                        position = 1
                        df.iloc[i, df.columns.get_loc("Signal")] = 1
                        trailing_stop = current_price - (current_atr * atr_multiplier)
                        highest_since_entry = current_price

                elif position == 1:  # In long position
                    # Update highest price since entry
                    highest_since_entry = max(current_price, highest_since_entry)

                    # Update trailing stop (can only move up)
                    new_stop = highest_since_entry - (current_atr * atr_multiplier)
                    if trailing_stop is not None:
                        trailing_stop = max(trailing_stop, new_stop)
                    else:
                        trailing_stop = new_stop

                    # Check for exit conditions (ATR trailing stop hit)
                    if current_price <= trailing_stop:
                        position = 0
                        df.iloc[i, df.columns.get_loc("Signal")] = -1  # Exit signal
                        trailing_stop = None
                        highest_since_entry = None

            elif position == 0:  # Not in position
                if entry_signal:  # SMA sell signal
                    position = -1
                    df.iloc[i, df.columns.get_loc("Signal")] = -1
                    trailing_stop = current_price + (current_atr * atr_multiplier)
                    highest_since_entry = current_price  # For short, track lowest

            elif position == -1:  # In short position
                # Update lowest price since entry (for short positions)
                highest_since_entry = min(current_price, highest_since_entry)

                # Update trailing stop (can only move down)
                new_stop = highest_since_entry + (current_atr * atr_multiplier)
                if trailing_stop is not None:
                    trailing_stop = min(trailing_stop, new_stop)
                else:
                    trailing_stop = new_stop

                # Check for exit conditions (ATR trailing stop hit)
                if current_price >= trailing_stop:
                    position = 0
                    df.iloc[i, df.columns.get_loc("Signal")] = 1  # Exit signal
                    trailing_stop = None
                    highest_since_entry = None

            # Record current state
            df.iloc[i, df.columns.get_loc("Position")] = position
            df.iloc[i, df.columns.get_loc("TrailingStop")] = trailing_stop
            df.iloc[i, df.columns.get_loc("HighestSinceEntry")] = highest_since_entry

        # Convert back to polars
        return pl.from_pandas(df)
