"""Efficiency score calculation for concurrency analysis."""

from typing import List, Callable

def calculate_efficiency_score(
    strategy_expectancies: List[float],
    avg_correlation: float,
    concurrent_periods: int,
    exclusive_periods: int,
    inactive_periods: int,
    total_periods: int,
    log: Callable[[str, str], None]
) -> float:
    """Calculate efficiency score for concurrent strategies.

    The efficiency score combines multiple factors to assess how well the strategies
    work together:
    - Total expectancy (sum of individual strategy expectancies)
    - Diversification (penalizes high correlations)
    - Independence (rewards strategies that trade in different periods)
    - Activity (penalizes inactive periods)

    Args:
        strategy_expectancies (List[float]): List of strategy expectancies
        avg_correlation (float): Average correlation between strategies
        concurrent_periods (int): Number of concurrent trading periods
        exclusive_periods (int): Number of exclusive trading periods
        inactive_periods (int): Number of inactive periods
        total_periods (int): Total number of periods
        log (Callable[[str, str], None]): Logging function

    Returns:
        float: Efficiency score between 0 and 1, where higher is better
    """
    try:
        log("Calculating efficiency score", "info")
        log(f"Input parameters: expectancies={strategy_expectancies}, avg_correlation={avg_correlation}", "info")
        log(f"Periods - concurrent: {concurrent_periods}, exclusive: {exclusive_periods}, inactive: {inactive_periods}, total: {total_periods}", "info")
        
        total_expectancy = sum(strategy_expectancies)
        
        if total_expectancy <= 0:
            log("Total expectancy is not positive, returning 0", "info")
            return 0.0
        
        # Calculate diversification multiplier (penalizes high correlations)
        diversification_multiplier = 1 - avg_correlation
        log(f"Diversification multiplier: {diversification_multiplier}", "info")
        
        # Calculate strategy independence multiplier
        active_periods = concurrent_periods + exclusive_periods
        independence_multiplier = (
            exclusive_periods / active_periods
            if active_periods > 0
            else 0
        )
        log(f"Independence multiplier: {independence_multiplier}", "info")
        
        # Calculate activity multiplier (penalizes inactive periods)
        activity_multiplier = 1 - (inactive_periods / total_periods)
        log(f"Activity multiplier: {activity_multiplier}", "info")
        
        # Calculate final efficiency score
        efficiency_score = (
            total_expectancy * 
            diversification_multiplier * 
            independence_multiplier * 
            activity_multiplier
        )
        
        log(f"Final efficiency score: {efficiency_score}", "info")
        return efficiency_score, total_expectancy, diversification_multiplier, independence_multiplier, activity_multiplier
        
    except Exception as e:
        log(f"Error calculating efficiency score: {str(e)}", "error")
        raise
