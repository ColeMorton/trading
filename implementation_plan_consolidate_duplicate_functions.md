# Implementation Plan: Consolidating Duplicate Utility Functions

This implementation plan outlines the steps to consolidate duplicate utility functions across three key modules in the trading system:
1. `app/strategies/update_portfolios.py`
2. `app/concurrency/review.py`
3. `app/ma_cross/1_get_portfolios.py`

The plan is divided into isolated phases, each addressing a specific area of duplication. The goal is to standardize the codebase, remove duplication, and improve maintainability while strictly following KISS and SOLID principles.

## Phase 1: Create Standardized Configuration Management

**Current State:**
- `app/concurrency/review.py` uses a TypedDict-based approach
- `app/strategies/update_portfolios.py` and `app/ma_cross/1_get_portfolios.py` use dictionary-based approaches
- Configuration validation is inconsistent across modules

**Implementation Steps:**

1. Create a new module `app/tools/config_management.py` with:
   ```python
   """Configuration management utilities.
   
   This module provides standardized utilities for configuration management,
   including validation, normalization, and merging.
   """
   from typing import Dict, Any, TypeVar, Type, Optional
   from pathlib import Path
   import os
   
   from app.tools.exceptions import ConfigurationError
   
   T = TypeVar('T', bound=Dict[str, Any])
   
   def normalize_config(config: Dict[str, Any]) -> Dict[str, Any]:
       """Normalize configuration by ensuring standard fields are present.
       
       Args:
           config: Configuration dictionary
           
       Returns:
           Normalized configuration dictionary
       """
       normalized = config.copy()
       
       # Ensure BASE_DIR is absolute
       if "BASE_DIR" in normalized and not os.path.isabs(normalized["BASE_DIR"]):
           normalized["BASE_DIR"] = os.path.abspath(normalized["BASE_DIR"])
       
       return normalized
   
   def merge_configs(base_config: Dict[str, Any], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
       """Merge a base configuration with overrides.
       
       Args:
           base_config: Base configuration dictionary
           overrides: Optional overrides to apply
           
       Returns:
           Merged configuration dictionary
       """
       if not overrides:
           return base_config.copy()
           
       result = base_config.copy()
       
       for key, value in overrides.items():
           if isinstance(value, dict) and key in result and isinstance(result[key], dict):
               # Merge dictionaries for nested configs
               result[key].update(value)
           else:
               # Replace value for simple configs
               result[key] = value
               
       return result
   
   def resolve_portfolio_filename(portfolio_name: str) -> str:
       """Resolve portfolio filename by adding extension if needed.
       
       Args:
           portfolio_name: Portfolio name (with or without extension)
           
       Returns:
           Portfolio name with extension
       """
       if portfolio_name.endswith('.json') or portfolio_name.endswith('.csv'):
           return portfolio_name
           
       # Try to determine the extension
       csv_path = Path(f"csv/strategies/{portfolio_name}.csv")
       json_path = Path(f"json/portfolios/{portfolio_name}.json")
       
       if csv_path.exists():
           return f"{portfolio_name}.csv"
       elif json_path.exists():
           return f"{portfolio_name}.json"
       else:
           # Default to CSV if we can't determine
           return f"{portfolio_name}.csv"
   ```

2. Update all three modules to use these standardized configuration utilities.

## Phase 2: Consolidate Synthetic Ticker Processing

**Current State:**
- `app/strategies/update_portfolios.py` has inline code for processing synthetic tickers
- `app/ma_cross/1_get_portfolios.py` has dedicated functions for synthetic ticker processing

**Implementation Steps:**

