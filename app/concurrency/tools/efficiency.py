"""Efficiency score calculation for concurrency analysis."""

from typing import List, Callable, Tuple, Dict
import numpy as np

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

def adjust_allocations(allocations):
    """
    Adjust allocations to ensure no value is more than twice the minimum
    or less than half the maximum while maintaining relative proportions.
    """
    # Convert allocations to numpy array and handle zero case
    alloc_array = np.array(allocations)
    print("\nDEBUG: Initial allocations:", alloc_array)
    
    if np.sum(alloc_array) == 0:
        print("DEBUG: All allocations are zero")
        return [100.0 / len(allocations)] * len(allocations)
    
    # Get initial proportions and handle zeros
    total = np.sum(alloc_array)
    initial_proportions = alloc_array / total
    print("DEBUG: Initial proportions:", initial_proportions)
    
    # Find non-zero allocations
    non_zero_mask = alloc_array > 0
    if not np.any(non_zero_mask):
        print("DEBUG: No non-zero allocations found")
        return [100.0 / len(allocations)] * len(allocations)
    
    non_zero_allocs = alloc_array[non_zero_mask]
    min_alloc = np.min(non_zero_allocs)
    max_alloc = np.max(non_zero_allocs)
    print(f"DEBUG: Min non-zero allocation: {min_alloc:.4f}")
    print(f"DEBUG: Max allocation: {max_alloc:.4f}")
    print(f"DEBUG: Current min/max ratio: {min_alloc/max_alloc:.4f}")
    
    # If already satisfies constraint, return normalized allocations
    if min_alloc >= max_alloc / 2:
        print("DEBUG: Allocations already satisfy ratio constraint")
        return (initial_proportions * 100).tolist()
    
    # Calculate power transformation factor to compress the range
    current_ratio = max_alloc / min_alloc
    target_ratio = 2.0  # max should be no more than 2x min
    power_factor = np.log(target_ratio) / np.log(current_ratio)
    print(f"DEBUG: Power factor: {power_factor:.4f}")
    
    # Apply power transformation to compress the range while preserving order
    result = np.zeros_like(alloc_array)
    result[non_zero_mask] = np.power(non_zero_allocs, power_factor)
    print("DEBUG: After power transformation:", result)
    
    # Normalize to 100% while preserving zeros
    result = result / np.sum(result) * 100
    print("DEBUG: After normalization:", result)
    
    # Verify relative ordering is maintained
    print("\nDEBUG: Verifying relative ordering")
    for i in range(len(allocations)):
        for j in range(i + 1, len(allocations)):
            if alloc_array[i] > alloc_array[j]:
                print(f"DEBUG: Checking {i}({alloc_array[i]:.4f}) > {j}({alloc_array[j]:.4f})")
                print(f"DEBUG: Result {i}({result[i]:.4f}) > {j}({result[j]:.4f})")
                if not result[i] > result[j]:
                    print(f"DEBUG: ERROR - Relative ordering violated between indices {i} and {j}")
                    print(f"DEBUG: Original: {alloc_array[i]:.4f} > {alloc_array[j]:.4f}")
                    print(f"DEBUG: Result: {result[i]:.4f} <= {result[j]:.4f}")
                assert result[i] > result[j], "Relative ordering violated"
            elif alloc_array[i] < alloc_array[j]:
                print(f"DEBUG: Checking {i}({alloc_array[i]:.4f}) < {j}({alloc_array[j]:.4f})")
                print(f"DEBUG: Result {i}({result[i]:.4f}) < {j}({result[j]:.4f})")
                if not result[i] < result[j]:
                    print(f"DEBUG: ERROR - Relative ordering violated between indices {i} and {j}")
                    print(f"DEBUG: Original: {alloc_array[i]:.4f} < {alloc_array[j]:.4f}")
                    print(f"DEBUG: Result: {result[i]:.4f} >= {result[j]:.4f}")
                assert result[i] < result[j], "Relative ordering violated"
    
    print("\nDEBUG: Final allocations:", result.tolist())
    return result.tolist()


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
        adjusted_allocations = adjust_allocations(allocations)
        log(f"Adjusted allocations: {adjusted_allocations}", "info")
        return adjusted_allocations

    except Exception as e:
        log(f"Error applying ratio-based allocation: {str(e)}", "error")
        raise

