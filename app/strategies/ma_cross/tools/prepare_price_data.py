import pandas as pd
import polars as pl


def prepare_prices(results_pl: pl.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Prepare price data for vectorbt analysis by converting Polars DataFrame to Pandas.
    Conversion to Pandas is necessary for vectorbt compatibility.

    Args:
        results_pl: Polars DataFrame with price data
        ticker: Ticker symbol

    Returns:
        Pandas DataFrame with date index and price column
    """
    date_col = "Datetime" if "Datetime" in results_pl.columns else "Date"

    # Keep data in Polars format until final conversion
    prices_pl = results_pl.select([pl.col(date_col), pl.col("Close").alias(ticker)])

    # Convert to pandas only at the end (required for vectorbt)
    prices_pd = prices_pl.to_pandas()
    prices_pd = prices_pd.set_index(date_col)
    return prices_pd
