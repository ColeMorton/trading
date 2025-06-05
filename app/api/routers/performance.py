"""
Performance Monitoring API Router

This module provides API endpoints for accessing performance metrics, optimization insights,
and strategy execution analytics.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.utils.performance_monitoring import (
    get_performance_monitor,
    get_performance_report,
)
from app.tools.performance_tracker import get_strategy_performance_tracker

router = APIRouter(prefix="/performance", tags=["performance"])


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""

    operation_name: str
    duration: Optional[float] = None
    memory_before_mb: Optional[float] = None
    memory_after_mb: Optional[float] = None
    memory_peak_mb: Optional[float] = None
    throughput_items: Optional[int] = None
    throughput_rate: Optional[float] = None
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OptimizationInsightResponse(BaseModel):
    """Response model for optimization insights."""

    execution_id: str
    type: str
    severity: str
    message: str
    recommendation: str
    timestamp: str


class StrategyPerformanceSummaryResponse(BaseModel):
    """Response model for strategy performance summary."""

    period_hours: int
    execution_count: int
    total_portfolios_processed: int
    total_execution_time: float
    average_throughput: float
    concurrent_execution_rate: float
    performance_insights_count: int
    timestamp: str


class OperationStatsResponse(BaseModel):
    """Response model for operation statistics."""

    operation_name: str
    count: int
    total_duration: float
    avg_duration: float
    min_duration: float
    max_duration: float
    total_throughput: float
    avg_throughput: float


@router.get("/metrics", response_model=List[PerformanceMetricsResponse])
async def get_performance_metrics(
    operation_name: Optional[str] = Query(None, description="Filter by operation name"),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of metrics to return"
    ),
):
    """
    Get recent performance metrics.

    Args:
        operation_name: Optional filter by operation name
        limit: Maximum number of metrics to return

    Returns:
        List of performance metrics
    """
    try:
        monitor = get_performance_monitor()
        metrics = monitor.get_recent_metrics(operation_name=operation_name, limit=limit)

        return [
            PerformanceMetricsResponse(
                operation_name=m.operation_name,
                duration=m.duration,
                memory_before_mb=m.memory_before,
                memory_after_mb=m.memory_after,
                memory_peak_mb=m.memory_peak,
                throughput_items=m.throughput_items,
                throughput_rate=m.throughput_rate,
                timestamp=datetime.fromtimestamp(m.start_time).isoformat(),
                metadata=m.metadata,
            )
            for m in metrics
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve performance metrics: {str(e)}"
        )


@router.get("/stats", response_model=Dict[str, OperationStatsResponse])
async def get_operation_stats(
    operation_name: Optional[str] = Query(
        None, description="Get stats for specific operation"
    )
):
    """
    Get aggregated operation statistics.

    Args:
        operation_name: Optional specific operation name

    Returns:
        Dictionary of operation statistics
    """
    try:
        monitor = get_performance_monitor()
        stats = monitor.get_operation_stats(operation_name=operation_name)

        if operation_name and operation_name in stats:
            # Return single operation stats
            stat_data = stats[operation_name]
            return {
                operation_name: OperationStatsResponse(
                    operation_name=operation_name, **stat_data
                )
            }
        else:
            # Return all operation stats
            return {
                name: OperationStatsResponse(operation_name=name, **stat_data)
                for name, stat_data in stats.items()
            }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve operation stats: {str(e)}"
        )


@router.get("/insights", response_model=List[OptimizationInsightResponse])
async def get_optimization_insights(
    execution_id: Optional[str] = Query(None, description="Filter by execution ID"),
    limit: int = Query(
        10, ge=1, le=100, description="Maximum number of insights to return"
    ),
):
    """
    Get optimization insights for strategy executions.

    Args:
        execution_id: Optional filter by execution ID
        limit: Maximum number of insights to return

    Returns:
        List of optimization insights
    """
    try:
        tracker = get_strategy_performance_tracker()
        insights = tracker.get_optimization_insights(
            execution_id=execution_id, limit=limit
        )

        return [
            OptimizationInsightResponse(
                execution_id=insight["execution_id"],
                type=insight["type"],
                severity=insight["severity"],
                message=insight["message"],
                recommendation=insight["recommendation"],
                timestamp=insight["timestamp"],
            )
            for insight in insights
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve optimization insights: {str(e)}",
        )


@router.get("/strategy-summary", response_model=StrategyPerformanceSummaryResponse)
async def get_strategy_performance_summary(
    hours: int = Query(
        24, ge=1, le=168, description="Time period in hours (max 7 days)"
    )
):
    """
    Get strategy performance summary for the specified time period.

    Args:
        hours: Time period in hours

    Returns:
        Strategy performance summary
    """
    try:
        tracker = get_strategy_performance_tracker()
        summary = tracker.get_performance_summary(hours=hours)

        return StrategyPerformanceSummaryResponse(**summary)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve strategy performance summary: {str(e)}",
        )


@router.get("/report")
async def get_comprehensive_performance_report():
    """
    Get a comprehensive performance report including all metrics and insights.

    Returns:
        Comprehensive performance report
    """
    try:
        # Get overall performance report
        performance_report = get_performance_report()

        # Get strategy-specific summary
        tracker = get_strategy_performance_tracker()
        strategy_summary = tracker.get_performance_summary(hours=24)
        recent_insights = tracker.get_optimization_insights(limit=20)

        return {
            "generated_at": datetime.now().isoformat(),
            "performance_overview": performance_report,
            "strategy_performance": strategy_summary,
            "recent_insights": recent_insights,
            "monitoring_status": {
                "total_operations": performance_report.get("total_operations", 0),
                "monitoring_enabled": performance_report.get(
                    "monitoring_enabled", False
                ),
                "insights_available": len(recent_insights),
            },
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate performance report: {str(e)}"
        )


@router.delete("/metrics")
async def clear_performance_history():
    """
    Clear all stored performance metrics history.

    Returns:
        Success message
    """
    try:
        monitor = get_performance_monitor()
        monitor.clear_history()

        return {"message": "Performance history cleared successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to clear performance history: {str(e)}"
        )


@router.get("/health")
async def performance_monitoring_health():
    """
    Check the health status of performance monitoring.

    Returns:
        Health status information
    """
    try:
        monitor = get_performance_monitor()
        tracker = get_strategy_performance_tracker()

        # Get basic stats
        stats = monitor.get_operation_stats()
        recent_metrics = monitor.get_recent_metrics(limit=10)
        recent_insights = tracker.get_optimization_insights(limit=5)

        return {
            "status": "healthy",
            "monitoring_enabled": monitor.enabled,
            "total_operation_types": len(stats),
            "recent_metrics_count": len(recent_metrics),
            "recent_insights_count": len(recent_insights),
            "memory_usage_tracking": True,
            "throughput_tracking": True,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
