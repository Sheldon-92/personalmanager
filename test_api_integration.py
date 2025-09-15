#!/usr/bin/env python3
"""Test API server with integration logging

This script starts the API server and makes some test requests to demonstrate
integration logging in action with real components.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
import threading
import urllib.request

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.pm.api.server import PersonalManagerAPI
except ImportError as e:
    print(f"Import error: {e}")
    print("Running basic integration test instead...")


def make_test_requests():
    """Make test API requests"""
    print("📡 Making test API requests...")
    time.sleep(2)  # Wait for server to start

    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/api/v1/status",
        "/api/v1/tasks",
        "/api/v1/projects",
        "/api/v1/metrics",
        "/api/v1/reports/status"
    ]

    for endpoint in endpoints:
        try:
            url = f"{base_url}{endpoint}"
            print(f"  → GET {endpoint}")

            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read()
                if response.status == 200:
                    print(f"    ✅ {response.status}")
                else:
                    print(f"    ⚠️  {response.status}")

        except Exception as e:
            print(f"    ❌ Error: {e}")

        time.sleep(0.5)

    print("✅ API requests completed")


def test_with_real_api():
    """Test with real API server"""
    try:
        print("🚀 Starting API server test...")

        # Start server in a thread
        server_thread = threading.Thread(
            target=lambda: PersonalManagerAPI(port=8000).start(),
            daemon=True
        )
        server_thread.start()

        # Make test requests
        make_test_requests()

        print("🛑 Stopping server...")

    except Exception as e:
        print(f"❌ API server test failed: {e}")


def test_integration_logger_only():
    """Test just the integration logger functionality"""
    print("🧪 Testing integration logger functionality...")

    from src.pm.obs.integration_logger import get_integration_logger

    logger = get_integration_logger()

    # Simulate some API-like operations
    print("  📋 Simulating component interactions...")

    # API request simulation
    req_id = logger.start_request(event_type="API:TestEndpoint")
    logger.add_component_timing(req_id, "validation", 5.2)
    logger.add_component_timing(req_id, "processing", 12.8)
    logger.update_handler_status(req_id, "ok")
    logger.update_metrics_status(req_id, "write:ok")
    logger.complete_request(req_id)

    # Event processing simulation
    req_id = logger.start_request(event_type="Event:TestEvent")
    logger.add_component_timing(req_id, "event_handling", 8.3)
    logger.update_handler_status(req_id, "ok")
    logger.update_plugin_status(req_id, "run:ok")
    logger.update_metrics_status(req_id, "collect:ok")
    logger.complete_request(req_id)

    print("  ✅ Integration logger test completed")


async def main():
    """Main test function"""
    print("🔧 Integration Logging API Test")
    print("=" * 50)

    # Check if we can import API components
    try:
        from src.pm.api.server import PersonalManagerAPI
        print("✅ API components available - running full test")
        test_with_real_api()
    except ImportError:
        print("⚠️  API components not available - testing logger only")
        test_integration_logger_only()

    # Show the log file results
    from src.pm.obs.integration_logger import get_integration_logger
    logger = get_integration_logger()

    if logger.log_file.exists():
        print(f"\n📄 Integration log file: {logger.log_file}")

        with open(logger.log_file, 'r') as f:
            lines = f.readlines()

        # Count actual log entries (non-comment lines)
        log_entries = [line for line in lines if not line.startswith('#') and line.strip()]

        print(f"📊 Total log entries: {len(log_entries)}")

        if log_entries:
            print("\n🔍 Recent log entries:")
            for line in log_entries[-5:]:  # Show last 5 entries
                print(f"   {line.strip()}")

    print("\n🎯 Integration logging test completed!")


if __name__ == "__main__":
    asyncio.run(main())