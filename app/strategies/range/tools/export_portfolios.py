"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files for the
range strategy using the centralized export functionality with
canonical 59-column schema compliance.
"""

from typing import Callable, Dict, List, Optional, Tuple

import polars as pl

from app.tools.export_csv import ExportConfig, export_csv
from app.tools.strategy.export_portfolios import (
    VALID_EXPORT_TYPES as CENTRAL_VALID_EXPORT_TYPES,
)
from app.tools.strategy.export_portfolios import (
    export_portfolios as central_export_portfolios,
)


class PortfolioExportError(Exception):
    """Custom exception for portfolio export errors."""


def export_best_portfolios(
    portfolios: List[Dict], config: ExportConfig, log: Callable
) -> bool:
    """Export the best range portfolios to a CSV file using canonical schema.

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
        # Use centralized export function for canonical schema compliance
        export_portfolios(
            portfolios=portfolios,
            config=config,
            export_type="portfolios_best",
            log=log,
            feature_dir="",  # Export to portfolios_best directly
        )

        # Get sort parameters from config
        sort_by = config.get("SORT_BY", "Total Return [%]")
        sort_asc = config.get("SORT_ASC", False)

        log(
            f"Exported {len(portfolios)} range portfolios sorted by {sort_by} in {'ascending' if sort_asc else 'descending'} order with canonical schema compliance"
        )
        return True
    except Exception as e:
        log(f"Failed to export range portfolios: {str(e)}", "error")
        return False


# Use centralized valid export types for consistency
VALID_EXPORT_TYPES = CENTRAL_VALID_EXPORT_TYPES


def _enrich_range_portfolios(
    portfolios: List[Dict], config: ExportConfig, log: Optional[Callable] = None
) -> List[Dict]:
    """Enrich range portfolios with canonical schema columns.

    Args:
        portfolios: List of portfolio dictionaries
        config: Export configuration
        log: Optional logging function

    Returns:
        Enriched portfolios with canonical schema columns
    """
    enriched_portfolios = []

    for portfolio in portfolios:
        enriched = portfolio.copy()

        # Ensure Strategy Type is set to Range
        enriched["Strategy Type"] = "Range"

        # Add missing canonical columns with appropriate defaults
        if "Allocation [%]" not in enriched:
            enriched["Allocation [%]"] = None

        if "Stop Loss [%]" not in enriched:
            enriched["Stop Loss [%]"] = None

        if "Metric Type" not in enriched:
            # Generate metric type based on performance if available
            if enriched.get("Score", 0) > 1.0:
                enriched["Metric Type"] = "High Performance Range"
            else:
                enriched["Metric Type"] = "Standard Range"

        if "Signal Window" not in enriched:
            enriched["Signal Window"] = enriched.get(
                "Range Window", 20
            )  # Use range window if available

        if "Short Window" not in enriched:
            enriched["Short Window"] = enriched.get("Range Window", 20)

        if "Long Window" not in enriched:
            enriched["Long Window"] = enriched.get("Range Period", 50)

        # Ensure Ticker is set from config if not present
        if "Ticker" not in enriched and "TICKER" in config:
            ticker = config["TICKER"]
            if isinstance(ticker, str):
                enriched["Ticker"] = ticker
            elif isinstance(ticker, list) and len(ticker) == 1:
                enriched["Ticker"] = ticker[0]

        enriched_portfolios.append(enriched)

    if log:
        log(
            f"Enriched {len(portfolios)} range portfolios with canonical schema columns",
            "info",
        )

    return enriched_portfolios


def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] | None = None,
    log: Optional[Callable] | None = None,
    feature_dir: str = "range",  # Default to range for backward compatibility
) -> Tuple[pl.DataFrame, bool]:
    """Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    This function now uses the centralized export system to ensure canonical
    59-column schema compliance.

    Args:
        portfolios (List[Dict]): List of portfolio dictionaries to export
        config (ExportConfig): Export configuration dictionary
        export_type (str): Type of export (must be one of: portfolios, portfolios_scanner, portfolios_filtered, portfolios_best)
        csv_filename (Optional[str]): Optional custom filename for the CSV
        log (Optional[Callable]): Optional logging function
        feature_dir (str): Directory for exports (default: "range")

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

    # Ensure range-specific enrichment before using centralized export
    enriched_portfolios = _enrich_range_portfolios(portfolios, config, log)

    # Set STRATEGY_TYPE to Range for proper identification
    export_config = config.copy()
    export_config["STRATEGY_TYPE"] = "Range"

    if log:
        log(
            f"Using centralized export for {len(enriched_portfolios)} range portfolios as {export_type} with canonical schema compliance",
            "info",
        )

    # Use centralized export function which handles canonical schema validation
    return central_export_portfolios(
        portfolios=enriched_portfolios,
        config=export_config,
        export_type=export_type,
        csv_filename=csv_filename,
        log=log,
        feature_dir=feature_dir,
    )
