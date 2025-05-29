"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA and SMA cross strategies, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

from typing import List, Dict, Any, Optional
import polars as pl
import json
import os
from app.tools.get_config import get_config
from app.tools.project_utils import (
    get_project_root
)
from app.tools.get_config import get_config
from app.tools.entry_point import run_from_command_line
from app.tools.strategy.types import StrategyConfig as Config
from app.ma_cross.tools.strategy_execution import execute_strategy
from app.tools.portfolio.collection import export_best_portfolios

# New imports for standardized logging and error handling
from app.tools.logging_context import logging_context
from app.tools.error_context import error_context
from app.tools.error_decorators import handle_errors
from app.tools.exceptions import (
    PortfolioLoadError,
    StrategyProcessingError,
    ConfigurationError,
    SyntheticTickerError,
    ExportError,
    TradingSystemError
)
from app.tools.config_management import (
    normalize_config
)
from app.tools.synthetic_ticker import (
    process_synthetic_config
)
from app.tools.strategy_utils import (
    get_strategy_types,
    filter_portfolios_by_signal
)
from app.tools.portfolio_results import (
    sort_portfolios,
    filter_open_trades,
    filter_signal_entries,
    calculate_breadth_metrics
)
# Import schema detection utilities
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    normalize_portfolio_data
)

# Import allocation utilities
from app.tools.portfolio.allocation import (
    validate_allocations,
    normalize_allocations,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    calculate_position_sizes
)

# Import stop loss utilities
from app.tools.portfolio.stop_loss import (
    validate_stop_loss,
    normalize_stop_loss,
    calculate_stop_loss_levels,
    get_stop_loss_summary
)

CONFIG: Config = {
    # "TICKER": "BTC-USD",
    "TICKER": ["PWR"],
    # Load tickers from JSON file
    # "TICKER": json.load(open(os.path.join(get_project_root(), "app/ma_cross/ticker_lists/portfolio.json"))),
    # "TICKER_2": 'AVGO',
    # "WINDOWS": 120,
    "WINDOWS": 80,
    # "WINDOWS": 55,
    # "WINDOWS": 34,
    # "SCANNER_LIST": 'DAILY.csv',
    # "USE_SCANNER": True,
    "BASE_DIR": get_project_root(),  # Use standardized project root resolver
    "REFRESH": False,
    "STRATEGY_TYPES": [ "SMA", "EMA" ],
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": True,
    "MINIMUMS": {
        "WIN_RATE": 0.44,
        # "TRADES": 34,
        # "WIN_RATE": 0.50,
        "TRADES": 54,
        # "WIN_RATE": 0.61,
        "EXPECTANCY_PER_TRADE": 1,
        "PROFIT_FACTOR": 1,
        "SORTINO_RATIO": 0.4,
        # "BEATS_BNH": 0
        # "BEATS_BNH": 0.13
    },
    "SORT_BY": "Score",
    "SORT_ASC": False,
    "USE_GBM": False
}

# Using the standardized synthetic_ticker module instead of local implementation

