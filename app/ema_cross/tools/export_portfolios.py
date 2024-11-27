import os
from datetime import datetime
import polars as pl
from typing import List, Dict, Tuple, Callable
from app.utils import get_path, get_filename

def export_portfolios(
    portfolios: List[Dict], 
    config: Dict, 
    export_type: str, 
    csv_filename: str | None,
    log: Callable
) -> Tuple[pl.DataFrame, bool]:
    """
    Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        export_type: Type of export (e.g., 'portfolios_summary', 'portfolios_filtered')
        csv_filename: Optional custom filename for the CSV
        log: Logging function for recording events and errors

    Returns:
        Tuple of (DataFrame, success status)
    """
    try:
        if not portfolios:
            log("No portfolios to export", "warning")
            return pl.DataFrame(), False

        # Convert list of dictionaries to Polars DataFrame
        portfolios_df = pl.DataFrame(portfolios)

        # Create export directory if it doesn't exist
        csv_path = get_path("csv", "ma_cross", config, export_type)
        
        # If USE_CURRENT is True, create a date subdirectory
        if config.get("USE_CURRENT", False):
            today = datetime.now().strftime("%Y%m%d")
            csv_path = os.path.join(csv_path, today)
        
        os.makedirs(csv_path, exist_ok=True)
        
        # Export results to CSV
        if csv_filename is None:
            csv_filename = get_filename("csv", config)
        full_path = os.path.join(csv_path, csv_filename)
        portfolios_df.write_csv(full_path)
        log(f"Successfully exported results to {full_path}")
        
        return portfolios_df, True
        
    except Exception as e:
        log(f"Failed to export portfolios: {e}", "error")
        return pl.DataFrame(), False
