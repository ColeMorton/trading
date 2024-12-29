import os
from typing import Callable, Tuple
import polars as pl
from app.tools.data_types import DataConfig
from app.tools.download_data import download_data
from app.tools.export_csv import export_csv, ExportConfig

def use_synthetic(ticker1: str, ticker2: str, config: DataConfig, log: Callable) -> Tuple[pl.DataFrame, str]:
    """Create a synthetic pair from two tickers.
    
    Args:
        ticker1 (str): First ticker symbol
        ticker2 (str): Second ticker symbol
        config (DataConfig): Configuration dictionary
        log (Callable): Logging function
        
    Returns:
        Tuple[pl.DataFrame, str]: Synthetic pair data and synthetic ticker name
    """
    try:
        log(f"Creating synthetic pair from {ticker1} and {ticker2}")
        
        log(f"Downloading data for {ticker1}")
        data_ticker_1 = download_data(ticker1, config, log)
        
        log(f"Downloading data for {ticker2}")
        data_ticker_2 = download_data(ticker2, config, log)

        log("Merging data from both tickers")
        data_merged = data_ticker_1.join(data_ticker_2, on='Date', how='inner', suffix="_2")
        log(f"Merged data contains {len(data_merged)} rows")

        log("Calculating synthetic pair ratios")
        data = pl.DataFrame({
            'Date': data_merged['Date'],
            'Close': (data_merged['Close'] / data_merged['Close_2']).cast(pl.Float64),
            'Open': (data_merged['Open'] / data_merged['Open_2']).cast(pl.Float64),
            'High': (data_merged['High'] / data_merged['High_2']).cast(pl.Float64),
            'Low': (data_merged['Low'] / data_merged['Low_2']).cast(pl.Float64),
            'Volume': data_merged['Volume'].cast(pl.Float64)  # Keep original volume
        })

        log(f"Synthetic pair statistics:")
        log(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
        log(f"Ratio range: {data['Close'].min():.4f} to {data['Close'].max():.4f}")

        synthetic_ticker = f"{ticker1}/{ticker2}"
        
        # Export synthetic pair data directly with custom filename
        export_path = os.path.join(config.get('BASE_DIR', '.'), 'csv', 'price_data')
        os.makedirs(export_path, exist_ok=True)
        
        # Create custom filename in format: {ticker1}_{ticker2}_{timeframe}.csv
        timeframe = "H" if config.get('USE_HOURLY', False) else "D"
        filename = f"{ticker1}_{ticker2}_{timeframe}.csv"
        full_path = os.path.join(export_path, filename)
        
        log("Exporting synthetic pair data to CSV")
        try:
            # Remove existing file if it exists
            if os.path.exists(full_path):
                os.remove(full_path)
            
            # Export data
            data.write_csv(full_path, separator=",")
            log(f"Successfully exported results to {full_path}")
            success = True
        except Exception as e:
            log(f"Failed to export synthetic pair data: {str(e)}", "error")
            success = False
        
        if success:
            log(f"Synthetic pair data exported successfully as {filename}")
        else:
            log("Failed to export synthetic pair data", "error")

        # Return the data and synthetic ticker for further processing
        if success:
            return data, synthetic_ticker
        else:
            log("Failed to create synthetic pair", "error")
            return pl.DataFrame(), ""

    except Exception as e:
        log(f"Error in use_synthetic: {str(e)}", "error")
        raise
