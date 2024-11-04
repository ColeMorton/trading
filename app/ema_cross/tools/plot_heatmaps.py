import logging
import polars as pl
import vectorbt as vbt
import numpy as np
from app.utils import get_filename, get_path

# Logging setup
logging.basicConfig(filename='./logs/ema_cross.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def plot_heatmap(results_pl: pl.DataFrame, config: dict) -> None:
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
    fast_ma, slow_ma = vbt.MA.run_combs(price_data, window=windows, r=2, short_names=['fast', 'slow'], ewm=use_ewm)
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)

    pf_kwargs = dict(size=np.inf, fees=0.001, freq=FREQ)
    pf = vbt.Portfolio.from_signals(price_data, entries, exits, **pf_kwargs)

    fig = pf.total_return().vbt.heatmap(
        x_level='fast_window', y_level='slow_window', symmetric=True,
        trace_kwargs=dict(colorbar=dict(title='Total return', tickformat='%')))

    # Save the plot with the correct filename
    # plot_filename = get_filename("png", config)
    png_path = get_path("png", "ema_cross", config, 'heatmap')
    png_filename = get_filename("png", config)
    
    # Now save as PNG
    fig.write_image(png_path + "/" + png_filename)
    
    logging.info(f"Plot saved as {png_path + "/" + png_filename}")
    fig.show()

# def plot_heatmaps(results_pl: pl.DataFrame, ticker: str, config: dict) -> None:
#     """Plot heatmaps of the results."""
#     logging.info("Plotting heatmaps")
#     try:
#         # Create a single subplot with increased figure size
#         fig, ax = plt.subplots(figsize=(14, 10))
        
#         # Set background color to white
#         fig.patch.set_facecolor('white')
#         ax.set_facecolor('white')
        
#         # Convert polars DataFrames to pandas DataFrames
#         results_pd = results_pl.to_pandas()
        
#         # Pivot the data for heatmap plotting
#         results_return_pivot = results_pd.pivot(index="Short Window", columns="Long Window", values="Total Return [%]")
        
#         # Create mask for current values
#         current_mask = results_pd.pivot(index="Short Window", columns="Long Window", values="Current")
        
#         # Check if there are any current signals
#         has_current_signals = (current_mask == 1).any().any()
        
#         # Only apply mask if SHOW_CURRENT is True and there are current signals
#         if config.get('SHOW_CURRENT', False) == True and has_current_signals:
#             plot_mask = current_mask != 1
#         else:
#             plot_mask = None
        
#         # Remove rows and columns with all NaN values
#         results_return_pivot = results_return_pivot.dropna(how='all').dropna(axis=1, how='all')
        
#         # Check if DataFrames are empty
#         if results_return_pivot.empty:
#             logging.warning("Pivot table is empty after removing NaN values. Unable to plot heatmap.")
#             return
        
#         # Create custom colormap with better contrast
#         cmap = sns.color_palette("YlOrRd", as_cmap=True)
        
#         # Plot heatmaps with masked annotations
#         sns.heatmap(results_return_pivot, 
#                    annot=True, 
#                    fmt=".0f", # Round to whole numbers for better readability
#                    cmap=cmap,
#                    cbar_kws={'label': 'Total Return [%]'},
#                    ax=ax,
#                    mask=plot_mask,
#                    annot_kws={"size": 9, "alpha": 1})
        
#         timeframe = "Hourly" if config["USE_HOURLY"] else "Daily"
#         ma_type = "SMA" if config["USE_SMA"] else "EMA"
#         ax.set_title(f'Parameter Sensitivity Analysis\n{ma_type} Cross Strategy ({timeframe}) for {ticker}', 
#                     pad=20, size=14, weight='bold')
#         ax.set_xlabel('Long Window Period', size=12)
#         ax.set_ylabel('Short Window Period', size=12)
        
#         # Rotate x-axis labels for better readability
#         plt.xticks(rotation=0)
#         plt.yticks(rotation=0)
        
#         # Add grid for better readability
#         ax.grid(False)
        
#         plt.tight_layout()
        
#         # Save the plot with the correct filename
#         plot_filename = get_filename("png", config)
#         plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
#         logging.info(f"Plot saved as {plot_filename}")

#         plt.show()
        
#     except Exception as e:
#         logging.error(f"Failed to plot heatmaps: {e}")
#         raise
