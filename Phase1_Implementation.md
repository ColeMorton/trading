# Phase 1: Implement Common Code and Components in /app/tools

This phase focuses on creating the shared utilities, interfaces, and base classes that will be used across the application. These components will form the foundation for the refactored architecture.

## 1. Create Strategy Interface

Create a common interface for all strategy types to ensure consistent implementation:

```python
# app/tools/strategy/strategy_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import polars as pl

class StrategyInterface(ABC):
    """
    Abstract base class for all trading strategies.
    Enforces a common interface for strategy implementations.
    """
    
    @abstractmethod
    def process_signals(self, ticker: str, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process signals for a given ticker with strategy-specific parameters.
        
        Args:
            ticker: Ticker symbol to process
            params: Strategy-specific parameters
            config: Global configuration
            
        Returns:
            Optional dictionary with signal results or None if processing fails
        """
        pass
    
    @abstractmethod
    def get_parameter_schema(self) -> Dict[str, Any]:
        """
        Get the parameter schema for this strategy type.
        
        Returns:
            Dictionary defining required and optional parameters
        """
        pass
    
    @abstractmethod
    def calculate_signals(self, data: pl.DataFrame, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[pl.DataFrame]:
        """
        Calculate strategy-specific signals on price data.
        
        Args:
            data: Price data as DataFrame
            params: Strategy-specific parameters
            config: Global configuration
            
        Returns:
            DataFrame with signals or None if calculation fails
        """
        pass
```

## 2. Create Schema Handler

Implement a unified schema handler to standardize data processing across different strategy types:

```python
# app/tools/schema_handler.py
import polars as pl
from typing import Dict, List, Any, Tuple

class SchemaHandler:
    """
    Unified schema handler for processing different strategy types.
    Handles schema detection, validation, and transformation.
    """
    
    @staticmethod
    def detect_schema(df: pl.DataFrame) -> Dict[str, bool]:
        """
        Detect schema type from DataFrame columns.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dictionary with schema detection results
        """
        columns = set(df.columns)
        
        return {
            "has_ticker": "TICKER" in columns or "Ticker" in columns,
            "is_new_schema": "Short Window" in columns and "Long Window" in columns,
            "is_legacy_schema": all(col in columns for col in ["SMA_FAST", "SMA_SLOW", "EMA_FAST", "EMA_SLOW"]),
            "is_macd_schema": "Signal Window" in columns,
            "is_minimal_schema": df.width <= 4 and "Short Window" in columns and "Long Window" in columns,
            "has_use_sma": "Use SMA" in columns or "USE_SMA" in columns,
            "has_rsi": "RSI Window" in columns and "RSI Threshold" in columns
        }
    
    @staticmethod
    def standardize_schema(df: pl.DataFrame, schema_info: Dict[str, bool]) -> pl.DataFrame:
        """
        Standardize DataFrame schema based on detected schema type.
        
        Args:
            df: DataFrame to standardize
            schema_info: Schema detection results
            
        Returns:
            Standardized DataFrame
        """
        # Determine column names
        ticker_col = "Ticker" if "Ticker" in df.columns else "TICKER"
        use_sma_col = "Use SMA" if "Use SMA" in df.columns else "USE_SMA" if "USE_SMA" in df.columns else None
        
        # Base columns
        base_columns = [
            pl.col(ticker_col).cast(pl.Utf8).alias("TICKER"),
            pl.col(use_sma_col).cast(pl.Boolean).alias("USE_SMA") if use_sma_col else pl.lit(False).alias("USE_SMA")
        ]
        
        # Strategy type column
        if "Strategy Type" in df.columns:
            base_columns.append(pl.col("Strategy Type").cast(pl.Utf8).alias("STRATEGY_TYPE"))
        elif "STRATEGY_TYPE" in df.columns:
            base_columns.append(pl.col("STRATEGY_TYPE").cast(pl.Utf8).alias("STRATEGY_TYPE"))
        
        # Window columns based on schema type
        window_columns = []
        
        if schema_info["is_new_schema"]:
            # New schema with Short/Long Window
            if "Short Window" in df.columns:
                window_columns.append(pl.col("Short Window").cast(pl.Int64).alias("SHORT_WINDOW"))
            if "Long Window" in df.columns:
                window_columns.append(pl.col("Long Window").cast(pl.Int64).alias("LONG_WINDOW"))
        
        if schema_info["is_legacy_schema"]:
            # Legacy schema with SMA/EMA columns
            window_columns.extend([
                pl.col("SMA_FAST").cast(pl.Int64),
                pl.col("SMA_SLOW").cast(pl.Int64),
                pl.col("EMA_FAST").cast(pl.Int64),
                pl.col("EMA_SLOW").cast(pl.Int64)
            ])
        
        if schema_info["is_macd_schema"]:
            # MACD schema with Signal Window
            if "Signal Window" in df.columns:
                window_columns.append(pl.col("Signal Window").cast(pl.Int64).alias("SIGNAL_WINDOW"))
        
        if schema_info["has_rsi"]:
            # RSI parameters
            if "RSI Window" in df.columns:
                window_columns.append(pl.col("RSI Window").cast(pl.Int64).alias("RSI_WINDOW"))
            if "RSI Threshold" in df.columns:
                window_columns.append(pl.col("RSI Threshold").cast(pl.Int64).alias("RSI_THRESHOLD"))
        
        # Return standardized DataFrame
        return df.select(base_columns + window_columns)
```