1. Create a new module `app/tools/synthetic_ticker.py` with:
   ```python
   """Synthetic ticker processing utilities.
   
   This module provides utilities for processing synthetic tickers,
   which are combinations of two individual tickers.
   """
   from typing import Dict, Any, List, Union, Optional
   
   from app.tools.exceptions import SyntheticTickerError
   
   def process_synthetic_ticker(ticker: str) -> tuple[str, str]:
       """Process a synthetic ticker string into its components.
       
       Args:
           ticker: Synthetic ticker string (e.g., "BTC_MSTR")
           
       Returns:
           Tuple of (ticker1, ticker2)
           
       Raises:
           SyntheticTickerError: If the ticker format is invalid
       """
       if '_' not in ticker:
           raise SyntheticTickerError(f"Not a synthetic ticker: {ticker}")
           
       ticker_parts = ticker.split('_')
       if len(ticker_parts) != 2:
           raise SyntheticTickerError(f"Invalid synthetic ticker format: {ticker}")
           
       return ticker_parts[0], ticker_parts[1]
   
   def create_synthetic_ticker(ticker1: str, ticker2: str) -> str:
       """Create a synthetic ticker from two component tickers.
       
       Args:
           ticker1: First ticker
           ticker2: Second ticker
           
       Returns:
           Synthetic ticker string
       """
       return f"{ticker1}_{ticker2}"
   
   def process_synthetic_config(
       config: Dict[str, Any],
       log_func = None
   ) -> Dict[str, Any]:
       """Process configuration for synthetic ticker handling.
       
       Args:
           config: Configuration dictionary
           log_func: Optional logging function
           
       Returns:
           Updated configuration dictionary
           
       Raises:
           SyntheticTickerError: If there's an issue with synthetic ticker processing
       """
       if not config.get("USE_SYNTHETIC"):
           if log_func:
               log_func(f"Processing strategy for ticker: {config['TICKER']}")
           return config.copy()
       
       result = config.copy()
       
       if isinstance(config["TICKER"], list):
           # Process multiple synthetic tickers
           if "TICKER_2" not in config:
               raise SyntheticTickerError("TICKER_2 must be specified when USE_SYNTHETIC is True")
               
           synthetic_tickers = [create_synthetic_ticker(ticker, config['TICKER_2']) for ticker in config["TICKER"]]
           
           if log_func:
               log_func(f"Processing strategies for synthetic pairs: {synthetic_tickers}")
               
           result["TICKER"] = synthetic_tickers
           result["ORIGINAL_TICKERS"] = config["TICKER"].copy() if isinstance(config["TICKER"], list) else [config["TICKER"]]
           
       elif isinstance(config["TICKER"], str):
           # Process single synthetic ticker
           if "TICKER_2" not in config:
               raise SyntheticTickerError("TICKER_2 must be specified when USE_SYNTHETIC is True")
               
           synthetic_ticker = create_synthetic_ticker(config["TICKER"], config["TICKER_2"])
           
           if log_func:
               log_func(f"Processing strategy for synthetic pair: {synthetic_ticker}")
               
           result["TICKER"] = synthetic_ticker
           result["ORIGINAL_TICKERS"] = [config["TICKER"]]
           
       else:
           raise SyntheticTickerError("TICKER must be a string or a list when USE_SYNTHETIC is True")
           
       return result
   
   def detect_synthetic_ticker(ticker: str) -> bool:
       """Detect if a ticker is synthetic.
       
       Args:
           ticker: Ticker string
           
       Returns:
           True if the ticker is synthetic, False otherwise
       """
       return '_' in ticker
   ```

2. Update all three modules to use these standardized synthetic ticker utilities.

## Phase 3: Standardize Strategy Type Handling

**Current State:**
- `app/ma_cross/1_get_portfolios.py` has a dedicated function for getting strategy types
- Other modules handle strategy types inline

**Implementation Steps:**

1. Create a new module `app/tools/strategy_utils.py` with:
   ```python
   """Strategy utilities.
   
   This module provides utilities for working with trading strategies.
   """
   from typing import Dict, Any, List, Callable, Optional
   
   def get_strategy_types(
       config: Dict[str, Any],
       log_func = None,
       default_type: str = "SMA"
   ) -> List[str]:
       """Get strategy types from config with defaults.
       
       Args:
           config: Configuration dictionary
           log_func: Optional logging function
           default_type: Default strategy type if none specified
           
       Returns:
           List of strategy types
       """
       strategy_types = config.get("STRATEGY_TYPES", [])
       
       if not strategy_types:
           if log_func:
               log_func(f"No strategy types specified in config, defaulting to {default_type}")
           strategy_types = [default_type]
       
       if log_func:
           log_func(f"Using strategy types: {strategy_types}")
           
       return strategy_types
   
   def filter_portfolios_by_signal(
       portfolios: List[Dict[str, Any]],
       config: Dict[str, Any],
       log_func = None,
       signal_field: str = "Signal Entry"
   ) -> List[Dict[str, Any]]:
       """Filter portfolios based on signal field.
       
       Args:
           portfolios: List of portfolio dictionaries
           config: Configuration dictionary
           log_func: Optional logging function
           signal_field: Field to filter by (default: "Signal Entry")
           
       Returns:
           Filtered list of portfolio dictionaries
       """
       if not portfolios:
           return []
           
       if not config.get("USE_CURRENT", False):
           return portfolios
           
       original_count = len(portfolios)
       filtered = [p for p in portfolios if str(p.get(signal_field, '')).lower() == 'true']
       filtered_count = original_count - len(filtered)
       
       if filtered_count > 0 and log_func:
           log_func(f"Filtered out {filtered_count} portfolios with {signal_field} = False", "info")
           log_func(f"Remaining portfolios: {len(filtered)}", "info")
           
       return filtered
   ```

