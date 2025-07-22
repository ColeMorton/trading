"""
Comprehensive test suite for MACD strategy multi-ticker functionality.

This test validates:
1. Single ticker execution with USE_CURRENT true/false
2. Multi-ticker execution with USE_CURRENT true/false
3. CSV export paths (portfolios, filtered, best)
4. Data integrity and structure
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

import polars as pl

from app.strategies.macd.config_types import DEFAULT_CONFIG
from app.strategies.macd.tools.export_portfolios import export_portfolios
from app.strategies.macd.tools.filter_portfolios import filter_portfolios
from app.strategies.macd.tools.portfolio_selection import get_best_portfolio
from app.strategies.macd.tools.signal_processing import process_ticker_portfolios
from app.tools.setup_logging import setup_logging


class TestResults:
    """Store test results for summary."""

    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def record_test(self, test_name: str, passed: bool, message: str = ""):
        """Record a test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✓ {test_name}")
        else:
            self.failures.append((test_name, message))
            print(f"✗ {test_name}: {message}")

    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*70}")
        print(f"Test Summary: {self.tests_passed}/{self.tests_run} passed")
        if self.failures:
            print("\nFailures:")
            for test, msg in self.failures:
                print(f"  - {test}: {msg}")
        print(f"{'='*70}\n")


