# Observability Guide

## Overview

The PM Observability System provides comprehensive monitoring, logging, and metrics collection capabilities for the personal-manager application. This guide covers setup, usage, and best practices for maintaining system observability.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Applications                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │    PM    │  │   APIs   │  │  Agents  │      │
│  │   CLI    │  │          │  │          │      │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘      │
│        │             │             │            │
│        └─────────────┴─────────────┘            │
│                      │                          │
├──────────────────────┼──────────────────────────┤
│              Observability Layer                 │
│  ┌──────────────────────────────────────────┐  │
│  │         Structured Logging                │  │
│  │  - JSON format                            │  │
│  │  - Context propagation                    │  │
│  │  - Automatic rotation                     │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │         Metrics Collection                │  │
│  │  - Counters, Gauges, Histograms          │  │
│  │  - Latency percentiles (P50/P95/P99)     │  │
│  │  - Error rates & Cache hit rates         │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │         Alert Management                  │  │
│  │  - Threshold monitoring                   │  │
│  │  - Alert generation                       │  │
│  │  - Notification dispatch                  │  │
│  └──────────────────────────────────────────┘  │
├──────────────────────────────────────────────────┤
│                 Storage Layer                    │
│  ┌──────────────────────────────────────────┐  │
│  │  ~/.pm/logs/     │  ~/.pm/metrics/       │  │
│  │  - *.json logs   │  - snapshots          │  │
│  │  - Rotated files │  - Latest metrics     │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## Components

### 1. Structured Logging (`src/pm/obs/logging.py`)

#### Features
- **JSON Format**: All logs are structured as JSON for easy parsing
- **Context Propagation**: Thread-local context for request tracing
- **Automatic Rotation**: Log files rotate at 10MB with 5 backups
- **Performance Tracking**: Built-in timer context for operation timing

#### Usage

```python
from pm.obs.logging import get_logger

# Get a logger instance
logger = get_logger("pm.mymodule")

# Basic logging
logger.info("Operation started", user_id="user123", action="recommend")

# Set context for all subsequent logs in thread
logger.set_context(request_id="req-456", trace_id="trace-789")

# Log with automatic timing
with logger.timer("database_query"):
    # Your operation here
    result = perform_query()

# Error logging with exception
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exception=e)
```

#### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error events that might still allow the application to continue
- `CRITICAL`: Very severe error events that might cause the application to abort

### 2. Metrics Collection (`src/pm/obs/metrics.py`)

#### Metric Types

##### Counters
Always increasing values (e.g., total requests, errors)
```python
from pm.obs.metrics import get_metrics_registry

registry = get_metrics_registry()
registry.counter('total_requests').increment()
registry.counter('total_errors').increment()
```

##### Gauges
Values that can go up or down (e.g., memory usage, active connections)
```python
registry.gauge('active_connections').set(42)
registry.gauge('memory_usage_mb').set(512.3)
```

##### Histograms & Timers
Track distributions and percentiles
```python
# Record latency
timer = registry.timer('api_latency')
with timer.start_timer():
    process_request()

# Or use decorator
@registry.timer('function_latency').time
def my_function():
    # function logic
    pass
```

#### Core Metrics Tracked

| Metric | Type | Description | Unit |
|--------|------|-------------|------|
| `recommendation_latency` | Timer | Time to generate recommendations | ms |
| `api_response_time` | Timer | API endpoint response time | ms |
| `event_processing_latency` | Timer | Event processing duration | ms |
| `total_requests` | Counter | Total number of requests | count |
| `total_errors` | Counter | Total number of errors | count |
| `cache_hits` | Counter | Cache hit count | count |
| `cache_misses` | Counter | Cache miss count | count |
| `disk_usage_percent` | Gauge | Disk usage percentage | % |
| `memory_usage_mb` | Gauge | Memory usage | MB |
| `cpu_usage_percent` | Gauge | CPU usage percentage | % |

#### Derived Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| `error_rate` | `total_errors / total_requests` | Percentage of failed requests |
| `cache_hit_rate` | `cache_hits / (cache_hits + cache_misses)` | Cache effectiveness |

### 3. Alert Thresholds

The system monitors key metrics and generates alerts when thresholds are exceeded:

| Alert | Threshold | Severity | Description |
|-------|-----------|----------|-------------|
| High Error Rate | > 5% | HIGH | Too many requests failing |
| High P99 Latency | > 1000ms | HIGH | Slow response times |
| Low Cache Hit Rate | < 50% | MEDIUM | Cache underperforming |
| High Disk Usage | > 90% | CRITICAL | Running out of disk space |

## CLI Commands

### Generate Metrics Snapshot
```bash
python -m pm.obs.metrics --snapshot
```
Output: Creates timestamped snapshot in `~/.pm/metrics/`

### View Metrics Summary
```bash
python -m pm.obs.metrics --summary
```
Output: JSON summary with key metrics and alerts

### Simulate Metrics (Testing)
```bash
python -m pm.obs.metrics --simulate --snapshot
```
Generates sample metrics for testing dashboards and alerts

## Integration Examples

### 1. Instrumenting a Function

