"""
Concurrency Analysis Module for Trading Strategies.

This module serves as the entry point for analyzing concurrent exposure between
multiple trading strategies and defines configuration types and defaults.
"""

from app.concurrency.tools.runner import main
from app.concurrency.tools.types import ConcurrencyConfig

# Default configuration
DEFAULT_CONFIG: ConcurrencyConfig = {
    # "PORTFOLIO": "spy_d_next.json",
    # "PORTFOLIO": "spy_qqq_d_next.json",
    # "PORTFOLIO": "spy_qqq_btc_sol_d_next.json",
    # "PORTFOLIO": "btc_d_next.json",
    # "PORTFOLIO": "sol_d_next.json",
    # "PORTFOLIO": "eth_d_next.json",
    "PORTFOLIO": "btc_sol_eth.json",
    # "PORTFOLIO": "crypto_d.json",
    # "PORTFOLIO": "crypto_d_next.json",
    "BASE_DIR": ".",
    "REFRESH": True,
    "SL_CANDLE_CLOSE": True
}

if __name__ == "__main__":
    try:
        result = main(DEFAULT_CONFIG)
        if result:
            print("Unified concurrency analysis completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
