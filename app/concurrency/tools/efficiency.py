"""Efficiency score calculation for concurrency analysis."""

from typing import List, Callable, Tuple, Dict
import numpy as np

def calculate_strategy_efficiency(
    correlation: float,
    concurrent_ratio: float,
    exclusive_ratio: float,
    inactive_ratio: float,
    log: Callable[[str, str], None]
) -> Tuple[float, float, float, float]:
    """Calculate individual strategy efficiency without allocation.
    
    Args:
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
        log(f"Input - correlation: {correlation}", "info")
        log(f"Ratios - concurrent: {concurrent_ratio}, exclusive: {exclusive_ratio}, inactive: {inactive_ratio}", "info")

        # Calculate multipliers
        diversification = 1 - correlation
        
        # Modify independence calculation to handle zero exclusive_ratio
        if exclusive_ratio <= 0:
            log(f"Warning: exclusive_ratio is {exclusive_ratio}, using minimum value for independence", "warning")
            independence = 0.0001  # Use a small positive value instead of zero
        else:
            independence = exclusive_ratio / (1 - inactive_ratio) if inactive_ratio < 1 else 0.0001
            
        activity = 1 - inactive_ratio

        # Calculate efficiency (without expectancy)
        efficiency = diversification * independence * activity
        
        # Ensure efficiency is at least a small positive value
        if efficiency <= 0:
            log(f"Warning: Calculated efficiency is {efficiency}, setting to minimum value", "warning")
            efficiency = 0.0001

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
        total_efficiency = sum(strategy_efficiencies)
        
        # Calculate portfolio multipliers
        diversification = 1 - avg_correlation
        
        # Handle case where exclusive_periods is 0
        if exclusive_periods <= 0:
            log(f"Warning: exclusive_periods is {exclusive_periods}, using minimum value for independence", "warning")
            independence = 0.01  # Use a small positive value instead of zero
        else:
            independence = (
                exclusive_periods / (concurrent_periods + exclusive_periods)
                if (concurrent_periods + exclusive_periods) > 0
                else 0.01
            )
            
        activity = 1 - (inactive_periods / total_periods)
        
        # Calculate final portfolio efficiency
        portfolio_efficiency = total_efficiency * diversification * independence * activity
        
        # Ensure portfolio efficiency is at least a small positive value
        if portfolio_efficiency <= 0:
            log(f"Warning: Calculated portfolio efficiency is {portfolio_efficiency}, setting to minimum value", "warning")
            portfolio_efficiency = 0.0001
        
        metrics = {
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
    strategy_efficiencies: List[float],
    strategy_tickers: List[str],
    log: Callable[[str, str], None],
    ratio_based_allocation: bool = False,
    strategy_configs: List[Dict] = None
) -> tuple[List[float], List[float]]:
    """Calculate allocation scores for each strategy.

    Args:
        strategy_efficiencies (List[float]): List of strategy efficiencies (used for length and logging)
        strategy_tickers (List[str]): List of tickers corresponding to each strategy
        log: Callable[[str, str], None]: Logging function
        ratio_based_allocation (bool): Flag to enable ratio-based allocation
        strategy_configs (List[Dict]): List of strategy configurations containing portfolio stats

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

        # Extract scores from portfolio stats if available
        strategy_scores = []
        if strategy_configs:
            for i, config in enumerate(strategy_configs):
                if 'PORTFOLIO_STATS' in config and 'Score' in config['PORTFOLIO_STATS']:
                    score = config['PORTFOLIO_STATS']['Score']
                    log(f"Strategy {i} score from portfolio stats: {score:.4f}", "info")
                    strategy_scores.append(score)
                else:
                    log(f"Strategy {i} missing Score in portfolio stats, using fallback", "error")
                    raise
        else:
            # If strategy_configs is not provided, use a fallback approach
            log("Strategy configs not provided, using fallback scores", "warning")
            strategy_scores = [0.0001] * len(strategy_efficiencies)  # Small positive values as fallback
        
        # Normalize the scores
        normalized_scores = normalize_values(strategy_scores)
        normalized_efficiencies = normalize_values(strategy_efficiencies)
        
        # Calculate raw allocation scores
        allocation_scores = []
        for i in range(len(strategy_efficiencies)):
            score_component = normalized_scores[i]
            efficiency_component = 0.786 * normalized_efficiencies[i]
            allocation_score = score_component + efficiency_component
            
            log(f"Strategy {i} allocation component:", "info")
            log(f"  Score component: {score_component:.4f}", "info")
            log(f"  Efficiency component (0.786 * {normalized_efficiencies[i]:.4f}): {efficiency_component:.4f}", "info")
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
            ticker_allocation = ticker_allocations[ticker]
            
            # Special case: if there's only one strategy for this ticker, it gets 100% of the ticker allocation
            if len(strategies) == 1:
                strategy_index = strategies[0]
                allocation_percentages[strategy_index] = ticker_allocation
                log(f"Strategy {strategy_index} is the only strategy for {ticker}, " +
                    f"assigning 100% of ticker allocation: {ticker_allocation:.4f}%", "info")
                continue
            
            # Create adjusted scores - use a very small value for zero scores
            adjusted_scores = []
            strategy_indices = []
            
            # Sort strategies by their original scores
            sorted_strategies = sorted(
                strategies,
                key=lambda idx: allocation_scores[idx],
                reverse=True
            )
            
            for strategy_index in sorted_strategies:
                strategy_indices.append(strategy_index)
                score = allocation_scores[strategy_index]
                if score <= 0:
                    # Use a very small positive value for zero scores
                    adjusted_scores.append(0.0001)
                    log(f"Strategy {strategy_index} has zero score, using minimal value 0.0001", "info")
                else:
                    adjusted_scores.append(score)
            
            # Calculate total adjusted score for normalization
            total_adjusted_score = sum(adjusted_scores)
            
            # Distribute allocations based on adjusted scores
            if total_adjusted_score > 0:
                for i, strategy_index in enumerate(strategy_indices):
                    strategy_proportion = adjusted_scores[i] / total_adjusted_score
                    allocation_percentages[strategy_index] = ticker_allocation * strategy_proportion
                    log(f"Strategy {strategy_index} adjusted score: {adjusted_scores[i]:.6f}, " +
                        f"proportion: {strategy_proportion:.4f}, " +
                        f"allocation: {allocation_percentages[strategy_index]:.4f}%", "info")

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
        
        # Create adjusted scores - use a very small value for zero scores
        adjusted_ticker_scores = {}
        for ticker, score in ticker_total_scores.items():
            if score <= 0:
                # Use a very small positive value for zero scores
                adjusted_ticker_scores[ticker] = 0.0001
                log(f"Ticker {ticker} has zero score, using minimal value 0.0001", "info")
            else:
                adjusted_ticker_scores[ticker] = score
        
        # Calculate initial ticker-level allocations
        total_adjusted_score = sum(adjusted_ticker_scores.values())
        ticker_allocations = {
            ticker: (score / total_adjusted_score) * 100 if total_adjusted_score > 0 else 0
            for ticker, score in adjusted_ticker_scores.items()
        }
        
        # Sort tickers by their original scores for logging
        sorted_tickers = sorted(
            ticker_allocations.keys(),
            key=lambda t: ticker_total_scores[t],
            reverse=True
        )
        
        log(f"Adjusted ticker scores: {adjusted_ticker_scores}", "info")
        log(f"Initial ticker allocations: {ticker_allocations}", "info")
        
        # Log allocations in order of original scores
        log("Allocations in order of original scores:", "info")
        for ticker in sorted_tickers:
            log(f"{ticker}: score={ticker_total_scores[ticker]:.6f}, allocation={ticker_allocations[ticker]:.4f}%", "info")
        
        log(f"Initial ticker allocations: {ticker_allocations}", "info")
        
        if ratio_based_allocation:
            # Get allocations in the same order as sorted_tickers
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
        # If all values are the same, return equal normalized values (0.5)
        # instead of all zeros to ensure fair allocation
        return [0.5] * len(values)
    return [(value - min_value) / (max_value - min_value) for value in values]
