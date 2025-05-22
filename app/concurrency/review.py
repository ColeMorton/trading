"""Concurrency Analysis Module for Trading Strategies.

This module serves as the entry point for analyzing concurrent exposure between
multiple trading strategies and defines configuration types and defaults.

Configuration Options:
    - PORTFOLIO: Portfolio filename with extension (e.g., 'crypto_d_20250303.json')
    - BASE_DIR: Directory for log files (defaults to './logs')
    - REFRESH: Whether to refresh cached data
    - SL_CANDLE_CLOSE: Use candle close for stop loss
    - RATIO_BASED_ALLOCATION: Enable ratio-based allocation
    - VISUALIZATION: Enable visualization of results
    - CSV_USE_HOURLY: Control timeframe for CSV file strategies (True for hourly, False for daily)
      Note: JSON files specify timeframes individually per strategy
    - REPORT_INCLUDES: Control what to include in the report:
        - TICKER_METRICS: Include ticker-level metrics
        - STRATEGIES: Include detailed strategy information
        - STRATEGY_RELATIONSHIPS: Include strategy relationship analysis
        - ALLOCATION: Include allocation calculations and fields
"""
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from app.tools.project_utils import (
    get_project_root
)
from app.tools.entry_point import run_from_command_line

from app.concurrency.tools.runner import main
from app.concurrency.config import (
    ConcurrencyConfig,
    validate_config,
    ConfigurationError
)
from app.tools.logging_context import logging_context
from app.tools.error_context import error_context
from app.tools.error_decorators import handle_errors
from app.tools.exceptions import (
    ConfigurationError as SystemConfigurationError,
    PortfolioLoadError,
    SyntheticTickerError,
    TradingSystemError
)
from app.tools.portfolio import (
    portfolio_context         # Using context manager
)
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version
)
from app.tools.portfolio.allocation import (
    validate_allocations,
    normalize_allocations,
    distribute_missing_allocations,
    ensure_allocation_sum_100_percent,
    calculate_position_sizes,
    get_allocation_summary
)
from app.tools.portfolio.stop_loss import (
    validate_stop_loss,
    normalize_stop_loss,
    get_stop_loss_summary,
    apply_stop_loss_rules
)
from app.tools.config_management import (
    normalize_config,
    merge_configs,
    resolve_portfolio_filename
)
from app.tools.synthetic_ticker import (
    detect_synthetic_ticker,
    process_synthetic_ticker,
    process_synthetic_config
)

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    # "PORTFOLIO": 'SPY_QQQ_202503027.csv',
    # "PORTFOLIO": "crypto_d_20250508.csv",
    # "PORTFOLIO": "BTC_MSTR_d_20250409.csv",
    # "PORTFOLIO": "DAILY_crypto.csv",
    # "PORTFOLIO": "DAILY_test.csv",
    # "PORTFOLIO": "atr_test_portfolio.json",
    # "PORTFOLIO": "stock_trades_20250517.csv",
    # "PORTFOLIO": "portfolio_d_20250519.csv",
    # "PORTFOLIO": "total_d_20250519.csv", 
    # "PORTFOLIO": "BTC-USD_SPY_d.csv",
    # "PORTFOLIO": "trades_20250520.csv",
    # "PORTFOLIO": "BTC_d_20250427.csv",
    "PORTFOLIO": "portfolio_risk.csv",
    "BASE_DIR": get_project_root(),  # Use standardized project root resolver
    "REFRESH": False,
    "OPTIMIZE": False,
    "OPTIMIZE_MIN_STRATEGIES": 13,
    # "OPTIMIZE_MAX_PERMUTATIONS": 1000,
    "SL_CANDLE_CLOSE": True, 
    "VISUALIZATION": False,
    "RATIO_BASED_ALLOCATION": True,
    "CSV_USE_HOURLY": False,
    "SORT_BY": "allocation",
    "REPORT_INCLUDES": {
        "TICKER_METRICS": False,
        "STRATEGIES": False,
        "STRATEGY_RELATIONSHIPS": False,
        "ALLOCATION": True
    },
    "ENSURE_COUNTERPART": True,
    "INITIAL_VALUE": 19726.55,
    "TARGET_VAR": 0.05,
    "MAX_RISK": {
        "STRATEGY": 169.771951300664
    }
}

