#!/usr/bin/env python3
"""Test script for integration logging system

This script demonstrates the integration logging by simulating
various component interactions and generating sample log entries.
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.pm.obs.integration_logger import (
    get_integration_logger,
    trace_api_request,
    trace_event_processing,
    trace_plugin_operation,
    trace_metrics_collection,
    HandlerStatus,
    PluginStatus,
    MetricsStatus
)


async def simulate_api_requests():
    """Simulate various API requests"""
    print("🌐 Simulating API requests...")

    # Simulate successful task retrieval
    with trace_api_request("/api/v1/tasks") as req_id:
        logger = get_integration_logger()
        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

        # Simulate some processing time
        await asyncio.sleep(0.025)

    # Simulate project API call with plugin interaction
    with trace_api_request("/api/v1/projects") as req_id:
        logger = get_integration_logger()

        # Simulate data processing
        with logger.time_component(req_id, "data_processing"):
            await asyncio.sleep(0.015)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_plugin_status(req_id, PluginStatus.LOADED)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

    # Simulate error scenario
    with trace_api_request("/api/v1/invalid") as req_id:
        logger = get_integration_logger()
        logger.update_handler_status(req_id, HandlerStatus.ERROR)
        logger.update_metrics_status(req_id, MetricsStatus.COLLECT_ERROR)


async def simulate_event_processing():
    """Simulate event bus operations"""
    print("📡 Simulating event processing...")

    # File change event
    with trace_event_processing("FileChange") as req_id:
        logger = get_integration_logger()

        with logger.time_component(req_id, "event_validation"):
            await asyncio.sleep(0.008)

        with logger.time_component(req_id, "handler_execution"):
            await asyncio.sleep(0.012)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_plugin_status(req_id, PluginStatus.NOT_FOUND)
        logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

    # Task creation event with plugin
    with trace_event_processing("TaskCreate") as req_id:
        logger = get_integration_logger()

        with logger.time_component(req_id, "event_processing"):
            await asyncio.sleep(0.020)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_plugin_status(req_id, PluginStatus.RUN_OK)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)


async def simulate_plugin_operations():
    """Simulate plugin loading and execution"""
    print("🔌 Simulating plugin operations...")

    # Plugin loading
    with trace_plugin_operation("report_exporter") as req_id:
        logger = get_integration_logger()

        with logger.time_component(req_id, "plugin_discovery"):
            await asyncio.sleep(0.005)

        with logger.time_component(req_id, "plugin_validation"):
            await asyncio.sleep(0.010)

        with logger.time_component(req_id, "plugin_initialization"):
            await asyncio.sleep(0.015)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_plugin_status(req_id, PluginStatus.LOADED)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

    # Plugin execution
    with trace_plugin_operation("custom_recommender") as req_id:
        logger = get_integration_logger()

        with logger.time_component(req_id, "algorithm_execution"):
            await asyncio.sleep(0.030)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_plugin_status(req_id, PluginStatus.RUN_OK)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)

    # Failed plugin load
    with trace_plugin_operation("missing_plugin") as req_id:
        logger = get_integration_logger()
        logger.update_handler_status(req_id, HandlerStatus.ERROR)
        logger.update_plugin_status(req_id, PluginStatus.RUN_ERROR)


async def simulate_metrics_operations():
    """Simulate metrics collection"""
    print("📊 Simulating metrics operations...")

    # System metrics collection
    with trace_metrics_collection("system_metrics") as req_id:
        logger = get_integration_logger()

        with logger.time_component(req_id, "cpu_collection"):
            await asyncio.sleep(0.012)

        with logger.time_component(req_id, "memory_collection"):
            await asyncio.sleep(0.008)

        with logger.time_component(req_id, "disk_collection"):
            await asyncio.sleep(0.005)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_metrics_status(req_id, MetricsStatus.COLLECT_OK)

    # Metrics snapshot save
    with trace_metrics_collection("snapshot_save") as req_id:
        logger = get_integration_logger()

        with logger.time_component(req_id, "snapshot_generation"):
            await asyncio.sleep(0.018)

        with logger.time_component(req_id, "file_write"):
            await asyncio.sleep(0.010)

        logger.update_handler_status(req_id, HandlerStatus.OK)
        logger.update_metrics_status(req_id, MetricsStatus.WRITE_OK)


def simulate_complex_request_chain():
    """Simulate a complex request that goes through multiple components"""
    print("🔗 Simulating complex request chain...")

    logger = get_integration_logger()

    # Start with an API request
    api_req_id = logger.start_request(event_type="API:ComplexOperation")

    try:
        # Simulate API processing
        with logger.time_component(api_req_id, "api_validation"):
            time.sleep(0.005)

        # Trigger event processing
        event_req_id = logger.start_request(event_type="Event:DataProcess")
        try:
            with logger.time_component(event_req_id, "event_handling"):
                time.sleep(0.010)

            logger.update_handler_status(event_req_id, HandlerStatus.OK)
            logger.update_plugin_status(event_req_id, PluginStatus.RUN_OK)
            logger.update_metrics_status(event_req_id, MetricsStatus.WRITE_OK)
        finally:
            logger.complete_request(event_req_id)

        # Trigger plugin operation
        plugin_req_id = logger.start_request(event_type="Plugin:DataTransform")
        try:
            with logger.time_component(plugin_req_id, "plugin_execution"):
                time.sleep(0.020)

            logger.update_handler_status(plugin_req_id, HandlerStatus.OK)
            logger.update_plugin_status(plugin_req_id, PluginStatus.RUN_OK)
            logger.update_metrics_status(plugin_req_id, MetricsStatus.WRITE_OK)
        finally:
            logger.complete_request(plugin_req_id)

        # Final metrics collection
        metrics_req_id = logger.start_request(event_type="Metrics:FinalCollect")
        try:
            with logger.time_component(metrics_req_id, "metrics_aggregation"):
                time.sleep(0.008)

            logger.update_handler_status(metrics_req_id, HandlerStatus.OK)
            logger.update_metrics_status(metrics_req_id, MetricsStatus.COLLECT_OK)
        finally:
            logger.complete_request(metrics_req_id)

        # Complete main API request
        logger.update_handler_status(api_req_id, HandlerStatus.OK)
        logger.update_plugin_status(api_req_id, PluginStatus.RUN_OK)
        logger.update_metrics_status(api_req_id, MetricsStatus.WRITE_OK)

    finally:
        logger.complete_request(api_req_id)


async def main():
    """Main test function"""
    print("🚀 Starting Integration Logging Test")
    print("=" * 60)

    # Initialize logger
    logger = get_integration_logger()
    print(f"📁 Log file: {logger.log_file}")
    print()

    # Run various simulations
    await simulate_api_requests()
    await asyncio.sleep(0.1)

    await simulate_event_processing()
    await asyncio.sleep(0.1)

    await simulate_plugin_operations()
    await asyncio.sleep(0.1)

    await simulate_metrics_operations()
    await asyncio.sleep(0.1)

    # Run synchronous complex chain
    simulate_complex_request_chain()

    print("\n✅ Integration logging test completed!")
    print(f"📄 Check the log file at: {logger.log_file}")

    # Show some sample log entries
    if logger.log_file.exists():
        print("\n📋 Sample log entries:")
        print("-" * 40)
        with open(logger.log_file, 'r') as f:
            lines = f.readlines()
            # Show header and first few actual log entries (skip header comments)
            header_lines = []
            log_lines = []
            for line in lines:
                if line.startswith('#') or line.strip() == '':
                    header_lines.append(line.rstrip())
                else:
                    log_lines.append(line.rstrip())

            # Show first few header lines
            for line in header_lines[:5]:
                print(line)

            if log_lines:
                print("\nSample log entries:")
                for line in log_lines[-10:]:  # Show last 10 entries
                    print(line)

    print(f"\n🎯 Total log entries generated: {len(log_lines) if 'log_lines' in locals() else 'N/A'}")


if __name__ == "__main__":
    asyncio.run(main())