"""
Async Messaging for Long Operations

This module provides asynchronous messaging capabilities for handling
long-running operations with progress tracking, cancellation, and result delivery.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, AsyncIterator, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import weakref

from app.api.event_bus import Event, EventHandler, event_bus, EventPriority


class OperationStatus(Enum):
    """Status of a long-running operation."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class OperationProgress:
    """Progress information for an operation."""
    current: int = 0
    total: Optional[int] = None
    percentage: Optional[float] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, current: int, total: Optional[int] = None, message: str = "", **details):
        """Update progress information."""
        self.current = current
        if total is not None:
            self.total = total
        if message:
            self.message = message
        if details:
            self.details.update(details)
        
        # Calculate percentage if total is available
        if self.total and self.total > 0:
            self.percentage = (self.current / self.total) * 100


@dataclass
class OperationResult:
    """Result of a long-running operation."""
    operation_id: str
    status: OperationStatus
    result: Any = None
    error: Optional[str] = None
    progress: Optional[OperationProgress] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AsyncOperation(ABC):
    """Abstract base class for async operations."""
    
    def __init__(self, operation_id: str, timeout: Optional[int] = None):
        self.operation_id = operation_id
        self.timeout = timeout
        self.status = OperationStatus.PENDING
        self.progress = OperationProgress()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.result: Any = None
        self.error: Optional[str] = None
        self.cancelled = False
        self._cancel_event = asyncio.Event()
        
    @abstractmethod
    async def execute(self) -> Any:
        """Execute the operation."""
        pass
    
    @abstractmethod
    def get_operation_name(self) -> str:
        """Get the name of this operation."""
        pass
    
    def cancel(self) -> None:
        """Cancel the operation."""
        self.cancelled = True
        self._cancel_event.set()
        self.status = OperationStatus.CANCELLED
    
    def is_cancelled(self) -> bool:
        """Check if operation is cancelled."""
        return self.cancelled
    
    async def update_progress(self, current: int, total: Optional[int] = None, message: str = "", **details):
        """Update operation progress and notify subscribers."""
        self.progress.update(current, total, message, **details)
        
        # Publish progress event
        await event_bus.publish(Event(
            event_type="operation.progress",
            source="async_messaging",
            data={
                "operation_id": self.operation_id,
                "progress": {
                    "current": self.progress.current,
                    "total": self.progress.total,
                    "percentage": self.progress.percentage,
                    "message": self.progress.message,
                    "details": self.progress.details
                }
            }
        ))
    
    def get_result(self) -> OperationResult:
        """Get current operation result."""
        duration = None
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at
        
        return OperationResult(
            operation_id=self.operation_id,
            status=self.status,
            result=self.result,
            error=self.error,
            progress=self.progress,
            started_at=self.started_at,
            completed_at=self.completed_at,
            duration=duration
        )


class OperationQueue:
    """Queue for managing async operations."""
    
    def __init__(self, max_concurrent: int = 4):
        self.max_concurrent = max_concurrent
        self._operations: Dict[str, AsyncOperation] = {}
        self._results: Dict[str, OperationResult] = {}
        self._running_operations: Dict[str, asyncio.Task] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._worker_tasks: List[asyncio.Task] = []
        self._running = False
        
        # Metrics
        self._total_operations = 0
        self._completed_operations = 0
        self._failed_operations = 0
        self._cancelled_operations = 0
    
    async def start(self) -> None:
        """Start the operation queue."""
        if self._running:
            return
        
        self._running = True
        
        # Start worker tasks
        for i in range(self.max_concurrent):
            task = asyncio.create_task(self._worker_loop(f"op-worker-{i}"))
            self._worker_tasks.append(task)
    
    async def stop(self) -> None:
        """Stop the operation queue."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all running operations
        for operation_id in list(self._running_operations.keys()):
            await self.cancel_operation(operation_id)
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()
    
    async def submit_operation(self, operation: AsyncOperation) -> str:
        """Submit an operation for execution."""
        if not self._running:
            raise RuntimeError("Operation queue is not running")
        
        self._operations[operation.operation_id] = operation
        await self._queue.put(operation.operation_id)
        self._total_operations += 1
        
        # Publish operation submitted event
        await event_bus.publish(Event(
            event_type="operation.submitted",
            source="async_messaging",
            data={
                "operation_id": operation.operation_id,
                "operation_name": operation.get_operation_name()
            }
        ))
        
        return operation.operation_id
    
    async def cancel_operation(self, operation_id: str) -> bool:
        """Cancel a running operation."""
        # Cancel if running
        if operation_id in self._running_operations:
            self._running_operations[operation_id].cancel()
            del self._running_operations[operation_id]
        
        # Mark operation as cancelled
        if operation_id in self._operations:
            self._operations[operation_id].cancel()
            result = self._operations[operation_id].get_result()
            self._results[operation_id] = result
            
            # Publish cancellation event
            await event_bus.publish(Event(
                event_type="operation.cancelled",
                source="async_messaging",
                data={"operation_id": operation_id}
            ))
            
            self._cancelled_operations += 1
            return True
        
        return False
    
    def get_operation_status(self, operation_id: str) -> Optional[OperationResult]:
        """Get status of an operation."""
        if operation_id in self._results:
            return self._results[operation_id]
        
        if operation_id in self._operations:
            return self._operations[operation_id].get_result()
        
        return None
    
    def list_operations(self, status_filter: Optional[OperationStatus] = None) -> List[OperationResult]:
        """List operations with optional status filter."""
        results = []
        
        # Add completed operations
        for result in self._results.values():
            if not status_filter or result.status == status_filter:
                results.append(result)
        
        # Add active operations
        for operation in self._operations.values():
            result = operation.get_result()
            if not status_filter or result.status == status_filter:
                results.append(result)
        
        return results
    
    async def _worker_loop(self, worker_id: str) -> None:
        """Worker loop for processing operations."""
        while self._running:
            try:
                # Get operation from queue
                operation_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                
                if operation_id in self._operations:
                    operation = self._operations[operation_id]
                    
                    # Execute operation
                    task = asyncio.create_task(self._execute_operation(operation, worker_id))
                    self._running_operations[operation_id] = task
                    
                    await task
                    
                    # Remove from running operations
                    if operation_id in self._running_operations:
                        del self._running_operations[operation_id]
                
                self._queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
    
    async def _execute_operation(self, operation: AsyncOperation, worker_id: str) -> None:
        """Execute a single operation."""
        operation.status = OperationStatus.RUNNING
        operation.started_at = datetime.utcnow()
        
        try:
            # Publish operation started event
            await event_bus.publish(Event(
                event_type="operation.started",
                source="async_messaging",
                data={
                    "operation_id": operation.operation_id,
                    "operation_name": operation.get_operation_name(),
                    "worker_id": worker_id
                }
            ))
            
            # Execute with timeout if specified
            if operation.timeout:
                result = await asyncio.wait_for(operation.execute(), timeout=operation.timeout)
            else:
                result = await operation.execute()
            
            # Operation completed successfully
            operation.result = result
            operation.status = OperationStatus.COMPLETED
            operation.completed_at = datetime.utcnow()
            self._completed_operations += 1
            
            # Publish completion event
            await event_bus.publish(Event(
                event_type="operation.completed",
                source="async_messaging",
                data={
                    "operation_id": operation.operation_id,
                    "operation_name": operation.get_operation_name(),
                    "duration": (operation.completed_at - operation.started_at).total_seconds()
                },
                priority=EventPriority.HIGH
            ))
            
        except asyncio.TimeoutError:
            operation.status = OperationStatus.TIMEOUT
            operation.error = f"Operation timed out after {operation.timeout} seconds"
            operation.completed_at = datetime.utcnow()
            self._failed_operations += 1
            
            await event_bus.publish(Event(
                event_type="operation.timeout",
                source="async_messaging",
                data={
                    "operation_id": operation.operation_id,
                    "timeout": operation.timeout
                }
            ))
            
        except asyncio.CancelledError:
            operation.status = OperationStatus.CANCELLED
            operation.completed_at = datetime.utcnow()
            self._cancelled_operations += 1
            
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error = str(e)
            operation.completed_at = datetime.utcnow()
            self._failed_operations += 1
            
            await event_bus.publish(Event(
                event_type="operation.failed",
                source="async_messaging",
                data={
                    "operation_id": operation.operation_id,
                    "error": str(e)
                },
                priority=EventPriority.HIGH
            ))
        
        finally:
            # Store result and clean up
            self._results[operation.operation_id] = operation.get_result()
            if operation.operation_id in self._operations:
                del self._operations[operation.operation_id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get operation queue metrics."""
        return {
            "total_operations": self._total_operations,
            "completed_operations": self._completed_operations,
            "failed_operations": self._failed_operations,
            "cancelled_operations": self._cancelled_operations,
            "running_operations": len(self._running_operations),
            "queued_operations": self._queue.qsize(),
            "success_rate": (self._completed_operations / max(self._total_operations, 1)) * 100,
            "max_concurrent": self.max_concurrent,
            "active_workers": len(self._worker_tasks),
            "running": self._running
        }


