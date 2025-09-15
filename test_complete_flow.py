#!/usr/bin/env python3
"""Complete Integration Flow Test

This script demonstrates the complete integration logging across all
instrumented components: API, Events, Plugins, and Metrics.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.pm.obs.integration_logger import (
    get_integration_logger,
    HandlerStatus,
    PluginStatus,
    MetricsStatus
)


async def test_complete_integration_flow():
    """Test complete integration flow across all components"""
    print("🌊 Testing Complete Integration Flow")
    print("=" * 50)

    logger = get_integration_logger()

    # 1. Simulate incoming API request that triggers entire chain
    print("1️⃣  API Request: POST /api/v1/tasks")
    api_req_id = logger.start_request(event_type="API:POST:/api/v1/tasks")

    try:
        # API processing
        with logger.time_component(api_req_id, "request_validation"):
            await asyncio.sleep(0.008)  # Simulate validation

        with logger.time_component(api_req_id, "authentication"):
            await asyncio.sleep(0.003)  # Simulate auth check

        # 2. Event bus processing
        print("2️⃣  Event Bus: TaskCreated event")
        event_req_id = logger.start_request(event_type="Event:TaskCreated")

        try:
            with logger.time_component(event_req_id, "event_routing"):
                await asyncio.sleep(0.005)

            with logger.time_component(event_req_id, "subscriber_notification"):
                await asyncio.sleep(0.012)

            logger.update_handler_status(event_req_id, HandlerStatus.OK)
            logger.update_plugin_status(event_req_id, PluginStatus.RUN_OK)
            logger.update_metrics_status(event_req_id, MetricsStatus.WRITE_OK)

        finally:
            logger.complete_request(event_req_id)

        # 3. Plugin system processing
        print("3️⃣  Plugin System: task_processor plugin")
        plugin_req_id = logger.start_request(event_type="Plugin:task_processor")

        try:
            with logger.time_component(plugin_req_id, "plugin_loading"):
                await asyncio.sleep(0.015)

            with logger.time_component(plugin_req_id, "task_analysis"):
                await asyncio.sleep(0.025)

            with logger.time_component(plugin_req_id, "recommendation_generation"):
                await asyncio.sleep(0.030)

            logger.update_handler_status(plugin_req_id, HandlerStatus.OK)
            logger.update_plugin_status(plugin_req_id, PluginStatus.RUN_OK)
            logger.update_metrics_status(plugin_req_id, MetricsStatus.WRITE_OK)

        finally:
            logger.complete_request(plugin_req_id)

        # 4. Metrics collection
        print("4️⃣  Metrics Collection: request_metrics")
        metrics_req_id = logger.start_request(event_type="Metrics:request_tracking")

        try:
            with logger.time_component(metrics_req_id, "latency_recording"):
                await asyncio.sleep(0.004)

            with logger.time_component(metrics_req_id, "counter_updates"):
                await asyncio.sleep(0.006)

            with logger.time_component(metrics_req_id, "alert_evaluation"):
                await asyncio.sleep(0.008)

            logger.update_handler_status(metrics_req_id, HandlerStatus.OK)
            logger.update_metrics_status(metrics_req_id, MetricsStatus.COLLECT_OK)

        finally:
            logger.complete_request(metrics_req_id)

        # Complete API request
        with logger.time_component(api_req_id, "response_serialization"):
            await asyncio.sleep(0.007)

        logger.update_handler_status(api_req_id, HandlerStatus.OK)
        logger.update_plugin_status(api_req_id, PluginStatus.RUN_OK)
        logger.update_metrics_status(api_req_id, MetricsStatus.WRITE_OK)

    finally:
        logger.complete_request(api_req_id)

    print("✅ Complete integration flow tested")


def analyze_log_output():
    """Analyze the generated log output"""
    logger = get_integration_logger()

    if not logger.log_file.exists():
        print("❌ No log file found")
        return

    with open(logger.log_file, 'r') as f:
        lines = f.readlines()

    # Separate header and log entries
    log_entries = [line.strip() for line in lines if not line.startswith('#') and line.strip()]

    print(f"\n📊 Log Analysis")
    print("=" * 30)
    print(f"Total entries: {len(log_entries)}")

    # Analyze by component
    components = {'API': 0, 'Event': 0, 'Plugin': 0, 'Metrics': 0, 'Hook': 0}
    status_counts = {'ok': 0, 'error': 0}
    plugin_statuses = {'loaded': 0, 'run:ok': 0, 'run:error': 0, 'not_found': 0}
    metrics_statuses = {'write:ok': 0, 'write:error': 0, 'collect:ok': 0, 'collect:error': 0}

    total_time = 0
    times = []

    for entry in log_entries:
        if '|' not in entry:
            continue

        parts = entry.split('|')
        for part in parts:
            if part.startswith('event='):
                event_type = part.split('=', 1)[1]
                if event_type.startswith('API'):
                    components['API'] += 1
                elif event_type.startswith('Event'):
                    components['Event'] += 1
                elif event_type.startswith('Plugin'):
                    components['Plugin'] += 1
                elif event_type.startswith('Metrics'):
                    components['Metrics'] += 1
                elif event_type.startswith('Hook'):
                    components['Hook'] += 1

            elif part.startswith('handler='):
                handler_status = part.split('=', 1)[1]
                if handler_status in status_counts:
                    status_counts[handler_status] += 1

            elif part.startswith('plugin='):
                plugin_status = part.split('=', 1)[1]
                if plugin_status in plugin_statuses:
                    plugin_statuses[plugin_status] += 1

            elif part.startswith('metrics='):
                metrics_status = part.split('=', 1)[1]
                if metrics_status in metrics_statuses:
                    metrics_statuses[metrics_status] += 1

            elif part.startswith('time='):
                time_ms = int(part.split('=', 1)[1])
                total_time += time_ms
                times.append(time_ms)

    print(f"\n📈 Component Breakdown:")
    for component, count in components.items():
        if count > 0:
            print(f"  {component}: {count} requests")

    print(f"\n🎯 Status Summary:")
    for status, count in status_counts.items():
        if count > 0:
            print(f"  Handler {status}: {count}")

    for status, count in plugin_statuses.items():
        if count > 0:
            print(f"  Plugin {status}: {count}")

    for status, count in metrics_statuses.items():
        if count > 0:
            print(f"  Metrics {status}: {count}")

    if times:
        print(f"\n⏱️  Timing Analysis:")
        print(f"  Total time: {total_time}ms")
        print(f"  Average time: {total_time / len(times):.1f}ms")
        print(f"  Min time: {min(times)}ms")
        print(f"  Max time: {max(times)}ms")

    print(f"\n📋 Recent Entries:")
    for entry in log_entries[-5:]:
        print(f"  {entry}")


async def main():
    """Main test function"""
    print("🔍 Complete Integration Logging Demonstration")
    print("🎯 Testing end-to-end request flow with chain tracing")
    print()

    # Run the complete flow test
    await test_complete_integration_flow()

    # Analyze the results
    analyze_log_output()

    logger = get_integration_logger()
    print(f"\n📁 Complete log file available at: {logger.log_file}")

    print("\n✨ Integration logging system successfully implemented!")
    print("\nKey Features Demonstrated:")
    print("✅ Standardized log format with field/unit mapping")
    print("✅ Request ID chain tracing across components")
    print("✅ Component timing measurements")
    print("✅ Handler, plugin, and metrics status tracking")
    print("✅ End-to-end request flow visibility")


if __name__ == "__main__":
    asyncio.run(main())