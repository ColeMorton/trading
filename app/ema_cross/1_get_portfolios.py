"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA and SMA cross strategies, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.ema_cross.config_types import PortfolioConfig, DEFAULT_CONFIG
from app.ema_cross.tools.strategy_execution import execute_strategy
from app.ema_cross.tools.portfolio_collection import export_best_portfolios, combine_strategy_portfolios

def run(config: PortfolioConfig = DEFAULT_CONFIG) -> bool:
    """Run portfolio analysis for single or multiple tickers.
    
    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis
    3. Filters portfolios based on criteria
    4. Displays and saves results
    
    Args:
        config (PortfolioConfig): Configuration dictionary containing analysis parameters
        
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
        
        # Execute strategy and collect best portfolios
        best_portfolios = execute_strategy(config, "EMA" if not config.get("USE_SMA") else "SMA", log)
        
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
            log_file='1_get_portfolios_combined.log'
        )
        
        # Initialize base config
        config_copy = DEFAULT_CONFIG.copy()
        config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
        
        # Run EMA strategy
        log("Running EMA strategy analysis...")
        ema_config = {**config_copy, "USE_SMA": False}
        ema_portfolios = execute_strategy(ema_config, "EMA", log)
        
        # Run SMA strategy
        log("Running SMA strategy analysis...")
        sma_config = {**config_copy, "USE_SMA": True}
        sma_portfolios = execute_strategy(sma_config, "SMA", log)
        
        # Combine and export best portfolios
        all_portfolios = combine_strategy_portfolios(ema_portfolios, sma_portfolios)
        if all_portfolios:
            export_best_portfolios(all_portfolios, config_copy, log)
        
        log_close()
        return True
        
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_both_strategies()