# Using standardized strategy utilities from app.tools.strategy_utils
def filter_portfolios(portfolios: List[Dict[str, Any]], config: Config, log) -> List[Dict[str, Any]]:
    """Filter portfolios based on configuration.
    
    Args:
        portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        Filtered list of portfolio dictionaries
    """
    # First detect schema version and normalize portfolio data
    schema_version = detect_schema_version(portfolios)
    log(f"Detected schema version: {schema_version.name}", "info")
    
    # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
    normalized_portfolios = normalize_portfolio_data(portfolios, schema_version, log)
    
    # Process allocation and stop loss values if they exist
    if schema_version == SchemaVersion.EXTENDED:
        # Process allocation values
        # Validate allocation values
        validated_portfolios = validate_allocations(normalized_portfolios, log)
        
        # Normalize allocation field names
        normalized_portfolios = normalize_allocations(validated_portfolios, log)
        
        # Distribute missing allocations if some rows have values and others don't
        distributed_portfolios = distribute_missing_allocations(normalized_portfolios, log)
        
        # Ensure allocation values sum to 100%
        normalized_portfolios = ensure_allocation_sum_100_percent(distributed_portfolios, log)
        
        # Calculate position sizes if account value is provided in config
        if "ACCOUNT_VALUE" in config and config["ACCOUNT_VALUE"] > 0:
            account_value = float(config["ACCOUNT_VALUE"])
            normalized_portfolios = calculate_position_sizes(normalized_portfolios, account_value, log)
            log(f"Calculated position sizes based on account value: {account_value}", "info")
        
        # Process stop loss values
        # Validate stop loss values
        validated_stop_loss = validate_stop_loss(normalized_portfolios, log)
        
        # Normalize stop loss field names
        normalized_portfolios = normalize_stop_loss(validated_stop_loss, log)
        
        # If we have entry prices, calculate stop loss levels
        if "ENTRY_PRICES" in config and config["ENTRY_PRICES"]:
            normalized_portfolios = calculate_stop_loss_levels(normalized_portfolios, config["ENTRY_PRICES"], log)
            log("Calculated stop loss levels based on entry prices", "info")
    
    # Filter by signal using the standardized filter_portfolios_by_signal function
    filtered = filter_portfolios_by_signal(normalized_portfolios, config, log)
    
    # Filter out portfolios with invalid metrics
    from app.tools.portfolio.filters import filter_invalid_metrics
    filtered = filter_invalid_metrics(filtered, log)
    
    # Apply MINIMUMS filtering if configured
    if filtered is not None and len(filtered) > 0 and "MINIMUMS" in config:
        import polars as pl
        
        # Convert to DataFrame for easier filtering
        df = pl.DataFrame(filtered)
        original_count = len(df)
        
        minimums = config["MINIMUMS"]
        
        # Define filter configurations
        filter_configs = [
            # (config_key, column_name, data_type, multiplier, message_prefix)
            ("WIN_RATE", "Win Rate [%]", pl.Float64, 100, "Filtered portfolios with win rate"),
            ("TRADES", "Total Trades", pl.Int64, 1, "Filtered portfolios with at least"),
            ("EXPECTANCY_PER_TRADE", "Expectancy per Trade", pl.Float64, 1, "Filtered portfolios with expectancy per trade"),
            ("PROFIT_FACTOR", "Profit Factor", pl.Float64, 1, "Filtered portfolios with profit factor"),
            ("SCORE", "Score", pl.Float64, 1, "Filtered portfolios with score"),
            ("SORTINO_RATIO", "Sortino Ratio", pl.Float64, 1, "Filtered portfolios with Sortino ratio"),
            ("BEATS_BNH", "Beats BNH [%]", pl.Float64, 1, "Filtered portfolios with Beats BNH percentage")
        ]
        
        # Apply each filter from the configuration
        for config_key, column_name, data_type, multiplier, message_prefix in filter_configs:
            if config_key in minimums and column_name in df.columns:
                adjusted_value = minimums[config_key] * multiplier
                df = df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)
                
                # Format the message based on the filter type
                if "win rate" in message_prefix.lower():
                    log(f"{message_prefix} >= {adjusted_value}%", "info")
                elif "trades" in message_prefix.lower():
                    log(f"{message_prefix} >= {int(adjusted_value)}", "info")
                else:
                    log(f"{message_prefix} >= {adjusted_value}", "info")
        
        # Log filtering results
        filtered_count = original_count - len(df)
        if filtered_count > 0:
            log(f"Filtered out {filtered_count} portfolios based on MINIMUMS criteria", "info")
            log(f"Remaining portfolios after MINIMUMS filtering: {len(df)}", "info")
        
        # Convert back to list of dicts
        filtered = df.to_dicts() if len(df) > 0 else []
    
    # If we have results and want to display them, use the portfolio_results utilities
    if filtered is not None and len(filtered) > 0 and config.get("DISPLAY_RESULTS", True):
        # Sort portfolios
        sorted_portfolios = sort_portfolios(filtered, config.get("SORT_BY", "Score"), config.get("SORT_ASC", False))
        
        # Get open trades
        open_trades = filter_open_trades(sorted_portfolios, log)
        
        # Get signal entries
        signal_entries = filter_signal_entries(sorted_portfolios, open_trades, log)
        
        # Calculate breadth metrics
        calculate_breadth_metrics(sorted_portfolios, open_trades, signal_entries, log)
        
        return sorted_portfolios
    
    return filtered

# Using the standardized synthetic_ticker module instead of local implementation

def execute_all_strategies(config: Config, log) -> List[Dict[str, Any]]:
    """Execute all strategies and collect results.
    
    Args:
        config: Configuration dictionary
        log: Logging function
        
    Returns:
        List of portfolio dictionaries
        
    Raises:
        StrategyProcessingError: If there's an error processing a strategy
    """
    strategy_types = get_strategy_types(config, log)
    log(f"Running strategies in sequence: {' -> '.join(strategy_types)}")
    
    all_portfolios = []
    
    for strategy_type in strategy_types:
        log(f"Running {strategy_type} strategy analysis...")
        strategy_config = {**config}
        strategy_config["STRATEGY_TYPE"] = strategy_type
        
        portfolios = execute_strategy(strategy_config, strategy_type, log)
        
        # Check if portfolios is not None and not empty
        if portfolios is not None:
            if isinstance(portfolios, pl.DataFrame):
                portfolio_count = len(portfolios)
                if portfolio_count > 0:
                    # Convert to dictionaries and process allocation and stop loss values
                    portfolio_dicts = portfolios.to_dicts()
                    all_portfolios.extend(portfolio_dicts)
            else:
                portfolio_count = len(portfolios)
                if portfolio_count > 0:
                    all_portfolios.extend(portfolios)
            
            log(f"{strategy_type} portfolios: {portfolio_count}", "info")
        else:
            log(f"{strategy_type} portfolios: 0", "info")
    
    if not all_portfolios:
        log("No portfolios returned from any strategy. Filtering criteria might be too strict.", "warning")
    
    return all_portfolios

