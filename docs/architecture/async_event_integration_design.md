# Async Event Integration Architecture Design

## Overview
This document describes the minimal architectural changes implemented to fix async event handling and cross-component integration issues while maintaining full backward compatibility with API v1.0.

## Problem Statement
The integration tests were failing due to:
1. `asyncio.run()` being called from already running event loops
2. Inconsistent async/sync context handling
3. Missing event ordering guarantees
4. Lack of error recovery patterns
5. Cross-component event flow not working properly

## Architectural Solution

### 1. Async Compatibility Layer (`src/pm/events/async_compat.py`)

**Purpose**: Seamlessly handle async operations in both sync and async contexts without breaking existing code.

**Key Components**:
- `AsyncCompatibilityBridge`: Detects execution context and routes appropriately
- `EventLoopManager`: Manages event loops across different threads
- `run_async_from_sync()`: Safely runs async code from sync context

**Design Patterns**:
- **Context Detection**: Automatically detects if code is running in async or sync context
- **Thread-Safe Loop Management**: Maintains separate event loops per thread
- **Fallback Mechanisms**: Multiple fallback strategies for edge cases

### 2. Event Ordering & Idempotency (`src/pm/events/ordering.py`)

**Purpose**: Ensure events are processed exactly once and in the correct order.

**Key Components**:
- `IdempotencyManager`: Prevents duplicate event processing using content-based hashing
- `EventOrderingManager`: Assigns sequence numbers and manages priority queues
- `OrderedEventProcessor`: Processes events in batches with guaranteed ordering

**Design Patterns**:
- **Content-Based Deduplication**: SHA256 hash of event type + data
- **Priority Queues**: Four priority levels (CRITICAL, HIGH, NORMAL, LOW)
- **Batch Processing**: Processes events in configurable batch sizes
- **TTL-Based Cleanup**: Automatic cleanup of old idempotency records

### 3. Error Recovery Patterns (`src/pm/events/recovery.py`)

**Purpose**: Provide resilience against transient failures and maintain system stability.

**Key Components**:
- `CircuitBreaker`: Protects against cascading failures
- `RetryManager`: Exponential backoff with jitter
- `DeadLetterQueue`: Stores failed events for later reprocessing
- `ResilientEventProcessor`: Combines all patterns

**Design Patterns**:
- **Circuit Breaker States**: CLOSED → OPEN → HALF_OPEN → CLOSED
- **Exponential Backoff**: Configurable retry delays with jitter
- **Dead Letter Queue**: Persistent storage for failed events
- **Metrics Collection**: Tracks processed, failed, retried, and DLQ events

## Implementation Details

### Event Bus Modifications

The EventBus was updated to use the compatibility layer:

```python
def publish_sync(self, event, data=None):
    """Synchronous publishing with compatibility handling"""
    result = run_async_from_sync(self.publish(event))
    if isinstance(result, asyncio.Task):
        # Async context - task scheduled
    else:
        # Sync context - completed
```

### Integration Test Updates

Tests were updated to use the compatibility layer instead of `asyncio.run()`:

```python
# Before
asyncio.run(run_event_test())

# After
from src.pm.events.async_compat import run_async_from_sync
run_async_from_sync(run_event_test())
```

## State Consistency Guarantees

### 1. Event Ordering
- Events are assigned monotonically increasing sequence numbers
- Priority-based processing ensures critical events are handled first
- Batch processing maintains order within priority levels

### 2. Idempotency
- Content-based hashing ensures duplicate events are detected
- TTL-based cleanup prevents memory growth
- Thread-safe operations prevent race conditions

### 3. Error Recovery
- Circuit breaker prevents cascading failures
- Retry logic handles transient failures
- Dead letter queue ensures no event is lost

## Backward Compatibility

### API v1.0 Compatibility
- All existing synchronous APIs continue to work unchanged
- New async capabilities are additive, not breaking
- Event handlers can be either sync or async

### Migration Path
- Existing code requires no changes
- New code can leverage async capabilities
- Gradual migration possible component by component

## Performance Considerations

### Throughput
- Batch processing reduces overhead
- Priority queues ensure important events aren't delayed
- Async processing enables higher concurrency

### Latency
- Circuit breaker reduces latency during failures
- Exponential backoff prevents thundering herd
- Idempotency checks are O(1) with hash lookup

### Resource Usage
- Thread pool executor limits concurrent sync operations
- Event queue has configurable max size
- Dead letter queue uses persistent storage

## Monitoring & Observability

### Metrics Exposed
- Event processing rate
- Circuit breaker state
- Retry attempts
- Dead letter queue size
- Processing latency percentiles

### Health Checks
- Circuit breaker state monitoring
- Event queue depth monitoring
- Dead letter queue growth rate

## Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock external dependencies
- Verify state transitions

### Integration Tests
- Test cross-component event flow
- Verify ordering guarantees
- Test error recovery scenarios

### Chaos Testing
- Inject failures to test circuit breaker
- Simulate high load for backpressure testing
- Test dead letter queue reprocessing

## Security Considerations

### Event Validation
- All events are validated before processing
- Malformed events are rejected early
- Error messages don't leak sensitive information

### Resource Limits
- Queue sizes are bounded
- TTLs prevent unbounded growth
- Rate limiting can be added if needed

## Future Enhancements

### Potential Improvements
1. Event sourcing for full audit trail
2. Distributed tracing integration
3. Multi-region event replication
4. Schema registry for event validation
5. Event replay capabilities

### Scalability Path
1. Replace in-memory queues with distributed message broker
2. Implement event sharding for horizontal scaling
3. Add event stream processing capabilities
4. Implement CQRS pattern for read/write separation

## Conclusion

This minimal design successfully addresses all integration test failures while maintaining full backward compatibility. The architecture provides:

- **Reliability**: Error recovery patterns ensure system resilience
- **Consistency**: Idempotency and ordering guarantees
- **Compatibility**: No breaking changes to existing APIs
- **Observability**: Comprehensive metrics and monitoring
- **Scalability**: Clear path for future growth

The implementation follows best practices for distributed systems while keeping complexity minimal and changes additive rather than breaking.