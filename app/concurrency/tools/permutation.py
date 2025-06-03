"""Strategy permutation analysis for optimization.

This module provides functionality for generating and analyzing permutations
of trading strategies to find the most efficient combinations.
"""

import time
from itertools import combinations
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.tools.portfolio import StrategyConfig


def generate_strategy_permutations(
    strategies: List[StrategyConfig], min_strategies: int = 3
) -> List[List[StrategyConfig]]:
    """Generate all valid permutations of strategies with at least min_strategies per permutation.

    Args:
        strategies (List[StrategyConfig]): List of all available strategies
        min_strategies (int): Minimum number of strategies per permutation

    Returns:
        List[List[StrategyConfig]]: List of strategy permutations

    Raises:
        ValueError: If min_strategies is less than 2 or greater than the number of strategies
    """
    if min_strategies < 2:
        raise ValueError("min_strategies must be at least 2")

    if min_strategies > len(strategies):
        raise ValueError(
            f"min_strategies ({min_strategies}) cannot be greater than the number of strategies ({len(strategies)})"
        )

    permutations = []

    # Generate all combinations from min_strategies to total number of strategies
    for r in range(min_strategies, len(strategies) + 1):
        for combo in combinations(range(len(strategies)), r):
            permutation = [strategies[i] for i in combo]
            permutations.append(permutation)

    return permutations


def analyze_permutation(
    permutation: List[StrategyConfig],
    process_strategies_func: Callable,
    analyze_concurrency_func: Callable,
    log: Callable[[str, str], None],
) -> Tuple[Dict[str, Any], List[Any]]:
    """Analyze a single permutation of strategies.

    Args:
        permutation (List[StrategyConfig]): A permutation of strategies to analyze
        process_strategies_func (Callable): Function to process strategies
        analyze_concurrency_func (Callable): Function to analyze concurrency
        log (Callable[[str, str], None]): Logging function

    Returns:
        Tuple[Dict[str, Any], List[Any]]: Analysis stats and aligned data

    Raises:
        Exception: If analysis fails
    """
    # Set equal allocations for all strategies in the permutation
    # This ensures fair comparison between different permutations
    equal_allocation = 1.0 / len(permutation)
    for strategy in permutation:
        strategy["ALLOCATION"] = equal_allocation

    log(
        f"Using equal allocations ({equal_allocation:.4f}) for all strategies in permutation",
        "info",
    )

    # Process strategies and get data
    strategy_data, updated_strategies = process_strategies_func(permutation, log)

    # Analyze concurrency
    stats, aligned_data = analyze_concurrency_func(
        strategy_data, updated_strategies, log
    )

    return stats, aligned_data


def find_optimal_permutation(
    strategies: List[StrategyConfig],
    process_strategies_func: Callable,
    analyze_concurrency_func: Callable,
    log: Callable[[str, str], None],
    min_strategies: int = 3,
    max_permutations: Optional[int] = None,
) -> Tuple[List[StrategyConfig], Dict[str, Any], List[Any]]:
    """Find the optimal permutation of strategies based on risk-adjusted efficiency score.

    The efficiency_score used for comparison is a comprehensive metric that includes:
    - Structural components (diversification, independence, activity)
    - Performance metrics (expectancy, risk factors, allocation)

    Args:
        strategies (List[StrategyConfig]): List of all available strategies
        process_strategies_func (Callable): Function to process strategies
        analyze_concurrency_func (Callable): Function to analyze concurrency
        log (Callable[[str, str], None]): Logging function
        min_strategies (int): Minimum number of strategies per permutation
        max_permutations (Optional[int]): Maximum permutations to analyze

    Returns:
        Tuple[List[StrategyConfig], Dict[str, Any], List[Any]]:
            Best permutation, its stats, and aligned data

    Raises:
        ValueError: If no valid permutations are found or if min_strategies is invalid
    """
    log("Starting permutation analysis for optimization", "info")

    # Generate all valid permutations
    permutations = generate_strategy_permutations(strategies, min_strategies)
    total_permutations = len(permutations)
    log(f"Generated {total_permutations} valid permutations", "info")

    # Limit permutations if max_permutations is specified
    if max_permutations and max_permutations < total_permutations:
        log(f"Limiting analysis to {max_permutations} permutations", "info")
        # Prioritize permutations with fewer strategies for efficiency
        permutations.sort(key=len)
        permutations = permutations[:max_permutations]
        total_permutations = len(permutations)

    # Track best permutation and its metrics
    best_permutation = None
    best_efficiency = 0.0
    best_stats = None
    best_aligned_data = None

    # Track progress
    progress_interval = max(
        1, total_permutations // 10
    )  # Report progress at 10% intervals
    start_time = time.time()

    # Analyze each permutation
    for i, permutation in enumerate(permutations):
        # Log progress at intervals
        if i % progress_interval == 0 or i == total_permutations - 1:
            elapsed_time = time.time() - start_time
            progress_pct = (i / total_permutations) * 100
            remaining_permutations = total_permutations - i - 1

            # Estimate remaining time
            if i > 0:
                avg_time_per_permutation = elapsed_time / i
                estimated_remaining_time = (
                    avg_time_per_permutation * remaining_permutations
                )
                log(
                    f"Progress: {progress_pct:.1f}% ({i+1}/{total_permutations}) - "
                    + f"Est. remaining time: {estimated_remaining_time:.1f} seconds",
                    "info",
                )
            else:
                log(
                    f"Progress: {progress_pct:.1f}% ({i+1}/{total_permutations})",
                    "info",
                )

        log(
            f"Analyzing permutation {i+1}/{total_permutations} with {len(permutation)} strategies",
            "debug",
        )

        try:
            # Analyze this permutation
            stats, aligned_data = analyze_permutation(
                permutation, process_strategies_func, analyze_concurrency_func, log
            )

            # Extract risk-adjusted efficiency score
            efficiency = stats["efficiency_score"]

            log(f"Permutation {i+1} risk-adjusted efficiency: {efficiency:.4f}", "info")

            # Update best if this is better
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_permutation = permutation
                best_stats = stats
                best_aligned_data = aligned_data
                log(
                    f"New best permutation found! Risk-adjusted efficiency: {best_efficiency:.4f}",
                    "info",
                )

        except Exception as e:
            log(f"Error analyzing permutation {i+1}: {str(e)}", "error")
            continue

    # Log final results
    total_time = time.time() - start_time
    if best_permutation:
        log(
            f"Permutation analysis complete in {total_time:.1f} seconds. Best efficiency: {best_efficiency:.4f}",
            "info",
        )
        return best_permutation, best_stats, best_aligned_data
    else:
        log("No valid permutations found", "error")
        raise ValueError("No valid permutations found")
