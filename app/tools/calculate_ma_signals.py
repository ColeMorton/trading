import polars as pl


def calculate_ma_signals(
    data: pl.DataFrame,
    config: dict,
) -> tuple[pl.Series, pl.Series]:
    """
    Generate entry and exit signals based on the strategy configuration.
    A signal is generated when the fast MA is above/below the slow MA on the last trading day.

    Args:
        data (pl.DataFrame): The input DataFrame containing MA_FAST and MA_SLOW columns
        config (Dict): The configuration dictionary containing strategy settings

    Returns:
        Tuple[pl.Series, pl.Series]: Entry and exit signals as polars Series
    """
    # Check if RSI should be used and if the necessary parameters exist
    use_rsi = config.get("USE_RSI", False) and "RSI" in data.columns
    has_rsi_threshold = (
        "RSI_THRESHOLD" in config and config["RSI_THRESHOLD"] is not None
    )

    # Get the last trading day's values
    ma_fast = pl.col("MA_FAST")
    ma_slow = pl.col("MA_SLOW")

    if config.get("DIRECTION", "Long") == "Short":
        # For short positions, check if fast MA is below slow MA on the last trading day
        entries = ma_fast < ma_slow
        if use_rsi and has_rsi_threshold:
            rsi_threshold = config.get("RSI_THRESHOLD", 70)
            entries = entries & (pl.col("RSI") <= (100 - rsi_threshold))
        exits = ma_fast > ma_slow
    else:
        # For long positions, check if fast MA is above slow MA on the last trading day
        entries = ma_fast > ma_slow
        if use_rsi and has_rsi_threshold:
            rsi_threshold = config.get("RSI_THRESHOLD", 70)
            entries = entries & (pl.col("RSI") >= rsi_threshold)
        exits = ma_fast < ma_slow

    # Apply conditions to DataFrame
    result = data.with_columns([entries.alias("entries"), exits.alias("exits")])

    return result.get_column("entries"), result.get_column("exits")
