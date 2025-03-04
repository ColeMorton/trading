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
    ConfigurationError,
    detect_portfolio_format
)
from app.tools.setup_logging import setup_logging

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    "PORTFOLIO": "SPY_QQQ_D.csv",
    "BASE_DIR": './logs',  # Default to logs directory
    "REFRESH": True,
    "SL_CANDLE_CLOSE": True,
    "VISUALIZATION": False,
    "RATIO_BASED_ALLOCATION": True,
    "CSV_USE_HOURLY": False
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
            # Determine portfolio path based on file extension
            portfolio_filename = validated_config["PORTFOLIO"]
            file_extension = portfolio_filename.split(".")[-1].lower()

            # Get the project root directory (3 levels up from this file)
            project_root = Path(__file__).parent.parent.parent

            if file_extension == "json":
                portfolio_path = project_root / "json" / "portfolios" / portfolio_filename
            elif file_extension == "csv":
                portfolio_path = project_root / "csv" / "portfolios" / portfolio_filename
            else:
                raise ValueError(f"Unsupported portfolio file type: {file_extension}")

            if not portfolio_path.exists():
                raise FileNotFoundError(f"Portfolio file not found at: {portfolio_path}")

            # Detect and validate portfolio format
            format_info = detect_portfolio_format(str(portfolio_path))
            format_info.validator(str(portfolio_path))

            validated_config["PORTFOLIO"] = str(portfolio_path)
            log(f"Portfolio path: {portfolio_path}", "debug")
        except (ValueError, FileNotFoundError) as e:
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

if __name__ == "__main__":
    try:
        success = run_analysis(DEFAULT_CONFIG)
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"Execution failed: {str(e)}", file=sys.stderr)
        sys.exit(1)
