"""
Event Bus Architecture

This module provides an event-driven architecture for decoupling components
through asynchronous message passing and event handling.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventPriority(Enum):
    """Event priority levels."""

    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Base event class."""

    event_type: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "data": self.data,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            event_type=data["event_type"],
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data.get("source"),
            data=data.get("data", {}),
            priority=EventPriority(data.get("priority", EventPriority.NORMAL.value)),
            correlation_id=data.get("correlation_id"),
            metadata=data.get("metadata", {}),
        )


class EventHandler(ABC):
    """Abstract base class for event handlers."""

    @abstractmethod
    async def handle(self, event: Event) -> None:
        """Handle an event."""

    @abstractmethod
    def get_event_types(self) -> List[str]:
        """Get list of event types this handler can process."""

    def get_handler_id(self) -> str:
        """Get unique identifier for this handler."""
        return f"{self.__class__.__module__}.{self.__class__.__name__}"


class EventFilter:
    """Filter for events based on various criteria."""

    def __init__(
        self,
        event_types: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        min_priority: Optional[EventPriority] = None,
        correlation_ids: Optional[List[str]] = None,
        custom_filter: Optional[Callable[[Event], bool]] = None,
    ):
        self.event_types = set(event_types) if event_types else None
        self.sources = set(sources) if sources else None
        self.min_priority = min_priority
        self.correlation_ids = set(correlation_ids) if correlation_ids else None
        self.custom_filter = custom_filter

    def matches(self, event: Event) -> bool:
        """Check if event matches filter criteria."""
        if self.event_types and event.event_type not in self.event_types:
            return False

        if self.sources and event.source not in self.sources:
            return False

        if self.min_priority and event.priority.value < self.min_priority.value:
            return False

        if self.correlation_ids and event.correlation_id not in self.correlation_ids:
            return False

        if self.custom_filter and not self.custom_filter(event):
            return False

        return True


@dataclass
class Subscription:
    """Event subscription."""

    handler: EventHandler
    filter: Optional[EventFilter] = None
    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    active: bool = True


