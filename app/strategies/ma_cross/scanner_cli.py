"""
Scanner CLI Module

This module provides the command-line interface for the MA Cross scanner,
maintaining backwards compatibility while using the new core functionality.
"""

import sys
from typing import Any, Dict

from app.strategies.ma_cross.scanner_adapter import ScannerAdapter
from app.tools.config_service import ConfigService
from app.tools.setup_logging import setup_logging

# Default Configuration (for backwards compatibility)
DEFAULT_CONFIG: Dict[str, Any] = {
    "PORTFOLIO": "DAILY.csv",
    "USE_HOURLY": False,
    "REFRESH": True,
    "DIRECTION": "Long",
}


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate configuration settings.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    if not config.get("PORTFOLIO"):
        raise ValueError("PORTFOLIO must be specified")
    if config.get("DIRECTION") not in [None, "Long", "Short"]:
        raise ValueError("DIRECTION must be either 'Long' or 'Short'")


def process_scanner(config: Dict[str, Any]) -> bool:
    """
    Process scanner using the new adapter architecture.

    Args:
        config: Configuration dictionary

    Returns:
        bool: True if successful
    """
    log, log_close, _, _ = setup_logging("ma_cross", "scanner_cli.log")

    try:
        # Validate configuration
        validate_config(config)

        # Use scanner adapter
        adapter = ScannerAdapter(log)
        portfolio_path = f"./csv/strategies/{config['PORTFOLIO']}"

        log(f"Processing portfolio: {config['PORTFOLIO']}")

        # Process portfolio
        result = adapter.process_portfolio_file(portfolio_path, config)

        # Log results
        total_tickers = len(result.tickers)
        signals_found = result.signal_count

        log(f"Processed {total_tickers} tickers, found {signals_found} signals")

        # Export results if signals found
        if signals_found > 0:
            from app.strategies.ma_cross.tools.scanner_processing import export_results

            # Convert to format expected by export_results
            results_data = []
            for ticker_result in result.tickers:
                if ticker_result.has_current_signal:
                    for signal in ticker_result.current_signals:
                        result_dict = {
                            "TICKER": ticker_result.ticker,
                            "SMA": signal.ma_type == "SMA",
                            "EMA": signal.ma_type == "EMA",
                            "SMA_FAST": (
                                signal.short_window if signal.ma_type == "SMA" else None
                            ),
                            "SMA_SLOW": (
                                signal.long_window if signal.ma_type == "SMA" else None
                            ),
                            "EMA_FAST": (
                                signal.short_window if signal.ma_type == "EMA" else None
                            ),
                            "EMA_SLOW": (
                                signal.long_window if signal.ma_type == "EMA" else None
                            ),
                        }
                        results_data.append(result_dict)

            # Load original scanner DataFrame for export
            import polars as pl

            scanner_df = pl.read_csv(portfolio_path)

            export_results(results_data, scanner_df, config, log)

        adapter.close()
        log_close()
        return True

    except Exception as e:
        log(f"Error processing scanner: {str(e)}", "error")
        log_close()
        raise


def main():
    """Main entry point for CLI execution."""
    try:
        # Load configuration
        config = ConfigService.process_config(DEFAULT_CONFIG)
        config["USE_SCANNER"] = True

        # Process scanner
        if process_scanner(config):
            print("Execution completed successfully!")
            sys.exit(0)
        else:
            print("Execution failed!")
            sys.exit(1)

    except ValueError as ve:
        print(f"Configuration error: {str(ve)}")
        sys.exit(1)
    except FileNotFoundError as fe:
        print(f"File error: {str(fe)}")
        sys.exit(1)
    except Exception as e:
        print(f"Execution failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
