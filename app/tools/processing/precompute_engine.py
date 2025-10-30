"""
Pre-computation Engine for Common Parameter Combinations

This module implements result pre-computation for the 20 most common parameter combinations
to provide instant responses for frequently requested analyses.
"""

import hashlib
import json
import logging
import threading
import time
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from .cache_manager import IntelligentCacheManager
from .performance_monitor import get_performance_monitor


logger = logging.getLogger(__name__)


@dataclass
class ParameterCombination:
    """Represents a parameter combination for pre-computation."""

    strategy_type: str
    ticker: str
    timeframe: str
    parameters: dict[str, Any]
    access_count: int = 0
    last_accessed: datetime | None = None
    computation_time_ms: float | None = None
    result_size_mb: float | None = None


@dataclass
class PrecomputeJob:
    """Represents a pre-computation job."""

    combination: ParameterCombination
    priority: float
    estimated_time_ms: float
    job_id: str
    status: str = "pending"  # pending, running, completed, failed
    result_cache_key: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class UsageAnalyzer:
    """Analyzes usage patterns to identify common parameter combinations."""

    def __init__(self, usage_file: Path | None = None):
        """Initialize usage analyzer."""
        self.usage_file = usage_file or Path("cache/usage_analysis.json")
        self.request_history: list[dict[str, Any]] = []
        self.combination_counter: Counter = Counter()
        self.parameter_patterns: dict[str, dict[str, Counter]] = defaultdict(
            lambda: defaultdict(Counter),
        )
        self._lock = threading.Lock()

        # Load existing usage data
        self._load_usage_data()

    def track_request(
        self,
        strategy_type: str,
        ticker: str,
        timeframe: str,
        parameters: dict[str, Any],
        computation_time_ms: float = 0.0,
        result_size_mb: float = 0.0,
    ):
        """Track a strategy analysis request."""
        request_data = {
            "strategy_type": strategy_type,
            "ticker": ticker,
            "timeframe": timeframe,
            "parameters": parameters.copy(),
            "timestamp": datetime.now().isoformat(),
            "computation_time_ms": computation_time_ms,
            "result_size_mb": result_size_mb,
        }

        with self._lock:
            self.request_history.append(request_data)

            # Create combination key
            combo_key = self._create_combination_key(
                strategy_type,
                ticker,
                timeframe,
                parameters,
            )
            self.combination_counter[combo_key] += 1

            # Track parameter patterns
            self.parameter_patterns[strategy_type]["ticker"][ticker] += 1
            self.parameter_patterns[strategy_type]["timeframe"][timeframe] += 1

            for param_name, param_value in parameters.items():
                self.parameter_patterns[strategy_type][param_name][
                    str(param_value)
                ] += 1

            # Keep only recent history (last 10,000 requests)
            if len(self.request_history) > 10000:
                self.request_history = self.request_history[-10000:]

    def get_top_combinations(
        self,
        limit: int = 20,
        min_requests: int = 3,
    ) -> list[ParameterCombination]:
        """Get the most frequently requested parameter combinations."""
        with self._lock:
            # Filter combinations with sufficient requests
            filtered_combinations = {
                combo_key: count
                for combo_key, count in self.combination_counter.items()
                if count >= min_requests
            }

            # Sort by frequency
            sorted_combinations = sorted(
                filtered_combinations.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:limit]

            # Convert to ParameterCombination objects
            combinations = []
            for combo_key, access_count in sorted_combinations:
                # Parse combination key back to components
                combo_data = self._parse_combination_key(combo_key)
                if combo_data:
                    # Find recent request for timing data
                    recent_request = self._find_recent_request(combo_data)

                    combination = ParameterCombination(
                        strategy_type=combo_data["strategy_type"],
                        ticker=combo_data["ticker"],
                        timeframe=combo_data["timeframe"],
                        parameters=combo_data["parameters"],
                        access_count=access_count,
                        last_accessed=self._get_last_access_time(combo_key),
                        computation_time_ms=recent_request.get("computation_time_ms"),
                        result_size_mb=recent_request.get("result_size_mb"),
                    )
                    combinations.append(combination)

            return combinations

    def get_parameter_insights(
        self,
        strategy_type: str | None = None,
    ) -> dict[str, Any]:
        """Get insights about parameter usage patterns."""
        with self._lock:
            if strategy_type:
                patterns = {strategy_type: self.parameter_patterns[strategy_type]}
            else:
                patterns = dict(self.parameter_patterns)

            insights: dict[str, Any] = {}
            for strat_type, params in patterns.items():
                insights[strat_type] = {}

                for param_name, value_counter in params.items():
                    total_count = sum(value_counter.values())
                    top_values = value_counter.most_common(5)

                    insights[strat_type][param_name] = {
                        "total_requests": total_count,
                        "unique_values": len(value_counter),
                        "top_values": [
                            {
                                "value": value,
                                "count": count,
                                "percentage": count / total_count * 100,
                            }
                            for value, count in top_values
                        ],
                    }

            return insights

    def _create_combination_key(
        self,
        strategy_type: str,
        ticker: str,
        timeframe: str,
        parameters: dict[str, Any],
    ) -> str:
        """Create a unique key for a parameter combination."""
        # Sort parameters for consistent key generation
        sorted_params = sorted(parameters.items())
        key_data = f"{strategy_type}|{ticker}|{timeframe}|{sorted_params}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def _parse_combination_key(self, combo_key: str) -> dict[str, Any] | None:
        """Parse combination key back to components (reverse lookup)."""
        # This requires searching through request history to find matching combination
        for request in reversed(self.request_history):  # Start with most recent
            test_key = self._create_combination_key(
                request["strategy_type"],
                request["ticker"],
                request["timeframe"],
                request["parameters"],
            )

            if test_key == combo_key:
                return {
                    "strategy_type": request["strategy_type"],
                    "ticker": request["ticker"],
                    "timeframe": request["timeframe"],
                    "parameters": request["parameters"],
                }

        return None

    def _find_recent_request(self, combo_data: dict[str, Any]) -> dict[str, Any]:
        """Find the most recent request for a combination."""
        for request in reversed(self.request_history):
            if (
                request["strategy_type"] == combo_data["strategy_type"]
                and request["ticker"] == combo_data["ticker"]
                and request["timeframe"] == combo_data["timeframe"]
                and request["parameters"] == combo_data["parameters"]
            ):
                return request

        return {}

    def _get_last_access_time(self, combo_key: str) -> datetime | None:
        """Get the last access time for a combination."""
        for request in reversed(self.request_history):
            test_key = self._create_combination_key(
                request["strategy_type"],
                request["ticker"],
                request["timeframe"],
                request["parameters"],
            )

            if test_key == combo_key:
                return datetime.fromisoformat(request["timestamp"])

        return None

    def _load_usage_data(self):
        """Load usage data from file."""
        if not self.usage_file.exists():
            return

        try:
            with open(self.usage_file) as f:
                data = json.load(f)

            self.request_history = data.get("request_history", [])

            # Rebuild counters from history
            for request in self.request_history:
                combo_key = self._create_combination_key(
                    request["strategy_type"],
                    request["ticker"],
                    request["timeframe"],
                    request["parameters"],
                )
                self.combination_counter[combo_key] += 1

                # Rebuild parameter patterns
                strategy_type = request["strategy_type"]
                self.parameter_patterns[strategy_type]["ticker"][request["ticker"]] += 1
                self.parameter_patterns[strategy_type]["timeframe"][
                    request["timeframe"]
                ] += 1

                for param_name, param_value in request["parameters"].items():
                    self.parameter_patterns[strategy_type][param_name][
                        str(param_value)
                    ] += 1

            logger.info(f"Loaded {len(self.request_history)} usage records")

        except Exception as e:
            logger.warning(f"Failed to load usage data: {e}")

    def save_usage_data(self):
        """Save usage data to file."""
        try:
            self.usage_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "request_history": self.request_history,
                "last_saved": datetime.now().isoformat(),
                "total_combinations": len(self.combination_counter),
                "top_combinations": [
                    {"key": key, "count": count}
                    for key, count in self.combination_counter.most_common(50)
                ],
            }

            with open(self.usage_file, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.exception(f"Failed to save usage data: {e}")


class PrecomputeEngine:
    """Engine for pre-computing common parameter combinations."""

    def __init__(
        self,
        cache_manager: IntelligentCacheManager | None = None,
        usage_analyzer: UsageAnalyzer | None = None,
        precompute_interval: int = 3600,  # 1 hour
        max_precompute_time: int = 1800,  # 30 minutes
        result_ttl: int = 86400,  # 24 hours
    ):
        """Initialize pre-compute engine."""
        self.cache_manager = cache_manager
        self.usage_analyzer = usage_analyzer or UsageAnalyzer()
        self.precompute_interval = precompute_interval
        self.max_precompute_time = max_precompute_time
        self.result_ttl = result_ttl

        self.strategy_executors: dict[str, Callable] = {}
        self.precompute_jobs: dict[str, PrecomputeJob] = {}
        self.precompute_stats = {
            "jobs_completed": 0,
            "jobs_failed": 0,
            "total_precompute_time": 0.0,
            "cache_hits_from_precompute": 0,
            "last_precompute_cycle": None,
        }

        self.active_precomputing = False
        self._precompute_thread = None
        self.performance_monitor = get_performance_monitor()

    def register_strategy_executor(self, strategy_type: str, executor: Callable):
        """Register a strategy executor for pre-computation.

        Args:
            strategy_type: Strategy type (e.g., 'SMA', 'EMA', 'MACD')
            executor: Function that executes the strategy given parameters
        """
        self.strategy_executors[strategy_type] = executor
        logger.info(f"Registered strategy executor for: {strategy_type}")

    def track_request(
        self,
        strategy_type: str,
        ticker: str,
        timeframe: str,
        parameters: dict[str, Any],
        computation_time_ms: float = 0.0,
        result_size_mb: float = 0.0,
    ):
        """Track a strategy request for usage analysis."""
        self.usage_analyzer.track_request(
            strategy_type,
            ticker,
            timeframe,
            parameters,
            computation_time_ms,
            result_size_mb,
        )

    def start_precomputing(self, daemon: bool = True):
        """Start the pre-computation cycle."""
        if self.active_precomputing:
            logger.warning("Pre-computing already active")
            return

        if not self.cache_manager:
            logger.error("Cannot start pre-computing without cache manager")
            return

        self.active_precomputing = True
        self._precompute_thread = threading.Thread(
            target=self._precompute_loop,
            daemon=daemon,
            name="PrecomputeEngine",
        )
        self._precompute_thread.start()
        logger.info("Pre-computation started")

    def stop_precomputing(self):
        """Stop the pre-computation cycle."""
        self.active_precomputing = False
        if self._precompute_thread and self._precompute_thread.is_alive():
            self._precompute_thread.join(timeout=10)
        logger.info("Pre-computation stopped")

    def _precompute_loop(self):
        """Main pre-computation loop."""
        while self.active_precomputing:
            try:
                self._execute_precompute_cycle()
            except Exception as e:
                logger.exception(f"Error in pre-compute cycle: {e}")

            # Wait for next cycle
            time.sleep(self.precompute_interval)

    def _execute_precompute_cycle(self):
        """Execute a single pre-computation cycle."""
        start_time = time.time()
        logger.info("Starting pre-computation cycle")

        # Get top combinations to pre-compute
        top_combinations = self.usage_analyzer.get_top_combinations(
            limit=20,
            min_requests=3,
        )

        if not top_combinations:
            logger.info("No combinations found for pre-computation")
            return

        # Create pre-compute jobs
        jobs = self._create_precompute_jobs(top_combinations)

        # Execute jobs within time limit
        completed, failed = self._execute_precompute_jobs(jobs)

        # Update stats
        cycle_time = time.time() - start_time
        self.precompute_stats["jobs_completed"] += completed
        self.precompute_stats["jobs_failed"] += failed
        self.precompute_stats["total_precompute_time"] += cycle_time
        self.precompute_stats["last_precompute_cycle"] = datetime.now()

        logger.info(
            f"Pre-compute cycle completed in {cycle_time:.2f}s: "
            f"{completed} jobs completed, {failed} jobs failed",
        )

        # Save usage data
        self.usage_analyzer.save_usage_data()

    def _create_precompute_jobs(
        self,
        combinations: list[ParameterCombination],
    ) -> list[PrecomputeJob]:
        """Create pre-compute jobs from parameter combinations."""
        jobs = []

        for combination in combinations:
            # Check if strategy executor is available
            if combination.strategy_type not in self.strategy_executors:
                logger.debug(f"No executor available for {combination.strategy_type}")
                continue

            # Check if result is already cached and fresh
            cache_key = self._create_cache_key(combination)
            if self._is_result_fresh(cache_key):
                logger.debug(f"Fresh result exists for {cache_key}")
                continue

            # Calculate priority (higher access count = higher priority)
            priority = combination.access_count

            # Estimate computation time
            estimated_time = (
                combination.computation_time_ms or 5000.0
            )  # Default 5 seconds

            job = PrecomputeJob(
                combination=combination,
                priority=priority,
                estimated_time_ms=estimated_time,
                job_id=f"precompute_{cache_key[:8]}_{int(time.time())}",
                result_cache_key=cache_key,
            )

            jobs.append(job)

        # Sort by priority (highest first)
        jobs.sort(key=lambda j: j.priority, reverse=True)
        return jobs

    def _execute_precompute_jobs(self, jobs: list[PrecomputeJob]) -> tuple[int, int]:
        """Execute pre-compute jobs within time limit."""
        completed = 0
        failed = 0
        total_time = 0

        for job in jobs:
            if total_time >= self.max_precompute_time:
                logger.info(
                    f"Pre-compute time limit reached ({self.max_precompute_time}s)",
                )
                break

            try:
                job_start_time = time.time()
                job.status = "running"
                job.started_at = datetime.now()

                # Execute strategy
                result = self._execute_strategy_job(job)

                if result is not None:
                    # Cache result
                    self.cache_manager.set(
                        job.result_cache_key,
                        result,
                        category="precomputed",
                        ttl=self.result_ttl,
                    )

                    job.status = "completed"
                    job.completed_at = datetime.now()
                    completed += 1

                    job_time = time.time() - job_start_time
                    total_time += job_time

                    logger.debug(f"Pre-computed {job.job_id} in {job_time:.2f}s")
                else:
                    job.status = "failed"
                    job.error_message = "Strategy returned no result"
                    failed += 1

            except Exception as e:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now()
                failed += 1
                logger.warning(f"Failed to pre-compute {job.job_id}: {e}")

            # Store job for tracking
            self.precompute_jobs[job.job_id] = job

        return completed, failed

    def _execute_strategy_job(self, job: PrecomputeJob) -> Any:
        """Execute a strategy for pre-computation."""
        combination = job.combination
        executor = self.strategy_executors[combination.strategy_type]

        # Prepare execution parameters
        execution_params = {
            "ticker": combination.ticker,
            "timeframe": combination.timeframe,
            **combination.parameters,
        }

        # Execute with performance monitoring
        with self.performance_monitor.monitor_operation(
            f"precompute_{combination.strategy_type}",
        ):
            return executor(execution_params)

    def _create_cache_key(self, combination: ParameterCombination) -> str:
        """Create cache key for a parameter combination."""
        key_data = {
            "strategy_type": combination.strategy_type,
            "ticker": combination.ticker,
            "timeframe": combination.timeframe,
            "parameters": combination.parameters,
            "precomputed": True,
        }

        key_string = json.dumps(key_data, sort_keys=True)
        return f"precomputed_{hashlib.md5(key_string.encode(), usedforsecurity=False).hexdigest()}"

    def _is_result_fresh(self, cache_key: str) -> bool:
        """Check if cached result is still fresh."""
        if not self.cache_manager:
            return False

        try:
            result = self.cache_manager.get(cache_key, category="precomputed")
            return result is not None
        except Exception:
            return False

    def check_precomputed_result(
        self,
        strategy_type: str,
        ticker: str,
        timeframe: str,
        parameters: dict[str, Any],
    ) -> Any | None:
        """Check if a pre-computed result exists for the given parameters."""
        if not self.cache_manager:
            return None

        combination = ParameterCombination(
            strategy_type=strategy_type,
            ticker=ticker,
            timeframe=timeframe,
            parameters=parameters,
        )

        cache_key = self._create_cache_key(combination)

        try:
            result = self.cache_manager.get(cache_key, category="precomputed")
            if result is not None:
                self.precompute_stats["cache_hits_from_precompute"] += 1
                logger.debug(f"Pre-computed result found for {cache_key}")
            return result
        except Exception as e:
            logger.debug(f"Failed to retrieve pre-computed result: {e}")
            return None

    def trigger_immediate_precompute(self, limit: int = 5) -> dict[str, str]:
        """Trigger immediate pre-computation for top combinations."""
        if not self.cache_manager:
            return {"error": "No cache manager available"}

        top_combinations = self.usage_analyzer.get_top_combinations(limit=limit)
        jobs = self._create_precompute_jobs(top_combinations)

        results = {}
        for job in jobs[:limit]:  # Limit to requested number
            try:
                job.status = "running"
                job.started_at = datetime.now()

                result = self._execute_strategy_job(job)

                if result is not None:
                    self.cache_manager.set(
                        job.result_cache_key,
                        result,
                        category="precomputed",
                        ttl=self.result_ttl,
                    )

                    job.status = "completed"
                    results[job.job_id] = "completed"
                else:
                    job.status = "failed"
                    results[job.job_id] = "failed - no result"

                job.completed_at = datetime.now()
                self.precompute_jobs[job.job_id] = job

            except Exception as e:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now()
                results[job.job_id] = f"failed - {e!s}"
                self.precompute_jobs[job.job_id] = job

        return results

    def get_precompute_status(self) -> dict[str, Any]:
        """Get pre-computation status and statistics."""
        top_combinations = self.usage_analyzer.get_top_combinations(limit=10)
        usage_insights = self.usage_analyzer.get_parameter_insights()

        return {
            "active": self.active_precomputing,
            "registered_executors": list(self.strategy_executors.keys()),
            "stats": self.precompute_stats.copy(),
            "top_combinations": [
                {
                    "strategy_type": combo.strategy_type,
                    "ticker": combo.ticker,
                    "timeframe": combo.timeframe,
                    "access_count": combo.access_count,
                    "last_accessed": (
                        combo.last_accessed.isoformat() if combo.last_accessed else None
                    ),
                    "computation_time_ms": combo.computation_time_ms,
                }
                for combo in top_combinations
            ],
            "usage_insights": usage_insights,
            "recent_jobs": len(
                [
                    j
                    for j in self.precompute_jobs.values()
                    if j.completed_at
                    and j.completed_at > datetime.now() - timedelta(hours=24)
                ],
            ),
        }


# Global pre-compute engine instance
_global_precompute_engine: PrecomputeEngine | None = None


def get_precompute_engine(
    cache_manager: IntelligentCacheManager | None = None,
    auto_start: bool = False,
) -> PrecomputeEngine:
    """Get or create global pre-compute engine instance."""
    global _global_precompute_engine

    if _global_precompute_engine is None:
        _global_precompute_engine = PrecomputeEngine(cache_manager)

        if auto_start and cache_manager:
            _global_precompute_engine.start_precomputing()

    return _global_precompute_engine


def configure_precomputing(
    cache_manager: IntelligentCacheManager | None = None,
    precompute_interval: int = 3600,
    max_precompute_time: int = 1800,
    result_ttl: int = 86400,
    auto_start: bool = True,
) -> PrecomputeEngine:
    """Configure and get pre-compute engine with custom settings."""
    global _global_precompute_engine

    _global_precompute_engine = PrecomputeEngine(
        cache_manager=cache_manager,
        precompute_interval=precompute_interval,
        max_precompute_time=max_precompute_time,
        result_ttl=result_ttl,
    )

    if auto_start and cache_manager:
        _global_precompute_engine.start_precomputing()

    return _global_precompute_engine
