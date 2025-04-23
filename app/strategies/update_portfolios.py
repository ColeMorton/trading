"""
Update Portfolios Module for Multiple Strategy Types

This module processes the results of market scanning to update portfolios.
It aggregates and analyzes the performance of SMA, EMA, and MACD strategies across
multiple tickers, calculating key metrics like expectancy and Trades Per Day.

The module supports both regular tickers and synthetic tickers (identified by an underscore
in the ticker name, e.g., 'STRK_MSTR'). Synthetic tickers are automatically detected and
processed by splitting them into their component tickers.
"""
import os
import sys
from typing import Dict, Any, Optional
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
    PortfolioLoadError,           # Using specific error type
    portfolio_context             # Using context manager (optional)
)
from app.tools.config_management import (
    normalize_config,
    merge_configs,
    resolve_portfolio_filename
)
from app.tools.synthetic_ticker import (
    detect_synthetic_ticker,
    process_synthetic_ticker,
    process_synthetic_config
)

# Default Configuration
config = {
    "PORTFOLIO": 'BTC-USD_SPY_d.csv',
    # "PORTFOLIO": 'total_d_20250328.csv',
    # "PORTFOLIO": 'crypto_d_20250421.csv',
    # "PORTFOLIO": 'DAILY_crypto.csv',
    # "PORTFOLIO": 'DAILY.csv',
    # "PORTFOLIO": 'DAILY_test.csv',
    # "PORTFOLIO": 'crypto_h.csv',
    # "PORTFOLIO": 'DAILY_crypto_short.csv',
    # "PORTFOLIO": 'Indices_d.csv',
    # "PORTFOLIO": 'stock_trades_20250422.csv',
    # "PORTFOLIO": 'portfolio_d_20250417.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": "QQQ_d_20250404.csv",
    # "PORTFOLIO": "TLT_d_20250404.csv",
    # "PORTFOLIO": 'HOURLY Crypto.csv',
    # "PORTFOLIO": 'BTC_MSTR_TLT_d_20250404.csv',
    # "PORTFOLIO": 'MSTR_d_20250415.csv',
    # "PORTFOLIO": 'NVDA_d_20250410.csv',
    # "PORTFOLIO": 'NFLX_d_20250410.csv',
    # "PORTFOLIO": 'COIN_d_20250414.csv',
    # "PORTFOLIO": 'MSTY_h.csv',
    # "PORTFOLIO": 'ORLY_d_20250410.csv',
    # "PORTFOLIO": 'STRK_h_20250415.csv',
    # "PORTFOLIO": 'BTC_MSTR_d_20250409.csv',
    # "PORTFOLIO": 'SPY_QQQ_20250327.csv',
    "REFRESH": True,
    "USE_CURRENT": False,
    "USE_HOURLY": False,
    "BASE_DIR": '.',  # Added BASE_DIR for export configuration
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
                sorted_portfolios = sorted(portfolios, key=lambda x: x.get('Score', 0), reverse=True)
                
                # List strategies where Total Open Trades = 1 AND Signal Entry = false (to avoid duplicates)
                open_trades_strategies = [p for p in sorted_portfolios if
                                         (p.get('Total Open Trades') == 1 or
                                          (isinstance(p.get('Total Open Trades'), str) and p.get('Total Open Trades') == '1')) and
                                         str(p.get('Signal Entry', '')).lower() != 'true']
                
                # Sort open trades strategies by Score
                open_trades_strategies = sorted(open_trades_strategies,
                                               key=lambda x: x.get('Score', 0),
                                               reverse=True)
                
                if open_trades_strategies:
                    log("\n=== Open Trades ===")
                    log("Ticker, Strategy Type, Short Window, Long Window, Signal Window, Score")
                    for p in open_trades_strategies:
                        ticker = p.get('Ticker', 'Unknown')
                        strategy_type = p.get('Strategy Type', 'Unknown')
                        short_window = p.get('Short Window', 'N/A')
                        long_window = p.get('Long Window', 'N/A')
                        signal_window = p.get('Signal Window', 'N/A')
                        score = p.get('Score', 0)

                        log(f"{ticker}, {strategy_type}, {short_window}, {long_window}, {signal_window}, {score:.4f}")
                else:
                    log("\n=== No Open Trades found ===")
                
                # List strategies where Signal Entry = true
                signal_entry_strategies = [p for p in sorted_portfolios if str(p.get('Signal Entry', '')).lower() == 'true']
                
                # Count strategies per ticker
                ticker_counts = {}
                for p in open_trades_strategies:
                    ticker = p.get('Ticker', 'Unknown')
                    ticker_counts[ticker] = ticker_counts.get(ticker, 0) + 1
                
                # Add the count to each strategy
                for p in signal_entry_strategies:
                    ticker = p.get('Ticker', 'Unknown')
                    p['open_trade_count'] = ticker_counts.get(ticker, 0)
                
                # Sort signal entry strategies by Score (descending)
                signal_entry_strategies = sorted(signal_entry_strategies, key=lambda x: x.get('Score', 0), reverse=True)
                
                if signal_entry_strategies:
                    log("\n=== Signal Entries ===")
                    log("Ticker, Strategy Type, Short Window, Long Window, Signal Window, Score, Total Open Trades")
                    for p in signal_entry_strategies:
                        ticker = p.get('Ticker', 'Unknown')
                        strategy_type = p.get('Strategy Type', 'Unknown')
                        short_window = p.get('Short Window', 'N/A')
                        long_window = p.get('Long Window', 'N/A')
                        signal_window = p.get('Signal Window', 'N/A')
                        score = p.get('Score', 0)
                        open_trade_count = p.get('open_trade_count', 0)
                        
                        log(f"{ticker}, {strategy_type}, {short_window}, {long_window}, {signal_window}, {score:.4f}, {open_trade_count}")
                else:
                    log("\n=== No Signal Entries found ===")
                
                # Calculate and log breadth metrics
                if sorted_portfolios:
                    log("\n=== Breadth Metrics ===")
                    
                    # Get total number of strategies
                    total_strategies = len(sorted_portfolios)
                    
                    # Count open trades (already calculated in open_trades_strategies)
                    total_open_trades = len(open_trades_strategies)
                    
                    # Count signal entries (already calculated in signal_entry_strategies)
                    total_signal_entries = len(signal_entry_strategies)
                    
                    # Count signal exits
                    signal_exit_strategies = [p for p in sorted_portfolios if str(p.get('Signal Exit', '')).lower() == 'true']
                    total_signal_exits = len(signal_exit_strategies)
                    
                    # Calculate breadth ratio (open trades to total strategies)
                    breadth_ratio = total_open_trades / total_strategies if total_strategies > 0 else 0
                    
                    # Calculate signal entry ratio
                    signal_entry_ratio = total_signal_entries / total_strategies if total_strategies > 0 else 0
                    
                    # Calculate signal exit ratio
                    signal_exit_ratio = total_signal_exits / total_strategies if total_strategies > 0 else 0
                    
                    # Calculate breadth momentum (signal entry ratio / signal exit ratio)
                    breadth_momentum = signal_entry_ratio / signal_exit_ratio if signal_exit_ratio > 0 else float('inf')
                    
                    # Log the metrics
                    log(f"Total Strategies: {total_strategies}")
                    log(f"Total Open Trades: {total_open_trades}")
                    log(f"Total Signal Entries: {total_signal_entries}")
                    log(f"Total Signal Exits: {total_signal_exits}")
                    log(f"Breadth Ratio: {breadth_ratio:.4f} (Open Trades / Total Strategies)")
                    log(f"Signal Entry Ratio: {signal_entry_ratio:.4f} (Signal Entries / Total Strategies)")
                    log(f"Signal Exit Ratio: {signal_exit_ratio:.4f} (Signal Exits / Total Strategies)")
                    log(f"Breadth Momentum: {breadth_momentum:.4f} (Signal Entry Ratio / Signal Exit Ratio)")
            
        return success

if __name__ == "__main__":
    with error_context(
        "Running portfolio update from command line",
        lambda msg, level='info': print(f"[{level.upper()}] {msg}"),
        reraise=False
    ):
        # Create a normalized copy of the default config
        normalized_config = normalize_config(config.copy())
        portfolio_name = normalized_config.get("PORTFOLIO", 'MSTR_d_20250403.csv')
        
        # Resolve portfolio filename with extension if needed
        resolved_portfolio = resolve_portfolio_filename(portfolio_name)
        
        result = run(resolved_portfolio)
        if result:
            print("Execution completed successfully!")
        else:
            sys.exit(1)