"""
Correlation Filter Module.

This module provides functionality to filter and limit strategy concurrency
based on correlation analysis, reducing risk concentration.
"""

from collections.abc import Callable
from enum import Enum
from typing import Any

import numpy as np


class CorrelationFilterMode(Enum):
    """Enumeration of correlation filter modes."""

    DISABLED = "disabled"  # No correlation filtering
    THRESHOLD = "threshold"  # Filter based on correlation threshold
    CLUSTERING = "clustering"  # Filter using correlation clustering
    DYNAMIC = "dynamic"  # Dynamically adjust based on market conditions


class ConcurrencyLimitMode(Enum):
    """Enumeration of concurrency limit modes."""

    DISABLED = "disabled"  # No concurrency limits
    FIXED = "fixed"  # Fixed maximum number of concurrent strategies
    ADAPTIVE = "adaptive"  # Adapt limit based on market conditions
    VOLATILITY_BASED = "volatility"  # Adjust limit based on market volatility


def filter_correlated_strategies(
    position_arrays: list[np.ndarray],
    strategy_ids: list[str],
    correlation_threshold: float = 0.5,
    mode: CorrelationFilterMode = CorrelationFilterMode.THRESHOLD,
    log: Callable[[str, str], None] | None = None,
) -> dict[str, list[str]]:
    """Filter strategies based on correlation analysis.

    Args:
        position_arrays: List of position arrays for each strategy
        strategy_ids: List of strategy IDs
        correlation_threshold: Correlation threshold for filtering
        mode: Correlation filter mode
        log: Optional logging function

    Returns:
        Dict[str, List[str]]: Dictionary mapping strategy groups to strategy IDs
    """
    if len(position_arrays) != len(strategy_ids):
        if log:
            log("Position arrays and strategy IDs must have the same length", "error")
        return {"all_strategies": strategy_ids}

    if mode == CorrelationFilterMode.DISABLED:
        # No filtering, return all strategies in a single group
        return {"all_strategies": strategy_ids}

    # Calculate correlation matrix
    correlation_matrix = np.zeros((len(position_arrays), len(position_arrays)))

    for i in range(len(position_arrays)):
        for j in range(len(position_arrays)):
            if i == j:
                correlation_matrix[i, j] = 1.0
            else:
                # Calculate correlation between position arrays
                correlation = float(
                    np.corrcoef(position_arrays[i], position_arrays[j])[0, 1],
                )
                correlation_matrix[i, j] = correlation

    if mode == CorrelationFilterMode.THRESHOLD:
        # Group strategies based on correlation threshold
        groups: dict[int, list[str]] = {}
        assigned_strategies = set()

        # Start with unassigned strategies
        for i, strategy_id in enumerate(strategy_ids):
            if strategy_id in assigned_strategies:
                continue

            # Create a new group
            group_name = f"group_{len(groups) + 1}"
            groups[group_name] = [strategy_id]
            assigned_strategies.add(strategy_id)

            # Find correlated strategies
            for j, other_id in enumerate(strategy_ids):
                if other_id in assigned_strategies:
                    continue

                # Check if correlation exceeds threshold
                if abs(correlation_matrix[i, j]) >= correlation_threshold:
                    # Add to group if correlated
                    groups[group_name].append(other_id)
                    assigned_strategies.add(other_id)

        # Add any remaining strategies to their own group
        if len(assigned_strategies) < len(strategy_ids):
            remaining = [sid for sid in strategy_ids if sid not in assigned_strategies]
            groups["uncorrelated_strategies"] = remaining

        if log:
            log(
                f"Grouped strategies into {len(groups)} correlation groups using threshold {correlation_threshold}",
                "info",
            )

        return groups

    if mode == CorrelationFilterMode.CLUSTERING:
        # Use hierarchical clustering to group strategies
        # This is a simplified implementation

        # Convert correlation matrix to distance matrix
        # (higher correlation = lower distance)
        distance_matrix = 1.0 - np.abs(correlation_matrix)

        # Simple clustering algorithm
        groups = _simple_hierarchical_clustering(
            distance_matrix,
            strategy_ids,
            correlation_threshold,
        )

        if log:
            log(
                f"Clustered strategies into {len(groups)} groups using hierarchical clustering",
                "info",
            )

        return groups

    if mode == CorrelationFilterMode.DYNAMIC:
        # Dynamic correlation filtering based on market conditions
        # This would typically use more sophisticated analysis

        # For now, use a simplified approach that adjusts the threshold
        # based on the average correlation in the matrix
        avg_correlation = np.mean(np.abs(correlation_matrix))

        # Adjust threshold based on average correlation
        dynamic_threshold = max(correlation_threshold, avg_correlation * 1.2)

        if log:
            log(
                f"Using dynamic correlation threshold: {dynamic_threshold:.2f} (base: {correlation_threshold:.2f})",
                "info",
            )

        # Use the adjusted threshold with the standard threshold-based approach
        return filter_correlated_strategies(
            position_arrays,
            strategy_ids,
            dynamic_threshold,
            CorrelationFilterMode.THRESHOLD,
            log,
        )

    # Invalid mode, return all strategies in a single group
    if log:
        log(
            f"Invalid correlation filter mode: {mode}. No filtering applied.",
            "warning",
        )
    return {"all_strategies": strategy_ids}


