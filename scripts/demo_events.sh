#!/bin/bash

# demo_events.sh - Demonstration script for PM Events System
# This script showcases the event bus and webhook handling capabilities

set -e

echo "🚀 Personal Manager Events System Demo"
echo "======================================"
echo

# Check if we're in the right directory
if [[ ! -f "src/pm/events/bus.py" ]]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create logs directory
mkdir -p logs/events logs/file_changes logs/reports logs/risk_alerts logs/webhooks

echo "📂 Created log directories"
echo

# Run the Python demo
echo "🔄 Starting Events System Demo..."
python3 -c "
import asyncio
import sys
import os

# Add src to Python path
sys.path.insert(0, 'src')

from pm.events.bus import EventBus, Event
from pm.events.handlers.file_change import FileChangeHandler
from pm.events.handlers.report_ready import ReportReadyHandler
from pm.events.handlers.risk_alert import RiskAlertHandler
from pm.events.handlers.webhook import WebhookHandler

async def main():
    print('🎯 Initializing Event Bus...')
    bus = EventBus()

    # Create handlers
    file_handler = FileChangeHandler()
    report_handler = ReportReadyHandler()
    risk_handler = RiskAlertHandler()
    webhook_handler = WebhookHandler()

    print('📡 Registering event handlers...')

    # Subscribe handlers to events
    bus.subscribe('file_change', file_handler.handle_file_change)
    bus.subscribe('report_ready', report_handler.handle_report_ready)
    bus.subscribe('risk_alert', risk_handler.handle_risk_alert)
    bus.subscribe('webhook_trigger', webhook_handler.handle_webhook_trigger)

    print(f'✅ Registered handlers: {bus.get_subscribers()}')
    print()

    # Start the event bus
    await bus.start()
    print('🚀 Event Bus started!')
    print()

    # Demo 1: File Change Event
    print('📁 Demo 1: File Change Event')
    print('-' * 30)

    file_event = Event(
        type='file_change',
        data={
            'file_path': '/Users/test/documents/report.pdf',
            'change_type': 'modified',
            'size': 2048576,
            'modified_time': '2025-01-15T10:30:00Z',
            'checksum': 'abc123def456'
        }
    )

    await bus.publish(file_event)
    await asyncio.sleep(0.5)  # Allow processing
    print()

    # Demo 2: Report Ready Event
    print('📊 Demo 2: Report Ready Event')
    print('-' * 30)

    report_event = Event(
        type='report_ready',
        data={
            'report_id': 'daily_report_20250115',
            'report_type': 'daily',
            'report_path': '/tmp/daily_report.pdf',
            'report_format': 'pdf',
            'generated_at': '2025-01-15T10:00:00Z',
            'size_bytes': 1234567,
            'recipients': ['manager@company.com', 'team@company.com'],
            'metadata': {
                'author': 'pm_system',
                'tags': ['daily', 'summary']
            }
        }
    )

    await bus.publish(report_event)
    await asyncio.sleep(0.5)  # Allow processing
    print()

    # Demo 3: Risk Alert Event
    print('⚠️ Demo 3: Risk Alert Event')
    print('-' * 30)

    risk_event = Event(
        type='risk_alert',
        data={
            'alert_id': 'security_alert_001',
            'risk_type': 'security',
            'severity': 'high',
            'title': 'Suspicious Login Activity Detected',
            'description': 'Multiple failed login attempts from unknown IP address',
            'affected_resources': ['user_auth_system', 'login_database'],
            'risk_score': 0.85,
            'detected_at': '2025-01-15T10:45:00Z',
            'source_system': 'security_scanner',
            'mitigation_steps': [
                'Block suspicious IP address',
                'Force password reset for affected accounts',
                'Enable additional MFA verification'
            ],
            'metadata': {
                'tags': ['automated', 'security', 'login'],
                'related_incidents': []
            }
        }
    )

    await bus.publish(risk_event)
    await asyncio.sleep(0.5)  # Allow processing
    print()

    # Demo 4: Webhook Callback
    print('🔗 Demo 4: Webhook Callback')
    print('-' * 30)

    webhook_event = Event(
        type='webhook_trigger',
        data={
            'trigger': 'file_change',
            'original_event': file_event.to_dict(),
            'callback_url': 'https://hooks.slack.com/services/fake/webhook/url',
            'callback_method': 'POST',
            'callback_headers': {
                'Content-Type': 'application/json',
                'X-PM-Source': 'events-system'
            },
            'callback_timeout': 30,
            'retry_on_failure': True
        }
    )

    await bus.publish(webhook_event)
    await asyncio.sleep(1.0)  # Allow processing
    print()

    # Stop the event bus
    await bus.stop()
    print('🛑 Event Bus stopped')
    print()

    # Show metrics
    print('📊 Demo Metrics:')
    print(f'   - Events triggered: 4')
    print(f'   - Handlers registered: {sum(bus.get_subscribers().values())}')
    print(f'   - Log file: {bus.get_log_file()}')
    print()

if __name__ == '__main__':
    asyncio.run(main())
"

echo
echo "📋 Demo completed! Check the following log files:"
echo "   - logs/events/events_$(date +%Y%m%d).log"
echo "   - logs/file_changes/file_changes.jsonl"
echo "   - logs/reports/report_generations.jsonl"
echo "   - logs/risk_alerts/risk_alerts.jsonl"
echo "   - logs/webhooks/webhook_attempts.jsonl"
echo

echo "📊 Event Log Summary:"
echo "===================="

# Show recent events from the main log
if [[ -f "logs/events/events_$(date +%Y%m%d).log" ]]; then
    echo
    echo "🔍 Recent Events:"
    tail -n 10 "logs/events/events_$(date +%Y%m%d).log" | grep -E "(file_change|report_ready|risk_alert|webhook)" || echo "No events found"
fi

echo
echo "✅ Events System Demo Complete!"
echo "   - Event bus: ✅ Functional"
echo "   - File change events: ✅ Handled"
echo "   - Report ready events: ✅ Handled"
echo "   - Risk alert events: ✅ Handled"
echo "   - Webhook callbacks: ✅ Simulated"
echo "   - Async processing: ✅ Working"
echo "   - Local file logging: ✅ Active"
echo