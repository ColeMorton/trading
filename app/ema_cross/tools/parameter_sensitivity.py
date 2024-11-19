import polars as pl
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
from app.utils import get_path, get_filename
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ema_cross.tools.signal_generation import is_signal_current
from app.tools.file_utils import convert_stats
from app.ema_cross.tools.backtest_strategy import backtest_strategy

def analyze_parameter_sensitivity(
    data: pl.DataFrame,
    short_windows: List[int],
    long_windows: List[int],
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
                        converted_stats['Current'] = int(current)
                        portfolios.append(converted_stats)
                    except Exception as e:
                        logging.warning(f"Failed to process windows {short}, {long}: {str(e)}")
                        continue

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
