"""
Portfolio Selection Module

This module handles the selection of the best portfolio based on consistent
Short Window/Long Window combinations in top performing portfolios.
"""

from typing import Optional
import polars as pl
from app.ema_cross.config_types import PortfolioConfig

def get_best_portfolio(portfolios: pl.DataFrame, config: PortfolioConfig, log: callable) -> Optional[dict]:
    """
    Get the best portfolio based on Short Window/Long Window combination frequency in top performers.
    
    The function analyzes the top performing portfolios to find the most consistent
    Short Window/Long Window combination using three criteria:
    1. If the top 3 portfolios have the same combination
    2. If 3 out of top 5 portfolios have the same combination
    3. If 5 out of top 8 portfolios have the same combination
    
    Args:
        portfolios (pl.DataFrame): DataFrame containing portfolio results
        config (PortfolioConfig): Configuration dictionary
        log (callable): Logging function
        
    Returns:
        Optional[dict]: Best portfolio if found, None otherwise
        
    Raises:
        ValueError: If portfolios DataFrame is empty or missing required columns
    """
    try:
        if portfolios is None or portfolios.height == 0:
            log("No portfolios provided for analysis", "error")
            return None
            
        sort_by = config.get('SORT_BY', 'Total Return [%]')
        required_cols = ["Short Window", "Long Window", sort_by]
        if not all(col in portfolios.columns for col in required_cols):
            log("Missing required columns in portfolios DataFrame", "error")
            return None
            
        # Sort portfolios by Total Return in descending order
        sorted_portfolios = portfolios.sort(sort_by, descending=True)
        
        # Get top portfolios for analysis
        top_3 = sorted_portfolios.head(3)
        top_5 = sorted_portfolios.head(5)
        top_8 = sorted_portfolios.head(8)
        
        # Function to check if combination appears enough times
        def check_combination_frequency(df: pl.DataFrame, required_count: int) -> Optional[tuple]:
            combinations = df.select(["Short Window", "Long Window"]).to_dicts()
            combo_count = {}
            for combo in combinations:
                key = (combo["Short Window"], combo["Long Window"])
                combo_count[key] = combo_count.get(key, 0) + 1
                if combo_count[key] >= required_count:
                    return key
            return None
            
        # Check each criterion
        # 1. All top 3 have same combination
        if (result := check_combination_frequency(top_3, 3)):
            log(f"Found matching combination in top 3: SW={result[0]}, LW={result[1]}")
            portfolio = sorted_portfolios.filter(
                (pl.col("Short Window") == result[0]) &
                (pl.col("Long Window") == result[1])
            ).head(1).to_dicts()[0]
            
            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]
                
            return portfolio
            
        # 2. 3 out of top 5 have same combination
        if (result := check_combination_frequency(top_5, 3)):
            log(f"Found matching combination in top 5: SW={result[0]}, LW={result[1]}")
            portfolio = sorted_portfolios.filter(
                (pl.col("Short Window") == result[0]) &
                (pl.col("Long Window") == result[1])
            ).head(1).to_dicts()[0]
            
            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]
                
            return portfolio
            
        # 3. 5 out of top 8 have same combination
        if (result := check_combination_frequency(top_8, 5)):
            log(f"Found matching combination in top 8: SW={result[0]}, LW={result[1]}")
            portfolio = sorted_portfolios.filter(
                (pl.col("Short Window") == result[0]) &
                (pl.col("Long Window") == result[1])
            ).head(1).to_dicts()[0]
            
            # Remove "Metric Type" column if it exists
            if "Metric Type" in portfolio:
                del portfolio["Metric Type"]
                
            return portfolio
            
        log("No consistent Short Window/Long Window combination found")
        return None
        
    except Exception as e:
        log(f"Error in get_best_portfolio: {str(e)}", "error")
        return None
