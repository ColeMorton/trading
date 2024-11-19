import os
import polars as pl
from typing import List, Dict, Tuple
from app.utils import get_path, get_filename
from app.tools.setup_logging import setup_logging

# Get the absolute path to the project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# Setup logging
log_dir = os.path.join(project_root, 'logs', 'ma_cross')
log, log_close, _, _ = setup_logging('ma_cross', log_dir, 'export_portfolios.log')

def export_portfolios(portfolios: List[Dict], config: Dict, export_type, csv_filename: None) -> Tuple[pl.DataFrame, bool]:
    """
    Convert portfolio dictionaries to Polars DataFrame and export to CSV.

    Args:
        portfolios: List of portfolio dictionaries
        config: Configuration dictionary
        export_type: Type of export (e.g., 'portfolios_summary', 'portfolios_filtered')

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
