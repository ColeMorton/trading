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
from app.ma_cross.tools.signal_processing import process_current_signals
from app.tools.portfolio.collection import combine_strategy_portfolios

class StrategyResult(TypedDict):
    """Type definition for strategy execution results."""
    ticker: str
    sma_windows: Optional[tuple[int, int]]
    ema_windows: Optional[tuple[int, int]]
    sma_portfolio: Optional[Dict]
    ema_portfolio: Optional[Dict]
    combined_portfolio: Optional[Dict]

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

def process_strategy(
    ticker: str,
    sma_windows: Optional[tuple[int, int]],
    ema_windows: Optional[tuple[int, int]],
    base_config: Config,
    log: callable
) -> StrategyResult:
    """
    Process both SMA and EMA strategies for a single ticker using specified windows.

    Args:
        ticker (str): Ticker symbol
        sma_windows (tuple[int, int]): SMA fast and slow windows, or None
        ema_windows (tuple[int, int]): EMA fast and slow windows, or None
        base_config (Config): Base configuration
        log (callable): Logging function

    Returns:
        StrategyResult: Results from strategy execution
    """
    result: StrategyResult = {
        "ticker": ticker,
        "sma_windows": sma_windows,
        "ema_windows": ema_windows,
        "sma_portfolio": None,
        "ema_portfolio": None,
        "combined_portfolio": None
    }
    
    try:
        # Create ticker-specific config
        ticker_config = {**base_config, "TICKER": ticker}
        
        # Process SMA strategy if windows exist
        if sma_windows:
            log(f"Processing SMA strategy for {ticker} with windows {sma_windows}")
            sma_config = {
                **ticker_config,
                "USE_SMA": True,
                "SHORT_WINDOW": sma_windows[0],
                "LONG_WINDOW": sma_windows[1]
            }
            sma_df = process_current_signals(ticker, sma_config, log)
            if sma_df is not None and len(sma_df) > 0:
                result["sma_portfolio"] = sma_df.to_dicts()[0]
                log(f"SMA portfolio keys: {list(result['sma_portfolio'].keys())}")
            
        # Process EMA strategy if windows exist
        if ema_windows:
            log(f"Processing EMA strategy for {ticker} with windows {ema_windows}")
            ema_config = {
                **ticker_config,
                "USE_SMA": False,
                "SHORT_WINDOW": ema_windows[0],
                "LONG_WINDOW": ema_windows[1]
            }
            ema_df = process_current_signals(ticker, ema_config, log)
            if ema_df is not None and len(ema_df) > 0:
                result["ema_portfolio"] = ema_df.to_dicts()[0]
                log(f"EMA portfolio keys: {list(result['ema_portfolio'].keys())}")
            
        # Combine portfolios if both strategies exist
        if result["sma_portfolio"] and result["ema_portfolio"]:
            result["combined_portfolio"] = combine_strategy_portfolios(
                [result["sma_portfolio"]],
                [result["ema_portfolio"]]
            )
            
    except Exception as e:
        log(f"Failed to process ticker portfolios: {str(e)}", "error")
        
    return result

def export_results(results: List[StrategyResult], config: Config, log: callable) -> bool:
    """
    Export strategy results back to scanner list.

    Args:
        results (List[StrategyResult]): List of strategy results
        config (Config): Configuration dictionary
        log (callable): Logging function

    Returns:
        bool: True if export successful
    """
    try:
        # Convert results to DataFrame
        rows = []
        for result in results:
            # Use original windows from scanner list
            row = {
                "TICKER": result["ticker"],
                "SMA_FAST": result["sma_windows"][0] if result["sma_windows"] else None,
                "SMA_SLOW": result["sma_windows"][1] if result["sma_windows"] else None,
                "EMA_FAST": result["ema_windows"][0] if result["ema_windows"] else None,
                "EMA_SLOW": result["ema_windows"][1] if result["ema_windows"] else None
            }
            
            # Log portfolio results for debugging
            if result["sma_portfolio"]:
                log(f"SMA portfolio for {result['ticker']}: {result['sma_portfolio']}")
            if result["ema_portfolio"]:
                log(f"EMA portfolio for {result['ticker']}: {result['ema_portfolio']}")
                
            rows.append(row)
            
        # Create DataFrame
        df = pl.DataFrame(rows)
        
        # Ensure export directory exists
        export_dir = os.path.join("csv", "ma_cross", "scanner_list")
        os.makedirs(export_dir, exist_ok=True)
        
        # Export to CSV
        export_path = os.path.join(export_dir, config["SCANNER_LIST"])
        df.write_csv(export_path)
        log(f"Results exported to {export_path}")
        return True
        
    except Exception as e:
        log(f"Error exporting results: {str(e)}", "error")
        return False

def run(config: Config = CONFIG) -> bool:
    """
    Run scanner list update process.

    This function:
    1. Reads strategies from scanner list
    2. Processes each strategy (SMA and/or EMA) with specified windows
    3. Exports updated results

    Args:
        config (Config): Configuration dictionary

    Returns:
        bool: True if execution successful
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_update_scanner_list.log'
    )
    
    try:
        # Initialize configuration
        config = get_config(config)
        
        # Read scanner list
        scanner_path = os.path.join("app", "ma_cross", "scanner_lists", config["SCANNER_LIST"])
        df = pl.read_csv(scanner_path)
        log(f"Loaded scanner list: {config['SCANNER_LIST']}")
        
        # Process each row
        results: List[StrategyResult] = []
        for row in df.iter_rows(named=True):
            ticker = row["TICKER"]
            log(f"Processing {ticker}")
            
            # Extract windows if they exist
            sma_windows = None
            if not pl.Series([row["SMA_FAST"], row["SMA_SLOW"]]).is_null().any():
                sma_windows = (int(row["SMA_FAST"]), int(row["SMA_SLOW"]))
                
            ema_windows = None
            if not pl.Series([row["EMA_FAST"], row["EMA_SLOW"]]).is_null().any():
                ema_windows = (int(row["EMA_FAST"]), int(row["EMA_SLOW"]))
            
            # Process strategies
            result = process_strategy(ticker, sma_windows, ema_windows, config, log)
            results.append(result)
            
        # Export results
        if export_results(results, config, log):
            log("Scanner list update completed successfully")
            log_close()
            return True
        else:
            raise Exception("Failed to export results")
            
    except Exception as e:
        log(f"Scanner list update failed: {str(e)}", "error")
        log_close()
        raise
        
if __name__ == "__main__":
    run()