def _simple_hierarchical_clustering(
    distance_matrix: np.ndarray,
    strategy_ids: list[str],
    threshold: float,
) -> dict[str, list[str]]:
    """Simple hierarchical clustering implementation.

    Args:
        distance_matrix: Distance matrix between strategies
        strategy_ids: List of strategy IDs
        threshold: Distance threshold for clustering

    Returns:
        Dict[str, List[str]]: Dictionary mapping cluster names to strategy IDs
    """
    # Initialize each strategy as its own cluster
    clusters = [{i} for i in range(len(strategy_ids))]

    # Iteratively merge clusters
    while len(clusters) > 1:
        # Find the two closest clusters
        min_distance = float("inf")
        merge_i, merge_j = -1, -1

        for i in range(len(clusters)):
            for j in range(i + 1, len(clusters)):
                # Calculate average distance between clusters
                cluster_distances = []

                for idx_i in clusters[i]:
                    for idx_j in clusters[j]:
                        cluster_distances.append(distance_matrix[idx_i, idx_j])

                avg_distance = np.mean(cluster_distances)

                if avg_distance < min_distance:
                    min_distance = avg_distance
                    merge_i, merge_j = i, j

        # If minimum distance exceeds threshold, stop merging
        if min_distance > threshold:
            break

        # Merge the two closest clusters
        clusters[merge_i].update(clusters[merge_j])
        clusters.pop(merge_j)

    # Convert cluster indices to strategy IDs
    result = {}
    for i, cluster in enumerate(clusters):
        cluster_name = f"cluster_{i + 1}"
        result[cluster_name] = [strategy_ids[idx] for idx in cluster]

    return result


