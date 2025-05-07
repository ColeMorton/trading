# Updated Implementation Plan: Optimizing Data Download in MA Cross Strategy

After reviewing additional modules in the system (`app/ma_cross/1_get_portfolios.py`, `app/strategies/update_portfolios.py` and `app/concurrency/review.py`), I'm updating the optimization plan to ensure consistency with the broader system architecture and existing patterns.

## Problem Statement
When multiple tickers are defined in CONFIG or USE_SYNTHETIC=True, the system makes redundant calls to download data for each strategy type (SMA, EMA), causing inefficiency and potential API rate limiting issues.

## Solution Overview
Create a centralized data retrieval mechanism that fetches all required ticker data once per execution and passes it to the strategy execution functions, consistent with the patterns used in other modules.

## Implementation Plan

### 1. Create a Data Provider Context Manager

**File: `app/tools/data_context.py`**

```python
"""
Data Context Module

This module provides a context manager for retrieving and caching financial data.
It ensures data is downloaded only once per execution and shared across strategy types.
"""

from typing import Dict, List, Union, Tuple, Callable, Optional, Any, ContextManager
from contextlib import contextmanager
import polars as pl
from app.tools.data_types import DataConfig
from app.tools.get_data import get_data
from app.tools.error_context import error_context
from app.tools.exceptions import DataRetrievalError

class DataCache:
    """
    Data cache class that handles centralized data storage.
    
    This class follows the Single Responsibility Principle by focusing solely on
    data caching operations.
    """
    
    def __init__(self):
        """Initialize an empty data cache."""
        self._data_cache = {}  # In-memory cache for current execution
    
    def get(self, key: str) -> Optional[Any]:
        """Get data from cache if available."""
        return self._data_cache.get(key)
    
    def set(self, key: str, data: Any) -> None:
        """Store data in cache."""
        self._data_cache[key] = data
    
    def has(self, key: str) -> bool:
        """Check if key exists in cache."""
        return key in self._data_cache

# Global cache instance (module-level singleton)
_data_cache = DataCache()

@contextmanager
def data_context(
    tickers: Union[str, List[str]], 
    config: DataConfig, 
    log: Callable
) -> ContextManager[Union[pl.DataFrame, Dict[str, pl.DataFrame], Tuple[pl.DataFrame, str]]]:
    """
    Context manager for retrieving and caching financial data.
    
    Args:
        tickers: Ticker symbol(s) or synthetic ticker name
        config: Configuration dictionary
        log: Logging function
        
    Yields:
        The retrieved data in the appropriate format
        
    Raises:
        DataRetrievalError: If data retrieval fails
    """
    # Create a cache key based on tickers
    cache_key = tickers if isinstance(tickers, str) else ','.join(sorted(tickers))
    
    # Check if data is already in cache
    if _data_cache.has(cache_key):
        log(f"Using cached data for: {tickers}")
        yield _data_cache.get(cache_key)
        return
    
    # Retrieve data if not in cache
    with error_context(f"Retrieving data for {tickers}", log, {Exception: DataRetrievalError}):
        log(f"Retrieving data for: {tickers}")
        data = get_data(tickers, config, log)
        
        # Cache the retrieved data
        _data_cache.set(cache_key, data)
        
        # Yield the data to the caller
        yield data
```

### 2. Update `app/tools/exceptions.py` to Add DataRetrievalError

```python
class DataRetrievalError(Exception):
    """Raised when there's an error retrieving financial data."""
    pass
```

### 3. Modify `run_strategies()` in `app/ma_cross/1_get_portfolios.py`