@handle_errors(
    "MA Cross portfolio analysis",
    {
        ValueError: StrategyProcessingError,
        KeyError: ConfigurationError,
        PortfolioLoadError: PortfolioLoadError,
        Exception: TradingSystemError
    }
)
def run(config: Config = CONFIG) -> bool:
    """Run portfolio analysis for single or multiple tickers.
    
    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis
    3. Filters portfolios based on criteria
    4. Displays and saves results
    
    Args:
        config (Config): Configuration dictionary containing analysis parameters
        
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
        # Initialize configuration
        with error_context("Initializing configuration", log, {Exception: ConfigurationError}):
            config = get_config(config)
            
            # Normalize the configuration (ensures BASE_DIR is absolute)
            config = normalize_config(config)
        
        # Handle synthetic pair if enabled
        with error_context("Processing synthetic ticker configuration", log, {ValueError: SyntheticTickerError}):
            synthetic_config = process_synthetic_config(config, log)

        # Get strategy types and execute strategies
        all_portfolios = []
        # Use the standardized get_strategy_types function with default_type="SMA"
        strategy_types = get_strategy_types(synthetic_config, log, "SMA")
        
        # Execute each strategy in sequence
        for strategy_type in strategy_types:
            with error_context(f"Executing {strategy_type} strategy", log, {Exception: StrategyProcessingError}):
                portfolios = execute_strategy(synthetic_config, strategy_type, log)
                if portfolios:
                    all_portfolios.extend(portfolios)
        
        # Export best portfolios
        if all_portfolios:
            with error_context("Filtering and exporting portfolios", log, {Exception: ExportError}):
                # Detect schema version and normalize portfolio data
                schema_version = detect_schema_version(all_portfolios)
                log(f"Detected schema version for export: {schema_version.name}", "info")
                
                # Process portfolios with schema detection and normalization
                filtered_portfolios = filter_portfolios(all_portfolios, synthetic_config, log)
                
                # If we have allocation and stop loss data, log summaries
                if schema_version == SchemaVersion.EXTENDED:
                    from app.tools.portfolio.allocation import get_allocation_summary
                    allocation_summary = get_allocation_summary(filtered_portfolios, log)
                    log(f"Allocation summary: {allocation_summary}", "info")
                    
                    # Log stop loss summary
                    stop_loss_summary = get_stop_loss_summary(filtered_portfolios, log)
                    log(f"Stop loss summary: {stop_loss_summary}", "info")
                
                # Export portfolios using the extended schema format
                export_best_portfolios(filtered_portfolios, synthetic_config, log)
        
        return True

@handle_errors(
    "MA Cross strategies analysis",
    {
        ValueError: StrategyProcessingError,
        KeyError: ConfigurationError,
        PortfolioLoadError: PortfolioLoadError,
        Exception: TradingSystemError
    }
)
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
        # Initialize all_portfolios to an empty list
        all_portfolios = []
        
        # Initialize config
        with error_context("Initializing configuration", log, {Exception: ConfigurationError}):
            # Use passed config if provided, otherwise use default CONFIG
            if config is not None:
                config_copy = config.copy()
            else:
                config_copy = CONFIG.copy()
            config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
            config_copy = normalize_config(config_copy)
        
        # Process synthetic configuration
        with error_context("Processing synthetic configuration", log, {ValueError: SyntheticTickerError}):
            base_config = process_synthetic_config(config_copy, log)
        
        # Execute strategies
        with error_context("Executing strategies", log, {Exception: StrategyProcessingError}):
            all_portfolios = execute_all_strategies(base_config, log)
        
        # Export results
        if all_portfolios is not None and len(all_portfolios) > 0:
            with error_context("Filtering and exporting portfolios", log, {Exception: ExportError}):
                # Detect schema version and normalize portfolio data
                schema_version = detect_schema_version(all_portfolios)
                log(f"Detected schema version for export: {schema_version.name}", "info")
                
                # Process portfolios with schema detection and normalization
                filtered_portfolios = filter_portfolios(all_portfolios, base_config, log)
                
                # If we have allocation and stop loss data, log summaries
                if schema_version == SchemaVersion.EXTENDED:
                    from app.tools.portfolio.allocation import get_allocation_summary
                    allocation_summary = get_allocation_summary(filtered_portfolios, log)
                    log(f"Allocation summary: {allocation_summary}", "info")
                    
                    # Log stop loss summary
                    stop_loss_summary = get_stop_loss_summary(filtered_portfolios, log)
                    log(f"Stop loss summary: {stop_loss_summary}", "info")
                
                if filtered_portfolios is not None and len(filtered_portfolios) > 0:
                    # Export portfolios using the extended schema format
                    export_best_portfolios(filtered_portfolios, base_config, log)
                else:
                    log("No portfolios remain after filtering", "warning")
        else:
            log("No portfolios returned from strategies", "warning")
        
        return True

if __name__ == "__main__":
    run_from_command_line(
        run_strategies,
        {},  # Empty config as run_strategies uses the default CONFIG
        "MA Cross portfolio analysis"
    )