"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA and SMA cross strategies, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

import os
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.ma_cross.config_types import Config
from app.ma_cross.tools.strategy_execution import execute_strategy
from app.tools.portfolio.collection import export_best_portfolios, combine_strategy_portfolios

CONFIG: Config = {
    "TICKER": [
        'BNB-USD',
        'TRX-USD'
    ],
    "TICKER_1": 'AMAT',
    "TICKER_2": 'LRCX',
    "WINDOWS": 89,
    # "WINDOWS": 120,
    # "WINDOWS": 55,
    # "SCANNER_LIST": 'DAILY.csv',
    # "USE_SCANNER": True,
    "BASE_DIR": ".",
    "REFRESH": True,
    # "USE_SMA": False,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": False,
    "MIN_TRADES": 34,
    "MIN_WIN_RATE": 0.35,
    # "MIN_WIN_RATE": 0.5,
    # "MIN_TRADES": 50,
    "SORT_BY": "Expectancy Adjusted",
    "USE_GBM": False
}

def run(config: Config = CONFIG) -> bool:
    """Run portfolio analysis for single or multiple tickers.
    
    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis
    3. Filters portfolios based on criteria
    4. Displays and saves results
    
    Args:
        config (Config): Configuration dictionary containing analysis parameters
        
    Returns:
        bool: True if execution successful
        
    Raises:
        Exception: If portfolio analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='1_get_portfolios.log'
    )
    
    try:
        # Initialize configuration
        config = get_config(config)
        
        # Ensure BASE_DIR is absolute
        if not os.path.isabs(config["BASE_DIR"]):
            config["BASE_DIR"] = os.path.abspath(config["BASE_DIR"])
        
        # Handle synthetic pair if enabled
        if config.get("USE_SYNTHETIC"):
            if not config.get("TICKER_1") or not config.get("TICKER_2"):
                raise ValueError("TICKER_1 and TICKER_2 must be provided when USE_SYNTHETIC is True")
            synthetic_ticker = f"{config['TICKER_1']}_{config['TICKER_2']}"
            log(f"Processing strategy for synthetic pair: {config['TICKER_1']}_{config['TICKER_2']}")
            # Create a modified config with the synthetic pair settings
            synthetic_config = {**config}
            synthetic_config["TICKER"] = synthetic_ticker  # Set synthetic ticker for file naming
        else:
            log(f"Processing strategy for ticker: {config['TICKER']}")
            synthetic_config = config

        # Execute strategy and collect best portfolios
        best_portfolios = execute_strategy(synthetic_config, "EMA" if not config.get("USE_SMA") else "SMA", log)
        
        # Export best portfolios
        if best_portfolios:
            export_best_portfolios(best_portfolios, config, log)
        
        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

def run_both_strategies() -> bool:
    """Run analysis with both EMA and SMA strategies.
    
    Returns:
        bool: True if execution successful
    """
    try:
        # Initialize logging
        log, log_close, _, _ = setup_logging(
            module_name='ma_cross',
            log_file='1_get_portfolios.log'
        )
        
        # Initialize config
        config_copy = CONFIG.copy()
        config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
        
        # Handle synthetic pair if enabled
        if config_copy.get("USE_SYNTHETIC"):
            if not config_copy.get("TICKER_1") or not config_copy.get("TICKER_2"):
                raise ValueError("TICKER_1 and TICKER_2 must be provided when USE_SYNTHETIC is True")
            synthetic_ticker = f"{config_copy['TICKER_1']}_{config_copy['TICKER_2']}"
            log(f"Processing strategies for synthetic pair: {config_copy['TICKER_1']}_{config_copy['TICKER_2']}")
            base_config = {**config_copy}
            base_config["TICKER"] = synthetic_ticker  # Set synthetic ticker for file naming
        else:
            log(f"Processing strategies for ticker: {config_copy['TICKER']}")
            base_config = config_copy

        # Run EMA strategy
        log("Running EMA strategy analysis...")
        ema_config = {**base_config, "USE_SMA": False}
        ema_portfolios = execute_strategy(ema_config, "EMA", log)
        
        # Run SMA strategy
        log("Running SMA strategy analysis...")
        sma_config = {**base_config, "USE_SMA": True}
        sma_portfolios = execute_strategy(sma_config, "SMA", log)
        
        # Combine and export best portfolios
        all_portfolios = combine_strategy_portfolios(ema_portfolios, sma_portfolios)
        if all_portfolios:
            # Ensure synthetic ticker is properly set for export
            if config_copy.get("USE_SYNTHETIC"):
                if not config_copy.get("TICKER_1") or not config_copy.get("TICKER_2"):
                    raise ValueError("TICKER_1 and TICKER_2 must be provided when USE_SYNTHETIC is True")
                config_copy["TICKER"] = f"{config_copy['TICKER_1']}_{config_copy['TICKER_2']}"
            export_best_portfolios(all_portfolios, config_copy, log)
        
        log_close()
        return True
        
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_both_strategies()
