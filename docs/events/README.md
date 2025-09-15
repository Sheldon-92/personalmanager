# Personal Manager Events System

The Personal Manager Events System provides a robust, asynchronous event bus with webhook handling capabilities. This system enables decoupled communication between components and external integrations.

## 🏗 Architecture

### Core Components

1. **EventBus** (`src/pm/events/bus.py`) - Core event distribution system
2. **Event Handlers** (`src/pm/events/handlers/`) - Specialized event processors
3. **Webhook Handler** - External callback management
4. **Local Logging** - File-based event persistence

### Event Flow

```
Event Source → EventBus → Event Handler → Action/Webhook
     ↓
  Log Files (JSON Lines format)
```

## 📡 Event Bus API

### Basic Usage

```python
from pm.events.bus import EventBus, Event

# Create event bus
bus = EventBus()

# Subscribe to events
bus.subscribe('file_change', my_handler)

# Start processing
await bus.start()

# Publish events
await bus.publish('file_change', {'file_path': '/path/to/file'})

# Stop processing
await bus.stop()
```

### Event Structure

```python
@dataclass
class Event:
    type: str                    # Event type identifier
    data: Dict[str, Any]        # Event payload
    timestamp: float            # Unix timestamp
    event_id: str              # Unique event identifier
    source: str                # Event source system
```

## 🎯 Supported Event Types

### 1. File Change Events (`file_change`)

Triggered when files are created, modified, or deleted.

**Event Data Format:**
```json
{
  "file_path": "/path/to/file.txt",
  "change_type": "created|modified|deleted",
  "size": 1234,
  "modified_time": "2025-01-15T10:00:00Z",
  "checksum": "optional_md5_hash"
}
```

**Handler Features:**
- Validates file existence
- Logs changes to `logs/file_changes/file_changes.jsonl`
- Triggers webhook callbacks
- Processes by change type (create/modify/delete)

### 2. Report Ready Events (`report_ready`)

Triggered when reports are generated and ready for distribution.

**Event Data Format:**
```json
{
  "report_id": "daily_report_20250115",
  "report_type": "daily|weekly|monthly|custom",
  "report_path": "/path/to/report.pdf",
  "report_format": "pdf|html|json",
  "generated_at": "2025-01-15T10:00:00Z",
  "size_bytes": 1234567,
  "recipients": ["user1@example.com", "user2@example.com"],
  "metadata": {
    "author": "pm_system",
    "tags": ["daily", "summary"]
  }
}
```

**Handler Features:**
- Report validation (file existence, format verification)
- Auto-distribution to recipients
- Metadata generation and storage
- Webhook notifications
- Logging to `logs/reports/report_generations.jsonl`

### 3. Risk Alert Events (`risk_alert`)

Triggered when security, performance, or compliance risks are detected.

**Event Data Format:**
```json
{
  "alert_id": "security_alert_001",
  "risk_type": "security|performance|compliance|financial",
  "severity": "low|medium|high|critical",
  "title": "Brief alert description",
  "description": "Detailed alert information",
  "affected_resources": ["resource1", "resource2"],
  "risk_score": 0.85,
  "detected_at": "2025-01-15T10:00:00Z",
  "source_system": "security_scanner",
  "mitigation_steps": ["action1", "action2"],
  "metadata": {
    "tags": ["security", "automated"],
    "related_incidents": ["inc123"]
  }
}
```

**Handler Features:**
- Severity-based processing (critical → immediate action)
- Auto-escalation for high-risk alerts
- Mitigation step execution
- Risk dashboard updates
- Multi-level webhook notifications
- Logging to `logs/risk_alerts/risk_alerts.jsonl`

## 🔗 Webhook System

### Outgoing Webhooks

The system can send HTTP callbacks to external services when events occur.

**Configuration:**
```python
# Environment variables
WEBHOOK_SIGNATURE_SECRET=your_secret_key
FILE_CHANGE_WEBHOOK_URL=https://your-service.com/webhooks/files
REPORT_READY_WEBHOOK_URL=https://your-service.com/webhooks/reports
CRITICAL_ALERT_WEBHOOK_URL=https://your-service.com/webhooks/critical
```

**Webhook Payload Format:**
```json
{
  "event_type": "file_change",
  "timestamp": 1642248000,
  "event_id": "uuid-string",
  "data": { /* original event data */ },
  "source": "personal-manager",
  "signature": "sha256=computed_hmac_signature"
}
```

**Security Features:**
- HMAC-SHA256 signature verification
- Configurable timeout and retries
- Exponential backoff for failures
- Request logging and monitoring

### Incoming Webhooks

The system can receive and process webhooks from external services.

```python
webhook_handler = WebhookHandler()

# Process incoming webhook
success = await webhook_handler.handle_incoming_webhook(
    payload=request_body,
    signature=request.headers.get('X-Webhook-Signature'),
    headers=dict(request.headers)
)
```

## 📊 Logging and Monitoring

### Log Files

All events are logged to structured files for auditing and debugging:

- **Main Events:** `logs/events/events_YYYYMMDD.log`
- **File Changes:** `logs/file_changes/file_changes.jsonl`
- **Reports:** `logs/reports/report_generations.jsonl`
- **Risk Alerts:** `logs/risk_alerts/risk_alerts.jsonl`
- **Webhooks:** `logs/webhooks/webhook_attempts.jsonl`

### Log Format

Events are logged in JSON Lines format for easy parsing:

