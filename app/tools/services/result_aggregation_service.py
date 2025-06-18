"""
Result Aggregation Service

This module handles result aggregation, response formatting, and task status management.
It provides utilities for creating responses and managing asynchronous task execution.
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.api.models.strategy_analysis import (
    MACrossAsyncResponse,
    MACrossResponse,
    PortfolioMetrics,
    StrategyAnalysisRequest,
)
from app.api.services.script_executor import task_status
from app.api.utils.monitoring import get_metrics_collector
from app.core.interfaces import (
    LoggingInterface,
    MonitoringInterface,
    ProgressTrackerInterface,
)


class ResultAggregationServiceError(Exception):
    """Exception raised by ResultAggregationService."""

    pass


class ResultAggregationService:
    """
    Handles result aggregation and response formatting.

    This service is responsible for:
    - Creating structured responses from analysis results
    - Managing asynchronous task status
    - Aggregating metrics and performance data
    - Task cleanup and lifecycle management
    """

    def __init__(
        self,
        logger: LoggingInterface,
        metrics: MonitoringInterface,
        progress_tracker: Optional[ProgressTrackerInterface] = None,
    ):
        """Initialize the result aggregation service."""
        self.logger = logger
        self.metrics = metrics
        self.progress_tracker = progress_tracker

    def create_analysis_response(
        self,
        request: StrategyAnalysisRequest,
        portfolio_metrics: List[PortfolioMetrics],
        deduplicated_portfolios: List[Dict[str, Any]],
        export_paths: Dict[str, List[str]],
        execution_time: float,
        log,
    ) -> MACrossResponse:
        """
        Create a structured response from analysis results.

        Args:
            request: Original analysis request
            portfolio_metrics: List of portfolio metrics
            deduplicated_portfolios: Deduplicated portfolio dictionaries
            export_paths: Export file paths
            execution_time: Analysis execution time
            log: Logging function

        Returns:
            MACrossResponse with structured results
        """
        try:
            # Log portfolio serialization details for debugging
            response_dict_default = {
                "portfolios": [p.model_dump() for p in portfolio_metrics]
            }
            response_dict_no_exclude = {
                "portfolios": [
                    p.model_dump(exclude_none=False) for p in portfolio_metrics
                ]
            }

            # Debug logging for serialization comparison
            if (
                response_dict_default.get("portfolios")
                and len(response_dict_default["portfolios"]) > 0
            ):
                first_serialized_default = response_dict_default["portfolios"][0]
                first_serialized_no_exclude = response_dict_no_exclude["portfolios"][0]

                log(
                    f"DEBUG: Default serialization keys: {len(first_serialized_default.keys())}",
                    "info",
                )
                log(
                    f"DEBUG: Default metric_type: '{first_serialized_default.get('metric_type', 'MISSING')}'",
                    "info",
                )
                log(
                    f"DEBUG: No-exclude serialization keys: {len(first_serialized_no_exclude.keys())}",
                    "info",
                )
                log(
                    f"DEBUG: No-exclude metric_type: '{first_serialized_no_exclude.get('metric_type', 'MISSING')}'",
                    "info",
                )

            # Create response
            import uuid

            strategy_type_str = (
                request.strategy_type.value
                if hasattr(request.strategy_type, "value")
                else str(request.strategy_type)
            )

            response = MACrossResponse(
                status="success",
                request_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                ticker=request.ticker,
                strategy_types=[strategy_type_str],
                portfolios=portfolio_metrics,
                portfolio_exports=export_paths,
                total_portfolios_analyzed=len(portfolio_metrics),
                total_portfolios_filtered=len(deduplicated_portfolios),
                execution_time=execution_time,
            )

            log(f"Created response with {len(portfolio_metrics)} portfolio metrics")
            return response

        except Exception as e:
            error_msg = f"Failed to create analysis response: {str(e)}"
            log(error_msg, "error")
            raise ResultAggregationServiceError(error_msg)

    def create_async_response(
        self, request: Any, execution_id: str
    ) -> MACrossAsyncResponse:
        """
        Create asynchronous response for long-running analysis.

        Args:
            request: Analysis request
            execution_id: Unique execution identifier

        Returns:
            MACrossAsyncResponse with task information
        """
        # Initialize task status
        task_status[execution_id] = {
            "status": "pending",
            "started_at": datetime.now().isoformat(),
            "progress": "Initializing analysis...",
            "results": None,
            "error": None,
        }

        # Return immediate response with execution ID
        return MACrossAsyncResponse(
            status="accepted",
            execution_id=execution_id,
            message="Analysis task submitted",
            status_url=f"/api/ma-cross/status/{execution_id}",
            stream_url=f"/api/ma-cross/stream/{execution_id}",
            timestamp=datetime.now(),
            estimated_time=60.0,  # Estimate based on typical analysis time
        )

    async def get_task_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get the status of an asynchronous task.

        Args:
            execution_id: Unique execution ID

        Returns:
            Task status dictionary

        Raises:
            ResultAggregationServiceError: If execution ID not found
        """
        if execution_id not in task_status:
            raise ResultAggregationServiceError(
                f"Execution ID not found: {execution_id}"
            )

        # Get base status from task_status
        status = task_status[execution_id].copy()

        # Try to get enhanced progress data from progress tracker
        try:
            if self.progress_tracker:
                progress_status = await self.progress_tracker.get_status(execution_id)
                if progress_status:
                    # Merge progress tracking data
                    status.update(
                        {
                            "progress_percentage": progress_status.get("progress", 0.0),
                            "progress_message": progress_status.get(
                                "message", status.get("progress", "")
                            ),
                            "operation": progress_status.get(
                                "operation", "Strategy Analysis"
                            ),
                            "progress_updated_at": (
                                progress_status.get("updated_at", "").isoformat()
                                if progress_status.get("updated_at")
                                else None
                            ),
                        }
                    )
        except Exception:
            # If progress tracker fails, continue with basic status
            pass

        return status

    def record_metrics(
        self,
        endpoint: str,
        method: str,
        execution_time: float,
        status_code: int = 200,
        client_ip: str = "internal",
        user_agent: str = "strategy_analysis_service",
    ):
        """
        Record performance metrics for the analysis.

        Args:
            endpoint: API endpoint
            method: HTTP method
            execution_time: Time taken for execution
            status_code: HTTP status code
            client_ip: Client IP address
            user_agent: User agent string
        """
        try:
            self.metrics.record_request(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=execution_time,
                client_ip=client_ip,
                user_agent=user_agent,
            )
        except Exception as e:
            # Don't fail the analysis if metrics recording fails
            self.logger.log(f"Failed to record metrics: {str(e)}", "warning")

    def cleanup_old_tasks(self, max_age_hours: int = 24) -> int:
        """
        Clean up old task statuses.

        Args:
            max_age_hours: Maximum age of tasks to keep

        Returns:
            Number of tasks cleaned up
        """
        current_time = datetime.now()
        cleaned = 0

        for exec_id, status in list(task_status.items()):
            try:
                started_at = datetime.fromisoformat(status["started_at"])
                age_hours = (current_time - started_at).total_seconds() / 3600

                if age_hours > max_age_hours:
                    del task_status[exec_id]
                    cleaned += 1
            except (ValueError, KeyError):
                # Remove tasks with invalid timestamps
                del task_status[exec_id]
                cleaned += 1

        return cleaned

    def generate_execution_id(self) -> str:
        """Generate a unique execution ID."""
        return str(uuid.uuid4())

    def update_task_status(
        self,
        execution_id: str,
        status: str,
        progress: str = None,
        results: Any = None,
        error: str = None,
    ):
        """
        Update task status with new information.

        Args:
            execution_id: Task execution ID
            status: New status (pending, running, completed, failed)
            progress: Progress message
            results: Task results if completed
            error: Error message if failed
        """
        if execution_id in task_status:
            task_data = task_status[execution_id]
            task_data["status"] = status

            if progress is not None:
                task_data["progress"] = progress

            if results is not None:
                task_data["results"] = results

            if error is not None:
                task_data["error"] = error

            # Update timestamp
            task_data["updated_at"] = datetime.now().isoformat()

    def get_analysis_summary(
        self, portfolio_metrics: List[PortfolioMetrics]
    ) -> Dict[str, Any]:
        """
        Generate summary statistics for analysis results.

        Args:
            portfolio_metrics: List of portfolio metrics

        Returns:
            Dictionary with summary statistics
        """
        if not portfolio_metrics:
            return {"total_portfolios": 0, "summary": "No results"}

        summary = {
            "total_portfolios": len(portfolio_metrics),
            "performance_stats": {},
            "strategy_breakdown": {},
        }

        try:
            # Calculate performance statistics
            returns = [
                p.total_return for p in portfolio_metrics if hasattr(p, "total_return")
            ]
            if returns:
                summary["performance_stats"] = {
                    "avg_return": sum(returns) / len(returns),
                    "max_return": max(returns),
                    "min_return": min(returns),
                }

            # Strategy type breakdown
            strategy_counts = {}
            for p in portfolio_metrics:
                if hasattr(p, "strategy_type"):
                    strategy = p.strategy_type
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

            summary["strategy_breakdown"] = strategy_counts

        except Exception as e:
            summary["error"] = f"Error calculating summary: {str(e)}"

        return summary
