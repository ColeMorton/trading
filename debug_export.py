#!/usr/bin/env python3
"""
Debug script to trace Metric Type during export process
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tools.setup_logging import setup_logging


def debug_export():
    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name="debug", log_file="debug_export.log"
    )

    try:
        # Test data simulating what comes from aggregation
        test_portfolio = {
            "Metric Type": "Most Best Trade [%], Most Expectancy, Most Total Return [%]",
            "Ticker": "CDW",
            "Strategy Type": "MACD",
            "Short Window": 28,
            "Long Window": 34,
            "Signal Window": 10,
            "Score": 1.2345,
            "Total Return [%]": 28.26,
            "Win Rate [%]": 59.26,
            "Total Trades": 82,
            # Add other required fields with dummy values
            "Signal Entry": True,
            "Signal Exit": False,
            "Total Open Trades": 1,
            "Profit Factor": 1.82,
            "Expectancy per Trade": 0.32,
            "Sortino Ratio": 1.32,
            "Beats BNH [%]": -0.97,
            "Avg Trade Duration": "1 days",
            "Trades Per Day": 0.018,
            "Trades per Month": 0.567,
            "Signals per Month": 1.127,
            "Expectancy per Month": 0.183,
            "Start": 0,
            "End": 3037,
            "Period": "3038 days",
            "Start Value": 1000.0,
            "End Value": 1282.65,
            "Benchmark Return [%]": 886.06,
            "Max Gross Exposure [%]": 100.0,
            "Total Fees Paid": 175.49,
            "Max Drawdown [%]": 6.39,
            "Max Drawdown Duration": "641 days",
            "Total Closed Trades": 81,
            "Open Trade PnL": -1.28,
            "Best Trade [%]": 10.09,
            "Worst Trade [%]": -2.88,
            "Avg Winning Trade [%]": 1.22,
            "Avg Losing Trade [%]": -0.98,
            "Avg Winning Trade Duration": "1 days",
            "Avg Losing Trade Duration": "1 days",
            "Expectancy": 3.51,
            "Sharpe Ratio": 0.58,
            "Calmar Ratio": 0.47,
            "Omega Ratio": 1.70,
            "Skew": 17.32,
            "Kurtosis": 594.55,
            "Tail Ratio": 3.63,
            "Common Sense Ratio": 0.47,
            "Value at Risk": 0.0,
            "Alpha": None,
            "Beta": None,
            "Daily Returns": 0.000086,
            "Annual Returns": 0.0216,
            "Cumulative Returns": 0.283,
            "Annualized Return": 0.0209,
            "Annualized Volatility": 0.045,
            "Signal Count": 0,
            "Position Count": 82,
            "Total Period": 4398.8,
            "Allocation [%]": None,
            "Stop Loss [%]": None,
            "Last Position Open Date": None,
            "Last Position Close Date": None
        }

        log(f"Original Metric Type: '{test_portfolio['Metric Type']}'")

        # Test the export pipeline
        from app.tools.strategy.export_portfolios import export_portfolios

        # Create a simple config for testing
        test_config = {
            "TICKER": "CDW",
            "STRATEGY_TYPES": ["MACD"],
            "TIMEFRAME": "D"
        }

        log("Testing export process...")

        # Call export with the test portfolio
        export_portfolios(
            portfolios=[test_portfolio],
            config=test_config,
            export_type="portfolios_best",
            log=log
        )

        log("Export completed - checking output file...")

        # Read the exported file to see what happened to Metric Type
        # Find the most recent export file
        import glob
        from datetime import datetime

        import polars as pl
        pattern = "/Users/colemorton/Projects/trading/data/raw/portfolios_best/*/20250726_*_D_MACD.csv"
        files = glob.glob(pattern)
        if files:
            latest_file = max(files)
            log(f"Reading exported file: {latest_file}")
            df = pl.read_csv(latest_file)
            if df.height > 0:
                exported_metric_type = df.row(0, named=True)["Metric Type"]
                log(f"Exported Metric Type: '{exported_metric_type}'")

                if exported_metric_type == test_portfolio["Metric Type"]:
                    log("✅ SUCCESS: Metric Type preserved correctly!")
                else:
                    log("❌ FAILURE: Metric Type was modified during export!")
                    log(f"Expected: '{test_portfolio['Metric Type']}'")
                    log(f"Got: '{exported_metric_type}'")
        else:
            log("No exported file found")

        log_close()

    except Exception as e:
        log(f"Error in debug_export: {str(e)}", "error")
        import traceback
        log(f"Traceback: {traceback.format_exc()}", "error")
        log_close()
        raise

if __name__ == "__main__":
    debug_export()
