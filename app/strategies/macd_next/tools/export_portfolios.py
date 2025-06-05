"""
Portfolio Export Module

This module handles the export of portfolio data to CSV files for the
MACD cross strategy using the centralized export functionality.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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


# Use centralized valid export types for consistency
VALID_EXPORT_TYPES = CENTRAL_VALID_EXPORT_TYPES


# Legacy functions removed - now using centralized export system for canonical schema compliance


def export_portfolios(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] | None = None,
    log: Optional[Callable] | None = None,
    feature_dir: str = "macd_next",  # Default to macd_next for backward compatibility
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
        feature_dir (str): Directory for exports (default: "macd_next")

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

    # Ensure MACD-specific enrichment before using centralized export
    enriched_portfolios = _enrich_macd_portfolios(portfolios, config, log)

    # Set STRATEGY_TYPE to MACD for proper filename generation
    export_config = config.copy()
    export_config["STRATEGY_TYPE"] = "MACD"

    if log:
        log(
            f"Using centralized export for {len(enriched_portfolios)} MACD portfolios as {export_type} with canonical schema compliance",
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


def _enrich_macd_portfolios(
    portfolios: List[Dict], config: ExportConfig, log: Optional[Callable] = None
) -> List[Dict]:
    """Enrich MACD portfolios with canonical schema columns.

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

        # Ensure Strategy Type is set to MACD
        enriched["Strategy Type"] = "MACD"

        # Add missing canonical columns with appropriate defaults
        if "Allocation [%]" not in enriched:
            enriched["Allocation [%]"] = None

        if "Stop Loss [%]" not in enriched:
            enriched["Stop Loss [%]"] = None

        if "Metric Type" not in enriched:
            # Generate metric type based on performance if available
            if enriched.get("Score", 0) > 1.0:
                enriched["Metric Type"] = "High Performance MACD"
            else:
                enriched["Metric Type"] = "Standard MACD"

        if "Signal Window" not in enriched:
            enriched["Signal Window"] = 0

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
            f"Enriched {len(portfolios)} MACD portfolios with canonical schema columns",
            "info",
        )

    return enriched_portfolios


def export_best_portfolios(
    portfolios: List[Dict[str, Any]], config: Dict, log: callable
) -> bool:
    """Export the best portfolios to a CSV file using canonical schema.

    The portfolios are sorted by the metric specified in config['SORT_BY'],
    defaulting to 'Total Return [%]' if not specified.

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
            f"Exported {len(portfolios)} MACD portfolios sorted by {sort_by} in {'ascending' if sort_asc else 'descending'} order with canonical schema compliance"
        )
        return True
    except Exception as e:
        log(f"Failed to export MACD portfolios: {str(e)}", "error")
        return False
