import polars as pl
from typing import List, Dict, Any, Optional, Callable
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ema_cross.tools.signal_generation import is_signal_current
from app.tools.file_utils import convert_stats
from app.tools.backtest_strategy import backtest_strategy

def analyze_window_combination(
    data: pl.DataFrame,
    short: int,
    long: int,
    config: Dict[str, Any],
    log: Callable
) -> Optional[Dict[str, Any]]:
    """
    Analyze a single window combination.
    
    Args:
        data: Price data DataFrame
        short: Short window period
        long: Long window period
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        Optional[Dict]: Portfolio statistics if successful, None if failed
    """
    try:
        if len(data) < max(short, long):
            log(f"Insufficient data for windows {short}, {long}", "warning")
            return None
            
        temp_data = calculate_ma_and_signals(data.clone(), short, long, config)
        if temp_data is None or len(temp_data) == 0:
            log(f"No signals generated for windows {short}, {long}", "warning")
            return None
            
        current = is_signal_current(temp_data)
        portfolio = backtest_strategy(temp_data, config, log)

        stats = portfolio.stats()
        stats['Short Window'] = short
        stats['Long Window'] = long
        converted_stats = convert_stats(stats)
        converted_stats['Current'] = int(current)
        
        return converted_stats
        
    except Exception as e:
        log(f"Failed to process windows {short}, {long}: {str(e)}", "warning")
        return None

def analyze_parameter_combinations(
    data: pl.DataFrame,
    short_windows: List[int],
    long_windows: List[int],
    config: Dict[str, Any],
    log: Callable
) -> List[Dict[str, Any]]:
    """
    Analyze all valid parameter combinations.
    
    Args:
        data: Price data DataFrame
        short_windows: List of short window periods
        long_windows: List of long window periods
        config: Configuration dictionary
        log: Logging function for recording events and errors
        
    Returns:
        List[Dict]: List of portfolio statistics for each valid combination
    """
    portfolios = []
    
    for short in short_windows:
        for long in long_windows:
            if short < long:
                result = analyze_window_combination(data, short, long, config, log)
                if result is not None:
                    portfolios.append(result)
                    
    return portfolios
