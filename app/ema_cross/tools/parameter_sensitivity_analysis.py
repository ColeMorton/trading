import polars as pl
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd
import logging
from app.utils import get_path, get_filename
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ema_cross.tools.get_current_signals import is_signal_current
from app.ema_cross.tools.convert_stats import convert_stats
from app.ema_cross.tools.backtest_strategy import backtest_strategy

def parameter_sensitivity_analysis(data: pl.DataFrame, short_windows: List[int], long_windows: List[int], config: dict) -> pl.DataFrame:
    """
    Perform parameter sensitivity analysis.
    
    Args:
        data: Price data
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
        
    Returns:
        DataFrame containing portfolio results for different parameter combinations
    """
    logging.info("Starting parameter sensitivity analysis")
    try:
        portfolios = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    try:
                        temp_data = data.clone()
                        # Handle data quality
                        if len(temp_data) < max(short, long):
                            logging.warning(f"Insufficient data for windows {short}, {long}")
                            continue
                            
                        temp_data = calculate_ma_and_signals(temp_data, short, long, config)
                        if temp_data is None or len(temp_data) == 0:
                            logging.warning(f"No signals generated for windows {short}, {long}")
                            continue
                            
                        current = is_signal_current(temp_data)
                        portfolio = backtest_strategy(temp_data, config)

                        stats = portfolio.stats()
                        stats['Short Window'] = short
                        stats['Long Window'] = long
                        converted_stats = convert_stats(stats)
                        converted_stats['Current'] = int(current)  # Ensure Current is an integer
                        portfolios.append(converted_stats)
                    except Exception as e:
                        logging.warning(f"Failed to process windows {short}, {long}: {str(e)}")
                        continue

        logging.info("Parameter sensitivity analysis completed successfully")

        if not portfolios:
            logging.warning("No valid portfolios generated")
            return pl.DataFrame()

        try:
            # Create DataFrame with explicit schema for numeric columns
            df = pl.DataFrame(portfolios)
            
            # Sort portfolios by Total Return [%] in descending order
            df = df.sort("Total Return [%]", descending=True)

            # Export to CSV
            csv_path = get_path("csv", "ma_cross", config, 'portfolios')
            csv_filename = get_filename("csv", config)
            df.write_csv(csv_path + "/" + csv_filename)

            print(f"Analysis complete. Portfolios written to {csv_path}")
            print(f"Total rows in output: {len(df)}")

            return df
            
        except Exception as e:
            logging.error(f"Failed to create DataFrame: {e}")
            # Return empty DataFrame if conversion fails
            return pl.DataFrame()
            
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise
