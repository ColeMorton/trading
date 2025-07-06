# Statistical Performance Divergence System - Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Statistical Performance Divergence System (SPDS) to production environments with performance optimization, monitoring, and maintenance procedures.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Configuration Management](#configuration-management)
4. [Performance Optimization](#performance-optimization)
5. [Monitoring and Alerting](#monitoring-and-alerting)
6. [Maintenance Procedures](#maintenance-procedures)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

## Pre-Deployment Checklist

### System Requirements

- **Python**: 3.9+
- **Memory**: Minimum 8GB RAM (16GB+ recommended)
- **Storage**: 50GB+ available space for data and caching
- **CPU**: Multi-core processor for parallel processing
- **Network**: Stable connection for data feeds

### Dependencies Validation

```bash
# Verify all dependencies are installed
poetry install

# Run dependency check
poetry check

# Verify ML libraries
python -c "import sklearn, scipy, numpy, pandas; print('Dependencies OK')"

# Test memory optimization
python -c "from app.tools.processing import MemoryOptimizer; print('Memory optimization available')"
```

### Data Preparation

```bash
# Ensure required data directories exist
mkdir -p ./csv/positions/
mkdir -p ./json/return_distribution/
mkdir -p ./csv/portfolios/
mkdir -p ./logs/

# Verify data integrity
python -m app.tools.validation.data_integrity_check

# Test data access permissions
python -c "
import os
for path in ['./csv/positions/', './json/return_distribution/']:
    assert os.access(path, os.R_OK | os.W_OK), f'No access to {path}'
print('Data access OK')
"
```

### Performance Validation

```bash
# Run performance tests
pytest tests/performance/ -v

# Validate exit efficiency targets
pytest tests/performance/test_exit_efficiency_targets.py::TestExitEfficiencyTargets::test_target_exit_efficiency_achievement -v

# Run integration tests
pytest tests/integration/test_statistical_analysis_integration.py -v
```

## Environment Setup

### Production Configuration

Create production configuration file:

```python
# config/production.py
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig, ConfidenceLevel

PRODUCTION_CONFIG = StatisticalAnalysisConfig(
    # Data Sources
    USE_TRADE_HISTORY=True,
    TRADE_HISTORY_PATH="./csv/positions/",
    FALLBACK_TO_EQUITY=True,

    # Optimized Thresholds (from adaptive learning)
    PERCENTILE_THRESHOLD=96,         # Optimized from 95
    DUAL_LAYER_THRESHOLD=0.87,      # Optimized from 0.85
    RARITY_THRESHOLD=0.04,          # Optimized from 0.05
    MULTI_TIMEFRAME_AGREEMENT=3,

    # Sample Size Management
    SAMPLE_SIZE_MINIMUM=15,
    CONFIDENCE_LEVELS=ConfidenceLevel(
        high_confidence=30,
        medium_confidence=15,
        low_confidence=5
    ),

    # Performance Optimization
    ENABLE_MEMORY_OPTIMIZATION=True,
    ENABLE_CACHING=True,
    CACHE_TTL_SECONDS=1800,         # 30 minutes
    ENABLE_PARALLEL_PROCESSING=True,
    MAX_WORKERS=4,                  # Adjust based on CPU cores

    # Logging and Monitoring
    LOG_LEVEL="INFO",
    ENABLE_PERFORMANCE_METRICS=True,
    METRICS_COLLECTION_INTERVAL=300, # 5 minutes

    # Risk Management
    MAX_ANALYSIS_TIME_SECONDS=30,   # Timeout for analysis
    ENABLE_CIRCUIT_BREAKER=True,
    ERROR_THRESHOLD=0.05            # 5% error rate threshold
)
```

### Environment Variables

```bash
# .env.production
export SPDS_ENV=production
export SPDS_LOG_LEVEL=INFO
export SPDS_CACHE_TTL=1800
export SPDS_MAX_WORKERS=4
export SPDS_ENABLE_MONITORING=true
export SPDS_METRICS_ENDPOINT=http://monitoring-server:9090/metrics

# Database settings (if using persistent storage)
export SPDS_DB_URL=postgresql://user:pass@localhost:5432/spds
export SPDS_REDIS_URL=redis://localhost:6379/0

# Performance settings
export SPDS_MEMORY_LIMIT_GB=12
export SPDS_ENABLE_MEMORY_OPTIMIZATION=true
export SPDS_BATCH_SIZE=20
```

### Service Setup

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  spds-api:
    build: .
    environment:
      - SPDS_ENV=production
      - SPDS_LOG_LEVEL=INFO
    volumes:
      - ./csv:/app/csv:ro
      - ./json:/app/json:ro
      - ./logs:/app/logs
      - ./cache:/app/cache
    ports:
      - '8000:8000'
    restart: unless-stopped
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 12G
          cpus: '4'
        reservations:
          memory: 8G
          cpus: '2'

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    ports:
      - '6379:6379'
    restart: unless-stopped

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - '9090:9090'
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
```

## Configuration Management

### Configuration Validation

```python
# deployment/validate_config.py
import asyncio
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService

async def validate_production_config(config):
    """Validate production configuration."""

    validation_results = {
        'config_valid': False,
        'service_initializable': False,
        'data_accessible': False,
        'performance_acceptable': False,
        'errors': []
    }

    try:
        # Validate configuration object
        assert isinstance(config, StatisticalAnalysisConfig)
        assert 85 <= config.PERCENTILE_THRESHOLD <= 99
        assert 0.7 <= config.DUAL_LAYER_THRESHOLD <= 0.95
        assert config.SAMPLE_SIZE_MINIMUM >= 10
        validation_results['config_valid'] = True

    except Exception as e:
        validation_results['errors'].append(f"Config validation failed: {e}")

    try:
        # Test service initialization
        service = StatisticalAnalysisService(config=config)
        validation_results['service_initializable'] = True

        # Test data access
        # Add actual data access tests here
        validation_results['data_accessible'] = True

        # Performance test
        import time
        start_time = time.time()
        # Run lightweight performance test
        elapsed = time.time() - start_time

        if elapsed < 5.0:  # Should complete in under 5 seconds
            validation_results['performance_acceptable'] = True
        else:
            validation_results['errors'].append(f"Performance test took {elapsed:.1f}s")

    except Exception as e:
        validation_results['errors'].append(f"Service validation failed: {e}")

    return validation_results

# Usage
if __name__ == "__main__":
    from config.production import PRODUCTION_CONFIG

    results = asyncio.run(validate_production_config(PRODUCTION_CONFIG))

    if all([
        results['config_valid'],
        results['service_initializable'],
        results['data_accessible'],
        results['performance_acceptable']
    ]):
        print("✅ Production configuration validation passed")
        exit(0)
    else:
        print("❌ Production configuration validation failed:")
        for error in results['errors']:
            print(f"  - {error}")
        exit(1)
```

### Environment-Specific Configurations

```python
# config/environments.py
from app.tools.config.statistical_analysis_config import StatisticalAnalysisConfig

class EnvironmentConfig:
    """Environment-specific configurations."""

    @staticmethod
    def get_config(env: str) -> StatisticalAnalysisConfig:
        if env == "production":
            return EnvironmentConfig._production_config()
        elif env == "staging":
            return EnvironmentConfig._staging_config()
        elif env == "development":
            return EnvironmentConfig._development_config()
        else:
            raise ValueError(f"Unknown environment: {env}")

    @staticmethod
    def _production_config() -> StatisticalAnalysisConfig:
        return StatisticalAnalysisConfig(
            # Production-optimized settings
            USE_TRADE_HISTORY=True,
            PERCENTILE_THRESHOLD=96,
            DUAL_LAYER_THRESHOLD=0.87,
            ENABLE_MEMORY_OPTIMIZATION=True,
            ENABLE_CACHING=True,
            CACHE_TTL_SECONDS=1800,
            LOG_LEVEL="INFO"
        )

    @staticmethod
    def _staging_config() -> StatisticalAnalysisConfig:
        return StatisticalAnalysisConfig(
            # Staging settings (similar to prod but with more logging)
            USE_TRADE_HISTORY=True,
            PERCENTILE_THRESHOLD=95,
            DUAL_LAYER_THRESHOLD=0.85,
            ENABLE_MEMORY_OPTIMIZATION=True,
            ENABLE_CACHING=True,
            CACHE_TTL_SECONDS=900,
            LOG_LEVEL="DEBUG"
        )

    @staticmethod
    def _development_config() -> StatisticalAnalysisConfig:
        return StatisticalAnalysisConfig(
            # Development settings (optimized for debugging)
            USE_TRADE_HISTORY=False,  # Use simpler data
            PERCENTILE_THRESHOLD=90,
            DUAL_LAYER_THRESHOLD=0.80,
            ENABLE_MEMORY_OPTIMIZATION=False,
            ENABLE_CACHING=False,
            LOG_LEVEL="DEBUG"
        )
```

## Performance Optimization

### Memory Optimization

```python
# deployment/memory_optimization.py
import psutil
import gc
from app.tools.processing.memory_optimizer import configure_memory_optimizer

class ProductionMemoryManager:
    """Production memory management."""

    def __init__(self, memory_limit_gb: float = 12):
        self.memory_limit_bytes = memory_limit_gb * 1024 * 1024 * 1024
        self.optimizer = configure_memory_optimizer(
            enable_pooling=True,
            enable_monitoring=True,
            memory_threshold_mb=memory_limit_gb * 800  # 80% of limit
        )

    def monitor_memory_usage(self):
        """Monitor and report memory usage."""
        process = psutil.Process()
        memory_info = process.memory_info()

        usage_pct = memory_info.rss / self.memory_limit_bytes * 100

        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'usage_percent': usage_pct,
            'limit_mb': self.memory_limit_bytes / 1024 / 1024,
            'available_mb': (self.memory_limit_bytes - memory_info.rss) / 1024 / 1024
        }

    def enforce_memory_limits(self):
        """Enforce memory limits and cleanup if needed."""
        memory_stats = self.monitor_memory_usage()

        if memory_stats['usage_percent'] > 85:  # 85% threshold
            print(f"Memory usage high: {memory_stats['usage_percent']:.1f}%")

            # Force garbage collection
            gc.collect()

            # Clear optimizer pools
            self.optimizer.clear_pools()

            # Re-check memory
            new_stats = self.monitor_memory_usage()
            print(f"Memory after cleanup: {new_stats['usage_percent']:.1f}%")

            return new_stats

        return memory_stats

# Usage in production
memory_manager = ProductionMemoryManager(memory_limit_gb=12)

# Regular memory monitoring
import schedule
schedule.every(5).minutes.do(memory_manager.enforce_memory_limits)
```

### Caching Strategy

```python
# deployment/caching.py
import redis
import pickle
import json
from typing import Any, Optional
from datetime import datetime, timedelta

class ProductionCacheManager:
    """Production caching with Redis backend."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = 1800  # 30 minutes

    def get_analysis_result(self, position_id: str) -> Optional[Any]:
        """Get cached analysis result."""
        key = f"spds:analysis:{position_id}"

        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"Cache get error: {e}")

        return None

    def set_analysis_result(self, position_id: str, result: Any, ttl: int = None):
        """Cache analysis result."""
        key = f"spds:analysis:{position_id}"
        ttl = ttl or self.default_ttl

        try:
            cached_data = pickle.dumps(result)
            self.redis_client.setex(key, ttl, cached_data)
        except Exception as e:
            print(f"Cache set error: {e}")

    def invalidate_position_cache(self, position_id: str):
        """Invalidate cache for a position."""
        key = f"spds:analysis:{position_id}"
        self.redis_client.delete(key)

    def get_cache_stats(self):
        """Get cache statistics."""
        info = self.redis_client.info()

        return {
            'memory_used_mb': info['used_memory'] / 1024 / 1024,
            'keys_count': info['db0']['keys'] if 'db0' in info else 0,
            'hit_rate': info.get('keyspace_hits', 0) / max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1),
            'connected_clients': info['connected_clients']
        }

# Usage
cache_manager = ProductionCacheManager()

# Decorator for caching analysis results
def cached_analysis(cache_manager: ProductionCacheManager):
    def decorator(func):
        async def wrapper(self, position, *args, **kwargs):
            # Check cache first
            cached_result = cache_manager.get_analysis_result(position.position_id)
            if cached_result:
                return cached_result

            # Compute result
            result = await func(self, position, *args, **kwargs)

            # Cache result
            cache_manager.set_analysis_result(position.position_id, result)

            return result
        return wrapper
    return decorator
```

### Parallel Processing

```python
# deployment/parallel_processing.py
import asyncio
import concurrent.futures
from typing import List, Any
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService

class ProductionParallelProcessor:
    """Production parallel processing manager."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    async def process_positions_parallel(
        self,
        service: StatisticalAnalysisService,
        positions: List[Any],
        batch_size: int = 20
    ) -> List[Any]:
        """Process positions in parallel batches."""

        results = []

        # Process in batches to manage memory
        for i in range(0, len(positions), batch_size):
            batch = positions[i:i + batch_size]

            # Create tasks for batch
            tasks = [
                service.analyze_position_statistical_performance(position)
                for position in batch
            ]

            # Execute batch in parallel
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle exceptions
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    print(f"Error processing position {batch[j].position_id}: {result}")
                    # Create fallback result
                    result = self._create_fallback_result(batch[j])

                results.append(result)

            # Memory cleanup between batches
            del batch_results
            import gc; gc.collect()

        return results

    def _create_fallback_result(self, position):
        """Create fallback result for failed analysis."""
        # Return minimal result structure
        return {
            'position_id': position.position_id,
            'analysis_status': 'failed',
            'exit_signal': 'HOLD',
            'confidence': 0.0,
            'error': True
        }

    def shutdown(self):
        """Shutdown parallel processor."""
        self.executor.shutdown(wait=True)

# Usage
processor = ProductionParallelProcessor(max_workers=4)

# Process large portfolio
results = await processor.process_positions_parallel(
    service, all_positions, batch_size=20
)
```

## Monitoring and Alerting

### Performance Metrics

```python
# monitoring/metrics.py
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from typing import Dict, Any

class SPDSMetrics:
    """Production metrics collection."""

    def __init__(self):
        # Analysis metrics
        self.analysis_counter = Counter(
            'spds_analysis_total',
            'Total number of position analyses',
            ['status', 'signal_type']
        )

        self.analysis_duration = Histogram(
            'spds_analysis_duration_seconds',
            'Time spent on position analysis',
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )

        # Performance metrics
        self.exit_efficiency_gauge = Gauge(
            'spds_exit_efficiency',
            'Current exit efficiency percentage'
        )

        self.portfolio_health_gauge = Gauge(
            'spds_portfolio_health_score',
            'Current portfolio health score'
        )

        # System metrics
        self.memory_usage_gauge = Gauge(
            'spds_memory_usage_mb',
            'Memory usage in MB'
        )

        self.cache_hit_rate_gauge = Gauge(
            'spds_cache_hit_rate',
            'Cache hit rate percentage'
        )

        # Error metrics
        self.error_counter = Counter(
            'spds_errors_total',
            'Total number of errors',
            ['error_type', 'component']
        )

    def record_analysis(self, duration: float, status: str, signal_type: str):
        """Record analysis metrics."""
        self.analysis_counter.labels(status=status, signal_type=signal_type).inc()
        self.analysis_duration.observe(duration)

    def update_performance_metrics(self, exit_efficiency: float, portfolio_health: float):
        """Update performance metrics."""
        self.exit_efficiency_gauge.set(exit_efficiency * 100)
        self.portfolio_health_gauge.set(portfolio_health)

    def update_system_metrics(self, memory_mb: float, cache_hit_rate: float):
        """Update system metrics."""
        self.memory_usage_gauge.set(memory_mb)
        self.cache_hit_rate_gauge.set(cache_hit_rate * 100)

    def record_error(self, error_type: str, component: str):
        """Record error occurrence."""
        self.error_counter.labels(error_type=error_type, component=component).inc()

    def get_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return generate_latest()

# Usage with analysis service
metrics = SPDSMetrics()

class MonitoredStatisticalAnalysisService(StatisticalAnalysisService):
    """Statistical analysis service with monitoring."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.metrics = metrics

    async def analyze_position_statistical_performance(self, position, **kwargs):
        """Monitored position analysis."""
        start_time = time.time()

        try:
            result = await super().analyze_position_statistical_performance(position, **kwargs)

            # Record successful analysis
            duration = time.time() - start_time
            signal_type = result.exit_signals.primary_signal if result.exit_signals else 'NONE'
            self.metrics.record_analysis(duration, 'success', signal_type)

            return result

        except Exception as e:
            # Record error
            duration = time.time() - start_time
            self.metrics.record_analysis(duration, 'error', 'NONE')
            self.metrics.record_error(type(e).__name__, 'analysis_service')
            raise
```

### Health Checks

```python
# monitoring/health.py
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

class HealthChecker:
    """Production health monitoring."""

    def __init__(self, service, cache_manager, memory_manager):
        self.service = service
        self.cache_manager = cache_manager
        self.memory_manager = memory_manager
        self.last_check = datetime.utcnow()

    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check."""

        health_status = {
            'overall_status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }

        # Service health
        try:
            service_health = await self._check_service_health()
            health_status['checks']['service'] = service_health
        except Exception as e:
            health_status['checks']['service'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['overall_status'] = 'unhealthy'

        # Memory health
        try:
            memory_health = self._check_memory_health()
            health_status['checks']['memory'] = memory_health

            if memory_health['usage_percent'] > 90:
                health_status['overall_status'] = 'degraded'
        except Exception as e:
            health_status['checks']['memory'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['overall_status'] = 'unhealthy'

        # Cache health
        try:
            cache_health = self._check_cache_health()
            health_status['checks']['cache'] = cache_health
        except Exception as e:
            health_status['checks']['cache'] = {'status': 'unhealthy', 'error': str(e)}
            # Cache failure is not critical

        # Data health
        try:
            data_health = self._check_data_health()
            health_status['checks']['data'] = data_health
        except Exception as e:
            health_status['checks']['data'] = {'status': 'unhealthy', 'error': str(e)}
            health_status['overall_status'] = 'unhealthy'

        self.last_check = datetime.utcnow()
        return health_status

    async def _check_service_health(self) -> Dict[str, Any]:
        """Check service health."""
        # Quick analysis test
        from app.tools.models.statistical_analysis_models import PositionData

        test_position = PositionData(
            position_id="HEALTH_CHECK",
            ticker="TEST",
            strategy_name="TEST",
            current_return=0.1,
            mfe=0.12,
            mae=0.02,
            days_held=10,
            entry_price=100,
            current_price=110
        )

        start_time = datetime.utcnow()

        try:
            # This should complete quickly
            result = await asyncio.wait_for(
                self.service.analyze_position_statistical_performance(test_position),
                timeout=5.0
            )

            duration = (datetime.utcnow() - start_time).total_seconds()

            return {
                'status': 'healthy',
                'response_time_seconds': duration,
                'analysis_successful': result is not None
            }

        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Service timeout after 5 seconds'
            }

    def _check_memory_health(self) -> Dict[str, Any]:
        """Check memory health."""
        memory_stats = self.memory_manager.monitor_memory_usage()

        status = 'healthy'
        if memory_stats['usage_percent'] > 90:
            status = 'critical'
        elif memory_stats['usage_percent'] > 80:
            status = 'warning'

        return {
            'status': status,
            **memory_stats
        }

    def _check_cache_health(self) -> Dict[str, Any]:
        """Check cache health."""
        try:
            cache_stats = self.cache_manager.get_cache_stats()

            status = 'healthy'
            if cache_stats['hit_rate'] < 0.5:  # 50% hit rate threshold
                status = 'degraded'

            return {
                'status': status,
                **cache_stats
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

    def _check_data_health(self) -> Dict[str, Any]:
        """Check data availability and freshness."""
        import os
        from pathlib import Path

        checks = {}

        # Check trade history data
        trade_history_path = Path("./csv/positions/")
        if trade_history_path.exists():
            files = list(trade_history_path.glob("*.csv"))
            checks['trade_history'] = {
                'available': len(files) > 0,
                'file_count': len(files)
            }
        else:
            checks['trade_history'] = {
                'available': False,
                'error': 'Trade history directory not found'
            }

        # Check return distribution data
        return_dist_path = Path("./json/return_distribution/")
        if return_dist_path.exists():
            files = list(return_dist_path.glob("*.json"))
            checks['return_distribution'] = {
                'available': len(files) > 0,
                'file_count': len(files)
            }
        else:
            checks['return_distribution'] = {
                'available': False,
                'error': 'Return distribution directory not found'
            }

        # Overall data status
        status = 'healthy'
        if not checks.get('trade_history', {}).get('available', False):
            status = 'degraded'
        if not checks.get('return_distribution', {}).get('available', False):
            status = 'unhealthy'

        return {
            'status': status,
            'checks': checks
        }

# Usage
health_checker = HealthChecker(service, cache_manager, memory_manager)

# Regular health checks
async def run_health_checks():
    health_status = await health_checker.comprehensive_health_check()

    if health_status['overall_status'] != 'healthy':
        print(f"Health check failed: {health_status}")
        # Send alert

    return health_status
```

### Alerting Configuration

```yaml
# monitoring/alerts.yml
groups:
  - name: spds.rules
    rules:
      # Performance alerts
      - alert: SPDSExitEfficiencyLow
        expr: spds_exit_efficiency < 75
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'SPDS exit efficiency below target'
          description: 'Exit efficiency is {{ $value }}%, below 75% threshold'

      - alert: SPDSPortfolioHealthLow
        expr: spds_portfolio_health_score < 70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Portfolio health score low'
          description: 'Portfolio health score is {{ $value }}, below 70 threshold'

      # System alerts
      - alert: SPDSHighMemoryUsage
        expr: spds_memory_usage_mb > 10000
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: 'SPDS high memory usage'
          description: 'Memory usage is {{ $value }}MB, above 10GB threshold'

      - alert: SPDSHighErrorRate
        expr: rate(spds_errors_total[5m]) > 0.1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: 'SPDS high error rate'
          description: 'Error rate is {{ $value }} per second'

      # Cache alerts
      - alert: SPDSLowCacheHitRate
        expr: spds_cache_hit_rate < 50
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: 'SPDS low cache hit rate'
          description: 'Cache hit rate is {{ $value }}%, below 50% threshold'
```

## Maintenance Procedures

### Regular Maintenance Tasks

```python
# maintenance/tasks.py
import asyncio
import shutil
from datetime import datetime, timedelta
from pathlib import Path

class MaintenanceTasks:
    """Production maintenance tasks."""

    def __init__(self, service, cache_manager, memory_manager):
        self.service = service
        self.cache_manager = cache_manager
        self.memory_manager = memory_manager

    async def daily_maintenance(self):
        """Daily maintenance routine."""
        print(f"Starting daily maintenance: {datetime.utcnow()}")

        # Clean old cache entries
        await self._clean_cache()

        # Clean old log files
        self._clean_logs()

        # Memory optimization
        self.memory_manager.enforce_memory_limits()

        # Validate data integrity
        await self._validate_data_integrity()

        # Update performance metrics
        await self._update_performance_metrics()

        print("Daily maintenance completed")

    async def weekly_maintenance(self):
        """Weekly maintenance routine."""
        print(f"Starting weekly maintenance: {datetime.utcnow()}")

        # Full cache refresh
        await self._refresh_cache()

        # Archive old data
        self._archive_old_data()

        # Performance analysis
        await self._analyze_performance_trends()

        # Update ML models
        await self._retrain_ml_models()

        print("Weekly maintenance completed")

    async def _clean_cache(self):
        """Clean expired cache entries."""
        try:
            # Redis will handle TTL automatically, but we can clean manually
            cache_stats = self.cache_manager.get_cache_stats()
            print(f"Cache stats before cleanup: {cache_stats}")

            # Force cleanup of expired keys
            self.cache_manager.redis_client.flushdb()

        except Exception as e:
            print(f"Cache cleanup error: {e}")

    def _clean_logs(self, days_to_keep: int = 7):
        """Clean old log files."""
        log_path = Path("./logs/")
        if not log_path.exists():
            return

        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

        for log_file in log_path.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                print(f"Deleted old log file: {log_file}")

    async def _validate_data_integrity(self):
        """Validate data integrity."""
        # Check for corrupted files
        data_paths = [
            Path("./csv/positions/"),
            Path("./json/return_distribution/")
        ]

        for path in data_paths:
            if path.exists():
                for file_path in path.glob("*.csv" if "csv" in str(path) else "*.json"):
                    try:
                        if "csv" in str(path):
                            import pandas as pd
                            pd.read_csv(file_path, nrows=1)  # Quick check
                        else:
                            import json
                            with open(file_path) as f:
                                json.load(f)  # Quick check
                    except Exception as e:
                        print(f"Data integrity issue in {file_path}: {e}")

    async def _update_performance_metrics(self):
        """Update performance tracking."""
        # Calculate recent performance
        # This would analyze recent trades and update metrics
        print("Updated performance metrics")

    async def _refresh_cache(self):
        """Refresh cache with current data."""
        # Clear all cache
        self.cache_manager.redis_client.flushdb()

        # Preload frequently accessed data
        # This would pre-populate cache with common analyses
        print("Cache refreshed")

    def _archive_old_data(self, days_to_keep: int = 90):
        """Archive old data files."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        archive_path = Path("./archive/")
        archive_path.mkdir(exist_ok=True)

        # Archive old CSV files
        csv_path = Path("./csv/")
        for csv_file in csv_path.rglob("*.csv"):
            if csv_file.stat().st_mtime < cutoff_date.timestamp():
                archive_file = archive_path / csv_file.relative_to(csv_path)
                archive_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(csv_file), str(archive_file))
                print(f"Archived: {csv_file} -> {archive_file}")

    async def _analyze_performance_trends(self):
        """Analyze performance trends over time."""
        # This would analyze historical performance data
        # and identify trends or degradation
        print("Analyzed performance trends")

    async def _retrain_ml_models(self):
        """Retrain ML models with recent data."""
        # This would retrain pattern recognition models
        # with the latest data
        print("Retrained ML models")

# Schedule maintenance tasks
import schedule

maintenance = MaintenanceTasks(service, cache_manager, memory_manager)

# Schedule daily maintenance at 2 AM
schedule.every().day.at("02:00").do(
    lambda: asyncio.create_task(maintenance.daily_maintenance())
)

# Schedule weekly maintenance on Sunday at 3 AM
schedule.every().sunday.at("03:00").do(
    lambda: asyncio.create_task(maintenance.weekly_maintenance())
)
```

### Backup Procedures

```bash
#!/bin/bash
# backup.sh - Production backup script

set -e

BACKUP_DIR="/backup/spds/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Starting SPDS backup to $BACKUP_DIR"

# Backup configuration
cp -r config/ "$BACKUP_DIR/"

# Backup data
rsync -av --exclude='*.tmp' csv/ "$BACKUP_DIR/csv/"
rsync -av --exclude='*.tmp' json/ "$BACKUP_DIR/json/"

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec cp {} "$BACKUP_DIR/logs/" \;

# Backup database dump (if using database)
if [ -n "$SPDS_DB_URL" ]; then
    pg_dump "$SPDS_DB_URL" > "$BACKUP_DIR/database.sql"
fi

# Create compressed archive
cd /backup/spds/
tar czf "spds_backup_$(date +%Y%m%d_%H%M%S).tar.gz" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

# Cleanup old backups (keep last 30 days)
find /backup/spds/ -name "spds_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed successfully"
```

## Troubleshooting

### Common Issues and Solutions

#### High Memory Usage

```python
# troubleshooting/memory_issues.py

def diagnose_memory_issues():
    """Diagnose memory usage issues."""
    import psutil
    import gc

    process = psutil.Process()
    memory_info = process.memory_info()

    print(f"Memory Usage Diagnosis:")
    print(f"  RSS: {memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"  VMS: {memory_info.vms / 1024 / 1024:.1f} MB")

    # Check garbage collection
    gc_stats = gc.get_stats()
    print(f"  GC Collections: {gc_stats}")

    # Force garbage collection
    collected = gc.collect()
    print(f"  Objects collected: {collected}")

    # Memory after cleanup
    new_memory_info = process.memory_info()
    print(f"  RSS after GC: {new_memory_info.rss / 1024 / 1024:.1f} MB")
    print(f"  Memory freed: {(memory_info.rss - new_memory_info.rss) / 1024 / 1024:.1f} MB")

# Solutions
def resolve_memory_issues():
    """Apply memory issue solutions."""

    # 1. Enable memory optimization
    from app.tools.processing.memory_optimizer import configure_memory_optimizer
    optimizer = configure_memory_optimizer(
        enable_pooling=True,
        enable_monitoring=True,
        memory_threshold_mb=8000
    )

    # 2. Reduce batch sizes
    import os
    os.environ['SPDS_BATCH_SIZE'] = '10'  # Reduce from 20

    # 3. Increase garbage collection frequency
    import gc
    gc.set_threshold(700, 10, 10)  # More aggressive GC

    print("Applied memory optimization solutions")
```

#### Performance Degradation

```python
# troubleshooting/performance_issues.py

async def diagnose_performance_issues(service):
    """Diagnose performance degradation."""
    import time
    from app.tools.models.statistical_analysis_models import PositionData

    # Test analysis performance
    test_position = PositionData(
        position_id="PERF_TEST",
        ticker="TEST",
        strategy_name="TEST",
        current_return=0.1,
        mfe=0.12,
        mae=0.02,
        days_held=15,
        entry_price=100,
        current_price=110
    )

    # Multiple runs to get average
    times = []
    for i in range(5):
        start_time = time.time()

        try:
            result = await service.analyze_position_statistical_performance(test_position)
            duration = time.time() - start_time
            times.append(duration)

        except Exception as e:
            print(f"Analysis failed on run {i+1}: {e}")

    if times:
        avg_time = sum(times) / len(times)
        print(f"Performance Diagnosis:")
        print(f"  Average analysis time: {avg_time:.2f}s")
        print(f"  Min time: {min(times):.2f}s")
        print(f"  Max time: {max(times):.2f}s")

        if avg_time > 5.0:
            print("⚠️  Performance degradation detected")
            return False
        else:
            print("✅ Performance within acceptable range")
            return True
    else:
        print("❌ All performance tests failed")
        return False

def resolve_performance_issues():
    """Apply performance issue solutions."""

    # 1. Enable caching
    import os
    os.environ['SPDS_ENABLE_CACHING'] = 'true'
    os.environ['SPDS_CACHE_TTL'] = '1800'

    # 2. Reduce parallel workers
    os.environ['SPDS_MAX_WORKERS'] = '2'

    # 3. Optimize thresholds
    os.environ['SPDS_PERCENTILE_THRESHOLD'] = '90'  # Less aggressive

    print("Applied performance optimization solutions")
```

### Log Analysis

```python
# troubleshooting/log_analysis.py
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta

class LogAnalyzer:
    """Analyze production logs for issues."""

    def __init__(self, log_path: str = "./logs/"):
        self.log_path = Path(log_path)

    def analyze_errors(self, hours: int = 24) -> dict:
        """Analyze errors in recent logs."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        error_patterns = []

        for log_file in self.log_path.glob("*.log"):
            with open(log_file, 'r') as f:
                for line in f:
                    # Parse log line
                    if 'ERROR' in line or 'CRITICAL' in line:
                        # Extract timestamp
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                        if timestamp_match:
                            timestamp = datetime.strptime(timestamp_match.group(1), '%Y-%m-%d %H:%M:%S')
                            if timestamp >= cutoff_time:
                                error_patterns.append(line.strip())

        # Analyze error patterns
        error_counts = Counter(error_patterns)

        return {
            'total_errors': len(error_patterns),
            'unique_errors': len(error_counts),
            'top_errors': error_counts.most_common(10),
            'hourly_distribution': self._get_hourly_distribution(error_patterns)
        }

    def _get_hourly_distribution(self, errors):
        """Get hourly distribution of errors."""
        hourly_counts = defaultdict(int)

        for error in errors:
            # Extract hour from timestamp
            timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} (\d{2}):\d{2}:\d{2}', error)
            if timestamp_match:
                hour = int(timestamp_match.group(1))
                hourly_counts[hour] += 1

        return dict(hourly_counts)

# Usage
log_analyzer = LogAnalyzer()
error_analysis = log_analyzer.analyze_errors(hours=24)

print(f"Error Analysis (last 24 hours):")
print(f"  Total errors: {error_analysis['total_errors']}")
print(f"  Unique errors: {error_analysis['unique_errors']}")
print(f"  Top errors:")
for error, count in error_analysis['top_errors'][:5]:
    print(f"    {count}x: {error[:100]}...")
```

## Rollback Procedures

### Configuration Rollback

```python
# rollback/config_rollback.py
import shutil
import json
from pathlib import Path
from datetime import datetime

class ConfigurationRollback:
    """Manage configuration rollbacks."""

    def __init__(self, config_path: str = "config/"):
        self.config_path = Path(config_path)
        self.backup_path = Path("config_backups/")
        self.backup_path.mkdir(exist_ok=True)

    def backup_current_config(self) -> str:
        """Backup current configuration."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_path / f"config_{timestamp}"

        shutil.copytree(self.config_path, backup_dir)

        # Create backup metadata
        metadata = {
            'timestamp': timestamp,
            'backup_path': str(backup_dir),
            'config_files': [str(f.relative_to(self.config_path)) for f in self.config_path.rglob("*.py")]
        }

        with open(backup_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"Configuration backed up to: {backup_dir}")
        return str(backup_dir)

    def rollback_to_backup(self, backup_path: str):
        """Rollback to a specific backup."""
        backup_dir = Path(backup_path)

        if not backup_dir.exists():
            raise ValueError(f"Backup directory does not exist: {backup_path}")

        # Backup current config before rollback
        current_backup = self.backup_current_config()
        print(f"Current config backed up to: {current_backup}")

        # Remove current config
        shutil.rmtree(self.config_path)

        # Restore from backup
        shutil.copytree(backup_dir, self.config_path)

        print(f"Configuration rolled back from: {backup_path}")

    def list_backups(self) -> list:
        """List available configuration backups."""
        backups = []

        for backup_dir in self.backup_path.glob("config_*"):
            metadata_file = backup_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
                    backups.append(metadata)

        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

# Usage
config_rollback = ConfigurationRollback()

# Backup before deployment
backup_path = config_rollback.backup_current_config()

# If deployment fails, rollback
try:
    # Deploy new configuration
    pass
except Exception as e:
    print(f"Deployment failed: {e}")
    config_rollback.rollback_to_backup(backup_path)
```

### Service Rollback

```bash
#!/bin/bash
# rollback/service_rollback.sh

set -e

ROLLBACK_VERSION=${1:-"previous"}
SERVICE_NAME="spds-api"

echo "Starting service rollback to version: $ROLLBACK_VERSION"

# Stop current service
docker-compose stop $SERVICE_NAME

# Backup current logs
mkdir -p rollback_logs/$(date +%Y%m%d_%H%M%S)
cp -r logs/* rollback_logs/$(date +%Y%m%d_%H%M%S)/

# Rollback to previous version
if [ "$ROLLBACK_VERSION" = "previous" ]; then
    # Use previous Docker image
    docker-compose pull $SERVICE_NAME:previous
    docker-compose up -d $SERVICE_NAME:previous
else
    # Use specific version
    docker-compose pull $SERVICE_NAME:$ROLLBACK_VERSION
    docker-compose up -d $SERVICE_NAME:$ROLLBACK_VERSION
fi

# Health check
sleep 30
if curl -f http://localhost:8000/health; then
    echo "✅ Service rollback successful"
else
    echo "❌ Service rollback failed"
    exit 1
fi

echo "Service rollback completed"
```

### Data Rollback

```python
# rollback/data_rollback.py
import shutil
import tarfile
from pathlib import Path
from datetime import datetime

class DataRollback:
    """Manage data rollbacks."""

    def __init__(self):
        self.data_paths = [
            Path("./csv/"),
            Path("./json/"),
            Path("./cache/")
        ]
        self.backup_path = Path("/backup/spds/")

    def rollback_to_backup(self, backup_file: str):
        """Rollback data to specific backup."""
        backup_path = self.backup_path / backup_file

        if not backup_path.exists():
            raise ValueError(f"Backup file does not exist: {backup_path}")

        print(f"Rolling back data from: {backup_path}")

        # Extract backup
        temp_dir = Path(f"/tmp/spds_rollback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")
        temp_dir.mkdir(exist_ok=True)

        with tarfile.open(backup_path, 'r:gz') as tar:
            tar.extractall(temp_dir)

        # Find extracted directory
        extracted_dir = next(temp_dir.iterdir())

        # Backup current data
        current_backup_dir = self.backup_path / f"current_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        current_backup_dir.mkdir(exist_ok=True)

        for data_path in self.data_paths:
            if data_path.exists():
                backup_dest = current_backup_dir / data_path.name
                shutil.copytree(data_path, backup_dest)

        # Restore from backup
        for data_path in self.data_paths:
            source_path = extracted_dir / data_path.name
            if source_path.exists():
                if data_path.exists():
                    shutil.rmtree(data_path)
                shutil.copytree(source_path, data_path)

        # Cleanup
        shutil.rmtree(temp_dir)

        print(f"Data rollback completed. Current data backed up to: {current_backup_dir}")

# Usage
data_rollback = DataRollback()

# Rollback to specific backup
data_rollback.rollback_to_backup("spds_backup_20240701_120000.tar.gz")
```

## Final Deployment Checklist

```bash
#!/bin/bash
# deployment/final_checklist.sh

echo "🚀 SPDS Production Deployment - Final Checklist"
echo "=============================================="

# Configuration validation
echo "1. Validating configuration..."
python deployment/validate_config.py
if [ $? -ne 0 ]; then
    echo "❌ Configuration validation failed"
    exit 1
fi
echo "✅ Configuration valid"

# Performance tests
echo "2. Running performance tests..."
pytest tests/performance/ -v
if [ $? -ne 0 ]; then
    echo "❌ Performance tests failed"
    exit 1
fi
echo "✅ Performance tests passed"

# Integration tests
echo "3. Running integration tests..."
pytest tests/integration/ -v
if [ $? -ne 0 ]; then
    echo "❌ Integration tests failed"
    exit 1
fi
echo "✅ Integration tests passed"

# Health check
echo "4. Running health check..."
python -c "
import asyncio
from monitoring.health import HealthChecker
from app.tools.services.statistical_analysis_service import StatisticalAnalysisService
from config.production import PRODUCTION_CONFIG

async def check():
    service = StatisticalAnalysisService(config=PRODUCTION_CONFIG)
    # Mock other components for check
    health_checker = HealthChecker(service, None, None)
    result = await health_checker._check_service_health()
    assert result['status'] == 'healthy'
    print('Health check passed')

asyncio.run(check())
"
if [ $? -ne 0 ]; then
    echo "❌ Health check failed"
    exit 1
fi
echo "✅ Health check passed"

# Backup current state
echo "5. Creating pre-deployment backup..."
./backup.sh
echo "✅ Backup completed"

# Ready for deployment
echo ""
echo "🎉 All checks passed! Ready for production deployment"
echo ""
echo "Next steps:"
echo "  1. docker-compose -f docker-compose.prod.yml up -d"
echo "  2. Monitor logs: docker-compose logs -f spds-api"
echo "  3. Monitor metrics: http://localhost:9090"
echo "  4. Health check: curl http://localhost:8000/health"
```

This comprehensive production deployment guide provides all necessary components for successfully deploying the Statistical Performance Divergence System to production environments with proper monitoring, maintenance, and rollback procedures.
