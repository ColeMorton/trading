"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files using the
centralized export functionality.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple

import polars as pl

from app.tools.export_csv import ExportConfig, export_csv
from app.tools.portfolio.base_extended_schemas import (
    CANONICAL_COLUMN_NAMES,
    ExtendedPortfolioSchema,
    FilteredPortfolioSchema,
    PortfolioSchemaValidationError,
    SchemaTransformer,
    SchemaType,
)
from app.tools.portfolio.schema_detection import ensure_allocation_sum_100_percent
from app.tools.portfolio.strategy_types import STRATEGY_TYPE_FIELDS
from app.tools.portfolio.strategy_utils import get_strategy_type_for_export


def _validate_portfolio_schema(
    portfolio: Dict,
    expected_schema: SchemaType,
    transformer: SchemaTransformer,
    log: Optional[Callable] = None,
) -> tuple[bool, List[str]]:
    """
    Perform mandatory schema validation before export.

    Args:
        portfolio: Portfolio dictionary to validate
        expected_schema: Expected schema type
        transformer: SchemaTransformer instance
        log: Optional logging function

    Returns:
        Tuple of (is_valid, list_of_errors)

    Raises:
        PortfolioSchemaValidationError: If strict validation fails
    """
    is_valid, errors = transformer.validate_schema(portfolio, expected_schema)

    if not is_valid:
        error_msg = (
            f"Schema validation failed for {expected_schema.name}: {'; '.join(errors)}"
        )
        if log:
            log(error_msg, "error")
        # In Phase 3, we implement fail-fast validation
        raise PortfolioSchemaValidationError(
            error_msg, {"errors": errors, "schema": expected_schema.name}
        )

    if log:
        log(f"Schema validation passed for {expected_schema.name}", "debug")

    return is_valid, errors


