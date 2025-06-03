"""
Risk accuracy validation with meaningful exceptions for portfolio variance estimation.

This module implements strict validation strategies that ensure data quality
and throw meaningful exceptions rather than using fallback values.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import polars as pl

from app.tools.exceptions import (
    CovarianceMatrixError,
    DataAlignmentError,
    PortfolioVarianceError,
    RiskCalculationError,
)


class ValidationLevel(Enum):
    """Validation strictness levels."""

    STRICT = "strict"  # Fail fast on any quality issues
    MODERATE = "moderate"  # Allow minor quality issues with warnings
    PERMISSIVE = "permissive"  # Only fail on critical errors


@dataclass
class ValidationResult:
    """Container for validation results."""

    is_valid: bool
    level: ValidationLevel
    messages: List[str]
    warnings: List[str]
    quality_score: float
    corrective_actions: List[str]


class RiskAccuracyValidator:
    """
    Comprehensive validation for risk calculation accuracy.

    Implements strict validation with meaningful exceptions and provides
    detailed diagnostics for troubleshooting data quality issues.
    """

    def __init__(
        self,
        log: Callable[[str, str], None],
        validation_level: ValidationLevel = ValidationLevel.STRICT,
    ):
        self.log = log
        self.validation_level = validation_level

        # Validation thresholds by level
        self.thresholds = {
            ValidationLevel.STRICT: {
                "min_observations": 30,
                "min_variance": 1e-8,
                "max_correlation": 0.95,
                "min_correlation": -0.95,
                "max_condition_number": 1000,
                "min_quality_score": 0.7,
                "max_missing_ratio": 0.05,
            },
            ValidationLevel.MODERATE: {
                "min_observations": 20,
                "min_variance": 1e-10,
                "max_correlation": 0.98,
                "min_correlation": -0.98,
                "max_condition_number": 5000,
                "min_quality_score": 0.5,
                "max_missing_ratio": 0.1,
            },
            ValidationLevel.PERMISSIVE: {
                "min_observations": 10,
                "min_variance": 1e-12,
                "max_correlation": 0.99,
                "min_correlation": -0.99,
                "max_condition_number": 10000,
                "min_quality_score": 0.3,
                "max_missing_ratio": 0.2,
            },
        }

    def validate_return_data(
        self, returns_matrix: np.ndarray, strategy_names: List[str]
    ) -> ValidationResult:
        """
        Validate return data quality for variance estimation.

        Args:
            returns_matrix: Matrix of returns (observations x strategies)
            strategy_names: List of strategy identifiers

        Returns:
            ValidationResult with validation outcome and diagnostics
        """
        messages = []
        warnings = []
        corrective_actions = []
        quality_factors = []

        thresholds = self.thresholds[self.validation_level]

        # Basic shape validation
        if returns_matrix.shape[1] != len(strategy_names):
            messages.append(
                f"Return matrix columns ({returns_matrix.shape[1]}) != strategy names ({len(strategy_names)})"
            )
            return ValidationResult(
                False,
                self.validation_level,
                messages,
                warnings,
                0.0,
                corrective_actions,
            )

        n_obs, n_strategies = returns_matrix.shape

        # 1. Sufficient observations check
        if n_obs < thresholds["min_observations"]:
            messages.append(
                f"Insufficient observations: {n_obs} < {thresholds['min_observations']} required"
            )
            corrective_actions.append(
                "Collect more historical data or use Bayesian/bootstrap methods"
            )
            if self.validation_level == ValidationLevel.STRICT:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

        quality_factors.append(min(1.0, n_obs / thresholds["min_observations"]))

        # 2. Data completeness check
        nan_count = np.sum(np.isnan(returns_matrix))
        inf_count = np.sum(np.isinf(returns_matrix))
        missing_ratio = (nan_count + inf_count) / returns_matrix.size

        if missing_ratio > thresholds["max_missing_ratio"]:
            messages.append(
                f"Too many missing/invalid values: {missing_ratio:.3f} > {thresholds['max_missing_ratio']:.3f}"
            )
            corrective_actions.append("Clean data or use interpolation methods")
            if self.validation_level in [
                ValidationLevel.STRICT,
                ValidationLevel.MODERATE,
            ]:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )
        elif missing_ratio > 0:
            warnings.append(
                f"Some missing/invalid values detected: {missing_ratio:.3f}"
            )

        quality_factors.append(1.0 - missing_ratio)

        # 3. Variance validation per strategy
        zero_variance_strategies = []
        low_variance_strategies = []

        for i, name in enumerate(strategy_names):
            strategy_returns = returns_matrix[:, i]
            valid_returns = strategy_returns[
                ~np.isnan(strategy_returns) & ~np.isinf(strategy_returns)
            ]

            if len(valid_returns) == 0:
                messages.append(f"Strategy {name} has no valid returns")
                continue

            strategy_var = np.var(valid_returns)

            if strategy_var <= 0:
                zero_variance_strategies.append(name)
            elif strategy_var < thresholds["min_variance"]:
                low_variance_strategies.append(name)

        if zero_variance_strategies:
            messages.append(
                f"Strategies with zero variance: {zero_variance_strategies}"
            )
            corrective_actions.append(
                "Remove constant strategies or check data quality"
            )
            if self.validation_level == ValidationLevel.STRICT:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

        if low_variance_strategies:
            warnings.append(
                f"Strategies with very low variance: {low_variance_strategies}"
            )

        # Variance quality score
        variances = [
            np.var(returns_matrix[:, i][~np.isnan(returns_matrix[:, i])])
            for i in range(n_strategies)
        ]
        valid_variances = [v for v in variances if v > 0]
        variance_quality = (
            len(valid_variances) / n_strategies if n_strategies > 0 else 0
        )
        quality_factors.append(variance_quality)

        # 4. Correlation matrix validation
        try:
            # Only use valid data for correlation calculation
            valid_mask = ~np.isnan(returns_matrix).any(axis=1)
            if np.sum(valid_mask) < 2:
                messages.append(
                    "Insufficient valid observations for correlation calculation"
                )
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

            valid_returns = returns_matrix[valid_mask, :]
            corr_matrix = np.corrcoef(valid_returns.T)

            # Check for perfect correlations
            perfect_corr_pairs = []
            high_corr_pairs = []

            for i in range(n_strategies):
                for j in range(i + 1, n_strategies):
                    corr_val = corr_matrix[i, j]

                    if not np.isnan(corr_val):
                        if abs(corr_val) >= 0.99:
                            perfect_corr_pairs.append(
                                (strategy_names[i], strategy_names[j], corr_val)
                            )
                        elif abs(corr_val) > thresholds["max_correlation"]:
                            high_corr_pairs.append(
                                (strategy_names[i], strategy_names[j], corr_val)
                            )

            if perfect_corr_pairs:
                messages.append(f"Perfect correlations detected: {perfect_corr_pairs}")
                corrective_actions.append(
                    "Remove redundant strategies or check for data duplication"
                )
                if self.validation_level == ValidationLevel.STRICT:
                    return ValidationResult(
                        False,
                        self.validation_level,
                        messages,
                        warnings,
                        0.0,
                        corrective_actions,
                    )

            if high_corr_pairs:
                warnings.append(f"High correlations detected: {high_corr_pairs}")
                if self.validation_level == ValidationLevel.STRICT:
                    corrective_actions.append(
                        "Consider reducing correlation through diversification"
                    )

            # Correlation quality score (penalize extreme correlations)
            corr_values = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
            valid_corr_values = corr_values[~np.isnan(corr_values)]

            if len(valid_corr_values) > 0:
                extreme_corr_ratio = np.sum(np.abs(valid_corr_values) > 0.9) / len(
                    valid_corr_values
                )
                correlation_quality = max(0.0, 1.0 - extreme_corr_ratio)
            else:
                correlation_quality = 0.5

            quality_factors.append(correlation_quality)

        except Exception as e:
            messages.append(f"Correlation matrix calculation failed: {str(e)}")
            corrective_actions.append("Check return data alignment and quality")
            quality_factors.append(0.0)
            if self.validation_level in [
                ValidationLevel.STRICT,
                ValidationLevel.MODERATE,
            ]:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

        # 5. Covariance matrix condition number
        try:
            cov_matrix = np.cov(valid_returns.T)
            condition_number = np.linalg.cond(cov_matrix)

            if condition_number > thresholds["max_condition_number"]:
                messages.append(
                    f"Covariance matrix ill-conditioned: condition number {condition_number:.0f}"
                )
                corrective_actions.append("Use regularization or shrinkage estimation")
                if self.validation_level == ValidationLevel.STRICT:
                    return ValidationResult(
                        False,
                        self.validation_level,
                        messages,
                        warnings,
                        0.0,
                        corrective_actions,
                    )
            elif condition_number > thresholds["max_condition_number"] / 2:
                warnings.append(
                    f"Covariance matrix condition number high: {condition_number:.0f}"
                )

            # Condition number quality score
            max_acceptable = thresholds["max_condition_number"]
            condition_quality = max(
                0.0, 1.0 - min(1.0, condition_number / max_acceptable)
            )
            quality_factors.append(condition_quality)

        except Exception as e:
            messages.append(f"Covariance matrix validation failed: {str(e)}")
            quality_factors.append(0.0)
            if self.validation_level == ValidationLevel.STRICT:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

        # 6. Overall quality score calculation
        if quality_factors:
            overall_quality = np.mean(quality_factors)
        else:
            overall_quality = 0.0

        # Final quality threshold check
        if overall_quality < thresholds["min_quality_score"]:
            messages.append(
                f"Overall data quality too low: {overall_quality:.3f} < {thresholds['min_quality_score']:.3f}"
            )
            corrective_actions.append(
                "Improve data collection or use more robust estimation methods"
            )
            if self.validation_level == ValidationLevel.STRICT:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    overall_quality,
                    corrective_actions,
                )

        # Log validation results
        is_valid = len(messages) == 0

        if is_valid:
            self.log(
                f"Return data validation passed (quality: {overall_quality:.3f})",
                "info",
            )
        else:
            self.log(f"Return data validation failed: {'; '.join(messages)}", "error")

        if warnings:
            self.log(f"Return data warnings: {'; '.join(warnings)}", "warning")

        return ValidationResult(
            is_valid=is_valid,
            level=self.validation_level,
            messages=messages,
            warnings=warnings,
            quality_score=overall_quality,
            corrective_actions=corrective_actions,
        )

    def validate_covariance_matrix(
        self, cov_matrix: np.ndarray, strategy_names: List[str]
    ) -> ValidationResult:
        """
        Validate covariance matrix properties for risk calculation.

        Args:
            cov_matrix: Covariance matrix
            strategy_names: List of strategy identifiers

        Returns:
            ValidationResult with covariance matrix validation
        """
        messages = []
        warnings = []
        corrective_actions = []
        quality_factors = []

        thresholds = self.thresholds[self.validation_level]

        # 1. Shape validation
        n_strategies = len(strategy_names)
        if cov_matrix.shape != (n_strategies, n_strategies):
            messages.append(
                f"Covariance matrix shape {cov_matrix.shape} != expected ({n_strategies}, {n_strategies})"
            )
            return ValidationResult(
                False,
                self.validation_level,
                messages,
                warnings,
                0.0,
                corrective_actions,
            )

        # 2. Symmetry check
        if not np.allclose(cov_matrix, cov_matrix.T, rtol=1e-10):
            messages.append("Covariance matrix is not symmetric")
            corrective_actions.append(
                "Ensure proper covariance calculation or enforce symmetry"
            )
            if self.validation_level == ValidationLevel.STRICT:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

        quality_factors.append(
            1.0 if np.allclose(cov_matrix, cov_matrix.T, rtol=1e-8) else 0.8
        )

        # 3. Positive definiteness
        try:
            eigenvalues = np.linalg.eigvals(cov_matrix)
            min_eigenvalue = np.min(eigenvalues)

            if min_eigenvalue <= 0:
                messages.append(
                    f"Covariance matrix not positive definite (min eigenvalue: {min_eigenvalue:.2e})"
                )
                corrective_actions.append(
                    "Use regularization or check for linear dependencies"
                )
                if self.validation_level in [
                    ValidationLevel.STRICT,
                    ValidationLevel.MODERATE,
                ]:
                    return ValidationResult(
                        False,
                        self.validation_level,
                        messages,
                        warnings,
                        0.0,
                        corrective_actions,
                    )
            elif min_eigenvalue < 1e-8:
                warnings.append(
                    f"Covariance matrix nearly singular (min eigenvalue: {min_eigenvalue:.2e})"
                )

            # Eigenvalue quality score
            eigenvalue_ratio = (
                min_eigenvalue / np.max(eigenvalues) if np.max(eigenvalues) > 0 else 0
            )
            eigenvalue_quality = min(
                1.0, max(0.0, np.log10(eigenvalue_ratio) + 8) / 8
            )  # Scale -8 to 0 -> 0 to 1
            quality_factors.append(eigenvalue_quality)

        except Exception as e:
            messages.append(f"Eigenvalue calculation failed: {str(e)}")
            quality_factors.append(0.0)
            if self.validation_level == ValidationLevel.STRICT:
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )

        # 4. Condition number
        try:
            condition_number = np.linalg.cond(cov_matrix)

            if condition_number > thresholds["max_condition_number"]:
                messages.append(
                    f"Covariance matrix ill-conditioned: {condition_number:.0f}"
                )
                corrective_actions.append("Apply shrinkage or regularization")
                if self.validation_level == ValidationLevel.STRICT:
                    return ValidationResult(
                        False,
                        self.validation_level,
                        messages,
                        warnings,
                        0.0,
                        corrective_actions,
                    )
            elif condition_number > thresholds["max_condition_number"] / 2:
                warnings.append(f"High condition number: {condition_number:.0f}")

            condition_quality = max(
                0.0,
                1.0 - min(1.0, condition_number / thresholds["max_condition_number"]),
            )
            quality_factors.append(condition_quality)

        except Exception as e:
            messages.append(f"Condition number calculation failed: {str(e)}")
            quality_factors.append(0.0)

        # 5. Diagonal dominance check
        try:
            diagonal_elements = np.diag(cov_matrix)
            if np.any(diagonal_elements <= 0):
                zero_var_indices = np.where(diagonal_elements <= 0)[0]
                zero_var_strategies = [strategy_names[i] for i in zero_var_indices]
                messages.append(
                    f"Zero/negative variances for strategies: {zero_var_strategies}"
                )
                corrective_actions.append(
                    "Remove strategies with zero variance or fix data"
                )
                if self.validation_level in [
                    ValidationLevel.STRICT,
                    ValidationLevel.MODERATE,
                ]:
                    return ValidationResult(
                        False,
                        self.validation_level,
                        messages,
                        warnings,
                        0.0,
                        corrective_actions,
                    )

            # Check for unreasonably small variances
            min_variance = thresholds["min_variance"]
            small_var_indices = np.where(diagonal_elements < min_variance)[0]
            if len(small_var_indices) > 0:
                small_var_strategies = [strategy_names[i] for i in small_var_indices]
                warnings.append(
                    f"Very small variances for strategies: {small_var_strategies}"
                )

            variance_quality = np.mean(diagonal_elements >= min_variance)
            quality_factors.append(variance_quality)

        except Exception as e:
            messages.append(f"Variance validation failed: {str(e)}")
            quality_factors.append(0.0)

        # 6. Correlation bounds check
        try:
            # Convert to correlation matrix
            std_devs = np.sqrt(np.diag(cov_matrix))
            std_matrix = np.outer(std_devs, std_devs)

            # Avoid division by zero
            with np.errstate(divide="ignore", invalid="ignore"):
                corr_matrix = np.divide(
                    cov_matrix,
                    std_matrix,
                    out=np.zeros_like(cov_matrix),
                    where=std_matrix != 0,
                )

            # Check correlation bounds
            off_diagonal = corr_matrix[np.triu_indices_from(corr_matrix, k=1)]
            valid_corr = off_diagonal[~np.isnan(off_diagonal)]

            if len(valid_corr) > 0:
                invalid_corr = np.sum((valid_corr < -1.01) | (valid_corr > 1.01))
                if invalid_corr > 0:
                    messages.append(
                        f"Invalid correlation values outside [-1,1]: {invalid_corr}"
                    )
                    corrective_actions.append(
                        "Check covariance calculation for numerical errors"
                    )
                    if self.validation_level == ValidationLevel.STRICT:
                        return ValidationResult(
                            False,
                            self.validation_level,
                            messages,
                            warnings,
                            0.0,
                            corrective_actions,
                        )

                correlation_quality = 1.0 - (invalid_corr / len(valid_corr))
            else:
                correlation_quality = 0.5

            quality_factors.append(correlation_quality)

        except Exception as e:
            warnings.append(f"Correlation bounds check failed: {str(e)}")
            quality_factors.append(0.5)

        # Calculate overall quality score
        overall_quality = np.mean(quality_factors) if quality_factors else 0.0

        # Final validation
        is_valid = len(messages) == 0

        if is_valid:
            self.log(
                f"Covariance matrix validation passed (quality: {overall_quality:.3f})",
                "info",
            )
        else:
            self.log(
                f"Covariance matrix validation failed: {'; '.join(messages)}", "error"
            )

        if warnings:
            self.log(f"Covariance matrix warnings: {'; '.join(warnings)}", "warning")

        return ValidationResult(
            is_valid=is_valid,
            level=self.validation_level,
            messages=messages,
            warnings=warnings,
            quality_score=overall_quality,
            corrective_actions=corrective_actions,
        )

    def validate_portfolio_weights(
        self, weights: np.ndarray, strategy_names: List[str]
    ) -> ValidationResult:
        """
        Validate portfolio weights for risk calculation.

        Args:
            weights: Array of portfolio weights
            strategy_names: List of strategy identifiers

        Returns:
            ValidationResult with weight validation
        """
        messages = []
        warnings = []
        corrective_actions = []

        # 1. Shape validation
        if len(weights) != len(strategy_names):
            messages.append(
                f"Weight array length ({len(weights)}) != strategy count ({len(strategy_names)})"
            )
            return ValidationResult(
                False,
                self.validation_level,
                messages,
                warnings,
                0.0,
                corrective_actions,
            )

        # 2. Value validation
        if np.any(np.isnan(weights)):
            nan_indices = np.where(np.isnan(weights))[0]
            nan_strategies = [strategy_names[i] for i in nan_indices]
            messages.append(f"NaN weights for strategies: {nan_strategies}")
            corrective_actions.append("Replace NaN weights with zero or equal weights")
            return ValidationResult(
                False,
                self.validation_level,
                messages,
                warnings,
                0.0,
                corrective_actions,
            )

        if np.any(np.isinf(weights)):
            inf_indices = np.where(np.isinf(weights))[0]
            inf_strategies = [strategy_names[i] for i in inf_indices]
            messages.append(f"Infinite weights for strategies: {inf_strategies}")
            corrective_actions.append("Replace infinite weights with finite values")
            return ValidationResult(
                False,
                self.validation_level,
                messages,
                warnings,
                0.0,
                corrective_actions,
            )

        if np.any(weights < 0):
            neg_indices = np.where(weights < 0)[0]
            neg_strategies = [strategy_names[i] for i in neg_indices]

            if self.validation_level == ValidationLevel.STRICT:
                messages.append(f"Negative weights not allowed: {neg_strategies}")
                corrective_actions.append("Use absolute values or long-only constraint")
                return ValidationResult(
                    False,
                    self.validation_level,
                    messages,
                    warnings,
                    0.0,
                    corrective_actions,
                )
            else:
                warnings.append(f"Negative weights detected: {neg_strategies}")

        # 3. Sum validation
        weight_sum = np.sum(weights)
        if weight_sum <= 0:
            messages.append(
                f"Portfolio weights sum to {weight_sum:.6f} (must be positive)"
            )
            corrective_actions.append("Use equal weights or check allocation data")
            return ValidationResult(
                False,
                self.validation_level,
                messages,
                warnings,
                0.0,
                corrective_actions,
            )

        # 4. Concentration check
        normalized_weights = weights / weight_sum
        max_weight = np.max(normalized_weights)

        if max_weight > 0.8:
            warnings.append(f"High concentration: max weight {max_weight:.1%}")
            if self.validation_level == ValidationLevel.STRICT and max_weight > 0.95:
                messages.append("Excessive concentration in single strategy")
                corrective_actions.append("Diversify portfolio weights")

        # Calculate quality score
        concentration_score = 1.0 - max(
            0, (max_weight - 0.5) / 0.5
        )  # Penalize concentration > 50%
        sum_score = (
            1.0 if abs(weight_sum - 1.0) < 0.1 else 0.8
        )  # Allow some deviation from 100%
        quality_score = (concentration_score + sum_score) / 2

        is_valid = len(messages) == 0

        if is_valid:
            self.log(
                f"Portfolio weights validation passed (quality: {quality_score:.3f})",
                "info",
            )
        else:
            self.log(
                f"Portfolio weights validation failed: {'; '.join(messages)}", "error"
            )

        if warnings:
            self.log(f"Portfolio weights warnings: {'; '.join(warnings)}", "warning")

        return ValidationResult(
            is_valid=is_valid,
            level=self.validation_level,
            messages=messages,
            warnings=warnings,
            quality_score=quality_score,
            corrective_actions=corrective_actions,
        )

    def validate_risk_calculation_inputs(
        self,
        returns_matrix: np.ndarray,
        weights: np.ndarray,
        strategy_names: List[str],
        cov_matrix: Optional[np.ndarray] = None,
    ) -> ValidationResult:
        """
        Comprehensive validation of all risk calculation inputs.

        Args:
            returns_matrix: Matrix of strategy returns
            weights: Portfolio weights
            strategy_names: Strategy identifiers
            cov_matrix: Optional pre-computed covariance matrix

        Returns:
            ValidationResult with comprehensive validation
        """
        all_messages = []
        all_warnings = []
        all_corrective_actions = []
        quality_scores = []

        # Validate return data
        return_validation = self.validate_return_data(returns_matrix, strategy_names)
        all_messages.extend(return_validation.messages)
        all_warnings.extend(return_validation.warnings)
        all_corrective_actions.extend(return_validation.corrective_actions)
        quality_scores.append(return_validation.quality_score)

        # Validate weights
        weight_validation = self.validate_portfolio_weights(weights, strategy_names)
        all_messages.extend(weight_validation.messages)
        all_warnings.extend(weight_validation.warnings)
        all_corrective_actions.extend(weight_validation.corrective_actions)
        quality_scores.append(weight_validation.quality_score)

        # Validate covariance matrix if provided
        if cov_matrix is not None:
            cov_validation = self.validate_covariance_matrix(cov_matrix, strategy_names)
            all_messages.extend(cov_validation.messages)
            all_warnings.extend(cov_validation.warnings)
            all_corrective_actions.extend(cov_validation.corrective_actions)
            quality_scores.append(cov_validation.quality_score)

        # Overall assessment
        overall_quality = np.mean(quality_scores) if quality_scores else 0.0
        is_valid = len(all_messages) == 0

        # Remove duplicate corrective actions
        unique_actions = list(set(all_corrective_actions))

        if is_valid:
            self.log(
                f"Risk calculation inputs validation passed (overall quality: {overall_quality:.3f})",
                "info",
            )
        else:
            self.log(
                f"Risk calculation inputs validation failed with {len(all_messages)} errors",
                "error",
            )

        return ValidationResult(
            is_valid=is_valid,
            level=self.validation_level,
            messages=all_messages,
            warnings=all_warnings,
            quality_score=overall_quality,
            corrective_actions=unique_actions,
        )


def create_validator(
    log: Callable[[str, str], None], validation_level: str = "strict"
) -> RiskAccuracyValidator:
    """
    Factory function to create a RiskAccuracyValidator with specified validation level.

    Args:
        log: Logging function
        validation_level: Validation strictness ("strict", "moderate", "permissive")

    Returns:
        RiskAccuracyValidator instance

    Raises:
        ValueError: If validation_level is unknown
    """
    level_map = {
        "strict": ValidationLevel.STRICT,
        "moderate": ValidationLevel.MODERATE,
        "permissive": ValidationLevel.PERMISSIVE,
    }

    if validation_level not in level_map:
        raise ValueError(
            f"Unknown validation level: {validation_level}. Must be one of {list(level_map.keys())}"
        )

    return RiskAccuracyValidator(log, level_map[validation_level])