```python
def run_strategies(config: Dict[str, Any] = None) -> bool:
    """Run analysis with strategies specified in STRATEGY_TYPES in sequence.
    
    Returns:
        bool: True if execution successful, False otherwise
        
    Raises:
        ConfigurationError: If the configuration is invalid
        StrategyProcessingError: If there's an error processing a strategy
        PortfolioLoadError: If the portfolio cannot be loaded
        ExportError: If results cannot be exported
        TradingSystemError: For other unexpected errors
    """
    with logging_context(
        module_name='ma_cross',
        log_file='1_get_portfolios.log'
    ) as log:
        # Initialize config
        with error_context("Initializing configuration", log, {Exception: ConfigurationError}):
            # Create a normalized copy of the default config
            config_copy = CONFIG.copy()
            config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
            config_copy = normalize_config(config_copy)
        
        # Process synthetic configuration
        with error_context("Processing synthetic configuration", log, {ValueError: SyntheticTickerError}):
            base_config = process_synthetic_config(config_copy, log)
        
        # Determine tickers to process
        tickers_to_process = base_config.get("TICKER")
        if base_config.get("USE_SYNTHETIC", False):
            ticker1 = base_config.get('TICKER_1')
            ticker2 = base_config.get('TICKER_2')
            if ticker1 and ticker2:
                tickers_to_process = f"{ticker1}_{ticker2}"
            else:
                synthetic_ticker_name = base_config.get("TICKER")
                if isinstance(synthetic_ticker_name, str) and "_" in synthetic_ticker_name:
                    tickers_to_process = synthetic_ticker_name
        
        # Import the data context manager
        from app.tools.data_context import data_context
        
        # Execute strategies with data context
        with error_context("Executing strategies", log, {Exception: StrategyProcessingError}):
            # Use data context to retrieve data once
            with data_context(tickers_to_process, base_config, log) as ticker_data:
                all_portfolios = execute_all_strategies_with_data(base_config, ticker_data, log)
        
        # Export results
        if all_portfolios:
            with error_context("Filtering and exporting portfolios", log, {Exception: ExportError}):
                filtered_portfolios = filter_portfolios(all_portfolios, base_config, log)
                export_best_portfolios(filtered_portfolios, base_config, log)
        
        return True
```
### 4. Create a New Function `execute_all_strategies_with_data()` in `app/ma_cross/1_get_portfolios.py`

```python
def execute_all_strategies_with_data(
    config: Config, 
    pre_loaded_data: Union[pl.DataFrame, Dict[str, pl.DataFrame], Tuple[pl.DataFrame, str]],
    log: callable
) -> List[Dict[str, Any]]:
    """Execute all strategies using pre-loaded data.
    
    Args:
        config: Configuration dictionary
        pre_loaded_data: Pre-loaded ticker data
        log: Logging function
        
    Returns:
        List of portfolio dictionaries
    """
    strategy_types = get_strategy_types(config, log)
    log(f"Running strategies in sequence: {' -> '.join(strategy_types)}")
    
    all_portfolios = []
    
    for strategy_type in strategy_types:
        log(f"Running {strategy_type} strategy analysis...")
        strategy_config = {**config}
        strategy_config["STRATEGY_TYPE"] = strategy_type
        
        # Pass pre-loaded data to execute_strategy
        portfolios = execute_strategy(strategy_config, strategy_type, log, pre_loaded_data)
        log(f"{strategy_type} portfolios: {len(portfolios) if portfolios else 0}", "info")
        
        if portfolios:
            all_portfolios.extend(portfolios)
    
    if not all_portfolios:
        log("No portfolios returned from any strategy. Filtering criteria might be too strict.", "warning")
    
    return all_portfolios
```

### 5. Modify `execute_strategy()` in `app/ma_cross/tools/strategy_execution.py`

```python
def execute_strategy(
    config: Config,
    strategy_type: str,
    log: callable,
    pre_loaded_data: Union[pl.DataFrame, Dict[str, pl.DataFrame], Tuple[pl.DataFrame, str]] = None
) -> List[Dict[str, Any]]:
    """Execute a trading strategy for all tickers.

    Args:
        config (Config): Configuration for the analysis
        strategy_type (str): Strategy type (e.g., 'EMA', 'SMA')
        log (callable): Logging function
        pre_loaded_data: Optional pre-loaded data for all tickers

    Returns:
        List[Dict[str, Any]]: List of best portfolios found after filtering.
    """
    all_portfolios: List[Dict[str, Any]] = []
    
    # Use pre-loaded data if provided, otherwise retrieve it
    if pre_loaded_data is not None:
        data_result = pre_loaded_data
        log(f"Using pre-loaded data for {strategy_type} strategy")
    else:
        # Determine the list of tickers to process
        tickers_to_process = get_tickers_to_process(config, log)
        if not tickers_to_process:
            return []
            
        # Import the data context manager
        from app.tools.data_context import data_context
        
        # Use data context to retrieve data
        with error_context(f"Retrieving data for {tickers_to_process}", log, {Exception: StrategyProcessingError}):
            with data_context(tickers_to_process, config, log) as data_result:
                # Process the data based on its type (this will be executed inside the context)
                return process_strategy_data(data_result, config, strategy_type, log)

    # If we have pre-loaded data, process it directly
    return process_strategy_data(data_result, config, strategy_type, log)
```

