"""
Bootstrap Validator

Performs bootstrap validation for small sample sizes to provide
robust statistical estimates with confidence intervals.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

from ..config.statistical_analysis_config import SPDSConfig
from ..models.statistical_analysis_models import BootstrapResults


class BootstrapValidator:
    """
    Performs bootstrap validation for statistical analysis.

    Provides robust statistical estimates for small samples using
    bootstrap resampling with confidence interval calculation.
    """

    def __init__(self, config: SPDSConfig, logger: logging.Logger | None = None):
        """
        Initialize the Bootstrap Validator

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Bootstrap parameters
        self.n_iterations = config.BOOTSTRAP_ITERATIONS
        self.sample_size = config.BOOTSTRAP_SAMPLE_SIZE
        self.confidence_levels = [0.90, 0.95, 0.99]

        # Random state for reproducibility
        self.random_state = np.random.RandomState(42)

        self.logger.info(
            f"BootstrapValidator initialized with {self.n_iterations} iterations, "
            f"sample_size={self.sample_size}",
        )

    async def validate_sample(
        self,
        data: pd.Series | np.ndarray | list[float],
        statistic: str = "mean",
        confidence_level: float = 0.95,
    ) -> BootstrapResults:
        """
        Perform bootstrap validation on a data sample

        Args:
            data: Sample data for validation
            statistic: Statistic to bootstrap ('mean', 'median', 'std')
            confidence_level: Confidence level for intervals

        Returns:
            Bootstrap validation results with confidence intervals
        """
        try:
            # Convert to numpy array
            data_array = np.array(data)

            # Filter out non-finite values
            data_clean = data_array[np.isfinite(data_array)]

            if len(data_clean) < self.config.MIN_SAMPLE_SIZE:
                msg = f"Insufficient data for bootstrap validation: {len(data_clean)} < {self.config.MIN_SAMPLE_SIZE}"
                raise ValueError(
                    msg,
                )

            self.logger.info(
                f"Starting bootstrap validation with {len(data_clean)} observations, "
                f"statistic={statistic}, confidence_level={confidence_level}",
            )

            # Perform bootstrap resampling
            bootstrap_estimates = self._perform_bootstrap_resampling(
                data_clean,
                statistic,
            )

            # Calculate confidence intervals
            confidence_intervals = self._calculate_confidence_intervals(
                bootstrap_estimates,
                confidence_level,
            )

            # Calculate bootstrap statistics
            mean_estimate = float(np.mean(bootstrap_estimates))
            standard_error = float(np.std(bootstrap_estimates))

            return BootstrapResults(
                mean_estimate=mean_estimate,
                confidence_interval_lower=confidence_intervals["lower"],
                confidence_interval_upper=confidence_intervals["upper"],
                standard_error=standard_error,
                iterations=self.n_iterations,
                confidence_level=confidence_level,
            )

        except Exception as e:
            self.logger.exception(f"Bootstrap validation failed: {e}")
            raise

    async def validate_strategy_performance(
        self,
        returns: pd.Series | np.ndarray | list[float],
        confidence_level: float = 0.95,
    ) -> dict[str, BootstrapResults]:
        """
        Validate multiple statistics for strategy performance

        Args:
            returns: Strategy return data
            confidence_level: Confidence level for intervals

        Returns:
            Dictionary of bootstrap results for different statistics
        """
        try:
            statistics_to_validate = ["mean", "median", "std", "sharpe_ratio"]
            results = {}

            for stat in statistics_to_validate:
                try:
                    result = await self.validate_sample(
                        returns,
                        statistic=stat,
                        confidence_level=confidence_level,
                    )
                    results[stat] = result
                except Exception as e:
                    self.logger.warning(f"Failed to validate {stat}: {e}")
                    continue

            return results

        except Exception as e:
            self.logger.exception(f"Strategy performance validation failed: {e}")
            raise

    async def compare_distributions(
        self,
        sample1: pd.Series | np.ndarray | list[float],
        sample2: pd.Series | np.ndarray | list[float],
        confidence_level: float = 0.95,
    ) -> dict[str, Any]:
        """
        Compare two distributions using bootstrap methods

        Args:
            sample1: First sample
            sample2: Second sample
            confidence_level: Confidence level for comparison

        Returns:
            Bootstrap comparison results
        """
        try:
            # Validate individual samples
            results1 = await self.validate_sample(
                sample1,
                confidence_level=confidence_level,
            )
            results2 = await self.validate_sample(
                sample2,
                confidence_level=confidence_level,
            )

            # Calculate difference in means
            mean_difference = results1.mean_estimate - results2.mean_estimate

            # Bootstrap the difference
            difference_estimates = self._bootstrap_difference(
                np.array(sample1),
                np.array(sample2),
            )

            difference_ci = self._calculate_confidence_intervals(
                difference_estimates,
                confidence_level,
            )

            # Statistical significance test
            is_significant = not (difference_ci["lower"] <= 0 <= difference_ci["upper"])

            return {
                "sample1_results": results1,
                "sample2_results": results2,
                "mean_difference": mean_difference,
                "difference_ci_lower": difference_ci["lower"],
                "difference_ci_upper": difference_ci["upper"],
                "is_statistically_significant": is_significant,
                "confidence_level": confidence_level,
            }

        except Exception as e:
            self.logger.exception(f"Distribution comparison failed: {e}")
            raise

    def _perform_bootstrap_resampling(
        self,
        data: np.ndarray,
        statistic: str,
    ) -> np.ndarray:
        """
        Perform bootstrap resampling for a given statistic

        Args:
            data: Sample data
            statistic: Statistic to calculate

        Returns:
            Array of bootstrap estimates
        """
        bootstrap_estimates = []
        sample_size = min(len(data), self.sample_size)

        for _i in range(self.n_iterations):
            # Resample with replacement
            bootstrap_sample = self.random_state.choice(
                data,
                size=sample_size,
                replace=True,
            )

            # Calculate statistic
            estimate = self._calculate_statistic(bootstrap_sample, statistic)
            bootstrap_estimates.append(estimate)

        return np.array(bootstrap_estimates)

    def _bootstrap_difference(
        self,
        sample1: np.ndarray,
        sample2: np.ndarray,
    ) -> np.ndarray:
        """
        Bootstrap the difference between two sample means

        Args:
            sample1: First sample
            sample2: Second sample

        Returns:
            Array of bootstrapped differences
        """
        differences = []

        sample1_clean = sample1[np.isfinite(sample1)]
        sample2_clean = sample2[np.isfinite(sample2)]

        sample_size1 = min(len(sample1_clean), self.sample_size)
        sample_size2 = min(len(sample2_clean), self.sample_size)

        for _i in range(self.n_iterations):
            # Bootstrap both samples
            bootstrap1 = self.random_state.choice(
                sample1_clean,
                size=sample_size1,
                replace=True,
            )
            bootstrap2 = self.random_state.choice(
                sample2_clean,
                size=sample_size2,
                replace=True,
            )

            # Calculate difference in means
            diff = np.mean(bootstrap1) - np.mean(bootstrap2)
            differences.append(diff)

        return np.array(differences)

    def _calculate_statistic(self, data: np.ndarray, statistic: str) -> float:
        """
        Calculate a specific statistic for the data

        Args:
            data: Sample data
            statistic: Statistic to calculate

        Returns:
            Calculated statistic value
        """
        if statistic == "mean":
            return float(np.mean(data))
        if statistic == "median":
            return float(np.median(data))
        if statistic == "std":
            return float(np.std(data))
        if statistic == "sharpe_ratio":
            mean_return = np.mean(data)
            std_return = np.std(data)
            return float(mean_return / std_return) if std_return > 0 else 0.0
        if statistic == "max":
            return float(np.max(data))
        if statistic == "min":
            return float(np.min(data))
        if statistic == "skewness":
            return float(stats.skew(data)) if len(data) > 2 else 0.0
        if statistic == "kurtosis":
            return float(stats.kurtosis(data)) if len(data) > 3 else 0.0
        msg = f"Unsupported statistic: {statistic}"
        raise ValueError(msg)

    def _calculate_confidence_intervals(
        self,
        bootstrap_estimates: np.ndarray,
        confidence_level: float,
    ) -> dict[str, float]:
        """
        Calculate confidence intervals from bootstrap estimates

        Args:
            bootstrap_estimates: Array of bootstrap estimates
            confidence_level: Confidence level (e.g., 0.95)

        Returns:
            Dictionary with lower and upper confidence bounds
        """
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100

        lower_bound = float(np.percentile(bootstrap_estimates, lower_percentile))
        upper_bound = float(np.percentile(bootstrap_estimates, upper_percentile))

        return {"lower": lower_bound, "upper": upper_bound}

    def assess_sample_adequacy(
        self,
        sample_size: int,
        required_precision: float = 0.1,
    ) -> dict[str, Any]:
        """
        Assess whether sample size is adequate for bootstrap validation

        Args:
            sample_size: Current sample size
            required_precision: Required precision level

        Returns:
            Assessment results
        """
        # Rule of thumb: bootstrap works well with n >= 30
        is_adequate = sample_size >= self.config.PREFERRED_SAMPLE_SIZE

        # Estimate required iterations based on sample size
        if sample_size < self.config.MIN_SAMPLE_SIZE:
            recommended_iterations = 0
            confidence = "insufficient"
        elif sample_size < self.config.PREFERRED_SAMPLE_SIZE:
            recommended_iterations = max(self.n_iterations, 2000)
            confidence = "low"
        else:
            recommended_iterations = self.n_iterations
            confidence = "adequate"

        return {
            "is_adequate": is_adequate,
            "sample_size": sample_size,
            "confidence_assessment": confidence,
            "recommended_iterations": recommended_iterations,
            "current_iterations": self.n_iterations,
            "minimum_sample_size": self.config.MIN_SAMPLE_SIZE,
            "preferred_sample_size": self.config.PREFERRED_SAMPLE_SIZE,
        }

    def get_validation_summary(self, results: BootstrapResults) -> str:
        """
        Generate a human-readable validation summary

        Args:
            results: Bootstrap validation results

        Returns:
            Formatted summary string
        """
        ci_width = results.confidence_interval_upper - results.confidence_interval_lower
        relative_precision = (
            ci_width / abs(results.mean_estimate)
            if results.mean_estimate != 0
            else float("inf")
        )

        precision_assessment = (
            "high"
            if relative_precision < 0.1
            else "medium"
            if relative_precision < 0.2
            else "low"
        )

        return (
            f"Bootstrap validation: estimate={results.mean_estimate:.4f}, "
            f"CI=[{results.confidence_interval_lower:.4f}, {results.confidence_interval_upper:.4f}], "
            f"SE={results.standard_error:.4f}, precision={precision_assessment} "
            f"({results.iterations} iterations)"
        )
