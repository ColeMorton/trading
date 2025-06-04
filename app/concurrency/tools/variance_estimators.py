"""
Advanced variance estimation methods for portfolio risk calculation.

This module implements sophisticated variance estimation techniques that provide
robust estimates especially for strategies with limited data or time-varying volatility.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar

from app.tools.exceptions import RiskCalculationError


@dataclass
class VarianceEstimate:
    """Container for variance estimation results."""

    value: float
    confidence_interval: Tuple[float, float]
    method: str
    data_quality_score: float
    observations_used: int
    effective_observations: Optional[float] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class VarianceEstimator:
    """
    Advanced variance estimation with data sufficiency validation.

    Implements multiple estimation methods and provides strict validation
    for minimum data requirements.
    """

    def __init__(self, log: Callable[[str, str], None]):
        self.log = log

        # Minimum data requirements per method
        self.min_requirements = {
            "sample": 2,
            "rolling": 10,
            "ewma": 5,
            "bootstrap": 30,
            "bayesian": 20,
        }

        # Default confidence level
        self.confidence_level = 0.95

    def validate_data_sufficiency(
        self, returns: np.ndarray, method: str
    ) -> Tuple[bool, str]:
        """
        Validate minimum data requirements for variance estimation method.

        Args:
            returns: Array of return observations
            method: Estimation method name

        Returns:
            Tuple of (is_sufficient, message)

        Raises:
            RiskCalculationError: If method is unknown
        """
        if method not in self.min_requirements:
            raise RiskCalculationError(f"Unknown variance estimation method: {method}")

        min_obs = self.min_requirements[method]
        actual_obs = len(returns)

        if actual_obs < min_obs:
            return (
                False,
                f"Insufficient data for {method}: {actual_obs} < {min_obs} required",
            )

        # Additional quality checks
        if np.all(returns == 0):
            return False, "All returns are zero - no variance to estimate"

        if np.any(np.isnan(returns)) or np.any(np.isinf(returns)):
            return False, f"Returns contain NaN or infinite values"

        return True, f"Data sufficient for {method}: {actual_obs} >= {min_obs}"

    def calculate_data_quality_score(self, returns: np.ndarray) -> float:
        """
        Calculate data quality score for variance reliability assessment.

        Args:
            returns: Array of return observations

        Returns:
            Quality score between 0 and 1 (higher is better)
        """
        if len(returns) == 0:
            return 0.0

        quality_factors = []

        # Factor 1: Sample size adequacy (0-1)
        sample_size_score = min(
            1.0, len(returns) / 252
        )  # 252 trading days = full score
        quality_factors.append(sample_size_score)

        # Factor 2: Data completeness (no NaN/inf)
        completeness_score = (
            1.0 if not (np.any(np.isnan(returns)) or np.any(np.isinf(returns))) else 0.0
        )
        quality_factors.append(completeness_score)

        # Factor 3: Non-zero variance
        variance_score = 1.0 if np.var(returns) > 1e-10 else 0.0
        quality_factors.append(variance_score)

        # Factor 4: Normality (lower kurtosis is better for variance estimation)
        try:
            kurtosis = stats.kurtosis(returns)
            normality_score = max(
                0.0, 1.0 - abs(kurtosis) / 10.0
            )  # Penalize extreme kurtosis
        except (ValueError, FloatingPointError):
            # Handle cases where kurtosis calculation fails
            normality_score = 0.5
        quality_factors.append(normality_score)

        # Factor 5: Stationarity proxy (consistency of rolling variance)
        if len(returns) >= 20:
            try:
                rolling_vars = []
                window = min(10, len(returns) // 2)
                for i in range(window, len(returns)):
                    rolling_vars.append(np.var(returns[i - window : i]))

                if len(rolling_vars) > 1:
                    var_of_vars = (
                        np.var(rolling_vars) / np.mean(rolling_vars) ** 2
                    )  # Coefficient of variation
                    stationarity_score = max(0.0, 1.0 - var_of_vars)
                else:
                    stationarity_score = 0.5
            except (ValueError, ZeroDivisionError, FloatingPointError):
                # Handle numerical errors in variance calculations
                stationarity_score = 0.5
        else:
            stationarity_score = 0.5

        quality_factors.append(stationarity_score)

        # Weighted average
        weights = [0.3, 0.2, 0.2, 0.15, 0.15]  # Sample size most important
        quality_score = sum(w * f for w, f in zip(weights, quality_factors))

        return max(0.0, min(1.0, quality_score))

    def sample_variance(self, returns: np.ndarray) -> VarianceEstimate:
        """
        Standard sample variance estimation.

        Args:
            returns: Array of return observations

        Returns:
            VarianceEstimate with confidence interval

        Raises:
            RiskCalculationError: If data insufficient
        """
        is_sufficient, message = self.validate_data_sufficiency(returns, "sample")
        if not is_sufficient:
            raise RiskCalculationError(f"Sample variance estimation failed: {message}")

        n = len(returns)
        sample_var = np.var(returns, ddof=1)  # Unbiased estimator
        quality_score = self.calculate_data_quality_score(returns)

        # Confidence interval using chi-squared distribution
        alpha = 1 - self.confidence_level
        chi2_lower = stats.chi2.ppf(alpha / 2, df=n - 1)
        chi2_upper = stats.chi2.ppf(1 - alpha / 2, df=n - 1)

        ci_lower = (n - 1) * sample_var / chi2_upper
        ci_upper = (n - 1) * sample_var / chi2_lower

        self.log(
            f"Sample variance: {sample_var:.8f}, CI: [{ci_lower:.8f}, {ci_upper:.8f}]",
            "info",
        )

        return VarianceEstimate(
            value=sample_var,
            confidence_interval=(ci_lower, ci_upper),
            method="sample",
            data_quality_score=quality_score,
            observations_used=n,
        )

    def rolling_variance(
        self, returns: np.ndarray, window: Optional[int] = None
    ) -> VarianceEstimate:
        """
        Rolling window variance for time-varying volatility.

        Args:
            returns: Array of return observations
            window: Rolling window size (default: adaptive based on data length)

        Returns:
            VarianceEstimate with time-varying variance

        Raises:
            RiskCalculationError: If data insufficient
        """
        is_sufficient, message = self.validate_data_sufficiency(returns, "rolling")
        if not is_sufficient:
            raise RiskCalculationError(f"Rolling variance estimation failed: {message}")

        n = len(returns)

        # Adaptive window size if not specified
        if window is None:
            window = max(10, min(60, n // 4))  # Between 10 and 60, or 1/4 of data

        if window >= n:
            raise RiskCalculationError(
                f"Rolling window ({window}) must be smaller than data length ({n})"
            )

        # Calculate rolling variances
        rolling_vars = []
        for i in range(window, n + 1):
            rolling_vars.append(np.var(returns[i - window : i], ddof=1))

        # Use the mean of rolling variances as the estimate
        rolling_var = np.mean(rolling_vars)
        rolling_std = np.std(rolling_vars)

        quality_score = self.calculate_data_quality_score(returns)

        # Confidence interval based on distribution of rolling variances
        alpha = 1 - self.confidence_level
        ci_lower = max(0, rolling_var - stats.norm.ppf(1 - alpha / 2) * rolling_std)
        ci_upper = rolling_var + stats.norm.ppf(1 - alpha / 2) * rolling_std

        warnings_list = []
        if rolling_std / rolling_var > 0.5:  # High relative volatility of variance
            warnings_list.append("High variance instability detected")

        effective_obs = len(rolling_vars)

        self.log(
            f"Rolling variance (window={window}): {
    rolling_var:.8f}, CI: [{
        ci_lower:.8f}, {
            ci_upper:.8f}]",
            "info",
        )

        return VarianceEstimate(
            value=rolling_var,
            confidence_interval=(ci_lower, ci_upper),
            method="rolling",
            data_quality_score=quality_score,
            observations_used=n,
            effective_observations=effective_obs,
            warnings=warnings_list,
        )

    def ewma_variance(
        self, returns: np.ndarray, lambda_param: Optional[float] = None
    ) -> VarianceEstimate:
        """
        Exponentially Weighted Moving Average variance estimation.

        Args:
            returns: Array of return observations
            lambda_param: Decay parameter (default: optimized via MLE)

        Returns:
            VarianceEstimate with EWMA variance

        Raises:
            RiskCalculationError: If data insufficient
        """
        is_sufficient, message = self.validate_data_sufficiency(returns, "ewma")
        if not is_sufficient:
            raise RiskCalculationError(f"EWMA variance estimation failed: {message}")

        n = len(returns)

        # Optimize lambda if not provided
        if lambda_param is None:
            lambda_param = self._optimize_ewma_lambda(returns)

        # Validate lambda parameter
        if not (0 < lambda_param < 1):
            raise RiskCalculationError(
                f"EWMA lambda parameter must be between 0 and 1, got {lambda_param}"
            )

        # Calculate EWMA variance
        ewma_var = self._calculate_ewma_variance(returns, lambda_param)
        quality_score = self.calculate_data_quality_score(returns)

        # Approximate confidence interval using asymptotic theory
        # This is a simplified approach - more sophisticated methods exist
        effective_obs = 2 / (1 - lambda_param)  # Effective sample size for EWMA

        # Use chi-squared approximation with effective sample size
        alpha = 1 - self.confidence_level
        chi2_lower = stats.chi2.ppf(alpha / 2, df=max(1, effective_obs - 1))
        chi2_upper = stats.chi2.ppf(1 - alpha / 2, df=max(1, effective_obs - 1))

        ci_lower = (effective_obs - 1) * ewma_var / chi2_upper
        ci_upper = (effective_obs - 1) * ewma_var / chi2_lower

        warnings_list = []
        if lambda_param > 0.95:
            warnings_list.append(
                "Very high lambda parameter - estimate may be unstable"
            )
        elif lambda_param < 0.05:
            warnings_list.append(
                "Very low lambda parameter - estimate heavily weighted to recent data"
            )

        self.log(
            f"EWMA variance (λ={
    lambda_param:.4f}): {
        ewma_var:.8f}, CI: [{
            ci_lower:.8f}, {
                ci_upper:.8f}]",
            "info",
        )

        return VarianceEstimate(
            value=ewma_var,
            confidence_interval=(ci_lower, ci_upper),
            method="ewma",
            data_quality_score=quality_score,
            observations_used=n,
            effective_observations=effective_obs,
            warnings=warnings_list,
        )

    def bootstrap_variance(
        self, returns: np.ndarray, n_bootstrap: int = 1000
    ) -> VarianceEstimate:
        """
        Bootstrap variance estimation for small samples.

        Args:
            returns: Array of return observations
            n_bootstrap: Number of bootstrap samples

        Returns:
            VarianceEstimate with bootstrap confidence interval

        Raises:
            RiskCalculationError: If data insufficient
        """
        is_sufficient, message = self.validate_data_sufficiency(returns, "bootstrap")
        if not is_sufficient:
            raise RiskCalculationError(
                f"Bootstrap variance estimation failed: {message}"
            )

        n = len(returns)

        # Generate bootstrap samples
        np.random.seed(42)  # For reproducibility
        bootstrap_vars = []

        for _ in range(n_bootstrap):
            # Resample with replacement
            bootstrap_sample = np.random.choice(returns, size=n, replace=True)
            bootstrap_vars.append(np.var(bootstrap_sample, ddof=1))

        bootstrap_vars = np.array(bootstrap_vars)

        # Bootstrap estimate
        bootstrap_var = np.mean(bootstrap_vars)
        quality_score = self.calculate_data_quality_score(returns)

        # Bootstrap confidence interval
        alpha = 1 - self.confidence_level
        ci_lower = np.percentile(bootstrap_vars, 100 * alpha / 2)
        ci_upper = np.percentile(bootstrap_vars, 100 * (1 - alpha / 2))

        warnings_list = []
        bootstrap_std = np.std(bootstrap_vars)
        if bootstrap_std / bootstrap_var > 0.3:
            warnings_list.append("High bootstrap variance - estimate may be unstable")

        self.log(
            f"Bootstrap variance ({n_bootstrap} samples): {
    bootstrap_var:.8f}, CI: [{
        ci_lower:.8f}, {
            ci_upper:.8f}]",
            "info",
        )

        return VarianceEstimate(
            value=bootstrap_var,
            confidence_interval=(ci_lower, ci_upper),
            method="bootstrap",
            data_quality_score=quality_score,
            observations_used=n,
            warnings=warnings_list,
        )

    def bayesian_variance(
        self,
        returns: np.ndarray,
        prior_variance: Optional[float] = None,
        prior_confidence: Optional[float] = None,
    ) -> VarianceEstimate:
        """
        Bayesian variance estimation with informative priors.

        Args:
            returns: Array of return observations
            prior_variance: Prior belief about variance (default: market average)
            prior_confidence: Confidence in prior (default: based on data length)

        Returns:
            VarianceEstimate with Bayesian posterior

        Raises:
            RiskCalculationError: If data insufficient
        """
        is_sufficient, message = self.validate_data_sufficiency(returns, "bayesian")
        if not is_sufficient:
            raise RiskCalculationError(
                f"Bayesian variance estimation failed: {message}"
            )

        n = len(returns)
        sample_var = np.var(returns, ddof=1)

        # Set default priors if not provided
        if prior_variance is None:
            # Use a reasonable market variance as prior (e.g., 0.0004 ~ 20% annual
            # volatility)
            prior_variance = 0.0004

        if prior_confidence is None:
            # Prior confidence decreases as we have more data
            prior_confidence = max(
                1, 252 // max(1, n)
            )  # Equivalent to prior_confidence days of data

        # Bayesian update using normal-inverse-gamma conjugate prior
        # Simplified approach using precision-weighted average

        # Prior precision (inverse variance)
        prior_precision = prior_confidence / prior_variance

        # Sample precision
        sample_precision = n / sample_var if sample_var > 0 else 0

        # Posterior precision
        posterior_precision = prior_precision + sample_precision

        # Posterior variance (inverse of precision)
        if posterior_precision > 0:
            posterior_var = (
                1
                / posterior_precision
                * (prior_precision * prior_variance + sample_precision * sample_var)
            )
        else:
            posterior_var = prior_variance

        quality_score = self.calculate_data_quality_score(returns)

        # Confidence interval using inverse-gamma distribution
        # Simplified approach - proper Bayesian CI would use MCMC
        alpha = 1 - self.confidence_level

        # Approximate degrees of freedom for posterior
        posterior_df = prior_confidence + n - 1

        if posterior_df > 0:
            chi2_lower = stats.chi2.ppf(alpha / 2, df=posterior_df)
            chi2_upper = stats.chi2.ppf(1 - alpha / 2, df=posterior_df)

            ci_lower = posterior_df * posterior_var / chi2_upper
            ci_upper = posterior_df * posterior_var / chi2_lower
        else:
            # Fallback to wide interval
            ci_lower = posterior_var * 0.5
            ci_upper = posterior_var * 2.0

        warnings_list = []
        shrinkage = prior_precision / posterior_precision
        if shrinkage > 0.5:
            warnings_list.append("High shrinkage toward prior - limited data influence")

        self.log(
            f"Bayesian variance (shrinkage={
    shrinkage:.3f}): {
        posterior_var:.8f}, CI: [{
            ci_lower:.8f}, {
                ci_upper:.8f}]",
            "info",
        )

        return VarianceEstimate(
            value=posterior_var,
            confidence_interval=(ci_lower, ci_upper),
            method="bayesian",
            data_quality_score=quality_score,
            observations_used=n,
            warnings=warnings_list,
        )

    def _optimize_ewma_lambda(self, returns: np.ndarray) -> float:
        """Optimize EWMA lambda parameter via maximum likelihood estimation."""

        def negative_log_likelihood(lambda_param):
            """Negative log-likelihood for EWMA model."""
            try:
                ewma_var = self._calculate_ewma_variance(returns, lambda_param)
                if ewma_var <= 0:
                    return np.inf

                # Simplified likelihood assuming normal returns
                log_likelihood = -0.5 * np.sum(
                    np.log(2 * np.pi * ewma_var) + returns**2 / ewma_var
                )
                return -log_likelihood
            except (ValueError, ZeroDivisionError, FloatingPointError):
                # Handle numerical errors in likelihood calculation
                return np.inf

        # Optimize lambda between 0.01 and 0.99
        result = minimize_scalar(
            negative_log_likelihood, bounds=(0.01, 0.99), method="bounded"
        )

        optimal_lambda = (
            result.x if result.success else 0.94
        )  # Default RiskMetrics value

        self.log(f"Optimized EWMA lambda: {optimal_lambda:.4f}", "info")
        return optimal_lambda

    def _calculate_ewma_variance(
        self, returns: np.ndarray, lambda_param: float
    ) -> float:
        """Calculate EWMA variance given lambda parameter."""
        n = len(returns)

        # Initialize with sample variance
        ewma_var = np.var(returns[: min(10, n)], ddof=1) if n > 1 else 0.0

        # EWMA recursion
        for i in range(n):
            ewma_var = lambda_param * ewma_var + (1 - lambda_param) * returns[i] ** 2

        return ewma_var

    def select_best_estimator(
        self, returns: np.ndarray, methods: Optional[List[str]] = None
    ) -> VarianceEstimate:
        """
        Automatically select the best variance estimator based on data characteristics.

        Args:
            returns: Array of return observations
            methods: List of methods to consider (default: all available)

        Returns:
            VarianceEstimate from the best method

        Raises:
            RiskCalculationError: If no methods are applicable
        """
        if methods is None:
            methods = ["sample", "rolling", "ewma", "bootstrap", "bayesian"]

        n = len(returns)
        quality_score = self.calculate_data_quality_score(returns)

        # Method selection logic based on data characteristics
        applicable_methods = []

        for method in methods:
            is_sufficient, _ = self.validate_data_sufficiency(returns, method)
            if is_sufficient:
                applicable_methods.append(method)

        if not applicable_methods:
            raise RiskCalculationError(
                "No variance estimation methods are applicable to this data"
            )

        # Selection rules based on data size and quality
        selected_method = None

        if n < 30:
            # Small sample - prefer bootstrap or Bayesian
            if "bootstrap" in applicable_methods:
                selected_method = "bootstrap"
            elif "bayesian" in applicable_methods:
                selected_method = "bayesian"
        elif n < 100:
            # Medium sample - prefer EWMA or Bayesian
            if "ewma" in applicable_methods:
                selected_method = "ewma"
            elif "bayesian" in applicable_methods:
                selected_method = "bayesian"
        else:
            # Large sample - consider stability
            if quality_score > 0.7:
                # High quality data - sample variance is fine
                selected_method = "sample"
            else:
                # Lower quality - prefer robust methods
                if "rolling" in applicable_methods:
                    selected_method = "rolling"
                elif "ewma" in applicable_methods:
                    selected_method = "ewma"

        # Fallback to first applicable method
        if selected_method is None:
            selected_method = applicable_methods[0]

        self.log(
            f"Auto-selected variance estimation method: {selected_method} (n={n}, quality={
    quality_score:.3f})",
            "info",
        )

        # Call the selected method
        if selected_method == "sample":
            return self.sample_variance(returns)
        elif selected_method == "rolling":
            return self.rolling_variance(returns)
        elif selected_method == "ewma":
            return self.ewma_variance(returns)
        elif selected_method == "bootstrap":
            return self.bootstrap_variance(returns)
        elif selected_method == "bayesian":
            return self.bayesian_variance(returns)
        else:
            raise RiskCalculationError(f"Unknown method selected: {selected_method}")


def estimate_portfolio_variance(
    strategy_returns_list: List[np.ndarray],
    strategy_names: List[str],
    method: str = "auto",
    log: Callable[[str, str], None] = None,
) -> Dict[str, VarianceEstimate]:
    """
    Estimate variance for multiple strategies using advanced methods.

    Args:
        strategy_returns_list: List of return arrays for each strategy
        strategy_names: List of strategy identifiers
        method: Estimation method ('auto', 'sample', 'rolling', 'ewma', 'bootstrap', 'bayesian')
        log: Logging function

    Returns:
        Dictionary mapping strategy names to VarianceEstimate objects

    Raises:
        RiskCalculationError: If estimation fails
    """
    if log is None:
        log = lambda msg, level: print(f"[{level.upper()}] {msg}")

    if len(strategy_returns_list) != len(strategy_names):
        raise RiskCalculationError(
            "Number of return arrays must match number of strategy names"
        )

    estimator = VarianceEstimator(log)
    variance_estimates = {}

    for returns, name in zip(strategy_returns_list, strategy_names):
        try:
            if method == "auto":
                estimate = estimator.select_best_estimator(returns)
            elif method == "sample":
                estimate = estimator.sample_variance(returns)
            elif method == "rolling":
                estimate = estimator.rolling_variance(returns)
            elif method == "ewma":
                estimate = estimator.ewma_variance(returns)
            elif method == "bootstrap":
                estimate = estimator.bootstrap_variance(returns)
            elif method == "bayesian":
                estimate = estimator.bayesian_variance(returns)
            else:
                raise RiskCalculationError(
                    f"Unknown variance estimation method: {method}"
                )

            variance_estimates[name] = estimate

            log(
                f"Strategy {name} variance estimate: {estimate.value:.8f} "
                + f"(method: {estimate.method}, quality: {estimate.data_quality_score:.3f})",
                "info",
            )

        except Exception as e:
            log(f"Error estimating variance for {name}: {str(e)}", "error")
            raise RiskCalculationError(
                f"Variance estimation failed for {name}: {str(e)}"
            )

    return variance_estimates