### 6. Add Helper Functions to `app/ma_cross/tools/strategy_execution.py`

```python
def process_strategy_data(
    data_result: Union[pl.DataFrame, Dict[str, pl.DataFrame], Tuple[pl.DataFrame, str]],
    config: Config,
    strategy_type: str,
    log: callable
) -> List[Dict[str, Any]]:
    """Process strategy data and return portfolios.
    
    Args:
        data_result: Data for the strategy
        config: Configuration dictionary
        strategy_type: Strategy type (e.g., 'EMA', 'SMA')
        log: Logging function
        
    Returns:
        List of portfolio dictionaries
    """
    all_portfolios: List[Dict[str, Any]] = []
    
    # Process the data based on its type
    if isinstance(data_result, tuple):
        # Synthetic ticker case
        process_synthetic_ticker_data(data_result, config, strategy_type, log, all_portfolios)
    elif isinstance(data_result, dict):
        # Multiple tickers case
        process_multiple_ticker_data(data_result, config, strategy_type, log, all_portfolios)
    elif isinstance(data_result, pl.DataFrame):
        # Single ticker case
        process_single_ticker_data(data_result, config, strategy_type, log, all_portfolios)
    else:
        log(f"Unexpected data structure returned: {type(data_result)}", "error")
        return []

    # Apply filtering and selection
    return apply_filtering_and_selection(all_portfolios, config, log)

def get_tickers_to_process(config: Config, log: callable) -> Union[str, List[str], None]:
    """Determine the list of tickers to process based on configuration.
    
    Args:
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Ticker(s) to process or None if invalid
    """
    if config.get("USE_SYNTHETIC", False):
        # For synthetic, get the component tickers
        ticker1 = config.get('TICKER_1')
        ticker2 = config.get('TICKER_2')
        if not ticker1 or not ticker2:
            # If not in config, try to extract from TICKER if it's a synthetic name
            synthetic_ticker_name = config.get("TICKER")
            if isinstance(synthetic_ticker_name, str) and "_" in synthetic_ticker_name:
                ticker_parts = synthetic_ticker_name.split("_")
                if len(ticker_parts) == 2:
                    ticker1, ticker2 = ticker_parts
                    config['TICKER_1'] = ticker1  # Update config
                    config['TICKER_2'] = ticker2  # Update config
                else:
                    log(f"Invalid synthetic ticker format in config: {synthetic_ticker_name}", "error")
                    return None
            else:
                log("USE_SYNTHETIC is True but TICKER_1 and TICKER_2 are not specified and TICKER is not a synthetic name.", "error")
                return None
        return f"{ticker1}_{ticker2}"  # Pass the synthetic name to get_data
    else:
        # Use the TICKER(s) from the config
        tickers_to_process = config.get("TICKER")
        if tickers_to_process is None:
            log("No TICKER specified in configuration.", "error")
            return None
        if not isinstance(tickers_to_process, (str, list)):
            log(f"Invalid TICKER format in configuration: {tickers_to_process}. Must be string or list.", "error")
            return None
        return tickers_to_process
```

