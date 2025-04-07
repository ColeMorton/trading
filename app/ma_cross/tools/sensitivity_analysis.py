import polars as pl
from typing import List, Dict, Any, Optional, Callable
from app.tools.calculate_ma_and_signals import calculate_ma_and_signals
from app.ma_cross.tools.signal_utils import is_signal_current
from app.tools.stats_converter import convert_stats
from app.tools.backtest_strategy import backtest_strategy
from app.tools.portfolio_transformation import reorder_columns

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
        data_length = len(data)
        max_window = max(short, long)
        
        log(f"Analyzing windows - Short: {short}, Long: {long}")
        log(f"Data length: {data_length}, Required length: {max_window}")
        
        if data_length < max_window:
            log(f"Insufficient data for windows {short}, {long} - Need at least {max_window} periods, have {data_length}", "warning")
            return None
            
        temp_data = calculate_ma_and_signals(data.clone(), short, long, config, log)
        if temp_data is None or len(temp_data) == 0:
            log(f"No signals generated for windows {short}, {long}", "warning")
            return None
            
        current = is_signal_current(temp_data, config)
        portfolio = backtest_strategy(temp_data, config, log)

        stats = portfolio.stats()
        stats['Short Window'] = short
        stats['Long Window'] = long
        stats['Ticker'] = config['TICKER']  # Add ticker from config
        # Add Strategy Type field based on USE_SMA (no longer adding Use SMA field)
        stats['Strategy Type'] = "SMA" if config.get('USE_SMA', False) else "EMA"
        stats = convert_stats(stats, log, config, current)
        stats = reorder_columns(stats)
        
        return stats
        
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
    total_combinations = 0
    successful_combinations = 0
    
    log(f"Starting analysis of window combinations")
    log(f"Data shape: {data.shape}")
    log(f"Date range: {data['Date'].min()} to {data['Date'].max()}")
    
    for short in short_windows:
        for long in long_windows:
            if short < long:
                total_combinations += 1
                result = analyze_window_combination(data, short, long, config, log)
                if result is not None:
                    successful_combinations += 1
                    portfolios.append(result)
    
    success_rate = (successful_combinations / total_combinations * 100) if total_combinations > 0 else 0
    log(f"Analysis complete - Successful combinations: {successful_combinations}/{total_combinations} ({success_rate:.2f}%)")
    
    return portfolios
