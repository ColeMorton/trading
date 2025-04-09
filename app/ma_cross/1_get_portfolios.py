"""
Portfolio Analysis Module for EMA Cross Strategy

This module handles portfolio analysis for the EMA and SMA cross strategies, supporting both
single ticker and multiple ticker analysis. It includes functionality for parameter
sensitivity analysis and portfolio filtering.
"""

import os
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging
from app.tools.strategy.types import StrategyConfig as Config
from app.ma_cross.tools.strategy_execution import execute_strategy
from app.tools.portfolio.collection import export_best_portfolios, combine_strategy_portfolios

CONFIG: Config = {
    # "TICKER": [
    #     "SPY",
    #     "QQQ"
    # ],
    # "TICKER": [
    #     "SPY",
    #     "QQQ",
    #     "BTC-USD",
    #     "MSTR",
    #     "MSTY",
    #     "STRK"
    # ],
    # "TICKER": [
    #     "SOL-USD",
    #     "BNB-USD",
    #     "TRX-USD",
    #     "RUNE-USD",
    #     "XMR-USD",
    #     "LTC-USD",
    #     "HBAR-USD",
    #     "DOGE-USD",
    #     "ETH-USD",
    #     "NEAR-USD",
    #     "FET-USD",
    #     "AVAX-USD",
    #     "LINK-USD",
    #     "AAVE-USD",
    #     "MKR-USD",
    #     "COMP-USD",
    #     "EOS-USD",
    #     "XRP-USD",
    #     "DASH-USD",
    #     "XLM-USD",
    #     "ETC-USD",
    #     "XNO-USD",
    #     "BCH-USD",
    #     "ALGO-USD",
    #     "SHIB-USD",
    #     "DOT-USD",
    #     "UNI-USD",
    #     "1INCH-USD",
    #     "ATOM-USD",
    #     "SUSHI-USD",
    #     "ADA-USD",
    #     "INJ-USD",
    #     "VET-USD",
    #     "PENDLE-USD",
    #     "ZEC-USD"
    # ],
    # "TICKER": [
    #     "TRX-USD",
    #     "MKR-USD"
    # ],
    # "TICKER": [
    #     "XLK",
    #     "XLC",
    #     "XLU",
    #     "XLE",
    #     "XLF",
    #     "XLY",
    #     "XLV",
    #     "XLRE",
    #     "XLI",
    #     "XLP",
    #     "XLB"
    # ],
    # "TICKER": [
    #     "TLT",
    #     "EDV"
    # ],
    "TICKER": 'MSTR',
    # "TICKER_2": 'MSTR',
    # "WINDOWS": 120,
    "WINDOWS": 89,
    # "WINDOWS": 55,
    # "SCANNER_LIST": 'DAILY.csv',
    # "USE_SCANNER": True,
    "BASE_DIR": ".",
    "REFRESH": False,
    "USE_SMA": False,
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": True,
    "MINIMUMS": {
        # "WIN_RATE": 0.38,
        # "TRADES": 34,
        # "WIN_RATE": 0.50,
        # "TRADES": 54,
        # "WIN_RATE": 0.61,
        # "EXPECTANCY_PER_TRADE": 1,
        # "PROFIT_FACTOR": 1,
        # "SORTINO_RATIO": 0.4,
        # "BEATS_BNH": 0.13
    },
    "SORT_BY": "Score",
    "SORT_ASC": False,
    "USE_GBM": False
}

