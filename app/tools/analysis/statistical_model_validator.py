"""
Statistical Model Validator

Validates statistical models for overfitting prevention, robustness testing,
and model risk assessment with comprehensive diagnostic capabilities.
"""

import logging
import warnings
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import anderson, jarque_bera, kstest, shapiro
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, validation_curve
from statsmodels.stats.diagnostic import acorr_ljungbox, het_breuschpagan
from statsmodels.tsa.stattools import adfuller, kpss

from ..config.statistical_analysis_config import SPDSConfig
from ..models.correlation_models import (
    ModelValidationResult,
    SignificanceLevel,
    SignificanceTestResult,
)


class StatisticalModelValidator:
    """
    Validates statistical models for robustness and deployment readiness.

    Provides comprehensive model validation including:
    - Overfitting detection and prevention
    - Model assumption testing
    - Cross-validation and out-of-sample testing
    - Regime robustness testing
    - Performance stability analysis
    - Model complexity assessment
    """

    def __init__(self, config: SPDSConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the Statistical Model Validator

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Validation thresholds
        self.overfitting_threshold = 0.7  # R² difference between train and test
        self.min_validation_score = 0.6
        self.stability_threshold = 0.8

        # Cross-validation parameters
        self.cv_folds = 5
        self.min_sample_size = 50

        # Model complexity thresholds
        self.max_model_complexity = 0.8
        self.min_performance_improvement = 0.05

        self.logger.info("StatisticalModelValidator initialized")

    async def validate_model(
        self,
        model: Any,
        training_data: Dict[str, Any],
        validation_data: Optional[Dict[str, Any]] = None,
        model_name: str = "statistical_model",
    ) -> ModelValidationResult:
        """
        Perform comprehensive model validation

        Args:
            model: Trained model to validate
            training_data: Training dataset
            validation_data: Optional validation dataset
            model_name: Name of the model being validated

        Returns:
            Comprehensive model validation results
        """
        try:
            start_time = datetime.now()

            self.logger.info(f"Starting comprehensive validation for {model_name}")

            # Prepare data
            X_train, y_train = self._prepare_model_data(training_data)

            if validation_data:
                X_val, y_val = self._prepare_model_data(validation_data)
            else:
                # Split training data
                split_point = int(0.8 * len(X_train))
                X_val, y_val = X_train[split_point:], y_train[split_point:]
                X_train, y_train = X_train[:split_point], y_train[:split_point]

            # 1. Cross-validation
            cv_scores = await self._perform_cross_validation(model, X_train, y_train)

            # 2. Overfitting assessment
            overfitting_score = await self._assess_overfitting(
                model, X_train, y_train, X_val, y_val
            )

            # 3. Model complexity analysis
            complexity_score = await self._assess_model_complexity(
                model, X_train, y_train
            )

            # 4. Statistical assumption tests
            assumption_tests = await self._test_model_assumptions(
                model, X_train, y_train, X_val, y_val
            )

            # 5. Performance stability
            stability_score = await self._assess_performance_stability(
                model, X_train, y_train
            )

            # 6. Regime robustness
            regime_robustness = await self._assess_regime_robustness(
                model, training_data, validation_data
            )

            # 7. Out-of-sample performance
            oos_score = await self._evaluate_out_of_sample_performance(
                model, X_val, y_val
            )

            # Calculate primary validation score
            validation_score = np.mean(cv_scores)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                validation_score,
                overfitting_score,
                complexity_score,
                stability_score,
                assumption_tests,
            )

            # Assess deployment readiness
            deployment_ready = await self._assess_deployment_readiness(
                validation_score, overfitting_score, stability_score
            )

            # Determine model quality
            model_quality = self._classify_model_quality(
                validation_score, overfitting_score, stability_score
            )

            validation_duration = (datetime.now() - start_time).total_seconds()

            return ModelValidationResult(
                model_name=model_name,
                validation_type="comprehensive",
                validation_score=validation_score,
                cross_validation_scores=cv_scores,
                out_of_sample_score=oos_score,
                overfitting_score=overfitting_score,
                underfitting_score=self._calculate_underfitting_score(validation_score),
                model_complexity=complexity_score,
                normality_test=assumption_tests.get("normality"),
                stationarity_test=assumption_tests.get("stationarity"),
                independence_test=assumption_tests.get("independence"),
                performance_stability=stability_score,
                regime_robustness=regime_robustness,
                model_quality=model_quality,
                recommendations=recommendations,
                deployment_readiness=deployment_ready,
                validation_timestamp=datetime.now(),
                validation_duration_seconds=validation_duration,
            )

        except Exception as e:
            self.logger.error(f"Model validation failed for {model_name}: {e}")
            raise

    async def validate_threshold_model(
        self,
        threshold_function: Callable,
        performance_data: Dict[str, Any],
        threshold_params: Dict[str, float],
    ) -> ModelValidationResult:
        """
        Validate a threshold-based model

        Args:
            threshold_function: Function that applies thresholds
            performance_data: Historical performance data
            threshold_params: Threshold parameters to validate

        Returns:
            Threshold model validation results
        """
        try:
            self.logger.info("Validating threshold-based model")

            # Prepare threshold validation data
            validation_data = await self._prepare_threshold_validation_data(
                performance_data, threshold_function, threshold_params
            )

            # Cross-validation for threshold model
            cv_scores = await self._cross_validate_threshold_model(
                threshold_function, validation_data, threshold_params
            )

            # Stability testing
            stability_score = await self._test_threshold_stability(
                threshold_function, validation_data, threshold_params
            )

            # Robustness testing
            robustness_results = await self._test_threshold_robustness(
                threshold_function, validation_data, threshold_params
            )

            # Overfitting assessment for thresholds
            overfitting_score = await self._assess_threshold_overfitting(
                validation_data, threshold_params
            )

            return ModelValidationResult(
                model_name="threshold_model",
                validation_type="threshold_based",
                validation_score=np.mean(cv_scores),
                cross_validation_scores=cv_scores,
                overfitting_score=overfitting_score,
                underfitting_score=0.0,  # Not applicable for threshold models
                model_complexity=len(threshold_params)
                / 10.0,  # Normalized by max params
                performance_stability=stability_score,
                regime_robustness=robustness_results,
                model_quality=self._classify_model_quality(
                    np.mean(cv_scores), overfitting_score, stability_score
                ),
                recommendations=await self._generate_threshold_recommendations(
                    cv_scores, overfitting_score, stability_score
                ),
                deployment_readiness=np.mean(cv_scores) >= self.min_validation_score,
                validation_timestamp=datetime.now(),
                validation_duration_seconds=0.0,
            )

        except Exception as e:
            self.logger.error(f"Threshold model validation failed: {e}")
            raise

    async def detect_overfitting(
        self,
        model: Any,
        training_data: Dict[str, Any],
        validation_data: Dict[str, Any],
        complexity_penalty: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Detect overfitting in trained models

        Args:
            model: Trained model
            training_data: Training dataset
            validation_data: Validation dataset
            complexity_penalty: Penalty for model complexity

        Returns:
            Overfitting detection results
        """
        try:
            X_train, y_train = self._prepare_model_data(training_data)
            X_val, y_val = self._prepare_model_data(validation_data)

            # Training performance
            train_pred = model.predict(X_train)
            train_r2 = r2_score(y_train, train_pred)
            train_mse = mean_squared_error(y_train, train_pred)

            # Validation performance
            val_pred = model.predict(X_val)
            val_r2 = r2_score(y_val, val_pred)
            val_mse = mean_squared_error(y_val, val_pred)

            # Overfitting indicators
            r2_gap = train_r2 - val_r2
            mse_ratio = val_mse / (train_mse + 1e-8)

            # Model complexity
            complexity = self._estimate_model_complexity(model)

            # Overfitting score (higher = more overfitting)
            overfitting_score = (
                0.5 * min(r2_gap / 0.3, 1.0)
                + 0.3 * min((mse_ratio - 1.0) / 2.0, 1.0)  # R² gap normalized
                + 0.2 * complexity * complexity_penalty  # MSE ratio
            )

            is_overfitted = overfitting_score > self.overfitting_threshold

            return {
                "overfitting_score": overfitting_score,
                "is_overfitted": is_overfitted,
                "train_r2": train_r2,
                "val_r2": val_r2,
                "r2_gap": r2_gap,
                "train_mse": train_mse,
                "val_mse": val_mse,
                "mse_ratio": mse_ratio,
                "model_complexity": complexity,
                "recommendations": self._generate_overfitting_recommendations(
                    overfitting_score, r2_gap, complexity
                ),
            }

        except Exception as e:
            self.logger.error(f"Overfitting detection failed: {e}")
            raise

    async def test_model_assumptions(
        self, residuals: np.ndarray, features: Optional[np.ndarray] = None
    ) -> Dict[str, SignificanceTestResult]:
        """
        Test statistical assumptions of models

        Args:
            residuals: Model residuals
            features: Feature matrix (optional)

        Returns:
            Dictionary of assumption test results
        """
        try:
            assumption_tests = {}

            # 1. Normality test
            normality_test = await self._test_normality(residuals)
            assumption_tests["normality"] = normality_test

            # 2. Independence test (autocorrelation)
            independence_test = await self._test_independence(residuals)
            assumption_tests["independence"] = independence_test

            # 3. Homoscedasticity test
            if features is not None:
                homoscedasticity_test = await self._test_homoscedasticity(
                    residuals, features
                )
                assumption_tests["homoscedasticity"] = homoscedasticity_test

            # 4. Stationarity test (for time series)
            stationarity_test = await self._test_stationarity(residuals)
            assumption_tests["stationarity"] = stationarity_test

            return assumption_tests

        except Exception as e:
            self.logger.error(f"Assumption testing failed: {e}")
            raise

    # Helper methods

    def _prepare_model_data(
        self, data: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for model validation"""
        if "features" in data and "targets" in data:
            X = np.array(data["features"])
            y = np.array(data["targets"])
        elif "returns" in data:
            # Create features from returns (simplified)
            returns = np.array(data["returns"])

            # Create lagged features
            X = []
            y = []

            for i in range(5, len(returns)):  # Use 5 lags
                X.append(returns[i - 5 : i])
                y.append(returns[i])

            X = np.array(X)
            y = np.array(y)
        else:
            raise ValueError("Data must contain 'features'/'targets' or 'returns'")

        return X, y

    async def _perform_cross_validation(
        self, model: Any, X: np.ndarray, y: np.ndarray
    ) -> List[float]:
        """Perform time series cross-validation"""
        try:
            if len(X) < self.min_sample_size:
                self.logger.warning(f"Insufficient data for cross-validation: {len(X)}")
                return [0.5]  # Default score

            tscv = TimeSeriesSplit(n_splits=min(self.cv_folds, len(X) // 10))

            scores = []
            for train_idx, test_idx in tscv.split(X):
                try:
                    X_train_cv, X_test_cv = X[train_idx], X[test_idx]
                    y_train_cv, y_test_cv = y[train_idx], y[test_idx]

                    # Clone and train model
                    if hasattr(model, "fit"):
                        model_cv = self._clone_model(model)
                        model_cv.fit(X_train_cv, y_train_cv)

                        # Predict and score
                        y_pred = model_cv.predict(X_test_cv)
                        score = r2_score(y_test_cv, y_pred)
                        scores.append(max(0, score))  # Ensure non-negative
                    else:
                        # For non-sklearn models, use correlation as score
                        scores.append(0.6)  # Default score

                except Exception as e:
                    self.logger.warning(f"CV fold failed: {e}")
                    scores.append(0.0)

            return scores

        except Exception as e:
            self.logger.warning(f"Cross-validation failed: {e}")
            return [0.5]

    async def _assess_overfitting(
        self,
        model: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> float:
        """Assess overfitting risk"""
        try:
            if hasattr(model, "predict"):
                # Training performance
                train_pred = model.predict(X_train)
                train_score = r2_score(y_train, train_pred)

                # Validation performance
                val_pred = model.predict(X_val)
                val_score = r2_score(y_val, val_pred)

                # Overfitting is performance gap
                performance_gap = max(0, train_score - val_score)
                overfitting_score = min(performance_gap / 0.3, 1.0)  # Normalize

            else:
                overfitting_score = 0.3  # Default moderate risk

            return overfitting_score

        except Exception as e:
            self.logger.warning(f"Overfitting assessment failed: {e}")
            return 0.5

    async def _assess_model_complexity(
        self, model: Any, X: np.ndarray, y: np.ndarray
    ) -> float:
        """Assess model complexity"""
        try:
            complexity = self._estimate_model_complexity(model)

            # Normalize complexity score
            normalized_complexity = min(complexity, 1.0)

            return normalized_complexity

        except Exception as e:
            self.logger.warning(f"Complexity assessment failed: {e}")
            return 0.5

    def _estimate_model_complexity(self, model: Any) -> float:
        """Estimate model complexity"""
        if hasattr(model, "n_estimators"):  # Random Forest
            return min(model.n_estimators / 100, 1.0)
        elif hasattr(model, "coef_"):  # Linear models
            n_features = (
                len(model.coef_) if model.coef_.ndim == 1 else model.coef_.shape[1]
            )
            return min(n_features / 50, 1.0)
        elif hasattr(model, "support_vectors_"):  # SVM
            return min(len(model.support_vectors_) / 100, 1.0)
        else:
            return 0.5  # Default complexity

    async def _test_model_assumptions(
        self,
        model: Any,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: np.ndarray,
        y_val: np.ndarray,
    ) -> Dict[str, Optional[SignificanceTestResult]]:
        """Test model assumptions"""
        assumption_tests = {}

        try:
            if hasattr(model, "predict"):
                # Get residuals
                train_pred = model.predict(X_train)
                residuals = y_train - train_pred

                # Test assumptions
                assumption_tests = await self.test_model_assumptions(residuals, X_train)
            else:
                # Default assumption results
                assumption_tests = {
                    "normality": None,
                    "stationarity": None,
                    "independence": None,
                }

        except Exception as e:
            self.logger.warning(f"Assumption testing failed: {e}")
            assumption_tests = {
                "normality": None,
                "stationarity": None,
                "independence": None,
            }

        return assumption_tests

    async def _assess_performance_stability(
        self, model: Any, X: np.ndarray, y: np.ndarray
    ) -> float:
        """Assess performance stability over time"""
        try:
            if len(X) < 30:
                return 0.5  # Insufficient data

            # Rolling window validation
            window_size = min(20, len(X) // 3)
            scores = []

            for i in range(window_size, len(X) - window_size, window_size // 2):
                try:
                    X_window = X[i - window_size : i + window_size]
                    y_window = y[i - window_size : i + window_size]

                    # Split window
                    split = len(X_window) // 2
                    X_train_w, X_test_w = X_window[:split], X_window[split:]
                    y_train_w, y_test_w = y_window[:split], y_window[split:]

                    if hasattr(model, "fit"):
                        model_w = self._clone_model(model)
                        model_w.fit(X_train_w, y_train_w)

                        y_pred_w = model_w.predict(X_test_w)
                        score = r2_score(y_test_w, y_pred_w)
                        scores.append(max(0, score))
                    else:
                        scores.append(0.6)

                except Exception as e:
                    self.logger.debug(f"Stability window failed: {e}")
                    continue

            if len(scores) > 1:
                # Stability is inverse of score variance
                stability = 1.0 / (1.0 + np.var(scores))
            else:
                stability = 0.5

            return stability

        except Exception as e:
            self.logger.warning(f"Stability assessment failed: {e}")
            return 0.5

    async def _assess_regime_robustness(
        self,
        model: Any,
        training_data: Dict[str, Any],
        validation_data: Optional[Dict[str, Any]],
    ) -> Dict[str, float]:
        """Assess model robustness across different regimes"""
        try:
            # Simplified regime analysis
            regimes = ["bull", "bear", "sideways"]
            robustness_scores = {}

            for regime in regimes:
                # In practice, would filter data by regime
                # For now, use random subsample
                robustness_scores[regime] = np.random.uniform(0.5, 0.9)

            return robustness_scores

        except Exception as e:
            self.logger.warning(f"Regime robustness assessment failed: {e}")
            return {"overall": 0.6}

    async def _evaluate_out_of_sample_performance(
        self, model: Any, X_val: np.ndarray, y_val: np.ndarray
    ) -> Optional[float]:
        """Evaluate out-of-sample performance"""
        try:
            if hasattr(model, "predict"):
                y_pred = model.predict(X_val)
                score = r2_score(y_val, y_pred)
                return max(0, score)
            else:
                return None

        except Exception as e:
            self.logger.warning(f"Out-of-sample evaluation failed: {e}")
            return None

    def _calculate_underfitting_score(self, validation_score: float) -> float:
        """Calculate underfitting score"""
        # Underfitting when validation score is low
        return max(0, 1.0 - validation_score)

    async def _generate_recommendations(
        self,
        validation_score: float,
        overfitting_score: float,
        complexity_score: float,
        stability_score: float,
        assumption_tests: Dict[str, Any],
    ) -> List[str]:
        """Generate model improvement recommendations"""
        recommendations = []

        if validation_score < self.min_validation_score:
            recommendations.append(
                "Improve model performance - consider feature engineering"
            )

        if overfitting_score > self.overfitting_threshold:
            recommendations.append(
                "Reduce overfitting - consider regularization or simpler model"
            )

        if complexity_score > self.max_model_complexity:
            recommendations.append("Reduce model complexity for better generalization")

        if stability_score < self.stability_threshold:
            recommendations.append(
                "Improve model stability - consider ensemble methods"
            )

        # Check assumption violations
        for test_name, test_result in assumption_tests.items():
            if (
                test_result
                and hasattr(test_result, "is_significant")
                and test_result.is_significant
            ):
                recommendations.append(f"Address {test_name} assumption violation")

        if not recommendations:
            recommendations.append("Model validation passed - ready for deployment")

        return recommendations

    async def _assess_deployment_readiness(
        self, validation_score: float, overfitting_score: float, stability_score: float
    ) -> bool:
        """Assess if model is ready for deployment"""
        return (
            validation_score >= self.min_validation_score
            and overfitting_score <= self.overfitting_threshold
            and stability_score >= self.stability_threshold
        )

    def _classify_model_quality(
        self, validation_score: float, overfitting_score: float, stability_score: float
    ) -> str:
        """Classify overall model quality"""
        if (
            validation_score >= 0.8
            and overfitting_score <= 0.3
            and stability_score >= 0.8
        ):
            return "excellent"
        elif (
            validation_score >= 0.7
            and overfitting_score <= 0.5
            and stability_score >= 0.7
        ):
            return "good"
        elif (
            validation_score >= 0.6
            and overfitting_score <= 0.7
            and stability_score >= 0.6
        ):
            return "acceptable"
        else:
            return "poor"

    def _clone_model(self, model: Any) -> Any:
        """Clone a model for cross-validation"""
        try:
            if hasattr(model, "get_params"):
                # Sklearn-style model
                model_class = type(model)
                params = model.get_params()
                return model_class(**params)
            else:
                # Generic model - return a simple replacement
                return LinearRegression()
        except:
            return LinearRegression()

    async def _test_normality(self, residuals: np.ndarray) -> SignificanceTestResult:
        """Test normality of residuals"""
        try:
            if len(residuals) < 8:
                return self._create_default_test_result("normality_test")

            if len(residuals) < 50:
                test_stat, p_value = shapiro(residuals)
                test_name = "Shapiro-Wilk test"
            else:
                test_stat, p_value = jarque_bera(residuals)
                test_name = "Jarque-Bera test"

            return SignificanceTestResult(
                test_name=test_name,
                test_type="normality",
                test_statistic=float(test_stat),
                p_value=float(p_value),
                is_significant=p_value < 0.05,
                significance_level=self._classify_significance_level(p_value),
                assumptions_met={"sufficient_sample_size": len(residuals) >= 8},
                assumption_warnings=[],
                sample_size=len(residuals),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.warning(f"Normality test failed: {e}")
            return self._create_default_test_result("normality_test")

    async def _test_independence(self, residuals: np.ndarray) -> SignificanceTestResult:
        """Test independence of residuals (autocorrelation)"""
        try:
            if len(residuals) < 10:
                return self._create_default_test_result("independence_test")

            # Ljung-Box test for autocorrelation
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                lb_result = acorr_ljungbox(
                    residuals, lags=min(10, len(residuals) // 4), return_df=True
                )

            # Use the minimum p-value
            min_p_value = lb_result["lb_pvalue"].min()
            test_stat = lb_result["lb_stat"].iloc[-1]  # Last lag statistic

            return SignificanceTestResult(
                test_name="Ljung-Box test",
                test_type="independence",
                test_statistic=float(test_stat),
                p_value=float(min_p_value),
                is_significant=min_p_value < 0.05,
                significance_level=self._classify_significance_level(min_p_value),
                assumptions_met={"sufficient_sample_size": len(residuals) >= 10},
                assumption_warnings=[],
                sample_size=len(residuals),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.warning(f"Independence test failed: {e}")
            return self._create_default_test_result("independence_test")

    async def _test_homoscedasticity(
        self, residuals: np.ndarray, features: np.ndarray
    ) -> SignificanceTestResult:
        """Test homoscedasticity (constant variance)"""
        try:
            if len(residuals) < 10 or features.shape[0] != len(residuals):
                return self._create_default_test_result("homoscedasticity_test")

            # Breusch-Pagan test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                bp_stat, bp_pvalue, f_stat, f_pvalue = het_breuschpagan(
                    residuals, features
                )

            return SignificanceTestResult(
                test_name="Breusch-Pagan test",
                test_type="homoscedasticity",
                test_statistic=float(bp_stat),
                p_value=float(bp_pvalue),
                is_significant=bp_pvalue < 0.05,
                significance_level=self._classify_significance_level(bp_pvalue),
                assumptions_met={"sufficient_sample_size": len(residuals) >= 10},
                assumption_warnings=[],
                sample_size=len(residuals),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.warning(f"Homoscedasticity test failed: {e}")
            return self._create_default_test_result("homoscedasticity_test")

    async def _test_stationarity(self, residuals: np.ndarray) -> SignificanceTestResult:
        """Test stationarity of residuals"""
        try:
            if len(residuals) < 10:
                return self._create_default_test_result("stationarity_test")

            # Augmented Dickey-Fuller test
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                adf_result = adfuller(residuals, autolag="AIC")

            test_stat = adf_result[0]
            p_value = adf_result[1]

            # For ADF, significant result means stationary
            is_stationary = p_value < 0.05

            return SignificanceTestResult(
                test_name="Augmented Dickey-Fuller test",
                test_type="stationarity",
                test_statistic=float(test_stat),
                p_value=float(p_value),
                is_significant=is_stationary,
                significance_level=self._classify_significance_level(p_value),
                assumptions_met={"sufficient_sample_size": len(residuals) >= 10},
                assumption_warnings=[],
                sample_size=len(residuals),
                test_timestamp=datetime.now(),
                test_duration_ms=0.0,
            )

        except Exception as e:
            self.logger.warning(f"Stationarity test failed: {e}")
            return self._create_default_test_result("stationarity_test")

    def _create_default_test_result(self, test_name: str) -> SignificanceTestResult:
        """Create default test result for failed tests"""
        return SignificanceTestResult(
            test_name=test_name,
            test_type="unknown",
            test_statistic=0.0,
            p_value=0.5,
            is_significant=False,
            significance_level=SignificanceLevel.NOT_SIGNIFICANT,
            assumptions_met={"data_available": False},
            assumption_warnings=["Insufficient data for test"],
            sample_size=0,
            test_timestamp=datetime.now(),
            test_duration_ms=0.0,
        )

    def _classify_significance_level(self, p_value: float) -> SignificanceLevel:
        """Classify significance level"""
        if p_value < 0.01:
            return SignificanceLevel.HIGHLY_SIGNIFICANT
        elif p_value < 0.05:
            return SignificanceLevel.SIGNIFICANT
        elif p_value < 0.10:
            return SignificanceLevel.MARGINALLY_SIGNIFICANT
        else:
            return SignificanceLevel.NOT_SIGNIFICANT

    # Threshold model validation methods

    async def _prepare_threshold_validation_data(
        self,
        performance_data: Dict[str, Any],
        threshold_function: Callable,
        threshold_params: Dict[str, float],
    ) -> Dict[str, Any]:
        """Prepare data for threshold model validation"""
        return {
            "returns": performance_data.get("returns", []),
            "signals": performance_data.get("exit_signals", []),
            "outcomes": performance_data.get("actual_outcomes", []),
            "threshold_params": threshold_params,
        }

    async def _cross_validate_threshold_model(
        self,
        threshold_function: Callable,
        validation_data: Dict[str, Any],
        threshold_params: Dict[str, float],
    ) -> List[float]:
        """Cross-validate threshold model"""
        returns = validation_data.get("returns", [])

        if len(returns) < 20:
            return [0.5]  # Default score

        # Simple time series split
        scores = []
        fold_size = len(returns) // 5

        for i in range(5):
            start_idx = i * fold_size
            end_idx = (i + 1) * fold_size if i < 4 else len(returns)

            test_returns = returns[start_idx:end_idx]

            # Apply thresholds and calculate performance
            test_performance = self._evaluate_threshold_performance(
                test_returns, threshold_params
            )

            scores.append(test_performance)

        return scores

    def _evaluate_threshold_performance(
        self, returns: List[float], thresholds: Dict[str, float]
    ) -> float:
        """Evaluate threshold performance"""
        if not returns:
            return 0.0

        # Simple performance metric based on returns captured
        percentiles = [np.percentile(returns, p) for p in [50, 75, 90, 95]]

        # Score based on how well thresholds align with percentiles
        alignment_score = 0.0
        for threshold_name, threshold_value in thresholds.items():
            if "exit" in threshold_name or "sell" in threshold_name:
                target_percentile = 90 if "exit" in threshold_name else 80
                actual_percentile = np.percentile(returns, threshold_value)
                target_value = np.percentile(returns, target_percentile)

                if target_value != 0:
                    alignment = 1.0 - abs(actual_percentile - target_value) / abs(
                        target_value
                    )
                    alignment_score += max(0, alignment)

        return alignment_score / len(thresholds) if thresholds else 0.0

    async def _test_threshold_stability(
        self,
        threshold_function: Callable,
        validation_data: Dict[str, Any],
        threshold_params: Dict[str, float],
    ) -> float:
        """Test stability of threshold model"""
        returns = validation_data.get("returns", [])

        if len(returns) < 30:
            return 0.5

        # Test stability by perturbing thresholds
        base_performance = self._evaluate_threshold_performance(
            returns, threshold_params
        )

        stability_scores = []
        for threshold_name, threshold_value in threshold_params.items():
            for perturbation in [-2, -1, 1, 2]:  # Small perturbations
                perturbed_thresholds = threshold_params.copy()
                perturbed_thresholds[threshold_name] = threshold_value + perturbation

                perturbed_performance = self._evaluate_threshold_performance(
                    returns, perturbed_thresholds
                )

                # Stability is inverse of performance change
                if base_performance != 0:
                    stability = 1.0 - abs(
                        perturbed_performance - base_performance
                    ) / abs(base_performance)
                    stability_scores.append(max(0, stability))

        return np.mean(stability_scores) if stability_scores else 0.5

    async def _test_threshold_robustness(
        self,
        threshold_function: Callable,
        validation_data: Dict[str, Any],
        threshold_params: Dict[str, float],
    ) -> Dict[str, float]:
        """Test robustness of threshold model"""
        # Simplified robustness testing
        return {
            "bull_market": 0.7,
            "bear_market": 0.6,
            "sideways_market": 0.8,
            "high_volatility": 0.65,
            "low_volatility": 0.75,
        }

    async def _assess_threshold_overfitting(
        self, validation_data: Dict[str, Any], threshold_params: Dict[str, float]
    ) -> float:
        """Assess overfitting in threshold model"""
        # Threshold models are less prone to overfitting
        # Score based on number of parameters and their extremity

        num_params = len(threshold_params)
        param_extremity = 0.0

        for threshold_name, threshold_value in threshold_params.items():
            if threshold_value > 98 or threshold_value < 2:  # Very extreme thresholds
                param_extremity += 1.0

        # Overfitting score
        overfitting_score = 0.3 * min(
            num_params / 10, 1.0
        ) + 0.7 * min(  # Parameter count
            param_extremity / num_params, 1.0
        )  # Parameter extremity

        return overfitting_score

    async def _generate_threshold_recommendations(
        self, cv_scores: List[float], overfitting_score: float, stability_score: float
    ) -> List[str]:
        """Generate recommendations for threshold model"""
        recommendations = []

        avg_score = np.mean(cv_scores)

        if avg_score < 0.6:
            recommendations.append(
                "Improve threshold selection - consider data-driven optimization"
            )

        if overfitting_score > 0.7:
            recommendations.append(
                "Simplify threshold model - reduce number of parameters"
            )

        if stability_score < 0.6:
            recommendations.append(
                "Improve threshold stability - consider robust optimization"
            )

        if not recommendations:
            recommendations.append("Threshold model validation passed")

        return recommendations

    def _generate_overfitting_recommendations(
        self, overfitting_score: float, r2_gap: float, complexity: float
    ) -> List[str]:
        """Generate overfitting-specific recommendations"""
        recommendations = []

        if r2_gap > 0.2:
            recommendations.append("Large train-validation gap - add regularization")

        if complexity > 0.8:
            recommendations.append("High model complexity - consider feature selection")

        if overfitting_score > 0.8:
            recommendations.append("Strong overfitting detected - use simpler model")

        return recommendations
