#!/usr/bin/env python3
"""
Test script for MA Cross portfolio analysis with specific parameters.

Tests the analysis with tickers: GLD, CL=F, BTC-USD, SPY, QQQ, DX-Y.NYB
Configuration: USE_CURRENT = False, no minimums
Validates all exports are created successfully.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.strategies.ma_cross.tools.strategy_execution import execute_strategy
from app.tools.logging_context import logging_context
from app.tools.orchestration import PortfolioOrchestrator
from app.tools.project_utils import get_project_root


def validate_exports(base_dir: Path, tickers: list, date_str: str, log) -> bool:
    """Validate that all expected export files were created."""
    success = True

    # Expected directories
    portfolios_dir = base_dir / "csv" / "portfolios" / date_str
    filtered_dir = base_dir / "csv" / "portfolios_filtered" / date_str
    best_dir = base_dir / "csv" / "portfolios_best" / date_str

    log("=" * 80)
    log("VALIDATING EXPORT FILES")
    log("=" * 80)

    # Check portfolio files for each ticker
    log("\nChecking portfolio files:")
    for ticker in tickers:
        # Replace special characters in ticker names for filenames
        ticker_clean = ticker.replace("=", "_").replace("-", "_")

        # Check for both SMA and EMA files
        for strategy in ["SMA", "EMA"]:
            portfolio_file = portfolios_dir / f"{ticker_clean}_D_{strategy}.csv"
            if portfolio_file.exists():
                log(f"✅ Found: {portfolio_file.name}")
            else:
                log(f"❌ Missing: {portfolio_file.name}", "warning")
                success = False

    # Check filtered portfolio files
    log("\nChecking filtered portfolio files:")
    for ticker in tickers:
        ticker_clean = ticker.replace("=", "_").replace("-", "_")

        for strategy in ["SMA", "EMA"]:
            filtered_file = filtered_dir / f"{ticker_clean}_D_{strategy}.csv"
            if filtered_file.exists():
                log(f"✅ Found: {filtered_file.name}")
            else:
                log(f"❌ Missing: {filtered_file.name}", "warning")
                success = False

    # Check best portfolio files
    log("\nChecking best portfolio files:")
    if best_dir.exists():
        best_files = list(best_dir.glob("*.csv"))
        if best_files:
            log(f"✅ Found {len(best_files)} best portfolio file(s):")
            for bf in best_files:
                log(f"   - {bf.name}")
        else:
            log("❌ No best portfolio files found", "warning")
            success = False
    else:
        log(f"❌ Best portfolio directory does not exist: {best_dir}", "warning")
        success = False

    log("\n" + "=" * 80)
    log(f"Export validation: {'PASSED' if success else 'FAILED'}")
    log("=" * 80 + "\n")

    return success


def run_test():
    """Run the MA Cross test with specified parameters."""

    # Test configuration
    test_config = {
        "TICKER": ["GLD", "CL=F", "BTC-USD", "SPY", "QQQ", "DX-Y.NYB"],
        "WINDOWS": 89,
        "BASE_DIR": get_project_root(),
        "REFRESH": True,
        "STRATEGY_TYPES": ["SMA", "EMA"],  # Test both strategies
        "DIRECTION": "Long",
        "USE_HOURLY": False,
        "USE_YEARS": False,
        "YEARS": 15,
        "USE_SYNTHETIC": False,
        "USE_CURRENT": False,  # As specified
        "MINIMUMS": {},  # No minimums as specified
        "SORT_BY": "Total Return [%]",
        "SORT_ASC": False,
        "USE_GBM": False,
        "USE_MA": True,
        "DISPLAY_RESULTS": True,
    }

    with logging_context(
        module_name="ma_cross_test", log_file="test_ma_cross_analysis.log"
    ) as log:
        log("=" * 80)
        log("MA CROSS PORTFOLIO ANALYSIS TEST")
        log("=" * 80)
        log(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"Tickers: {', '.join(test_config['TICKER'])}")
        log(f"USE_CURRENT: {test_config['USE_CURRENT']}")
        log(f"MINIMUMS: {test_config['MINIMUMS']} (empty = no minimums)")
        log(f"STRATEGY_TYPES: {', '.join(test_config['STRATEGY_TYPES'])}")
        log("=" * 80 + "\n")

        try:
            # Use PortfolioOrchestrator to run the analysis
            orchestrator = PortfolioOrchestrator(log)
            success = orchestrator.run(test_config)

            if success:
                log("\n✅ Portfolio analysis completed successfully")

                # Get current date for validation
                date_str = datetime.now().strftime("%Y%m%d")

                # Validate exports
                export_success = validate_exports(
                    Path(test_config["BASE_DIR"]), test_config["TICKER"], date_str, log
                )

                if export_success:
                    log("\n🎉 All validations passed!")
                else:
                    log("\n⚠️  Some export files are missing", "warning")

            else:
                log("\n❌ Portfolio analysis failed", "error")

        except Exception as e:
            log(f"\n❌ Test failed with error: {str(e)}", "error")
            import traceback

            log(traceback.format_exc(), "error")
            return False

        log(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("=" * 80)

        # Display log file location
        log_file_path = (
            Path(test_config["BASE_DIR"])
            / "logs"
            / "ma_cross_test"
            / "test_ma_cross_analysis.log"
        )
        print(f"\n📄 Full log output saved to: {log_file_path}")
        print("\nTo review the log output:")
        print(f"  cat {log_file_path}")
        print(f"\nTo see the most recent best portfolio:")
        print(
            f"  ls -la {Path(test_config['BASE_DIR']) / 'csv' / 'portfolios_best' / date_str}/"
        )

        return success


if __name__ == "__main__":
    success = run_test()
    sys.exit(0 if success else 1)