def run(config: Config = CONFIG) -> bool:
    """Run portfolio analysis for single or multiple tickers.
    
    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis
    3. Filters portfolios based on criteria
    4. Displays and saves results
    
    Args:
        config (Config): Configuration dictionary containing analysis parameters
        
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
        # Initialize configuration
        config = get_config(config)
        
        # Ensure BASE_DIR is absolute
        if not os.path.isabs(config["BASE_DIR"]):
            config["BASE_DIR"] = os.path.abspath(config["BASE_DIR"])
        
        # Handle synthetic pair if enabled
        if config.get("USE_SYNTHETIC"):
            if isinstance(config["TICKER"], list):
                # Process multiple synthetic tickers
                synthetic_tickers = [f"{ticker}_{config['TICKER_2']}" for ticker in config["TICKER"]]
                log(f"Processing strategies for synthetic pairs: {synthetic_tickers}")
                synthetic_config = {**config}
                synthetic_config["TICKER"] = synthetic_tickers  # Set synthetic tickers for file naming
            elif isinstance(config["TICKER"], str):
                # Process single synthetic ticker
                synthetic_ticker = f"{config['TICKER']}_{config['TICKER_2']}"
                log(f"Processing strategy for synthetic pair: {synthetic_ticker}")
                synthetic_config = {**config}
                synthetic_config["TICKER"] = synthetic_ticker  # Set synthetic ticker for file naming
            else:
                raise ValueError("TICKER must be a string or a list when USE_SYNTHETIC is True")
        else:
            log(f"Processing strategy for ticker: {config['TICKER']}")
            synthetic_config = config

        # Execute strategy and collect best portfolios
        best_portfolios = execute_strategy(synthetic_config, "EMA" if not config.get("USE_SMA") else "SMA", log)
        
        # Export best portfolios
        if best_portfolios:
            export_best_portfolios(best_portfolios, config, log)
        
        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

def run_both_strategies() -> bool:
    """Run analysis with both EMA and SMA strategies.
    
    Returns:
        bool: True if execution successful
    """
    try:
        # Initialize logging
        log, log_close, _, _ = setup_logging(
            module_name='ma_cross',
            log_file='1_get_portfolios.log'
        )
        
        # Initialize config
        config_copy = CONFIG.copy()
        config_copy["USE_MA"] = True  # Ensure USE_MA is set for proper filename suffix
        
        # Handle synthetic pair if enabled
        if config_copy.get("USE_SYNTHETIC"):
            if isinstance(config_copy["TICKER"], list):
                # Process multiple synthetic tickers
                original_tickers = config_copy["TICKER"].copy()  # Save original tickers
                synthetic_tickers = []
                
                for ticker in original_tickers:
                    # Create synthetic ticker name
                    synthetic_ticker = f"{ticker}_{config_copy['TICKER_2']}"
                    synthetic_tickers.append(synthetic_ticker)
                
                log(f"Processing strategies for synthetic pairs: {synthetic_tickers}")
                base_config = {**config_copy}
                base_config["TICKER"] = synthetic_tickers  # Set synthetic tickers for file naming
                
                # Store original tickers for reference
                base_config["ORIGINAL_TICKERS"] = original_tickers
            elif isinstance(config_copy["TICKER"], str):
                # Process single synthetic ticker
                original_ticker = config_copy["TICKER"]  # Save original ticker
                synthetic_ticker = f"{original_ticker}_{config_copy['TICKER_2']}"
                log(f"Processing strategies for synthetic pair: {synthetic_ticker}")
                base_config = {**config_copy}
                base_config["TICKER"] = synthetic_ticker  # Set synthetic ticker for file naming
                
                # Store original ticker for reference
                base_config["ORIGINAL_TICKERS"] = [original_ticker]
            else:
                raise ValueError("TICKER must be a string or a list when USE_SYNTHETIC is True")
        else:
            log(f"Processing strategies for ticker: {config_copy['TICKER']}")
            base_config = config_copy

        # Run EMA strategy
        log("Running EMA strategy analysis...")
        ema_config = {**base_config, "USE_SMA": False}
        ema_portfolios = execute_strategy(ema_config, "EMA", log)
        
        # Run SMA strategy
        log("Running SMA strategy analysis...")
        sma_config = {**base_config, "USE_SMA": True}
        sma_portfolios = execute_strategy(sma_config, "SMA", log)
        
        # Check if filtering criteria might be too strict
        if not ema_portfolios and not sma_portfolios:
            log("No portfolios returned from either strategy. Filtering criteria might be too strict.", "warning")
            log(f"Current MINIMUMS: {config_copy.get('MINIMUMS', {})}", "info")
            log("Consider relaxing the filtering criteria, especially TRADES and WIN_RATE.", "info")
        
        # Log portfolio counts
        log(f"EMA portfolios: {len(ema_portfolios) if ema_portfolios else 0}", "info")
        log(f"SMA portfolios: {len(sma_portfolios) if sma_portfolios else 0}", "info")
        
        # Combine and export best portfolios
        all_portfolios = combine_strategy_portfolios(ema_portfolios, sma_portfolios)
        log(f"Combined portfolios: {len(all_portfolios) if all_portfolios else 0}", "info")
            
        # Ensure all portfolios have strategy type information
        if all_portfolios:
            for portfolio in all_portfolios:
                if "Strategy Type" not in portfolio:
                    # Note: USE_SMA is deprecated but check it for legacy support
                    if "USE_SMA" in portfolio:
                        portfolio["Strategy Type"] = "SMA" if portfolio["USE_SMA"] else "EMA"
                    else:
                        portfolio["Strategy Type"] = "EMA"  # Default to EMA
            
            if log:
                log("Ensured all portfolios have Strategy Type information", "info")
                
            # Ensure required configuration fields are present
            if "BASE_DIR" not in config_copy:
                config_copy["BASE_DIR"] = "."
                log("Added missing BASE_DIR to configuration", "warning")
                
            if "TICKER" not in config_copy:
                config_copy["TICKER"] = "Unknown"
                log("Added missing TICKER to configuration", "warning")
        else:
            log("No portfolios to export", "warning")
            return True  # Return success to avoid error
            
        if all_portfolios:
            # Ensure synthetic ticker is properly set for export
            if config_copy.get("USE_SYNTHETIC"):
                if isinstance(config_copy["TICKER"], list):
                    # For list of tickers, no need to modify as each portfolio should have its own ticker
                    if log:
                        log(f"Using list of tickers for export: {config_copy['TICKER']}", "info")
                elif isinstance(config_copy["TICKER"], str):
                    # For single ticker, create synthetic name
                    config_copy["TICKER"] = f"{config_copy['TICKER']}_{config_copy['TICKER_2']}"
                    if log:
                        log(f"Using synthetic ticker for export: {config_copy['TICKER']}", "info")
            export_best_portfolios(all_portfolios, config_copy, log)
        
        log_close()
        return True
        
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_both_strategies()
