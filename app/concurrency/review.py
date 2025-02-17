"""Concurrency Analysis Module for Trading Strategies.

This module serves as the entry point for analyzing concurrent exposure between
multiple trading strategies and defines configuration types and defaults.
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

# Get the absolute path to the portfolios directory
CONCURRENCY_DIR = Path(__file__).parent
PORTFOLIOS_DIR = CONCURRENCY_DIR / "portfolios"

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "spy_qqq_btc_sol_d_next.json"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "BTC_D_test.csv"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "BTC_SOL_D.csv"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "btc_d_macd.json"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "btc_d_20250217.json"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "eth_d_20250217.json"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "sol_d_20250217.json"),
    "PORTFOLIO": str(PORTFOLIOS_DIR / "crypto_d_20250217.json"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "crypto_d_next.json"),
    # "PORTFOLIO": str(PORTFOLIOS_DIR / "btc_d_next.json"),
    "BASE_DIR": str(CONCURRENCY_DIR),
    "REFRESH": True,
    "SL_CANDLE_CLOSE": True,
    "VISUALIZATION": True
}

def run_analysis(config: Dict[str, Any]) -> bool:
    """Run concurrency analysis with the given configuration.

    Args:
        config (Dict[str, Any]): Configuration dictionary

    Returns:
        bool: True if analysis completed successfully, False otherwise
    """
    log_dir = Path(config["BASE_DIR"]) / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log, log_close, _, _ = setup_logging(
        module_name="concurrency_review",
        log_file="review.log",
        level=logging.INFO
    )
    
    try:
        # Validate configuration
        log("Validating configuration...", "info")
        validated_config = validate_config(config)
        
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
