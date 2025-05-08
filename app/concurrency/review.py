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
    # "PORTFOLIO": "stock_trades_20250508.csv",
    # "PORTFOLIO": "portfolio_d_20250505.csv",
    # "PORTFOLIO": "total_d_20250505.csv", 
    # "PORTFOLIO": "BTC-USD_SPY_d.csv",
    # "PORTFOLIO": "macd_test.json",
    "PORTFOLIO": "MSTR_d_20250415.csv",
    "BASE_DIR": get_project_root(),  # Use standardized project root resolver
    "REFRESH": False,
    "SL_CANDLE_CLOSE": True, 
    "VISUALIZATION": False,
    "RATIO_BASED_ALLOCATION": True,
    "CSV_USE_HOURLY": False,
    "SORT_BY": "allocation",
    "REPORT_INCLUDES": {
        "TICKER_METRICS": True,
        "STRATEGIES": True,
        "STRATEGY_RELATIONSHIPS": True
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
                # Process each strategy in the portfolio to check for synthetic tickers
                if portfolio_data:
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
