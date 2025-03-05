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
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.backtest_strategy import backtest_strategy
from app.tools.stats_converter import convert_stats

def execute_single_strategy(
    ticker: str,
    config: Config,
    log: callable
) -> Optional[Dict]:
    """Execute a single strategy with specified parameters.
    
    This function tests a specific MA strategy (SMA or EMA) with exact window
    parameters, using the same workflow as execute_strategy but without
    parameter searching or filtering.
    
    Args:
        ticker: The ticker symbol
        config: Configuration containing:
            - USE_SMA: bool (True for SMA, False for EMA)
            - SHORT_WINDOW: int (Fast MA period)
            - LONG_WINDOW: int (Slow MA period)
            - Other standard config parameters
        log: Logging function
        
    Returns:
        Optional[Dict]: Strategy performance metrics if successful, None otherwise
    """
    try:
        # Get price data
        data_result = get_data(ticker, config, log)
        if isinstance(data_result, tuple):
            data, synthetic_ticker = data_result
            config["TICKER"] = synthetic_ticker  # Update config with synthetic ticker
        else:
            data = data_result
            
        if data is None:
            log(f"Failed to get price data for {ticker}", "error")
            return None
            
        # Calculate MA and signals
        data = calculate_ma_and_signals(
            data,
            config["SHORT_WINDOW"],
            config["LONG_WINDOW"],
            config,
            log
        )
        if data is None:
            log(f"Failed to calculate signals for {ticker}", "error")
            return None
            
        # Run backtest using app/ma_cross/tools/backtest_strategy.py
        portfolio = backtest_strategy(data, config, log)
        if portfolio is None:
            return None
            
        # Get raw stats from vectorbt
        stats = portfolio.stats()
        
        # Convert stats using app/tools/stats_converter.py
        converted_stats = convert_stats(stats, log, config)
        
        # Add strategy identification fields
        converted_stats.update({
            "TICKER": ticker,  # Use uppercase TICKER
            "Use SMA": config.get("USE_SMA", False),
            "SMA_FAST": config["SHORT_WINDOW"] if config.get("USE_SMA", False) else None,
            "SMA_SLOW": config["LONG_WINDOW"] if config.get("USE_SMA", False) else None,
            "EMA_FAST": config["SHORT_WINDOW"] if not config.get("USE_SMA", False) else None,
            "EMA_SLOW": config["LONG_WINDOW"] if not config.get("USE_SMA", False) else None
        })
        
        return converted_stats
            
    except Exception as e:
        log(f"Failed to execute strategy: {str(e)}", "error")
        return None

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
        
    # Apply win rate and minimum trades filters only if explicitly configured
    if "MIN_WIN_RATE" in ticker_config and "Win Rate [%]" in portfolios_df.columns:
        min_win_rate = ticker_config["MIN_WIN_RATE"]
        portfolios_df = portfolios_df.filter(pl.col("Win Rate [%]").cast(pl.Float64) >= min_win_rate * 100)
        log(f"Filtered portfolios with win rate >= {min_win_rate * 100}%")
        
    if "MIN_TRADES" in ticker_config and "Total Trades" in portfolios_df.columns:
        min_trades = ticker_config["MIN_TRADES"]
        portfolios_df = portfolios_df.filter(pl.col("Total Trades").cast(pl.Int64) >= min_trades)
        log(f"Filtered portfolios with at least {min_trades} trades")
        
    if len(portfolios_df) == 0:
        log("No portfolios remain after filtering", "warning")
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
        
        # Handle synthetic tickers
        if config.get("USE_SYNTHETIC", False) and isinstance(ticker, str) and "_" in ticker:
            # Extract original tickers from synthetic ticker name
            ticker_parts = ticker.split("_")
            if len(ticker_parts) >= 2:
                # Store original ticker parts for later use
                ticker_config["TICKER_1"] = ticker_parts[0]
                if "TICKER_2" not in ticker_config:
                    ticker_config["TICKER_2"] = ticker_parts[1]
                log(f"Extracted ticker components: {ticker_config['TICKER_1']} and {ticker_config['TICKER_2']}")
        
        # Ensure synthetic tickers use underscore format
        formatted_ticker = ticker.replace('/', '_') if isinstance(ticker, str) else ticker
        ticker_config["TICKER"] = formatted_ticker
        
        best_portfolio = process_single_ticker(ticker, ticker_config, log)
        if best_portfolio is not None:
            best_portfolios.append(best_portfolio)
            
    return best_portfolios