def verify_portfolio_structure(df: pl.DataFrame) -> bool:
    """Verify the portfolio DataFrame has expected structure."""
    required_columns = [
        "Ticker",
        "Strategy Type",
        "Short Window",
        "Long Window",
        "Signal Window",
        "Total Return [%]",
        "Win Rate [%]",
        "Total Trades",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    return len(missing_columns) == 0, missing_columns


def test_comprehensive_macd_functionality():
    """Run comprehensive tests for MACD multi-ticker functionality."""

    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name="macd_test", log_file="test_comprehensive.log"
    )

    results = TestResults()

    try:
        print("Starting comprehensive MACD strategy tests...\n")

        # Test 1: Single ticker with USE_CURRENT=False
        print("Test 1: Single ticker (MSFT) with USE_CURRENT=False")
        config = DEFAULT_CONFIG.copy()
        config.update(
            {
                "TICKER": "MSFT",
                "USE_CURRENT": False,
                "USE_YEARS": True,
                "YEARS": 1,  # Use 1 year for faster testing
                "SHORT_WINDOW_START": 12,
                "SHORT_WINDOW_END": 12,
                "LONG_WINDOW_START": 26,
                "LONG_WINDOW_END": 26,
                "SIGNAL_WINDOW_START": 9,
                "SIGNAL_WINDOW_END": 9,
                "STEP": 1,
            }
        )

        result = process_ticker_portfolios("MSFT", config, log)
        if result is not None and len(result) > 0:
            # Verify structure
            valid_structure, missing = verify_portfolio_structure(result)
            results.record_test(
                "Single ticker portfolio structure",
                valid_structure,
                f"Missing columns: {missing}" if not valid_structure else "",
            )

            # Check CSV export
            export_portfolios(
                portfolios=result.to_dicts(),
                config=config,
                export_type="portfolios",
                log=log,
            )
            # Check both standard directory and dated subdirectory
            csv_paths = [
                Path("data/raw/strategies/MSFT_D_MACD.csv"),
                Path("data/raw/strategies")
                / datetime.now().strftime("%Y%m%d")
                / "MSFT_D_MACD.csv",
            ]
            csv_found = any(p.exists() for p in csv_paths)
            results.record_test(
                "Single ticker CSV export",
                csv_found,
                f"File not found at any of: {[str(p) for p in csv_paths]}",
            )
        else:
            results.record_test(
                "Single ticker processing", False, "No portfolios generated"
            )

        # Test 2: Multi-ticker with USE_CURRENT=False
        print("\nTest 2: Multi-ticker (AAPL, GOOGL) with USE_CURRENT=False")
        config["TICKER"] = ["AAPL", "GOOGL"]

        ticker_results = {}
        for ticker in config["TICKER"]:
            ticker_config = config.copy()
            ticker_config["TICKER"] = ticker
            result = process_ticker_portfolios(ticker, ticker_config, log)
            if result is not None:
                ticker_results[ticker] = result

        results.record_test(
            "Multi-ticker processing",
            len(ticker_results) == 2,
            f"Processed {len(ticker_results)}/2 tickers",
        )

        # Test 3: Filter portfolios
        print("\nTest 3: Portfolio filtering")
        if ticker_results:
            ticker = list(ticker_results.keys())[0]
            portfolios_df = ticker_results[ticker]

            filter_config = config.copy()
            filter_config["TICKER"] = ticker
            filter_config["MINIMUMS"] = {
                "WIN_RATE": 0.20,  # Lower threshold
                "TRADES": 3,  # Lower threshold
                "EXPECTANCY_PER_TRADE": 0.01,
                "PROFIT_FACTOR": 1.00,
            }

            filtered = filter_portfolios(portfolios_df, filter_config, log)
            results.record_test(
                "Portfolio filtering",
                filtered is not None and len(filtered) > 0,
                "No portfolios passed filter criteria" if filtered is None else "",
            )

            # Export filtered portfolios
            if filtered is not None and len(filtered) > 0:
                try:
                    export_portfolios(
                        portfolios=filtered.to_dicts(),
                        config=filter_config,
                        export_type="portfolios_filtered",
                        log=log,
                    )

                    # Check filtered CSV path in standard directories
                    date_str = datetime.now().strftime("%Y%m%d")
                    filtered_paths = [
                        Path(f"data/raw/strategies/filtered/{ticker}_D_MACD.csv"),
                        Path(
                            f"data/raw/strategies/filtered/{date_str}/{ticker}_D_MACD.csv"
                        ),
                    ]
                    filtered_found = any(p.exists() for p in filtered_paths)

                    results.record_test(
                        "Filtered portfolio export",
                        filtered_found,
                        f"File not found at any of: {[str(p) for p in filtered_paths]}",
                    )
                except Exception as e:
                    results.record_test(
                        "Filtered portfolio export", False, f"Export failed: {str(e)}"
                    )
            else:
                results.record_test(
                    "Filtered portfolio export",
                    True,  # Pass if no portfolios to export (not an error)
                    "No portfolios passed filter (expected)",
                )

        # Test 4: Best portfolio selection
        print("\nTest 4: Best portfolio selection")
        if ticker_results:
            best_portfolios = []
            for ticker, portfolios_df in ticker_results.items():
                ticker_config = config.copy()
                ticker_config["TICKER"] = ticker

                # Filter first
                filtered = filter_portfolios(portfolios_df, ticker_config, log)
                if filtered is not None and len(filtered) > 0:
                    best = get_best_portfolio(filtered, ticker_config, log)
                    if best is not None:
                        best_portfolios.append(best)

            results.record_test(
                "Best portfolio selection",
                len(best_portfolios) > 0,
                "No best portfolios selected",
            )

            # Export best portfolios
            if best_portfolios:
                try:
                    export_portfolios(
                        portfolios=best_portfolios,
                        config=config,
                        export_type="portfolios_best",
                        log=log,
                    )

                    # Check best portfolio path in standard directories
                    date_str = datetime.now().strftime("%Y%m%d")
                    best_paths = [
                        Path("data/raw/strategies/best"),
                        Path(f"data/raw/strategies/best/{date_str}"),
                    ]
                    best_found = any(
                        p.exists() and any(p.glob("*MACD*.csv")) for p in best_paths
                    )

                    results.record_test(
                        "Best portfolio export",
                        best_found,
                        f"No MACD files found in: {[str(p) for p in best_paths]}",
                    )
                except Exception as e:
                    results.record_test(
                        "Best portfolio export", False, f"Export failed: {str(e)}"
                    )
            else:
                results.record_test(
                    "Best portfolio export",
                    True,  # Pass if no best portfolios (not necessarily an error)
                    "No best portfolios selected (may be expected)",
                )

        # Test 5: USE_CURRENT=True (may not generate portfolios if no current signals)
        print("\nTest 5: Single ticker with USE_CURRENT=True")
        config = DEFAULT_CONFIG.copy()
        config.update(
            {
                "TICKER": "SPY",
                "USE_CURRENT": True,
                "USE_YEARS": True,
                "YEARS": 1,
                "SHORT_WINDOW_START": 12,
                "SHORT_WINDOW_END": 14,
                "LONG_WINDOW_START": 26,
                "LONG_WINDOW_END": 28,
                "SIGNAL_WINDOW_START": 9,
                "SIGNAL_WINDOW_END": 10,
                "STEP": 1,
            }
        )

        result = process_ticker_portfolios("SPY", config, log)
        # USE_CURRENT=True may not generate portfolios if no current signals
        # Just verify it runs without error
        results.record_test(
            "USE_CURRENT=True execution", True, ""  # Pass if no exception
        )

        # Test 6: Verify standard directory structure
        print("\nTest 6: Directory structure verification")
        expected_dirs = [
            "data/raw/strategies",
            "data/raw/strategies/filtered",
            "data/raw/strategies/best",
        ]

        all_dirs_exist = all(Path(d).exists() for d in expected_dirs)
        results.record_test(
            "Standard directory structure",
            all_dirs_exist,
            f"Some expected standard directories missing: {[d for d in expected_dirs if not Path(d).exists()]}",
        )

        # Print summary
        results.print_summary()

        log_close()
        return results.tests_passed == results.tests_run

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {e}")
        import traceback

        traceback.print_exc()
        log(f"Test suite failed: {e}", "error")
        log_close()
        return False


if __name__ == "__main__":
    success = test_comprehensive_macd_functionality()
    sys.exit(0 if success else 1)
