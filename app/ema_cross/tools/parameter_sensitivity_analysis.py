import polars as pl
from datetime import datetime
from typing import List
import pandas as pd
import vectorbt as vbt
import logging
from app.utils import get_path, get_filename
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ema_cross.tools.get_current_signals import is_signal_current

# Convert stats to compatible format
def convert_stats(stats):
    converted = {}
    # Add short_window and long_window first if they exist in stats
    if 'Short Window' in stats:
        converted['Short Window'] = stats['Short Window']
    if 'Long Window' in stats:
        converted['Long Window'] = stats['Long Window']
    
    # Then add the rest of the stats
    for k, v in stats.items():
        if k not in ['Short Window', 'Long Window']:  # Skip these since we already added them
            if k == 'Start' or k == 'End':
                converted[k] = v.strftime('%Y-%m-%d %H:%M:%S') if isinstance(v, datetime) else str(v)
            elif isinstance(v, pd.Timedelta):
                converted[k] = str(v)
            else:
                converted[k] = v
    return converted

def backtest_strategy(data: pl.DataFrame, config: dict) -> vbt.Portfolio:
    """Backtest the MA cross strategy."""
    try:
        freq = 'h' if config.get('USE_HOURLY', False) else 'D'
        
        # Convert polars DataFrame to pandas DataFrame for vectorbt
        data_pd = data.to_pandas()
        
        if config.get('SHORT', False):
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                short_entries=data_pd['Signal'] == 1,
                short_exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        else:
            portfolio = vbt.Portfolio.from_signals(
                close=data_pd['Close'],
                entries=data_pd['Signal'] == 1,
                exits=data_pd['Signal'] == 0,
                init_cash=1000,
                fees=0.001,
                freq=freq
            )
        
        logging.info("Backtest completed successfully")
        return portfolio
    except Exception as e:
        logging.error(f"Backtest failed: {e}")
        raise

def parameter_sensitivity_analysis(data: pl.DataFrame, short_windows: List[int], long_windows: List[int], config: dict) -> List[pl.DataFrame]:
    """Perform parameter sensitivity analysis."""
    logging.info("Starting parameter sensitivity analysis")
    try:
        portfolios = []
        
        for short in short_windows:
            for long in long_windows:
                if short < long:
                    temp_data = data.clone()
                    temp_data = calculate_ma_and_signals(temp_data, short, long, config)
                    current = is_signal_current(temp_data)
                    portfolio = backtest_strategy(temp_data, config)

                    stats = portfolio.stats()
                    stats['Short Window'] = short
                    stats['Long Window'] = long
                    converted_stats = convert_stats(stats)
                    converted_stats['Current'] = 1 if current else 0
                    portfolios.append(converted_stats)

        logging.info("Parameter sensitivity analysis completed successfully")

        portfolios = pl.DataFrame(portfolios)
        
        # Sort portfolios by Total Return [%] in descending order
        portfolios = portfolios.sort("Total Return [%]", descending=True)

        # Export to CSV
        csv_path = get_path("csv", "ma_cross", config, 'portfolios')
        csv_filename = get_filename("csv", config)
        portfolios.write_csv(csv_path + "/" + csv_filename)

        print(f"Analysis complete. Portfolios written to {csv_path}")
        print(f"Total rows in output: {len(portfolios)}")

        return portfolios
    except Exception as e:
        logging.error(f"Parameter sensitivity analysis failed: {e}")
        raise
