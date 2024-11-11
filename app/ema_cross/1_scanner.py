import logging
import pandas as pd
import polars as pl
from typing import TypedDict, NotRequired
from app.ema_cross.tools.generate_current_signals import generate_current_signals

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
    "USE_SMA": True,
    "TICKER": 'ZEC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False
}

# Logging setup
logging.basicConfig(filename='./logs/ma_cross/1_scanner.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def process_scanner():
    """
    Process each ticker in SCANNER.csv with both SMA and EMA configurations.
    Checks if current signals match the window combinations in SCANNER.csv.
    
    For each ticker:
    - Processes with both SMA and EMA
    - Checks if the signal windows match those in SCANNER.csv
    - Sets Current flag based on signal match
    """
    try:
        # Read scanner data
        scanner_df = pd.read_csv('app/ema_cross/SCANNER.csv')
        
        for _, row in scanner_df.iterrows():
            ticker = row['TICKER']
            logging.info(f"Processing {ticker}")
            
            # Process with SMA
            sma_config = config.copy()
            sma_config.update({
                "TICKER": ticker,
                "USE_SMA": True
            })
            
            # Get current SMA signals
            sma_signals = generate_current_signals(sma_config)
            
            # Check if any signal matches SCANNER.csv windows
            if len(sma_signals) > 0:
                sma_current = any(
                    (signal["Short Window"] == row['SMA_FAST'] and 
                     signal["Long Window"] == row['SMA_SLOW'])
                    for signal in sma_signals.to_dicts()
                )
            else:
                sma_current = False
            
            if sma_current:
                message = f"{ticker} SMA - Current signal found matching windows {row['SMA_FAST']}/{row['SMA_SLOW']}"
                logging.info(message)
                print(message)
            else:
                message = f"{ticker} SMA - No matching current signals for windows {row['SMA_FAST']}/{row['SMA_SLOW']}"
                logging.info(message)
                print(message)
            
            # Process with EMA
            ema_config = config.copy()
            ema_config.update({
                "TICKER": ticker,
                "USE_SMA": False
            })
            
            # Get current EMA signals
            ema_signals = generate_current_signals(ema_config)
            
            # Check if any signal matches SCANNER.csv windows
            if len(ema_signals) > 0:
                ema_current = any(
                    (signal["Short Window"] == row['EMA_FAST'] and 
                     signal["Long Window"] == row['EMA_SLOW'])
                    for signal in ema_signals.to_dicts()
                )
            else:
                ema_current = False
            
            if ema_current:
                message = f"{ticker} EMA - Current signal found matching windows {row['EMA_FAST']}/{row['EMA_SLOW']}"
                logging.info(message)
                print(message)
            else:
                message = f"{ticker} EMA - No matching current signals for windows {row['EMA_FAST']}/{row['EMA_SLOW']}"
                logging.info(message)
                print(message)
                
    except Exception as e:
        logging.error(f"Error processing scanner: {e}")
        raise

if __name__ == "__main__":
    try:
        config["USE_SCANNER"] = True

        process_scanner()

        logging.info(f"Execution Success!")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
