"""
Statistical Analyzer Service

Focused service for core statistical analysis operations.
Extracted from the larger statistical analysis service for better maintainability.
"""

import logging

import numpy as np
import pandas as pd
import polars as pl

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config
from app.tools.models.statistical_analysis_models import (
    PercentileMetrics,
    StatisticalMetrics,
    VaRMetrics,
)


class StatisticalAnalyzer:
    """
    Core statistical analyzer for basic statistical operations.

    This service handles:
    - Basic statistical calculations
    - VaR and percentile analysis
    - Statistical metric computation
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the statistical analyzer."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def calculate_basic_statistics(
        self, data: pd.DataFrame | pl.DataFrame,
    ) -> dict[str, float]:
        """Calculate basic statistical metrics."""
        if isinstance(data, pl.DataFrame):
            data = data.to_pandas()

        return {
            "mean": float(data.mean().iloc[0]) if not data.empty else 0.0,
            "std": float(data.std().iloc[0]) if not data.empty else 0.0,
            "min": float(data.min().iloc[0]) if not data.empty else 0.0,
            "max": float(data.max().iloc[0]) if not data.empty else 0.0,
            "median": float(data.median().iloc[0]) if not data.empty else 0.0,
            "skew": float(data.skew().iloc[0]) if not data.empty else 0.0,
            "kurtosis": float(data.kurtosis().iloc[0]) if not data.empty else 0.0,
        }

    def calculate_var_metrics(self, returns: pd.Series | pl.Series) -> VaRMetrics:
        """Calculate Value at Risk metrics."""
        if isinstance(returns, pl.Series):
            returns = returns.to_pandas()

        if returns.empty:
            return VaRMetrics(var_95=0.0, var_99=0.0, cvar_95=0.0, cvar_99=0.0)

        var_95 = float(np.percentile(returns, 5))
        var_99 = float(np.percentile(returns, 1))

        # Calculate Conditional VaR (Expected Shortfall)
        cvar_95 = (
            float(returns[returns <= var_95].mean())
            if (returns <= var_95).any()
            else var_95
        )
        cvar_99 = (
            float(returns[returns <= var_99].mean())
            if (returns <= var_99).any()
            else var_99
        )

        return VaRMetrics(
            var_95=var_95, var_99=var_99, cvar_95=cvar_95, cvar_99=cvar_99,
        )

    def calculate_percentile_metrics(
        self, data: pd.Series | pl.Series,
    ) -> PercentileMetrics:
        """Calculate percentile-based metrics."""
        if isinstance(data, pl.Series):
            data = data.to_pandas()

        if data.empty:
            return PercentileMetrics(
                p25=0.0, p50=0.0, p75=0.0, p90=0.0, p95=0.0, p99=0.0,
            )

        return PercentileMetrics(
            p25=float(np.percentile(data, 25)),
            p50=float(np.percentile(data, 50)),
            p75=float(np.percentile(data, 75)),
            p90=float(np.percentile(data, 90)),
            p95=float(np.percentile(data, 95)),
            p99=float(np.percentile(data, 99)),
        )

    def calculate_statistical_metrics(
        self, data: pd.DataFrame | pl.DataFrame,
    ) -> StatisticalMetrics:
        """Calculate comprehensive statistical metrics."""
        if isinstance(data, pl.DataFrame):
            data = data.to_pandas()

        if data.empty:
            return StatisticalMetrics(
                mean=0.0,
                std=0.0,
                skew=0.0,
                kurtosis=0.0,
                var_metrics=VaRMetrics(
                    var_95=0.0, var_99=0.0, cvar_95=0.0, cvar_99=0.0,
                ),
                percentile_metrics=PercentileMetrics(
                    p25=0.0, p50=0.0, p75=0.0, p90=0.0, p95=0.0, p99=0.0,
                ),
            )

        # Assume first numeric column for analysis
        numeric_columns = data.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) == 0:
            msg = "No numeric columns found in data"
            raise ValueError(msg)

        series = data[numeric_columns[0]]

        return StatisticalMetrics(
            mean=float(series.mean()),
            std=float(series.std()),
            skew=float(series.skew()),
            kurtosis=float(series.kurtosis()),
            var_metrics=self.calculate_var_metrics(series),
            percentile_metrics=self.calculate_percentile_metrics(series),
        )
