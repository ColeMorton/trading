import logging
import polars as pl
from typing import Dict, Any, Optional
from app.utils import get_path, get_filename
from app.ema_cross.tools.sensitivity_analysis import analyze_parameter_combinations

def analyze_parameter_sensitivity(
    data: pl.DataFrame,
    short_windows: list[int],
    long_windows: list[int],
    config: Dict[str, Any]
) -> Optional[pl.DataFrame]:
    """
    Perform parameter sensitivity analysis and export results.
    
    Args:
        data: Price data DataFrame
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
        
    Returns:
        Optional[pl.DataFrame]: DataFrame containing portfolio results, None if analysis fails
    """
    logging.info("Starting parameter sensitivity analysis")
    try:
        # Analyze all parameter combinations
        portfolios = analyze_parameter_combinations(data, short_windows, long_windows, config)

        if not portfolios:
            logging.warning("No valid portfolios generated")
            return None

        # Create DataFrame and sort by Total Return
        df = pl.DataFrame(portfolios)
        df = df.sort("Total Return [%]", descending=True)

        # Export results
        export_results(df, config)
        
        return df
            
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        return None

def export_results(df: pl.DataFrame, config: Dict[str, Any]) -> None:
    """
    Export analysis results to CSV.
    
    Args:
        df: DataFrame containing analysis results
        config: Configuration dictionary
    """
    try:
        csv_path = get_path("csv", "ma_cross", config, 'portfolios')
        csv_filename = get_filename("csv", config)
        full_path = f"{csv_path}/{csv_filename}"
        
        df.write_csv(full_path)
        logging.info(f"Analysis results exported to {full_path}")
        print(f"Analysis complete. Results written to {csv_path}")
        print(f"Total rows in output: {len(df)}")
        
    except Exception as e:
        logging.error(f"Failed to export results: {e}")
