"""
Significance Testing Engine

Performs statistical significance testing with parametric and non-parametric tests,
including multiple testing corrections for robust statistical validation.
"""

from datetime import datetime
import logging
from typing import Any
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import (
    jarque_bera,
    kruskal,
    levene,
    mannwhitneyu,
    shapiro,
    ttest_ind,
    ttest_rel,
    wilcoxon,
)
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import adfuller

from ..config.statistical_analysis_config import SPDSConfig
from ..models.correlation_models import (
    MultipleTestingCorrection,
    SignificanceLevel,
    SignificanceTestResult,
)


class SignificanceTestingEngine:
    """
    Performs comprehensive statistical significance testing.

    Provides both parametric and non-parametric tests with automatic
    assumption checking and multiple testing corrections.
    """

    def __init__(self, config: SPDSConfig, logger: logging.Logger | None = None):
        """
        Initialize the Significance Testing Engine

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Significance levels
        self.alpha_levels = {
            "highly_significant": 0.01,
            "significant": 0.05,
            "marginally_significant": 0.10,
        }

        # Minimum sample sizes for tests
        self.min_sample_sizes = {
            "ttest": 10,
            "mannwhitney": 5,
            "wilcoxon": 5,
            "normality": 8,
            "correlation": 10,
        }

        self.logger.info("SignificanceTestingEngine initialized")

    async def test_mean_difference(
        self,
        sample1: list[float] | np.ndarray | pd.Series,
        sample2: list[float] | np.ndarray | pd.Series,
        paired: bool = False,
        alpha: float = 0.05,
        alternative: str = "two-sided",
    ) -> SignificanceTestResult:
        """
        Test for significant difference in means between two samples

        Args:
            sample1: First sample
            sample2: Second sample
            paired: Whether samples are paired
            alpha: Significance level
            alternative: Alternative hypothesis ('two-sided', 'less', 'greater')

        Returns:
            Significance test result
        """
        try:
            # Convert to numpy arrays
            x1 = np.array(sample1)
            x2 = np.array(sample2)

            # Remove NaN values
            x1 = x1[~np.isnan(x1)]
            x2 = x2[~np.isnan(x2)]

            # Check minimum sample sizes
            if (
                len(x1) < self.min_sample_sizes["ttest"]
                or len(x2) < self.min_sample_sizes["ttest"]
            ):
                msg = f"Insufficient sample size: {len(x1)}, {len(x2)}"
                raise ValueError(msg)

            # Test assumptions
            assumptions = await self._test_assumptions_for_ttest(x1, x2, paired)

            # Choose appropriate test based on assumptions
            if assumptions["normality"] and assumptions["equal_variance"]:
                # Parametric t-test
                if paired:
                    test_stat, p_value = ttest_rel(x1, x2, alternative=alternative)
                    test_name = "Paired t-test"
                    dof = len(x1) - 1
                else:
                    test_stat, p_value = ttest_ind(
                        x1,
                        x2,
                        equal_var=True,
                        alternative=alternative,
                    )
                    test_name = "Independent t-test"
                    dof = len(x1) + len(x2) - 2

                test_type = "parametric"

            elif assumptions["normality"] and not assumptions["equal_variance"]:
                # Welch's t-test
                test_stat, p_value = ttest_ind(
                    x1,
                    x2,
                    equal_var=False,
                    alternative=alternative,
                )
                test_name = "Welch's t-test"
                test_type = "parametric"
                dof = self._calculate_welch_dof(x1, x2)

            else:
                # Non-parametric test
                if paired:
                    test_stat, p_value = wilcoxon(x1, x2, alternative=alternative)
                    test_name = "Wilcoxon signed-rank test"
                    dof = None
                else:
                    test_stat, p_value = mannwhitneyu(x1, x2, alternative=alternative)
                    test_name = "Mann-Whitney U test"
                    dof = None

                test_type = "non-parametric"

            # Calculate effect size
            effect_size = self._calculate_effect_size(x1, x2, test_type, paired)

            # Determine significance level
            significance_level = self._classify_significance(p_value)

            # Generate warnings for assumption violations
            warnings_list = []
            if not assumptions["normality"]:
                warnings_list.append("Normality assumption violated")
            if not assumptions["equal_variance"] and test_type == "parametric":
                warnings_list.append("Equal variance assumption violated")

            return SignificanceTestResult(
                test_name=test_name,
                test_type=test_type,
                test_statistic=float(test_stat),
                p_value=float(self._validate_p_value(p_value)),
                alpha=alpha,
                degrees_of_freedom=dof,
                is_significant=self._validate_p_value(p_value) < alpha,
                significance_level=significance_level,
                effect_size=effect_size["value"],
                effect_size_interpretation=effect_size["interpretation"],
                assumptions_met=assumptions,
                assumption_warnings=warnings_list,
                sample_size=len(x1) + len(x2),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,  # Would track actual duration in production
            )

        except Exception as e:
            self.logger.exception(f"Mean difference test failed: {e}")
            raise

    async def test_correlation_significance(
        self,
        correlation: float,
        sample_size: int,
        alpha: float = 0.05,
        alternative: str = "two-sided",
    ) -> SignificanceTestResult:
        """
        Test significance of a correlation coefficient

        Args:
            correlation: Correlation coefficient
            sample_size: Sample size used to calculate correlation
            alpha: Significance level
            alternative: Alternative hypothesis

        Returns:
            Significance test result
        """
        try:
            if sample_size < self.min_sample_sizes["correlation"]:
                msg = f"Insufficient sample size: {sample_size}"
                raise ValueError(msg)

            # Calculate t-statistic for correlation
            if abs(correlation) >= 1.0:
                # Perfect correlation - handle edge case gracefully
                self.logger.warning(f"Perfect correlation detected: {correlation}")
                test_stat = float("inf") if correlation > 0 else float("-inf")
                p_value = 1e-10  # Very small but non-zero p-value
            else:
                test_stat = correlation * np.sqrt(
                    (sample_size - 2) / (1 - correlation**2),
                )

                # Calculate p-value
                dof = sample_size - 2
                if alternative == "two-sided":
                    p_value = 2 * (1 - stats.t.cdf(abs(test_stat), dof))
                elif alternative == "greater":
                    p_value = 1 - stats.t.cdf(test_stat, dof)
                else:  # 'less'
                    p_value = stats.t.cdf(test_stat, dof)

            # Calculate confidence interval
            self._correlation_confidence_interval(correlation, sample_size, alpha)

            # Effect size interpretation
            effect_interpretation = self._interpret_correlation_magnitude(
                abs(correlation),
            )

            return SignificanceTestResult(
                test_name="Correlation significance test",
                test_type="parametric",
                test_statistic=float(test_stat),
                p_value=float(self._validate_p_value(p_value)),
                alpha=alpha,
                degrees_of_freedom=sample_size - 2,
                is_significant=self._validate_p_value(p_value) < alpha,
                significance_level=self._classify_significance(
                    self._validate_p_value(p_value),
                ),
                effect_size=abs(correlation),
                effect_size_interpretation=effect_interpretation,
                assumptions_met={"normality": True, "linearity": True},
                assumption_warnings=[],
                sample_size=sample_size,
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.exception(f"Correlation significance test failed: {e}")
            raise

    async def test_multiple_groups(
        self,
        groups: list[list[float] | np.ndarray | pd.Series],
        group_names: list[str] | None = None,
        alpha: float = 0.05,
    ) -> SignificanceTestResult:
        """
        Test for significant differences between multiple groups

        Args:
            groups: List of groups to compare
            group_names: Names for the groups
            alpha: Significance level

        Returns:
            Significance test result
        """
        try:
            if len(groups) < 2:
                msg = "Need at least 2 groups for comparison"
                raise ValueError(msg)

            # Convert to numpy arrays and clean
            clean_groups = []
            for group in groups:
                arr = np.array(group)
                clean_arr = arr[~np.isnan(arr)]
                if len(clean_arr) < 3:
                    msg = f"Group has insufficient data: {len(clean_arr)}"
                    raise ValueError(msg)
                clean_groups.append(clean_arr)

            # Test assumptions for ANOVA
            assumptions = await self._test_assumptions_for_anova(clean_groups)

            if assumptions["normality"] and assumptions["equal_variance"]:
                # One-way ANOVA
                test_stat, p_value = stats.f_oneway(*clean_groups)
                test_name = "One-way ANOVA"
                test_type = "parametric"
                dof = len(clean_groups) - 1
            else:
                # Kruskal-Wallis test
                test_stat, p_value = kruskal(*clean_groups)
                test_name = "Kruskal-Wallis test"
                test_type = "non-parametric"
                dof = len(clean_groups) - 1

            # Calculate effect size (eta-squared for ANOVA)
            effect_size = self._calculate_group_effect_size(clean_groups, test_type)

            # Generate warnings
            warnings_list = []
            if not assumptions["normality"]:
                warnings_list.append(
                    "Normality assumption violated - using Kruskal-Wallis",
                )
            if not assumptions["equal_variance"]:
                warnings_list.append("Equal variance assumption violated")

            total_sample_size = sum(len(group) for group in clean_groups)

            return SignificanceTestResult(
                test_name=test_name,
                test_type=test_type,
                test_statistic=float(test_stat),
                p_value=float(self._validate_p_value(p_value)),
                alpha=alpha,
                degrees_of_freedom=dof,
                is_significant=self._validate_p_value(p_value) < alpha,
                significance_level=self._classify_significance(
                    self._validate_p_value(p_value),
                ),
                effect_size=effect_size["value"],
                effect_size_interpretation=effect_size["interpretation"],
                assumptions_met=assumptions,
                assumption_warnings=warnings_list,
                sample_size=total_sample_size,
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.exception(f"Multiple groups test failed: {e}")
            raise

    async def test_normality(
        self,
        data: list[float] | np.ndarray | pd.Series,
        alpha: float = 0.05,
    ) -> SignificanceTestResult:
        """
        Test for normality of data distribution

        Args:
            data: Data to test
            alpha: Significance level

        Returns:
            Significance test result
        """
        try:
            # Convert and clean data
            x = np.array(data)
            x = x[~np.isnan(x)]

            if len(x) < self.min_sample_sizes["normality"]:
                msg = f"Insufficient sample size: {len(x)}"
                raise ValueError(msg)

            # Choose appropriate normality test based on sample size
            if len(x) < 50:
                # Shapiro-Wilk test for small samples
                test_stat, p_value = shapiro(x)
                test_name = "Shapiro-Wilk test"
            else:
                # Jarque-Bera test for larger samples
                test_stat, p_value = jarque_bera(x)
                test_name = "Jarque-Bera test"

            return SignificanceTestResult(
                test_name=test_name,
                test_type="parametric",
                test_statistic=float(test_stat),
                p_value=float(self._validate_p_value(p_value)),
                alpha=alpha,
                degrees_of_freedom=None,
                is_significant=self._validate_p_value(p_value) < alpha,
                significance_level=self._classify_significance(
                    self._validate_p_value(p_value),
                ),
                effect_size=None,
                effect_size_interpretation=None,
                assumptions_met={
                    "sample_size_adequate": len(x)
                    >= self.min_sample_sizes["normality"],
                },
                assumption_warnings=[],
                sample_size=len(x),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.exception(f"Normality test failed: {e}")
            raise

    async def test_stationarity(
        self,
        time_series: list[float] | np.ndarray | pd.Series,
        alpha: float = 0.05,
    ) -> SignificanceTestResult:
        """
        Test for stationarity of time series data

        Args:
            time_series: Time series data
            alpha: Significance level

        Returns:
            Significance test result
        """
        try:
            # Convert and clean data
            ts = np.array(time_series)
            ts = ts[~np.isnan(ts)]

            if len(ts) < 10:
                msg = f"Insufficient time series length: {len(ts)}"
                raise ValueError(msg)

            # Augmented Dickey-Fuller test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                adf_result = adfuller(ts, autolag="AIC")

            test_stat = adf_result[0]
            p_value = adf_result[1]
            adf_result[4]

            # For ADF test, null hypothesis is non-stationarity
            # So significant result means data IS stationary
            validated_p_value = self._validate_p_value(p_value)
            is_stationary = validated_p_value < alpha

            return SignificanceTestResult(
                test_name="Augmented Dickey-Fuller test",
                test_type="parametric",
                test_statistic=float(test_stat),
                p_value=float(validated_p_value),
                alpha=alpha,
                degrees_of_freedom=None,
                is_significant=is_stationary,
                significance_level=self._classify_significance(validated_p_value),
                effect_size=None,
                effect_size_interpretation=(
                    "Stationary" if is_stationary else "Non-stationary"
                ),
                assumptions_met={"sufficient_length": len(ts) >= 10},
                assumption_warnings=[],
                sample_size=len(ts),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.exception(f"Stationarity test failed: {e}")
            raise

    async def apply_multiple_testing_correction(
        self,
        p_values: list[float],
        method: str = "fdr_bh",
        alpha: float = 0.05,
    ) -> MultipleTestingCorrection:
        """
        Apply multiple testing correction to p-values

        Args:
            p_values: List of p-values to correct
            method: Correction method ('bonferroni', 'fdr_bh', 'fdr_by', etc.)
            alpha: Family-wise error rate

        Returns:
            Multiple testing correction results
        """
        try:
            p_values_array = np.array(p_values)

            # Apply correction
            rejected, corrected_p_values, alpha_sidak, alpha_bonf = multipletests(
                p_values_array,
                alpha=alpha,
                method=method,
            )

            # Calculate corrected alpha based on method
            if method == "bonferroni":
                corrected_alpha = alpha / len(p_values)
            elif method in ["fdr_bh", "fdr_by"]:
                corrected_alpha = alpha  # FDR controls different error rate
            else:
                corrected_alpha = alpha_bonf

            # Calculate false discovery rate
            if np.sum(rejected) > 0:
                fdr = np.sum(corrected_p_values[rejected] > alpha) / np.sum(rejected)
            else:
                fdr = 0.0

            return MultipleTestingCorrection(
                correction_method=method,
                original_alpha=alpha,
                corrected_alpha=corrected_alpha,
                original_p_values=p_values,
                corrected_p_values=corrected_p_values.tolist(),
                rejected_hypotheses=rejected.tolist(),
                total_tests=len(p_values),
                significant_tests=int(np.sum(rejected)),
                false_discovery_rate=float(fdr),
                correction_timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.exception(f"Multiple testing correction failed: {e}")
            raise

    # Helper methods

    async def _test_assumptions_for_ttest(
        self,
        x1: np.ndarray,
        x2: np.ndarray,
        paired: bool,
    ) -> dict[str, bool]:
        """Test assumptions for t-test"""
        assumptions = {}

        # Test normality for both samples
        try:
            if len(x1) >= 8:
                _, p1 = shapiro(x1) if len(x1) < 50 else jarque_bera(x1)
            else:
                p1 = 1.0  # Assume normal for very small samples

            if len(x2) >= 8:
                _, p2 = shapiro(x2) if len(x2) < 50 else jarque_bera(x2)
            else:
                p2 = 1.0

            assumptions["normality"] = p1 > 0.05 and p2 > 0.05
        except:
            assumptions["normality"] = True  # Default to assuming normality

        # Test equal variances (only for independent samples)
        if not paired:
            try:
                _, p_var = levene(x1, x2)
                assumptions["equal_variance"] = p_var > 0.05
            except:
                assumptions["equal_variance"] = True
        else:
            assumptions["equal_variance"] = True  # Not applicable for paired

        return assumptions

    async def _test_assumptions_for_anova(
        self,
        groups: list[np.ndarray],
    ) -> dict[str, bool]:
        """Test assumptions for ANOVA"""
        assumptions = {}

        # Test normality for each group
        normality_results = []
        for group in groups:
            if len(group) >= 8:
                try:
                    _, p = shapiro(group) if len(group) < 50 else jarque_bera(group)
                    normality_results.append(p > 0.05)
                except:
                    normality_results.append(True)
            else:
                normality_results.append(True)

        assumptions["normality"] = all(normality_results)

        # Test equal variances
        try:
            _, p_var = levene(*groups)
            assumptions["equal_variance"] = p_var > 0.05
        except:
            assumptions["equal_variance"] = True

        return assumptions

    def _calculate_welch_dof(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """Calculate degrees of freedom for Welch's t-test"""
        n1, n2 = len(x1), len(x2)
        s1, s2 = np.var(x1, ddof=1), np.var(x2, ddof=1)

        numerator = (s1 / n1 + s2 / n2) ** 2
        denominator = (s1 / n1) ** 2 / (n1 - 1) + (s2 / n2) ** 2 / (n2 - 1)

        return numerator / denominator

    def _calculate_effect_size(
        self,
        x1: np.ndarray,
        x2: np.ndarray,
        test_type: str,
        paired: bool,
    ) -> dict[str, Any]:
        """Calculate appropriate effect size measure"""
        if test_type == "parametric":
            if paired:
                # Cohen's d for paired samples
                diff = x1 - x2
                d = np.mean(diff) / np.std(diff, ddof=1)
            else:
                # Cohen's d for independent samples
                pooled_std = np.sqrt(
                    (
                        (len(x1) - 1) * np.var(x1, ddof=1)
                        + (len(x2) - 1) * np.var(x2, ddof=1)
                    )
                    / (len(x1) + len(x2) - 2),
                )
                d = (np.mean(x1) - np.mean(x2)) / pooled_std

            interpretation = self._interpret_cohens_d(abs(d))
            return {"value": float(d), "interpretation": interpretation}

        # For non-parametric tests, use rank-biserial correlation or similar
        # Simplified implementation
        effect_size = abs(np.mean(x1) - np.mean(x2)) / (np.std(x1) + np.std(x2))
        return {
            "value": float(effect_size),
            "interpretation": "Non-parametric effect size",
        }

    def _calculate_group_effect_size(
        self,
        groups: list[np.ndarray],
        test_type: str,
    ) -> dict[str, Any]:
        """Calculate effect size for multiple groups comparison"""
        if test_type == "parametric":
            # Eta-squared (proportion of variance explained)
            grand_mean = np.mean(np.concatenate(groups))
            ss_between = sum(
                len(group) * (np.mean(group) - grand_mean) ** 2 for group in groups
            )
            ss_total = sum(
                sum((x - grand_mean) ** 2 for x in group) for group in groups
            )

            eta_squared = ss_between / ss_total
            interpretation = self._interpret_eta_squared(eta_squared)

            return {"value": float(eta_squared), "interpretation": interpretation}
        # For non-parametric, use epsilon-squared approximation
        h_statistic, _ = kruskal(*groups)
        n_total = sum(len(group) for group in groups)
        epsilon_squared = (h_statistic - len(groups) + 1) / (n_total - len(groups))

        return {
            "value": float(epsilon_squared),
            "interpretation": "Non-parametric effect size",
        }

    def _correlation_confidence_interval(
        self,
        r: float,
        n: int,
        alpha: float = 0.05,
    ) -> tuple[float, float]:
        """Calculate confidence interval for correlation coefficient"""
        # Fisher z-transformation
        z = 0.5 * np.log((1 + r) / (1 - r))
        se = 1 / np.sqrt(n - 3)

        # Critical value
        z_crit = stats.norm.ppf(1 - alpha / 2)

        # Confidence interval for z
        z_lower = z - z_crit * se
        z_upper = z + z_crit * se

        # Transform back to correlation scale
        r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
        r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)

        return (float(r_lower), float(r_upper))

    def _classify_significance(self, p_value: float) -> SignificanceLevel:
        """Classify significance level based on p-value"""
        if p_value < self.alpha_levels["highly_significant"]:
            return SignificanceLevel.HIGHLY_SIGNIFICANT
        if p_value < self.alpha_levels["significant"]:
            return SignificanceLevel.SIGNIFICANT
        if p_value < self.alpha_levels["marginally_significant"]:
            return SignificanceLevel.MARGINALLY_SIGNIFICANT
        return SignificanceLevel.NOT_SIGNIFICANT

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        if d >= 0.8:
            return "Large effect"
        if d >= 0.5:
            return "Medium effect"
        if d >= 0.2:
            return "Small effect"
        return "Negligible effect"

    def _interpret_eta_squared(self, eta_sq: float) -> str:
        """Interpret eta-squared effect size"""
        if eta_sq >= 0.14:
            return "Large effect"
        if eta_sq >= 0.06:
            return "Medium effect"
        if eta_sq >= 0.01:
            return "Small effect"
        return "Negligible effect"

    def _interpret_correlation_magnitude(self, r: float) -> str:
        """Interpret correlation magnitude"""
        if r >= 0.7:
            return "Strong relationship"
        if r >= 0.5:
            return "Moderate relationship"
        if r >= 0.3:
            return "Weak relationship"
        return "Negligible relationship"

    def _validate_p_value(self, p_value: float) -> float:
        """
        Validate and sanitize p-value to ensure it's within statistical bounds

        Args:
            p_value: Raw p-value to validate

        Returns:
            Validated p-value within bounds [1e-10, 1.0]
        """
        if p_value < 0:
            self.logger.warning(
                f"Negative p-value detected: {p_value}, setting to 1e-10",
            )
            return 1e-10
        if p_value > 1.0:
            self.logger.warning(f"P-value > 1.0 detected: {p_value}, setting to 1.0")
            return 1.0
        if p_value == 0.0:
            self.logger.warning("P-value of exactly 0.0 detected, setting to 1e-10")
            return 1e-10
        if np.isnan(p_value) or np.isinf(p_value):
            self.logger.warning(
                f"Invalid p-value detected: {p_value}, setting to 1e-10",
            )
            return 1e-10
        return p_value
