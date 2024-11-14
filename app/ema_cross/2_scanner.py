import os
import polars as pl
from typing import TypedDict, NotRequired
from app.tools.setup_logging import setup_logging
from app.tools.get_config import get_config
from app.utils import get_path, get_filename
from app.ema_cross.tools.process_ma_signals import process_ma_signals

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Setup logging
log_dir = os.path.join(project_root, 'logs', 'ma_cross')
log, log_close, _, _ = setup_logging('ma_cross', log_dir, '2_scanner.log')

class Config(TypedDict):
    TICKER: str
    WINDOWS: int
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
    "WINDOWS": 89
}

def process_scanner():
    """
    Process each ticker in csv with both SMA and EMA configurations.
    Creates a DataFrame with results and exports to CSV.
    """
    try:
        # Determine which CSV file to use based on USE_HOURLY config
        csv_filename = 'HOURLY.csv' if config.get("USE_HOURLY", False) else 'DAILY.csv'
        
        # Read scanner data using polars
        scanner_df = pl.read_csv(f'app/ema_cross/scanner_lists/{csv_filename}')
        
        # Initialize empty lists to store results
        results_data = []
        
        for row in scanner_df.iter_rows(named=True):
            ticker = row['TICKER']
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