```json
{"timestamp": 1642248000, "event_id": "uuid", "type": "file_change", "data": {...}}
{"timestamp": 1642248001, "event_id": "uuid", "type": "report_ready", "data": {...}}
```

### Metrics

The system provides runtime metrics:

```python
# Get subscriber counts
subscribers = bus.get_subscribers()
# {'file_change': 2, 'report_ready': 1, 'risk_alert': 1}

# Get log file location
log_file = bus.get_log_file()
```

## 🚀 Quick Start

### 1. Run the Demo

```bash
# From project root
bash scripts/demo_events.sh
```

This demonstrates all three event types and webhook functionality.

### 2. Basic Integration

```python
import asyncio
from pm.events.bus import get_event_bus
from pm.events.handlers import FileChangeHandler

async def setup_events():
    # Get global event bus
    bus = get_event_bus()

    # Create and register handlers
    file_handler = FileChangeHandler()
    bus.subscribe('file_change', file_handler.handle_file_change)

    # Start processing
    await bus.start()

    # Publish an event
    await bus.publish('file_change', {
        'file_path': '/tmp/test.txt',
        'change_type': 'created',
        'size': 1024
    })

# Run the setup
asyncio.run(setup_events())
```

### 3. Custom Event Handler

```python
async def my_custom_handler(event):
    print(f"Received {event.type}: {event.data}")

    # Your custom processing logic here
    if event.type == 'file_change':
        # Handle file changes
        pass

# Subscribe to events
bus = get_event_bus()
bus.subscribe('file_change', my_custom_handler)
```

## ⚙️ Configuration

### Environment Variables

```bash
# Webhook configuration
WEBHOOK_SIGNATURE_SECRET=your_secret_key

# Event-specific webhook URLs
FILE_CHANGE_WEBHOOK_URL=https://example.com/webhooks/files
REPORT_READY_WEBHOOK_URL=https://example.com/webhooks/reports
CRITICAL_ALERT_WEBHOOK_URL=https://example.com/webhooks/critical
HIGH_ALERT_WEBHOOK_URL=https://example.com/webhooks/high
MEDIUM_ALERT_WEBHOOK_URL=https://example.com/webhooks/medium
LOW_ALERT_WEBHOOK_URL=https://example.com/webhooks/low
DEFAULT_RISK_WEBHOOK_URL=https://example.com/webhooks/risk
```

### Handler Configuration

```python
# Customize handlers during initialization
file_handler = FileChangeHandler(log_changes=True)
report_handler = ReportReadyHandler(auto_distribute=False)
risk_handler = RiskAlertHandler(escalation_enabled=True)
webhook_handler = WebhookHandler(max_retries=5)
```

## 🔧 Advanced Usage

### Custom Event Types

```python
# Define custom event handler
async def handle_deployment(event):
    data = event.data
    print(f"Deployment {data['status']}: {data['service']}")

# Register custom handler
bus.subscribe('deployment', handle_deployment)

# Publish custom event
await bus.publish('deployment', {
    'service': 'api-gateway',
    'status': 'success',
    'version': '1.2.3'
})
```

### Event Filtering

```python
async def filtered_handler(event):
    # Only process high-priority events
    if event.data.get('priority') == 'high':
        await process_high_priority_event(event)

bus.subscribe('custom_event', filtered_handler)
```

### Batch Event Processing

```python
# Process multiple events
events = [
    Event('file_change', {'file_path': '/tmp/file1.txt'}),
    Event('file_change', {'file_path': '/tmp/file2.txt'}),
    Event('file_change', {'file_path': '/tmp/file3.txt'})
]

for event in events:
    await bus.publish(event)
```

## 🐛 Troubleshooting

### Common Issues

1. **Events not processing**: Ensure `bus.start()` is called
2. **Handler not triggered**: Check subscription with `bus.get_subscribers()`
3. **Webhook failures**: Check URL accessibility and signature secrets
4. **Log files missing**: Verify write permissions in logs directory

### Debug Mode

```python
import logging

# Enable debug logging
logging.getLogger('pm.events').setLevel(logging.DEBUG)

# Check handler registrations
print(f"Registered handlers: {bus.get_subscribers()}")

# Monitor event queue
print(f"Queue size: {bus._event_queue.qsize()}")
```

### Performance Considerations

- **High Volume**: Consider implementing event batching
- **Long Processing**: Use async handlers to avoid blocking
- **Memory Usage**: Monitor log file sizes and implement rotation
- **Network Issues**: Configure appropriate webhook timeouts

## 📚 API Reference

### EventBus Methods

- `subscribe(event_type, handler)` - Register event handler
- `unsubscribe(event_type, handler)` - Remove event handler
- `publish(event, data=None)` - Publish event (async)
- `publish_sync(event, data=None)` - Publish event (sync)
- `start()` - Start event processing
- `stop()` - Stop event processing
- `get_subscribers()` - Get handler counts
- `get_log_file()` - Get current log file path

### Event Methods

- `to_dict()` - Convert to dictionary
- `to_json()` - Convert to JSON string

### WebhookHandler Methods

- `handle_webhook_trigger(event)` - Process outgoing webhook
- `handle_incoming_webhook(payload, signature, headers)` - Process incoming webhook
- `verify_webhook_signature(payload, signature)` - Verify HMAC signature

---

## 📄 License

This events system is part of the Personal Manager project. See project license for details.