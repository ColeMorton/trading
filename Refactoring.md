# Refactoring of ma_cross Scanner, strategies Update Portfolios, and concurrency Review

Based on my analysis of both `app/strategies/update_portfolios.py` and `app/ma_cross/1_scanner.py`, I'll outline the specific changes needed to make the ma_cross scanner fully compatible with MACD strategies, while adhering to key software engineering principles.

## Current Limitations in ma_cross Scanner

The ma_cross scanner (`1_scanner.py`) currently has several limitations that prevent it from handling MACD strategies:

1. **Missing MACD Parameters**: The scanner doesn't support the `signal_window` parameter required for MACD strategies
2. **Limited Strategy Processing**: The `process_ticker` function in `scanner_processing.py` only processes SMA and EMA signals
3. **Schema Limitations**: The CSV schema handling doesn't account for MACD-specific columns
4. **No MACD Signal Generation**: There's no mechanism to generate and evaluate MACD signals

## Software Engineering Principles for Implementation

Before detailing the specific changes, it's crucial to emphasize the software engineering principles that should guide this implementation:

### 1. Single Responsibility Principle (SRP)

Each module, class, and function should have one and only one reason to change. In our implementation:
- Strategy-specific logic should be isolated in dedicated modules
- Signal generation should be separate from signal processing
- Data loading should be separate from strategy execution

### 2. Don't Repeat Yourself (DRY)

Code duplication should be eliminated by abstracting common functionality:
- Create a unified strategy processing framework
- Use strategy-specific adapters that implement common interfaces
- Share common utility functions across strategy types

### 3. Separation of Concerns (SoC)

Different aspects of the application should be handled by distinct modules:
- Data acquisition should be separate from signal generation
- Signal generation should be separate from backtesting
- Configuration handling should be separate from execution logic

## Architectural Approach

Rather than simply adding MACD functionality to the existing code, we should refactor toward a more modular architecture:

```
app/
├── strategies/
│   ├── base/
│   │   ├── strategy_interface.py  # Common interface for all strategies
│   │   └── signal_processor.py    # Generic signal processing
│   ├── ma_cross/
│   │   ├── sma_strategy.py        # SMA-specific implementation
│   │   └── ema_strategy.py        # EMA-specific implementation
│   └── macd/
│       └── macd_strategy.py       # MACD-specific implementation
├── scanner/
│   ├── base_scanner.py            # Generic scanner functionality
│   ├── ma_scanner.py              # MA-specific scanner
│   └── macd_scanner.py            # MACD-specific scanner
└── tools/
    ├── data/
    │   └── data_loader.py         # Unified data loading
    ├── signals/
    │   ├── ma_signals.py          # MA signal generation
    │   └── macd_signals.py        # MACD signal generation
    └── config/
        └── config_loader.py       # Configuration management
```

## Required Changes

With these principles in mind, here's a detailed plan for changes needed to make the ma_cross scanner fully compatible with MACD strategies:

### 1. Create a Strategy Interface

First, establish a common interface for all strategy types:

```python
# app/strategies/base/strategy_interface.py
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

### 2. Implement Strategy-Specific Classes

Create concrete implementations for each strategy type:

```python
# app/strategies/ma_cross/sma_strategy.py
from app.strategies.base.strategy_interface import StrategyInterface
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.get_data import get_data
from app.tools.strategy.signal_utils import is_signal_current
import polars as pl
from typing import Dict, Any, Optional, Callable

