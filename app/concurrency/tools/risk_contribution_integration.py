"""
Integration module for the fixed risk contribution calculator.

This module provides the integration point between the existing concurrency
analysis system and the new mathematically correct risk contribution calculator.
"""

import logging
from typing import Any

import numpy as np

from app.concurrency.tools.risk_contribution_calculator import (
    calculate_risk_contributions_fixed,
)


logger = logging.getLogger(__name__)


def integrate_fixed_risk_calculations(analysis_module):
    """
    Monkey patch the analysis module to use the fixed risk calculations.

    This is a temporary integration method that allows us to test the
    fixed calculations without modifying the existing codebase.

    Args:
        analysis_module: The analysis module to patch
    """
    # Store original function
    original_calculate_risk = getattr(
        analysis_module, "calculate_risk_contributions", None
    )

    if original_calculate_risk:
        # Replace with fixed version
        analysis_module.calculate_risk_contributions = (
            calculate_risk_contributions_fixed
        )
        logger.info("Integrated fixed risk contribution calculator")

        # Store original for rollback
        analysis_module._original_calculate_risk_contributions = original_calculate_risk
    else:
        logger.warning("Could not find calculate_risk_contributions to patch")


def rollback_to_original_calculations(analysis_module):
    """
    Rollback to the original risk calculation implementation.

    Args:
        analysis_module: The analysis module to restore
    """
    original_func = getattr(
        analysis_module, "_original_calculate_risk_contributions", None
    )

    if original_func:
        analysis_module.calculate_risk_contributions = original_func
        logger.info("Rolled back to original risk contribution calculator")
    else:
        logger.warning("No original function found to rollback to")


def compare_risk_calculations(
    position_arrays: list[np.ndarray],
    data_list: list[Any],
    strategy_allocations: list[float],
    strategy_configs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Compare the original and fixed risk contribution calculations.

    This function runs both implementations and compares the results,
    useful for validation and testing.

    Args:
        position_arrays: List of position arrays for each strategy
        data_list: List of dataframes with price data
        strategy_allocations: List of strategy allocations
        strategy_configs: Optional list of strategy configurations

    Returns:
        Dictionary containing comparison results
    """
    # Mock log function
    logs_original = []
    logs_fixed = []

    def log_original(msg, level):
        logs_original.append((msg, level))

    def log_fixed(msg, level):
        logs_fixed.append((msg, level))

    # Calculate with fixed implementation (only option now)
    try:
        result_fixed = calculate_risk_contributions_fixed(
            position_arrays,
            data_list,
            strategy_allocations,
            log_fixed,
            strategy_configs,
        )
    except Exception as e:
        logger.error(f"Fixed calculation failed: {e}")
        result_fixed = None

    # No legacy implementation comparison since it's been removed
    result_original = None

    # Compare results
    comparison = {"original": result_original, "fixed": result_fixed, "comparison": {}}

    if result_original and result_fixed:
        # Calculate risk contribution sums
        original_sum = sum(
            v for k, v in result_original.items() if k.endswith("_risk_contrib")
        )
        fixed_sum = sum(
            v for k, v in result_fixed.items() if k.endswith("_risk_contrib")
        )

        comparison["comparison"]["original_sum"] = original_sum
        comparison["comparison"]["fixed_sum"] = fixed_sum
        comparison["comparison"]["original_sum_pct"] = f"{original_sum * 100:.2f}%"
        comparison["comparison"]["fixed_sum_pct"] = f"{fixed_sum * 100:.2f}%"
        comparison["comparison"]["sum_difference"] = original_sum - fixed_sum
        comparison["comparison"]["sum_difference_pct"] = (
            f"{(original_sum - fixed_sum) * 100:.2f}%"
        )

        # Compare individual contributions
        strategy_comparison = []
        n_strategies = len(position_arrays)

        for i in range(n_strategies):
            key = f"strategy_{i+1}_risk_contrib"
            if key in result_original and key in result_fixed:
                orig_val = result_original[key]
                fixed_val = result_fixed[key]
                strategy_comparison.append(
                    {
                        "strategy": f"strategy_{i+1}",
                        "original": orig_val,
                        "fixed": fixed_val,
                        "difference": orig_val - fixed_val,
                        "original_pct": f"{orig_val * 100:.2f}%",
                        "fixed_pct": f"{fixed_val * 100:.2f}%",
                        "difference_pct": f"{(orig_val - fixed_val) * 100:.2f}%",
                    }
                )

        comparison["comparison"]["strategies"] = strategy_comparison

        # Log summary
        logger.info(
            f"Risk contribution sum - Original: {original_sum*100:.2f}%, Fixed: {fixed_sum*100:.2f}%"
        )
        logger.info(f"Difference: {(original_sum - fixed_sum)*100:.2f}%")

    return comparison


def validate_portfolio_risk_contributions(
    portfolio_path: str, use_fixed: bool = True
) -> dict[str, Any]:
    """
    Validate risk contributions for a specific portfolio.

    Args:
        portfolio_path: Path to the portfolio file
        use_fixed: Whether to use the fixed calculation

    Returns:
        Validation results
    """
    # This would integrate with the portfolio loading system
    # For now, return a placeholder
    return {
        "portfolio": portfolio_path,
        "use_fixed": use_fixed,
        "status": "Not implemented - requires portfolio loading integration",
    }


def create_risk_contribution_report(
    risk_metrics: dict[str, Any], output_path: str | None | None = None
) -> str:
    """
    Create a formatted report of risk contributions.

    Args:
        risk_metrics: Risk metrics from the calculator
        output_path: Optional path to save the report

    Returns:
        Formatted report string
    """
    report_lines = [
        "Risk Contribution Analysis Report",
        "=" * 50,
        "",
        f"Portfolio Volatility: {risk_metrics.get('portfolio_volatility', 0):.6f}",
        f"Portfolio Variance: {risk_metrics.get('portfolio_variance', 0):.6f}",
        "",
        "Risk Contributions by Strategy:",
        "-" * 40,
    ]

    if "risk_contributions" in risk_metrics:
        for strategy, data in risk_metrics["risk_contributions"].items():
            report_lines.extend(
                [
                    f"\n{strategy}:",
                    f"  Weight: {data['weight']:.4f}",
                    f"  Marginal Contribution: {data['marginal_contribution']:.6f}",
                    f"  Risk Contribution: {data['risk_contribution']:.6f}",
                    f"  Risk Contribution %: {data['risk_contribution_pct_display']}",
                ]
            )

    # Add validation section
    report_lines.extend(["", "Validation:", "-" * 40])

    # Calculate sum of risk contributions
    if "risk_contributions" in risk_metrics:
        total_contrib = sum(
            data["risk_contribution_pct"]
            for data in risk_metrics["risk_contributions"].values()
        )
        report_lines.append(f"Total Risk Contributions: {total_contrib*100:.2f}%")

        if np.isclose(total_contrib, 1.0, rtol=1e-3):
            report_lines.append("✓ Risk contributions correctly sum to 100%")
        else:
            report_lines.append("✗ WARNING: Risk contributions do not sum to 100%!")

    report = "\n".join(report_lines)

    # Save if path provided
    if output_path:
        with open(output_path, "w") as f:
            f.write(report)
        logger.info(f"Risk contribution report saved to {output_path}")

    return report
