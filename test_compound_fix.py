#!/usr/bin/env python3
"""
Test that validates the compound metric type fix
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import polars as pl

from app.tools.portfolio.collection import deduplicate_and_aggregate_portfolios
from app.tools.setup_logging import setup_logging
from app.tools.strategy.export_portfolios import export_portfolios


def test_compound_fix():
    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name="test", log_file="test_compound_fix.log"
    )

    try:
        # Load the actual filtered MACD data that should generate compound metric types
        filtered_file = "/Users/colemorton/Projects/trading/data/raw/portfolios_filtered/20250726/CDW_D_MACD.csv"

        log(f"Loading filtered MACD data: {filtered_file}")
        filtered_df = pl.read_csv(filtered_file)

        log(f"Filtered data shape: {filtered_df.shape}")
        log(
            f"Number of unique metric types: {len(filtered_df['Metric Type'].unique())}"
        )

        # Test aggregation to generate compound metric type
        log("Testing aggregation...")
        aggregated_result = deduplicate_and_aggregate_portfolios(filtered_df, log=log)

        if aggregated_result is not None and aggregated_result.height > 0:
            result_dict = aggregated_result.to_dicts()[0]
            compound_metric_type = result_dict.get("Metric Type", "MISSING")
            log(f"Aggregated Metric Type: '{compound_metric_type}'")

            # Check if it's actually compound (contains commas)
            is_compound = "," in compound_metric_type
            log(f"Is compound metric type: {is_compound}")

            if is_compound:
                log("✅ SUCCESS: Aggregation generates compound metric types")

                # Now test direct export WITHOUT the problematic final collection export
                log("Testing direct export of aggregated result...")

                test_config = {
                    "TICKER": "CDW",
                    "STRATEGY_TYPES": ["MACD"],
                    "TIMEFRAME": "D",
                }

                # Export using the same method as the individual ticker exports
                export_portfolios(
                    portfolios=[result_dict],
                    config=test_config,
                    export_type="portfolios_best",
                    log=log,
                )

                # Read back the exported file to verify compound type is preserved
                import glob
                from datetime import datetime

                pattern = "/Users/colemorton/Projects/trading/data/raw/portfolios_best/*/20250726_*_D_MACD.csv"
                files = glob.glob(pattern)
                if files:
                    latest_file = max(files)
                    log(f"Reading back exported file: {latest_file}")
                    exported_df = pl.read_csv(latest_file)
                    if exported_df.height > 0:
                        exported_metric_type = exported_df.row(0, named=True)[
                            "Metric Type"
                        ]
                        log(f"Exported Metric Type: '{exported_metric_type}'")

                        if exported_metric_type == compound_metric_type:
                            log(
                                "🎉 SUCCESS: Compound metric type preserved through export!"
                            )
                            return True
                        else:
                            log("❌ FAILURE: Compound metric type lost during export")
                            log(f"Expected: '{compound_metric_type}'")
                            log(f"Got: '{exported_metric_type}'")
                            return False
                else:
                    log("❌ No exported file found")
                    return False
            else:
                log("❌ FAILURE: Aggregation did not generate compound metric type")
                return False
        else:
            log("❌ FAILURE: Aggregation returned no results")
            return False

    except Exception as e:
        log(f"Error in test: {str(e)}", "error")
        import traceback

        log(f"Traceback: {traceback.format_exc()}", "error")
        return False
    finally:
        log_close()


if __name__ == "__main__":
    success = test_compound_fix()
    if success:
        print("✅ TEST PASSED: Compound metric types work correctly")
    else:
        print("❌ TEST FAILED: Compound metric types not working")
    exit(0 if success else 1)