@handle_errors(
    "Concurrency analysis",
    {
        ConfigurationError: SystemConfigurationError,
        PortfolioLoadError: PortfolioLoadError,
        SyntheticTickerError: SyntheticTickerError,
        Exception: TradingSystemError
    }
)
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
                # Process portfolio data with schema detection and allocation handling
                if portfolio_data:
                    # Detect schema version
                    schema_version = detect_schema_version(portfolio_data)
                    log(f"Detected schema version: {schema_version.name}", "info")
                    
                    # Process allocation and stop loss data if using extended schema
                    if schema_version == SchemaVersion.EXTENDED:
                        # Process allocation data if allocation reporting is enabled
                        if validated_config.get("REPORT_INCLUDES", {}).get("ALLOCATION", True):
                            log("Processing allocation data...", "info")
                            
                            # Validate and normalize allocation values
                            validated_data = validate_allocations(portfolio_data, log)
                            normalized_data = normalize_allocations(validated_data, log)
                            
                            # Distribute missing allocations if needed
                            distributed_data = distribute_missing_allocations(normalized_data, log)
                            
                            # Ensure allocations sum to 100%
                            portfolio_data = ensure_allocation_sum_100_percent(distributed_data, log)
                            
                            # Calculate position sizes if account value is provided
                            if "INITIAL_VALUE" in validated_config and validated_config["INITIAL_VALUE"] > 0:
                                account_value = float(validated_config["INITIAL_VALUE"])
                                portfolio_data = calculate_position_sizes(portfolio_data, account_value, log)
                                log(f"Calculated position sizes based on account value: {account_value}", "info")
                            
                            # Get allocation summary
                            allocation_summary = get_allocation_summary(portfolio_data, log)
                            log(f"Allocation summary: {allocation_summary}", "info")
                        
                        # Process stop loss data
                        log("Processing stop loss data...", "info")
                        
                        # Validate stop loss values
                        validated_stop_loss = validate_stop_loss(portfolio_data, log)
                        
                        # Normalize stop loss field names
                        portfolio_data = normalize_stop_loss(validated_stop_loss, log)
                        
                        # Get stop loss summary
                        stop_loss_summary = get_stop_loss_summary(portfolio_data, log)
                        log(f"Stop loss summary: {stop_loss_summary}", "info")
                        
                        # Apply stop loss rules if price data is available and SL_CANDLE_CLOSE is configured
                        if "PRICE_DATA" in validated_config and validated_config.get("SL_CANDLE_CLOSE") is not None:
                            log("Applying stop loss rules to strategies...", "info")
                            use_candle_close = validated_config.get("SL_CANDLE_CLOSE", True)
                            
                            # Apply stop loss rules to each strategy
                            for i, strategy in enumerate(portfolio_data):
                                portfolio_data[i] = apply_stop_loss_rules(
                                    strategy,
                                    validated_config["PRICE_DATA"],
                                    use_candle_close,
                                    log
                                )
                            
                            # Count strategies with triggered stop losses
                            triggered_count = sum(1 for s in portfolio_data if s.get('stop_triggered', False))
                            if triggered_count > 0:
                                log(f"Stop loss triggered for {triggered_count} strategies", "info")
                    
                    # Check for synthetic tickers in portfolio strategies
                    log("Checking for synthetic tickers in portfolio strategies...", "info")
                    
                    # Also set synthetic ticker flag in the main config if any synthetic tickers are found
                    has_synthetic_tickers = False
                    
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
                                        
                                except SyntheticTickerError as e:
                                    log(f"Invalid synthetic ticker format: {ticker} - {str(e)}", "warning")
                    
                    # If we found synthetic tickers, process the main config
                    if has_synthetic_tickers:
                        log("Processing synthetic ticker configuration for main analysis...", "info")
                        validated_config = process_synthetic_config(validated_config, log)
        
        # Run analysis
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
            
            # Log allocation and stop loss information if available and enabled
            if validated_config.get("REPORT_INCLUDES", {}).get("ALLOCATION", True):
                log("Allocation handling is enabled for this analysis", "info")
            
            # Log stop loss configuration
            if validated_config.get("SL_CANDLE_CLOSE") is not None:
                log(f"Stop loss handling is enabled using {'candle close' if validated_config['SL_CANDLE_CLOSE'] else 'intracandle'} prices", "info")
            
            result = main(validated_config)
            if result:
                log("Concurrency analysis completed successfully!", "info")
                return True
            else:
                log("Concurrency analysis failed", "error")
                return False

def run_concurrency_review(portfolio_name: str, config_overrides: Optional[Dict[str, Any]] = None) -> bool:
    """Run concurrency review with a specific portfolio file and configuration overrides.
    
    Args:
        portfolio_name (str): Name of the portfolio file (with or without extension)
        config_overrides (Dict[str, Any], optional): Configuration overrides to apply
        
    Returns:
        bool: True if analysis completed successfully, False otherwise
        
    Raises:
        SyntheticTickerError: If there's an issue with synthetic ticker processing
    """
    # Create a copy of the default config
    config = DEFAULT_CONFIG.copy()
    
    # Resolve portfolio filename with extension
    resolved_portfolio_name = resolve_portfolio_filename(portfolio_name)
    
    # Set the portfolio name in the config
    config["PORTFOLIO"] = resolved_portfolio_name
    
    # Merge with any config overrides
    if config_overrides:
        config = merge_configs(config, config_overrides)
    
    # Normalize the configuration (ensure BASE_DIR is absolute, etc.)
    config = normalize_config(config)
    
    # Run the analysis
    return run_analysis(config)

if __name__ == "__main__":
    # Create a normalized copy of the default config
    config = normalize_config(DEFAULT_CONFIG.copy())
    
    # Use the standardized entry point utility
    run_from_command_line(
        run_analysis,
        config,
        "concurrency analysis"
    )
