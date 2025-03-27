"""
Update Portfolios Module for MA Cross Strategyies

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of both SMA and EMA strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.
"""

from app.tools.setup_logging import setup_logging
from app.ma_cross.tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)
from app.tools.portfolio import (
    load_portfolio
)

# Default Configuration
config = {
    # "PORTFOLIO": 'spy_qqq_h_20250311.csv',
    # "PORTFOLIO": 'total_d_20250326.csv',
    # "PORTFOLIO": 'DAILY_crypto.csv',
    "PORTFOLIO": 'DAILY.csv',
    # "PORTFOLIO": 'crypto_h.csv',
    # "PORTFOLIO": 'btc_20250307.csv',
    # "PORTFOLIO": 'DAILY_crypto_short.csv',
    # "PORTFOLIO": 'Indices_d.csv',
    # "PORTFOLIO": 'stock_trades_20250325.csv',
    # "PORTFOLIO": "SPY_QQQ_D.csv",
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    # "PORTFOLIO": 'SPY_GLD_BTC_20250316.csv',
    # "PORTFOLIO": 'GLD_h.csv',
    # "PORTFOLIO": 'BTC_d.csv',
    # "PORTFOLIO": 'MSTY_h.csv',
    # "PORTFOLIO": 'SPY_QQQ_202503026.csv',
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": '.',  # Added BASE_DIR for export configuration
    "DIRECTION": "Long",
    "SORT_BY": "Expectancy Adjusted",
    "SORT_ASC": False
}

def run(portfolio: str) -> bool:
    """
    Process portfolio and generate portfolio summary.

    This function:
    1. Reads the portfolio
    2. Processes each ticker with both SMA and EMA strategies
    3. Calculates performance metrics and adjustments
    4. Exports combined results to CSV

    Args:
        portfolio (str): Name of the portfolio file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        Exception: If processing fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='ma_cross',
        log_file='2_update_portfolios.log'
    )
    
    try:
        # Load portfolio using the shared portfolio loader
        try:
            daily_df = load_portfolio(portfolio, log, config)
            log(f"Successfully loaded portfolio with {len(daily_df)} entries")
        except FileNotFoundError:
            log(f"Portfolio not found: {portfolio}", "error")
            log_close()
            return False

        portfolios = []
        
        # Process each ticker
        for strategy in daily_df:
            ticker = strategy['TICKER']
            log(f"Processing {ticker}")
            
            # Pass the config to process_ticker_portfolios
            result = process_ticker_portfolios(ticker, strategy, config, log)
            if result:
                portfolios.extend(result)

        # Export results with config
        success = export_summary_results(portfolios, portfolio, log, config)
        
        log_close()
        return success
        
    except Exception as e:
        log(f"Run failed: {e}", "error")
        log_close()
        return False

if __name__ == "__main__":
    try:
        result = run(config.get("PORTFOLIO", 'DAILY.csv'))
        if result:
            print("Execution completed successfully!")
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise