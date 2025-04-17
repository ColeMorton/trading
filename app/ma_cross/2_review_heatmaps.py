"""
Heatmap Generation Module for EMA Cross Strategy

This module generates heatmaps visualizing the performance of different moving average
window combinations for the EMA cross strategy from portfolio data.
"""

from app.tools.setup_logging import setup_logging
from app.tools.heatmap_utils import process_heatmap_data
from app.ma_cross.config_types import HeatmapConfig

def run(config: HeatmapConfig = {
    "USE_CURRENT": True,
    "USE_BEST_PORTFOLIO": False,  # Default to regular portfolios directory
    "USE_SMA": True,
    "TICKER": 'ALL',
    "TICKER_1": 'BTC-USD',
    "TICKER_2": 'BTC-USD',
    "WINDOWS": 89,
    "USE_HOURLY": False,
    "USE_SYNTHETIC": False,
    "REFRESH": True,
    "BASE_DIR": ".",
    "DIRECTION": "Long"  # Default to Long position
}) -> bool:
    """Run the heatmap generation process.

    This function:
    1. Sets up logging
    2. Processes portfolio data
    3. Generates heatmaps based on portfolio performance

    Args:
        config (HeatmapConfig): Configuration dictionary

    Returns:
        bool: True if heatmap generation successful

    Raises:
        Exception: If portfolio data is missing or heatmap generation fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_get_heatmaps.log'
    )
    
    try:
        result = process_heatmap_data(config, log)
        log_close()
        return result
        
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        result = run()
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
