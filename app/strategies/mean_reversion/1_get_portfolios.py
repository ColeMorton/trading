"""
Portfolio Analysis Module for Mean Reversion Strategy

This module handles portfolio analysis for the mean reversion strategy, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.mean_reversion.tools.filter_portfolios import filter_portfolios
from app.mean_reversion.tools.export_portfolios import export_portfolios, PortfolioExportError
from app.mean_reversion.tools.signal_processing import process_ticker_portfolios
from app.mean_reversion.config_types import PortfolioConfig, DEFAULT_CONFIG

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
        module_name='mean_reversion',
        log_file='1_get_portfolios.log'
    )
    
    try:
        # Initialize configuration and tickers
        config = get_config(config)
        tickers = [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
        
        # Process each ticker
        for ticker in tickers:
            log(f"Processing ticker: {ticker}")
            
            # Create a config copy with single ticker
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker
            
            # Process portfolios for ticker
            portfolios_df = process_ticker_portfolios(ticker, ticker_config, log)
            if portfolios_df is None:
                continue
                
            # Export unfiltered portfolios if using current signals
            if config.get("USE_CURRENT", False):
                try:
                    export_portfolios(
                        portfolios=portfolios_df.to_dicts(),
                        config=ticker_config,
                        export_type="portfolios",
                        log=log
                    )
                except (ValueError, PortfolioExportError) as e:
                    log(f"Failed to export portfolios for {ticker}: {str(e)}", "error")
                    continue

            # Filter portfolios for individual ticker
            filtered_portfolios = filter_portfolios(portfolios_df, ticker_config, log)
            if filtered_portfolios is not None:
                log(f"Filtered results for {ticker}")
                print(filtered_portfolios)

                # Export filtered portfolios
                try:
                    export_portfolios(
                        portfolios=filtered_portfolios.to_dicts(),
                        config=ticker_config,
                        export_type="portfolios_filtered",
                        log=log
                    )
                except (ValueError, PortfolioExportError) as e:
                    log(f"Failed to export filtered portfolios for {ticker}: {str(e)}", "error")

        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        # Run analysis with both Long and Short directions
        config_copy = DEFAULT_CONFIG.copy()
        
        # Run for both trading directions
        run({**config_copy, "DIRECTION": "Long"})  # Run Long strategy
        run({**config_copy, "DIRECTION": "Short"}) # Run Short strategy
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
