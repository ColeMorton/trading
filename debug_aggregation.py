#!/usr/bin/env python3
"""
Debug script to test aggregation function with MACD filtered data
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import polars as pl

from app.tools.portfolio.collection import deduplicate_and_aggregate_portfolios
from app.tools.setup_logging import setup_logging


def debug_aggregation():
    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name="debug", log_file="debug_aggregation.log"
    )

    try:
        # Read the filtered MACD data
        filtered_file = "/Users/colemorton/Projects/trading/data/raw/portfolios_filtered/20250726/CDW_D_MACD.csv"

        log(f"Reading filtered data from: {filtered_file}")
        filtered_df = pl.read_csv(filtered_file)

        log(f"Filtered data shape: {filtered_df.shape}")
        log(f"Unique metric types: {filtered_df['Metric Type'].unique().to_list()}")

        # Test aggregation
        log("Testing aggregation function...")
        aggregated_result = deduplicate_and_aggregate_portfolios(filtered_df, log=log)

        log(f"Aggregation result type: {type(aggregated_result)}")

        if aggregated_result is not None:
            if hasattr(aggregated_result, "shape"):
                log(f"Aggregated data shape: {aggregated_result.shape}")

            # Convert to dict and check metric type
            if hasattr(aggregated_result, "to_dicts"):
                result_dicts = aggregated_result.to_dicts()
                if result_dicts:
                    log(f"Number of aggregated results: {len(result_dicts)}")
                    for i, result in enumerate(result_dicts):
                        log(
                            f"Result {i+1} Metric Type: '{result.get('Metric Type', 'NOT_FOUND')}'"
                        )
                        log(f"Result {i+1} Ticker: {result.get('Ticker', 'UNKNOWN')}")
                        log(
                            f"Result {i+1} Strategy Type: {result.get('Strategy Type', 'UNKNOWN')}"
                        )
                        log(
                            f"Result {i+1} Windows: {result.get('Fast Period', '?')}/{result.get('Slow Period', '?')}/{result.get('Signal Period', '?')}"
                        )
        else:
            log("Aggregation returned None")

        log_close()

    except Exception as e:
        log(f"Error in debug_aggregation: {str(e)}", "error")
        log_close()
        raise


if __name__ == "__main__":
    debug_aggregation()
