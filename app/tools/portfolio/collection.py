"""
Portfolio Collection Module

This module handles the collection, sorting, and export of portfolios.
It provides centralized functionality for consistent portfolio operations
across the application.
"""

from typing import Any, Callable, Dict, List, Optional, Union

import polars as pl

from app.strategies.ma_cross.config_types import Config
from app.tools.portfolio.base_extended_schemas import SchemaTransformer, SchemaType


# Define our own error class to avoid circular imports
class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""


def sort_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame], config: Config
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """Sort portfolios using consistent logic across the application.

    Args:
        portfolios: Either a list of portfolio dictionaries or a Polars DataFrame
        config: Configuration dictionary containing sorting preferences

    Returns:
        Sorted portfolios in the same format as input (list or DataFrame)

    Note:
        Uses config['SORT_BY'] to determine sort column, defaults to 'Total Return [%]'
    """
    # Convert to DataFrame if necessary
    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios

    # Sort using consistent logic
    sort_by = config.get("SORT_BY", "Total Return [%]")
    sorted_df = df.sort(sort_by, descending=True)

    # Return in original format
    return sorted_df.to_dicts() if input_is_list else sorted_df


def deduplicate_and_aggregate_portfolios(
    portfolios: Union[List[Dict[str, Any]], pl.DataFrame],
    log: Optional[Callable] | None = None,
    desired_metric_types: Optional[List[str]] | None = None,
) -> Union[List[Dict[str, Any]], pl.DataFrame]:
    """
    Deduplicate portfolios to have exactly ONE row per {ticker,strategy_type} combination.
    Uses get_best_portfolio to find the best configuration for each ticker+strategy,
    then aggregates ALL metric types for that specific best configuration.

    Args:
        portfolios: Portfolio data
        log: Logging function
        desired_metric_types: Optional list of specific Metric Types to keep.
                             If None, keeps all. If provided, filters to only these types.

    Returns:
        Deduplicated portfolios with aggregated metric types (one per ticker+strategy)
    """
    from app.tools.portfolio.selection import get_best_portfolio

    input_is_list = isinstance(portfolios, list)
    df = pl.DataFrame(portfolios) if input_is_list else portfolios

    # Phase 3: Enhanced pre-aggregation validation with fail-fast error handling
    if log:
        log("🔧 PHASE 3: Starting aggregation with enhanced validation", "info")
    
    # Validate input data completeness
    if len(df) == 0:
        error_msg = "Cannot aggregate empty portfolio dataset"
        if log:
            log(f"❌ AGGREGATION ERROR: {error_msg}", "error")
        raise ValueError(error_msg)
    
    # Validate required columns for aggregation
    required_columns = ["Ticker", "Strategy Type", "Short Window", "Long Window"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = f"Missing required columns for aggregation: {missing_columns}"
        if log:
            log(f"❌ AGGREGATION ERROR: {error_msg}", "error")
        raise ValueError(error_msg)
    
    # Phase 3: Validate data completeness for metric type aggregation
    if "Metric Type" in df.columns:
        # Group by configuration to validate metric type completeness
        config_groups_df = df.group_by(["Ticker", "Strategy Type", "Short Window", "Long Window"]).agg([
            pl.col("Metric Type").unique().alias("metric_types"),
            pl.len().alias("row_count")
        ])
        
        total_configs = len(config_groups_df)
        configs_with_multiple_metrics = 0
        
        for row in config_groups_df.to_dicts():
            ticker = row["Ticker"]
            strategy = row["Strategy Type"] 
            short = row["Short Window"]
            long = row["Long Window"]
            metric_types = row["metric_types"]
            metric_count = len(metric_types) if metric_types else 0
            
            if metric_count > 1:
                configs_with_multiple_metrics += 1
                if log:
                    log(f"✅ Config {ticker},{strategy},{short},{long}: {metric_count} metric types - {metric_types[:3]}{'...' if metric_count > 3 else ''}", "debug")
            elif metric_count == 1:
                if log:
                    log(f"⚠️ Config {ticker},{strategy},{short},{long}: Only {metric_count} metric type - {metric_types}", "warning")
        
        if log:
            log(f"📊 AGGREGATION VALIDATION: {configs_with_multiple_metrics}/{total_configs} configurations have multiple metric types", "info")
            if configs_with_multiple_metrics == 0:
                log("⚠️ WARNING: No configurations with multiple metric types found - aggregation may not provide expected concatenation", "warning")
    else:
        if log:
            log("📊 No Metric Type column found - proceeding with standard deduplication", "info")

    # Filter to desired Metric Types if specified
    if desired_metric_types is not None and "Metric Type" in df.columns:
        original_count = len(df)
        # Get unique metric types present in data for debugging
        unique_metric_types = df["Metric Type"].unique().to_list()
        if log:
            log(f"Metric types present in data: {unique_metric_types}", "info")
            log(f"Desired metric types: {desired_metric_types}", "info")

        df = df.filter(pl.col("Metric Type").is_in(desired_metric_types))
        if log:
            log(
                f"Filtered to desired Metric Types: {len(df)}/{original_count} rows kept",
                "info",
            )

    # Verify Score column exists (should be calculated by stats_converter)
    if "Score" not in df.columns:
        if log:
            log(f"Score column not found. Available columns: {df.columns}", "warning")
        # Try to find score column with different casing
        score_col = None
        for col in df.columns:
            if col.lower() == "score":
                score_col = col
                break

        if score_col:
            df = df.rename({score_col: "Score"})
            if log:
                log(f"Renamed '{score_col}' column to 'Score'", "info")
        else:
            # Use Total Return [%] as fallback
            if "Total Return [%]" in df.columns:
                df = df.with_columns(
                    pl.col("Total Return [%]").cast(pl.Float64).alias("Score")
                )
                if log:
                    log("Using 'Total Return [%]' as Score column", "info")
            else:
                if log:
                    log(
                        "ERROR: Neither Score nor Total Return [%] column found",
                        "error",
                    )
                raise ValueError("Neither Score nor Total Return [%] column found")

    # Check if Metric Type column exists
    if "Metric Type" not in df.columns:
        if log:
            log("No Metric Type column found, skipping aggregation", "warning")
        return df.to_dicts() if input_is_list else df

    # Get unique ticker+strategy combinations
    ticker_strategy_combinations = df.select(["Ticker", "Strategy Type"]).unique()

    result_portfolios = []

    if log:
        log(
            f"Processing {len(ticker_strategy_combinations)} ticker+strategy combinations",
            "info",
        )

    for combination in ticker_strategy_combinations.to_dicts():
        ticker = combination["Ticker"]
        strategy_type = combination["Strategy Type"]

        # Get all portfolios for this ticker+strategy combination
        ticker_strategy_df = df.filter(
            (pl.col("Ticker") == ticker) & (pl.col("Strategy Type") == strategy_type)
        )

        if log:
            log(
                f"Processing {ticker} {strategy_type}: {len(ticker_strategy_df)} portfolios",
                "info",
            )

        # Use get_best_portfolio to find the best configuration
        # Create a mock config for get_best_portfolio
        mock_config = {"SORT_BY": "Score"}
        best_portfolio = get_best_portfolio(ticker_strategy_df, mock_config, log)

        if best_portfolio is None:
            if log:
                log(
                    f"No best portfolio found for {ticker} {strategy_type}, using highest score",
                    "warning",
                )
            # Fallback: use the highest scoring portfolio
            best_row = (
                ticker_strategy_df.sort("Score", descending=True).head(1).to_dicts()[0]
            )
            best_short = best_row["Short Window"]
            best_long = best_row["Long Window"]
            best_signal = best_row.get("Signal Window", 0)
        else:
            # get_best_portfolio returns consistent column names
            best_short = best_portfolio["Short Window"]
            best_long = best_portfolio["Long Window"]
            best_signal = best_portfolio.get("Signal Window", 0)

        # Phase 3: Optimized filtering with performance monitoring and enhanced error handling
        import time
        filter_start_time = time.time()
        
        # Find ALL metric types for this exact best configuration
        # Use optimized filtering with type-safe comparisons
        try:
            # First try direct comparison for performance
            best_config_df = ticker_strategy_df.filter(
                (pl.col("Short Window") == best_short)
                & (pl.col("Long Window") == best_long)
                & (pl.col("Signal Window") == best_signal)
            )
            
            # If no results, fall back to string conversion for data type compatibility
            if len(best_config_df) == 0:
                if log:
                    log(f"🔧 PHASE 3: Using string conversion fallback for {ticker} {strategy_type}", "debug")
                best_config_df = ticker_strategy_df.filter(
                    (pl.col("Short Window").cast(pl.Utf8) == str(best_short))
                    & (pl.col("Long Window").cast(pl.Utf8) == str(best_long))
                    & (pl.col("Signal Window").cast(pl.Utf8) == str(best_signal))
                )
            
        except Exception as e:
            if log:
                log(f"⚠️ PHASE 3: Filtering error for {ticker} {strategy_type}, using string conversion: {str(e)}", "warning")
            # Fallback to string conversion
            best_config_df = ticker_strategy_df.filter(
                (pl.col("Short Window").cast(pl.Utf8) == str(best_short))
                & (pl.col("Long Window").cast(pl.Utf8) == str(best_long))
                & (pl.col("Signal Window").cast(pl.Utf8) == str(best_signal))
            )
        
        filter_time = time.time() - filter_start_time
        
        # Phase 3: Enhanced debug logging with performance metrics
        if log:
            log(f"🔧 PHASE 3: Filtering for {ticker} {strategy_type} with {best_short}/{best_long}/{best_signal} completed in {filter_time:.4f}s", "debug")
            log(f"📊 Portfolios: {len(ticker_strategy_df)} → {len(best_config_df)} (after configuration filter)", "debug")

        if len(best_config_df) == 0:
            if log:
                log(
                    f"No portfolios found for best config {ticker} {strategy_type} {best_short}/{best_long}",
                    "warning",
                )
            continue

        # Collect all metric types for this configuration (unique only)
        metric_types = best_config_df.select("Metric Type").unique().to_series().to_list()

        # Phase 4: Enhanced debug logging for metric type aggregation
        if log:
            log(f"Debug: Found {len(metric_types)} metric types for {ticker} {strategy_type} config {best_short}/{best_long}/{best_signal}", "debug")
            log(f"Debug: Raw metric types: {metric_types}", "debug")

        # Sort metric types by priority: Most → Mean → Median → Least
        def get_priority(metric: str) -> int:
            metric = metric.strip()
            if metric.startswith("Most"):
                return 1
            elif metric.startswith("Mean"):
                return 2
            elif metric.startswith("Median"):
                return 3
            elif metric.startswith("Least"):
                return 4
            else:
                return 5

        sorted_metrics = sorted(metric_types, key=lambda x: (get_priority(x), x))
        aggregated_metric_type = ", ".join(sorted_metrics)

        # Phase 4: Enhanced debug logging for concatenation process
        if log:
            log(f"Debug: Sorted metric types: {sorted_metrics}", "debug")
            log(f"Debug: Aggregated metric type: '{aggregated_metric_type}'", "debug")

        # Use the best portfolio as the base and update the Metric Type
        final_portfolio = (
            best_config_df.sort("Score", descending=True).head(1).to_dicts()[0]
        )
        final_portfolio["Metric Type"] = aggregated_metric_type

        # Phase 3: Enhanced schema integration with comprehensive validation and error handling
        transformer = SchemaTransformer()
        schema_start_time = time.time()
        
        try:
            # Validate pre-normalization data integrity
            required_fields = ["Ticker", "Strategy Type", "Short Window", "Long Window", "Score"]
            missing_fields = [field for field in required_fields if field not in final_portfolio or final_portfolio[field] is None]
            
            if missing_fields:
                error_msg = f"Missing required fields for schema normalization: {missing_fields}"
                if log:
                    log(f"❌ SCHEMA ERROR for {ticker} {strategy_type}: {error_msg}", "error")
                raise ValueError(error_msg)
            
            # Normalize the portfolio to FILTERED schema (includes Metric Type)
            # Force analysis defaults to clear allocation values for aggregated portfolios
            normalized_portfolio = transformer.normalize_to_schema(
                final_portfolio, 
                SchemaType.FILTERED,
                metric_type=aggregated_metric_type,
                force_analysis_defaults=True
            )
            
            # Phase 3: Comprehensive post-normalization validation
            schema_time = time.time() - schema_start_time
            
            # Verify the metric type was preserved in normalization
            if normalized_portfolio.get("Metric Type") != aggregated_metric_type:
                if log:
                    log(f"⚠️ SCHEMA WARNING: Metric type changed during normalization: '{aggregated_metric_type}' → '{normalized_portfolio.get('Metric Type')}'", "warning")
            
            # Validate schema compliance
            is_valid, validation_errors = transformer.validate_schema(normalized_portfolio, SchemaType.FILTERED)
            if not is_valid:
                if log:
                    log(f"⚠️ SCHEMA VALIDATION FAILED for {ticker} {strategy_type}: {validation_errors}", "warning")
            
            # Verify allocation handling for analysis exports
            allocation_value = normalized_portfolio.get("Allocation [%]")
            if allocation_value is not None:
                if log:
                    log(f"⚠️ ALLOCATION WARNING: Expected None for analysis export, got: {allocation_value}", "warning")
            
            result_portfolios.append(normalized_portfolio)
            
            if log:
                log(f"✅ PHASE 3: Schema normalization completed for {ticker} {strategy_type} in {schema_time:.4f}s", "debug")
                log(f"📊 Metric type preserved: '{aggregated_metric_type}'", "debug")
                
        except Exception as e:
            schema_time = time.time() - schema_start_time
            error_details = {
                "ticker": ticker,
                "strategy_type": strategy_type,
                "aggregated_metric_type": aggregated_metric_type,
                "error": str(e),
                "processing_time": schema_time
            }
            
            if log:
                log(f"❌ PHASE 3: Schema normalization failed for {ticker} {strategy_type} after {schema_time:.4f}s: {str(e)}", "error")
                log(f"📊 Error context: {error_details}", "error")
            
            # Enhanced fallback with proper error handling
            try:
                # Fallback: Clear Allocation [%] for portfolios_best exports since this represents aggregated data
                final_portfolio["Allocation [%]"] = None  # Use None instead of empty string for consistency
                final_portfolio["Stop Loss [%]"] = None
                
                # Ensure Metric Type is preserved even in fallback
                final_portfolio["Metric Type"] = aggregated_metric_type
                
                result_portfolios.append(final_portfolio)
                
                if log:
                    log(f"🔧 PHASE 3: Applied fallback normalization for {ticker} {strategy_type}", "info")
                    
            except Exception as fallback_error:
                if log:
                    log(f"❌ CRITICAL: Fallback normalization also failed for {ticker} {strategy_type}: {str(fallback_error)}", "error")
                # Skip this portfolio if both normalization and fallback fail
                continue

        if log:
            log(
                f"Best config for {ticker} {strategy_type}: {best_short}/{best_long}, {len(metric_types)} metric types",
                "info",
            )

    # Phase 3: Enhanced result processing with performance monitoring
    if not result_portfolios:
        if log:
            log("⚠️ PHASE 3: No portfolios processed successfully", "warning")
        return [] if input_is_list else pl.DataFrame()
    
    try:
        result_df = pl.DataFrame(result_portfolios).sort("Score", descending=True)
    except Exception as e:
        if log:
            log(f"❌ PHASE 3: Failed to create result DataFrame: {str(e)}", "error")
        return result_portfolios if input_is_list else pl.DataFrame(result_portfolios)

    # Phase 3: Comprehensive validation and performance reporting
    if log:
        log(f"🔧 PHASE 3: Aggregation completed successfully", "info")
        log(f"📊 Portfolio reduction: {len(df)} → {len(result_df)} rows (one per ticker+strategy)", "info")
        
        # Validate schema compliance across all results
        schema_compliant_count = 0
        for portfolio in result_portfolios:
            if "Metric Type" in portfolio and portfolio["Metric Type"]:
                schema_compliant_count += 1
        
        log(f"📊 Schema compliance: {schema_compliant_count}/{len(result_df)} aggregated portfolios have valid Metric Types", "info")
        
        # Performance and quality metrics
        total_metric_types = sum(
            len(row.get("Metric Type", "").split(", ")) if row.get("Metric Type") else 0 
            for row in result_df.to_dicts()
        )
        avg_metric_types = total_metric_types / len(result_df) if len(result_df) > 0 else 0
        
        log(f"📊 Quality metrics: Average {avg_metric_types:.1f} metric types per aggregated portfolio", "info")
        
        # Log detailed sample of results
        sample_count = min(3, len(result_df))
        log(f"📊 Sample results (showing {sample_count} of {len(result_df)}):", "info")
        
        for i, row in enumerate(result_df.head(sample_count).to_dicts()):
            ticker = row.get("Ticker", "N/A")
            strategy = row.get("Strategy Type", "N/A")
            short_window = row.get("Short Window", "N/A")
            long_window = row.get("Long Window", "N/A")
            metric_type = row.get("Metric Type", "")
            metric_count = len(metric_type.split(", ")) if metric_type else 0
            score = row.get("Score", "N/A")
            
            log(f"  {i+1}. {ticker} {strategy} {short_window}/{long_window} - Score: {score}, Metrics: {metric_count} types", "info")
            if metric_type and len(metric_type) < 100:  # Only log short metric types
                log(f"     └─ '{metric_type}'", "info")
            elif metric_type:
                log(f"     └─ '{metric_type[:97]}...'", "info")
        
        # Final validation check
        if len(result_df) == 0:
            log("⚠️ PHASE 3: WARNING - No portfolios in final result", "warning")
        elif schema_compliant_count / len(result_df) < 0.8:
            log(f"⚠️ PHASE 3: WARNING - Low schema compliance rate: {schema_compliant_count}/{len(result_df)} ({schema_compliant_count/len(result_df)*100:.1f}%)", "warning")
        else:
            log(f"✅ PHASE 3: Aggregation validation passed - {schema_compliant_count}/{len(result_df)} portfolios schema compliant", "info")

    return result_df.to_dicts() if input_is_list else result_df


def test_bkng_metric_aggregation(log: Optional[Callable] = None) -> bool:
    """
    Test function to validate BKNG metric type concatenation through unified pipeline.
    
    This tests the specific BKNG case mentioned in Phase 4 requirements where
    4 unique (BKNG,SMA,60,77) portfolios should have their metric types concatenated.
    
    Args:
        log: Optional logging function
        
    Returns:
        True if test passes, False otherwise
    """
    if log:
        log("Testing BKNG metric type aggregation through unified pipeline", "info")
    
    # Sample BKNG data based on the CSV structure
    bkng_portfolios = [
        {
            "Ticker": "BKNG",
            "Strategy Type": "SMA", 
            "Short Window": 60,
            "Long Window": 77,
            "Signal Window": 0,
            "Metric Type": "Mean Win Rate [%]",
            "Score": 1.458,
            "Win Rate [%]": 50.9,
            "Total Trades": 56,
            "Allocation [%]": 2.78
        },
        {
            "Ticker": "BKNG",
            "Strategy Type": "SMA",
            "Short Window": 60, 
            "Long Window": 77,
            "Signal Window": 0,
            "Metric Type": "Most Profit Factor",
            "Score": 1.458,
            "Win Rate [%]": 50.9,
            "Total Trades": 56,
            "Allocation [%]": 2.78
        },
        {
            "Ticker": "BKNG",
            "Strategy Type": "SMA",
            "Short Window": 60,
            "Long Window": 77, 
            "Signal Window": 0,
            "Metric Type": "Most Expectancy",
            "Score": 1.458,
            "Win Rate [%]": 50.9,
            "Total Trades": 56,
            "Allocation [%]": 2.78
        },
        {
            "Ticker": "BKNG",
            "Strategy Type": "SMA",
            "Short Window": 60,
            "Long Window": 77,
            "Signal Window": 0, 
            "Metric Type": "Most Avg Winning Trade Duration",
            "Score": 1.458,
            "Win Rate [%]": 50.9,
            "Total Trades": 56,
            "Allocation [%]": 2.78
        }
    ]
    
    try:
        # Test the aggregation
        result = deduplicate_and_aggregate_portfolios(bkng_portfolios, log)
        
        # Validate results
        if len(result) != 1:
            if log:
                log(f"Test FAILED: Expected 1 aggregated portfolio, got {len(result)}", "error")
            return False
            
        aggregated = result[0]
        expected_metric_types = "Most Avg Winning Trade Duration, Most Expectancy, Most Profit Factor, Mean Win Rate [%]"
        actual_metric_type = aggregated.get("Metric Type", "")
        
        if actual_metric_type != expected_metric_types:
            if log:
                log(f"Test FAILED: Expected metric type '{expected_metric_types}', got '{actual_metric_type}'", "error")
            return False
            
        # Validate schema compliance - allocation should be None for analysis exports
        if "Allocation [%]" in aggregated:
            allocation_value = aggregated["Allocation [%]"]
            if allocation_value is not None:
                if log:
                    log(f"Test FAILED: Allocation [%] should be None for analysis exports, got '{allocation_value}'", "error")
                return False
        
        if log:
            log(f"Test PASSED: BKNG aggregation successful with metric type '{actual_metric_type}'", "info")
        return True
        
    except Exception as e:
        if log:
            log(f"Test FAILED: Exception during BKNG aggregation: {str(e)}", "error")
        return False


def export_best_portfolios(
    portfolios: List[Dict[str, Any]], config: Config, log: callable
) -> bool:
    """Export the best portfolios to a CSV file with deduplication.

    Args:
        portfolios: List of portfolio dictionaries to export
        config: Configuration for the export
        log: Logging function

    Returns:
        bool: True if export successful, False otherwise
    """
    if not portfolios:
        log("No portfolios to export", "warning")
        return False

    try:
        # Log configuration for debugging
        log("Configuration for export_best_portfolios:", "info")
        required_fields = ["BASE_DIR", "TICKER"]
        for field in required_fields:
            log(
                f"Field '{field}' present: {field in config}, value: {config.get(field)}",
                "info",
            )

        # Sort by Score instead of Total Return [%]
        original_sort_by = config.get("SORT_BY", "Total Return [%]")
        config["SORT_BY"] = "Score"

        # Sort portfolios
        sorted_portfolios = sort_portfolios(portfolios, config)

        # Use desired metric types from config if provided, otherwise use defaults
        desired_metric_types = config.get(
            "DESIRED_METRIC_TYPES",
            [
                # Total Return [%] variants
                "Most Total Return [%]",
                "Mean Total Return [%]",
                "Median Total Return [%]",
                # Total Trades variants
                "Most Total Trades",
                # Avg Winning Trade [%] variants
                "Most Avg Winning Trade [%]",
                "Mean Avg Winning Trade [%]",
                "Median Avg Winning Trade [%]",
                # Avg Winning Trade Duration variants
                "Most Avg Winning Trade Duration",
                "Mean Avg Winning Trade Duration",
                "Median Avg Winning Trade Duration"
                # Avg Losing Trade [%] variants
                "Least Avg Losing Trade [%]",
                # Avg Losing Trade Duration variants
                "Least Avg Losing Trade Duration",
                # Sharpe Ratio variants
                "Most Sharpe Ratio",
                "Mean Sharpe Ratio",
                "Median Sharpe Ratio",
                # Omega Ratio variants
                "Most Omega Ratio",
                "Mean Omega Ratio",
                "Median Omega Ratio",
                # Sortino Ratio variants
                "Most Sortino Ratio",
                "Mean Sortino Ratio",
                "Median Sortino Ratio",
                # Win Rate [%] variants
                "Most Win Rate [%]",
                "Mean Win Rate [%]",
                "Median Win Rate [%]",
                # Score variants
                "Most Score",
                "Mean Score",
                "Median Score",
                # Profit Factor variants
                "Most Profit Factor",
                "Mean Profit Factor",
                "Median Profit Factor",
                # Expectancy variants (both per Trade and standalone)
                "Most Expectancy per Trade",
                "Mean Expectancy per Trade",
                "Median Expectancy per Trade",
                "Most Expectancy",
                "Mean Expectancy",
                "Median Expectancy"
                # Beats BNH [%] variants
                "Most Beats BNH [%]",
                "Mean Beats BNH [%]",
                "Median Beats BNH [%]",
                # Calmar Ratio variants
                "Most Calmar Ratio",
                "Mean Calmar Ratio",
                "Median Calmar Ratio",
                # Max Drawdown [%] variants
                "Least Max Drawdown [%]",
                # Max Drawdown Duration variants
                "Least Max Drawdown Duration",
                # Best Trade [%] variants
                "Most Best Trade [%]",
                "Mean Best Trade [%]",
                "Median Best Trade [%]",
                # Worst Trade [%] variants
                "Least Worst Trade [%]",
                # Total Fees Paid variants
                "Least Total Fees Paid",
            ],
        )

        # Apply deduplication and metric type aggregation
        deduplicated_portfolios = deduplicate_and_aggregate_portfolios(
            sorted_portfolios, log, desired_metric_types
        )

        # Restore original sort configuration
        config["SORT_BY"] = original_sort_by

        # Import export_portfolios here to avoid circular imports
        if log:
            log("Importing export_portfolios to avoid circular imports", "info")
        try:
            from app.tools.strategy.export_portfolios import export_portfolios
        except ImportError as e:
            log(
                f"Failed to import export_portfolios due to circular import: {str(e)}",
                "error",
            )
            return False

        export_portfolios(
            portfolios=deduplicated_portfolios,
            config=config,
            export_type="portfolios_best",
            log=log,
        )

        log(
            f"Exported {len(deduplicated_portfolios)} unique portfolios sorted by Score"
        )
        return True

    except (ValueError, PortfolioExportError) as e:
        log(f"Failed to export portfolios: {str(e)}", "error")
        return False


def combine_strategy_portfolios(
    ema_portfolios: List[Dict[str, Any]], sma_portfolios: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Combine portfolios from EMA and SMA strategies.

    Args:
        ema_portfolios (List[Dict[str, Any]]): List of EMA strategy portfolios
        sma_portfolios (List[Dict[str, Any]]): List of SMA strategy portfolios

    Returns:
        List[Dict[str, Any]]: Combined list of portfolios with all required columns
    """
    # Ensure all required columns are present in both sets of portfolios
    required_columns = ["Short Window", "Long Window", "Strategy Type"]

    for portfolio in ema_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "EMA"
                else:
                    portfolio[col] = None

    for portfolio in sma_portfolios:
        for col in required_columns:
            if col not in portfolio:
                if col == "Strategy Type":
                    portfolio[col] = "SMA"
                else:
                    portfolio[col] = None

    return ema_portfolios + sma_portfolios


def collect_filtered_portfolios_for_export(
    config: Dict[str, Any], strategy_types: List[str], log: Callable
) -> List[Dict[str, Any]]:
    """
    Collect filtered portfolios data (multiple metric types per configuration)
    from portfolios_filtered CSV files for best portfolios export.

    This function reads the portfolios_filtered CSV files that contain multiple
    metric types (Most, Least, Mean, Median) per unique strategy configuration,
    which is what should be used for portfolios_best aggregation.

    Args:
        config: Configuration dictionary
        strategy_types: List of strategy types to collect (e.g., ["SMA", "EMA"])
        log: Logging function

    Returns:
        List of portfolio dictionaries with Metric Type column containing
        multiple metric types per strategy configuration
    """
    from pathlib import Path

    import polars as pl

    all_portfolios = []

    try:
        # Get the ticker(s) from config
        ticker_config = config.get("TICKER", "")
        if not ticker_config:
            log("No ticker found in config for filtered portfolio collection", "error")
            return []

        # Handle both single ticker (string) and multiple tickers (list)
        if isinstance(ticker_config, list):
            tickers = ticker_config
        else:
            tickers = [ticker_config]

        # Get the base directory for CSV files
        base_dir = config.get("BASE_DIR", "/Users/colemorton/Projects/trading")
        csv_base = Path(base_dir) / "csv"

        # Determine the timeframe suffix
        timeframe = "H" if config.get("USE_HOURLY", False) else "D"

        # Process each ticker
        for ticker in tickers:
            for strategy_type in strategy_types:
                # Construct the path to the filtered CSV file
                # portfolios_filtered files contain multiple metric types per
                # configuration
                filtered_file = (
                    csv_base
                    / "portfolios_filtered"
                    / f"{ticker}_{timeframe}_{strategy_type}.csv"
                )

                # Also check in date-based subdirectories (most recent first)
                portfolios_filtered_dir = csv_base / "portfolios_filtered"
                date_dirs = sorted(
                    [
                        d
                        for d in portfolios_filtered_dir.iterdir()
                        if d.is_dir() and d.name.isdigit()
                    ],
                    reverse=True,
                )

                # Try root directory first
                if not filtered_file.exists():
                    # Try date directories
                    for date_dir in date_dirs:
                        date_filtered_file = (
                            date_dir / f"{ticker}_{timeframe}_{strategy_type}.csv"
                        )
                        if date_filtered_file.exists():
                            filtered_file = date_filtered_file
                            log(
                                f"Found filtered file for {ticker} in date directory: {date_dir.name}"
                            )
                            break

                if not filtered_file.exists():
                    log(
                        f"Filtered portfolios file not found: {ticker}_{timeframe}_{strategy_type}.csv",
                        "warning",
                    )
                    continue

                try:
                    # Read the filtered CSV file
                    log(f"Reading filtered portfolios from: {filtered_file}")
                    df = pl.read_csv(str(filtered_file))

                    if len(df) == 0:
                        log(
                            f"Empty filtered portfolios file: {filtered_file}",
                            "warning",
                        )
                        continue

                    # Convert to dictionaries
                    portfolios_data = df.to_dicts()
                    log(
                        f"Found {len(portfolios_data)} filtered portfolios from {ticker} {strategy_type}"
                    )

                    # Verify the data has Metric Type column
                    if len(portfolios_data) > 0:
                        first_portfolio = portfolios_data[0]
                        if "Metric Type" in first_portfolio:
                            log(
                                f"Confirmed Metric Type column present in {ticker} {strategy_type} data"
                            )
                            log(
                                f"Sample metric types: {[p.get('Metric Type', 'N/A') for p in portfolios_data[:3]]}"
                            )
                        else:
                            log(
                                f"WARNING: Metric Type column missing from {ticker} {strategy_type} filtered data",
                                "warning",
                            )

                    all_portfolios.extend(portfolios_data)

                except Exception as e:
                    log(
                        f"Error reading filtered portfolios file {filtered_file}: {str(e)}",
                        "error",
                    )
                    continue

        log(f"Collected total of {len(all_portfolios)} portfolios from filtered data")

        if len(all_portfolios) > 0:
            # Verify we have multiple metric types per configuration
            sample_config_groups = {}
            for portfolio in all_portfolios[:10]:  # Sample first 10
                ticker = portfolio.get("Ticker", "")
                strategy = portfolio.get("Strategy Type", "")
                short_window = portfolio.get("Short Window", "")
                long_window = portfolio.get("Long Window", "")
                metric_type = portfolio.get("Metric Type", "")

                config_key = f"{ticker},{strategy},{short_window},{long_window}"
                if config_key not in sample_config_groups:
                    sample_config_groups[config_key] = []
                sample_config_groups[config_key].append(metric_type)

            for config_key, metric_types in sample_config_groups.items():
                log(
                    f"Config {config_key}: {len(metric_types)} metric types - {', '.join(metric_types[:3])}{'...' if len(metric_types) > 3 else ''}"
                )

        return all_portfolios

    except Exception as e:
        log(f"Error collecting filtered portfolios: {str(e)}", "error")
        return []
