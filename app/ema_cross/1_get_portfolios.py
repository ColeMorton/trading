"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA and SMA cross strategies, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.ema_cross.tools.filter_portfolios import filter_portfolios
from app.ema_cross.tools.export_portfolios import export_portfolios, PortfolioExportError
from app.ema_cross.tools.signal_processing import process_ticker_portfolios
from app.ema_cross.tools.portfolio_selection import get_best_portfolio
from app.ema_cross.tools.summary_processing import reorder_columns
from app.ema_cross.config_types import PortfolioConfig, DEFAULT_CONFIG

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
        # Initialize configuration and tickers
        config = get_config(config)
        tickers = [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
        
        # List to store best portfolios
        best_portfolios = []
        
        # Process each ticker
        for ticker in tickers:
            log(f"Processing ticker: {ticker}")
            
            # Create a config copy with single ticker
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker
            ticker_config["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
            
            # Process portfolios for ticker
            portfolios_df = process_ticker_portfolios(ticker, ticker_config, log)
            if portfolios_df is None:
                continue
                
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

                # Get best portfolio
                best_portfolio = get_best_portfolio(filtered_portfolios, ticker_config, log)
                if best_portfolio is not None:
                    log(f"Best portfolio for {ticker}:")
                    print(best_portfolio)
                    best_portfolios.append(best_portfolio)

        # Export best portfolios if any were found
        if best_portfolios:
            try:
                export_portfolios(
                    portfolios=best_portfolios,
                    config=config,  # Use original config for all tickers
                    export_type="portfolios_best",
                    log=log
                )
                log(f"Exported {len(best_portfolios)} best portfolios")
            except (ValueError, PortfolioExportError) as e:
                log(f"Failed to export best portfolios: {str(e)}", "error")

        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

if __name__ == "__main__":
    try:
        # Run analysis with both EMA and SMA
        config_copy = DEFAULT_CONFIG.copy()
        config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
        run({**config_copy, "USE_SMA": False})  # Run with EMA
        run({**config_copy, "USE_SMA": True})   # Run with SMA
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
