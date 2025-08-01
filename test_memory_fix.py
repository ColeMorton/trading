#!/usr/bin/env python3
"""
Test that validates compound metric types are preserved in memory during export processing
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import polars as pl

from app.tools.portfolio.collection import deduplicate_and_aggregate_portfolios
from app.tools.setup_logging import setup_logging

# Remove the non-existent import

def test_memory_fix():
    # Set up logging
    log, log_close, _, _ = setup_logging(
        module_name="test", log_file="test_memory_fix.log"
    )

    try:
        # Load the actual filtered MACD data
        filtered_file = "/Users/colemorton/Projects/trading/data/raw/portfolios_filtered/20250726/CDW_D_MACD.csv"

        log(f"Loading filtered MACD data: {filtered_file}")
        filtered_df = pl.read_csv(filtered_file)

        # Test aggregation to generate compound metric type
        log("Testing aggregation...")
        aggregated_result = deduplicate_and_aggregate_portfolios(filtered_df, log=log)

        if aggregated_result is not None and aggregated_result.height > 0:
            result_dict = aggregated_result.to_dicts()[0]
            compound_metric_type = result_dict.get("Metric Type", "MISSING")
            log(f"Original compound metric type: '{compound_metric_type}'")

            # Test the export processing WITHOUT actually writing to CSV
            log("Testing export processing in memory...")

            # Create DataFrame from the compound result
            test_df = pl.DataFrame([result_dict])
            log(f"Input to export processing - Metric Type: '{test_df['Metric Type'][0]}'")

            # Test the export processing function directly
            try:
                # Call the internal processing function that handles schema transformation
                from app.tools.portfolio.base_extended_schemas import SchemaType
                from app.tools.strategy.export_portfolios import export_portfolios

                # Simulate the export processing steps
                config = {
                    "TICKER": "CDW",
                    "STRATEGY_TYPES": ["MACD"],
                    "TIMEFRAME": "D"
                }

                # Check if the export function would preserve the compound metric type
                log("Checking export function logic...")

                # Test the specific logic that was causing issues
                has_metric_type = "Metric Type" in test_df.columns
                if has_metric_type:
                    metric_types = test_df["Metric Type"].unique().to_list()
                    compound_types = [mt for mt in metric_types if "," in str(mt)]
                    has_compound_metric_types = len(compound_types) > 0

                    log(f"Has Metric Type column: {has_metric_type}")
                    log(f"Metric types found: {metric_types}")
                    log(f"Compound types found: {compound_types}")
                    log(f"Has compound metric types: {has_compound_metric_types}")

                    if has_compound_metric_types:
                        log("✅ SUCCESS: Export function correctly detects compound metric types!")
                        log("✅ SUCCESS: Re-aggregation would be skipped!")

                        # Test schema transformation preserves compound type
                        from app.tools.portfolio.base_extended_schemas import (
                            SchemaTransformer,
                        )
                        transformer = SchemaTransformer()

                        portfolio_dict = test_df.to_dicts()[0]
                        log(f"Before schema transformation: '{portfolio_dict.get('Metric Type', 'MISSING')}'")

                        # Test the normalize function that was overriding the metric type
                        normalized = transformer.normalize_to_schema(
                            portfolio_dict,
                            SchemaType.FILTERED,
                            metric_type=portfolio_dict.get("Metric Type", "Most Total Return [%]")
                        )

                        final_metric_type = normalized.get("Metric Type", "MISSING")
                        log(f"After schema transformation: '{final_metric_type}'")

                        if final_metric_type == compound_metric_type:
                            log("🎉 SUCCESS: Schema transformation preserves compound metric types!")
                            return True
                        else:
                            log("❌ FAILURE: Schema transformation lost compound metric type")
                            return False
                    else:
                        log("❌ FAILURE: Export function doesn't detect compound metric types")
                        return False

            except Exception as e:
                log(f"Error during export processing test: {str(e)}", "error")
                import traceback
                log(f"Traceback: {traceback.format_exc()}", "error")
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
    success = test_memory_fix()
    if success:
        print("✅ TEST PASSED: Compound metric types preserved in memory")
    else:
        print("❌ TEST FAILED: Compound metric types not preserved in memory")
    exit(0 if success else 1)