```python
def process_synthetic_ticker_data(
    data_result: Tuple[pl.DataFrame, str],
    config: Config,
    strategy_type: str,
    log: callable,
    all_portfolios: List[Dict[str, Any]]
):
    """Process synthetic ticker data and add portfolios to the result list.
    
    Args:
        data_result: Tuple of (synthetic_data, synthetic_name)
        config: Configuration dictionary
        strategy_type: Strategy type (e.g., 'EMA', 'SMA')
        log: Logging function
        all_portfolios: List to append portfolios to
    """
    synthetic_data, synthetic_ticker_name = data_result
    log(f"Processing synthetic data for {synthetic_ticker_name}")
    ticker_config = config.copy()
    ticker_config["TICKER"] = synthetic_ticker_name
    ticker_config["STRATEGY_TYPE"] = strategy_type
    portfolios_df = process_ticker_portfolios(synthetic_data, synthetic_ticker_name, ticker_config, log)
    if portfolios_df is not None:
        all_portfolios.extend(portfolios_df.to_dicts())

def process_multiple_ticker_data(
    data_result: Dict[str, pl.DataFrame],
    config: Config,
    strategy_type: str,
    log: callable,
    all_portfolios: List[Dict[str, Any]]
):
    """Process multiple ticker data and add portfolios to the result list.
    
    Args:
        data_result: Dictionary of ticker data frames
        config: Configuration dictionary
        strategy_type: Strategy type (e.g., 'EMA', 'SMA')
        log: Logging function
        all_portfolios: List to append portfolios to
    """
    log(f"Processing data for multiple tickers: {list(data_result.keys())}")
    for ticker, data in data_result.items():
        log(f"Processing {strategy_type} strategy for ticker: {ticker}")
        ticker_config = config.copy()
        ticker_config["TICKER"] = ticker
        ticker_config["STRATEGY_TYPE"] = strategy_type
        portfolios_df = process_ticker_portfolios(data, ticker, ticker_config, log)
        if portfolios_df is not None:
            all_portfolios.extend(portfolios_df.to_dicts())

def process_single_ticker_data(
    data_result: pl.DataFrame,
    config: Config,
    strategy_type: str,
    log: callable,
    all_portfolios: List[Dict[str, Any]]
):
    """Process single ticker data and add portfolios to the result list.
    
    Args:
        data_result: DataFrame for a single ticker
        config: Configuration dictionary
        strategy_type: Strategy type (e.g., 'EMA', 'SMA')
        log: Logging function
        all_portfolios: List to append portfolios to
    """
    ticker = config.get("TICKER")
    if isinstance(ticker, list) and len(ticker) == 1:
        ticker = ticker[0]
    log(f"Processing data for single ticker: {ticker}")
    ticker_config = config.copy()
    ticker_config["TICKER"] = ticker
    ticker_config["STRATEGY_TYPE"] = strategy_type
    portfolios_df = process_ticker_portfolios(data_result, ticker, ticker_config, log)
    if portfolios_df is not None:
        all_portfolios.extend(portfolios_df.to_dicts())

def apply_filtering_and_selection(
    all_portfolios: List[Dict[str, Any]],
    config: Config,
    log: callable
) -> List[Dict[str, Any]]:
    """Apply filtering and selection to portfolios.
    
    Args:
        all_portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Filtered and selected portfolios
    """
    if not all_portfolios:
        log("No portfolios generated from any ticker.", "warning")
        return []

    # Convert the list of dictionaries to a Polars DataFrame for filtering and selection
    all_portfolios_df = pl.DataFrame(all_portfolios)
    log(f"Total portfolios generated: {len(all_portfolios_df)}")

    # Apply filtering
    log("Applying filters to collected portfolios.")
    filtered_portfolios_df = apply_filters(all_portfolios_df, config, log)
    
    log(f"Portfolios remaining after filtering: {len(filtered_portfolios_df)}")
    if len(filtered_portfolios_df) == 0:
        log("No portfolios remain after filtering.", "warning")
        return []

    # Get best portfolio(s)
    best_portfolios_list = get_best_portfolio(filtered_portfolios_df, config, log)
    if best_portfolios_list is not None:
        log(f"Found {len(best_portfolios_list)} best portfolio(s).")
        return best_portfolios_list
    else:
        log("No best portfolios found after selection.", "warning")
        return []

def apply_filters(df: pl.DataFrame, config: Config, log: callable) -> pl.DataFrame:
    """Apply filters to the portfolios DataFrame.
    
    Args:
        df: DataFrame of portfolios
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Filtered DataFrame
    """
    filtered_df = df.clone()  # Start with a copy
    
    # Define filter configurations
    filter_configs = [
        # (config_key, column_name, data_type, multiplier, message_prefix)
        ("WIN_RATE", "Win Rate [%]", pl.Float64, 100, "Filtered portfolios with win rate"),
        ("TRADES", "Total Trades", pl.Int64, 1, "Filtered portfolios with at least"),
        ("EXPECTANCY_PER_TRADE", "Expectancy Per Trade", pl.Float64, 1, "Filtered portfolios with expectancy per trade"),
        ("PROFIT_FACTOR", "Profit Factor", pl.Float64, 1, "Filtered portfolios with profit factor"),
        ("SCORE", "Score", pl.Float64, 1, "Filtered portfolios with score"),
        ("SORTINO_RATIO", "Sortino Ratio", pl.Float64, 1, "Filtered portfolios with Sortino ratio"),
        ("BEATS_BNH", "Beats BNH [%]", pl.Float64, 1, "Filtered portfolios with Beats BNH percentage")
    ]
    
    # Apply filters from the MINIMUMS dictionary
    if "MINIMUMS" in config:
        minimums = config["MINIMUMS"]
        
        # Apply each filter from the configuration
        for config_key, column_name, data_type, multiplier, message_prefix in filter_configs:
            if config_key in minimums:
                filtered_df = apply_filter(
                    filtered_df,
                    column_name,
                    minimums[config_key],
                    data_type,
                    multiplier,
                    message_prefix,
                    log
                )
    
    return filtered_df

def apply_filter(
    df: pl.DataFrame,
    column_name: str,
    min_value: float,
    data_type: type,
    multiplier: float = 1,
    message_prefix: str = "",
    log: callable = None
) -> pl.DataFrame:
    """Apply a filter to the dataframe based on a minimum value.
    
    Args:
        df: DataFrame to filter
        column_name: Column to filter on
        min_value: Minimum value
        data_type: Data type for casting
        multiplier: Value multiplier
        message_prefix: Log message prefix
        log: Logging function
        
    Returns:
        Filtered DataFrame
    """
    if column_name in df.columns:
        adjusted_value = min_value * multiplier
        df = df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)
        
        # Format the message based on the filter type
        if log and message_prefix:
            if "win rate" in message_prefix.lower():
                log(f"{message_prefix} >= {adjusted_value}%")
            elif "trades" in message_prefix.lower():
                log(f"{message_prefix} >= {int(adjusted_value)}")
            else:
                log(f"{message_prefix} >= {adjusted_value}")
        
        return df
    return df
```