def _validate_canonical_ordering(
    df: pl.DataFrame, expected_schema: SchemaType, log: Optional[Callable] = None
) -> tuple[bool, List[str]]:
    """
    Perform strict canonical ordering validation on DataFrame.

    Args:
        df: DataFrame to validate
        expected_schema: Expected schema type
        log: Optional logging function

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    columns = df.columns

    if expected_schema == SchemaType.EXTENDED:
        expected_columns = ExtendedPortfolioSchema.get_column_names()
        schema_name = "Extended (62-column)"
    elif expected_schema == SchemaType.FILTERED:
        expected_columns = FilteredPortfolioSchema.get_column_names()
        schema_name = "Filtered (63-column)"
    else:
        # For other schema types, use CANONICAL_COLUMN_NAMES
        expected_columns = CANONICAL_COLUMN_NAMES
        schema_name = "Canonical"

    # Check if columns match expected ordering exactly
    if len(columns) != len(expected_columns):
        errors.append(
            f"Column count mismatch: expected {len(expected_columns)}, got {len(columns)}"
        )

    # Check column ordering
    for i, (actual, expected) in enumerate(zip(columns, expected_columns)):
        if actual != expected:
            errors.append(
                f"Column ordering error at position {i}: expected '{expected}', got '{actual}'"
            )
            break  # Only report first ordering error to avoid spam

    # Specific validation for critical columns
    critical_positions = {
        "Allocation [%]": 59,  # Position 59 in Extended schema
        "Stop Loss [%]": 60,  # Position 60 in Extended schema
    }

    for col_name, expected_pos in critical_positions.items():
        if col_name in columns:
            actual_pos = columns.index(col_name) + 1  # 1-based indexing
            if actual_pos != expected_pos and expected_schema == SchemaType.EXTENDED:
                errors.append(
                    f"Critical column '{col_name}' at wrong position: expected {expected_pos}, got {actual_pos}"
                )

    is_valid = len(errors) == 0

    if log:
        if is_valid:
            log(
                f"Canonical ordering validation passed for {schema_name} schema",
                "debug",
            )
        else:
            log(
                f"Canonical ordering validation failed for {schema_name} schema: {'; '.join(errors)}",
                "error",
            )

    return is_valid, errors


class ExportTypeRouter:
    """
    Enhanced export type routing based on SchemaType enum with validation and monitoring.
    """

    # Schema routing configuration with additional metadata
    EXPORT_SCHEMA_CONFIG = {
        "portfolios_best": {
            "schema": SchemaType.FILTERED,
            "description": "63 columns, Metric Type + Extended for best portfolios with aggregated metrics",
            "allocation_handling": "none",  # No allocation values for analysis
            "validation_level": "strict",
        },
        "portfolios_filtered": {
            "schema": SchemaType.FILTERED,
            "description": "63 columns, Metric Type + Extended for filtered results",
            "allocation_handling": "none",
            "validation_level": "strict",
        },
        "portfolios_scanner": {
            "schema": SchemaType.EXTENDED,
            "description": "62 columns, canonical format for scanner results",
            "allocation_handling": "none",
            "validation_level": "strict",
        },
        "portfolios": {
            "schema": SchemaType.EXTENDED,
            "description": "62 columns, canonical format (default)",
            "allocation_handling": "none",
            "validation_level": "strict",
        },
    }

    @classmethod
    def get_target_schema_type(cls, export_type: str) -> SchemaType:
        """
        Determine the appropriate target schema type based on export type.

        Args:
            export_type: Type of export

        Returns:
            SchemaType: Appropriate schema type for the export
        """
        config = cls.EXPORT_SCHEMA_CONFIG.get(export_type)
        if config:
            return config["schema"]
        return SchemaType.EXTENDED  # Default fallback

    @classmethod
    def get_export_config(cls, export_type: str) -> Dict[str, Any]:
        """
        Get complete export configuration for the given export type.

        Args:
            export_type: Type of export

        Returns:
            Dictionary with export configuration
        """
        return cls.EXPORT_SCHEMA_CONFIG.get(
            export_type,
            {
                "schema": SchemaType.EXTENDED,
                "description": "Default configuration",
                "allocation_handling": "none",
                "validation_level": "strict",
            },
        )

    @classmethod
    def validate_export_type(cls, export_type: str) -> bool:
        """
        Validate if export type is supported.

        Args:
            export_type: Type of export to validate

        Returns:
            True if supported, False otherwise
        """
        return export_type in cls.EXPORT_SCHEMA_CONFIG


def _get_target_schema_type(export_type: str) -> SchemaType:
    """
    Legacy wrapper for backward compatibility.
    """
    return ExportTypeRouter.get_target_schema_type(export_type)


class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""


VALID_EXPORT_TYPES = {
    "portfolios",
    "portfolios_scanner",
    "portfolios_filtered",
    "portfolios_best",
}


def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] | None = None,
    log: Optional[Callable] | None = None,
    feature_dir: str = "",  # Default to empty string for direct export to data/raw/strategies/
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered, portfolios_best)
        csv_filename (Optional[str]): Optional custom filename for the CSV
        log (Optional[Callable]): Optional logging function
        feature_dir (str): Directory to export to (default: "" for direct export to data/raw/strategies/)
                          Can be set to "ma_cross" for backward compatibility

    Returns:
        Tuple[pl.DataFrame, bool]: (DataFrame of exported data, success status)

    Raises:
        PortfolioExportError: If export fails or invalid export type provided
        ValueError: If portfolios list is empty
    """
    if not portfolios:
        if log:
            log("No portfolios to export", "warning")
        raise ValueError("Cannot export empty portfolio list")

    # Enhanced export type validation using ExportTypeRouter (Phase 3)
    if not ExportTypeRouter.validate_export_type(export_type):
        supported_types = list(ExportTypeRouter.EXPORT_SCHEMA_CONFIG.keys())
        error_msg = f"Invalid export type: {export_type}. Must be one of: {', '.join(supported_types)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg)

    # Get export configuration with schema routing details
    export_config = ExportTypeRouter.get_export_config(export_type)
    if log:
        log(f"Export configuration: {export_config['description']}", "info")

    # Phase 1 Data Flow Audit: Log incoming portfolio data to export_portfolios
    log(
        f"📊 PHASE 1 AUDIT: export_portfolios() entry with {len(portfolios)} portfolios, export_type='{export_type}'",
        "info",
    )

    # Log metric type distribution in incoming data
    incoming_metric_counts = {}
    incoming_cbre_data = []
    for p in portfolios:
        metric_type = p.get("Metric Type", "Unknown")
        incoming_metric_counts[metric_type] = (
            incoming_metric_counts.get(metric_type, 0) + 1
        )

        if p.get("Ticker") == "CBRE":
            incoming_cbre_data.append(
                {
                    "Ticker": p.get("Ticker"),
                    "Strategy": p.get("Strategy Type"),
                    "Short": p.get("Short Window"),
                    "Long": p.get("Long Window"),
                    "Metric": p.get("Metric Type"),
                }
            )

    log(
        f"📊 INCOMING METRIC TYPES TO export_portfolios(): {dict(incoming_metric_counts)}",
        "info",
    )
    if incoming_cbre_data:
        log(
            f"📊 INCOMING CBRE DATA TO export_portfolios(): {incoming_cbre_data}", "info"
        )

    if log:
        log(f"Exporting {len(portfolios)} portfolios as {export_type}...", "info")

    # Determine strategy type from STRATEGY_TYPES list for filename generation
    strategy_types = config.get("STRATEGY_TYPES", ["SMA"])

    # Set STRATEGY_TYPE for filename generation based on single vs multiple strategies
    if len(strategy_types) == 1:
        # Single strategy: use specific strategy type in filename
        strategy_type = strategy_types[0]
        config["STRATEGY_TYPE"] = strategy_type
        config["USE_MA"] = True  # Always include strategy suffix for single strategies
    else:
        # Multiple strategies: use generic filename without strategy suffix
        config["STRATEGY_TYPE"] = "Multi"
        config["USE_MA"] = False

    try:
        # Check if we have pre-sorted portfolios in the config
        if config.get("_SORTED_PORTFOLIOS") is not None:
            # Use the pre-sorted portfolios
            portfolios = config["_SORTED_PORTFOLIOS"]
            if log:
                log("Using pre-sorted portfolios from config", "info")
            # Remove from config to avoid confusion
            del config["_SORTED_PORTFOLIOS"]

        # Note: Allocation processing is now handled by SchemaTransformer defaults
        # The schema ensures proper allocation handling (None for analysis exports)
        # No manual allocation processing needed as SchemaTransformer handles this

        # Convert portfolios to DataFrame
        df = pl.DataFrame(portfolios)

        # Initialize SchemaTransformer for unified schema handling
        transformer = SchemaTransformer()
        target_schema_type = _get_target_schema_type(export_type)

        if log:
            log(
                f"Using schema type {target_schema_type.name} for export type {export_type}",
                "info",
            )

        # Phase 4: Special handling for portfolios_best with metric type aggregation or multiple strategy types
        has_metric_type = "Metric Type" in df.columns
        has_multiple_strategy_types = (
            "Strategy Type" in df.columns
            and len(df.select("Strategy Type").unique()) > 1
        )

        # Apply minimum filtering for portfolios_best before any aggregation
        if export_type == "portfolios_best":
            from app.tools.portfolio.filtering_service import PortfolioFilterService

            # Apply MinimumsFilter to ensure YAML config criteria are enforced
            filter_service = PortfolioFilterService()
            filtered_df = filter_service.filter_portfolios_dataframe(df, config, log)

            if filtered_df is None or len(filtered_df) == 0:
                if log:
                    log(
                        "No portfolios remain after applying MINIMUMS filtering for portfolios_best",
                        "warning",
                    )
                return pl.DataFrame(), False

            df = filtered_df
            if log:
                log(
                    f"Applied MINIMUMS filtering for portfolios_best: {len(df)} portfolios remain",
                    "info",
                )

        # Check if portfolios already have compound metric types (indicating prior aggregation)
        has_compound_metric_types = False
        if has_metric_type:
            metric_types = df["Metric Type"].unique().to_list()
            compound_types = [mt for mt in metric_types if "," in str(mt)]
            has_compound_metric_types = len(compound_types) > 0

            if log and has_compound_metric_types:
                log(
                    f"📊 DETECTED compound metric types: {compound_types[:3]}{'...' if len(compound_types) > 3 else ''}",
                    "info",
                )

        if (
            export_type == "portfolios_best"
            and (has_metric_type or has_multiple_strategy_types)
            and not has_compound_metric_types
        ):
            from app.tools.portfolio.collection import (
                deduplicate_and_aggregate_portfolios,
            )

            if log:
                if has_metric_type and has_multiple_strategy_types:
                    log(
                        "📊 DETECTED Metric Type column AND multiple strategy types - applying aggregation for portfolios_best export",
                        "info",
                    )
                elif has_metric_type:
                    log(
                        "📊 DETECTED Metric Type column - applying aggregation for portfolios_best export",
                        "info",
                    )
                elif has_multiple_strategy_types:
                    log(
                        "📊 DETECTED multiple strategy types - applying aggregation for portfolios_best export",
                        "info",
                    )

                # Log detailed pre-aggregation data
                pre_agg_cbre = df.filter(pl.col("Ticker") == "CBRE")
                if len(pre_agg_cbre) > 0:
                    log(
                        f"📊 PRE-AGGREGATION CBRE DATA: {len(pre_agg_cbre)} rows", "info"
                    )
                    cbre_details = pre_agg_cbre.select(
                        "Ticker",
                        "Strategy Type",
                        "Short Window",
                        "Long Window",
                        "Metric Type",
                    ).to_dicts()
                    log(f"📊 PRE-AGGREGATION CBRE DETAILS: {cbre_details}", "info")

            # Apply metric type aggregation before schema transformation
            pre_aggregation_count = len(df)

            # Convert to dict for aggregation function
            pre_agg_portfolios = df.to_dicts()
            log(
                f"📊 CALLING deduplicate_and_aggregate_portfolios() with {len(pre_agg_portfolios)} portfolios",
                "info",
            )

            aggregated_portfolios = deduplicate_and_aggregate_portfolios(
                pre_agg_portfolios, log
            )
            df = pl.DataFrame(aggregated_portfolios)

            if log:
                log(
                    f"📊 AGGREGATION RESULT: {pre_aggregation_count} → {len(df)} portfolios",
                    "info",
                )

                # Log post-aggregation CBRE data
                post_agg_cbre = df.filter(pl.col("Ticker") == "CBRE")
                if len(post_agg_cbre) > 0:
                    log(
                        f"📊 POST-AGGREGATION CBRE DATA: {len(post_agg_cbre)} rows",
                        "info",
                    )
                    cbre_post_details = post_agg_cbre.select(
                        "Ticker",
                        "Strategy Type",
                        "Short Window",
                        "Long Window",
                        "Metric Type",
                    ).to_dicts()
                    log(f"📊 POST-AGGREGATION CBRE DETAILS: {cbre_post_details}", "info")
        elif export_type == "portfolios_best" and has_compound_metric_types:
            if log:
                log(
                    "📊 SKIPPING aggregation - portfolios already have compound metric types (previously aggregated)",
                    "info",
                )

        # Special handling for portfolios_best export type
        if export_type == "portfolios_best":
            # Ensure required columns exist
            required_columns = ["Short Window", "Long Window"]
            for col in required_columns:
                if col not in df.columns:
                    df = df.with_columns(pl.lit(None).alias(col))

            # Check if we need to rename SMA/EMA columns to Short/Long Window
            if "Short Window" not in df.columns or df.get_column(
                "Short Window"
            ).null_count() == len(df):
                # Create Short Window and Long Window columns based on available data
                expressions = []

                # Check if we have SMA columns
                has_sma_fast = "SMA_FAST" in df.columns
                has_sma_slow = "SMA_SLOW" in df.columns

                # Check if we have EMA columns
                has_ema_fast = "EMA_FAST" in df.columns
                has_ema_slow = "EMA_SLOW" in df.columns

                # Create Short Window expression based on available columns
                if has_sma_fast and has_ema_fast:
                    # If both SMA_FAST and EMA_FAST exist, use conditional based on
                    # Strategy Type
                    if "Strategy Type" in df.columns:
                        expressions.append(
                            pl.when(pl.col("Strategy Type").eq("SMA"))
                            .then(pl.col("SMA_FAST"))
                            .otherwise(pl.col("EMA_FAST"))
                            .alias("Short Window")
                        )
                    elif "Use SMA" in df.columns:
                        # Legacy support for Use SMA
                        expressions.append(
                            pl.when(pl.col("Use SMA").eq(True))
                            .then(pl.col("SMA_FAST"))
                            .otherwise(pl.col("EMA_FAST"))
                            .alias("Short Window")
                        )
                    else:
                        # Default to EMA if no strategy type information
                        expressions.append(pl.col("EMA_FAST").alias("Short Window"))
                        if log:
                            log(
                                "No strategy type information found, defaulting to EMA for Short Window",
                                "warning",
                            )
                elif has_sma_fast:
                    # If only SMA_FAST exists
                    expressions.append(pl.col("SMA_FAST").alias("Short Window"))
                elif has_ema_fast:
                    # If only EMA_FAST exists
                    expressions.append(pl.col("EMA_FAST").alias("Short Window"))
                else:
                    # If neither exists, create empty column
                    expressions.append(pl.lit(None).alias("Short Window"))

                # Create Long Window expression based on available columns
                if has_sma_slow and has_ema_slow:
                    # If both SMA_SLOW and EMA_SLOW exist, use conditional based on
                    # Strategy Type
                    if "Strategy Type" in df.columns:
                        expressions.append(
                            pl.when(pl.col("Strategy Type").eq("SMA"))
                            .then(pl.col("SMA_SLOW"))
                            .otherwise(pl.col("EMA_SLOW"))
                            .alias("Long Window")
                        )
                    elif "Use SMA" in df.columns:
                        # Legacy support for Use SMA
                        expressions.append(
                            pl.when(pl.col("Use SMA").eq(True))
                            .then(pl.col("SMA_SLOW"))
                            .otherwise(pl.col("EMA_SLOW"))
                            .alias("Long Window")
                        )
                    else:
                        # Default to EMA if no strategy type information
                        expressions.append(pl.col("EMA_SLOW").alias("Long Window"))
                        if log:
                            log(
                                "No strategy type information found, defaulting to EMA for Long Window",
                                "warning",
                            )
                elif has_sma_slow:
                    # If only SMA_SLOW exists
                    expressions.append(pl.col("SMA_SLOW").alias("Long Window"))
                elif has_ema_slow:
                    # If only EMA_SLOW exists
                    expressions.append(pl.col("EMA_SLOW").alias("Long Window"))
                else:
                    # If neither exists, create empty column
                    expressions.append(pl.lit(None).alias("Long Window"))

                # Apply the expressions if we have any
                if expressions:
                    df = df.with_columns(expressions)

            # Remove redundant columns
            redundant_columns = ["EMA_FAST", "EMA_SLOW", "SMA_FAST", "SMA_SLOW"]
            for col in redundant_columns:
                if col in df.columns:
                    df = df.drop(col)

            # Add Strategy Type column based on strategy type information
            if STRATEGY_TYPE_FIELDS["CSV"] not in df.columns:
                # Create a list of rows to process
                rows = df.to_dicts()
                strategy_types = []

                # Process each row to determine strategy type
                for row in rows:
                    strategy_type = get_strategy_type_for_export(row, log)
                    strategy_types.append(strategy_type)

                # Add the strategy type column
                df = df.with_columns(
                    pl.Series(STRATEGY_TYPE_FIELDS["CSV"], strategy_types)
                )

                if log:
                    log(
                        f"Added {STRATEGY_TYPE_FIELDS['CSV']} column with determined strategy types",
                        "info",
                    )

            # Remove Use SMA field from export as it's now redundant
            if "Use SMA" in df.columns:
                df = df.drop("Use SMA")
                if log:
                    log("Removed redundant 'Use SMA' field from export", "info")

            # Get ticker from config
            ticker = config["TICKER"]
            if isinstance(ticker, list):
                if len(ticker) == 1:
                    ticker = ticker[0]
                else:
                    # For multiple tickers, each portfolio should already have its
                    # ticker
                    if "Ticker" not in df.columns:
                        raise PortfolioExportError(
                            "Missing Ticker column for multiple ticker export"
                        )

            # Add or update Ticker column if it's a single ticker
            if isinstance(ticker, str):
                if "Ticker" in df.columns:
                    df = df.drop("Ticker")
                df = df.with_columns(pl.lit(ticker).alias("Ticker"))

        # Schema normalization for FILTERED schema types (portfolios_best, portfolios_filtered)
        if target_schema_type in [SchemaType.FILTERED, SchemaType.ATR_FILTERED]:
            # Use SchemaTransformer to normalize to target schema with mandatory validation
            # This replaces the custom column ordering logic and ensures proper allocation handling
            portfolios_normalized = []
            validation_failures = 0

            for portfolio_dict in df.to_dicts():
                try:
                    # Step 1: Normalize each portfolio to target schema with canonical ordering
                    # For analysis exports (portfolios_best, portfolios_filtered), force allocation/stop loss to None
                    force_analysis_defaults = export_type in [
                        "portfolios_best",
                        "portfolios_filtered",
                    ]

                    # Preserve existing metric type if present (critical for aggregated portfolios)
                    existing_metric_type = portfolio_dict.get(
                        "Metric Type", "Most Total Return [%]"
                    )

                    normalized_portfolio = transformer.normalize_to_schema(
                        portfolio_dict,
                        target_schema_type,
                        metric_type=existing_metric_type,
                        force_analysis_defaults=force_analysis_defaults,
                    )

                    # Step 2: Mandatory schema validation (Phase 3 enhancement)
                    _validate_portfolio_schema(
                        normalized_portfolio, target_schema_type, transformer, log
                    )

                    portfolios_normalized.append(normalized_portfolio)

                except PortfolioSchemaValidationError as e:
                    validation_failures += 1
                    if log:
                        log(
                            f"Schema validation failed for portfolio: {str(e)}", "error"
                        )
                    # Re-raise validation errors as they are critical
                    raise

                except Exception as e:
                    if log:
                        log(
                            f"Schema normalization failed for portfolio: {str(e)}",
                            "warning",
                        )
                    # Fall back to original portfolio if normalization fails
                    portfolios_normalized.append(portfolio_dict)

            # Recreate DataFrame with normalized portfolios
            df = pl.DataFrame(portfolios_normalized)

            # Phase 3: Strict canonical ordering validation
            ordering_valid, ordering_errors = _validate_canonical_ordering(
                df, target_schema_type, log
            )
            if not ordering_valid:
                error_msg = f"Canonical ordering validation failed: {'; '.join(ordering_errors)}"
                if log:
                    log(error_msg, "error")
                raise PortfolioSchemaValidationError(
                    error_msg,
                    {
                        "errors": ordering_errors,
                        "validation_type": "canonical_ordering",
                    },
                )

            # Performance monitoring and compliance reporting (Phase 3 enhancement)
            if log:
                total_portfolios = (
                    len(df.to_dicts()) if portfolios_normalized else len(df)
                )
                success_rate = (
                    ((total_portfolios - validation_failures) / total_portfolios * 100)
                    if total_portfolios > 0
                    else 0
                )
                log(
                    f"Schema compliance report: {len(portfolios_normalized)}/{total_portfolios} portfolios processed",
                    "info",
                )
                log(f"Schema validation success rate: {success_rate:.1f}%", "info")
                log(
                    f"Applied SchemaTransformer normalization with {target_schema_type.name} schema",
                    "info",
                )
                log(
                    f"Canonical ordering validation: {'PASSED' if ordering_valid else 'FAILED'}",
                    "info",
                )

                if validation_failures > 0:
                    log(
                        f"WARNING: {validation_failures} validation failures encountered",
                        "warning",
                    )

        # Use the provided feature_dir parameter for the feature1 value
        # This allows different scripts to export to different directories
        # If feature_dir is empty, use export_type to ensure correct directory structure
        feature1 = feature_dir if feature_dir else export_type

        # Ensure all return metrics are included in the export
        # List of metrics that should be included in the export
        return_metrics = [
            "Daily Returns",
            "Annual Returns",
            "Cumulative Returns",
            "Annualized Return",
            "Annualized Volatility",
            "Skew",
            "Kurtosis",
            "Tail Ratio",
            "Common Sense Ratio",
            "Value at Risk",
        ]

        # Remove 'RSI Window' column if it exists
        if "RSI Window" in df.columns:
            df = df.drop("RSI Window")
            if log:
                log("Removed 'RSI Window' column from export data", "info")

        # Ensure columns have the expected data types
        # Convert integer columns
        integer_columns = ["Short Window", "Long Window", "Total Trades"]
        for col in integer_columns:
            if col in df.columns:
                try:
                    df = df.with_columns(pl.col(col).cast(pl.Int64))
                except Exception as e:
                    if log:
                        log(
                            f"Failed to convert column '{col}' to Int64: {str(e)}",
                            "warning",
                        )

        # Convert float columns
        float_columns = ["Win Rate [%]"]
        for col in float_columns:
            if col in df.columns:
                try:
                    df = df.with_columns(pl.col(col).cast(pl.Float64))
                except Exception as e:
                    if log:
                        log(
                            f"Failed to convert column '{col}' to Float64: {str(e)}",
                            "warning",
                        )

        # Special handling for Allocation [%] and Stop Loss [%] columns
        special_columns = ["Allocation [%]", "Stop Loss [%]"]
        for col in special_columns:
            if col in df.columns:
                try:
                    # Replace string "None" with actual None, then cast to Float64
                    df = df.with_columns(
                        pl.when(pl.col(col).eq("None").or_(pl.col(col).is_null()))
                        .then(pl.lit(None))
                        .otherwise(pl.col(col))
                        .cast(pl.Float64)
                        .alias(col)
                    )
                    if log:
                        log(
                            f"Successfully converted column '{col}' to Float64 with None values",
                            "info",
                        )
                except Exception as e:
                    if log:
                        log(
                            f"Failed to convert column '{col}' to Float64: {str(e)}",
                            "warning",
                        )

        # Log which return metrics are included in the export
        included_metrics = [metric for metric in return_metrics if metric in df.columns]
        missing_metrics = [
            metric for metric in return_metrics if metric not in df.columns
        ]

        if log and missing_metrics:
            log(
                f"Missing return metrics in export: {', '.join(missing_metrics)}",
                "warning",
            )

        # Check if any metrics are present in the DataFrame but have null values
        null_metrics = []
        for metric in included_metrics:
            if df.get_column(metric).null_count() == len(df):
                null_metrics.append(metric)

        if log and null_metrics:
            log(
                f"Return metrics with all null values: {', '.join(null_metrics)}",
                "warning",
            )

        # Default behavior: when feature_dir is empty, use export_type as directory
        # When feature_dir is "strategies", export directly to /data/raw/strategies/
        if feature_dir == "" or feature_dir == "strategies":
            # Skip the export_type (feature2) to avoid creating a subdirectory
            return export_csv(
                data=df,
                feature1=feature1,
                config=config,
                feature2="",  # Empty string to avoid creating a subdirectory
                filename=csv_filename,
                log=log,
                target_schema=target_schema_type,
            )
        else:
            # Legacy case for other feature directories (e.g., ma_cross)
            return export_csv(
                data=df,
                feature1=feature1,
                config=config,
                feature2=export_type,  # Use original export_type to maintain correct subdirectories
                filename=csv_filename,
                log=log,
                target_schema=target_schema_type,
            )
    except Exception as e:
        error_msg = f"Failed to export portfolios: {str(e)}"
        if log:
            log(error_msg, "error")
        raise PortfolioExportError(error_msg) from e
