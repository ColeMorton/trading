"""
Strategy Execution Module

This module handles the execution of trading strategies, including portfolio processing,
filtering, and best portfolio selection for both single and multiple tickers.
"""

from typing import List, Optional, Dict, Any
import polars as pl
from app.ma_cross.tools.filter_portfolios import filter_portfolios
from app.tools.strategy.export_portfolios import export_portfolios, PortfolioExportError
from app.ma_cross.tools.signal_processing import process_ticker_portfolios
from app.tools.strategy.signal_utils import is_signal_current, is_exit_signal_current
from app.tools.portfolio.selection import get_best_portfolio
from app.ma_cross.config_types import Config
from app.tools.get_data import get_data
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.tools.backtest_strategy import backtest_strategy
from app.tools.stats_converter import convert_stats
from app.tools.portfolio.schema_detection import (
    SchemaVersion,
    detect_schema_version,
    normalize_portfolio_data,
    ensure_allocation_sum_100_percent
)

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
            - STRATEGY_TYPE: str (Strategy type, e.g., "SMA" or "EMA")
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
            
        # Get strategy type from config or default to SMA
        strategy_type = config.get("STRATEGY_TYPE", "SMA")
            
        # Calculate MA and signals
        data = calculate_ma_and_signals(
            data,
            config["SHORT_WINDOW"],
            config["LONG_WINDOW"],
            config,
            log,
            strategy_type
        )
        if data is None:
            log(f"Failed to calculate signals for {ticker}", "error")
            return None
            
        # Check if there's a current entry signal
        current_signal = is_signal_current(data, config)
        log(f"Current entry signal for {ticker}: {current_signal}", "info")
        
        # Check if there's a current exit signal
        exit_signal = is_exit_signal_current(data, config)
        log(f"Current exit signal for {ticker}: {exit_signal}", "info")
            
        # Run backtest using app/tools/backtest_strategy.py
        portfolio = backtest_strategy(data, config, log)
        if portfolio is None:
            return None
            
        # Get raw stats from vectorbt
        stats = portfolio.stats()
        
        # Check for invalid metrics before converting stats
        from app.tools.portfolio.filters import check_invalid_metrics
        valid_stats = check_invalid_metrics(stats, log)
        if valid_stats is None:
            log(f"Portfolio for {ticker} with {strategy_type} strategy (short window: {config['SHORT_WINDOW']}, long window: {config['LONG_WINDOW']}) has invalid metrics - skipping", "info")
            return None
        
        # Convert stats using app/tools/stats_converter.py
        # Pass both the current entry and exit signals to convert_stats
        converted_stats = convert_stats(valid_stats, log, config, current_signal, exit_signal)
        
        # Add strategy identification fields
        converted_stats.update({
            "TICKER": ticker,  # Use uppercase TICKER
            "Strategy Type": strategy_type,
            "SMA_FAST": config["SHORT_WINDOW"] if strategy_type == "SMA" else None,
            "SMA_SLOW": config["LONG_WINDOW"] if strategy_type == "SMA" else None,
            "EMA_FAST": config["SHORT_WINDOW"] if strategy_type == "EMA" else None,
            "EMA_SLOW": config["LONG_WINDOW"] if strategy_type == "EMA" else None,
            # Add Allocation [%] and Stop Loss [%] fields if they exist in config
            "Allocation [%]": config.get("ALLOCATION", None),
            "Stop Loss [%]": config.get("STOP_LOSS", None)
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
        
    # Helper function to apply a filter
    def apply_filter(df, column_name, min_value, data_type, multiplier=1, message_prefix=""):
        """Apply a filter to the dataframe based on a minimum value.
        
        Args:
            df: DataFrame to filter
            column_name: Column to filter on
            min_value: Minimum value to filter by
            data_type: Data type to cast the column to
            multiplier: Value to multiply the min_value by (default: 1)
            message_prefix: Prefix for the log message (default: "")
            
        Returns:
            Filtered DataFrame
        """
        if column_name in df.columns:
            adjusted_value = min_value * multiplier
            df = df.filter(pl.col(column_name).cast(data_type) >= adjusted_value)
            
            # Format the message based on the filter type
            if message_prefix:
                if "win rate" in message_prefix.lower():
                    log(f"{message_prefix} >= {adjusted_value}%")
                elif "trades" in message_prefix.lower():
                    log(f"{message_prefix} >= {int(adjusted_value)}")
                else:
                    log(f"{message_prefix} >= {adjusted_value}")
            
            return df
        return df
    
    # Define filter configurations
    filter_configs = [
        # (config_key, column_name, data_type, multiplier, message_prefix)
        ("WIN_RATE", "Win Rate [%]", pl.Float64, 100, "Filtered portfolios with win rate"),
        ("TRADES", "Total Trades", pl.Int64, 1, "Filtered portfolios with at least"),
        ("EXPECTANCY_PER_TRADE", "Expectancy Per Trade", pl.Float64, 1, "Filtered portfolios with expectancy per trade"),
        ("PROFIT_FACTOR", "Profit Factor", pl.Float64, 1, "Filtered portfolios with profit factor"),
        ("SCORE", "Score", pl.Float64, 1, "Filtered portfolios with score"),
        ("SORTINO_RATIO", "Sortino Ratio", pl.Float64, 1, "Filtered portfolios with Sortino ratio"),
        ("BEATS_BNH", "Beats BNH [%]", pl.Float64, 1, "Filtered portfolios with Beats BNH percentage")
    ]
    
    # First, filter out portfolios with invalid metrics
    from app.tools.portfolio.filters import filter_invalid_metrics
    portfolios_df = filter_invalid_metrics(portfolios_df, log)
    
    # Check if any portfolios remain after filtering invalid metrics
    if portfolios_df is None or len(portfolios_df) == 0:
        log("No portfolios remain after filtering invalid metrics", "warning")
        return None
    
    # Then apply filters from the MINIMUMS dictionary
    if "MINIMUMS" in ticker_config:
        minimums = ticker_config["MINIMUMS"]
        
        # Apply each filter from the configuration
        for config_key, column_name, data_type, multiplier, message_prefix in filter_configs:
            if config_key in minimums:
                portfolios_df = apply_filter(
                    portfolios_df,
                    column_name,
                    minimums[config_key],
                    data_type,
                    multiplier,
                    message_prefix
                )
        
    # Check if portfolios_df is None or empty
    if portfolios_df is None or len(portfolios_df) == 0:
        log("No portfolios remain after filtering", "warning")
        return None
        
    try:
        # Convert to dictionaries and normalize schema
        portfolio_dicts = portfolios_df.to_dicts()
        
        # Detect schema version
        schema_version = detect_schema_version(portfolio_dicts)
        log(f"Detected schema version for export: {schema_version.name}", "info")
        
        # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
        normalized_portfolios = normalize_portfolio_data(portfolio_dicts, schema_version, log)
        
        # Ensure allocation values sum to 100% if they exist
        if schema_version == SchemaVersion.EXTENDED:
            normalized_portfolios = ensure_allocation_sum_100_percent(normalized_portfolios, log)
        
        export_portfolios(
            portfolios=normalized_portfolios,
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
        # Convert to dictionaries and normalize schema
        filtered_dicts = filtered_portfolios.to_dicts()
        
        # Detect schema version
        schema_version = detect_schema_version(filtered_dicts)
        log(f"Detected schema version for filtered export: {schema_version.name}", "info")
        
        # Normalize portfolio data to handle Allocation [%] and Stop Loss [%] columns
        normalized_filtered = normalize_portfolio_data(filtered_dicts, schema_version, log)
        
        # Ensure allocation values sum to 100% if they exist
        if schema_version == SchemaVersion.EXTENDED:
            normalized_filtered = ensure_allocation_sum_100_percent(normalized_filtered, log)
        
        export_portfolios(
            portfolios=normalized_filtered,
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
    """Execute a trading strategy for all tickers.

    Args:
        config (Config): Configuration for the analysis
        strategy_type (str): Strategy type (e.g., 'EMA', 'SMA')
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
        
        # Set the strategy type in the config
        ticker_config["STRATEGY_TYPE"] = strategy_type
        
        best_portfolio = process_single_ticker(ticker, ticker_config, log)
        if best_portfolio is not None:
            best_portfolios.append(best_portfolio)
            
    return best_portfolios