def limit_strategy_concurrency(
    position_arrays: list[np.ndarray],
    strategy_ids: list[str],
    max_concurrent: int = 5,
    mode: ConcurrencyLimitMode = ConcurrencyLimitMode.FIXED,
    market_volatility: float | None | None = None,
    log: Callable[[str, str], None] | None = None,
) -> dict[str, np.ndarray]:
    """Limit the number of concurrent strategies.

    Args:
        position_arrays: List of position arrays for each strategy
        strategy_ids: List of strategy IDs
        max_concurrent: Maximum number of concurrent strategies
        mode: Concurrency limit mode
        market_volatility: Optional market volatility metric
        log: Optional logging function

    Returns:
        Dict[str, np.ndarray]: Dictionary mapping strategy IDs to modified position arrays
    """
    if len(position_arrays) != len(strategy_ids):
        if log:
            log("Position arrays and strategy IDs must have the same length", "error")
        return {
            sid: arr.copy()
            for sid, arr in zip(strategy_ids, position_arrays, strict=False)
        }

    if mode == ConcurrencyLimitMode.DISABLED:
        # No concurrency limits, return original position arrays
        return {
            sid: arr.copy()
            for sid, arr in zip(strategy_ids, position_arrays, strict=False)
        }

    # Determine the concurrency limit based on mode
    limit = max_concurrent

    if mode == ConcurrencyLimitMode.ADAPTIVE:
        # Adapt limit based on number of strategies
        # More strategies = higher limit, but with diminishing returns
        limit = min(max_concurrent, max(3, int(np.sqrt(len(strategy_ids)))))

        if log:
            log(
                f"Using adaptive concurrency limit: {limit} (base: {max_concurrent})",
                "info",
            )

    elif (
        mode == ConcurrencyLimitMode.VOLATILITY_BASED and market_volatility is not None
    ):
        # Adjust limit based on market volatility
        # Higher volatility = lower limit

        # Normalize volatility to a 0-1 scale (assuming typical range is 0-0.1)
        normalized_volatility = min(1.0, market_volatility / 0.1)

        # Adjust limit: higher volatility = lower limit
        volatility_factor = 1.0 - normalized_volatility * 0.5  # 0.5-1.0 range
        limit = max(2, int(max_concurrent * volatility_factor))

        if log:
            log(
                f"Using volatility-based concurrency limit: {limit} (base: {max_concurrent}, volatility: {market_volatility:.4f})",
                "info",
            )

    # Create modified position arrays
    modified_positions = {
        sid: arr.copy() for sid, arr in zip(strategy_ids, position_arrays, strict=False)
    }

    # Stack position arrays to create a matrix
    position_matrix = np.column_stack(list(position_arrays))

    # Count active strategies at each time step
    active_count = np.sum(position_matrix != 0, axis=1)

    # Identify time steps where too many strategies are active
    excess_indices = np.where(active_count > limit)[0]

    if len(excess_indices) == 0:
        # No excess concurrency, return original arrays
        return modified_positions

    # Process each time step with excess concurrency
    for idx in excess_indices:
        # Get active strategies at this time step
        active_strategies = []

        for i, arr in enumerate(position_arrays):
            if idx < len(arr) and arr[idx] != 0:
                active_strategies.append((i, strategy_ids[i], arr[idx]))

        # Sort strategies by priority (could use various metrics)
        # For now, use absolute position value as a simple priority metric
        active_strategies.sort(key=lambda x: abs(x[2]), reverse=True)

        # Keep only the top strategies up to the limit
        for i, _, _ in active_strategies[limit:]:
            # Set position to zero for excess strategies
            modified_positions[strategy_ids[i]][idx] = 0

    if log:
        total_reduced = sum(
            1
            for arr in modified_positions.values()
            if not np.array_equal(arr, position_arrays[strategy_ids.index(sid)])
        )
        log(
            f"Limited concurrency to {limit} strategies. Modified {total_reduced} strategy positions.",
            "info",
        )

    return modified_positions


def get_correlation_filter_config(
    config: dict[str, Any],
) -> tuple[CorrelationFilterMode, float]:
    """Get correlation filter configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple[CorrelationFilterMode, float]: Correlation filter mode and threshold
    """
    mode_str = config.get("CORRELATION_FILTER_MODE", "disabled")
    threshold = config.get("CORRELATION_THRESHOLD", 0.5)

    try:
        mode = CorrelationFilterMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        mode = CorrelationFilterMode.DISABLED

    # Ensure threshold is a valid float between 0 and 1
    if not isinstance(threshold, int | float) or threshold < 0 or threshold > 1:
        threshold = 0.5

    return mode, threshold


def get_concurrency_limit_config(
    config: dict[str, Any],
) -> tuple[ConcurrencyLimitMode, int]:
    """Get concurrency limit configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple[ConcurrencyLimitMode, int]: Concurrency limit mode and maximum concurrent strategies
    """
    mode_str = config.get("CONCURRENCY_LIMIT_MODE", "disabled")
    max_concurrent = config.get("MAX_CONCURRENT_STRATEGIES", 5)

    try:
        mode = ConcurrencyLimitMode(mode_str)
    except ValueError:
        # Invalid mode, return default
        mode = ConcurrencyLimitMode.DISABLED

    # Ensure max_concurrent is a valid positive integer
    if not isinstance(max_concurrent, int) or max_concurrent < 1:
        max_concurrent = 5

    return mode, max_concurrent
