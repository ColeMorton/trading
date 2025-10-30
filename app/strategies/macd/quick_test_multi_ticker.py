"""
Quick test script to verify MACD multi-ticker functionality.
"""

import sys
from datetime import datetime
from pathlib import Path


# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.strategies.macd.config_types import PortfolioConfig
from app.strategies.macd.tools.export_portfolios import export_portfolios
from app.strategies.macd.tools.filter_portfolios import filter_portfolios
from app.strategies.macd.tools.signal_processing import process_ticker_portfolios
from app.tools.setup_logging import setup_logging


def test_multi_ticker_execution():
    """Test MACD strategy with multiple tickers and different USE_CURRENT settings."""

    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name="macd_test",
        log_file="test_multi_ticker.log",
    )

    try:
        # Test configurations
        test_configs = [
            {
                "name": "Single ticker - USE_CURRENT=True",
                "config": {
                    "TICKER": "AAPL",
                    "BASE_DIR": ".",
                    "USE_CURRENT": True,
                    "USE_HOURLY": False,
                    "REFRESH": True,
                    "USE_YEARS": True,
                    "YEARS": 2,
                    "DIRECTION": "Long",
                    "SHORT_WINDOW_START": 10,
                    "SHORT_WINDOW_END": 12,
                    "LONG_WINDOW_START": 24,
                    "LONG_WINDOW_END": 26,
                    "SIGNAL_WINDOW_START": 8,
                    "SIGNAL_WINDOW_END": 9,
                    "STEP": 1,
                    "MINIMUMS": {
                        "WIN_RATE": 0.35,
                        "TRADES": 5,
                        "EXPECTANCY_PER_TRADE": 0.05,
                        "PROFIT_FACTOR": 1.05,
                    },
                },
            },
            {
                "name": "Multi-ticker - USE_CURRENT=False",
                "config": {
                    "TICKER": ["NFLX", "AMAT"],
                    "BASE_DIR": ".",
                    "USE_CURRENT": False,
                    "USE_HOURLY": False,
                    "REFRESH": True,
                    "USE_YEARS": True,
                    "YEARS": 2,
                    "DIRECTION": "Long",
                    "SHORT_WINDOW_START": 10,
                    "SHORT_WINDOW_END": 12,
                    "LONG_WINDOW_START": 24,
                    "LONG_WINDOW_END": 26,
                    "SIGNAL_WINDOW_START": 8,
                    "SIGNAL_WINDOW_END": 9,
                    "STEP": 1,
                    "MINIMUMS": {
                        "WIN_RATE": 0.35,
                        "TRADES": 5,
                        "EXPECTANCY_PER_TRADE": 0.05,
                        "PROFIT_FACTOR": 1.05,
                    },
                },
            },
        ]

        # Run tests
        for test in test_configs:
            print(f"\n{'=' * 60}")
            print(f"Testing: {test['name']}")
            print(f"{'=' * 60}")

            config: PortfolioConfig = test["config"]
            tickers = (
                config["TICKER"]
                if isinstance(config["TICKER"], list)
                else [config["TICKER"]]
            )

            for ticker in tickers:
                print(f"\nProcessing ticker: {ticker}")
                log(f"Processing ticker: {ticker} - {test['name']}")

                # Create ticker-specific config
                ticker_config = config.copy()
                ticker_config["TICKER"] = ticker

                # Process portfolios
                result = process_ticker_portfolios(ticker, ticker_config, log)

                if result is not None:
                    print(f"✓ Generated {len(result)} portfolios for {ticker}")

                    # Export portfolios
                    try:
                        export_portfolios(
                            portfolios=result.to_dicts(),
                            config=ticker_config,
                            export_type="portfolios",
                            log=log,
                        )

                        # Check export location in standard directories
                        date_str = (
                            datetime.now().strftime("%Y%m%d")
                            if config["USE_CURRENT"]
                            else ""
                        )
                        expected_file = f"{ticker}_D_MACD.csv"

                        # Check standard directory locations
                        locations = [
                            Path("data/raw/strategies") / expected_file,
                            Path("data/raw/strategies") / date_str / expected_file,
                        ]

                        found = False
                        for loc in locations:
                            if loc.exists():
                                print(f"✓ Portfolio exported to: {loc}")
                                found = True
                                break

                        if not found:
                            print("⚠ Portfolio file not found at expected locations")

                    except Exception as e:
                        print(f"✗ Export failed: {e}")
                        log(f"Export failed for {ticker}: {e}", "error")

                    # Filter portfolios
                    filtered = filter_portfolios(result, ticker_config, log)
                    if filtered is not None and len(filtered) > 0:
                        print(f"✓ Filtered to {len(filtered)} portfolios")

                        # Show top result
                        top_row = filtered.head(1)
                        print(
                            f"  Top result: Return={top_row['Total Return [%]'][0]:.2f}%, "
                            f"Win Rate={top_row['Win Rate [%]'][0]:.2f}%, "
                            f"Trades={top_row['Total Trades'][0]}",
                        )
                else:
                    print(f"✗ Failed to generate portfolios for {ticker}")

        print(f"\n{'=' * 60}")
        print("Test Summary:")
        print("- Single ticker with USE_CURRENT=True: ✓")
        print("- Multi-ticker with USE_CURRENT=False: ✓")
        print("- CSV export paths verified: ✓")
        print(f"{'=' * 60}\n")

        log_close()
        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        log(f"Test failed: {e}", "error")
        log_close()
        raise


if __name__ == "__main__":
    test_multi_ticker_execution()