class ProgressStreamHandler(EventHandler):
    """Handler for streaming operation progress via Server-Sent Events."""
    
    def __init__(self):
        self._streams: Dict[str, List[asyncio.Queue]] = {}
    
    async def handle(self, event: Event) -> None:
        """Handle progress events."""
        if event.event_type == "operation.progress":
            operation_id = event.data.get("operation_id")
            if operation_id and operation_id in self._streams:
                progress_data = {
                    "type": "progress",
                    "data": event.data
                }
                
                # Send to all subscribers
                for queue in self._streams[operation_id]:
                    try:
                        await queue.put(progress_data)
                    except:
                        pass  # Queue might be closed
    
    def get_event_types(self) -> List[str]:
        return ["operation.progress", "operation.completed", "operation.failed", "operation.cancelled"]
    
    async def subscribe_to_operation(self, operation_id: str) -> AsyncIterator[Dict[str, Any]]:
        """Subscribe to progress updates for an operation."""
        queue = asyncio.Queue()
        
        if operation_id not in self._streams:
            self._streams[operation_id] = []
        self._streams[operation_id].append(queue)
        
        try:
            while True:
                data = await queue.get()
                yield data
                
                # Stop streaming if operation is complete
                if data.get("type") in ["completed", "failed", "cancelled"]:
                    break
        finally:
            # Clean up
            if operation_id in self._streams:
                self._streams[operation_id].remove(queue)
                if not self._streams[operation_id]:
                    del self._streams[operation_id]


# Global instances
operation_queue = OperationQueue()
progress_stream_handler = ProgressStreamHandler()


# Example long-running operations
class DataAnalysisOperation(AsyncOperation):
    """Example data analysis operation."""
    
    def __init__(self, operation_id: str, dataset_size: int, timeout: int = 300):
        super().__init__(operation_id, timeout)
        self.dataset_size = dataset_size
    
    def get_operation_name(self) -> str:
        return "data_analysis"
    
    async def execute(self) -> Dict[str, Any]:
        """Simulate data analysis."""
        total_steps = 100
        
        for step in range(total_steps):
            if self.is_cancelled():
                raise asyncio.CancelledError()
            
            # Simulate work
            await asyncio.sleep(0.1)
            
            # Update progress
            await self.update_progress(
                current=step + 1,
                total=total_steps,
                message=f"Processing step {step + 1}/{total_steps}",
                dataset_size=self.dataset_size
            )
        
        return {
            "analysis_complete": True,
            "dataset_size": self.dataset_size,
            "steps_completed": total_steps
        }


class PortfolioOptimizationOperation(AsyncOperation):
    """Example portfolio optimization operation."""
    
    def __init__(self, operation_id: str, symbols: List[str], timeout: int = 600):
        super().__init__(operation_id, timeout)
        self.symbols = symbols
    
    def get_operation_name(self) -> str:
        return "portfolio_optimization"
    
    async def execute(self) -> Dict[str, Any]:
        """Simulate portfolio optimization."""
        total_symbols = len(self.symbols)
        
        for i, symbol in enumerate(self.symbols):
            if self.is_cancelled():
                raise asyncio.CancelledError()
            
            # Simulate optimization work
            await asyncio.sleep(0.5)
            
            await self.update_progress(
                current=i + 1,
                total=total_symbols,
                message=f"Optimizing {symbol}",
                current_symbol=symbol
            )
        
        return {
            "optimization_complete": True,
            "symbols_processed": self.symbols,
            "optimal_weights": {symbol: round(1/total_symbols, 4) for symbol in self.symbols}
        }


# Convenience functions
async def submit_data_analysis(dataset_size: int, timeout: int = 300) -> str:
    """Submit a data analysis operation."""
    operation_id = str(uuid.uuid4())
    operation = DataAnalysisOperation(operation_id, dataset_size, timeout)
    return await operation_queue.submit_operation(operation)


async def submit_portfolio_optimization(symbols: List[str], timeout: int = 600) -> str:
    """Submit a portfolio optimization operation."""
    operation_id = str(uuid.uuid4())
    operation = PortfolioOptimizationOperation(operation_id, symbols, timeout)
    return await operation_queue.submit_operation(operation)