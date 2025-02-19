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


def calculate_allocation_scores(
    strategy_expectancies: List[float],
    strategy_risk_contributions: List[float],
    strategy_alphas: List[float],
    strategy_efficiencies: List[float],
    log: Callable[[str, str], None]
) -> List[float]:
    """Calculate allocation scores for each strategy.

    Args:
        strategy_expectancies (List[float]): List of strategy expectancies
        strategy_risk_contributions (List[float]): List of risk contributions
        strategy_alphas (List[float]): List of strategy alphas
        strategy_efficiencies (List[float]): List of strategy efficiencies
        log: Callable[[str, str], None]

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

        log(f"Allocation scores: {allocation_scores}", "info")
        return allocation_scores

    except Exception as e:
        log(f"Error calculating allocation scores: {str(e)}", "error")
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
