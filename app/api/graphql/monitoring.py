"""
GraphQL Monitoring and Logging

This module provides monitoring, logging, and performance tracking for GraphQL operations.
"""

import time
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timezone
from strawberry.types import Info
from strawberry.extensions import SchemaExtension
import json

logger = logging.getLogger("app.graphql")

class GraphQLMonitoringExtension(SchemaExtension):
    """
    Extension to monitor and log GraphQL operations
    """
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.operation_name: Optional[str] = None
        self.operation_type: Optional[str] = None
        self.variables: Optional[Dict[str, Any]] = None
        
    async def on_operation(self):
        """Called at the start of a GraphQL operation"""
        self.start_time = time.time()
        
        # Extract operation details
        execution_context = self.execution_context
        if execution_context.operation_name:
            self.operation_name = execution_context.operation_name
            
        # Get operation type (query/mutation/subscription)
        if execution_context.operation_type:
            self.operation_type = execution_context.operation_type.value
            
        # Get variables
        if execution_context.variables:
            self.variables = execution_context.variables
            
        # Log operation start
        logger.info(
            "GraphQL operation started",
            extra={
                "operation_name": self.operation_name,
                "operation_type": self.operation_type,
                "variables": json.dumps(self.variables) if self.variables else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Continue with operation
        yield
        
        # Calculate execution time
        execution_time = (time.time() - self.start_time) * 1000  # Convert to milliseconds
        
        # Log operation completion
        logger.info(
            "GraphQL operation completed",
            extra={
                "operation_name": self.operation_name,
                "operation_type": self.operation_type,
                "execution_time_ms": round(execution_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
        
    def on_validate(self):
        """Called during validation phase"""
        yield
        
    def on_parse(self):
        """Called during parsing phase"""
        yield
        
    async def resolve(self, _next, root, info: Info, **kwargs):
        """Called for each field resolution"""
        field_name = info.field_name
        parent_type = info.parent_type.name
        
        start = time.time()
        
        try:
            result = await _next(root, info, **kwargs)
            
            # Log slow field resolutions (> 100ms)
            duration_ms = (time.time() - start) * 1000
            if duration_ms > 100:
                logger.warning(
                    f"Slow GraphQL field resolution: {parent_type}.{field_name}",
                    extra={
                        "field": field_name,
                        "parent_type": parent_type,
                        "duration_ms": round(duration_ms, 2)
                    }
                )
                
            return result
            
        except Exception as e:
            # Log field resolution errors
            logger.error(
                f"GraphQL field resolution error: {parent_type}.{field_name}",
                extra={
                    "field": field_name,
                    "parent_type": parent_type,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise

class GraphQLMetrics:
    """
    Singleton to track GraphQL metrics
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = {
                "total_operations": 0,
                "total_queries": 0,
                "total_mutations": 0,
                "total_errors": 0,
                "operation_durations": [],
                "slow_operations": []
            }
        return cls._instance
    
    def record_operation(self, operation_type: str, duration_ms: float, error: bool = False):
        """Record a GraphQL operation"""
        self.metrics["total_operations"] += 1
        
        if operation_type == "query":
            self.metrics["total_queries"] += 1
        elif operation_type == "mutation":
            self.metrics["total_mutations"] += 1
            
        if error:
            self.metrics["total_errors"] += 1
            
        self.metrics["operation_durations"].append(duration_ms)
        
        # Keep only last 1000 durations
        if len(self.metrics["operation_durations"]) > 1000:
            self.metrics["operation_durations"] = self.metrics["operation_durations"][-1000:]
            
        # Track slow operations (> 1000ms)
        if duration_ms > 1000:
            self.metrics["slow_operations"].append({
                "type": operation_type,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Keep only last 100 slow operations
            if len(self.metrics["slow_operations"]) > 100:
                self.metrics["slow_operations"] = self.metrics["slow_operations"][-100:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        durations = self.metrics["operation_durations"]
        
        return {
            "total_operations": self.metrics["total_operations"],
            "total_queries": self.metrics["total_queries"],
            "total_mutations": self.metrics["total_mutations"],
            "total_errors": self.metrics["total_errors"],
            "average_duration_ms": sum(durations) / len(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "slow_operations_count": len(self.metrics["slow_operations"])
        }

# Global metrics instance
graphql_metrics = GraphQLMetrics()