"""
Export System Adapters

This module provides adapters to maintain backward compatibility with existing
export functions while using the new unified export system.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd
import polars as pl

from app.tools.export.interfaces import ExportContext, ExportFormat, ExportResult
from app.tools.export.manager import ExportManager
from app.tools.export_csv import ExportConfig

# Global export manager instance
_manager = ExportManager()


def export_csv_adapter(
    data: Union[pl.DataFrame, pd.DataFrame, List[Dict]],
    feature1: str,
    config: ExportConfig,
    feature2: str = "",
    filename: Optional[str] = None,
    log: Optional[Callable] = None,
) -> Tuple[pl.DataFrame, bool]:
    """Adapter for the legacy export_csv function.

    This function maintains backward compatibility with the existing export_csv
    interface while using the new unified export system.

    Args:
        data: Data to export (DataFrame or list of dictionaries)
        feature1: Primary feature directory
        config: Export configuration dictionary
        feature2: Secondary feature directory (optional)
        filename: Optional custom filename
        log: Optional logging function

    Returns:
        Tuple of (DataFrame, success status)
    """
    # Build feature path
    feature_path = feature1
    if feature2:
        feature_path = f"{feature1}/{feature2}"

    # Create export context
    context = ExportContext(
        data=data,
        format=ExportFormat.CSV,
        feature_path=feature_path,
        config=config,
        filename=filename,
        log=log,
    )

    # Export using the new system
    result = _manager.export(context)

    # Convert result to legacy format
    if result.success:
        # Return the original data as DataFrame
        if isinstance(data, pl.DataFrame):
            return data, True
        elif isinstance(data, pd.DataFrame):
            return pl.DataFrame(data), True
        elif isinstance(data, list):
            return pl.DataFrame(data), True
        else:
            return pl.DataFrame(), True
    else:
        return pl.DataFrame(), False


def export_portfolios_adapter(
    portfolios: List[Dict],
    config: ExportConfig,
    export_type: str,
    csv_filename: Optional[str] = None,
    log: Optional[Callable] = None,
    feature_dir: str = "",
) -> Tuple[pl.DataFrame, bool]:
    """Adapter for the legacy export_portfolios function.

    This function provides a bridge between the existing portfolio export
    interface and the new unified export system.

    Args:
        portfolios: List of portfolio dictionaries to export
        config: Export configuration dictionary
        export_type: Type of export (portfolios, portfolios_filtered, etc.)
        csv_filename: Optional custom filename for the CSV
        log: Optional logging function
        feature_dir: Directory to export to

    Returns:
        Tuple[pl.DataFrame, bool]: (DataFrame of exported data, success status)
    """
    # Import here to avoid circular dependency
    from app.tools.strategy.export_portfolios import export_portfolios

    # For now, delegate to the existing implementation
    # In a future phase, we can fully migrate this to use ExportManager
    return export_portfolios(
        portfolios=portfolios,
        config=config,
        export_type=export_type,
        csv_filename=csv_filename,
        log=log,
        feature_dir=feature_dir,
    )


def save_json_report_adapter(
    report: Dict[str, Any],
    config: Dict[str, Any],
    log: Callable[[str, str], None],
    json_encoder: Optional[type] = None,
) -> str:
    """Adapter for saving JSON reports.

    This function provides compatibility with the existing JSON report
    saving interface while using the new export system.

    Args:
        report: Report data to save
        config: Configuration dictionary
        log: Logging function
        json_encoder: Optional custom JSON encoder class

    Returns:
        str: Path where report was saved

    Raises:
        IOError: If saving fails
    """
    # Build feature path
    feature_path = "concurrency"

    # Get filename from config
    if "PORTFOLIO" in config:
        from pathlib import Path

        portfolio_filename = Path(config["PORTFOLIO"]).stem
        filename = f"{portfolio_filename}.json"
    else:
        filename = "report.json"

    # Create export context
    context = ExportContext(
        data=report,
        format=ExportFormat.JSON,
        feature_path=feature_path,
        config={"BASE_DIR": "."},  # Use current directory as base
        filename=filename,
        log=log,
        json_encoder=json_encoder,
        indent=4,
    )

    # Export using the new system
    result = _manager.export(context)

    if result.success:
        return result.path
    else:
        raise IOError(f"Failed to save report: {result.error_message}")


def migrate_to_export_manager(
    data: Any,
    export_format: str,
    config: Dict[str, Any],
    feature_path: str = "",
    filename: Optional[str] = None,
    log: Optional[Callable] = None,
    **kwargs,
) -> ExportResult:
    """Helper function to migrate existing code to use ExportManager.

    This function provides a simple migration path for existing code
    to start using the new export system.

    Args:
        data: Data to export
        export_format: Format to export to ("csv" or "json")
        config: Export configuration
        feature_path: Feature path for organizing exports
        filename: Optional custom filename
        log: Optional logging function
        **kwargs: Additional arguments for ExportContext

    Returns:
        ExportResult with status and details
    """
    # Create export context
    context = ExportContext(
        data=data,
        format=export_format,
        feature_path=feature_path,
        config=config,
        filename=filename,
        log=log,
        **kwargs,
    )

    # Export using the manager
    return _manager.export(context)
