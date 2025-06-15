#!/usr/bin/env python3
"""
Quick test script for MA Cross portfolio analysis with reduced window range.

Tests the analysis with tickers: GLD, CL=F, BTC-USD, SPY, QQQ, DX-Y.NYB
Configuration: USE_CURRENT = False, no minimums, reduced window range for faster execution
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


def validate_exports(base_dir: Path, tickers: list, date_str: str, log) -> dict:
    """Validate that export files were created and return summary."""
    results = {
        "portfolios": {"found": 0, "expected": 0, "files": []},
        "filtered": {"found": 0, "expected": 0, "files": []},
        "best": {"found": 0, "files": []},
    }

    # Expected directories
    portfolios_dir = base_dir / "csv" / "portfolios" / date_str
    filtered_dir = base_dir / "csv" / "portfolios_filtered" / date_str
    best_dir = base_dir / "csv" / "portfolios_best" / date_str

    log("=" * 80)
    log("EXPORT FILES VALIDATION")
    log("=" * 80)

    # Check portfolio files
    log("\nPortfolio files:")
    for ticker in tickers:
        ticker_clean = ticker.replace("=", "_").replace("-", "_")
        for strategy in ["SMA", "EMA"]:
            results["portfolios"]["expected"] += 1
            portfolio_file = portfolios_dir / f"{ticker_clean}_D_{strategy}.csv"
            if portfolio_file.exists():
                results["portfolios"]["found"] += 1
                results["portfolios"]["files"].append(portfolio_file.name)
                log(f"✅ {portfolio_file.name}")
            else:
                log(f"❌ {portfolio_file.name}", "warning")

    # Check filtered files
    log("\nFiltered portfolio files:")
    for ticker in tickers:
        ticker_clean = ticker.replace("=", "_").replace("-", "_")
        for strategy in ["SMA", "EMA"]:
            results["filtered"]["expected"] += 1
            filtered_file = filtered_dir / f"{ticker_clean}_D_{strategy}.csv"
            if filtered_file.exists():
                results["filtered"]["found"] += 1
                results["filtered"]["files"].append(filtered_file.name)
                log(f"✅ {filtered_file.name}")
            else:
                log(f"❌ {filtered_file.name}", "warning")

    # Check best portfolio files
    log("\nBest portfolio files:")
    if best_dir.exists():
        best_files = list(best_dir.glob("*.csv"))
        results["best"]["found"] = len(best_files)
        for bf in best_files:
            results["best"]["files"].append(bf.name)
            log(f"✅ {bf.name}")

            # Show first few lines of best portfolio
            try:
                with open(bf, "r") as f:
                    lines = f.readlines()[:5]
                log(f"\n  Preview of {bf.name}:")
                for line in lines:
                    log(f"  {line.strip()}")
            except Exception as e:
                log(f"  Could not read file: {e}", "warning")
    else:
        log(f"❌ Best portfolio directory missing: {best_dir}", "warning")

    # Summary
    log("\n" + "=" * 80)
    log("VALIDATION SUMMARY:")
    log(
        f"Portfolios: {results['portfolios']['found']}/{results['portfolios']['expected']}"
    )
    log(f"Filtered: {results['filtered']['found']}/{results['filtered']['expected']}")
    log(f"Best: {results['best']['found']} files")
    log("=" * 80)

    return results


def run_quick_test():
    """Run a quick MA Cross test with reduced parameters."""

    # Test configuration with reduced window range for faster execution
    test_config = {
        "TICKER": ["GLD", "CL=F", "BTC-USD", "SPY", "QQQ", "DX-Y.NYB"],
        "WINDOWS": 21,  # Reduced from 89 for faster execution
        "BASE_DIR": get_project_root(),
        "REFRESH": True,
        "STRATEGY_TYPES": ["SMA", "EMA"],
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
        module_name="ma_cross_test", log_file="test_ma_cross_quick.log"
    ) as log:
        log("=" * 80)
        log("MA CROSS QUICK TEST (REDUCED WINDOWS)")
        log("=" * 80)
        log(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log(f"Tickers: {', '.join(test_config['TICKER'])}")
        log(f"Windows: {test_config['WINDOWS']} (reduced for quick test)")
        log(f"USE_CURRENT: {test_config['USE_CURRENT']}")
        log(f"MINIMUMS: {test_config['MINIMUMS']}")
        log("=" * 80 + "\n")

        try:
            # Run the analysis
            orchestrator = PortfolioOrchestrator(log)
            success = orchestrator.run(test_config)

            if success:
                log("\n✅ Analysis completed successfully")

                # Validate exports
                date_str = datetime.now().strftime("%Y%m%d")
                results = validate_exports(
                    Path(test_config["BASE_DIR"]), test_config["TICKER"], date_str, log
                )

                # Check for consistency
                log("\nCONSISTENCY CHECKS:")
                if results["best"]["found"] > 0:
                    log("✅ Best portfolios were generated")

                    # Read and analyze best portfolio
                    best_dir = (
                        Path(test_config["BASE_DIR"])
                        / "csv"
                        / "portfolios_best"
                        / date_str
                    )
                    for bf in best_dir.glob("*.csv"):
                        log(f"\nAnalyzing {bf.name}:")
                        try:
                            import polars as pl

                            df = pl.read_csv(bf)
                            log(f"  Rows: {len(df)}")
                            log(f"  Columns: {df.columns}")

                            # Check for required columns
                            required_cols = [
                                "Ticker",
                                "Strategy",
                                "Total Return [%]",
                                "Win Rate [%]",
                            ]
                            missing = [
                                col for col in required_cols if col not in df.columns
                            ]
                            if missing:
                                log(f"  ⚠️  Missing columns: {missing}", "warning")
                            else:
                                log("  ✅ All required columns present")

                            # Show top performers
                            if len(df) > 0:
                                log("\n  Top 3 performers:")
                                top_df = df.sort(
                                    "Total Return [%]", descending=True
                                ).head(3)
                                for row in top_df.to_dicts():
                                    log(
                                        f"    {row['Ticker']} {row['Strategy']}: {row['Total Return [%]']:.2f}%"
                                    )

                        except Exception as e:
                            log(f"  Error reading best portfolio: {e}", "error")
                else:
                    log("❌ No best portfolios generated", "warning")

            else:
                log("\n❌ Analysis failed", "error")

        except Exception as e:
            log(f"\n❌ Test error: {str(e)}", "error")
            import traceback

            log(traceback.format_exc(), "error")
            return False

        log(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log("=" * 80)

        # Display instructions
        log_file = (
            Path(test_config["BASE_DIR"])
            / "logs"
            / "ma_cross_test"
            / "test_ma_cross_quick.log"
        )
        print(f"\n📄 Log: {log_file}")
        print(f"\n🔍 Review commands:")
        print(f"  cat {log_file} | grep -E '(✅|❌|WARNING|ERROR)'")
        print(f"  ls -la csv/portfolios_best/{date_str}/")

        return success


if __name__ == "__main__":
    success = run_quick_test()
    sys.exit(0 if success else 1)
