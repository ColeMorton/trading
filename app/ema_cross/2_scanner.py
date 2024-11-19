import os
import polars as pl
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.utils import get_path, get_filename
from app.ema_cross.tools.process_ma_signals import process_ma_signals
from app.ema_cross.tools.is_file_from_today import is_file_from_today

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup logging
log_dir = os.path.join(project_root, 'logs', 'ma_cross')
log, log_close, _, _ = setup_logging('ma_cross', log_dir, '2_scanner.log')

class Config(TypedDict):
    TICKER: str
    WINDOWS: int
    SCANNER_LIST: str
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

# Default Configuration
config: Config = {
    "WINDOWS": 89,
    "SCANNER_LIST": 'DAILY.csv'
}

def process_scanner():
    """
    Process each ticker in csv with both SMA and EMA configurations.
    Creates a DataFrame with results and exports to CSV.
    """
    try:
        # Determine which CSV file to use based on USE_HOURLY config
        csv_filename = 'HOURLY.csv' if config.get("USE_HOURLY", False) else config.get("SCANNER_LIST", 'DAILY.csv')
        
        # Read scanner data using polars
        scanner_df = pl.read_csv(f'app/ema_cross/scanner_lists/{csv_filename}')
        
        # Initialize empty lists to store results
        results_data = []
        
        # If not using hourly data, check for existing results from today
        existing_tickers = set()
        if not config.get("USE_HOURLY", False):
            csv_path = get_path("csv", "ma_cross", config, 'portfolios_scanned')
            results_filename = get_filename("csv", config)
            full_path = os.path.join(csv_path, results_filename)
            
            if is_file_from_today(full_path):
                try:
                    existing_results = pl.read_csv(full_path)
                    existing_tickers = set(existing_results['TICKER'].to_list())
                    results_data = existing_results.to_dicts()
                    log(f"Found existing results from today with {len(existing_tickers)} tickers")
                except Exception as e:
                    log(f"Error reading existing results: {e}", "error")
        
        # Filter scanner list to only process new tickers
        for row in scanner_df.iter_rows(named=True):
            ticker = row['TICKER']
            
            # Skip if ticker already processed today
            if ticker in existing_tickers:
                continue
                
            log(f"Processing {ticker}")
            
            # Process SMA signals
            sma_current = process_ma_signals(
                ticker=ticker,
                ma_type="SMA",
                config=config,
                fast_window=row['SMA_FAST'],
                slow_window=row['SMA_SLOW']
            )
            
            # Process EMA signals
            ema_current = process_ma_signals(
                ticker=ticker,
                ma_type="EMA",
                config=config,
                fast_window=row['EMA_FAST'],
                slow_window=row['EMA_SLOW']
            )
            
            # Add results to list
            results_data.append({
                "TICKER": ticker,
                "SMA": sma_current,
                "EMA": ema_current
            })
        
        # Create results DataFrame
        results_df = pl.DataFrame(results_data)
        
        # Export results to CSV
        if not config.get("USE_HOURLY", False):
            csv_path = get_path("csv", "ma_cross", config, 'portfolios_scanned')
            csv_filename = get_filename("csv", config)
            results_df.write_csv(csv_path + "/" + csv_filename)
                
    except Exception as e:
        log(f"Error processing scanner: {e}", "error")
        raise

if __name__ == "__main__":
    try:
        config = get_config(config)
        config["USE_SCANNER"] = True
        process_scanner()
        log_close()
    except Exception as e:
        log(f"Execution failed: {e}", "error")
        raise