class EventBus:
    """Asynchronous event bus for decoupled communication."""

    def __init__(self, max_workers: int = 4):
        self._subscriptions: Dict[str, List[Subscription]] = {}
        self._global_subscriptions: List[Subscription] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_tasks: List[asyncio.Task] = []
        self._max_workers = max_workers
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self._event_history: List[Event] = []
        self._max_history = 1000
        self._handlers_by_id: Dict[str, EventHandler] = {}

        # Metrics
        self._events_published = 0
        self._events_processed = 0
        self._events_failed = 0

    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return

        self._running = True

        # Start worker tasks
        for i in range(self._max_workers):
            task = asyncio.create_task(self._worker_loop(f"worker-{i}"))
            self._worker_tasks.append(task)

    async def stop(self) -> None:
        """Stop the event bus gracefully."""
        if not self._running:
            return

        self._running = False

        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._worker_tasks, return_exceptions=True)
        self._worker_tasks.clear()

        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)

    def subscribe(
        self,
        handler: EventHandler,
        event_types: Optional[List[str]] = None,
        filter: Optional[EventFilter] = None,
    ) -> str:
        """Subscribe a handler to events."""
        event_types = event_types or handler.get_event_types()

        subscription = Subscription(handler=handler, filter=filter)

        self._handlers_by_id[handler.get_handler_id()] = handler

        if event_types:
            for event_type in event_types:
                if event_type not in self._subscriptions:
                    self._subscriptions[event_type] = []
                self._subscriptions[event_type].append(subscription)
        else:
            # Global subscription (all events)
            self._global_subscriptions.append(subscription)

        return subscription.subscription_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe a handler."""
        # Check global subscriptions
        for i, sub in enumerate(self._global_subscriptions):
            if sub.subscription_id == subscription_id:
                self._global_subscriptions.pop(i)
                return True

        # Check event-specific subscriptions
        for event_type, subscriptions in self._subscriptions.items():
            for i, sub in enumerate(subscriptions):
                if sub.subscription_id == subscription_id:
                    subscriptions.pop(i)
                    if not subscriptions:
                        del self._subscriptions[event_type]
                    return True

        return False

    def unsubscribe_handler(self, handler_id: str) -> int:
        """Unsubscribe all subscriptions for a handler. Returns count of removed subscriptions."""
        removed_count = 0

        # Remove from global subscriptions
        self._global_subscriptions = [
            sub
            for sub in self._global_subscriptions
            if sub.handler.get_handler_id() != handler_id
        ]

        # Remove from event-specific subscriptions
        for event_type in list(self._subscriptions.keys()):
            original_count = len(self._subscriptions[event_type])
            self._subscriptions[event_type] = [
                sub
                for sub in self._subscriptions[event_type]
                if sub.handler.get_handler_id() != handler_id
            ]
            removed_count += original_count - len(self._subscriptions[event_type])

            if not self._subscriptions[event_type]:
                del self._subscriptions[event_type]

        # Remove from handlers registry
        if handler_id in self._handlers_by_id:
            del self._handlers_by_id[handler_id]

        return removed_count

    async def publish(self, event: Event) -> None:
        """Publish an event to the bus."""
        if not self._running:
            raise RuntimeError("Event bus is not running")

        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)

        # Queue for processing
        await self._event_queue.put(event)
        self._events_published += 1

    async def publish_dict(self, event_data: Dict[str, Any]) -> None:
        """Publish an event from dictionary data."""
        event = Event.from_dict(event_data)
        await self.publish(event)

    async def _worker_loop(self, worker_id: str) -> None:
        """Main worker loop for processing events."""
        while self._running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)

                # Process event
                await self._process_event(event, worker_id)

                # Mark task as done
                self._event_queue.task_done()

            except asyncio.TimeoutError:
                # No event to process, continue
                continue
            except Exception as e:
                # Log error but continue processing
                print(f"Worker {worker_id} error: {e}")
                self._events_failed += 1

    async def _process_event(self, event: Event, worker_id: str) -> None:
        """Process a single event."""
        handlers_to_call = []

        # Get event-specific handlers
        if event.event_type in self._subscriptions:
            for subscription in self._subscriptions[event.event_type]:
                if subscription.active and (
                    not subscription.filter or subscription.filter.matches(event)
                ):
                    handlers_to_call.append(subscription.handler)

        # Get global handlers
        for subscription in self._global_subscriptions:
            if subscription.active and (
                not subscription.filter or subscription.filter.matches(event)
            ):
                handlers_to_call.append(subscription.handler)

        # Call handlers concurrently
        if handlers_to_call:
            tasks = [
                self._call_handler_safely(handler, event)
                for handler in handlers_to_call
            ]
            await asyncio.gather(*tasks, return_exceptions=True)

        self._events_processed += 1

    async def _call_handler_safely(self, handler: EventHandler, event: Event) -> None:
        """Call event handler with error handling."""
        try:
            await handler.handle(event)
        except Exception as e:
            # Log error but don't propagate
            print(
                f"Handler {handler.get_handler_id()} failed for event {event.event_id}: {e}"
            )
            self._events_failed += 1

    def get_subscriptions(self) -> Dict[str, Any]:
        """Get information about current subscriptions."""
        return {
            "event_specific": {
                event_type: [
                    {
                        "subscription_id": sub.subscription_id,
                        "handler_id": sub.handler.get_handler_id(),
                        "created_at": sub.created_at.isoformat(),
                        "active": sub.active,
                    }
                    for sub in subscriptions
                ]
                for event_type, subscriptions in self._subscriptions.items()
            },
            "global": [
                {
                    "subscription_id": sub.subscription_id,
                    "handler_id": sub.handler.get_handler_id(),
                    "created_at": sub.created_at.isoformat(),
                    "active": sub.active,
                }
                for sub in self._global_subscriptions
            ],
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics."""
        return {
            "events_published": self._events_published,
            "events_processed": self._events_processed,
            "events_failed": self._events_failed,
            "queue_size": self._event_queue.qsize(),
            "total_subscriptions": len(self._global_subscriptions)
            + sum(len(subs) for subs in self._subscriptions.values()),
            "total_handlers": len(self._handlers_by_id),
            "running": self._running,
            "worker_count": len(self._worker_tasks),
        }

    def get_event_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get recent event history."""
        events = self._event_history
        if limit:
            events = events[-limit:]
        return [event.to_dict() for event in events]


# Global event bus instance
event_bus = EventBus()


# Convenience functions
async def publish_event(
    event_type: str,
    data: Dict[str, Any],
    source: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
    correlation_id: Optional[str] = None,
) -> str:
    """Convenience function to publish an event."""
    event = Event(
        event_type=event_type,
        data=data,
        source=source,
        priority=priority,
        correlation_id=correlation_id,
    )
    await event_bus.publish(event)
    return event.event_id


def subscribe_to_events(
    handler: EventHandler,
    event_types: Optional[List[str]] = None,
    filter: Optional[EventFilter] = None,
) -> str:
    """Convenience function to subscribe to events."""
    return event_bus.subscribe(handler, event_types, filter)


# Example event types for trading system
class TradingEvents:
    """Trading system event types."""

    PORTFOLIO_CREATED = "portfolio.created"
    PORTFOLIO_UPDATED = "portfolio.updated"
    PORTFOLIO_DELETED = "portfolio.deleted"
    STRATEGY_EXECUTED = "strategy.executed"
    ANALYSIS_COMPLETED = "analysis.completed"
    DATA_UPDATED = "data.updated"
    SYSTEM_ERROR = "system.error"
    USER_ACTION = "user.action"


# Example event handlers
class LoggingEventHandler(EventHandler):
    """Example handler that logs all events."""

    async def handle(self, event: Event) -> None:
        print(
            f"[LOG] {event.timestamp}: {event.event_type} from {event.source} - {event.data}"
        )

    def get_event_types(self) -> List[str]:
        return []  # Global handler (all events)


class PortfolioEventHandler(EventHandler):
    """Example handler for portfolio events."""

    async def handle(self, event: Event) -> None:
        if event.event_type == TradingEvents.PORTFOLIO_CREATED:
            print(f"New portfolio created: {event.data.get('portfolio_id')}")
        elif event.event_type == TradingEvents.PORTFOLIO_UPDATED:
            print(f"Portfolio updated: {event.data.get('portfolio_id')}")
        elif event.event_type == TradingEvents.PORTFOLIO_DELETED:
            print(f"Portfolio deleted: {event.data.get('portfolio_id')}")

    def get_event_types(self) -> List[str]:
        return [
            TradingEvents.PORTFOLIO_CREATED,
            TradingEvents.PORTFOLIO_UPDATED,
            TradingEvents.PORTFOLIO_DELETED,
        ]
