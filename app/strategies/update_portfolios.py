"""
Update Portfolios Module for Multiple Strategy Types

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of SMA, EMA, and MACD strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.

The module supports both regular tickers and synthetic tickers (identified by an underscore
in the ticker name, e.g., 'STRK_MSTR'). Synthetic tickers are automatically detected and
processed by splitting them into their component tickers.
"""

from app.tools.setup_logging import setup_logging
from app.strategies.tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)
from app.tools.portfolio import (
    load_portfolio
)

# Default Configuration
config = {
    # "PORTFOLIO": 'spy_qqq_h_20250311.csv',
    # "PORTFOLIO": 'total_d_20250328.csv',
    # "PORTFOLIO": 'DAILY_crypto.csv',
    "PORTFOLIO": 'DAILY.csv',
    # "PORTFOLIO": 'crypto_h.csv',
    # "PORTFOLIO": 'DAILY_crypto_short.csv',
    # "PORTFOLIO": 'Indices_d.csv',
    # "PORTFOLIO": 'stock_trades_20250404.csv',
    # "PORTFOLIO": 'portfolio_d_20250410.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": "QQQ_d_20250404.csv",
    # "PORTFOLIO": "TLT_d_20250404.csv",
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    # "PORTFOLIO": 'BTC_MSTR_TLT_d_20250404.csv',
    # "PORTFOLIO": 'MSTR_vs_MSTY_h_20250409.csv',
    # "PORTFOLIO": 'NVDA_d_20250410.csv',
    # "PORTFOLIO": 'BTC_d.csv',
    # "PORTFOLIO": 'MSTY_h.csv',
    # "PORTFOLIO": 'ORLY_d_20250410.csv',
    # "PORTFOLIO": 'TLT_EDV_d_20250404.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": 'SPY_QQQ_20250327.csv',
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": '.',  # Added BASE_DIR for export configuration
    "DIRECTION": "Long",
    "SORT_BY": "Score",
    "SORT_ASC": False
}

def run(portfolio: str) -> bool:
    """
    Process portfolio and generate portfolio summary.

    This function:
    1. Reads the portfolio
    2. Processes each ticker with appropriate strategy (SMA, EMA, or MACD)
    3. Detects and processes synthetic tickers (those containing an underscore)
    4. Calculates performance metrics and adjustments
    5. Exports combined results to CSV

    Args:
        portfolio (str): Name of the portfolio file

    Returns:
        bool: True if execution successful, False otherwise

    Raises:
        Exception: If processing fails
    """
    log, log_close, _, _ = setup_logging(
        module_name='strategies',
        log_file='update_portfolios.log'
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
            
            # Create a copy of the config for this strategy
            strategy_config = config.copy()
            
            # Check if this is a synthetic ticker (contains underscore)
            if '_' in ticker:
                ticker_parts = ticker.split('_')
                if len(ticker_parts) == 2:
                    ticker1, ticker2 = ticker_parts
                    # Update config for synthetic ticker processing
                    strategy_config["USE_SYNTHETIC"] = True
                    strategy_config["TICKER_1"] = ticker1
                    strategy_config["TICKER_2"] = ticker2
                    log(f"Detected synthetic ticker: {ticker} (components: {ticker1}, {ticker2})")
                else:
                    log(f"Invalid synthetic ticker format: {ticker}", "warning")
            
            # Pass the updated config to process_ticker_portfolios
            result = process_ticker_portfolios(ticker, strategy, strategy_config, log)
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