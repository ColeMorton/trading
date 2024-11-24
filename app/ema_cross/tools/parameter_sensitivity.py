import polars as pl
import os
from typing import Dict, Any, Optional
from app.ema_cross.tools.sensitivity_analysis import analyze_parameter_combinations
from app.tools.setup_logging import setup_logging
from app.tools.export_csv import export_csv

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
    # Setup logging
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    log_dir = os.path.join(project_root, 'logs', 'ma_cross')
    log, log_close, _, _ = setup_logging('ma_cross', 'parameter_sensitivity.log', log_subdir=log_dir)
    
    try:
        log("Starting parameter sensitivity analysis")
        
        # Analyze all parameter combinations
        portfolios = analyze_parameter_combinations(data, short_windows, long_windows, config)

        if not portfolios:
            log("No valid portfolios generated", "warning")
            log_close()
            return None

        # Create DataFrame and sort by Total Return
        df = pl.DataFrame(portfolios)
        df = df.sort("Total Return [%]", descending=True)

        # Export results
        export_results(df, config, log)
        
        log_close()
        return df
            
    except Exception as e:
        log(f"Parameter sensitivity analysis failed: {e}", "error")
        log_close()
        return None

def export_results(df: pl.DataFrame, config: Dict[str, Any], log: callable) -> None:
    """
    Export analysis results to CSV.
    
    Args:
        df: DataFrame containing analysis results
        config: Configuration dictionary
        log: Logging function
    """
    try:
        log(f"Exporting results for {config.get('TICKER', '')}")
        log(f"USE_HOURLY: {config.get('USE_HOURLY', False)}")
        log(f"USE_SMA: {config.get('USE_SMA', False)}")
        
        # Export using centralized CSV export functionality
        export_csv(df, "ma_cross", config, "portfolios")
        
        log(f"Analysis results exported successfully")
        print(f"Analysis complete. Total rows in output: {len(df)}")
        
    except Exception as e:
        log(f"Failed to export results: {e}", "error")
        raise
