"""
Pattern Recognition System

Identifies recurring performance patterns and trends using statistical
pattern matching algorithms and regime change detection.
"""

from datetime import datetime
import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ..config.statistical_analysis_config import SPDSConfig
from ..models.correlation_models import PatternResult, SignificanceLevel


class PatternRecognitionSystem:
    """
    Identifies and analyzes recurring patterns in trading performance data.

    Provides pattern detection using:
    - Statistical pattern matching
    - Sliding window analysis
    - Regime change detection
    - Cluster analysis
    - Shape-based pattern recognition
    """

    def __init__(self, config: SPDSConfig, logger: logging.Logger | None = None):
        """
        Initialize the Pattern Recognition System

        Args:
            config: SPDS configuration instance
            logger: Logger instance for operations
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Pattern detection parameters
        self.min_pattern_length = 5
        self.max_pattern_length = 20
        self.similarity_threshold = 0.8
        self.min_pattern_frequency = 3

        # Sliding window parameters
        self.window_sizes = [5, 10, 15, 20]
        self.step_size = 1

        # Regime detection parameters
        self.regime_change_threshold = 2.0  # Standard deviations
        self.min_regime_length = 10

        # Pattern storage
        self.discovered_patterns = {}
        self.pattern_performance = {}

        self.logger.info("PatternRecognitionSystem initialized")

    async def discover_patterns(
        self,
        data: dict[str, pd.Series] | pd.DataFrame,
        entity_name: str,
        timeframe: str = "D",
    ) -> list[PatternResult]:
        """
        Discover patterns in performance data

        Args:
            data: Performance data (returns, equity curves, etc.)
            entity_name: Name of entity being analyzed
            timeframe: Timeframe of data

        Returns:
            List of discovered patterns
        """
        try:
            self.logger.info(f"Starting pattern discovery for {entity_name}")

            # Convert data to suitable format
            if isinstance(data, dict):
                # Assume it's a single time series
                time_series = next(iter(data.values())) if data else pd.Series([])
            else:
                # Assume it's a DataFrame with a primary column
                time_series = data.iloc[:, 0] if not data.empty else pd.Series([])

            if len(time_series) < self.min_pattern_length * 2:
                self.logger.warning(
                    f"Insufficient data for pattern discovery: {len(time_series)}"
                )
                return []

            discovered_patterns = []

            # 1. Shape-based pattern discovery
            shape_patterns = await self._discover_shape_patterns(
                time_series, entity_name, timeframe
            )
            discovered_patterns.extend(shape_patterns)

            # 2. Statistical pattern discovery
            statistical_patterns = await self._discover_statistical_patterns(
                time_series, entity_name, timeframe
            )
            discovered_patterns.extend(statistical_patterns)

            # 3. Regime change patterns
            regime_patterns = await self._discover_regime_patterns(
                time_series, entity_name, timeframe
            )
            discovered_patterns.extend(regime_patterns)

            # 4. Cyclical patterns
            cyclical_patterns = await self._discover_cyclical_patterns(
                time_series, entity_name, timeframe
            )
            discovered_patterns.extend(cyclical_patterns)

            # 5. Volatility patterns
            volatility_patterns = await self._discover_volatility_patterns(
                time_series, entity_name, timeframe
            )
            discovered_patterns.extend(volatility_patterns)

            # Filter and rank patterns by significance
            significant_patterns = await self._filter_and_rank_patterns(
                discovered_patterns
            )

            self.logger.info(
                f"Discovered {len(significant_patterns)} significant patterns for {entity_name}"
            )

            return significant_patterns

        except Exception as e:
            self.logger.error(f"Pattern discovery failed for {entity_name}: {e}")
            raise

    async def match_patterns(
        self,
        current_data: pd.Series | np.ndarray,
        entity_name: str,
        pattern_library: list[PatternResult] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Match current data against known patterns

        Args:
            current_data: Current performance data
            entity_name: Entity being analyzed
            pattern_library: Known patterns to match against

        Returns:
            List of pattern matches with similarity scores
        """
        try:
            if pattern_library is None:
                pattern_library = self.discovered_patterns.get(entity_name, [])

            if not pattern_library:
                return []

            current_series = (
                pd.Series(current_data)
                if not isinstance(current_data, pd.Series)
                else current_data
            )

            # Normalize current data
            normalized_current = self._normalize_series(current_series)

            matches = []

            for pattern in pattern_library:
                # Extract pattern template
                pattern_template = pattern.pattern_data.get("template", [])

                if len(pattern_template) == 0:
                    continue

                # Calculate similarity
                similarity = await self._calculate_pattern_similarity(
                    normalized_current, pattern_template
                )

                if similarity >= self.similarity_threshold:
                    # Calculate confidence based on pattern history
                    confidence = self._calculate_match_confidence(
                        pattern, similarity, len(current_series)
                    )

                    match = {
                        "pattern_id": pattern.pattern_id,
                        "pattern_name": pattern.pattern_name,
                        "pattern_type": pattern.pattern_type,
                        "similarity_score": similarity,
                        "confidence_score": confidence,
                        "pattern_strength": pattern.pattern_strength,
                        "historical_success_rate": pattern.success_rate,
                        "expected_outcome": pattern.pattern_outcome,
                        "pattern_duration": pattern.pattern_duration,
                        "entities_with_pattern": pattern.entities_involved,
                        "last_seen": pattern.detection_timestamp,
                    }

                    matches.append(match)

            # Sort by confidence score
            matches.sort(key=lambda x: x["confidence_score"], reverse=True)

            return matches[:10]  # Return top 10 matches

        except Exception as e:
            self.logger.error(f"Pattern matching failed: {e}")
            raise

    async def detect_regime_changes(
        self, data: pd.Series | np.ndarray, window_size: int = 20
    ) -> list[dict[str, Any]]:
        """
        Detect regime changes in time series data

        Args:
            data: Time series data
            window_size: Window size for regime detection

        Returns:
            List of detected regime changes
        """
        try:
            series = pd.Series(data) if not isinstance(data, pd.Series) else data

            if len(series) < window_size * 2:
                return []

            regime_changes = []

            # Calculate rolling statistics
            series.rolling(window=window_size).mean()
            series.rolling(window=window_size).std()

            # Detect significant changes in mean and volatility
            for i in range(window_size, len(series) - window_size):
                # Compare current window with previous window
                current_window = series.iloc[i : i + window_size]
                previous_window = series.iloc[i - window_size : i]

                # Test for mean change
                mean_change = abs(current_window.mean() - previous_window.mean())
                pooled_std = np.sqrt((current_window.var() + previous_window.var()) / 2)

                if pooled_std > 0:
                    z_score = mean_change / pooled_std

                    if z_score > self.regime_change_threshold:
                        # Statistical test for regime change
                        from scipy.stats import ttest_ind

                        _, p_value = ttest_ind(previous_window, current_window)

                        if p_value < 0.05:  # Significant change
                            regime_change = {
                                "change_point": i,
                                "change_timestamp": (
                                    series.index[i]
                                    if hasattr(series.index, "__getitem__")
                                    else i
                                ),
                                "z_score": z_score,
                                "p_value": p_value,
                                "previous_mean": previous_window.mean(),
                                "current_mean": current_window.mean(),
                                "previous_std": previous_window.std(),
                                "current_std": current_window.std(),
                                "change_magnitude": mean_change,
                                "change_direction": (
                                    "increase"
                                    if current_window.mean() > previous_window.mean()
                                    else "decrease"
                                ),
                            }

                            regime_changes.append(regime_change)

            return regime_changes

        except Exception as e:
            self.logger.error(f"Regime change detection failed: {e}")
            raise

    async def analyze_pattern_performance(
        self, patterns: list[PatternResult], outcomes_data: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze the performance of discovered patterns

        Args:
            patterns: List of patterns to analyze
            outcomes_data: Historical outcome data

        Returns:
            Pattern performance analysis
        """
        try:
            performance_analysis = {
                "total_patterns": len(patterns),
                "pattern_success_rates": {},
                "pattern_reliability": {},
                "best_performing_patterns": [],
                "pattern_frequency_analysis": {},
                "pattern_duration_analysis": {},
            }

            for pattern in patterns:
                pattern_id = pattern.pattern_id

                # Calculate success rate
                success_rate = pattern.success_rate or 0.5
                performance_analysis["pattern_success_rates"][pattern_id] = success_rate

                # Calculate reliability score
                reliability = self._calculate_pattern_reliability(pattern)
                performance_analysis["pattern_reliability"][pattern_id] = reliability

                # Frequency analysis
                performance_analysis["pattern_frequency_analysis"][pattern_id] = {
                    "frequency": pattern.pattern_frequency,
                    "entities_count": len(pattern.entities_involved),
                    "strength": pattern.pattern_strength,
                }

                # Duration analysis
                performance_analysis["pattern_duration_analysis"][pattern_id] = {
                    "average_duration": pattern.pattern_duration,
                    "pattern_type": pattern.pattern_type,
                }

            # Identify best performing patterns
            sorted_patterns = sorted(
                patterns,
                key=lambda p: (p.success_rate or 0.5)
                * p.pattern_strength
                * p.confidence_score,
                reverse=True,
            )

            performance_analysis["best_performing_patterns"] = [
                {
                    "pattern_id": p.pattern_id,
                    "pattern_name": p.pattern_name,
                    "composite_score": (p.success_rate or 0.5)
                    * p.pattern_strength
                    * p.confidence_score,
                    "success_rate": p.success_rate,
                    "pattern_strength": p.pattern_strength,
                    "confidence_score": p.confidence_score,
                }
                for p in sorted_patterns[:5]
            ]

            return performance_analysis

        except Exception as e:
            self.logger.error(f"Pattern performance analysis failed: {e}")
            raise

    # Helper methods for pattern discovery

    async def _discover_shape_patterns(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> list[PatternResult]:
        """Discover shape-based patterns using sliding window"""
        patterns = []

        try:
            normalized_series = self._normalize_series(series)

            # Extract subsequences of different lengths
            for window_size in self.window_sizes:
                if len(series) < window_size * 2:
                    continue

                subsequences = []
                for i in range(len(normalized_series) - window_size + 1):
                    subseq = normalized_series.iloc[i : i + window_size].values
                    subsequences.append(subseq)

                if len(subsequences) < self.min_pattern_frequency:
                    continue

                # Cluster similar subsequences
                clusters = await self._cluster_subsequences(subsequences)

                # Create patterns from significant clusters
                for _cluster_id, cluster_data in clusters.items():
                    if len(cluster_data["indices"]) >= self.min_pattern_frequency:
                        pattern = self._create_shape_pattern(
                            cluster_data, window_size, entity_name, timeframe
                        )
                        patterns.append(pattern)

            return patterns

        except Exception as e:
            self.logger.warning(f"Shape pattern discovery failed: {e}")
            return []

    async def _discover_statistical_patterns(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> list[PatternResult]:
        """Discover statistical patterns (mean reversion, momentum, etc.)"""
        patterns = []

        try:
            # Mean reversion patterns
            mr_pattern = await self._detect_mean_reversion_pattern(
                series, entity_name, timeframe
            )
            if mr_pattern:
                patterns.append(mr_pattern)

            # Momentum patterns
            momentum_pattern = await self._detect_momentum_pattern(
                series, entity_name, timeframe
            )
            if momentum_pattern:
                patterns.append(momentum_pattern)

            # Volatility clustering patterns
            vol_pattern = await self._detect_volatility_clustering(
                series, entity_name, timeframe
            )
            if vol_pattern:
                patterns.append(vol_pattern)

            return patterns

        except Exception as e:
            self.logger.warning(f"Statistical pattern discovery failed: {e}")
            return []

    async def _discover_regime_patterns(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> list[PatternResult]:
        """Discover regime change patterns"""
        try:
            regime_changes = await self.detect_regime_changes(series)

            if len(regime_changes) < 2:
                return []

            # Analyze regime transition patterns
            transition_pattern = self._create_regime_transition_pattern(
                regime_changes, entity_name, timeframe
            )

            return [transition_pattern] if transition_pattern else []

        except Exception as e:
            self.logger.warning(f"Regime pattern discovery failed: {e}")
            return []

    async def _discover_cyclical_patterns(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> list[PatternResult]:
        """Discover cyclical patterns using frequency analysis"""
        try:
            # Use FFT to detect dominant frequencies
            fft = np.fft.fft(series.fillna(0).values)
            frequencies = np.fft.fftfreq(len(series))

            # Find dominant frequencies
            magnitude = np.abs(fft)
            dominant_freq_idx = np.argsort(magnitude)[-5:]  # Top 5 frequencies

            patterns = []
            for idx in dominant_freq_idx:
                if frequencies[idx] > 0:  # Positive frequencies only
                    period = 1 / frequencies[idx]
                    if 5 <= period <= len(series) / 3:  # Reasonable periods
                        cyclical_pattern = self._create_cyclical_pattern(
                            period, magnitude[idx], entity_name, timeframe
                        )
                        patterns.append(cyclical_pattern)

            return patterns

        except Exception as e:
            self.logger.warning(f"Cyclical pattern discovery failed: {e}")
            return []

    async def _discover_volatility_patterns(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> list[PatternResult]:
        """Discover volatility-related patterns"""
        try:
            # Calculate rolling volatility
            rolling_vol = series.rolling(window=10).std()

            # Detect volatility regimes
            vol_regimes = await self.detect_regime_changes(rolling_vol)

            if len(vol_regimes) >= 2:
                vol_pattern = self._create_volatility_pattern(
                    vol_regimes, entity_name, timeframe
                )
                return [vol_pattern] if vol_pattern else []

            return []

        except Exception as e:
            self.logger.warning(f"Volatility pattern discovery failed: {e}")
            return []

    async def _cluster_subsequences(
        self, subsequences: list[np.ndarray]
    ) -> dict[int, dict[str, Any]]:
        """Cluster similar subsequences"""
        try:
            if len(subsequences) < 3:
                return {}

            # Standardize subsequences
            scaler = StandardScaler()
            X = scaler.fit_transform(subsequences)

            # Determine optimal number of clusters
            max_clusters = min(len(subsequences) // 2, 10)
            best_score = -1
            best_k = 2

            for k in range(2, max_clusters + 1):
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                labels = kmeans.fit_predict(X)

                if len(set(labels)) > 1:  # More than one cluster
                    score = silhouette_score(X, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k

            # Final clustering
            kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X)

            # Organize clusters
            clusters = {}
            for i, label in enumerate(labels):
                if label not in clusters:
                    clusters[label] = {
                        "indices": [],
                        "subsequences": [],
                        "centroid": kmeans.cluster_centers_[label],
                    }
                clusters[label]["indices"].append(i)
                clusters[label]["subsequences"].append(subsequences[i])

            return clusters

        except Exception as e:
            self.logger.warning(f"Subsequence clustering failed: {e}")
            return {}

    def _normalize_series(self, series: pd.Series) -> pd.Series:
        """Normalize series to zero mean and unit variance"""
        return (series - series.mean()) / (series.std() + 1e-8)

    async def _calculate_pattern_similarity(
        self, current_data: pd.Series, pattern_template: list[float]
    ) -> float:
        """Calculate similarity between current data and pattern template"""
        try:
            if len(current_data) < len(pattern_template):
                return 0.0

            # Take the last N points to match pattern length
            recent_data = current_data.tail(len(pattern_template))
            normalized_recent = self._normalize_series(recent_data)

            # Calculate correlation
            correlation = np.corrcoef(normalized_recent.values, pattern_template)[0, 1]

            # Convert to similarity score [0, 1]
            similarity = (correlation + 1) / 2

            return max(0.0, min(1.0, similarity))

        except Exception as e:
            self.logger.warning(f"Pattern similarity calculation failed: {e}")
            return 0.0

    def _calculate_match_confidence(
        self, pattern: PatternResult, similarity: float, data_length: int
    ) -> float:
        """Calculate confidence in pattern match"""
        # Base confidence from similarity
        base_confidence = similarity

        # Adjust for pattern strength
        strength_adjustment = pattern.pattern_strength

        # Adjust for pattern frequency (more frequent = more reliable)
        frequency_adjustment = min(pattern.pattern_frequency / 10, 1.0)

        # Adjust for data length (more data = more reliable)
        data_adjustment = min(data_length / 50, 1.0)

        # Composite confidence
        confidence = (
            base_confidence * 0.4
            + strength_adjustment * 0.3
            + frequency_adjustment * 0.2
            + data_adjustment * 0.1
        )

        return max(0.0, min(1.0, confidence))

    def _calculate_pattern_reliability(self, pattern: PatternResult) -> float:
        """Calculate overall pattern reliability"""
        # Combine multiple factors
        success_rate = pattern.success_rate or 0.5
        strength = pattern.pattern_strength
        confidence = pattern.confidence_score
        frequency = min(pattern.pattern_frequency / 5, 1.0)

        reliability = (
            success_rate * 0.4 + strength * 0.3 + confidence * 0.2 + frequency * 0.1
        )

        return max(0.0, min(1.0, reliability))

    def _create_shape_pattern(
        self,
        cluster_data: dict[str, Any],
        window_size: int,
        entity_name: str,
        timeframe: str,
    ) -> PatternResult:
        """Create a shape-based pattern from cluster data"""
        pattern_id = f"shape_{entity_name}_{timeframe}_{len(cluster_data['indices'])}_{window_size}"

        return PatternResult(
            pattern_id=pattern_id,
            pattern_type="shape",
            pattern_name=f"Shape pattern ({window_size} periods)",
            pattern_strength=min(len(cluster_data["indices"]) / 10, 1.0),
            confidence_score=0.7,  # Default confidence
            statistical_significance=SignificanceLevel.SIGNIFICANT,
            pattern_data={
                "template": cluster_data["centroid"].tolist(),
                "cluster_size": len(cluster_data["indices"]),
                "window_size": window_size,
            },
            pattern_duration=window_size,
            pattern_frequency=len(cluster_data["indices"]),
            entities_involved=[entity_name],
            timeframe=timeframe,
            similar_patterns=[],
            detection_timestamp=datetime.now(),
            detection_method="k_means_clustering",
        )

    async def _detect_mean_reversion_pattern(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> PatternResult | None:
        """Detect mean reversion pattern"""
        try:
            # Calculate Hurst exponent
            def hurst_exponent(ts):
                lags = range(2, min(100, len(ts) // 2))
                tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
                poly = np.polyfit(np.log(lags), np.log(tau), 1)
                return poly[0] * 2.0

            hurst = hurst_exponent(series.values)

            # Hurst < 0.5 indicates mean reversion
            if hurst < 0.4:
                pattern_id = f"mean_reversion_{entity_name}_{timeframe}"

                return PatternResult(
                    pattern_id=pattern_id,
                    pattern_type="mean_reversion",
                    pattern_name="Mean Reversion Pattern",
                    pattern_strength=1.0 - hurst,
                    confidence_score=0.8,
                    statistical_significance=SignificanceLevel.SIGNIFICANT,
                    pattern_data={"hurst_exponent": hurst},
                    pattern_duration=len(series),
                    pattern_frequency=1.0,
                    entities_involved=[entity_name],
                    timeframe=timeframe,
                    similar_patterns=[],
                    pattern_outcome="Mean reversion expected",
                    success_rate=0.7,
                    detection_timestamp=datetime.now(),
                    detection_method="hurst_exponent",
                )

            return None

        except Exception as e:
            self.logger.warning(f"Mean reversion detection failed: {e}")
            return None

    async def _detect_momentum_pattern(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> PatternResult | None:
        """Detect momentum pattern"""
        try:
            # Calculate momentum indicator
            momentum = series.diff(10).rolling(window=5).mean()

            # Detect strong momentum periods
            momentum_strength = abs(momentum).rolling(window=10).mean()
            strong_momentum_periods = momentum_strength > momentum_strength.quantile(
                0.8
            )

            if (
                strong_momentum_periods.sum() > len(series) * 0.2
            ):  # At least 20% of periods
                pattern_id = f"momentum_{entity_name}_{timeframe}"

                return PatternResult(
                    pattern_id=pattern_id,
                    pattern_type="momentum",
                    pattern_name="Momentum Pattern",
                    pattern_strength=float(strong_momentum_periods.mean()),
                    confidence_score=0.75,
                    statistical_significance=SignificanceLevel.SIGNIFICANT,
                    pattern_data={
                        "momentum_periods": int(strong_momentum_periods.sum()),
                        "average_momentum": float(momentum.mean()),
                    },
                    pattern_duration=len(series),
                    pattern_frequency=1.0,
                    entities_involved=[entity_name],
                    timeframe=timeframe,
                    similar_patterns=[],
                    pattern_outcome="Momentum continuation expected",
                    success_rate=0.65,
                    detection_timestamp=datetime.now(),
                    detection_method="momentum_analysis",
                )

            return None

        except Exception as e:
            self.logger.warning(f"Momentum detection failed: {e}")
            return None

    async def _detect_volatility_clustering(
        self, series: pd.Series, entity_name: str, timeframe: str
    ) -> PatternResult | None:
        """Detect volatility clustering pattern"""
        try:
            # Calculate squared returns (proxy for volatility)
            squared_returns = (series.diff() ** 2).fillna(0)

            # Test for autocorrelation in squared returns (ARCH effect)
            from statsmodels.stats.diagnostic import het_arch

            if len(squared_returns) > 20:
                lm_stat, lm_pvalue, f_stat, f_pvalue = het_arch(
                    squared_returns.dropna(), maxlag=5
                )

                if f_pvalue < 0.05:  # Significant ARCH effect
                    pattern_id = f"volatility_clustering_{entity_name}_{timeframe}"

                    return PatternResult(
                        pattern_id=pattern_id,
                        pattern_type="volatility_clustering",
                        pattern_name="Volatility Clustering Pattern",
                        pattern_strength=1.0 - f_pvalue,
                        confidence_score=0.8,
                        statistical_significance=SignificanceLevel.SIGNIFICANT,
                        pattern_data={
                            "arch_test_statistic": float(f_stat),
                            "arch_p_value": float(f_pvalue),
                        },
                        pattern_duration=len(series),
                        pattern_frequency=1.0,
                        entities_involved=[entity_name],
                        timeframe=timeframe,
                        similar_patterns=[],
                        pattern_outcome="Volatility clustering present",
                        success_rate=0.8,
                        detection_timestamp=datetime.now(),
                        detection_method="arch_test",
                    )

            return None

        except Exception as e:
            self.logger.warning(f"Volatility clustering detection failed: {e}")
            return None

    def _create_regime_transition_pattern(
        self, regime_changes: list[dict[str, Any]], entity_name: str, timeframe: str
    ) -> PatternResult | None:
        """Create pattern from regime changes"""
        if len(regime_changes) < 2:
            return None

        pattern_id = f"regime_transition_{entity_name}_{timeframe}"

        return PatternResult(
            pattern_id=pattern_id,
            pattern_type="regime_transition",
            pattern_name="Regime Transition Pattern",
            pattern_strength=0.8,
            confidence_score=0.75,
            statistical_significance=SignificanceLevel.SIGNIFICANT,
            pattern_data={
                "regime_changes": regime_changes,
                "change_count": len(regime_changes),
            },
            pattern_duration=len(regime_changes),
            pattern_frequency=len(regime_changes),
            entities_involved=[entity_name],
            timeframe=timeframe,
            similar_patterns=[],
            pattern_outcome="Regime transitions detected",
            detection_timestamp=datetime.now(),
            detection_method="regime_change_analysis",
        )

    def _create_cyclical_pattern(
        self, period: float, magnitude: float, entity_name: str, timeframe: str
    ) -> PatternResult:
        """Create cyclical pattern"""
        pattern_id = f"cyclical_{entity_name}_{timeframe}_{int(period)}"

        return PatternResult(
            pattern_id=pattern_id,
            pattern_type="cyclical",
            pattern_name=f"Cyclical Pattern ({int(period)} periods)",
            pattern_strength=min(magnitude / 1000, 1.0),  # Normalize magnitude
            confidence_score=0.6,
            statistical_significance=SignificanceLevel.MARGINALLY_SIGNIFICANT,
            pattern_data={"period": period, "magnitude": magnitude},
            pattern_duration=int(period),
            pattern_frequency=1.0,
            entities_involved=[entity_name],
            timeframe=timeframe,
            similar_patterns=[],
            pattern_outcome="Cyclical behavior expected",
            detection_timestamp=datetime.now(),
            detection_method="fft_analysis",
        )

    def _create_volatility_pattern(
        self, vol_regimes: list[dict[str, Any]], entity_name: str, timeframe: str
    ) -> PatternResult:
        """Create volatility pattern"""
        pattern_id = f"volatility_regime_{entity_name}_{timeframe}"

        return PatternResult(
            pattern_id=pattern_id,
            pattern_type="volatility_regime",
            pattern_name="Volatility Regime Pattern",
            pattern_strength=0.7,
            confidence_score=0.7,
            statistical_significance=SignificanceLevel.SIGNIFICANT,
            pattern_data={
                "volatility_regimes": vol_regimes,
                "regime_count": len(vol_regimes),
            },
            pattern_duration=len(vol_regimes),
            pattern_frequency=len(vol_regimes),
            entities_involved=[entity_name],
            timeframe=timeframe,
            similar_patterns=[],
            pattern_outcome="Volatility regime changes detected",
            detection_timestamp=datetime.now(),
            detection_method="volatility_regime_analysis",
        )

    async def _filter_and_rank_patterns(
        self, patterns: list[PatternResult]
    ) -> list[PatternResult]:
        """Filter and rank patterns by significance and quality"""
        # Filter out low-quality patterns
        significant_patterns = [
            p
            for p in patterns
            if p.pattern_strength >= 0.3 and p.confidence_score >= 0.5
        ]

        # Rank by composite score
        ranked_patterns = sorted(
            significant_patterns,
            key=lambda p: p.pattern_strength
            * p.confidence_score
            * (p.success_rate or 0.5),
            reverse=True,
        )

        return ranked_patterns
