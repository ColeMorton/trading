from typing import TypedDict, NotRequired, List, Dict
from typing import TypedDict, NotRequired
from app.ema_cross.tools.generate_current_signals import generate_current_signals

class Config(TypedDict):
    TICKER: str
    WINDOWS: int
    SHORT: NotRequired[bool]
    USE_SMA: NotRequired[bool]
    USE_HOURLY: NotRequired[bool]
    USE_YEARS: NotRequired[bool]
    YEARS: NotRequired[float]
    USE_GBM: NotRequired[bool]
    USE_SYNTHETIC: NotRequired[bool]
    TICKER_1: NotRequired[str]
    TICKER_2: NotRequired[str]

def check_signal_match(signals: List[Dict], fast_window: int, slow_window: int) -> bool:
    """
    Check if any signal matches the given window combination.

    Args:
        signals: List of signal dictionaries containing window information
        fast_window: Fast window value to match
        slow_window: Slow window value to match

    Returns:
        bool: True if a matching signal is found, False otherwise
    """
    if not signals:
        return False
    
    return any(
        signal["Short Window"] == fast_window and 
        signal["Long Window"] == slow_window
        for signal in signals
    )

def process_ma_signals(ticker: str, ma_type: str, config: Config, 
                      fast_window: int, slow_window: int) -> bool:
    """
    Process moving average signals for a given ticker and configuration.

    Args:
        ticker: The ticker symbol to process
        ma_type: Type of moving average ('SMA' or 'EMA')
        config: Configuration dictionary
        fast_window: Fast window value from scanner
        slow_window: Slow window value from scanner

    Returns:
        bool: True if current signal is found, False otherwise
    """
    ma_config = config.copy()
    ma_config.update({
        "TICKER": ticker,
        "USE_SMA": ma_type == "SMA"
    })
    
    signals = generate_current_signals(ma_config)
    
    is_current = check_signal_match(
        signals.to_dicts() if len(signals) > 0 else [], 
        fast_window, 
        slow_window
    )
    
    message = (
        f"{ticker} {ma_type} - {'Current signal found' if is_current else 'No signals'} "
        f"for {fast_window}/{slow_window}{'!!!!!' if is_current else ''}"
    )
    print(message)
    
    return is_current