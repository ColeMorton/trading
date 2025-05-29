"""
Concrete Strategy Implementations

This module contains concrete implementations of trading strategies
that inherit from the BaseStrategy abstract class.
"""

from typing import Dict, Any, Callable
import polars as pl

from app.tools.strategy.base import BaseStrategy
from app.tools.calculate_mas import calculate_mas
from app.tools.calculate_ma_signals import calculate_ma_signals
from app.tools.calculate_rsi import calculate_rsi
from app.tools.signal_conversion import convert_signals_to_positions


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
        log: Callable[[str, str], None]
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
        
        direction = "Short" if config.get('DIRECTION', 'Long') == 'Short' else "Long"
        log(f"Calculating {direction} SMAs and signals with short window {short_window} and long window {long_window}")
        
        try:
            # Calculate simple moving averages (use_sma=True)
            data = calculate_mas(data, short_window, long_window, True, log)
            
            # Calculate RSI if enabled
            if config.get('USE_RSI', False):
                rsi_period = config.get('RSI_WINDOW', 14)
                data = calculate_rsi(data, rsi_period)
                log(f"Calculated RSI with period {rsi_period}", "info")
            
            # Generate signals based on MA crossovers
            entries, exits = calculate_ma_signals(data, config)
            
            # Add Signal column (-1 for short entry, 1 for long entry, 0 for no signal)
            if config.get('DIRECTION', 'Long') == 'Short':
                data = data.with_columns([
                    pl.when(entries).then(-1).otherwise(0).alias("Signal")
                ])
            else:
                data = data.with_columns([
                    pl.when(entries).then(1).otherwise(0).alias("Signal")
                ])
            
            # Convert signals to positions with audit trail
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = "SMA"
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window
            
            data = convert_signals_to_positions(
                data=data,
                config=strategy_config,
                log=log
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
        log: Callable[[str, str], None]
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
        
        direction = "Short" if config.get('DIRECTION', 'Long') == 'Short' else "Long"
        log(f"Calculating {direction} EMAs and signals with short window {short_window} and long window {long_window}")
        
        try:
            # Calculate exponential moving averages (use_sma=False)
            data = calculate_mas(data, short_window, long_window, False, log)
            
            # Calculate RSI if enabled
            if config.get('USE_RSI', False):
                rsi_period = config.get('RSI_WINDOW', 14)
                data = calculate_rsi(data, rsi_period)
                log(f"Calculated RSI with period {rsi_period}", "info")
            
            # Generate signals based on MA crossovers
            entries, exits = calculate_ma_signals(data, config)
            
            # Add Signal column (-1 for short entry, 1 for long entry, 0 for no signal)
            if config.get('DIRECTION', 'Long') == 'Short':
                data = data.with_columns([
                    pl.when(entries).then(-1).otherwise(0).alias("Signal")
                ])
            else:
                data = data.with_columns([
                    pl.when(entries).then(1).otherwise(0).alias("Signal")
                ])
            
            # Convert signals to positions with audit trail
            strategy_config = config.copy()
            strategy_config["STRATEGY_TYPE"] = "EMA"
            strategy_config["SHORT_WINDOW"] = short_window
            strategy_config["LONG_WINDOW"] = long_window
            
            data = convert_signals_to_positions(
                data=data,
                config=strategy_config,
                log=log
            )
            
            return data
            
        except Exception as e:
            log(f"Failed to calculate {direction} EMAs and signals: {e}", "error")
            raise