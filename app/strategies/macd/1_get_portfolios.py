"""
Portfolio Analysis Module for MACD Cross Strategy

This module handles portfolio analysis for the MACD cross strategy, supporting both
single ticker and multiple ticker analysis. The strategy identifies MACD crossovers where:

Long:
- Entry when MACD line crosses above Signal line
- Exit when MACD line crosses below Signal line

Short:
- Entry when MACD line crosses below Signal line
- Exit when MACD line crosses above Signal line

It includes functionality for parameter sensitivity analysis and portfolio filtering.
"""

import sys
from pathlib import Path

# Add the project root to Python path when running directly
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.macd.config_types import DEFAULT_CONFIG, PortfolioConfig
from app.strategies.macd.tools.export_portfolios import (
    PortfolioExportError,
    export_portfolios,
)
from app.strategies.macd.tools.filter_portfolios import filter_portfolios
from app.strategies.macd.tools.signal_processing import process_ticker_portfolios
from app.tools.get_config import get_config
from app.tools.setup_logging import setup_logging

# Use centralized error handling
from app.tools.strategy.error_handling import (
    ErrorSeverity,
    StrategyErrorCode,
    create_error_handler,
    handle_strategy_error,
)


def run(config: PortfolioConfig = DEFAULT_CONFIG) -> bool:
    """Run portfolio analysis for single or multiple tickers using the MACD cross strategy.

    This function handles the main workflow of portfolio analysis:
    1. Processes each ticker (single or multiple)
    2. Performs parameter sensitivity analysis on MACD parameters
    3. Filters portfolios based on criteria
    4. Selects best portfolio from filtered portfolios
    5. Displays and saves results

    The workflow ensures that portfolios that excel in multiple metrics
    (as identified in the filtering step) are properly considered for
    best portfolio selection.

    Args:
        config (PortfolioConfig): Configuration dictionary containing analysis parameters

    Returns:
        bool: True if execution successful

    Raises:
        Exception: If portfolio analysis fails
    """
    log, log_close, _, _ = setup_logging(
        module_name="macd", log_file="1_get_portfolios.log"
    )

    try:
        # Initialize configuration and tickers
        config = get_config(config)
        tickers = (
            [config["TICKER"]]
            if isinstance(config["TICKER"], str)
            else config["TICKER"]
        )
        # Process each ticker
        all_portfolios = []  # Collect all portfolios for best portfolios export
        best_portfolios = []  # Collect best portfolios from each ticker

        for ticker in tickers:
            log(f"Processing ticker: {ticker}")
            # Create a config copy with single ticker
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker

            # Process portfolios for ticker
            result = process_ticker_portfolios(ticker, ticker_config, log)
            if result is None:
                continue

            # Set portfolios_df from result
            portfolios_df = result

            # Export unfiltered portfolios
            try:
                export_portfolios(
                    portfolios=portfolios_df.to_dicts(),
                    config=ticker_config,
                    export_type="portfolios",
                    log=log,
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
                        log=log,
                    )

                    # Always select best portfolio from filtered portfolios
                    from app.strategies.macd.tools.portfolio_selection import (
                        get_best_portfolio,
                    )

                    best_portfolio = get_best_portfolio(
                        filtered_portfolios, ticker_config, log
                    )
                    if best_portfolio is not None:
                        log(
                            f"Found best portfolio for {ticker} from filtered portfolios"
                        )
                        best_portfolios.append(best_portfolio)
                except (ValueError, PortfolioExportError) as e:
                    log(
                        f"Failed to export filtered portfolios for {ticker}: {str(e)}",
                        "error",
                    )

            # Add portfolios to all_portfolios for best portfolios export
            all_portfolios.extend(portfolios_df.to_dicts())

        # We no longer export all portfolios to portfolios_best
        # This avoids duplicate exports to the same directory
        if all_portfolios:
            log(f"Collected {len(all_portfolios)} portfolios across all tickers")

        # Export best portfolio from each ticker
        if best_portfolios:
            log(
                f"Exporting {len(best_portfolios)} best portfolios (one from each ticker)"
            )
            try:
                # Export to portfolios_best directory only
                export_portfolios(
                    portfolios=best_portfolios,
                    config=config,
                    export_type="portfolios_best",
                    log=log,
                )
            except (ValueError, PortfolioExportError) as e:
                log(f"Failed to export best portfolios collection: {str(e)}", "error")

        log_close()
        return True

    except Exception as e:
        log(f"Execution failed: {str(e)}", "error")
        log_close()
        raise


def run_strategies() -> bool:
    """Run analysis with strategies specified in configuration.

    This function is similar to the run function in ma_cross/1_get_portfolios.py,
    providing a consistent interface across strategy modules.

    Returns:
        bool: True if execution successful
    """
    try:
        # Initialize logging
        log, log_close, _, _ = setup_logging(
            module_name="macd", log_file="1_get_portfolios.log"
        )

        # Initialize config
        config_copy = DEFAULT_CONFIG.copy()

        # Use the direction from the configuration
        direction = config_copy.get("DIRECTION", "Long")
        log(f"Running {direction} MACD strategy as specified in configuration", "info")

        # Run the main analysis function
        result = run(config_copy)

        log_close()
        return result

    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    try:
        # Run analysis with the direction specified in the configuration
        run_strategies()
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        raise
