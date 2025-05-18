"""
Update Portfolios Module for Multiple Strategy Types

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of SMA, EMA, and MACD strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.

The module supports both regular tickers and synthetic tickers (identified by an underscore
in the ticker name, e.g., 'STRK_MSTR'). Synthetic tickers are automatically detected and
processed by splitting them into their component tickers.
"""
from app.tools.project_utils import (
    get_project_root,
    resolve_path
)
from app.tools.portfolio_results import (
    sort_portfolios,
    filter_open_trades,
    filter_signal_entries,
    calculate_breadth_metrics
)
from app.tools.entry_point import run_from_command_line
from app.tools.logging_context import logging_context
from app.tools.error_context import error_context
from app.tools.error_decorators import handle_errors
from app.tools.exceptions import (
    PortfolioLoadError,
    StrategyProcessingError,
    SyntheticTickerError,
    ExportError,
    TradingSystemError
)
from app.strategies.tools.summary_processing import (
    process_ticker_portfolios,
    export_summary_results
)
from app.tools.portfolio import (
    load_portfolio_with_logging,  # Using enhanced loader
    PortfolioLoadError            # Using specific error type
)
from app.tools.config_management import (
    normalize_config,
    resolve_portfolio_filename
)
from app.tools.synthetic_ticker import (
    detect_synthetic_ticker,
    process_synthetic_ticker
)
from app.tools.strategy_utils import (
    filter_portfolios_by_signal
)

# Default Configuration
config = {
    # "PORTFOLIO": 'BTC-USD_SPY_d.csv',
    # "PORTFOLIO": 'total_d_20250328.csv',
    # "PORTFOLIO": 'crypto_d_20250421.csv',
    # "PORTFOLIO": 'DAILY_crypto.csv',
    # "PORTFOLIO": 'DAILY.csv',
    # "PORTFOLIO": 'DAILY_test.csv',
    # "PORTFOLIO": 'crypto_h.csv',
    # "PORTFOLIO": 'DAILY_crypto_short.csv',
    # "PORTFOLIO": 'Indices_d.csv',
    # "PORTFOLIO": 'stock_trades_20250422.csv',
    # "PORTFOLIO": 'portfolio_d_20250505.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": "QQQ_d_20250404.csv",
    # "PORTFOLIO": "TLT_d_20250404.csv",
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    # "PORTFOLIO": 'BTC_MSTR_TLT_d_20250404.csv',
    # "PORTFOLIO": 'HIMS_d_20250513.csv',
    "PORTFOLIO": 'QQQ_d_20250508.csv',
    # "PORTFOLIO": 'NFLX_d_20250410.csv',
    # "PORTFOLIO": 'COIN_d_20250414.csv',
    # "PORTFOLIO": 'MSTY_h.csv',
    # "PORTFOLIO": 'BTC_h_20250416.csv',
    # "PORTFOLIO": 'STRK_h_20250415.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": 'SPY_QQQ_RSP_20250506.csv',
    "REFRESH": False,
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": get_project_root(),  # Use standardized project root resolver
    "DIRECTION": "Long",
    "SORT_BY": "Score",
    "SORT_ASC": False
}

@handle_errors(
    "Portfolio update process",
    {
        PortfolioLoadError: PortfolioLoadError,
        ValueError: StrategyProcessingError,
        KeyError: StrategyProcessingError,
        Exception: TradingSystemError
    }
)
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
        PortfolioLoadError: If the portfolio cannot be loaded
        StrategyProcessingError: If there's an error processing a strategy
        SyntheticTickerError: If there's an issue with synthetic ticker processing
        ExportError: If results cannot be exported
        TradingSystemError: For other unexpected errors
    """
    with logging_context(
        module_name='strategies',
        log_file='update_portfolios.log'
    ) as log:
        # Get a normalized copy of the global config
        local_config = normalize_config(config.copy())
        
        # Use the enhanced portfolio loader with standardized error handling
        with error_context(
            "Loading portfolio",
            log,
            {FileNotFoundError: PortfolioLoadError}
        ):
            daily_df = load_portfolio_with_logging(portfolio, log, local_config)
            if not daily_df:
                return False

            portfolios = []
            
        # Process each ticker
        for strategy in daily_df:
            ticker = strategy['TICKER']
            log(f"Processing {ticker}")
            # Create a copy of the config for this strategy
            strategy_config = local_config.copy()
            
            
            # Check if this is a synthetic ticker (contains underscore)
            with error_context(
                f"Processing synthetic ticker {ticker}",
                log,
                {ValueError: SyntheticTickerError},
                reraise=False
            ):
                if detect_synthetic_ticker(ticker):
                    try:
                        ticker1, ticker2 = process_synthetic_ticker(ticker)
                        # Update config for synthetic ticker processing
                        strategy_config["USE_SYNTHETIC"] = True
                        strategy_config["TICKER_1"] = ticker1
                        strategy_config["TICKER_2"] = ticker2
                        log(f"Detected synthetic ticker: {ticker} (components: {ticker1}, {ticker2})")
                    except SyntheticTickerError as e:
                        log(f"Invalid synthetic ticker format: {ticker} - {str(e)}", "warning")
            
            # Process the ticker portfolio
            with error_context(
                f"Processing ticker portfolio for {ticker}",
                log,
                {Exception: StrategyProcessingError},
                reraise=False
            ):
                result = process_ticker_portfolios(ticker, strategy, strategy_config, log)
                if result:
                    portfolios.extend(result)

        # Export results with config
        with error_context(
            "Exporting summary results",
            log,
            {Exception: ExportError},
            reraise=False
        ):
            success = export_summary_results(portfolios, portfolio, log, local_config)
            # Display strategy data as requested
            if success and portfolios:
                log("=== Strategy Summary ===")
                
                # Sort portfolios by Score (descending) for main display
                sorted_portfolios = sort_portfolios(portfolios, "Score", False)
                
                # Use standardized utility to filter and display open trades
                open_trades_strategies = filter_open_trades(sorted_portfolios, log)
                
                # Use standardized utility to filter and display signal entries
                # First get signal entries using the strategy_utils filter
                temp_config = {"USE_CURRENT": True}
                signal_entry_strategies = filter_portfolios_by_signal(sorted_portfolios, temp_config, log)
                
                # Then use the portfolio_results utility to process and display them
                signal_entry_strategies = filter_signal_entries(signal_entry_strategies, open_trades_strategies, log)
                
                # Calculate and display breadth metrics
                if sorted_portfolios:
                    calculate_breadth_metrics(
                        sorted_portfolios,
                        open_trades_strategies,
                        signal_entry_strategies,
                        log
                    )
            
        return success

if __name__ == "__main__":
    # Create a normalized copy of the default config
    normalized_config = normalize_config(config.copy())
    portfolio_name = normalized_config.get("PORTFOLIO", 'MSTR_d_20250403.csv')
    
    # Resolve portfolio filename with extension if needed
    resolved_portfolio = resolve_portfolio_filename(portfolio_name)
    
    # Use the standardized entry point utility
    run_from_command_line(
        lambda _: run(resolved_portfolio),  # Wrapper function to match expected signature
        {},  # Empty config as we're passing the portfolio directly to run()
        "portfolio update"
    )