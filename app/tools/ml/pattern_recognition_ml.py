"""Machine learning pattern recognition for statistical analysis.

This module provides ML-based pattern recognition capabilities for identifying
recurring performance patterns and anomalies in trading strategies.
"""

from dataclasses import dataclass
import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

from app.tools.models.statistical_analysis_models import (
    PositionData,
    StatisticalAnalysisResult,
)


logger = logging.getLogger(__name__)


@dataclass
class PatternMatch:
    """Pattern match result with similarity metrics."""

    position_id: str
    similarity_score: float
    pattern_type: str
    historical_outcome: float | None = None
    confidence: float = 0.0
    matched_features: list[str] = None
    recommendation: str = ""
    expected_outcome: str | None = None


@dataclass
class AnomalyDetectionResult:
    """Result of anomaly detection analysis."""

    is_anomaly: bool
    anomaly_score: float
    anomaly_type: str
    confidence: float
    contributing_features: list[str]
    recommendation: str


class PatternRecognitionML:
    """Machine learning-based pattern recognition for trading analysis.

    This class provides advanced pattern recognition capabilities including:
    - Historical pattern matching
    - Anomaly detection
    - Clustering-based pattern identification
    - Feature importance analysis
    """

    def __init__(
        self,
        min_similarity_threshold: float = 0.75,
        anomaly_contamination: float = 0.1,
        n_neighbors: int = 5,
        min_cluster_size: int = 3,
    ):
        """Initialize pattern recognition engine.

        Args:
            min_similarity_threshold: Minimum similarity score for pattern matching
            anomaly_contamination: Expected proportion of anomalies
            n_neighbors: Number of neighbors for KNN analysis
            min_cluster_size: Minimum cluster size for DBSCAN
        """
        self.min_similarity_threshold = min_similarity_threshold
        self.anomaly_contamination = anomaly_contamination
        self.n_neighbors = n_neighbors
        self.min_cluster_size = min_cluster_size

        # Initialize ML models
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% variance
        self.anomaly_detector = IsolationForest(
            contamination=anomaly_contamination, random_state=42,
        )
        self.clusterer = DBSCAN(min_samples=min_cluster_size, eps=0.3)
        self.knn = NearestNeighbors(n_neighbors=n_neighbors)

        # Feature mapping
        self.feature_names = [
            "return",
            "mfe",
            "mae",
            "duration_days",
            "mfe_mae_ratio",
            "exit_efficiency",
            "asset_percentile",
            "strategy_percentile",
            "dual_layer_score",
            "statistical_rarity",
        ]

        # Historical patterns database
        self.pattern_database: list[dict[str, Any]] = []
        self.is_fitted = False

    def fit(self, historical_data: pd.DataFrame) -> None:
        """Fit ML models on historical trading data.

        Args:
            historical_data: DataFrame with historical trade features
        """
        logger.info(
            f"Fitting pattern recognition models on {len(historical_data)} samples",
        )

        # Extract features
        features = self._extract_features(historical_data)

        if len(features) < self.min_cluster_size:
            logger.warning(f"Insufficient data for ML fitting: {len(features)} samples")
            return

        # Fit preprocessing
        scaled_features = self.scaler.fit_transform(features)
        reduced_features = self.pca.fit_transform(scaled_features)

        # Fit ML models
        self.anomaly_detector.fit(reduced_features)
        self.clusterer.fit(reduced_features)
        self.knn.fit(reduced_features)

        # Store pattern database
        self._build_pattern_database(historical_data, reduced_features)

        self.is_fitted = True
        logger.info("Pattern recognition models fitted successfully")

    def find_similar_patterns(
        self,
        position: PositionData,
        analysis: StatisticalAnalysisResult,
        top_k: int = 3,
    ) -> list[PatternMatch]:
        """Find similar historical patterns for a position.

        Args:
            position: Current position data
            analysis: Statistical analysis results
            top_k: Number of top matches to return

        Returns:
            List of pattern matches with similarity scores
        """
        if not self.is_fitted:
            logger.warning("Models not fitted, returning empty pattern matches")
            return []

        # Extract features for current position
        features = self._extract_position_features(position, analysis)
        scaled_features = self.scaler.transform([features])
        reduced_features = self.pca.transform(scaled_features)

        # Find nearest neighbors
        distances, indices = self.knn.kneighbors(reduced_features)

        # Create pattern matches
        matches = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0], strict=False)):
            if i >= top_k:
                break

            similarity_score = 1.0 - min(
                dist / 2.0, 1.0,
            )  # Convert distance to similarity

            if similarity_score >= self.min_similarity_threshold:
                pattern = self.pattern_database[idx]

                match = PatternMatch(
                    position_id=position.position_id,
                    similarity_score=similarity_score,
                    pattern_type=pattern["pattern_type"],
                    historical_outcome=pattern["outcome"],
                    confidence=similarity_score * pattern["confidence"],
                    matched_features=self._get_matched_features(
                        features, pattern["features"],
                    ),
                    recommendation=self._generate_recommendation(
                        pattern, similarity_score,
                    ),
                    expected_outcome=self._predict_outcome(pattern, similarity_score),
                )
                matches.append(match)

        return matches

    def detect_anomalies(
        self, position: PositionData, analysis: StatisticalAnalysisResult,
    ) -> AnomalyDetectionResult:
        """Detect if position represents an anomaly.

        Args:
            position: Current position data
            analysis: Statistical analysis results

        Returns:
            Anomaly detection result
        """
        if not self.is_fitted:
            return AnomalyDetectionResult(
                is_anomaly=False,
                anomaly_score=0.0,
                anomaly_type="unknown",
                confidence=0.0,
                contributing_features=[],
                recommendation="Models not fitted",
            )

        # Extract features
        features = self._extract_position_features(position, analysis)
        scaled_features = self.scaler.transform([features])
        reduced_features = self.pca.transform(scaled_features)

        # Detect anomaly
        anomaly_prediction = self.anomaly_detector.predict(reduced_features)[0]
        anomaly_score = abs(self.anomaly_detector.score_samples(reduced_features)[0])

        is_anomaly = anomaly_prediction == -1

        # Identify contributing features
        contributing_features = (
            self._identify_anomaly_features(features) if is_anomaly else []
        )

        # Determine anomaly type
        anomaly_type = self._classify_anomaly_type(features, contributing_features)

        # Calculate confidence
        confidence = min(anomaly_score * 2, 1.0) if is_anomaly else 1.0 - anomaly_score

        return AnomalyDetectionResult(
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            anomaly_type=anomaly_type,
            confidence=confidence,
            contributing_features=contributing_features,
            recommendation=self._generate_anomaly_recommendation(
                is_anomaly, anomaly_type, contributing_features,
            ),
        )

    def identify_pattern_clusters(self) -> dict[int, list[int]]:
        """Identify pattern clusters in historical data.

        Returns:
            Dictionary mapping cluster IDs to sample indices
        """
        if not self.is_fitted:
            logger.warning("Models not fitted, cannot identify clusters")
            return {}

        clusters = {}
        for idx, label in enumerate(self.clusterer.labels_):
            if label != -1:  # Exclude noise points
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(idx)

        logger.info(f"Identified {len(clusters)} pattern clusters")
        return clusters

    def calculate_pattern_confidence(
        self, pattern_matches: list[PatternMatch],
    ) -> float:
        """Calculate overall confidence from pattern matches.

        Args:
            pattern_matches: List of pattern matches

        Returns:
            Aggregate confidence score
        """
        if not pattern_matches:
            return 0.0

        # Weighted average by similarity score
        total_weight = sum(match.similarity_score for match in pattern_matches)
        if total_weight == 0:
            return 0.0

        return (
            sum(match.confidence * match.similarity_score for match in pattern_matches)
            / total_weight
        )


    def _extract_features(self, data: pd.DataFrame) -> np.ndarray:
        """Extract ML features from historical data."""
        features = []

        for _, row in data.iterrows():
            feature_vector = [
                row.get("return", 0),
                row.get("mfe", 0),
                row.get("mae", 0),
                row.get("duration_days", 0),
                row.get("mfe", 0) / max(row.get("mae", 1), 0.001),  # MFE/MAE ratio
                row.get("exit_efficiency", 0),
                row.get("asset_percentile", 50),
                row.get("strategy_percentile", 50),
                row.get("dual_layer_score", 0),
                row.get("statistical_rarity", 0),
            ]
            features.append(feature_vector)

        return np.array(features)

    def _extract_position_features(
        self, position: PositionData, analysis: StatisticalAnalysisResult,
    ) -> np.ndarray:
        """Extract features from current position."""
        divergence = analysis.divergence_analysis

        feature_vector = [
            position.current_return,
            position.mfe,
            position.mae,
            position.days_held,
            position.mfe / max(position.mae, 0.001),
            position.exit_efficiency or 0,
            divergence.asset_layer.current_percentile if divergence.asset_layer else 50,
            (
                divergence.strategy_layer.current_percentile
                if divergence.strategy_layer
                else 50
            ),
            divergence.dual_layer_convergence_score,
            divergence.statistical_rarity_score,
        ]

        return np.array(feature_vector)

    def _build_pattern_database(
        self, historical_data: pd.DataFrame, reduced_features: np.ndarray,
    ) -> None:
        """Build pattern database from historical data."""
        self.pattern_database = []

        for i, (_, row) in enumerate(historical_data.iterrows()):
            pattern = {
                "features": reduced_features[i],
                "original_features": self._extract_features(historical_data.iloc[[i]])[
                    0
                ],
                "outcome": row.get("return", 0),
                "pattern_type": self._classify_pattern_type(row),
                "confidence": self._calculate_pattern_confidence_score(row),
                "metadata": {
                    "ticker": row.get("ticker", "unknown"),
                    "strategy": row.get("strategy", "unknown"),
                    "date": row.get("date", None),
                },
            }
            self.pattern_database.append(pattern)

    def _classify_pattern_type(self, row: pd.Series) -> str:
        """Classify pattern type based on features."""
        if row.get("return", 0) > 0.20:  # 20%+ return
            return "exceptional_winner"
        if row.get("return", 0) > 0.10:  # 10-20% return
            return "strong_winner"
        if row.get("return", 0) > 0:
            return "moderate_winner"
        if row.get("return", 0) > -0.05:  # -5% to 0%
            return "small_loss"
        return "significant_loss"

    def _calculate_pattern_confidence_score(self, row: pd.Series) -> float:
        """Calculate confidence score for a pattern."""
        # Base confidence on exit efficiency and MFE/MAE ratio
        exit_eff = row.get("exit_efficiency", 0.5)
        mfe_mae_ratio = row.get("mfe", 0) / max(row.get("mae", 1), 0.001)

        # Normalize components
        exit_score = min(exit_eff, 1.0)
        ratio_score = min(mfe_mae_ratio / 5.0, 1.0)  # Normalize by 5

        return (exit_score + ratio_score) / 2.0

    def _get_matched_features(
        self, current_features: np.ndarray, pattern_features: np.ndarray,
    ) -> list[str]:
        """Identify which features matched most closely."""
        if len(current_features) != len(self.feature_names):
            return []

        # Calculate feature-wise differences
        differences = np.abs(
            current_features - pattern_features[: len(current_features)],
        )

        # Find features with smallest differences
        sorted_indices = np.argsort(differences)
        return [self.feature_names[i] for i in sorted_indices[:3]]


    def _generate_recommendation(
        self, pattern: dict[str, Any], similarity_score: float,
    ) -> str:
        """Generate recommendation based on pattern match."""
        pattern_type = pattern["pattern_type"]
        pattern["outcome"]

        if pattern_type == "exceptional_winner" and similarity_score > 0.9:
            return "CAPTURE_GAINS_IMMEDIATELY"
        if (
            pattern_type in ["exceptional_winner", "strong_winner"]
            and similarity_score > 0.8
        ):
            return "MONITOR_FOR_OPTIMAL_EXIT"
        if pattern_type == "significant_loss":
            return "EXIT_ON_ANY_FAVORABLE_MOVEMENT"
        return "APPLY_STANDARD_STATISTICAL_THRESHOLDS"

    def _predict_outcome(self, pattern: dict[str, Any], similarity_score: float) -> str:
        """Predict likely outcome based on pattern."""
        if similarity_score < self.min_similarity_threshold:
            return "Uncertain outcome due to low similarity"

        outcome = pattern["outcome"]
        pattern_type = pattern["pattern_type"]

        if pattern_type == "exceptional_winner":
            return f"Statistical exhaustion likely within 2-3 days (historical: {outcome:.1%})"
        if pattern_type == "strong_winner":
            return f"Continued gains possible but monitor closely (historical: {outcome:.1%})"
        if pattern_type == "significant_loss":
            return f"High risk of further losses (historical: {outcome:.1%})"
        return f"Moderate outcome expected (historical: {outcome:.1%})"

    def _identify_anomaly_features(self, features: np.ndarray) -> list[str]:
        """Identify features contributing to anomaly."""
        # Calculate z-scores for each feature
        z_scores = np.abs((features - np.mean(features)) / (np.std(features) + 1e-8))

        # Find features with high z-scores
        anomaly_indices = np.where(z_scores > 2.0)[0]

        return [
            self.feature_names[i]
            for i in anomaly_indices
            if i < len(self.feature_names)
        ]

    def _classify_anomaly_type(
        self, features: np.ndarray, contributing_features: list[str],
    ) -> str:
        """Classify type of anomaly based on features."""
        if not contributing_features:
            return "normal"

        if "statistical_rarity" in contributing_features:
            return "statistical_outlier"
        if "mfe" in contributing_features or "return" in contributing_features:
            return "performance_outlier"
        if "duration_days" in contributing_features:
            return "duration_outlier"
        return "multi_factor_anomaly"

    def _generate_anomaly_recommendation(
        self, is_anomaly: bool, anomaly_type: str, contributing_features: list[str],
    ) -> str:
        """Generate recommendation for anomaly detection."""
        if not is_anomaly:
            return "Normal pattern - apply standard thresholds"

        if anomaly_type == "statistical_outlier":
            return "IMMEDIATE_EXIT - Statistical exhaustion detected"
        if anomaly_type == "performance_outlier":
            return "CAPTURE_GAINS - Exceptional performance detected"
        if anomaly_type == "duration_outlier":
            return "TIME_BASED_EXIT - Position held beyond normal duration"
        return "HEIGHTENED_MONITORING - Multiple anomaly factors detected"
