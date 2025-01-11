"""
Concurrency Analysis Module for Trading Strategies.

This module serves as the entry point for analyzing concurrent exposure between
multiple trading strategies and defines configuration types and defaults.
"""

from app.concurrency.tools.runner import main
from app.concurrency.tools.types import ConcurrencyConfig

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    # "PORTFOLIO": "spy_qqq_btc_sol_D.json",
    # "PORTFOLIO": "btc_d_next.json",
    "PORTFOLIO": "btc_d_ma.json",
    "BASE_DIR": ".",
    "REFRESH": True
}

if __name__ == "__main__":
    try:
        result = main(DEFAULT_CONFIG)
        if result:
            print("Unified concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
