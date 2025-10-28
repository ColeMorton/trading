"""
Divergence Detection Service

Focused service for detecting performance divergences between different data sources.
Extracted from the larger analysis service for better maintainability.
"""

import logging

import numpy as np
import pandas as pd
import polars as pl

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config
from app.tools.models.statistical_analysis_models import (
    DivergenceMetrics,
    DualLayerConvergence,
    DualSourceConvergence,
)


class DivergenceDetector:
    """
    Service for detecting statistical divergences between data sources.

    This service handles:
    - Dual-layer convergence analysis
    - Dual-source convergence detection
    - Divergence metric calculation
    - Confidence level assessment
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the divergence detector."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def detect_dual_layer_convergence(
        self,
        layer1_data: Union[pd.DataFrame, pl.DataFrame],
        layer2_data: Union[pd.DataFrame, pl.DataFrame],
        convergence_threshold: float = 0.05,
    ) -> DualLayerConvergence:
        """Detect convergence between two analysis layers."""
        if isinstance(layer1_data, pl.DataFrame):
            layer1_data = layer1_data.to_pandas()
        if isinstance(layer2_data, pl.DataFrame):
            layer2_data = layer2_data.to_pandas()

        # Calculate convergence metrics
        convergence_score = self._calculate_convergence_score(layer1_data, layer2_data)
        is_converged = convergence_score < convergence_threshold

        return DualLayerConvergence(
            layer1_metrics=self._extract_layer_metrics(layer1_data),
            layer2_metrics=self._extract_layer_metrics(layer2_data),
            convergence_score=convergence_score,
            is_converged=is_converged,
            divergence_areas=self._identify_divergence_areas(layer1_data, layer2_data),
        )

    def detect_dual_source_convergence(
        self,
        source1_data: Union[pd.DataFrame, pl.DataFrame],
        source2_data: Union[pd.DataFrame, pl.DataFrame],
        convergence_threshold: float = 0.05,
    ) -> DualSourceConvergence:
        """Detect convergence between two data sources."""
        if isinstance(source1_data, pl.DataFrame):
            source1_data = source1_data.to_pandas()
        if isinstance(source2_data, pl.DataFrame):
            source2_data = source2_data.to_pandas()

        # Calculate convergence metrics
        convergence_score = self._calculate_convergence_score(
            source1_data, source2_data,
        )
        is_converged = convergence_score < convergence_threshold

        return DualSourceConvergence(
            source1_metrics=self._extract_source_metrics(source1_data),
            source2_metrics=self._extract_source_metrics(source2_data),
            convergence_score=convergence_score,
            is_converged=is_converged,
            divergence_magnitude=self._calculate_divergence_magnitude(
                source1_data, source2_data,
            ),
        )

    def calculate_divergence_metrics(
        self,
        reference_data: Union[pd.DataFrame, pl.DataFrame],
        comparison_data: Union[pd.DataFrame, pl.DataFrame],
    ) -> DivergenceMetrics:
        """Calculate comprehensive divergence metrics."""
        if isinstance(reference_data, pl.DataFrame):
            reference_data = reference_data.to_pandas()
        if isinstance(comparison_data, pl.DataFrame):
            comparison_data = comparison_data.to_pandas()

        # Calculate various divergence measures
        statistical_divergence = self._calculate_statistical_divergence(
            reference_data, comparison_data,
        )
        trend_divergence = self._calculate_trend_divergence(
            reference_data, comparison_data,
        )
        volatility_divergence = self._calculate_volatility_divergence(
            reference_data, comparison_data,
        )

        return DivergenceMetrics(
            statistical_divergence=statistical_divergence,
            trend_divergence=trend_divergence,
            volatility_divergence=volatility_divergence,
            overall_divergence=np.mean(
                [statistical_divergence, trend_divergence, volatility_divergence],
            ),
        )

    def _calculate_convergence_score(
        self, data1: pd.DataFrame, data2: pd.DataFrame,
    ) -> float:
        """Calculate convergence score between two datasets."""
        if data1.empty or data2.empty:
            return 1.0  # Maximum divergence

        # Use first numeric column for comparison
        numeric_cols1 = data1.select_dtypes(include=[np.number]).columns
        numeric_cols2 = data2.select_dtypes(include=[np.number]).columns

        if len(numeric_cols1) == 0 or len(numeric_cols2) == 0:
            return 1.0

        series1 = data1[numeric_cols1[0]]
        series2 = data2[numeric_cols2[0]]

        # Calculate correlation-based convergence
        try:
            correlation = series1.corr(series2)
            return abs(1.0 - abs(correlation)) if not np.isnan(correlation) else 1.0
        except:
            return 1.0

    def _extract_layer_metrics(self, data: pd.DataFrame) -> dict[str, float]:
        """Extract metrics from a layer."""
        if data.empty:
            return {}

        numeric_cols = data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) == 0:
            return {}

        series = data[numeric_cols[0]]
        return {
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "max": float(series.max()),
        }

    def _extract_source_metrics(self, data: pd.DataFrame) -> dict[str, float]:
        """Extract metrics from a source."""
        return self._extract_layer_metrics(data)

    def _identify_divergence_areas(
        self, data1: pd.DataFrame, data2: pd.DataFrame,
    ) -> list[str]:
        """Identify areas of divergence between datasets."""
        divergence_areas = []

        metrics1 = self._extract_layer_metrics(data1)
        metrics2 = self._extract_layer_metrics(data2)

        for key in metrics1:
            if key in metrics2:
                diff = abs(metrics1[key] - metrics2[key])
                if diff > 0.1:  # Threshold for significant divergence
                    divergence_areas.append(key)

        return divergence_areas

    def _calculate_divergence_magnitude(
        self, data1: pd.DataFrame, data2: pd.DataFrame,
    ) -> float:
        """Calculate the magnitude of divergence."""
        metrics1 = self._extract_source_metrics(data1)
        metrics2 = self._extract_source_metrics(data2)

        if not metrics1 or not metrics2:
            return 1.0

        total_diff = 0.0
        count = 0

        for key in metrics1:
            if key in metrics2:
                # Normalize by the average to get relative difference
                avg = (metrics1[key] + metrics2[key]) / 2
                if avg != 0:
                    total_diff += abs(metrics1[key] - metrics2[key]) / abs(avg)
                    count += 1

        return total_diff / count if count > 0 else 1.0

    def _calculate_statistical_divergence(
        self, ref_data: pd.DataFrame, comp_data: pd.DataFrame,
    ) -> float:
        """Calculate statistical divergence between datasets."""
        ref_metrics = self._extract_layer_metrics(ref_data)
        comp_metrics = self._extract_layer_metrics(comp_data)

        if not ref_metrics or not comp_metrics:
            return 1.0

        # Calculate normalized difference in means
        if "mean" in ref_metrics and "mean" in comp_metrics:
            ref_mean = ref_metrics["mean"]
            comp_mean = comp_metrics["mean"]
            if ref_mean != 0:
                return abs(comp_mean - ref_mean) / abs(ref_mean)

        return 1.0

    def _calculate_trend_divergence(
        self, ref_data: pd.DataFrame, comp_data: pd.DataFrame,
    ) -> float:
        """Calculate trend divergence between datasets."""
        # Simple trend calculation using linear regression slope
        if ref_data.empty or comp_data.empty:
            return 1.0

        # This is a simplified trend calculation
        # In practice, you might want to use more sophisticated trend analysis
        return 0.5  # Placeholder

    def _calculate_volatility_divergence(
        self, ref_data: pd.DataFrame, comp_data: pd.DataFrame,
    ) -> float:
        """Calculate volatility divergence between datasets."""
        ref_metrics = self._extract_layer_metrics(ref_data)
        comp_metrics = self._extract_layer_metrics(comp_data)

        if not ref_metrics or not comp_metrics:
            return 1.0

        # Calculate normalized difference in standard deviations
        if "std" in ref_metrics and "std" in comp_metrics:
            ref_std = ref_metrics["std"]
            comp_std = comp_metrics["std"]
            if ref_std != 0:
                return abs(comp_std - ref_std) / abs(ref_std)

        return 1.0