class SMAStrategy(StrategyInterface):
    """SMA strategy implementation"""
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "required": ["short_window", "long_window"],
            "optional": [],
            "types": {
                "short_window": int,
                "long_window": int
            }
        }
    
    def calculate_signals(self, data: pl.DataFrame, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[pl.DataFrame]:
        """Calculate SMA signals on price data"""
        try:
            # Set SMA configuration
            strategy_config = config.copy()
            strategy_config["USE_SMA"] = True
            
            # Calculate signals
            return calculate_ma_and_signals(
                data.clone(),
                params["short_window"],
                params["long_window"],
                strategy_config,
                config.get("log", lambda x, y=None: None)
            )
        except Exception as e:
            if "log" in config:
                config["log"](f"Error calculating SMA signals: {str(e)}", "error")
            return None
    
    def process_signals(self, ticker: str, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process SMA signals for a ticker"""
        log = config.get("log", lambda x, y=None: None)
        
        try:
            # Validate parameters
            if "short_window" not in params or "long_window" not in params:
                log(f"Missing required parameters for SMA strategy", "error")
                return None
                
            # Get data
            data = get_data(ticker, config, log)
            if data is None:
                log(f"No data available for {ticker}", "error")
                return None
                
            # Calculate signals
            signal_data = self.calculate_signals(data, params, config)
            if signal_data is None:
                log(f"Failed to calculate SMA signals for {ticker}", "error")
                return None
                
            # Check for current signal
            current_signal = is_signal_current(signal_data, config)
            
            return {
                "TICKER": ticker,
                "SMA": current_signal,
                "EMA": False,
                "MACD": False,
                "SMA_FAST": params["short_window"],
                "SMA_SLOW": params["long_window"],
                "STRATEGY_TYPE": "SMA"
            }
            
        except Exception as e:
            log(f"Error processing SMA signals for {ticker}: {str(e)}", "error")
            return None
```

```python
# app/strategies/macd/macd_strategy.py
from app.strategies.base.strategy_interface import StrategyInterface
from app.tools.calculate_macd_and_signals import calculate_macd_and_signals
from app.tools.get_data import get_data
from app.tools.strategy.signal_utils import is_signal_current
import polars as pl
from typing import Dict, Any, Optional, Callable

class MACDStrategy(StrategyInterface):
    """MACD strategy implementation"""
    
    def get_parameter_schema(self) -> Dict[str, Any]:
        return {
            "required": ["short_window", "long_window", "signal_window"],
            "optional": ["rsi_window", "rsi_threshold"],
            "types": {
                "short_window": int,
                "long_window": int,
                "signal_window": int,
                "rsi_window": int,
                "rsi_threshold": int
            }
        }
    
    def calculate_signals(self, data: pl.DataFrame, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[pl.DataFrame]:
        """Calculate MACD signals on price data"""
        try:
            # Set MACD configuration
            strategy_config = config.copy()
            
            # Add RSI parameters if provided
            if "rsi_window" in params and "rsi_threshold" in params:
                strategy_config["RSI_WINDOW"] = params["rsi_window"]
                strategy_config["RSI_THRESHOLD"] = params["rsi_threshold"]
            
            # Calculate signals
            return calculate_macd_and_signals(
                data.clone(),
                params["short_window"],
                params["long_window"],
                params["signal_window"],
                strategy_config,
                config.get("log", lambda x, y=None: None)
            )
        except Exception as e:
            if "log" in config:
                config["log"](f"Error calculating MACD signals: {str(e)}", "error")
            return None
    
    def process_signals(self, ticker: str, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process MACD signals for a ticker"""
        log = config.get("log", lambda x, y=None: None)
        
        try:
            # Validate parameters
            required_params = ["short_window", "long_window", "signal_window"]
            if not all(param in params for param in required_params):
                log(f"Missing required parameters for MACD strategy", "error")
                return None
                
            # Get data
            data = get_data(ticker, config, log)
            if data is None:
                log(f"No data available for {ticker}", "error")
                return None
                
            # Calculate signals
            signal_data = self.calculate_signals(data, params, config)
            if signal_data is None:
                log(f"Failed to calculate MACD signals for {ticker}", "error")
                return None
                
            # Check for current signal
            current_signal = is_signal_current(signal_data, config)
            
            return {
                "TICKER": ticker,
                "SMA": False,
                "EMA": False,
                "MACD": current_signal,
                "MACD_FAST": params["short_window"],
                "MACD_SLOW": params["long_window"],
                "SIGNAL_WINDOW": params["signal_window"],
                "STRATEGY_TYPE": "MACD"
            }
            
        except Exception as e:
            log(f"Error processing MACD signals for {ticker}: {str(e)}", "error")
            return None
```

### 3. Create a Strategy Factory

Implement a factory to instantiate the appropriate strategy:

```python
# app/strategies/strategy_factory.py
from typing import Dict, Optional
from app.strategies.base.strategy_interface import StrategyInterface
from app.strategies.ma_cross.sma_strategy import SMAStrategy
from app.strategies.ma_cross.ema_strategy import EMAStrategy
from app.strategies.macd.macd_strategy import MACDStrategy

class StrategyFactory:
    """Factory for creating strategy instances"""
    
    @staticmethod
    def create_strategy(strategy_type: str) -> Optional[StrategyInterface]:
        """
        Create a strategy instance based on strategy type.
        
        Args:
            strategy_type: Type of strategy to create ("SMA", "EMA", "MACD")
            
        Returns:
            Strategy instance or None if strategy type is not supported
        """
        strategies: Dict[str, StrategyInterface] = {
            "SMA": SMAStrategy(),
            "EMA": EMAStrategy(),
            "MACD": MACDStrategy()
        }
        
        return strategies.get(strategy_type)
```

### 4. Update Scanner to Use Strategy Pattern

Refactor the scanner to use the strategy pattern:

```python
# app/ma_cross/tools/scanner_processing.py (updated)
import os
from datetime import datetime
import polars as pl
from typing import Tuple, List, Dict, Callable, Optional
from app.utils import get_path, get_filename
from app.tools.file_utils import is_file_from_today
from app.strategies.strategy_factory import StrategyFactory

def process_ticker(ticker: str, row: dict, config: dict, log: Callable) -> Optional[Dict]:
    """
    Process a single ticker with the appropriate strategy based on parameters.
    
    Args:
        ticker (str): Ticker symbol to process
        row (dict): Row data containing strategy parameters
        config (dict): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        Optional[Dict]: Results dictionary containing signals or None if processing fails
    """
    # Determine strategy type
    strategy_type = None
    params = {}
    
    # Check for explicit strategy type
    if "STRATEGY_TYPE" in row:
        strategy_type = row["STRATEGY_TYPE"]
    # Legacy detection based on parameters
    elif row.get('SMA_FAST') is not None and row.get('SMA_SLOW') is not None and row.get('USE_SMA', False):
        strategy_type = "SMA"
        params = {
            "short_window": row['SMA_FAST'],
            "long_window": row['SMA_SLOW']
        }
    elif row.get('EMA_FAST') is not None and row.get('EMA_SLOW') is not None and not row.get('USE_SMA', True):
        strategy_type = "EMA"
        params = {
            "short_window": row['EMA_FAST'],
            "long_window": row['EMA_SLOW']
        }
    elif row.get('MACD_FAST') is not None and row.get('MACD_SLOW') is not None and row.get('SIGNAL_WINDOW') is not None:
        strategy_type = "MACD"
        params = {
            "short_window": row['MACD_FAST'],
            "long_window": row['MACD_SLOW'],
            "signal_window": row['SIGNAL_WINDOW']
        }
        # Add RSI parameters if available
        if row.get('RSI_WINDOW') is not None and row.get('RSI_THRESHOLD') is not None:
            params["rsi_window"] = row['RSI_WINDOW']
            params["rsi_threshold"] = row['RSI_THRESHOLD']
    else:
        log(f"Could not determine strategy type for {ticker}", "error")
        return None
    
    # Create strategy instance
    strategy = StrategyFactory.create_strategy(strategy_type)
    if strategy is None:
        log(f"Unsupported strategy type: {strategy_type}", "error")
        return None
    
    # Add logging to config
    strategy_config = config.copy()
    strategy_config["log"] = log
    
    # Process signals using the strategy
    return strategy.process_signals(ticker, params, strategy_config)
```

### 5. Update Config TypedDict in `1_scanner.py`

```python
class Config(TypedDict):
    """
    Configuration type definition for market scanner.
    
    Required Fields:
        TICKER (str): Ticker symbol to analyze
        PORTFOLIO (str): Name of the portfolio file
        
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
    PORTFOLIO: str
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

### 6. Create a Unified Schema Handler

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

### 7. Update Export Results Function

```python
def export_results(results_data: List[Dict], original_df: pl.DataFrame, config: dict, log: Callable) -> None:
    """
    Export scanner results to CSV in a date-specific subdirectory.
    """
    # Log signals
    log("\nSignals detected:")
    signal_configs = []  # Store specific configurations with signals
    
    for result in results_data:
        ticker = result["TICKER"]
        strategy_type = result.get("STRATEGY_TYPE", "Unknown")
        
        # Log signal based on strategy type
        if strategy_type == "SMA" and result.get("SMA", False):
            log(f"SMA Signal - {ticker}: Fast={result.get('SMA_FAST')}, Slow={result.get('SMA_SLOW')}")
            signal_configs.append({
                "ticker": ticker,
                "strategy_type": "SMA",
                "use_sma": True,
                "short_window": result.get("SMA_FAST"),
                "long_window": result.get("SMA_SLOW")
            })
        elif strategy_type == "EMA" and result.get("EMA", False):
            log(f"EMA Signal - {ticker}: Fast={result.get('EMA_FAST')}, Slow={result.get('EMA_SLOW')}")
            signal_configs.append({
                "ticker": ticker,
                "strategy_type": "EMA",
                "use_sma": False,
                "short_window": result.get("EMA_FAST"),
                "long_window": result.get("EMA_SLOW")
            })
        elif strategy_type == "MACD" and result.get("MACD", False):
            log(f"MACD Signal - {ticker}: Fast={result.get('MACD_FAST')}, Slow={result.get('MACD_SLOW')}, Signal={result.get('SIGNAL_WINDOW')}")
            signal_configs.append({
                "ticker": ticker,
                "strategy_type": "MACD",
                "short_window": result.get("MACD_FAST"),
                "long_window": result.get("MACD_SLOW"),
                "signal_window": result.get("SIGNAL_WINDOW")
            })
    
    # Rest of the function remains the same...
```

## Implementation Plan

To implement these changes while maintaining backward compatibility, I recommend the following phased approach:

### Phase 1: Refactor Common Components
1. Create the strategy interface and base classes
2. Implement the schema handler
3. Create the strategy factory

### Phase 2: Implement Strategy-Specific Components
1. Implement SMA and EMA strategies
2. Implement MACD strategy
3. Update signal processing functions

### Phase 3: Update Scanner
1. Refactor scanner to use the strategy pattern
2. Update schema handling
3. Update export functionality

## Summary of Benefits

This refactored approach offers several advantages:

1. **Maintainability**: Each strategy is encapsulated in its own class, making the code easier to maintain
2. **Extensibility**: Adding new strategies becomes straightforward by implementing the strategy interface
3. **Testability**: Strategy components can be tested in isolation
4. **Readability**: Clear separation of concerns makes the code more readable
5. **Consistency**: Unified approach to strategy processing ensures consistent behavior

By following these software engineering principles, we not only make the ma_cross scanner compatible with MACD strategies but also improve the overall architecture of the codebase, making it more robust and easier to extend in the future.