## SOLID Principles Implementation

1. **Single Responsibility Principle**:
   - Created `data_context` context manager with the sole responsibility of managing data retrieval and caching
   - Split `execute_strategy` into smaller functions with specific responsibilities
   - Each helper function has a single, well-defined purpose
   - Separated data caching (DataCache class) from data retrieval (data_context function)

2. **Open/Closed Principle**:
   - Extended functionality by adding new components rather than modifying existing ones
   - `execute_strategy` now accepts pre-loaded data without changing its core behavior
   - New functions can be added without modifying existing ones

3. **Liskov Substitution Principle**:
   - Maintained consistent interfaces for data handling functions
   - Ensured that all data processing functions follow the same parameter patterns
   - Context manager pattern is consistent with other context managers in the system

4. **Interface Segregation Principle**:
   - Created focused helper functions that handle specific data types
   - Each function only depends on the parameters it actually needs
   - Context manager provides a clean interface for data retrieval

5. **Dependency Inversion Principle**:
   - `data_context` abstracts the data retrieval mechanism
   - Strategy execution depends on the data abstraction, not the concrete implementation
   - Error handling is consistent with the rest of the system

## DRY, KISS, and YAGNI Principles

1. **DRY (Don't Repeat Yourself)**:
   - Eliminated duplicate data retrieval code
   - Centralized filtering logic in helper functions
   - Reused existing functions where possible
   - Consistent with patterns used in other modules

2. **KISS (Keep It Simple, Stupid)**:
   - Used clear, descriptive function names
   - Maintained straightforward control flow
   - Avoided complex conditional logic
   - Used familiar context manager pattern consistent with other modules

3. **YAGNI (You Aren't Gonna Need It)**:
   - Focused only on solving the specific problem of redundant data downloads
   - Avoided adding unnecessary features or complexity
   - Kept the implementation focused on the immediate requirements
   - Leveraged existing error handling and logging patterns

## System Integration Considerations

1. **Consistency with Existing Modules**:
   - Used context manager pattern similar to `portfolio_context` in `app/concurrency/review.py`
   - Followed the same error handling pattern with `error_context`
   - Maintained consistent synthetic ticker handling with `app/strategies/update_portfolios.py`
   - Used the same configuration processing approach

2. **Error Handling**:
   - Added `DataRetrievalError` to the exception hierarchy
   - Used `error_context` for consistent error handling
   - Maintained the same error propagation pattern

3. **Synthetic Ticker Support**:
   - Maintained compatibility with the synthetic ticker processing in other modules
   - Ensured the data context works with both regular and synthetic tickers

### 7. Modify `run_analysis()` in `app/concurrency/review.py`

```python
def run_analysis(config: Dict[str, Any]) -> bool:
    """Run concurrency analysis with the given configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        bool: True if analysis completed successfully, False otherwise
        
    Raises:
        ConfigurationError: If the configuration is invalid
        PortfolioLoadError: If the portfolio cannot be loaded
        TradingSystemError: For other unexpected errors
    """
    # Ensure configuration is normalized
    config = normalize_config(config)
    
    # Get log subdirectory from BASE_DIR if specified
    log_subdir = None
    if config["BASE_DIR"] != get_project_root():
        log_subdir = Path(config["BASE_DIR"]).name
    
    with logging_context(
        module_name="concurrency_review",
        log_file="review.log",
        level=logging.INFO,
        log_subdir=log_subdir
    ) as log:
        # Validate configuration
        log("Validating configuration...", "info")
        with error_context(
            "Validating configuration",
            log,
            {Exception: SystemConfigurationError},
            reraise=True
        ):
            validated_config = validate_config(config)

        # Get portfolio filename from validated config
        portfolio_filename = validated_config["PORTFOLIO"]
        
        # Use the enhanced portfolio loader via context manager
        with error_context(
            "Loading portfolio",
            log,
            {PortfolioLoadError: PortfolioLoadError},
            reraise=True
        ):
            with portfolio_context(portfolio_filename, log, validated_config) as portfolio_data:
                # Process each strategy in the portfolio to check for synthetic tickers
                if portfolio_data:
                    log("Checking for synthetic tickers in portfolio strategies...", "info")
                    
                    # Also set synthetic ticker flag in the main config if any synthetic tickers are found
                    has_synthetic_tickers = False
                    
                    # Collect all tickers that need data retrieval
                    all_tickers = []
                    
                    for strategy in portfolio_data:
                        if 'TICKER' in strategy:
                            ticker = strategy['TICKER']
                            # Check if this is a synthetic ticker
                            if detect_synthetic_ticker(ticker):
                                has_synthetic_tickers = True
                                try:
                                    # Process the synthetic ticker
                                    ticker1, ticker2 = process_synthetic_ticker(ticker)
                                    log(f"Detected synthetic ticker: {ticker} (components: {ticker1}, {ticker2})", "info")
                                    
                                    # Update strategy config for synthetic ticker processing
                                    strategy["USE_SYNTHETIC"] = True
                                    strategy["TICKER_1"] = ticker1
                                    strategy["TICKER_2"] = ticker2
                                    
                                    # Also update the main config to indicate synthetic ticker usage
                                    validated_config["USE_SYNTHETIC"] = True
                                    
                                    # If this is the first synthetic ticker, set the main config ticker components
                                    if "TICKER_1" not in validated_config:
                                        validated_config["TICKER_1"] = ticker1
                                        validated_config["TICKER_2"] = ticker2
                                    
                                    # Add component tickers to the list for data retrieval
                                    all_tickers.extend([ticker1, ticker2])
                                        
                                except SyntheticTickerError as e:
                                    log(f"Invalid synthetic ticker format: {ticker} - {str(e)}", "warning")
                            else:
                                # Add regular ticker to the list
                                all_tickers.append(ticker)
                    
                    # Remove duplicates while preserving order
                    unique_tickers = []
                    for ticker in all_tickers:
                        if ticker not in unique_tickers:
                            unique_tickers.append(ticker)
                    
                    # If we found synthetic tickers, process the main config
                    if has_synthetic_tickers:
                        log("Processing synthetic ticker configuration for main analysis...", "info")
                        validated_config = process_synthetic_config(validated_config, log)
                    
                    # Import the data context manager
                    from app.tools.data_context import data_context
                    
                    # Pre-load all ticker data once if we have tickers to process
                    if unique_tickers:
                        log(f"Pre-loading data for all tickers: {unique_tickers}", "info")
                        with error_context("Pre-loading ticker data", log, {Exception: TradingSystemError}):
                            with data_context(unique_tickers, validated_config, log) as ticker_data:
                                # Run analysis with pre-loaded data
                                log("Starting concurrency analysis...", "info")
                                with error_context(
                                    "Running main analysis",
                                    log,
                                    {Exception: TradingSystemError},
                                    reraise=False
                                ):
                                    # Ensure the main function knows about synthetic tickers
                                    if validated_config.get("USE_SYNTHETIC", False):
                                        log(f"Running analysis with synthetic ticker support enabled", "info")
                                    
                                    # Pass pre-loaded data to main function
                                    result = main(validated_config, ticker_data)
                                    if result:
                                        log("Concurrency analysis completed successfully!", "info")
                                        return True
                                    else:
                                        log("Concurrency analysis failed", "error")
                                        return False
                    else:
                        # No tickers to process, run analysis without pre-loaded data
                        log("No tickers found for pre-loading, running analysis without pre-loaded data", "info")
                        result = main(validated_config)
                        if result:
                            log("Concurrency analysis completed successfully!", "info")
                            return True
                        else:
                            log("Concurrency analysis failed", "error")
                            return False
```

### 8. Update `main()` in `app/concurrency/tools/runner.py`

```python
def main(config, pre_loaded_data=None):
    """Run the main concurrency analysis.
    
    Args:
        config: Configuration dictionary
        pre_loaded_data: Optional pre-loaded ticker data
        
    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    # Use pre-loaded data if provided, otherwise retrieve it as needed
    # Pass pre-loaded data to any functions that retrieve ticker data
    
    # Rest of the main function implementation...
    
    return True
```

### 9. Modify `run()` in `app/strategies/update_portfolios.py`

```python
def run(portfolio: str) -> bool:
    """
    Process portfolio and generate portfolio summary.

    This function:
    1. Reads the portfolio
    2. Processes each ticker with appropriate strategy (SMA, EMA, or MACD)
    3. Detects and processes synthetic tickers (those containing an underscore)
    4. Calculates performance metrics and adjustments
    5. Exports combined results to CSV

    Args:
        portfolio (str): Name of the portfolio file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        PortfolioLoadError: If the portfolio cannot be loaded
        StrategyProcessingError: If there's an error processing a strategy
        SyntheticTickerError: If there's an issue with synthetic ticker processing
        ExportError: If results cannot be exported
        TradingSystemError: For other unexpected errors
    """
    with logging_context(
        module_name='strategies',
        log_file='update_portfolios.log'
    ) as log:
        # Get a normalized copy of the global config
        local_config = normalize_config(config.copy())
        
        # Use the enhanced portfolio loader with standardized error handling
        with error_context(
            "Loading portfolio",
            log,
            {FileNotFoundError: PortfolioLoadError}
        ):
            daily_df = load_portfolio_with_logging(portfolio, log, local_config)
            if not daily_df:
                return False

            # Collect all tickers that need data retrieval
            all_tickers = []
            for strategy in daily_df:
                ticker = strategy['TICKER']
                if detect_synthetic_ticker(ticker):
                    try:
                        ticker1, ticker2 = process_synthetic_ticker(ticker)
                        all_tickers.extend([ticker1, ticker2])
                    except SyntheticTickerError:
                        # Skip invalid synthetic tickers
                        pass
                else:
                    all_tickers.append(ticker)

            # Remove duplicates while preserving order
            unique_tickers = []
            for ticker in all_tickers:
                if ticker not in unique_tickers:
                    unique_tickers.append(ticker)

            # Import the data context manager
            from app.tools.data_context import data_context
            
            # Pre-load all ticker data once
            portfolios = []
            with error_context("Pre-loading ticker data", log, {Exception: StrategyProcessingError}):
                with data_context(unique_tickers, local_config, log) as ticker_data:
                    # Process each ticker using the pre-loaded data
                    for strategy in daily_df:
                        ticker = strategy['TICKER']
                        log(f"Processing {ticker}")
                        strategy_config = local_config.copy()
                        
                        # Process synthetic ticker if needed
                        if detect_synthetic_ticker(ticker):
                            try:
                                ticker1, ticker2 = process_synthetic_ticker(ticker)
                                strategy_config["USE_SYNTHETIC"] = True
                                strategy_config["TICKER_1"] = ticker1
                                strategy_config["TICKER_2"] = ticker2
                                log(f"Detected synthetic ticker: {ticker} (components: {ticker1}, {ticker2})")
                            except SyntheticTickerError as e:
                                log(f"Invalid synthetic ticker format: {ticker} - {str(e)}", "warning")
                        
                        # Process the ticker portfolio with pre-loaded data
                        with error_context(f"Processing ticker portfolio for {ticker}", log, {Exception: StrategyProcessingError}, reraise=False):
                            # Pass the pre-loaded data to process_ticker_portfolios
                            result = process_ticker_portfolios(ticker, strategy, strategy_config, log, ticker_data)
                            if result:
                                portfolios.extend(result)

            # Export results with config
            with error_context(
                "Exporting summary results",
                log,
                {Exception: ExportError},
                reraise=False
            ):
                success = export_summary_results(portfolios, portfolio, log, local_config)
                # Display strategy data as requested
                if success and portfolios:
                    log("=== Strategy Summary ===")
                    
                    # Sort portfolios by Score (descending) for main display
                    sorted_portfolios = sort_portfolios(portfolios, "Score", False)
                    
                    # Use standardized utility to filter and display open trades
                    open_trades_strategies = filter_open_trades(sorted_portfolios, log)
                    
                    # Use standardized utility to filter and display signal entries
                    # First get signal entries using the strategy_utils filter
                    temp_config = {"USE_CURRENT": True}
                    signal_entry_strategies = filter_portfolios_by_signal(sorted_portfolios, temp_config, log)
                    
                    # Then use the portfolio_results utility to process and display them
                    signal_entry_strategies = filter_signal_entries(signal_entry_strategies, open_trades_strategies, log)
                    
                    # Calculate and display breadth metrics
                    if sorted_portfolios:
                        calculate_breadth_metrics(
                            sorted_portfolios,
                            open_trades_strategies,
                            signal_entry_strategies,
                            log
                        )
                
            return success
```

### 10. Update `process_ticker_portfolios()` in `app/strategies/tools/summary_processing.py`

```python
def process_ticker_portfolios(ticker, strategy, config, log, pre_loaded_data=None):
    """Process ticker portfolios with optional pre-loaded data.
    
    Args:
        ticker: Ticker symbol
        strategy: Strategy configuration
        config: Global configuration
        log: Logging function
        pre_loaded_data: Optional pre-loaded ticker data
        
    Returns:
        List of portfolio dictionaries
    """
    # Use pre-loaded data if provided, otherwise retrieve it as needed
    # This ensures data is retrieved only once per execution
    
    # Rest of the function implementation...
    
    return portfolios
```

## Implementation Steps

1. Create the new `app/tools/data_context.py` file
2. Update `app/tools/exceptions.py` to add `DataRetrievalError`
3. Modify `run_strategies()` in `app/ma_cross/1_get_portfolios.py`
4. Add `execute_all_strategies_with_data()` to `app/ma_cross/1_get_portfolios.py`
5. Update `execute_strategy()` in `app/ma_cross/tools/strategy_execution.py`
6. Add the helper functions to `app/ma_cross/tools/strategy_execution.py`
7. Modify `run_analysis()` in `app/concurrency/review.py` to use `data_context`
8. Update `main()` in `app/concurrency/tools/runner.py` to accept pre-loaded data
9. Modify `run()` in `app/strategies/update_portfolios.py` to use `data_context`
10. Update `process_ticker_portfolios()` in `app/strategies/tools/summary_processing.py` to accept pre-loaded data

This updated implementation plan ensures that `yf.download` is called only once per execution across all three files, regardless of how many strategy types are being processed, while adhering to SOLID, DRY, KISS, and YAGNI principles and maintaining consistency with the existing system architecture.