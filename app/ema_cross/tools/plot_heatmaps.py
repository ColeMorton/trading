import logging
import polars as pl
import vectorbt as vbt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from app.utils import get_filename, get_path
import os

# Logging setup
logging.basicConfig(filename='./logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def plot_heatmap(results_pl: pl.DataFrame, config: dict) -> None:
    """
    Plot heatmap of MA cross strategy performance.
    When USE_CURRENT is True, only shows or emphasizes current window combinations.

    Args:
        results_pl: Polars DataFrame with price data
        config: Configuration dictionary

    Returns:
        None
    """
    FREQ = '1D'

    # Check if we have 'Date' or 'Datetime' column
    date_col = 'Datetime' if 'Datetime' in results_pl.columns else 'Date'

    # Extract Date/Datetime and Close price from results_pl
    price_data = results_pl.select([date_col, 'Close']).to_pandas()
    # Rename Close column to ticker name and set index
    price_data.rename(columns={'Close': config["TICKER"]}, inplace=True)
    price_data.set_index(date_col, inplace=True)

    windows = np.arange(2, config["WINDOWS"])
    
    # Use SMA if USE_SMA is True, otherwise use EMA
    use_ewm = not config.get("USE_SMA", False)
    
    if config.get("USE_CURRENT", False):
        # Read current signals file
        filename = f"{config['TICKER']}_D_{'SMA' if config.get('USE_SMA', True) else 'EMA'}.csv"
        filepath = f"csv/ma_cross/current_signals/{filename}"
        
        # Check if file exists and has content
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            print(f"No current signals found for {config['TICKER']}. Displaying full heatmap instead.")
            config["USE_CURRENT"] = False
        else:
            try:
                current_signals = pd.read_csv(filepath)
                if len(current_signals) == 0:
                    print(f"No current signals found for {config['TICKER']}. Displaying full heatmap instead.")
                    config["USE_CURRENT"] = False
                else:
                    # Convert current signals to set of tuples
                    current_windows = set(zip(current_signals['Short Window'].astype(int), 
                                            current_signals['Long Window'].astype(int)))
                    
                    # Create combinations only for current windows
                    window_combs = []
                    for short, long in current_windows:
                        if short in windows and long in windows:
                            window_combs.append((short, long))
                    
                    if not window_combs:
                        print(f"No valid window combinations found for {config['TICKER']}. Displaying full heatmap instead.")
                        config["USE_CURRENT"] = False
                    else:
                        # Sort combinations for consistent ordering
                        window_combs.sort()
                        
                        # Extract short and long windows
                        short_windows, long_windows = zip(*window_combs)
                        
                        # Run MA only for current combinations
                        fast_ma = vbt.MA.run(price_data, list(short_windows), short_name='fast', ewm=use_ewm)
                        slow_ma = vbt.MA.run(price_data, list(long_windows), short_name='slow', ewm=use_ewm)
                        
                        entries = fast_ma.ma_crossed_above(slow_ma)
                        exits = fast_ma.ma_crossed_below(slow_ma)

                        pf_kwargs = dict(size=np.inf, fees=0.001, freq=FREQ)
                        pf = vbt.Portfolio.from_signals(price_data, entries, exits, **pf_kwargs)
                        
                        # Get returns
                        returns = pf.total_return()
                        
                        # Create a matrix of NaN values
                        matrix = np.full((len(windows), len(windows)), np.nan)
                        
                        # Fill in only the current combinations
                        for i, (short, long) in enumerate(window_combs):
                            long_idx = np.where(windows == long)[0][0]
                            short_idx = np.where(windows == short)[0][0]
                            matrix[long_idx, short_idx] = returns.iloc[i]  # Note: swapped indices
                        
                        # Create heatmap using plotly
                        fig = go.Figure(data=go.Heatmap(
                            z=matrix,
                            x=windows,  # Short window on x-axis
                            y=windows,  # Long window on y-axis
                            colorscale='Viridis',
                            colorbar=dict(title='Total return', tickformat='%'),
                            hoverongaps=False
                        ))
                        
                        # Update layout
                        fig.update_layout(
                            title=f'{config['TICKER']} {"SMA" if config.get("USE_SMA", False) else "EMA"} Cross Strategy Returns (Current Signals Only)',
                            xaxis_title='Short Window',  # Changed axis labels
                            yaxis_title='Long Window'
                        )
            except pd.errors.EmptyDataError:
                print(f"No current signals found for {config['TICKER']}. Displaying full heatmap instead.")
                config["USE_CURRENT"] = False
    
    if not config.get("USE_CURRENT", False):
        fast_ma, slow_ma = vbt.MA.run_combs(price_data, window=windows, r=2, 
                                           short_names=['fast', 'slow'], 
                                           ewm=use_ewm)
        
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)

        pf_kwargs = dict(size=np.inf, fees=0.001, freq=FREQ)
        pf = vbt.Portfolio.from_signals(price_data, entries, exits, **pf_kwargs)
        
        # Get returns and create proper index
        returns = pf.total_return()
        # Swap the order in the MultiIndex to put short window first
        returns.index = pd.MultiIndex.from_tuples(
            [(idx[2], idx[0]) for idx in returns.index],  # Swap the order
            names=['slow_window', 'fast_window']  # Swap the names
        )
        
        # Create heatmap
        fig = returns.vbt.heatmap(
            symmetric=True,
            trace_kwargs=dict(
                colorscale='Viridis',
                colorbar=dict(title='Total return', tickformat='%'),
                showscale=True
            )
        )
        # Update axis labels
        fig.update_layout(
            xaxis_title='Short Window',
            yaxis_title='Long Window'
        )

    # Save the plot
    png_path = get_path("png", "ema_cross", config, 'heatmap')
    png_filename = get_filename("png", config)
    
    # Save as PNG
    fig.write_image(png_path + "/" + png_filename)
    
    logging.info(f"Plot saved as {png_path + "/" + png_filename}")
    fig.show()
