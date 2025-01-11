"""
Strategy Execution Module

This module handles the execution of trading strategies, including portfolio processing,
filtering, and best portfolio selection for both single and multiple tickers.
"""

from typing import List, Optional, Dict, Any
import polars as pl
from app.ma_cross.tools.filter_portfolios import filter_portfolios
from app.ma_cross.tools.export_portfolios import export_portfolios, PortfolioExportError
from app.ma_cross.tools.signal_processing import process_ticker_portfolios
from app.tools.portfolio.selection import get_best_portfolio
from app.ma_cross.config_types import Config

def process_single_ticker(
    ticker: str,
    config: Config,
    log: callable
) -> Optional[Dict[str, Any]]:
    """Process a single ticker through the portfolio analysis pipeline.

    Args:
        ticker (str): The ticker symbol to process
        config (Config): Configuration for the analysis
        log (callable): Logging function

    Returns:
        Optional[Dict[str, Any]]: Best portfolio if found, None otherwise
    """
    # Create a config copy with single ticker
    ticker_config = config.copy()
    # Ensure synthetic tickers use underscore format
    formatted_ticker = ticker.replace('/', '_') if isinstance(ticker, str) else ticker
    ticker_config["TICKER"] = formatted_ticker
    ticker_config["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
    
    # Process portfolios for ticker
    portfolios_df = process_ticker_portfolios(ticker, ticker_config, log)
    if portfolios_df is None:
        return None
        
    # Apply win rate and minimum trades filters
    min_win_rate = ticker_config.get("MIN_WIN_RATE", 0.34)
    min_trades = ticker_config.get("MIN_TRADES", 21)
    
    # Filter by win rate
    if "Win Rate [%]" in portfolios_df.columns:
        portfolios_df = portfolios_df.filter(pl.col("Win Rate [%]").cast(pl.Float64) >= min_win_rate * 100)
        log(f"Filtered portfolios with win rate >= {min_win_rate * 100}%")
        
    # Filter by number of trades
    if "Total Trades" in portfolios_df.columns:
        portfolios_df = portfolios_df.filter(pl.col("Total Trades").cast(pl.Int64) >= min_trades)
        log(f"Filtered portfolios with at least {min_trades} trades")
        
    if len(portfolios_df) == 0:
        log("No portfolios remain after win rate and trade count filtering", "warning")
        return None
        
    try:
        export_portfolios(
            portfolios=portfolios_df.to_dicts(),
            config=ticker_config,
            export_type="portfolios",
            log=log
        )
    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios for {ticker}: {str(e)}", "error")
        return None

    # Filter portfolios for individual ticker
    filtered_portfolios = filter_portfolios(portfolios_df, ticker_config, log)
    if filtered_portfolios is None:
        return None
        
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
        return best_portfolio
    
    return None

def execute_strategy(
    config: Config,
    strategy_type: str,
    log: callable
) -> List[Dict[str, Any]]:
    """Execute a trading strategy (EMA or SMA) for all tickers.

    Args:
        config (Config): Configuration for the analysis
        strategy_type (str): Either 'EMA' or 'SMA'
        log (callable): Logging function

    Returns:
        List[Dict[str, Any]]: List of best portfolios found
    """
    best_portfolios = []
    tickers = [config["TICKER"]] if isinstance(config["TICKER"], str) else config["TICKER"]
    
    for ticker in tickers:
        log(f"Processing {strategy_type} strategy for ticker: {ticker}")
        ticker_config = config.copy()
        # Ensure synthetic tickers use underscore format
        formatted_ticker = ticker.replace('/', '_') if isinstance(ticker, str) else ticker
        ticker_config["TICKER"] = formatted_ticker
        best_portfolio = process_single_ticker(ticker, ticker_config, log)
        if best_portfolio is not None:
            best_portfolios.append(best_portfolio)
            
    return best_portfolios