```python
from pm.obs.logging import get_logger, log_performance
from pm.obs.metrics import get_metrics_registry

logger = get_logger(__name__)
registry = get_metrics_registry()

@log_performance  # Automatic logging
def process_recommendation(user_id: str):
    timer = registry.timer('recommendation_latency')

    with timer.start_timer():
        logger.info("Processing recommendation", user_id=user_id)

        try:
            # Your logic here
            result = generate_recommendation(user_id)

            registry.counter('total_requests').increment()
            logger.info("Recommendation generated",
                       user_id=user_id,
                       items=len(result))

            return result

        except Exception as e:
            registry.counter('total_errors').increment()
            logger.error("Recommendation failed",
                        exception=e,
                        user_id=user_id)
            raise
```

### 2. Cache Instrumentation

```python
def get_from_cache(key: str):
    registry = get_metrics_registry()

    value = cache.get(key)
    if value is not None:
        registry.counter('cache_hits').increment()
    else:
        registry.counter('cache_misses').increment()

    return value
```

### 3. Background Monitoring

```python
import time
import threading
from pm.obs.metrics import get_metrics_registry

def monitor_system():
    registry = get_metrics_registry()

    while True:
        # Collect system metrics
        registry.collect_system_metrics()

        # Check for alerts
        alerts = registry.check_alerts()
        for alert in alerts:
            logger.warning("Alert triggered", **alert)

        # Save snapshot every 5 minutes
        registry.save_snapshot()
        time.sleep(300)

# Start monitoring in background
monitor_thread = threading.Thread(target=monitor_system, daemon=True)
monitor_thread.start()
```

## File Locations

### Logs
- **Location**: `~/.pm/logs/`
- **Format**: JSON lines
- **Rotation**: 10MB max, 5 backups
- **Files**:
  - `{logger_name}.json` - Current log
  - `{logger_name}.json.1-5` - Rotated logs

### Metrics
- **Location**: `~/.pm/metrics/`
- **Format**: JSON
- **Files**:
  - `metrics_snapshot_YYYYMMDD_HHMMSS.json` - Timestamped snapshots
  - `latest_snapshot.json` - Most recent snapshot

## Performance Considerations

### Low Overhead Design
- **Async writes**: Log writes are buffered
- **Sampling**: Histograms use reservoir sampling (max 10,000 samples)
- **Lazy evaluation**: Metrics calculated on-demand
- **Thread-safe**: All operations are thread-safe with minimal locking

### Resource Usage
- **CPU**: < 2% overhead for normal operations
- **Memory**: ~10MB for metrics storage
- **Disk I/O**: Batched writes, automatic rotation
- **Network**: Local file storage only (no external dependencies)

## Best Practices

### 1. Logging
- Use structured fields instead of string formatting
- Set request context early in request lifecycle
- Include relevant identifiers (user_id, request_id, etc.)
- Use appropriate log levels

### 2. Metrics
- Increment counters for discrete events
- Use timers for operation durations
- Record all operations, not just successful ones
- Name metrics consistently: `{component}_{operation}_{unit}`

### 3. Alerts
- Review and tune thresholds based on actual data
- Implement gradual degradation for non-critical alerts
- Log alert state changes for audit trail
- Consider time-of-day and day-of-week patterns

### 4. Debugging
- Correlate logs and metrics using timestamps
- Use request_id/trace_id for distributed tracing
- Keep recent snapshots for comparison
- Monitor trends, not just absolute values

## Troubleshooting

### High Error Rate
1. Check recent logs for error patterns
2. Review recent code changes
3. Verify external dependencies
4. Check system resources

### High Latency
1. Review timer metrics for specific operations
2. Check cache hit rates
3. Monitor system CPU and memory
4. Profile slow operations

### Missing Metrics
1. Verify metric registration in code
2. Check if application is running
3. Review logs for metric collection errors
4. Ensure storage permissions

### Storage Issues
1. Check disk space: `df -h ~/.pm/`
2. Review rotation settings
3. Clean old snapshots if needed
4. Verify file permissions

## Dashboard Access

The monitoring dashboard can be accessed at:
- **Local File**: `docs/obs/dashboard.html`
- **Auto-refresh**: Opens in browser with 30-second refresh
- **Metrics Source**: Reads from `~/.pm/metrics/latest_snapshot.json`

## Future Enhancements

### Planned Features
- [ ] Remote metric aggregation
- [ ] Custom alert rules DSL
- [ ] Metric anomaly detection
- [ ] Distributed tracing support
- [ ] Grafana integration
- [ ] Webhook notifications
- [ ] Performance profiling
- [ ] Automatic baseline calculation

### Integration Points
- OpenTelemetry export
- Prometheus scraping endpoint
- CloudWatch metrics
- Datadog APM
- New Relic integration

## Summary

The PM Observability System provides:
- **Structured JSON logging** with context propagation
- **Comprehensive metrics** with percentile tracking
- **Automatic alerting** based on configurable thresholds
- **Local storage** with rotation and cleanup
- **Low overhead** (< 5% performance impact)
- **Easy integration** with decorators and context managers

For questions or issues, check the logs at `~/.pm/logs/` or run `python -m pm.obs.metrics --summary` for current system status.