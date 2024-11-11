import polars as pl
import logging
from typing import List, Dict, Any
from app.utils import get_path, get_filename

def get_metric_rows(df: pl.DataFrame, metric: str) -> List[Dict[str, Any]]:
    """
    Get metric rows with proper error handling.
    
    Args:
        df: Input DataFrame
        metric: Metric name to process
        
    Returns:
        List of dictionaries containing metric information
    """
    try:
        # Sort by the metric in descending order
        df_sorted = df.sort(metric, descending=True)
        
        if len(df_sorted) == 0:
            return []
            
        # Get the top row
        top_row = df_sorted.row(0)
        
        # Get the bottom row
        bottom_row = df_sorted.row(-1)
        
        # Calculate mean values
        mean_row = df_sorted.mean().row(0)
        
        return [
            {**{'Metric Type': f'Best {metric}'}, **{col: val for col, val in zip(df.columns, top_row)}},
            {**{'Metric Type': f'Worst {metric}'}, **{col: val for col, val in zip(df.columns, bottom_row)}},
            {**{'Metric Type': f'Mean {metric}'}, **{col: val for col, val in zip(df.columns, mean_row)}}
        ]
    except Exception as e:
        logging.error(f"Error processing metric {metric}: {str(e)}")
        return []

def filter_portfolios(df: pl.DataFrame, config: dict) -> pl.DataFrame:
    """
    Filter and analyze portfolios based on various metrics.
    
    Args:
        df: Input DataFrame containing portfolio results
        config: Configuration dictionary
        
    Returns:
        DataFrame containing filtered and analyzed results
    """
    try:
        if len(df) == 0:
            logging.warning("Empty DataFrame provided to filter_portfolios")
            return pl.DataFrame()
            
        metrics = [
            'Total Return [%]',
            'Sharpe Ratio',
            'Calmar Ratio',
            'Max. Drawdown [%]',
            'Avg. Winning Trade [%]',
            'Avg. Losing Trade [%]',
            'Win Rate [%]',
            'Profit Factor',
            'Expectancy',
            'Sortino Ratio',
            'Omega Ratio'
        ]
        
        rows = []
        for metric in metrics:
            if metric in df.columns:
                metric_rows = get_metric_rows(df, metric)
                rows.extend(metric_rows)
        
        if not rows:
            logging.warning("No valid metrics found for filtering")
            return pl.DataFrame()
            
        # Create filtered DataFrame
        filtered_df = pl.DataFrame(rows)
        
        # Export to CSV
        csv_path = get_path("csv", "ma_cross", config, 'portfolios_filtered')
        csv_filename = get_filename("csv", config)
        filtered_df.write_csv(csv_path + "/" + csv_filename)
        
        print(f"\nFiltered portfolios written to {csv_path}")
        print(f"Total rows in filtered output: {len(filtered_df)}")
        
        return filtered_df
        
    except Exception as e:
        logging.error(f"Error in filter_portfolios: {str(e)}")
        return pl.DataFrame()