def calculate_allocation_scores(
    strategy_risk_contributions: List[float],
    strategy_signal_quality_scores: List[float],
    strategy_efficiencies: List[float],
    strategy_tickers: List[str],  # Added parameter for ticker mapping
    log: Callable[[str, str], None],
    ratio_based_allocation: bool = False
) -> tuple[List[float], List[float]]:
    """Calculate allocation scores for each strategy.

    Args:
        strategy_expectancies (List[float]): List of strategy expectancies
        strategy_risk_contributions (List[float]): List of risk contributions
        strategy_signal_quality_scores (List[float]): List of strategy signal quality scores
        strategy_efficiencies (List[float]): List of strategy efficiencies
        strategy_tickers (List[str]): List of tickers corresponding to each strategy
        log: Callable[[str, str], None]
        ratio_based_allocation (bool): Flag to enable ratio-based allocation

    Returns:
        List[float]: Allocation scores for each strategy
    """
    try:
        log("Calculating allocation scores", "info")
        log(f"Number of strategies: {len(strategy_efficiencies)}", "info")
        log(f"Raw strategy efficiencies: {strategy_efficiencies}", "info")
        
        # Log each strategy's efficiency individually
        for i, efficiency in enumerate(strategy_efficiencies):
            log(f"Strategy {i} raw efficiency: {efficiency}", "info")

        # Normalize the metrics
        normalized_risks = normalize_risk_values(strategy_risk_contributions)
        normalized_signal_quality_scores = normalize_values(strategy_signal_quality_scores)
        normalized_efficiencies = normalize_values(strategy_efficiencies)

        # Calculate raw allocation scores
        allocation_scores = []
        for i in range(len(strategy_efficiencies)):
            efficiency_component = 1 * normalized_efficiencies[i]
            risk_component = 0.65 * normalized_risks[i]
            signal_quality_component = 0.618 * normalized_signal_quality_scores[i]
            
            allocation_score = efficiency_component + risk_component + signal_quality_component
            
            log(f"Strategy {i} allocation components:", "info")
            log(f"  Efficiency component (0.35 * {normalized_efficiencies[i]:.4f}): {efficiency_component:.4f}", "info")
            log(f"  Risk component (0.30 * {normalized_risks[i]:.4f}): {risk_component:.4f}", "info")
            log(f"  Signal quality component (0.25 * {normalized_signal_quality_scores[i]:.4f}): {signal_quality_component:.4f}", "info")
            log(f"  Total allocation score: {allocation_score:.4f}", "info")
            
            allocation_scores.append(allocation_score)

        # Group strategies by ticker
        ticker_strategies = {}
        for i, ticker in enumerate(strategy_tickers):
            if ticker not in ticker_strategies:
                ticker_strategies[ticker] = []
            ticker_strategies[ticker].append(i)

        # Calculate ticker-level metrics
        ticker_metrics = {}
        for ticker, strategy_indices in ticker_strategies.items():
            ticker_metrics[ticker] = {
                'allocation_score': sum(allocation_scores[i] for i in strategy_indices)
            }

        # Get ticker allocations
        ticker_allocations = calculate_ticker_allocations(
            ticker_metrics,
            ratio_based_allocation,
            log
        )

        # Distribute ticker allocations to strategies proportionally
        allocation_percentages = [0.0] * len(strategy_efficiencies)
        for ticker, strategies in ticker_strategies.items():
            ticker_total_score = sum(allocation_scores[i] for i in strategies)
            if ticker_total_score > 0:
                ticker_allocation = ticker_allocations[ticker]
                for strategy_index in strategies:
                    strategy_proportion = allocation_scores[strategy_index] / ticker_total_score
                    allocation_percentages[strategy_index] = ticker_allocation * strategy_proportion

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
        
        # Group strategies by ticker and sum their allocation scores
        ticker_total_scores = {}
        for ticker, metrics in ticker_metrics.items():
            ticker_total_scores[ticker] = metrics['allocation_score']
        
        log(f"Ticker total scores: {ticker_total_scores}", "info")
        
        # Calculate initial ticker-level allocations
        total_score = sum(ticker_total_scores.values())
        ticker_allocations = {
            ticker: (score / total_score) * 100 if total_score > 0 else 0
            for ticker, score in ticker_total_scores.items()
        }
        
        log(f"Initial ticker allocations: {ticker_allocations}", "info")
        
        if ratio_based_allocation:
            # Sort tickers by allocation to maintain relative ordering
            sorted_tickers = sorted(
                ticker_allocations.keys(),
                key=lambda t: ticker_allocations[t],
                reverse=True
            )
            sorted_allocations = [ticker_allocations[t] for t in sorted_tickers]
            
            # Adjust allocations while preserving ticker ordering
            adjusted = adjust_allocations(sorted_allocations)
            
            # Map back to tickers while maintaining original order
            ticker_allocations = dict(zip(sorted_tickers, adjusted))
            
            log(f"Adjusted ticker allocations: {ticker_allocations}", "info")
            
            # Verify relative ordering is maintained
            sorted_final = sorted(
                ticker_allocations.items(),
                key=lambda x: x[1],
                reverse=True
            )
            log("Final allocation order:", "info")
            for ticker, alloc in sorted_final:
                log(f"{ticker}: {alloc:.2f}%", "info")
        
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
