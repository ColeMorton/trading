"""
Base Strategy Abstract Class

This module defines the abstract base class for all trading strategies.
It follows the Strategy pattern and ensures consistent interface across
all strategy implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Callable, Optional
import polars as pl


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the interface that all concrete strategies must implement.
    It provides common validation methods and ensures consistent behavior across
    different strategy types.
    """
    
    @abstractmethod
    def calculate(
        self,
        data: pl.DataFrame,
        short_window: int,
        long_window: int,
        config: Dict[str, Any],
        log: Callable[[str, str], None]
    ) -> pl.DataFrame:
        """
        Calculate strategy signals and positions.
        
        This is the main method that each strategy must implement.
        It should calculate moving averages, generate signals, and
        convert them to positions.
        
        Args:
            data: Input price data with at least a 'close' column
            short_window: Short moving average window period
            long_window: Long moving average window period
            config: Configuration dictionary containing strategy parameters
            log: Logging function that accepts message and log level
            
        Returns:
            DataFrame with calculated signals and positions
            
        Raises:
            Exception: If calculation fails
        """
        pass
    
    def validate_windows(
        self,
        short_window: int,
        long_window: int,
        log: Callable[[str, str], None]
    ) -> bool:
        """
        Validate window parameters.
        
        Args:
            short_window: Short moving average window period
            long_window: Long moving average window period
            log: Logging function
            
        Returns:
            True if windows are valid, False otherwise
        """
        if short_window <= 0 or long_window <= 0:
            log(f"Window values must be positive: short={short_window}, long={long_window}", "error")
            return False
            
        if short_window >= long_window:
            log(f"Short window ({short_window}) must be less than long window ({long_window})", "error")
            return False
            
        return True
    
    def validate_data(
        self,
        data: Optional[pl.DataFrame],
        log: Callable[[str, str], None]
    ) -> bool:
        """
        Validate input data.
        
        Args:
            data: Input price data
            log: Logging function
            
        Returns:
            True if data is valid, False otherwise
        """
        if data is None:
            log("Data is None", "error")
            return False
            
        if not isinstance(data, pl.DataFrame):
            log(f"Data must be a Polars DataFrame, got {type(data)}", "error")
            return False
            
        if data.is_empty():
            log("Data is empty", "error")
            return False
            
        if "close" not in data.columns:
            log("Data must contain 'close' column", "error")
            return False
            
        return True
    
    def get_strategy_name(self) -> str:
        """
        Get the name of this strategy.
        
        Returns:
            Strategy name derived from class name
        """
        return self.__class__.__name__.replace("Strategy", "")