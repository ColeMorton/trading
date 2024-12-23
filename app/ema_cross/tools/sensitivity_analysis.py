import polars as pl
from typing import List, Dict, Any, Optional, Callable
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ema_cross.tools.signal_generation import is_signal_current
from app.tools.stats_converter import convert_stats
from app.tools.backtest_strategy import backtest_strategy

def reorder_columns(portfolio: Dict) -> Dict:
    """
    Reorder columns to match required format.

    Args:
        portfolio (Dict): Portfolio statistics

    Returns:
        Dict: Portfolio with reordered columns
    """
    first_columns = [
        'Ticker',
        'Use SMA',
        'Short Window',
        'Long Window',
        'Total Trades',
        'Win Rate [%]',
        'Profit Factor',
        'Tradability',
        'Expectancy',
        'Expectancy Adjusted',
        'Trades per Month',
        'Signals per Month',
        'Expectancy per Month',
        'Sortino Ratio'
    ]
    
    reordered = {}
    # Add first columns in specified order
    for col in first_columns:
        reordered[col] = portfolio[col]
    
    # Add remaining columns
    for key, value in portfolio.items():
        if key not in first_columns:
            reordered[key] = value
            
    return reordered

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
            
        temp_data = calculate_ma_and_signals(data.clone(), short, long, config, log)  # Added log parameter
        if temp_data is None or len(temp_data) == 0:
            log(f"No signals generated for windows {short}, {long}", "warning")
            return None
            
        current = is_signal_current(temp_data)
        portfolio = backtest_strategy(temp_data, config, log)

        stats = portfolio.stats()
        stats['Short Window'] = short
        stats['Long Window'] = long
        stats['Ticker'] = config['TICKER']  # Add ticker from config
        stats['Use SMA'] = config.get('USE_SMA', False)  # Add SMA usage info
        converted_stats = convert_stats(stats, log, config)
        converted_stats['Current'] = int(current)
        converted_stats = reorder_columns(converted_stats)
        
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
