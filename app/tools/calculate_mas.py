import polars as pl
import pandas as pd

def calculate_mas(data: pl.DataFrame, fast_window: int, slow_window: int, use_sma: bool = False) -> pl.DataFrame:
    """Calculate Moving Averages (SMA or EMA)."""
    # Convert to pandas for calculations
    df = data.to_pandas()
    
    # Ensure numeric type for Close column
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    
    if use_sma:
        df['MA_FAST'] = df['Close'].rolling(window=fast_window).mean()
        df['MA_SLOW'] = df['Close'].rolling(window=slow_window).mean()
    else:
        df['MA_FAST'] = df['Close'].ewm(span=fast_window, adjust=False).mean()
        df['MA_SLOW'] = df['Close'].ewm(span=slow_window, adjust=False).mean()
    
    # Convert back to polars
    return pl.from_pandas(df)