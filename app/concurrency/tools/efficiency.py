"""Efficiency score calculation for concurrency analysis."""

from typing import Callable, Dict, List, Optional, Tuple


def calculate_strategy_efficiency(
    correlation: float,
    concurrent_ratio: float,
    exclusive_ratio: float,
    inactive_ratio: float,
    log: Callable[[str, str], None],
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
        log(
            f"Ratios - concurrent: {concurrent_ratio}, exclusive: {exclusive_ratio}, inactive: {inactive_ratio}",
            "info",
        )

        # Calculate multipliers
        diversification = 1 - correlation

        # Calculate independence using the improved formula
        independence = calculate_independence_factor(
            exclusive_ratio, concurrent_ratio, inactive_ratio
        )

        # Log a warning if exclusive_ratio is 0, but we're still using a better
        # independence value
        if exclusive_ratio <= 0:
            log(
                f"Note: exclusive_ratio is {exclusive_ratio}, using improved independence calculation: {independence:.4f}",
                "info",
            )

        activity = 1 - inactive_ratio

        # Calculate efficiency with adjusted independence to be less sensitive to low values
        # This ensures that even with low independence, efficiency doesn't drop too low
        adjusted_independence = 0.2 + 0.8 * independence
        efficiency = diversification * adjusted_independence * activity

        # Ensure efficiency is at least a small positive value
        if efficiency <= 0:
            log(
                f"Warning: Calculated efficiency is {efficiency}, setting to minimum value",
                "warning",
            )
            efficiency = 0.0001

        log("Strategy efficiency components:", "info")
        log(f"Diversification: {diversification}", "info")
        log(f"Independence (raw): {independence}", "info")
        log(f"Independence (adjusted): {adjusted_independence}", "info")
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
    strategy_risk_contributions: List[float],
    avg_correlation: float,
    concurrent_periods: int,
    exclusive_periods: int,
    inactive_periods: int,
    total_periods: int,
    log: Callable[[str, str], None],
) -> Dict[str, float]:
    """Calculate portfolio-level efficiency metrics with risk adjustment.

    Args:
        strategy_efficiencies (List[float]): List of individual strategy efficiencies
        strategy_expectancies (List[float]): List of strategy expectancies
        strategy_allocations (List[float]): List of strategy allocations
        strategy_risk_contributions (List[float]): List of risk contributions for each strategy
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

        # Initialize metrics dictionary
        metrics = {"total_weighted_expectancy": 0.0}

        # Calculate ratios from raw counts
        concurrent_ratio = concurrent_periods / total_periods
        exclusive_ratio = exclusive_periods / total_periods
        inactive_ratio = inactive_periods / total_periods

        # Calculate portfolio multipliers
        diversification = 1 - avg_correlation

        # Calculate independence using the improved formula
        independence = calculate_independence_factor(
            exclusive_ratio, concurrent_ratio, inactive_ratio
        )

        # Log a note if exclusive_ratio is 0, but we're still using a better
        # independence value
        if exclusive_ratio <= 0:
            log(
                f"Note: exclusive_ratio is {exclusive_ratio}, using improved independence calculation: {independence:.4f}",
                "info",
            )

        activity = 1 - inactive_ratio

        # Calculate weighted efficiencies with equal allocations
        weighted_efficiencies = []
        total_efficiency = 0.0

        log("Using equal weighting for weighted efficiency calculation", "info")

        # Calculate weighted efficiencies with equal allocations
        equal_allocation = 1.0 / len(strategy_efficiencies)

        # Log the inputs for debugging
        log(f"Strategy efficiencies: {strategy_efficiencies}", "info")
        log(f"Strategy expectancies: {strategy_expectancies}", "info")
        log(
            f"Using equal allocation: {equal_allocation:.6f} for all strategies", "info"
        )
        log(f"Strategy risk contributions: {strategy_risk_contributions}", "info")

        for i, (eff, exp, risk) in enumerate(
            zip(
                strategy_efficiencies,
                strategy_expectancies,
                strategy_risk_contributions,
            )
        ):
            # Use equal allocation for all strategies
            norm_alloc = equal_allocation
            # Calculate risk-adjusted weight (lower risk is better)
            risk_factor = calculate_risk_factor(
                risk
            )  # Lower risk contribution is better

            # Combine factors (efficiency * expectancy * allocation * risk_factor)
            weighted_eff = eff * exp * norm_alloc * risk_factor
            weighted_efficiencies.append(weighted_eff)

            # FIXED: Calculate weighted expectancy correctly (average, not sum)
            if i == 0:  # Only initialize once
                metrics["total_weighted_expectancy"] = 0.0
                metrics["expectancy_calculation_debug"] = []

            # Calculate weighted contribution (allocation * expectancy)
            weighted_expectancy_contribution = exp * norm_alloc
            metrics["total_weighted_expectancy"] += weighted_expectancy_contribution

            # Store debug info for validation
            metrics["expectancy_calculation_debug"].append(
                {
                    "strategy": i,
                    "expectancy": exp,
                    "allocation": norm_alloc,
                    "contribution": weighted_expectancy_contribution,
                }
            )

            log(f"Strategy {i} weighted efficiency components:", "info")
            log(f"  Base efficiency: {eff:.6f}", "info")
            log(f"  Expectancy: {exp:.6f}", "info")
            log(f"  Equal allocation: {norm_alloc:.6f}", "info")
            log(f"  Risk factor (1 - {risk:.6f}): {risk_factor:.6f}", "info")
            log(f"  Weighted efficiency: {weighted_eff:.6f}", "info")

        # Calculate total weighted efficiency
        total_efficiency = sum(weighted_efficiencies)
        log(
            f"Total weighted efficiency (with equal allocations): {total_efficiency:.6f}",
            "info",
        )

        # Calculate adjusted independence to be less sensitive to low values
        adjusted_independence = 0.2 + 0.8 * independence

        # Calculate final portfolio efficiency
        # Note: We don't multiply by diversification, adjusted_independence, and activity again
        # because these structural components are already incorporated in the base efficiency
        # calculation that feeds into total_efficiency

        # Use a simple average of strategy efficiencies
        log(
            "Using simple average of strategy efficiencies for portfolio efficiency",
            "info",
        )
        portfolio_efficiency = (
            sum(strategy_efficiencies) / len(strategy_efficiencies)
            if strategy_efficiencies
            else 0.0
        )

        # Log the components for debugging
        log("Portfolio efficiency calculation components:", "info")
        log(f"  Total weighted efficiency: {total_efficiency:.6f}", "info")
        log(
            f"  Note: Diversification ({diversification:.6f}), Independence ({adjusted_independence:.6f}), and Activity ({activity:.6f})",
            "info",
        )
        log(
            "  multipliers are already incorporated in the base efficiency calculation",
            "info",
        )
        log("  and are not applied again at the portfolio level", "info")
        log(f"  Portfolio efficiency: {portfolio_efficiency:.6f}", "info")

        # Ensure portfolio efficiency is at least a small positive value
        if portfolio_efficiency <= 0:
            log(
                f"Warning: Calculated portfolio efficiency is {portfolio_efficiency}, setting to minimum value",
                "warning",
            )
            portfolio_efficiency = 0.0001

        # If portfolio efficiency is still very low but individual strategy efficiencies are higher,
        # use a weighted average of strategy efficiencies as a floor
        if portfolio_efficiency < 0.01 and strategy_efficiencies:
            avg_strategy_efficiency = sum(strategy_efficiencies) / len(
                strategy_efficiencies
            )
            if avg_strategy_efficiency > portfolio_efficiency:
                log(
                    f"Portfolio efficiency ({portfolio_efficiency:.6f}) is much lower than average strategy efficiency ({avg_strategy_efficiency:.6f})",
                    "warning",
                )
                log(
                    "Setting portfolio efficiency to 50% of average strategy efficiency",
                    "info",
                )
                portfolio_efficiency = max(
                    portfolio_efficiency, avg_strategy_efficiency * 0.5
                )
                log(
                    f"Adjusted portfolio efficiency: {portfolio_efficiency:.6f}", "info"
                )

        # VALIDATION: Check expectancy calculation reasonableness
        _validate_expectancy_calculation(metrics, strategy_expectancies, log)

        portfolio_metrics = {
            "portfolio_efficiency": portfolio_efficiency,
            "weighted_efficiency": total_efficiency,
            "diversification_multiplier": diversification,
            "independence_multiplier": independence,
            "independence_multiplier_adjusted": adjusted_independence,
            "activity_multiplier": activity,
            "total_weighted_expectancy": metrics.get("total_weighted_expectancy", 0.0),
        }

        log(f"Portfolio metrics calculated: {portfolio_metrics}", "info")
        return portfolio_metrics

    except Exception as e:
        log(f"Error calculating portfolio efficiency: {str(e)}", "error")
        raise


def calculate_independence_factor(
    exclusive_ratio: float, concurrent_ratio: float, inactive_ratio: float
) -> float:
    """Calculate an independence factor that provides a more nuanced measure of strategy independence.

    Args:
        exclusive_ratio (float): Ratio of exclusive trading periods
        concurrent_ratio (float): Ratio of concurrent trading periods
        inactive_ratio (float): Ratio of inactive periods

    Returns:
        float: Independence factor between 0.1 and 1.0
    """
    # Base independence on the ratio of exclusive to active periods
    active_ratio = 1 - inactive_ratio
    if active_ratio <= 0:
        return 0.1  # Minimum value for completely inactive strategies

    # Calculate the proportion of active periods that are exclusive
    exclusive_proportion = exclusive_ratio / active_ratio

    # Calculate the proportion of active periods that are concurrent
    concurrent_proportion = concurrent_ratio / active_ratio

    # Calculate independence as a function of these proportions
    # This formula gives higher scores to strategies with more exclusive periods
    # but doesn't severely penalize strategies with no exclusive periods
    independence = 0.1 + 0.9 * (
        exclusive_proportion / (exclusive_proportion + concurrent_proportion)
        if (exclusive_proportion + concurrent_proportion) > 0
        else 0.1
    )

    return independence


def calculate_risk_factor(risk: float) -> float:
    """Calculate a risk factor where lower risk results in a higher factor.

    Args:
        risk (float): Risk value (either raw or normalized)

    Returns:
        float: Risk factor where lower risk gives higher value
    """
    # Invert the risk value to get the risk factor
    # This ensures that lower risk results in a higher factor
    return 1 - risk


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


def _validate_expectancy_calculation(
    metrics: Dict[str, float],
    strategy_expectancies: List[float],
    log: Callable[[str, str], None],
) -> None:
    """
    Validate that expectancy calculation is reasonable and doesn't show unit confusion.

    This function checks for the expectancy magnitude issue where values become
    unrealistically large due to incorrect aggregation.
    """
    try:
        total_weighted_expectancy = metrics.get("total_weighted_expectancy", 0)
        debug_info: list = metrics.get("expectancy_calculation_debug", [])
        if not isinstance(debug_info, list):
            debug_info = []

        if strategy_expectancies:
            # Calculate simple average for comparison
            simple_average = sum(strategy_expectancies) / len(strategy_expectancies)

            # Check for unrealistic magnitude
            magnitude_ratio = (
                abs(total_weighted_expectancy / simple_average)
                if simple_average != 0
                else 0
            )

            log("Expectancy validation:", "info")
            log(
                f"  Individual expectancies: {[f'{e:.3f}' for e in strategy_expectancies]}",
                "info",
            )
            log(f"  Simple average: {simple_average:.3f}", "info")
            log(f"  Weighted portfolio: {total_weighted_expectancy:.3f}", "info")
            log(f"  Magnitude ratio: {magnitude_ratio:.2f}×", "info")

            # Validate reasonableness
            if magnitude_ratio > 50:
                log(
                    f"WARNING: Expectancy magnitude suspiciously high! Portfolio: {total_weighted_expectancy:.2f}, Average: {simple_average:.2f}",
                    "warning",
                )
                log(
                    "This suggests expectancies are being summed instead of averaged",
                    "warning",
                )

            elif magnitude_ratio > 10:
                log(
                    f"WARNING: Expectancy magnitude high. Portfolio: {total_weighted_expectancy:.2f}, Average: {simple_average:.2f}",
                    "warning",
                )

            elif abs(total_weighted_expectancy) > 1000:
                log(
                    "WARNING: Expectancy magnitude suggests unit confusion (should be per-trade dollars, not percentages)",
                    "warning",
                )

            else:
                log(
                    f"Expectancy calculation validated: Portfolio={total_weighted_expectancy:.3f}, Average={simple_average:.3f}",
                    "info",
                )

            # Debug detailed calculation
            if debug_info:
                log("Expectancy calculation breakdown:", "info")
                for item in debug_info:
                    log(
                        f"  Strategy {item['strategy']}: {item['expectancy']:.3f} × {item['allocation']:.3f} = {item['contribution']:.3f}",
                        "info",
                    )

    except Exception as e:
        log(f"Error in expectancy validation: {str(e)}", "error")


def convert_expectancy_units(
    expectancy_value: float,
    source_unit: str = "percentage",
    target_unit: str = "decimal",
    log: Optional[Callable[[str, str], None]] = None,
) -> float:
    """
    Convert expectancy between different units (percentage vs decimal).

    Args:
        expectancy_value: The expectancy value to convert
        source_unit: "percentage" (0-100) or "decimal" (0-1)
        target_unit: "percentage" (0-100) or "decimal" (0-1)
        log: Optional logging function

    Returns:
        Converted expectancy value
    """
    if source_unit == target_unit:
        return expectancy_value

    if source_unit == "percentage" and target_unit == "decimal":
        result = expectancy_value / 100.0
    elif source_unit == "decimal" and target_unit == "percentage":
        result = expectancy_value * 100.0
    else:
        if log:
            log(f"Unknown unit conversion: {source_unit} to {target_unit}", "error")
        return expectancy_value

    if log:
        log(
            f"Converted expectancy: {expectancy_value} ({source_unit}) → {result} ({target_unit})",
            "info",
        )

    return result
