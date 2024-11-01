import logging
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from app.tools.get_config import get_config
from app.ema_cross.tools.get_current_signals import get_current_signals
from app.utils import get_data, get_path, get_filename
from app.geometric_brownian_motion.get_median import get_median

# Default Configuration
CONFIG = {
    "YEARS": 30,
    "USE_YEARS": False,
    "PERIOD": 'max',
    "USE_HOURLY": False,
    "TICKER": 'AAPL',
    "USE_SYNTHETIC": False,
    "TICKER_1": 'BCH-USD',
    "TICKER_2": 'SPY',
    "SHORT_WINDOW": 11,
    "LONG_WINDOW": 17,
    "SHORT": False,
    "USE_GBM": False,
    "USE_SMA": True,
    "BASE_DIR": 'C:/Projects/trading',
    "WINDOWS": 55
}

config = get_config(CONFIG)

# Logging setup
logging.basicConfig(filename='./logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def create_heatmap(df_pandas):
    """Create a heatmap visualization of the signals."""
    # Pivot the data for the heatmap with Long Window on Y-axis and Short Window on X-axis
    pivot_table = pd.crosstab(df_pandas['Long Window'], df_pandas['Short Window'])
    
    # Create annotation text for each cell
    annotations = []
    for long_window in pivot_table.index:
        row_annotations = []
        for short_window in pivot_table.columns:
            row_annotations.append(f"{short_window}:{long_window}")
        annotations.append(row_annotations)
    
    # Create the heatmap
    plt.figure(figsize=(14, 10))
    sns.heatmap(pivot_table, cmap='YlOrRd', annot=np.array(annotations), fmt='', 
                annot_kws={'size': 8})  # Reduced font size
    plt.gca().invert_yaxis()  # Invert the Y-axis
    plt.xlabel('Short Window')
    plt.ylabel('Long Window')
    plt.title('EMA Cross Signals: Short vs Long Windows')
    plt.show()

def run() -> None:
    """Main execution method."""

    # Create distinct integer values for windows
    short_windows = np.arange(2, config["WINDOWS"])  # [2, 3, ..., WINDOWS]
    long_windows = np.arange(3, config["WINDOWS"])  # [3, 4, ..., WINDOWS]

    if config.get('USE_GBM', False) == True:
        data = get_median(config)
    else:
        data = get_data(config)

    current_signals = get_current_signals(data, short_windows, long_windows, config)
    
    # Convert Polars DataFrame to Pandas DataFrame
    df_pandas = current_signals.to_pandas()
    
    # Save full data to CSV
    csv_path = get_path("csv", "ma_cross", config, 'current_signals')
    csv_filename = get_filename("csv", config)
    df_pandas.to_csv(csv_path + "/" + csv_filename, index=False)
    
    # Display full data
    pd.set_option('display.max_rows', None)
    print("\nFull data table:")
    print(current_signals)

    if len(current_signals) == 0:
        print("No signals found for today")
    else:
        # Create visualization
        create_heatmap(df_pandas)
        
        print(f"\nData has been saved to '{csv_path}'")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        raise
