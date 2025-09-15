"""Event Ordering and Idempotency Module

Ensures event handlers are idempotent and maintains event ordering guarantees.
"""

import asyncio
import hashlib
import json
import time
from collections import OrderedDict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum
import threading


class EventPriority(Enum):
    """Event priority levels for ordering"""
    CRITICAL = 0  # Highest priority
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class EventSequence:
    """Tracks event sequence for ordering"""
    event_id: str
    sequence_number: int
    timestamp: float
    priority: EventPriority = EventPriority.NORMAL


class IdempotencyManager:
    """Manages idempotent event processing"""

    def __init__(self, ttl_seconds: int = 3600):
        """Initialize idempotency manager

        Args:
            ttl_seconds: Time to live for processed event records
        """
        self._processed_events: OrderedDict[str, float] = OrderedDict()
        self._lock = threading.Lock()
        self._ttl_seconds = ttl_seconds
        self._last_cleanup = time.time()

    def _generate_event_key(self, event_type: str, event_data: Dict[str, Any]) -> str:
        """Generate unique key for event based on type and data"""
        # Create deterministic hash of event
        event_str = f"{event_type}:{json.dumps(event_data, sort_keys=True)}"
        return hashlib.sha256(event_str.encode()).hexdigest()

    def is_duplicate(self, event_type: str, event_data: Dict[str, Any]) -> bool:
        """Check if event has already been processed"""
        event_key = self._generate_event_key(event_type, event_data)

        with self._lock:
            # Cleanup old entries periodically
            self._cleanup_old_entries()

            # Check if already processed
            if event_key in self._processed_events:
                return True

            # Mark as processed
            self._processed_events[event_key] = time.time()
            return False

    def _cleanup_old_entries(self):
        """Remove expired entries"""
        current_time = time.time()

        # Only cleanup every 60 seconds
        if current_time - self._last_cleanup < 60:
            return

        self._last_cleanup = current_time
        cutoff_time = current_time - self._ttl_seconds

        # Remove old entries
        to_remove = []
        for key, timestamp in self._processed_events.items():
            if timestamp < cutoff_time:
                to_remove.append(key)
            else:
                break  # OrderedDict maintains insertion order

        for key in to_remove:
            del self._processed_events[key]


class EventOrderingManager:
    """Manages event ordering and sequencing"""

    def __init__(self, max_queue_size: int = 10000):
        """Initialize ordering manager

        Args:
            max_queue_size: Maximum events to queue
        """
        self._sequence_counter = 0
        self._priority_queues: Dict[EventPriority, deque] = {
            priority: deque(maxlen=max_queue_size)
            for priority in EventPriority
        }
        self._pending_sequences: Dict[str, EventSequence] = {}
        self._lock = threading.Lock()
        self._waiting_events: Dict[int, List] = {}  # sequence -> [events]

    def assign_sequence(
        self,
        event_id: str,
        priority: EventPriority = EventPriority.NORMAL
    ) -> EventSequence:
        """Assign sequence number to event"""
        with self._lock:
            sequence = EventSequence(
                event_id=event_id,
                sequence_number=self._sequence_counter,
                timestamp=time.time(),
                priority=priority
            )
            self._sequence_counter += 1
            self._pending_sequences[event_id] = sequence
            return sequence

    def queue_event(self, event: Any, sequence: EventSequence):
        """Queue event for ordered processing"""
        with self._lock:
            # Add to priority queue
            self._priority_queues[sequence.priority].append((sequence, event))

    def get_next_events(self, batch_size: int = 10) -> List[tuple]:
        """Get next batch of events in order"""
        events = []

        with self._lock:
            # Process in priority order
            for priority in EventPriority:
                queue = self._priority_queues[priority]

                while queue and len(events) < batch_size:
                    events.append(queue.popleft())

                if len(events) >= batch_size:
                    break

        return events

    def mark_processed(self, event_id: str):
        """Mark event as processed"""
        with self._lock:
            if event_id in self._pending_sequences:
                del self._pending_sequences[event_id]


class OrderedEventProcessor:
    """Processes events with ordering and idempotency guarantees"""

    def __init__(
        self,
        idempotency_ttl: int = 3600,
        max_batch_size: int = 10,
        process_interval: float = 0.1
    ):
        """Initialize ordered processor

        Args:
            idempotency_ttl: TTL for idempotency checks
            max_batch_size: Maximum events to process in batch
            process_interval: Interval between processing batches
        """
        self.idempotency_manager = IdempotencyManager(idempotency_ttl)
        self.ordering_manager = EventOrderingManager()
        self._handlers: Dict[str, List[Callable]] = {}
        self._max_batch_size = max_batch_size
        self._process_interval = process_interval
        self._processing = False
        self._processor_task: Optional[asyncio.Task] = None

    def register_handler(
        self,
        event_type: str,
        handler: Callable,
        priority: EventPriority = EventPriority.NORMAL
    ):
        """Register handler with priority"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append((handler, priority))

    async def process_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        event_id: str,
        priority: EventPriority = EventPriority.NORMAL
    ) -> bool:
        """Process event with ordering and idempotency

        Returns:
            True if event was processed, False if duplicate
        """
        # Check idempotency
        if self.idempotency_manager.is_duplicate(event_type, event_data):
            return False

        # Assign sequence
        sequence = self.ordering_manager.assign_sequence(event_id, priority)

        # Queue for ordered processing
        event = {
            'type': event_type,
            'data': event_data,
            'id': event_id
        }
        self.ordering_manager.queue_event(event, sequence)

        return True

    async def start_processing(self):
        """Start background event processing"""
        if self._processing:
            return

        self._processing = True
        self._processor_task = asyncio.create_task(self._process_loop())

    async def stop_processing(self):
        """Stop background processing"""
        self._processing = False
        if self._processor_task:
            await self._processor_task

    async def _process_loop(self):
        """Main processing loop"""
        while self._processing:
            try:
                # Get next batch of events
                events = self.ordering_manager.get_next_events(self._max_batch_size)

                if events:
                    # Process batch
                    await self._process_batch(events)

                # Wait before next batch
                await asyncio.sleep(self._process_interval)

            except Exception as e:
                # Log error and continue
                print(f"Error in event processing: {e}")
                await asyncio.sleep(self._process_interval)

    async def _process_batch(self, events: List[tuple]):
        """Process a batch of events"""
        tasks = []

        for sequence, event in events:
            event_type = event['type']
            event_data = event['data']
            event_id = event['id']

            # Get handlers for this event type
            if event_type in self._handlers:
                for handler, _ in self._handlers[event_type]:
                    if asyncio.iscoroutinefunction(handler):
                        task = asyncio.create_task(
                            self._run_handler(handler, event)
                        )
                    else:
                        task = asyncio.create_task(
                            asyncio.get_event_loop().run_in_executor(
                                None, handler, event
                            )
                        )
                    tasks.append(task)

            # Mark as processed
            self.ordering_manager.mark_processed(event_id)

        # Wait for all handlers
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_handler(self, handler: Callable, event: Dict):
        """Run a single handler with error handling"""
        try:
            await handler(event)
        except Exception as e:
            # Log error but don't fail the batch
            print(f"Handler error for event {event.get('id')}: {e}")


# Global instance for easy access
_processor: Optional[OrderedEventProcessor] = None


def get_ordered_processor() -> OrderedEventProcessor:
    """Get global ordered processor instance"""
    global _processor
    if _processor is None:
        _processor = OrderedEventProcessor()
    return _processor