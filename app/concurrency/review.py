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

from typing import Dict, Any
from pathlib import Path
import sys
import logging

from app.concurrency.tools.runner import main
from app.concurrency.config import (
    ConcurrencyConfig,
    validate_config,
    ConfigurationError
)
from app.tools.setup_logging import setup_logging
from app.tools.portfolio import (
    load_portfolio,
    resolve_portfolio_path
)

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    # "PORTFOLIO": "stock_portfolio_h_20250221.json",  # Updated to use an existing portfolio file
    # "PORTFOLIO": "spy_qqq_h_20250311.csv",
    # "PORTFOLIO": "stock_trades_20250314.csv",
    "PORTFOLIO": "SPY_QQQ_202503012.csv",
    # "PORTFOLIO": "crypto_d_20250313.json",
    # "PORTFOLIO": "DAILY_test.csv",
    # "PORTFOLIO": "stock_trades_20250312.csv",
    # "PORTFOLIO": "total_20250310.csv",
    # "PORTFOLIO": "DAILY_crypto.csv",
    # "PORTFOLIO": "btc_d_20250307.json",
    "BASE_DIR": '.',  # Default to project root directory
    "REFRESH": True,
    "SL_CANDLE_CLOSE": True,
    "VISUALIZATION": True,
    "RATIO_BASED_ALLOCATION": True,
    "CSV_USE_HOURLY": False,
    "REPORT_INCLUDES": {
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

def run_analysis(config: Dict[str, Any]) -> bool:
    """Run concurrency analysis with the given configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    # Get log subdirectory from BASE_DIR if specified
    log_subdir = None
    if config["BASE_DIR"] != './logs':
        log_subdir = Path(config["BASE_DIR"]).name
    
    log, log_close, _, _ = setup_logging(
        module_name="concurrency_review",
        log_file="review.log",
        level=logging.INFO,
        log_subdir=log_subdir
    )
    
    try:
        # Validate configuration
        log("Validating configuration...", "info")
        validated_config = validate_config(config)

        try:
            # Resolve portfolio path using shared functionality
            portfolio_filename = validated_config["PORTFOLIO"]
            
            try:
                portfolio_path = resolve_portfolio_path(
                    portfolio_filename, 
                    validated_config.get("BASE_DIR")
                )
                log(f"Portfolio path resolved: {portfolio_path}", "info")
            except FileNotFoundError:
                raise ConfigurationError(f"Portfolio file not found: {portfolio_filename}")
            
            # Load portfolio to validate format
            try:
                portfolio_data = load_portfolio(
                    portfolio_filename, 
                    log, 
                    validated_config
                )
                log(f"Successfully loaded portfolio with {len(portfolio_data)} strategies", "info")
            except (ValueError, FileNotFoundError) as e:
                raise ConfigurationError(f"Error loading portfolio: {str(e)}")
            
            # Update config with resolved path
            validated_config["PORTFOLIO"] = str(portfolio_path)
            log(f"Portfolio path: {portfolio_path}", "debug")
            
        except ConfigurationError as e:
            raise ConfigurationError(str(e))

        # Run analysis
        log("Starting concurrency analysis...", "info")
        result = main(validated_config)
        if result:
            log("Concurrency analysis completed successfully!", "info")
            return True
        else:
            log("Concurrency analysis failed", "error")
            return False
            
    except ConfigurationError as e:
        log(f"Configuration error: {str(e)}", "error")
        return False
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "error")
        return False
    finally:
        log_close()

def run_concurrency_review(portfolio_name: str, config_overrides: Dict[str, Any] = None) -> bool:
    """Run concurrency review with a specific portfolio file and configuration overrides.
    
    Args:
        portfolio_name (str): Name of the portfolio file (with or without extension)
        config_overrides (Dict[str, Any], optional): Configuration overrides to apply
        
    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    # Create a copy of the default config
    config = DEFAULT_CONFIG.copy()
    
    # Set the portfolio name
    if not portfolio_name.endswith('.json') and not portfolio_name.endswith('.csv'):
        # Try to determine the extension
        csv_path = Path(f"csv/portfolios/{portfolio_name}.csv")
        json_path = Path(f"json/portfolios/{portfolio_name}.json")
        
        if csv_path.exists():
            portfolio_name = f"{portfolio_name}.csv"
        elif json_path.exists():
            portfolio_name = f"{portfolio_name}.json"
        else:
            # Default to CSV if we can't determine
            portfolio_name = f"{portfolio_name}.csv"
    
    config["PORTFOLIO"] = portfolio_name
    
    # Apply any config overrides
    if config_overrides:
        for key, value in config_overrides.items():
            if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                # Merge dictionaries for nested configs
                config[key].update(value)
            else:
                # Replace value for simple configs
                config[key] = value
    
    # Run the analysis
    return run_analysis(config)

if __name__ == "__main__":
    try:
        success = run_analysis(DEFAULT_CONFIG)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Execution failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
