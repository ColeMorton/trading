import polars as pl
import logging

def calculate_rsi(data: pl.DataFrame, period: int) -> pl.DataFrame:
    logging.info(f"Calculating RSI with period: {period}")
    try:
        delta = data['Close'].diff()
        gain = (delta.fill_null(0) > 0) * delta.fill_null(0)
        loss = (delta.fill_null(0) < 0) * -delta.fill_null(0)
        avg_gain = gain.rolling_mean(window_size=period)
        avg_loss = loss.rolling_mean(window_size=period)
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return data.with_columns([rsi.alias('RSI')])
    except Exception as e:
        logging.error(f"Failed to calculate RSI: {e}")
        raise