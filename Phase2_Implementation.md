# Phase 2: Update Application Modules to Use New Code

This phase focuses on updating the application modules to use the new common code implemented in Phase 1. The modules to be updated are:

1. `/app/ma_cross`
2. `/app/strategies`
3. `/app/concurrency`

## 1. Implement Strategy-Specific Classes

Create concrete implementations for each strategy type:

### SMA Strategy Implementation

```python
# app/strategies/ma_cross/sma_strategy.py
from app.tools.strategy.strategy_interface import StrategyInterface
from app.tools.strategy.signal_utils import calculate_ma_signals, is_signal_current
from app.tools.data_loader import load_ticker_data
import polars as pl
from typing import Dict, Any, Optional

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
            return calculate_ma_signals(
                data.clone(),
                params["short_window"],
                params["long_window"],
                use_sma=True,
                config=strategy_config
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
            data = load_ticker_data(ticker, config, log)
            if data is None:
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

### EMA Strategy Implementation

```python
# app/strategies/ma_cross/ema_strategy.py
from app.tools.strategy.strategy_interface import StrategyInterface
from app.tools.strategy.signal_utils import calculate_ma_signals, is_signal_current
from app.tools.data_loader import load_ticker_data
import polars as pl
from typing import Dict, Any, Optional

class EMAStrategy(StrategyInterface):
    """EMA strategy implementation"""
    
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
        """Calculate EMA signals on price data"""
        try:
            # Set EMA configuration
            strategy_config = config.copy()
            strategy_config["USE_SMA"] = False
            
            # Calculate signals
            return calculate_ma_signals(
                data.clone(),
                params["short_window"],
                params["long_window"],
                use_sma=False,
                config=strategy_config
            )
        except Exception as e:
            if "log" in config:
                config["log"](f"Error calculating EMA signals: {str(e)}", "error")
            return None
    
    def process_signals(self, ticker: str, params: Dict[str, Any], config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process EMA signals for a ticker"""
        log = config.get("log", lambda x, y=None: None)
        
        try:
            # Validate parameters
            if "short_window" not in params or "long_window" not in params:
                log(f"Missing required parameters for EMA strategy", "error")
                return None
                
            # Get data
            data = load_ticker_data(ticker, config, log)
            if data is None:
                return None
                
            # Calculate signals
            signal_data = self.calculate_signals(data, params, config)
            if signal_data is None:
                log(f"Failed to calculate EMA signals for {ticker}", "error")
                return None
                
            # Check for current signal
            current_signal = is_signal_current(signal_data, config)
            
            return {
                "TICKER": ticker,
                "SMA": False,
                "EMA": current_signal,
                "MACD": False,
                "EMA_FAST": params["short_window"],
                "EMA_SLOW": params["long_window"],
                "STRATEGY_TYPE": "EMA"
            }
            
        except Exception as e:
            log(f"Error processing EMA signals for {ticker}: {str(e)}", "error")
            return None
```

### MACD Strategy Implementation

```python
# app/strategies/macd/macd_strategy.py
from app.tools.strategy.strategy_interface import StrategyInterface
from app.tools.strategy.signal_utils import calculate_macd_signals, is_signal_current
from app.tools.data_loader import load_ticker_data
import polars as pl
from typing import Dict, Any, Optional

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
            return calculate_macd_signals(
                data.clone(),
                params["short_window"],
                params["long_window"],
                params["signal_window"],
                config=strategy_config
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
            data = load_ticker_data(ticker, config, log)
            if data is None:
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

## 2. Register Strategies with Factory

Create a module to register all strategies with the factory:

```python
# app/strategies/register_strategies.py
from app.tools.strategy.strategy_factory import StrategyFactory
from app.strategies.ma_cross.sma_strategy import SMAStrategy
from app.strategies.ma_cross.ema_strategy import EMAStrategy
from app.strategies.macd.macd_strategy import MACDStrategy

def register_all_strategies():
    """Register all strategy implementations with the factory"""
    StrategyFactory.register_strategy("SMA", SMAStrategy())
    StrategyFactory.register_strategy("EMA", EMAStrategy())
    StrategyFactory.register_strategy("MACD", MACDStrategy())
```

## 3. Update Scanner Processing

Refactor the scanner processing to use the strategy pattern:

```python
# app/ma_cross/tools/scanner_processing.py
import os
from datetime import datetime
import polars as pl
from typing import Tuple, List, Dict, Callable, Optional
from app.utils import get_path, get_filename
from app.tools.file_utils import is_file_from_today
from app.tools.strategy.strategy_factory import StrategyFactory
from app.tools.schema_handler import SchemaHandler

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

## 4. Update Scanner Main Module

Update the main scanner module to use the new schema handler and strategy pattern:

```python
# app/ma_cross/1_scanner.py (partial update)
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.tools.schema_handler import SchemaHandler
from app.strategies.register_strategies import register_all_strategies
from app.ma_cross.tools.scanner_processing import (
    load_existing_results,
    process_ticker,
    export_results
)

def process_scanner() -> bool:
    """
    Process each ticker in the scanner list with appropriate strategy.
    Creates a DataFrame with results and exports to CSV.
    
    Returns:
        bool: True if execution successful, raises exception otherwise
    """
    log = None
    log_close = None
    
    try:
        # Initialize logging
        log, log_close, _, _ = setup_logging('ma_cross', '2_scanner.log')
        if not log or not log_close:
            raise RuntimeError("Failed to initialize logging")
        
        # Register all strategies
        register_all_strategies()
        
        # Read scanner data using polars with explicit schema handling
        scanner_df = pl.read_csv(
            f'./csv/strategies/{config["PORTFOLIO"]}',
            infer_schema_length=10000,
            try_parse_dates=True,
            ignore_errors=True,
            truncate_ragged_lines=True,
            schema_overrides={
                'Start Value': pl.Float64,
                'End Value': pl.Float64,
                'Return': pl.Float64,
                'Annual Return': pl.Float64,
                'Sharpe Ratio': pl.Float64,
                'Max Drawdown': pl.Float64,
                'Calmar Ratio': pl.Float64,
                'Recovery Factor': pl.Float64,
                'Profit Factor': pl.Float64,
                'Common Sense Ratio': pl.Float64,
                'Win Rate': pl.Float64,
                'Short Window': pl.Int64,
                'Long Window': pl.Int64
            }
        )
        log(f"Loaded scanner list: {config["PORTFOLIO"]}")
        
        # Load existing results if available
        existing_tickers, results_data = load_existing_results(config, log)
        
        # Detect schema type
        schema_info = SchemaHandler.detect_schema(scanner_df)
        
        # Validate schema
        if not schema_info["has_ticker"]:
            raise ValueError("Missing required Ticker column")
            
        if not any([schema_info["is_new_schema"], schema_info["is_legacy_schema"], schema_info["is_minimal_schema"]]):
            raise ValueError("Invalid schema: Must contain either (Short Window, Long Window) or (SMA_FAST, SMA_SLOW, EMA_FAST, EMA_SLOW)")
            
        log(f"Schema type: {'Minimal' if schema_info['is_minimal_schema'] else 'New' if schema_info['is_new_schema'] else 'Legacy'}")
        
        # Standardize schema
        scanner_df = SchemaHandler.standardize_schema(scanner_df, schema_info)
        
        # Process tickers
        # ... (rest of the function remains similar but uses the new process_ticker)
```

## 5. Update Export Results Function

Update the export results function to handle different strategy types:

```python
# app/ma_cross/tools/scanner_processing.py (continued)
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
    
    # Rest of the function remains similar but handles MACD strategy type
```

## 6. Update Strategies Update Portfolios

Update the strategies update_portfolios.py to use the new strategy pattern:

```python
# app/strategies/tools/summary_processing.py
from app.tools.strategy.strategy_factory import StrategyFactory
from typing import List, Dict, Any, Callable, Optional

def process_ticker_portfolios(ticker: str, strategy: Dict[str, Any], config: Dict[str, Any], log: Callable) -> Optional[List[Dict[str, Any]]]:
    """
    Process a ticker with the appropriate strategy.
    
    Args:
        ticker: Ticker symbol to process
        strategy: Strategy parameters
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        List of portfolio results or None if processing fails
    """
    # Determine strategy type
    strategy_type = strategy.get("STRATEGY_TYPE")
    if not strategy_type:
        # Legacy detection based on parameters
        if strategy.get('SMA_FAST') is not None and strategy.get('USE_SMA', False):
            strategy_type = "SMA"
        elif strategy.get('EMA_FAST') is not None and not strategy.get('USE_SMA', True):
            strategy_type = "EMA"
        elif strategy.get('MACD_FAST') is not None and strategy.get('SIGNAL_WINDOW') is not None:
            strategy_type = "MACD"
        else:
            log(f"Could not determine strategy type for {ticker}", "error")
            return None
    
    # Create strategy instance
    strategy_instance = StrategyFactory.create_strategy(strategy_type)
    if strategy_instance is None:
        log(f"Unsupported strategy type: {strategy_type}", "error")
        return None
    
    # Extract parameters based on strategy type
    params = {}
    if strategy_type == "SMA":
        params = {
            "short_window": strategy.get('SMA_FAST'),
            "long_window": strategy.get('SMA_SLOW')
        }
    elif strategy_type == "EMA":
        params = {
            "short_window": strategy.get('EMA_FAST'),
            "long_window": strategy.get('EMA_SLOW')
        }
    elif strategy_type == "MACD":
        params = {
            "short_window": strategy.get('MACD_FAST'),
            "long_window": strategy.get('MACD_SLOW'),
            "signal_window": strategy.get('SIGNAL_WINDOW')
        }
        # Add RSI parameters if available
        if strategy.get('RSI_WINDOW') is not None and strategy.get('RSI_THRESHOLD') is not None:
            params["rsi_window"] = strategy.get('RSI_WINDOW')
            params["rsi_threshold"] = strategy.get('RSI_THRESHOLD')
    
    # Add logging to config
    strategy_config = config.copy()
    strategy_config["log"] = log
    
    # Process signals using the strategy
    result = strategy_instance.process_signals(ticker, params, strategy_config)
    if result is None:
        return None
    
    # Convert to portfolio format
    # ... (implementation specific to portfolio processing)
    
    return [result]  # Return as a list for consistency
```

## 7. Update Concurrency Review

Update the concurrency review module to use the new strategy pattern:

```python
# app/concurrency/tools/strategy_processor.py
from app.tools.strategy.strategy_factory import StrategyFactory
from typing import Dict, Any, List, Callable, Optional

def process_strategy(strategy_data: Dict[str, Any], config: Dict[str, Any], log: Callable) -> Optional[Dict[str, Any]]:
    """
    Process a strategy with the appropriate strategy type.
    
    Args:
        strategy_data: Strategy data including parameters
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Processed strategy data or None if processing fails
    """
    ticker = strategy_data.get("TICKER")
    if not ticker:
        log("Missing ticker in strategy data", "error")
        return None
    
    # Determine strategy type
    strategy_type = strategy_data.get("STRATEGY_TYPE")
    if not strategy_type:
        # Legacy detection based on parameters
        if strategy_data.get('SMA_FAST') is not None and strategy_data.get('USE_SMA', False):
            strategy_type = "SMA"
        elif strategy_data.get('EMA_FAST') is not None and not strategy_data.get('USE_SMA', True):
            strategy_type = "EMA"
        elif strategy_data.get('MACD_FAST') is not None and strategy_data.get('SIGNAL_WINDOW') is not None:
            strategy_type = "MACD"
        else:
            log(f"Could not determine strategy type for {ticker}", "error")
            return None
    
    # Create strategy instance
    strategy_instance = StrategyFactory.create_strategy(strategy_type)
    if strategy_instance is None:
        log(f"Unsupported strategy type: {strategy_type}", "error")
        return None
    
    # Extract parameters based on strategy type
    params = {}
    if strategy_type == "SMA":
        params = {
            "short_window": strategy_data.get('SMA_FAST'),
            "long_window": strategy_data.get('SMA_SLOW')
        }
    elif strategy_type == "EMA":
        params = {
            "short_window": strategy_data.get('EMA_FAST'),
            "long_window": strategy_data.get('EMA_SLOW')
        }
    elif strategy_type == "MACD":
        params = {
            "short_window": strategy_data.get('MACD_FAST'),
            "long_window": strategy_data.get('MACD_SLOW'),
            "signal_window": strategy_data.get('SIGNAL_WINDOW')
        }
        # Add RSI parameters if available
        if strategy_data.get('RSI_WINDOW') is not None and strategy_data.get('RSI_THRESHOLD') is not None:
            params["rsi_window"] = strategy_data.get('RSI_WINDOW')
            params["rsi_threshold"] = strategy_data.get('RSI_THRESHOLD')
    
    # Add logging to config
    strategy_config = config.copy()
    strategy_config["log"] = log
    
    # Process signals using the strategy
    return strategy_instance.process_signals(ticker, params, strategy_config)
```

## Implementation Checklist

- [ ] Create strategy implementation classes:
  - [ ] `app/strategies/ma_cross/sma_strategy.py`
  - [ ] `app/strategies/ma_cross/ema_strategy.py`
  - [ ] `app/strategies/macd/macd_strategy.py`
- [ ] Create strategy registration module:
  - [ ] `app/strategies/register_strategies.py`
- [ ] Update scanner processing:
  - [ ] `app/ma_cross/tools/scanner_processing.py`
- [ ] Update scanner main module:
  - [ ] `app/ma_cross/1_scanner.py`
- [ ] Update strategies module:
  - [ ] `app/strategies/tools/summary_processing.py`
  - [ ] `app/strategies/update_portfolios.py`
- [ ] Update concurrency module:
  - [ ] `app/concurrency/tools/strategy_processor.py`
  - [ ] `app/concurrency/review.py`
- [ ] Document updated modules with proper docstrings