2. Update all three modules to use these standardized strategy utilities.

## Phase 4: Create Common Main Entry Point Pattern

**Current State:**
- All three modules have similar patterns for their main entry points
- Error handling and logging setup is duplicated

**Implementation Steps:**

1. Create a new module `app/tools/entry_point.py` with:
   ```python
   """Entry point utilities.
   
   This module provides utilities for creating standardized entry points
   for trading system modules.
   """
   import sys
   from typing import Dict, Any, Callable, Optional
   
   from app.tools.error_context import error_context
   
   def run_from_command_line(
       run_func: Callable,
       config: Dict[str, Any],
       operation_name: str,
       exit_on_failure: bool = True
   ) -> bool:
       """Run a function from the command line with standardized error handling.
       
       Args:
           run_func: Function to run
           config: Configuration dictionary
           operation_name: Name of the operation for error context
           exit_on_failure: Whether to exit with code 1 on failure
           
       Returns:
           True if execution successful, False otherwise
       """
       with error_context(
           f"Running {operation_name} from command line",
           lambda msg, level='info': print(f"[{level.upper()}] {msg}"),
           reraise=False
       ):
           success = run_func(config)
           if not success and exit_on_failure:
               sys.exit(1)
           return success
   ```

2. Update all three modules to use this standardized entry point utility.

## Phase 5: Consolidate Portfolio Result Processing

**Current State:**
- `app/strategies/update_portfolios.py` has complex result processing and display logic
- `app/ma_cross/1_get_portfolios.py` has simpler filtering and export logic

**Implementation Steps:**

