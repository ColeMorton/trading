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
import sys
import logging

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

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    # "PORTFOLIO": 'SPY_QQQ_202503027.csv',
    # "PORTFOLIO": "crypto_d_20250422.csv",
    # "PORTFOLIO": "BTC_MSTR_d_20250409.csv",
    # "PORTFOLIO": "DAILY_crypto.csv",
    # "PORTFOLIO": "DAILY_test.csv",
    # "PORTFOLIO": "atr_test_portfolio.json",
    # "PORTFOLIO": "stock_trades_20250422.csv",
    "PORTFOLIO": "portfolio_d_20250417.csv",
    # "PORTFOLIO": "total_20250417.csv",
    # "PORTFOLIO": "BTC-USD_SPY_d.csv",
    # "PORTFOLIO": "macd_test.json",
    # "PORTFOLIO": "MSTR_d_20250415.csv",
    "BASE_DIR": '.',  # Default to project root directory
    "REFRESH": True,
    "SL_CANDLE_CLOSE": True, 
    "VISUALIZATION": False,
    "RATIO_BASED_ALLOCATION": True,
    "CSV_USE_HOURLY": False,
    "SORT_BY": "allocation",
    "REPORT_INCLUDES": {
        "TICKER_METRICS": True,
        "STRATEGIES": True,
        "STRATEGY_RELATIONSHIPS": False
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
    if config["BASE_DIR"] != './logs':
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
            with portfolio_context(portfolio_filename, log, validated_config) as _:
                # The portfolio is loaded in the main function, so we don't need to do anything with it here
                pass
        
        # Run analysis
        log("Starting concurrency analysis...", "info")
        with error_context(
            "Running main analysis",
            log,
            {Exception: TradingSystemError},
            reraise=False
        ):
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
    with error_context(
        "Running concurrency analysis from command line",
        lambda msg, level='info': print(f"[{level.upper()}] {msg}"),
        reraise=False
    ):
        # Create a normalized copy of the default config
        config = normalize_config(DEFAULT_CONFIG.copy())
        success = run_analysis(config)
        if not success:
            sys.exit(1)
