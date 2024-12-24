"""
Portfolio Analysis Module for Range High Break Strategy

This module handles portfolio analysis for the Range High Break strategy, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.

The Range High Break strategy:
- Entry condition: Price close is greater than range_length High 1 candle ago
- Exit condition: Price close is NOT greater than range_length High candle_lookback candles ago

Parameter Sensitivity Testing:
- range_length: Integer values from 2 to 34 (period length for calculating range high)
- candle_lookback: Integer values from 1 to 21 (lookback period for exit condition)
"""

from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.range.config_types import PortfolioConfig, DEFAULT_CONFIG
from app.range.tools.strategy_execution import execute_strategy
from app.range.tools.portfolio_collection import export_best_portfolios

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
        module_name='range',
        log_file='1_get_portfolios.log'
    )
    
    try:
        # Initialize configuration
        config = get_config(config)
        
        # Execute Range High Break strategy and collect best portfolios
        best_portfolios = execute_strategy(config, "RANGE", log)
        
        # Export best portfolios
        if best_portfolios:
            export_best_portfolios(best_portfolios, config, log)
        
        log_close()
        return True
            
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