1. Create a new module `app/tools/portfolio_results.py` with:
   ```python
   """Portfolio result processing utilities.
   
   This module provides utilities for processing and displaying portfolio results.
   """
   from typing import Dict, Any, List, Callable, Optional
   
   def sort_portfolios(
       portfolios: List[Dict[str, Any]],
       sort_by: str = "Score",
       ascending: bool = False
   ) -> List[Dict[str, Any]]:
       """Sort portfolios by a specified field.
       
       Args:
           portfolios: List of portfolio dictionaries
           sort_by: Field to sort by
           ascending: Whether to sort in ascending order
           
       Returns:
           Sorted list of portfolio dictionaries
       """
       if not portfolios:
           return []
           
       return sorted(
           portfolios,
           key=lambda x: x.get(sort_by, 0),
           reverse=not ascending
       )
   
   def filter_open_trades(
       portfolios: List[Dict[str, Any]],
       log_func = None
   ) -> List[Dict[str, Any]]:
       """Filter portfolios to only include open trades.
       
       Args:
           portfolios: List of portfolio dictionaries
           log_func: Optional logging function
           
       Returns:
           Filtered list of portfolio dictionaries
       """
       if not portfolios:
           return []
           
       # List strategies where Total Open Trades = 1 AND Signal Entry = false (to avoid duplicates)
       open_trades = [p for p in portfolios if
                     (p.get('Total Open Trades') == 1 or
                      (isinstance(p.get('Total Open Trades'), str) and p.get('Total Open Trades') == '1')) and
                     str(p.get('Signal Entry', '')).lower() != 'true']
       
       # Sort open trades by Score
       open_trades = sort_portfolios(open_trades, "Score", False)
       
       if log_func:
           if open_trades:
               log_func("\n=== Open Trades ===")
               log_func("Ticker, Strategy Type, Short Window, Long Window, Signal Window, Score")
               for p in open_trades:
                   ticker = p.get('Ticker', 'Unknown')
                   strategy_type = p.get('Strategy Type', 'Unknown')
                   short_window = p.get('Short Window', 'N/A')
                   long_window = p.get('Long Window', 'N/A')
                   signal_window = p.get('Signal Window', 'N/A')
                   score = p.get('Score', 0)
                   log_func(f"{ticker}, {strategy_type}, {short_window}, {long_window}, {signal_window}, {score:.4f}")
           else:
               log_func("\n=== No Open Trades found ===")
       
       return open_trades
   
   def filter_signal_entries(
       portfolios: List[Dict[str, Any]],
       open_trades: List[Dict[str, Any]] = None,
       log_func = None
   ) -> List[Dict[str, Any]]:
       """Filter portfolios to only include signal entries.
       
       Args:
           portfolios: List of portfolio dictionaries
           open_trades: Optional list of open trades for counting
           log_func: Optional logging function
           
       Returns:
           Filtered list of portfolio dictionaries
       """
       if not portfolios:
           return []
           
       # List strategies where Signal Entry = true
       signal_entries = [p for p in portfolios if str(p.get('Signal Entry', '')).lower() == 'true']
       
       # Count strategies per ticker if open_trades is provided
       if open_trades:
           ticker_counts = {}
           for p in open_trades:
               ticker = p.get('Ticker', 'Unknown')
               ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
           
           # Add the count to each strategy
           for p in signal_entries:
               ticker = p.get('Ticker', 'Unknown')
               p['open_trade_count'] = ticker_counts.get(ticker, 0)
       
       # Sort signal entry strategies by Score
       signal_entries = sort_portfolios(signal_entries, "Score", False)
       
       if log_func:
           if signal_entries:
               log_func("\n=== Signal Entries ===")
               log_func("Ticker, Strategy Type, Short Window, Long Window, Signal Window, Score, Total Open Trades")
               for p in signal_entries:
                   ticker = p.get('Ticker', 'Unknown')
                   strategy_type = p.get('Strategy Type', 'Unknown')
                   short_window = p.get('Short Window', 'N/A')
                   long_window = p.get('Long Window', 'N/A')
                   signal_window = p.get('Signal Window', 'N/A')
                   score = p.get('Score', 0)
                   open_trade_count = p.get('open_trade_count', 0)
                   log_func(f"{ticker}, {strategy_type}, {short_window}, {long_window}, {signal_window}, {score:.4f}, {open_trade_count}")
           else:
               log_func("\n=== No Signal Entries found ===")
       
       return signal_entries
   
   def calculate_breadth_metrics(
       portfolios: List[Dict[str, Any]],
       open_trades: List[Dict[str, Any]] = None,
       signal_entries: List[Dict[str, Any]] = None,
       log_func = None
   ) -> Dict[str, float]:
       """Calculate breadth metrics for a set of portfolios.
       
       Args:
           portfolios: List of portfolio dictionaries
           open_trades: Optional list of open trades
           signal_entries: Optional list of signal entries
           log_func: Optional logging function
           
       Returns:
           Dictionary of breadth metrics
       """
       if not portfolios:
           return {}
           
       # Get total number of strategies
       total_strategies = len(portfolios)
       
       # Count open trades
       total_open_trades = len(open_trades) if open_trades is not None else len([p for p in portfolios if
                          (p.get('Total Open Trades') == 1 or
                           (isinstance(p.get('Total Open Trades'), str) and p.get('Total Open Trades') == '1')) and
                          str(p.get('Signal Entry', '')).lower() != 'true'])
       
       # Count signal entries
       total_signal_entries = len(signal_entries) if signal_entries is not None else len([p for p in portfolios if str(p.get('Signal Entry', '')).lower() == 'true'])
       
       # Count signal exits
       signal_exit_strategies = [p for p in portfolios if str(p.get('Signal Exit', '')).lower() == 'true']
       total_signal_exits = len(signal_exit_strategies)
       
       # Calculate breadth ratio (open trades to total strategies)
       breadth_ratio = total_open_trades / total_strategies if total_strategies > 0 else 0
       
       # Calculate signal entry ratio
       signal_entry_ratio = total_signal_entries / total_strategies if total_strategies > 0 else 0
       
       # Calculate signal exit ratio
       signal_exit_ratio = total_signal_exits / total_strategies if total_strategies > 0 else 0
       
       # Calculate breadth momentum (signal entry ratio / signal exit ratio)
       breadth_momentum = signal_entry_ratio / signal_exit_ratio if signal_exit_ratio > 0 else float('inf')
       
       metrics = {
           "total_strategies": total_strategies,
           "total_open_trades": total_open_trades,
           "total_signal_entries": total_signal_entries,
           "total_signal_exits": total_signal_exits,
           "breadth_ratio": breadth_ratio,
           "signal_entry_ratio": signal_entry_ratio,
           "signal_exit_ratio": signal_exit_ratio,
           "breadth_momentum": breadth_momentum
       }
       
       if log_func:
           log_func("\n=== Breadth Metrics ===")
           log_func(f"Total Strategies: {total_strategies}")
           log_func(f"Total Open Trades: {total_open_trades}")
           log_func(f"Total Signal Entries: {total_signal_entries}")
           log_func(f"Total Signal Exits: {total_signal_exits}")
           log_func(f"Breadth Ratio: {breadth_ratio:.4f} (Open Trades / Total Strategies)")
           log_func(f"Signal Entry Ratio: {signal_entry_ratio:.4f} (Signal Entries / Total Strategies)")
           log_func(f"Signal Exit Ratio: {signal_exit_ratio:.4f} (Signal Exits / Total Strategies)")
           log_func(f"Breadth Momentum: {breadth_momentum:.4f} (Signal Entry Ratio / Signal Exit Ratio)")
       
       return metrics
   ```

