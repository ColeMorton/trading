import polars as pl
import logging

def calculate_macd(data: pl.DataFrame, short_window: int, long_window: int, signal_window: int) -> pl.DataFrame:
    logging.info(f"Calculating MACD with short period: {short_window}, long period: {long_window}, signal period: {signal_window}")
    try:
        exp1 = data['Close'].ewm_mean(span=short_window)
        exp2 = data['Close'].ewm_mean(span=long_window)
        macd = exp1 - exp2
        signal = macd.ewm_mean(span=signal_window)
        return data.with_columns([
            macd.alias('MACD'),
            signal.alias('Signal_Line')
        ])
    except Exception as e:
        logging.error(f"Failed to calculate MACD: {e}")
        raise