"""
Signal Aggregator Service

Focused service for aggregating and processing signal data from multiple sources.
Extracted from the larger signal_data_aggregator for better maintainability.
"""

from dataclasses import dataclass
import logging
from typing import Any

import pandas as pd
import polars as pl

from app.tools.config.statistical_analysis_config import SPDSConfig, get_spds_config


@dataclass
class SignalMetrics:
    """Signal quality and performance metrics."""

    signal_strength: float
    confidence_level: float
    signal_to_noise_ratio: float
    consistency_score: float
    reliability_index: float


@dataclass
class AggregatedSignal:
    """Aggregated signal data from multiple sources."""

    strategy_name: str
    ticker: str
    signal_type: str
    timestamp: str
    signal_value: float
    confidence: float
    sources: list[str]
    metrics: SignalMetrics
    raw_data: dict[str, Any]


class SignalAggregator:
    """
    Service for aggregating signals from multiple data sources.

    This service handles:
    - Multi-source signal aggregation
    - Signal quality assessment
    - Signal consistency validation
    - Signal strength calculation
    """

    def __init__(
        self,
        config: SPDSConfig | None = None,
        logger: logging.Logger | None = None,
    ):
        """Initialize the signal aggregator."""
        self.config = config or get_spds_config()
        self.logger = logger or logging.getLogger(__name__)

    def aggregate_signals(
        self,
        sources: dict[str, pd.DataFrame | pl.DataFrame],
        strategy_identifier: str,
    ) -> list[AggregatedSignal]:
        """Aggregate signals from multiple sources."""
        if not sources:
            self.logger.warning("No signal sources provided")
            return []

        try:
            # Convert all sources to consistent format
            normalized_sources = self._normalize_sources(sources)

            # Extract signals from each source
            extracted_signals = {}
            for source_name, data in normalized_sources.items():
                signals = self._extract_signals_from_source(data, source_name)
                extracted_signals[source_name] = signals

            # Aggregate signals across sources
            return self._aggregate_across_sources(
                extracted_signals,
                strategy_identifier,
            )

        except Exception as e:
            self.logger.exception(f"Signal aggregation failed: {e!s}")
            return []

    def calculate_signal_quality(
        self,
        signal_data: pd.DataFrame | pl.DataFrame,
        baseline_data: pd.DataFrame | pl.DataFrame | None = None,
    ) -> SignalMetrics:
        """Calculate signal quality metrics."""
        if isinstance(signal_data, pl.DataFrame):
            signal_data = signal_data.to_pandas()

        if signal_data.empty:
            return SignalMetrics(
                signal_strength=0.0,
                confidence_level=0.0,
                signal_to_noise_ratio=0.0,
                consistency_score=0.0,
                reliability_index=0.0,
            )

        # Calculate signal strength
        signal_strength = self._calculate_signal_strength(signal_data)

        # Calculate confidence level
        confidence_level = self._calculate_confidence_level(signal_data)

        # Calculate signal-to-noise ratio
        snr = self._calculate_signal_to_noise_ratio(signal_data, baseline_data)

        # Calculate consistency score
        consistency_score = self._calculate_consistency_score(signal_data)

        # Calculate reliability index
        reliability_index = self._calculate_reliability_index(signal_data)

        return SignalMetrics(
            signal_strength=signal_strength,
            confidence_level=confidence_level,
            signal_to_noise_ratio=snr,
            consistency_score=consistency_score,
            reliability_index=reliability_index,
        )

    def validate_signal_consistency(
        self,
        signals: list[AggregatedSignal],
        consistency_threshold: float = 0.8,
    ) -> dict[str, Any]:
        """Validate consistency across aggregated signals."""
        if not signals:
            return {
                "is_consistent": True,
                "consistency_score": 1.0,
                "inconsistent_signals": [],
                "validation_summary": "No signals to validate",
            }

        # Calculate consistency metrics
        consistency_scores = []
        inconsistent_signals = []

        for signal in signals:
            if signal.metrics.consistency_score < consistency_threshold:
                inconsistent_signals.append(signal.strategy_name)
            consistency_scores.append(signal.metrics.consistency_score)

        overall_consistency = sum(consistency_scores) / len(consistency_scores)
        is_consistent = overall_consistency >= consistency_threshold

        return {
            "is_consistent": is_consistent,
            "consistency_score": overall_consistency,
            "inconsistent_signals": inconsistent_signals,
            "validation_summary": f"Validated {len(signals)} signals with {overall_consistency:.2f} consistency",
        }

    def _normalize_sources(
        self,
        sources: dict[str, pd.DataFrame | pl.DataFrame],
    ) -> dict[str, pd.DataFrame]:
        """Normalize all sources to pandas DataFrames."""
        normalized = {}

        for source_name, data in sources.items():
            if isinstance(data, pl.DataFrame):
                normalized[source_name] = data.to_pandas()
            else:
                normalized[source_name] = data

        return normalized

    def _extract_signals_from_source(
        self,
        data: pd.DataFrame,
        source_name: str,
    ) -> list[dict[str, Any]]:
        """Extract signals from a single source."""
        signals = []

        if data.empty:
            return signals

        # Look for common signal columns
        signal_columns = ["signal", "exit_signal", "entry_signal", "trade_signal"]
        signal_col = None

        for col in signal_columns:
            if col in data.columns:
                signal_col = col
                break

        if signal_col is None:
            # Try to infer signals from other columns
            if "position" in data.columns:
                signal_col = "position"
            elif "action" in data.columns:
                signal_col = "action"

        if signal_col:
            for idx, row in data.iterrows():
                signal = {
                    "source": source_name,
                    "signal_type": row.get(signal_col, "UNKNOWN"),
                    "timestamp": row.get("timestamp", row.get("date", str(idx))),
                    "confidence": row.get(
                        "confidence",
                        row.get("signal_confidence", 0.5),
                    ),
                    "raw_data": row.to_dict(),
                }
                signals.append(signal)

        return signals

    def _aggregate_across_sources(
        self,
        extracted_signals: dict[str, list[dict[str, Any]]],
        strategy_identifier: str,
    ) -> list[AggregatedSignal]:
        """Aggregate signals across multiple sources."""
        aggregated = []

        # Group signals by timestamp/strategy
        signal_groups = {}

        for signals in extracted_signals.values():
            for signal in signals:
                timestamp = signal["timestamp"]
                if timestamp not in signal_groups:
                    signal_groups[timestamp] = []
                signal_groups[timestamp].append(signal)

        # Create aggregated signals
        for timestamp, signals in signal_groups.items():
            if not signals:
                continue

            # Calculate aggregated metrics
            avg_confidence = sum(s["confidence"] for s in signals) / len(signals)
            sources = [s["source"] for s in signals]

            # Determine dominant signal type
            signal_types = [s["signal_type"] for s in signals]
            dominant_signal = max(set(signal_types), key=signal_types.count)

            # Calculate signal metrics
            signal_data = pd.DataFrame([s["raw_data"] for s in signals])
            metrics = self.calculate_signal_quality(signal_data)

            aggregated_signal = AggregatedSignal(
                strategy_name=strategy_identifier,
                ticker=signals[0]["raw_data"].get("ticker", "UNKNOWN"),
                signal_type=dominant_signal,
                timestamp=timestamp,
                signal_value=avg_confidence,
                confidence=avg_confidence,
                sources=sources,
                metrics=metrics,
                raw_data={"signals": signals},
            )

            aggregated.append(aggregated_signal)

        return aggregated

    def _calculate_signal_strength(self, data: pd.DataFrame) -> float:
        """Calculate signal strength."""
        if data.empty:
            return 0.0

        # Use confidence column if available
        if "confidence" in data.columns:
            return float(data["confidence"].mean())

        # Use signal_confidence if available
        if "signal_confidence" in data.columns:
            return float(data["signal_confidence"].mean())

        # Default calculation based on data quality
        return 0.5

    def _calculate_confidence_level(self, data: pd.DataFrame) -> float:
        """Calculate confidence level."""
        if data.empty:
            return 0.0

        # Look for explicit confidence columns
        confidence_columns = ["confidence_level", "statistical_significance", "p_value"]

        for col in confidence_columns:
            if col in data.columns:
                if col == "p_value":
                    # Convert p-value to confidence (1 - p_value)
                    return float(1.0 - data[col].mean())
                return float(data[col].mean())

        # Default confidence calculation
        return 0.6

    def _calculate_signal_to_noise_ratio(
        self,
        signal_data: pd.DataFrame,
        baseline_data: pd.DataFrame | None = None,
    ) -> float:
        """Calculate signal-to-noise ratio."""
        if signal_data.empty:
            return 0.0

        # Simple SNR calculation
        numeric_cols = signal_data.select_dtypes(include=["number"]).columns

        if len(numeric_cols) == 0:
            return 0.0

        signal_values = signal_data[numeric_cols[0]]
        signal_mean = signal_values.mean()
        signal_std = signal_values.std()

        if signal_std == 0:
            return float("inf") if signal_mean != 0 else 0.0

        return abs(signal_mean) / signal_std

    def _calculate_consistency_score(self, data: pd.DataFrame) -> float:
        """Calculate consistency score."""
        if data.empty:
            return 0.0

        # Look for consistency-related columns
        if "consistency_score" in data.columns:
            return float(data["consistency_score"].mean())

        # Calculate based on signal variability
        numeric_cols = data.select_dtypes(include=["number"]).columns

        if len(numeric_cols) == 0:
            return 0.0

        # Use coefficient of variation as consistency measure
        for col in numeric_cols:
            series = data[col]
            if series.std() == 0:
                return 1.0  # Perfect consistency
            cv = series.std() / abs(series.mean()) if series.mean() != 0 else 0
            return max(0.0, 1.0 - cv)  # Higher consistency = lower variability

        return 0.5

    def _calculate_reliability_index(self, data: pd.DataFrame) -> float:
        """Calculate reliability index."""
        if data.empty:
            return 0.0

        # Composite reliability based on multiple factors
        factors = []

        # Data completeness
        completeness = 1.0 - (
            data.isnull().sum().sum() / (len(data) * len(data.columns))
        )
        factors.append(completeness)

        # Data consistency (low variance indicates higher reliability)
        numeric_cols = data.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            consistency = self._calculate_consistency_score(data)
            factors.append(consistency)

        # Sample size factor (more data = higher reliability)
        sample_size_factor = min(1.0, len(data) / 100.0)  # Normalize to 100 samples
        factors.append(sample_size_factor)

        return sum(factors) / len(factors) if factors else 0.0
