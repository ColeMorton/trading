import polars as pl
from typing import Dict, Any, Optional, Callable
from app.ma_cross.tools.sensitivity_analysis import analyze_parameter_combinations
# Import export_portfolios inside functions to avoid circular imports
from app.tools.portfolio.collection import sort_portfolios

def analyze_parameter_sensitivity(
    data: pl.DataFrame,
    short_windows: list[int],
    long_windows: list[int],
    config: Dict[str, Any],
    log: Callable
) -> Optional[pl.DataFrame]:
    """
    Perform parameter sensitivity analysis and export results.
    
    Args:
        data: Price data DataFrame
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        Optional[pl.DataFrame]: DataFrame containing portfolio results, None if analysis fails
    """
    try:
        log("Starting parameter sensitivity analysis")
        
        # Analyze all parameter combinations
        portfolios = analyze_parameter_combinations(data, short_windows, long_windows, config, log)

        if not portfolios:
            log("No valid portfolios generated", "warning")
            return None

        # Create DataFrame and use centralized sorting
        df = pl.DataFrame(portfolios)
        df = sort_portfolios(df, config)

        # Export results
        export_results(df, config, log)
        
        return df
            
    except Exception as e:
        log(f"Parameter sensitivity analysis failed: {e}", "error")
        return None

def export_results(df: pl.DataFrame, config: Dict[str, Any], log: Callable) -> None:
    """
    Export analysis results to CSV.
    
    Args:
        df: DataFrame containing analysis results
        config: Configuration dictionary
        log: Logging function for recording events and errors
    """
    try:
        log(f"Exporting results for {config.get('TICKER', '')}")
        log(f"USE_HOURLY: {config.get('USE_HOURLY', False)}")
        log(f"USE_SMA: {config.get('USE_SMA', False)}")
        # Import export_portfolios here to avoid circular imports
        from app.ma_cross.tools.export_portfolios import export_portfolios
        
        # Export using centralized portfolio export functionality
        export_portfolios(
            portfolios=df.to_dicts(),
            config=config,
            export_type="portfolios",
            log=log
        )
        
        log(f"Analysis results exported successfully")
        print(f"Analysis complete. Total rows in output: {len(df)}")
        
    except Exception as e:
        log(f"Failed to export results: {e}", "error")
        raise
