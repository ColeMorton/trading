"""
Scanner List Update Module for MA Cross Strategy

This module processes and updates scanner lists by:
1. Reading strategies from scanner list CSV
2. Backtesting both SMA and EMA strategies where defined
3. Exporting updated results back to scanner list
"""

import os
import polars as pl
from typing import Dict, List, Optional, TypedDict, Union

from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.ma_cross.config_types import Config
from app.ma_cross.tools.strategy_execution import execute_single_strategy

CONFIG: Config = {
    "SCANNER_LIST": 'DAILY_test.csv',
    "BASE_DIR": ".",
    "REFRESH": False,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "SORT_BY": "Expectancy Adjusted",
    "USE_GBM": False,
    "USE_SCANNER": True
}

def run(config: Config = CONFIG) -> bool:
    """Run scanner list update process."""
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_get_scanner_list.log'
    )
    
    try:
        # Initialize configuration
        config = get_config(config)
        
        # Read scanner list
        scanner_path = os.path.join("app", "ma_cross", "scanner_lists", config["SCANNER_LIST"])
        df = pl.read_csv(scanner_path)
        log(f"Loaded scanner list: {config['SCANNER_LIST']}")
        
        # Handle both 'Ticker' and 'TICKER' column names
        ticker_col = 'TICKER' if 'TICKER' in df.columns else 'Ticker'
        
        # Process each row
        results = []
        for row in df.iter_rows(named=True):
            ticker = row[ticker_col]
            log(f"Processing {ticker}")
            
            # Check for SMA strategy
            if not pl.Series([row["SMA_FAST"], row["SMA_SLOW"]]).is_null().any():
                sma_config = {
                    **config,
                    "TICKER": ticker,  # Always use uppercase TICKER in config
                    "USE_SMA": True,
                    "SHORT_WINDOW": int(row["SMA_FAST"]),
                    "LONG_WINDOW": int(row["SMA_SLOW"])
                }
                sma_result = execute_single_strategy(ticker, sma_config, log)
                if sma_result:
                    results.append(sma_result)
                    
            # Check for EMA strategy
            if not pl.Series([row["EMA_FAST"], row["EMA_SLOW"]]).is_null().any():
                ema_config = {
                    **config,
                    "TICKER": ticker,  # Always use uppercase TICKER in config
                    "USE_SMA": False,
                    "SHORT_WINDOW": int(row["EMA_FAST"]),
                    "LONG_WINDOW": int(row["EMA_SLOW"])
                }
                ema_result = execute_single_strategy(ticker, ema_config, log)
                if ema_result:
                    results.append(ema_result)
            
        # Export results
        if len(results) > 0:
            # Create DataFrame
            df = pl.DataFrame(results)
            
            # Ensure export directory exists
            export_dir = os.path.join("csv", "ma_cross", "scanner_list")
            os.makedirs(export_dir, exist_ok=True)
            
            # Export to CSV
            export_path = os.path.join(export_dir, config["SCANNER_LIST"])
            df.write_csv(export_path)
            log(f"Results exported to {export_path}")
            log_close()
            return True
        else:
            raise Exception("No valid results to export")
            
    except Exception as e:
        log(f"Scanner list update failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    run()