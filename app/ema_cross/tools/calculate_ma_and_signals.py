import logging
import polars as pl
from datetime import datetime
from app.utils import calculate_mas, generate_ma_signals, get_data, getPath

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": False,
    "BASE_DIR": 'C:/Projects/trading'
}

# Logging setup
logging.basicConfig(filename='./logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def calculate_ma_and_signals(data: pl.DataFrame, short_window: int, long_window: int, config: dict) -> pl.DataFrame:
    """Calculate MAs and generate trading signals."""
    ma_type = "SMA" if config.get('USE_SMA', False) else "EMA"

    logging.info(f"Calculating {ma_type}s and signals with short window {short_window} and long window {long_window}")
    try:
        data = calculate_mas(data, short_window, long_window)
        entries, exits = generate_ma_signals(data, config)
        
        # When a Signal of 1 appears, it means "we should enter a trade"
        data = data.with_columns([
            pl.when(entries).then(1).otherwise(0).alias("Signal")
        ])
        
        # The Position of 1 in the next period shows "we are now in the trade"
        data = data.with_columns([
            pl.col("Signal").shift(1).alias("Position")
        ])
        
        logging.info(f"{ma_type}s and signals calculated successfully")

        # Export to CSV
        csv_path = getPath("csv", "ma_cross", config, 'signals')
        csv_filename = f'{config["TICKER_1"]}{"_H" if config.get("USE_HOURLY_DATA", False) else "_D"}{"_SMA" if config.get("USE_SMA", False) else "_EMA"}{"_" + datetime.now().strftime("%Y%m%d") if config.get("SHOW_LAST", True) else ""}.csv'
        data.write_csv(csv_path + "/" + csv_filename)

        return data
    except Exception as e:
        logging.error(f"Failed to calculate {ma_type}s and signals: {e}")
        raise

def run() -> None:
    """Main execution method."""

    data = get_data(CONFIG)
    signals = calculate_ma_and_signals(data, CONFIG["SHORT_WINDOW"], CONFIG["LONG_WINDOW"], CONFIG)

    print(signals)

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise