"""Efficiency score calculation for concurrency analysis."""

from typing import List, Callable, Tuple, Dict

def calculate_strategy_efficiency(
    expectancy: float,
    correlation: float,
    concurrent_ratio: float,
    exclusive_ratio: float,
    inactive_ratio: float,
    log: Callable[[str, str], None]
) -> Tuple[float, float, float, float]:
    """Calculate individual strategy efficiency without allocation.
    
    Args:
        expectancy (float): Strategy's raw expectancy
        correlation (float): Strategy's correlation with other strategies
        concurrent_ratio (float): Ratio of concurrent trading periods
        exclusive_ratio (float): Ratio of exclusive trading periods
        inactive_ratio (float): Ratio of inactive periods
        log (Callable[[str, str], None]): Logging function
    
    Returns:
        Tuple[float, float, float, float]: (efficiency, diversification, independence, activity)
    """
    try:
        log("Calculating strategy efficiency", "info")
        log(f"Input - expectancy: {expectancy}, correlation: {correlation}", "info")
        log(f"Ratios - concurrent: {concurrent_ratio}, exclusive: {exclusive_ratio}, inactive: {inactive_ratio}", "info")

        if expectancy <= 0:
            log("Strategy expectancy is not positive, returning 0", "info")
            return 0.0, 0.0, 0.0, 0.0

        # Calculate multipliers
        diversification = 1 - correlation
        independence = exclusive_ratio / (1 - inactive_ratio) if inactive_ratio < 1 else 0
        activity = 1 - inactive_ratio

        # Calculate efficiency
        efficiency = expectancy * diversification * independence * activity

        log(f"Strategy efficiency components:", "info")
        log(f"Diversification: {diversification}", "info")
        log(f"Independence: {independence}", "info")
        log(f"Activity: {activity}", "info")
        log(f"Final efficiency: {efficiency}", "info")

        return efficiency, diversification, independence, activity

    except Exception as e:
        log(f"Error calculating strategy efficiency: {str(e)}", "error")
        raise

def calculate_portfolio_efficiency(
    strategy_efficiencies: List[float],
    strategy_expectancies: List[float],
    strategy_allocations: List[float],
    avg_correlation: float,
    concurrent_periods: int,
    exclusive_periods: int,
    inactive_periods: int,
    total_periods: int,
    log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate portfolio-level efficiency metrics.
    
    Args:
        strategy_efficiencies (List[float]): List of individual strategy efficiencies
        strategy_expectancies (List[float]): List of strategy expectancies
        strategy_allocations (List[float]): List of strategy allocations
        avg_correlation (float): Average correlation between strategies
        concurrent_periods (int): Number of concurrent trading periods
        exclusive_periods (int): Number of exclusive trading periods
        inactive_periods (int): Number of inactive periods
        total_periods (int): Total number of periods
        log (Callable[[str, str], None]): Logging function
    
    Returns:
        Dict[str, float]: Portfolio efficiency metrics
    """
    try:
        log("Calculating portfolio efficiency", "info")
        
        # Calculate raw portfolio metrics (without allocation weights)
        total_expectancy = sum(strategy_expectancies)
        total_efficiency = sum(strategy_efficiencies)
        
        # Calculate portfolio multipliers
        diversification = 1 - avg_correlation
        independence = (
            exclusive_periods / (concurrent_periods + exclusive_periods)
            if (concurrent_periods + exclusive_periods) > 0
            else 0
        )
        activity = 1 - (inactive_periods / total_periods)
        
        # Calculate final portfolio efficiency
        portfolio_efficiency = total_efficiency * diversification * independence * activity
        
        metrics = {
            'total_expectancy': total_expectancy,
            'portfolio_efficiency': portfolio_efficiency,
            'diversification_multiplier': diversification,
            'independence_multiplier': independence,
            'activity_multiplier': activity
        }
        
        log(f"Portfolio metrics calculated: {metrics}", "info")
        return metrics
        
    except Exception as e:
        log(f"Error calculating portfolio efficiency: {str(e)}", "error")
        raise

def calculate_efficiency_score(
    strategy_expectancies: List[float],
    strategy_allocations: List[float],
    avg_correlation: float,
    concurrent_periods: int,
    exclusive_periods: int,
    inactive_periods: int,
    total_periods: int,
    log: Callable[[str, str], None]
) -> Tuple[float, float, float, float, float]:
    """Calculate efficiency score for concurrent strategies.
    
    This is a legacy function that now uses the new calculation methods internally.
    For new code, prefer using calculate_strategy_efficiency and calculate_portfolio_efficiency directly.
    
    Returns:
        Tuple[float, float, float, float, float]: Legacy format (efficiency, expectancy, div, ind, act)
    """
    try:
        # Calculate ratios
        total_active = concurrent_periods + exclusive_periods
        concurrent_ratio = concurrent_periods / total_periods if total_periods > 0 else 0
        exclusive_ratio = exclusive_periods / total_periods if total_periods > 0 else 0
        inactive_ratio = inactive_periods / total_periods if total_periods > 0 else 0
        
        # Calculate individual efficiencies
        strategy_metrics = []
        for expectancy in strategy_expectancies:
            metrics = calculate_strategy_efficiency(
                expectancy=expectancy,
                correlation=avg_correlation,
                concurrent_ratio=concurrent_ratio,
                exclusive_ratio=exclusive_ratio,
                inactive_ratio=inactive_ratio,
                log=log
            )
            strategy_metrics.append(metrics)
        
        # Calculate portfolio metrics
        portfolio_metrics = calculate_portfolio_efficiency(
            strategy_efficiencies=[m[0] for m in strategy_metrics],
            strategy_expectancies=strategy_expectancies,
            strategy_allocations=strategy_allocations,
            avg_correlation=avg_correlation,
            concurrent_periods=concurrent_periods,
            exclusive_periods=exclusive_periods,
            inactive_periods=inactive_periods,
            total_periods=total_periods,
            log=log
        )
        
        # Return in legacy format
        return (
            portfolio_metrics['portfolio_efficiency'],
            portfolio_metrics['total_expectancy'],
            portfolio_metrics['diversification_multiplier'],
            portfolio_metrics['independence_multiplier'],
            portfolio_metrics['activity_multiplier']
        )
        
    except Exception as e:
        log(f"Error in legacy efficiency calculation: {str(e)}", "error")
        raise


def apply_ratio_based_allocation(
    allocations: List[float],
    log: Callable[[str, str], None]
) -> List[float]:
    """Apply ratio-based allocation to ensure smallest allocation is at least half of the largest.

    Args:
        allocations (List[float]): List of initial allocation percentages.
        log (Callable[[str, str], None]): Logging function.

    Returns:
        List[float]: Adjusted allocation percentages.
    """
    try:
        log("Applying ratio-based allocation", "info")

        min_alloc = min(allocations)
        max_alloc = max(allocations)

        if min_alloc < 0.5 * max_alloc:
            log("Smallest allocation is less than half of the largest, scaling allocations", "info")
            # Calculate the total increase needed for small allocations
            total_increase = sum(half_max - alloc for alloc in allocations if alloc < half_max)

            # Calculate the total of large allocations
            total_large = sum(alloc for alloc in allocations if alloc >= half_max)

            # Calculate the reduction factor for large allocations
            reduction_factor = (total_large - total_increase) / total_large if total_large > 0 else 0

            # Create new allocations list
            new_allocations = [0.0] * len(allocations)

            # Set small allocations to half_max
            for i, alloc in enumerate(allocations):
                if alloc < half_max:
                    new_allocations[i] = half_max
                else:
                    new_allocations[i] = alloc * reduction_factor

            # Normalize to 100%
            total = sum(new_allocations)
            final_allocations = [alloc / total * 100 for alloc in new_allocations]

            log(f"Scaled allocations: {final_allocations}", "info")
            return final_allocations
        else:
            log("Smallest allocation is already at least half of the largest, no scaling needed", "info")
            return allocations

    except Exception as e:
        log(f"Error applying ratio-based allocation: {str(e)}", "error")
        raise

def calculate_allocation_scores(
    strategy_expectancies: List[float],
    strategy_risk_contributions: List[float],
    strategy_alphas: List[float],
    strategy_efficiencies: List[float],
    log: Callable[[str, str], None],
    ratio_based_allocation: bool = False
) -> tuple[List[float], List[float]]:
    """Calculate allocation scores for each strategy.

    Args:
        strategy_expectancies (List[float]): List of strategy expectancies
        strategy_risk_contributions (List[float]): List of risk contributions
        strategy_alphas (List[float]): List of strategy alphas
        strategy_efficiencies (List[float]): List of strategy efficiencies
        log: Callable[[str, str], None]
        ratio_based_allocation (bool): Flag to enable ratio-based allocation

    Returns:
        List[float]: Allocation scores for each strategy
    """
    try:
        log("Calculating allocation scores", "info")

        # Normalize the metrics
        normalized_expectancies = normalize_values(strategy_expectancies)
        normalized_risks = normalize_risk_values(strategy_risk_contributions)
        normalized_alphas = normalize_values(strategy_alphas)
        normalized_efficiencies = normalize_values(strategy_efficiencies)

        # Calculate allocation scores
        allocation_scores = []
        for i in range(len(strategy_expectancies)):
            allocation_score = (
                (0.35 * normalized_efficiencies[i]) +
                (0.30 * normalized_expectancies[i]) +
                (0.25 * normalized_risks[i]) +
                (0.10 * normalized_alphas[i])
            )
            allocation_scores.append(allocation_score)

        # Calculate the sum of all allocation scores
        total_allocation_score = sum(allocation_scores)

        # Calculate the allocation percentage for each strategy
        allocation_percentages = [
            (score / total_allocation_score) * 100 if total_allocation_score > 0 else 0
            for score in allocation_scores
        ]

        if ratio_based_allocation:
            allocation_percentages = apply_ratio_based_allocation(allocation_percentages, log)

        log(f"Allocation scores: {allocation_scores}", "info")
        log(f"Allocation percentages: {allocation_percentages}", "info")
        return allocation_scores, allocation_percentages

    except Exception as e:
        log(f"Error calculating allocation scores: {str(e)}", "error")
        raise


def calculate_ticker_allocations(
    ticker_metrics: Dict[str, Dict],
    ratio_based_allocation: bool,
    log: Callable[[str, str], None]
) -> Dict[str, float]:
    """Calculate allocations for individual tickers.

    Args:
        ticker_metrics (Dict[str, Dict]): Dictionary of ticker metrics
        ratio_based_allocation (bool): Whether to apply ratio-based allocation
        log (Callable[[str, str], None]): Logging function

    Returns:
        Dict[str, float]: Ticker allocation percentages
    """
    try:
        log("Calculating ticker allocations", "info")
        
        # Extract allocation scores from ticker metrics
        tickers = []
        allocation_scores = []
        for ticker, metrics in ticker_metrics.items():
            tickers.append(ticker)
            allocation_scores.append(metrics['allocation_score'])
        
        log(f"Initial allocation scores: {dict(zip(tickers, allocation_scores))}", "info")
        
        # Calculate initial allocation percentages
        total_score = sum(allocation_scores)
        allocations = [
            (score / total_score) * 100 if total_score > 0 else 0
            for score in allocation_scores
        ]
        
        log(f"Initial allocations: {dict(zip(tickers, allocations))}", "info")
        
        # Apply ratio-based allocation if enabled
        if ratio_based_allocation:
            min_alloc = min(allocations)
            max_alloc = max(allocations)
            half_max = 0.5 * max_alloc
            
            if min_alloc < half_max:
                log(f"Min allocation {min_alloc:.2f}% is less than half of max {max_alloc:.2f}%", "info")
                
                # Calculate required adjustments
                small_allocations = []
                large_allocations = []
                small_indices = []
                large_indices = []
                
                for i, alloc in enumerate(allocations):
                    if alloc < half_max:
                        small_allocations.append(alloc)
                        small_indices.append(i)
                    else:
                        large_allocations.append(alloc)
                        large_indices.append(i)
                
                if small_allocations:
                    # Calculate total increase needed for small allocations
                    total_increase = sum(half_max - alloc for alloc in small_allocations)
                    
                    # Calculate reduction factor for large allocations
                    total_large = sum(large_allocations)
                    reduction_factor = (total_large - total_increase) / total_large
                    
                    # Create new allocations list
                    new_allocations = [0.0] * len(allocations)
                    
                    # Set small allocations to half_max
                    for i in small_indices:
                        new_allocations[i] = half_max
                    
                    # Reduce large allocations proportionally
                    for i, large_idx in enumerate(large_indices):
                        new_allocations[large_idx] = large_allocations[i] * reduction_factor
                    
                    # Normalize to 100%
                    total = sum(new_allocations)
                    allocations = [alloc / total * 100 for alloc in new_allocations]
                    
                    log(f"Adjusted allocations: {dict(zip(tickers, allocations))}", "info")
                    
                    # Verify ratio constraint
                    new_min = min(allocations)
                    new_max = max(allocations)
                    ratio = new_min / new_max
                    log(f"New min/max ratio: {ratio:.2f} (target >= 0.5)", "info")
                    
                    if ratio < 0.499:  # Allow small numerical error
                        log("Warning: Ratio constraint not satisfied after adjustment", "warning")
            else:
                log("Allocations already satisfy ratio constraint", "info")
        
        # Create dictionary mapping tickers to their allocations
        ticker_allocations = dict(zip(tickers, allocations))
        
        log(f"Final ticker allocations: {ticker_allocations}", "info")
        return ticker_allocations
        
    except Exception as e:
        log(f"Error calculating ticker allocations: {str(e)}", "error")
        raise

def normalize_values(values: List[float]) -> List[float]:
    """Normalize a list of values to a scale of 0 to 1.

    Args:
        values (List[float]): List of values to normalize

    Returns:
        List[float]: Normalized values
    """
    min_value = min(values)
    max_value = max(values)
    if max_value == min_value:
        return [0.0] * len(values)  # Avoid division by zero
    return [(value - min_value) / (max_value - min_value) for value in values]


def normalize_risk_values(risks: List[float]) -> List[float]:
    """Normalize risk values using inverted normalization (lower risk is better).

    Args:
        risks (List[float]): List of risk values to normalize

    Returns:
        List[float]: Normalized risk values
    """
    min_risk = min(risks)
    max_risk = max(risks)
    if max_risk == min_risk:
        return [1.0] * len(risks)  # Avoid division by zero, all risks are equal
    return [1 - ((risk - min_risk) / (max_risk - min_risk)) for risk in risks]
