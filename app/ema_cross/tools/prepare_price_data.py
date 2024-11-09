import pandas as pd
import polars as pl

def prepare_price_data(results_pl: pl.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Prepare price data for vectorbt analysis by converting Polars DataFrame to Pandas.
    Conversion to Pandas is necessary for vectorbt compatibility.

    Args:
        results_pl: Polars DataFrame with price data
        ticker: Ticker symbol

    Returns:
        Pandas DataFrame with date index and price column
    """
    date_col = 'Datetime' if 'Datetime' in results_pl.columns else 'Date'
    
    # Keep data in Polars format until final conversion
    price_data_pl = results_pl.select([
        pl.col(date_col),
        pl.col('Close').alias(ticker)
    ])
    
    # Convert to pandas only at the end (required for vectorbt)
    price_data_pd = price_data_pl.to_pandas()
    price_data_pd.set_index(date_col, inplace=True)
    return price_data_pd