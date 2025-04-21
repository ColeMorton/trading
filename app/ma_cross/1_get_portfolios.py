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
from app.tools.portfolio.collection import export_best_portfolios

CONFIG: Config = {
    # "TICKER": [
    #     "SPY",
    #     "QQQ"
    # ],
    # "TICKER": [
    #     "SPY",
    #     "QQQ",
    #     "BTC-USD",
    #     "SOL-USD",
    #     "MSTY",
    #     "STRK",
    #     "CRWD",
    #     "LYV",
    #     "ALL",
    #     "ATO"
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
    #     "MKR-USD",
    #     "PENDLE-USD"
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
    #     "LYV",
    #     "CRWD"
    # ],
    "TICKER": 'VRSK',
    # "TICKER_2": 'SPY',
    # "WINDOWS": 120,
    "WINDOWS": 89,
    # "WINDOWS": 55,
    # "WINDOWS": 34,
    # "SCANNER_LIST": 'DAILY.csv',
    # "USE_SCANNER": True,
    "BASE_DIR": ".",
    "REFRESH": True,
    "STRATEGY_TYPES": [ "SMA", "EMA" ],
    "DIRECTION": "Long",
    "USE_HOURLY": False,
    "USE_YEARS": False,
    "YEARS": 15,
    "USE_SYNTHETIC": False,
    "USE_CURRENT": True,
    "MINIMUMS": {
        # "TRADES": 13,
        # "TRADES": 21,
        "WIN_RATE": 0.38,
        "TRADES": 34,
        # "WIN_RATE": 0.50,
        # "TRADES": 54,
        # "WIN_RATE": 0.61,
        "EXPECTANCY_PER_TRADE": 1,
        "PROFIT_FACTOR": 1,
        "SORTINO_RATIO": 0.4,
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

        # Get strategy types from config
        strategy_types = config.get("STRATEGY_TYPES", [])
        if not strategy_types:
            log("No strategy types specified in config, defaulting to SMA")
            strategy_types = ["SMA"]
        log(f"Using strategy types: {strategy_types}")
        
        all_portfolios = []
        
        # Execute each strategy in sequence
        for strategy_type in strategy_types:
            log(f"Executing {strategy_type} strategy...")
            
            # Execute strategy and collect best portfolios
            portfolios = execute_strategy(synthetic_config, strategy_type, log)
            if portfolios:
                all_portfolios.extend(portfolios)
        
        # Use all_portfolios instead of best_portfolios
        best_portfolios = all_portfolios
        
        # Export best portfolios
        if best_portfolios:
            # Filter portfolios to only include those with Signal Entry = True when USE_CURRENT = True
            if config.get("USE_CURRENT", False):
                original_count = len(best_portfolios)
                best_portfolios = [p for p in best_portfolios if p.get("Signal Entry", False) is True]
                filtered_count = original_count - len(best_portfolios)
                if filtered_count > 0:
                    log(f"Filtered out {filtered_count} portfolios with Signal Entry = False when USE_CURRENT = True", "info")
                    log(f"Remaining portfolios: {len(best_portfolios)}", "info")
            
            export_best_portfolios(best_portfolios, config, log)
        
        log_close()
        return True
            
    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise

def run_strategies() -> bool:
    """Run analysis with strategies specified in STRATEGY_TYPES in sequence.
    
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

        # Get strategy types from config
        strategy_types = base_config.get("STRATEGY_TYPES", [])
        if not strategy_types:
            log("No strategy types specified in config, defaulting to SMA")
            strategy_types = ["SMA"]
        log(f"Running strategies in sequence: {' -> '.join(strategy_types)}")
        
        all_portfolios = []
        strategy_portfolios = {}
        
        # Run each strategy type in the specified sequence
        for strategy_type in strategy_types:
            log(f"Running {strategy_type} strategy analysis...")
            strategy_config = {**base_config}
            
            # Set the strategy type in the config
            strategy_config["STRATEGY_TYPE"] = strategy_type
            
            # Execute strategy
            portfolios = execute_strategy(strategy_config, strategy_type, log)
            strategy_portfolios[strategy_type] = portfolios
            
            # Log portfolio count
            log(f"{strategy_type} portfolios: {len(portfolios) if portfolios else 0}", "info")
            
            # Add to all portfolios
            if portfolios:
                all_portfolios.extend(portfolios)
        
        # Check if filtering criteria might be too strict
        if not all_portfolios:
            log("No portfolios returned from any strategy. Filtering criteria might be too strict.", "warning")
            log(f"Current MINIMUMS: {base_config.get('MINIMUMS', {})}", "info")
            log("Consider relaxing the filtering criteria, especially TRADES and WIN_RATE.", "info")
        
        # Ensure all portfolios have strategy type information
        if all_portfolios:
            for portfolio in all_portfolios:
                if "Strategy Type" not in portfolio:
                    # Use the first strategy type as default if available
                    portfolio["Strategy Type"] = strategy_types[0] if strategy_types else "SMA"
            
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
            
            # Filter portfolios to only include those with Signal Entry = True when USE_CURRENT = True
            if config_copy.get("USE_CURRENT", False):
                original_count = len(all_portfolios)
                all_portfolios = [p for p in all_portfolios if p.get("Signal Entry", False) is True]
                filtered_count = original_count - len(all_portfolios)
                if filtered_count > 0:
                    log(f"Filtered out {filtered_count} portfolios with Signal Entry = False when USE_CURRENT = True", "info")
                    log(f"Remaining portfolios: {len(all_portfolios)}", "info")
            
            export_best_portfolios(all_portfolios, config_copy, log)
        
        log_close()
        return True
        
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_strategies()
