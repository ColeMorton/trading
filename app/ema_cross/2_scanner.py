import os
import polars as pl
from typing import TypedDict, NotRequired, List, Dict
from app.tools.setup_logging import setup_logging
from app.ema_cross.tools.generate_current_signals import generate_current_signals

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

def check_signal_match(signals: List[Dict], fast_window: int, slow_window: int) -> bool:
    """
    Check if any signal matches the given window combination.

    Args:
        signals: List of signal dictionaries containing window information
        fast_window: Fast window value to match
        slow_window: Slow window value to match

    Returns:
        bool: True if a matching signal is found, False otherwise
    """
    if not signals:
        return False
    
    return any(
        signal["Short Window"] == fast_window and 
        signal["Long Window"] == slow_window
        for signal in signals
    )

def process_ma_signals(ticker: str, ma_type: str, config: Config, 
                      fast_window: int, slow_window: int) -> None:
    """
    Process moving average signals for a given ticker and configuration.

    Args:
        ticker: The ticker symbol to process
        ma_type: Type of moving average ('SMA' or 'EMA')
        config: Configuration dictionary
        fast_window: Fast window value from scanner
        slow_window: Slow window value from scanner

    Returns:
        None
    """
    ma_config = config.copy()
    ma_config.update({
        "TICKER": ticker,
        "USE_SMA": ma_type == "SMA"
    })
    
    signals = generate_current_signals(ma_config)
    
    is_current = check_signal_match(
        signals.to_dicts() if len(signals) > 0 else [], 
        fast_window, 
        slow_window
    )
    
    message = (
        f"{ticker} {ma_type} - {'Current signal found' if is_current else 'No signals'} "
        f"for {fast_window}/{slow_window}{'!!!!!' if is_current else ''}"
    )
    log(message)
    print(message)

def process_scanner():
    """
    Process each ticker in csv with both SMA and EMA configurations.
    Checks if current signals match the window combinations in csv.
    """
    try:
        # Determine which CSV file to use based on USE_HOURLY config
        csv_filename = 'HOURLY.csv' if config.get("USE_HOURLY", False) else 'DAILY.csv'
        
        # Read scanner data using polars
        scanner_df = pl.read_csv(f'app/ema_cross/scanner_lists/{csv_filename}')
        
        for row in scanner_df.iter_rows(named=True):
            ticker = row['TICKER']
            log(f"Processing {ticker}")
            
            # Process SMA signals
            process_ma_signals(
                ticker=ticker,
                ma_type="SMA",
                config=config,
                fast_window=row['SMA_FAST'],
                slow_window=row['SMA_SLOW']
            )
            
            # Process EMA signals
            process_ma_signals(
                ticker=ticker,
                ma_type="EMA",
                config=config,
                fast_window=row['EMA_FAST'],
                slow_window=row['EMA_SLOW']
            )
                
    except Exception as e:
        log(f"Error processing scanner: {e}", "error")
        raise

if __name__ == "__main__":
    try:
        config["USE_SCANNER"] = True
        process_scanner()
        log_close()
    except Exception as e:
        log(f"Execution failed: {e}", "error")
        raise
