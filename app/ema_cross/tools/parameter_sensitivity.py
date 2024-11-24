import polars as pl
import os
from typing import Dict, Any, Optional
from app.ema_cross.tools.sensitivity_analysis import analyze_parameter_combinations
from app.tools.setup_logging import setup_logging

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
    log, log_close, _, _ = setup_logging('ma_cross', log_dir, 'parameter_sensitivity.log')
    
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
        # Get absolute paths
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
        portfolios_dir = os.path.join(project_root, 'csv', 'ma_cross', 'portfolios')
        
        # Ensure directory exists
        os.makedirs(portfolios_dir, exist_ok=True)
        
        # Log directory info
        log(f"Project root: {project_root}")
        log(f"Portfolios directory: {portfolios_dir}")
        log(f"Directory exists: {os.path.exists(portfolios_dir)}")
        log(f"Directory is writable: {os.access(portfolios_dir, os.W_OK)}")
        
        # Construct filename
        ticker = config.get("TICKER", "")
        use_hourly = config.get("USE_HOURLY", False)
        use_sma = config.get("USE_SMA", False)
        
        filename = f"{ticker}_{'H' if use_hourly else 'D'}_{'SMA' if use_sma else 'EMA'}.csv"
        full_path = os.path.join(portfolios_dir, filename)
        
        # Log file info
        log(f"Exporting results for {ticker}")
        log(f"USE_HOURLY: {use_hourly}")
        log(f"USE_SMA: {use_sma}")
        log(f"Full path: {full_path}")
        
        # Save file
        df.write_csv(full_path)
        
        # Verify file was created
        log(f"File exists after save: {os.path.exists(full_path)}")
        log(f"File size: {os.path.getsize(full_path) if os.path.exists(full_path) else 'N/A'}")
        
        log(f"Analysis results exported successfully")
        print(f"Analysis complete. Results written to {portfolios_dir}")
        print(f"Total rows in output: {len(df)}")
        
    except Exception as e:
        log(f"Failed to export results: {e}", "error")
        raise