2. Update all three modules to use these standardized portfolio result processing utilities.

## Phase 6: Create a Common Project Root Resolver

**Current State:**
- `app/strategies/update_portfolios.py` has code to resolve the project root
- Other modules handle this differently

**Implementation Steps:**

1. Create a new module `app/tools/project_utils.py` with:
   ```python
   """Project utilities.
   
   This module provides utilities for working with project paths and directories.
   """
   import os
   from pathlib import Path
   
   def get_project_root() -> str:
       """Get the absolute path to the project root directory.
       
       Returns:
           Absolute path to the project root directory
       """
       # Start from the current file and go up to the project root
       current_file = os.path.abspath(__file__)
       tools_dir = os.path.dirname(current_file)
       app_dir = os.path.dirname(tools_dir)
       project_root = os.path.dirname(app_dir)
       
       return project_root
   
   def resolve_path(path: str, base_dir: str = None) -> str:
       """Resolve a path relative to a base directory.
       
       Args:
           path: Path to resolve
           base_dir: Base directory (defaults to project root)
           
       Returns:
           Absolute path
       """
       if os.path.isabs(path):
           return path
           
       if base_dir is None:
           base_dir = get_project_root()
           
       return os.path.abspath(os.path.join(base_dir, path))
   ```

2. Update all three modules to use these standardized project utilities.

## Implementation Strategy

For each phase:

1. Create the new utility module with the consolidated functions
2. Update each of the three modules one at a time to use the new utilities
3. Test each module after updating to ensure functionality is preserved
4. Refactor any remaining duplicated code

## Benefits

This implementation plan provides several benefits:

1. **Reduced Duplication**: Consolidating duplicate utility functions reduces code duplication and maintenance burden.
2. **Improved Consistency**: Standardized utilities ensure consistent behavior across modules.
3. **Better Maintainability**: Centralized utilities make it easier to update and improve functionality.
4. **Enhanced Reusability**: Utility functions can be reused in other modules.
5. **Clearer Responsibilities**: Following SOLID principles ensures each utility has a clear responsibility.

## SOLID Principles Application

1. **Single Responsibility**: Each utility module has a clear, focused purpose.
2. **Open/Closed**: Utilities are designed to be extended without modification.
3. **Liskov Substitution**: Functions with similar signatures can be used interchangeably.
4. **Interface Segregation**: Utilities expose only what clients need.
5. **Dependency Inversion**: Modules depend on abstractions (utility functions) rather than concrete implementations.

## KISS Principle Application

1. **Simple Interfaces**: Utility functions have clear, simple interfaces.
2. **Minimal Dependencies**: Utilities have minimal dependencies on other modules.
3. **Focused Functionality**: Each utility does one thing well.
4. **Clear Documentation**: Utilities are well-documented with clear examples.