## 3. Create Strategy Factory

Implement a factory to instantiate the appropriate strategy:

```python
# app/tools/strategy/strategy_factory.py
from typing import Dict, Optional
from app.tools.strategy.strategy_interface import StrategyInterface

class StrategyFactory:
    """Factory for creating strategy instances"""
    
    _strategies: Dict[str, StrategyInterface] = {}
    
    @classmethod
    def register_strategy(cls, strategy_type: str, strategy_instance: StrategyInterface) -> None:
        """
        Register a strategy instance for a specific strategy type.
        
        Args:
            strategy_type: Type of strategy to register
            strategy_instance: Strategy instance to register
        """
        cls._strategies[strategy_type] = strategy_instance
    
    @classmethod
    def create_strategy(cls, strategy_type: str) -> Optional[StrategyInterface]:
        """
        Create a strategy instance based on strategy type.
        
        Args:
            strategy_type: Type of strategy to create ("SMA", "EMA", "MACD")
            
        Returns:
            Strategy instance or None if strategy type is not supported
        """
        return cls._strategies.get(strategy_type)
```

## 4. Create Signal Utilities

Implement common signal utilities to be used across different strategies:

```python
# app/tools/strategy/signal_utils.py
import polars as pl
from typing import Dict, Any, Optional

def is_signal_current(signal_data: pl.DataFrame, config: Dict[str, Any]) -> bool:
    """
    Check if the most recent data point contains a signal.
    
    Args:
        signal_data: DataFrame containing signal data
        config: Configuration dictionary
        
    Returns:
        True if current data point has a signal, False otherwise
    """
    if signal_data is None or len(signal_data) == 0:
        return False
    
    # Get the most recent row
    latest_row = signal_data.tail(1)
    
    # Check for signal column
    if "signal" in latest_row.columns:
        return latest_row["signal"].item() == 1
    
    # Check for buy_signal column (alternative name)
    if "buy_signal" in latest_row.columns:
        return latest_row["buy_signal"].item() == 1
    
    return False

def calculate_ma_signals(data: pl.DataFrame, short_window: int, long_window: int, 
                         use_sma: bool = False, config: Dict[str, Any] = None) -> Optional[pl.DataFrame]:
    """
    Calculate moving average signals (SMA or EMA).
    
    Args:
        data: Price data as DataFrame
        short_window: Short window period
        long_window: Long window period
        use_sma: Whether to use SMA (True) or EMA (False)
        config: Configuration dictionary
        
    Returns:
        DataFrame with signals or None if calculation fails
    """
    try:
        # Ensure data has required columns
        if "close" not in data.columns:
            return None
        
        # Calculate short MA
        if use_sma:
            data = data.with_columns(
                pl.col("close").rolling_mean(short_window).alias("short_ma")
            )
        else:
            data = data.with_columns(
                pl.col("close").ewm_mean(span=short_window).alias("short_ma")
            )
        
        # Calculate long MA
        if use_sma:
            data = data.with_columns(
                pl.col("close").rolling_mean(long_window).alias("long_ma")
            )
        else:
            data = data.with_columns(
                pl.col("close").ewm_mean(span=long_window).alias("long_ma")
            )
        
        # Calculate crossover signal
        data = data.with_columns(
            (pl.col("short_ma") > pl.col("long_ma")).alias("current_position")
        )
        
        # Calculate signal (1 when position changes from 0 to 1)
        data = data.with_columns(
            (pl.col("current_position").shift(1).fill_null(0) == 0) & 
            (pl.col("current_position") == 1)
        ).alias("signal")
        
        return data
    except Exception:
        return None

def calculate_macd_signals(data: pl.DataFrame, short_window: int, long_window: int, 
                          signal_window: int, config: Dict[str, Any] = None) -> Optional[pl.DataFrame]:
    """
    Calculate MACD signals.
    
    Args:
        data: Price data as DataFrame
        short_window: Short window period
        long_window: Long window period
        signal_window: Signal line window period
        config: Configuration dictionary
        
    Returns:
        DataFrame with signals or None if calculation fails
    """
    try:
        # Ensure data has required columns
        if "close" not in data.columns:
            return None
        
        # Calculate short EMA
        data = data.with_columns(
            pl.col("close").ewm_mean(span=short_window).alias("short_ema")
        )
        
        # Calculate long EMA
        data = data.with_columns(
            pl.col("close").ewm_mean(span=long_window).alias("long_ema")
        )
        
        # Calculate MACD line
        data = data.with_columns(
            (pl.col("short_ema") - pl.col("long_ema")).alias("macd_line")
        )
        
        # Calculate signal line
        data = data.with_columns(
            pl.col("macd_line").ewm_mean(span=signal_window).alias("signal_line")
        )
        
        # Calculate histogram
        data = data.with_columns(
            (pl.col("macd_line") - pl.col("signal_line")).alias("histogram")
        )
        
        # Calculate crossover signal
        data = data.with_columns(
            (pl.col("macd_line") > pl.col("signal_line")).alias("current_position")
        )
        
        # Calculate signal (1 when position changes from 0 to 1)
        data = data.with_columns(
            (pl.col("current_position").shift(1).fill_null(0) == 0) & 
            (pl.col("current_position") == 1)
        ).alias("signal")
        
        return data
    except Exception:
        return None
```

