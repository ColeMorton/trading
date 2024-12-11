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
        
        # Export synthetic pair data to CSV
        export_config: ExportConfig = {
            'BASE_DIR': config.get('BASE_DIR', '.'),
            'TICKER': synthetic_ticker,
            'USE_HOURLY': config.get('USE_HOURLY', False),
            'USE_MA': False
        }
        
        log("Exporting synthetic pair data to CSV")
        data, export_path = export_csv(
            data=data,
            feature1='price_data',
            config=export_config
        )
        log(f"Synthetic pair data exported successfully to {export_path}")

        return data, synthetic_ticker

    except Exception as e:
        log(f"Error in use_synthetic: {str(e)}", "error")
        raise
