"""Error Recovery Patterns for Event Processing

Implements circuit breaker, retry logic, and dead letter queue patterns.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import json
from pathlib import Path
import logging


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class RetryPolicy:
    """Retry configuration"""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes to close from half-open
    timeout: float = 60.0  # Seconds before trying half-open
    window_size: int = 10  # Rolling window for failure rate


@dataclass
class FailedEvent:
    """Dead letter queue entry"""
    event_type: str
    event_data: Dict[str, Any]
    error: str
    attempts: int
    first_failure: datetime
    last_failure: datetime
    event_id: Optional[str] = None


class CircuitBreaker:
    """Circuit breaker for protecting failing services"""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_state_change = time.time()
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        async with self._lock:
            # Check circuit state
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = time.time()
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            # Execute the function
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

            # Record success
            await self._on_success()
            return result

        except Exception as e:
            # Record failure
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call"""
        async with self._lock:
            self.failure_count = 0

            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.success_count = 0
                    self.last_state_change = time.time()
                    logging.info(f"Circuit breaker {self.name} closed")

    async def _on_failure(self):
        """Handle failed call"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()
                logging.warning(f"Circuit breaker {self.name} reopened")

            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.last_state_change = time.time()
                    logging.warning(f"Circuit breaker {self.name} opened after {self.failure_count} failures")

    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset from open state"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.timeout

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time,
            "last_state_change": self.last_state_change
        }


class RetryManager:
    """Manages retry logic with exponential backoff"""

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        on_retry: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """Execute function with retry logic"""
        last_exception = None
        delay = self.policy.initial_delay

        for attempt in range(1, self.policy.max_attempts + 1):
            try:
                # Execute function
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if attempt >= self.policy.max_attempts:
                    break

                # Call retry callback if provided
                if on_retry:
                    await on_retry(attempt, e, delay)

                # Wait before retry
                if self.policy.jitter:
                    import random
                    jitter_delay = delay * (0.5 + random.random())
                    await asyncio.sleep(jitter_delay)
                else:
                    await asyncio.sleep(delay)

                # Calculate next delay
                delay = min(
                    delay * self.policy.exponential_base,
                    self.policy.max_delay
                )

        # All retries exhausted
        raise last_exception


class DeadLetterQueue:
    """Manages failed events for later processing"""

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path:
            self.storage_path = storage_path
        else:
            self.storage_path = Path.home() / '.pm' / 'dlq'

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.queue_file = self.storage_path / 'dead_letters.json'
        self._lock = asyncio.Lock()

    async def add_failed_event(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        error: str,
        event_id: Optional[str] = None
    ):
        """Add failed event to DLQ"""
        async with self._lock:
            # Load existing queue
            queue = await self._load_queue()

            # Create or update failed event
            key = event_id or f"{event_type}_{hash(json.dumps(event_data, sort_keys=True))}"

            if key in queue:
                # Update existing
                failed = queue[key]
                failed['attempts'] += 1
                failed['last_failure'] = datetime.now().isoformat()
                failed['error'] = error
            else:
                # Add new
                queue[key] = {
                    'event_type': event_type,
                    'event_data': event_data,
                    'error': error,
                    'attempts': 1,
                    'first_failure': datetime.now().isoformat(),
                    'last_failure': datetime.now().isoformat(),
                    'event_id': event_id
                }

            # Save queue
            await self._save_queue(queue)

    async def get_failed_events(
        self,
        max_age_hours: Optional[int] = None
    ) -> List[FailedEvent]:
        """Get failed events from DLQ"""
        async with self._lock:
            queue = await self._load_queue()

            events = []
            cutoff = None
            if max_age_hours:
                cutoff = datetime.now() - timedelta(hours=max_age_hours)

            for key, data in queue.items():
                last_failure = datetime.fromisoformat(data['last_failure'])

                if cutoff and last_failure < cutoff:
                    continue

                events.append(FailedEvent(
                    event_type=data['event_type'],
                    event_data=data['event_data'],
                    error=data['error'],
                    attempts=data['attempts'],
                    first_failure=datetime.fromisoformat(data['first_failure']),
                    last_failure=last_failure,
                    event_id=data.get('event_id')
                ))

            return events

    async def remove_event(self, event_id: str):
        """Remove event from DLQ after successful reprocessing"""
        async with self._lock:
            queue = await self._load_queue()
            if event_id in queue:
                del queue[event_id]
                await self._save_queue(queue)

    async def _load_queue(self) -> Dict:
        """Load queue from storage"""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    async def _save_queue(self, queue: Dict):
        """Save queue to storage"""
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2, default=str)


class ResilientEventProcessor:
    """Event processor with full resilience patterns"""

    def __init__(
        self,
        name: str,
        retry_policy: Optional[RetryPolicy] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        enable_dlq: bool = True
    ):
        self.name = name
        self.retry_manager = RetryManager(retry_policy)
        self.circuit_breaker = CircuitBreaker(name, circuit_config)
        self.dlq = DeadLetterQueue() if enable_dlq else None
        self._metrics = {
            'processed': 0,
            'failed': 0,
            'retried': 0,
            'dlq_added': 0
        }

    async def process_event(
        self,
        handler: Callable,
        event_type: str,
        event_data: Dict[str, Any],
        event_id: Optional[str] = None
    ) -> bool:
        """Process event with full resilience

        Returns:
            True if processed successfully, False if failed
        """
        try:
            # Track retry attempts
            retry_count = [0]

            async def on_retry(attempt, error, delay):
                retry_count[0] = attempt
                self._metrics['retried'] += 1
                logging.warning(
                    f"Retry {attempt} for event {event_type} after {delay}s: {error}"
                )

            # Execute with circuit breaker and retry
            async def execute():
                return await self.circuit_breaker.call(
                    handler,
                    {'type': event_type, 'data': event_data, 'id': event_id}
                )

            await self.retry_manager.execute_with_retry(
                execute,
                on_retry=on_retry
            )

            self._metrics['processed'] += 1
            return True

        except Exception as e:
            self._metrics['failed'] += 1
            logging.error(f"Failed to process event {event_type}: {e}")

            # Add to dead letter queue
            if self.dlq:
                await self.dlq.add_failed_event(
                    event_type,
                    event_data,
                    str(e),
                    event_id
                )
                self._metrics['dlq_added'] += 1

            return False

    async def reprocess_dlq(
        self,
        handler: Callable,
        max_events: int = 100
    ) -> Dict[str, int]:
        """Reprocess events from dead letter queue"""
        if not self.dlq:
            return {'processed': 0, 'failed': 0}

        results = {'processed': 0, 'failed': 0}

        # Get failed events
        events = await self.dlq.get_failed_events()

        for event in events[:max_events]:
            success = await self.process_event(
                handler,
                event.event_type,
                event.event_data,
                event.event_id
            )

            if success:
                results['processed'] += 1
                # Remove from DLQ
                if event.event_id:
                    await self.dlq.remove_event(event.event_id)
            else:
                results['failed'] += 1

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics"""
        return {
            **self._metrics,
            'circuit_state': self.circuit_breaker.get_state()
        }