## 5. Create Data Loading Utilities

Implement common data loading utilities:

```python
# app/tools/data_loader.py
import polars as pl
from typing import Dict, Any, Optional, Callable
from app.tools.get_data import get_data

def load_ticker_data(ticker: str, config: Dict[str, Any], log: Callable) -> Optional[pl.DataFrame]:
    """
    Load data for a specific ticker with error handling.
    
    Args:
        ticker: Ticker symbol to load data for
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        DataFrame with ticker data or None if loading fails
    """
    try:
        data = get_data(ticker, config, log)
        if data is None or len(data) == 0:
            log(f"No data available for {ticker}", "error")
            return None
        
        return data
    except Exception as e:
        log(f"Error loading data for {ticker}: {str(e)}", "error")
        return None
```

## 6. Create Configuration TypedDict

Define a common configuration TypedDict for use across the application:

```python
# app/tools/config_types.py
from typing import TypedDict, NotRequired

class StrategyConfig(TypedDict):
    """
    Configuration type definition for strategy processing.
    
    Required Fields:
        TICKER (str): Ticker symbol to analyze
        
    Optional Fields:
        DIRECTION (NotRequired[str]): Trading direction ("Long" or "Short")
        USE_SMA (NotRequired[bool]): Whether to use Simple Moving Average instead of EMA
        USE_HOURLY (NotRequired[bool]): Whether to use hourly data
        USE_YEARS (NotRequired[bool]): Whether to limit data by years
        YEARS (NotRequired[float]): Number of years of data to use
        USE_GBM (NotRequired[bool]): Whether to use Geometric Brownian Motion
        USE_SYNTHETIC (NotRequired[bool]): Whether to create synthetic pairs
        TICKER_1 (NotRequired[str]): First ticker for synthetic pairs
        TICKER_2 (NotRequired[str]): Second ticker for synthetic pairs
        STRATEGY_TYPE (NotRequired[str]): Strategy type ("SMA", "EMA", or "MACD")
        SIGNAL_WINDOW (NotRequired[int]): Signal window for MACD strategies
        RSI_WINDOW (NotRequired[int]): RSI window for MACD+RSI strategies
        RSI_THRESHOLD (NotRequired[int]): RSI threshold for MACD+RSI strategies
    """
    TICKER: str
    DIRECTION: NotRequired[str]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]
    STRATEGY_TYPE: NotRequired[str]
    SIGNAL_WINDOW: NotRequired[int]
    RSI_WINDOW: NotRequired[int]
    RSI_THRESHOLD: NotRequired[int]
```

## Implementation Checklist

- [ ] Create `app/tools/strategy/strategy_interface.py`
- [ ] Create `app/tools/schema_handler.py`
- [ ] Create `app/tools/strategy/strategy_factory.py`
- [ ] Create `app/tools/strategy/signal_utils.py`
- [ ] Create `app/tools/data_loader.py`
- [ ] Create `app/tools/config_types.py`
- [ ] Document new components with proper docstrings