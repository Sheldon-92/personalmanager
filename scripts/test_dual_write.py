#!/usr/bin/env python3
"""
Simple test script to demonstrate dual-write collection functionality
Collects metrics from both legacy and standardized endpoints and writes to JSONL
"""

import json
import time
import requests
from datetime import datetime, timezone
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8001"
OUTPUT_DIR = Path("/Users/sheldonzhao/programs/personal-manager/logs")
COLLECTION_INTERVAL = 30

def collect_and_write_metrics():
    """Collect from both endpoints and write to JSONL files"""
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        # Collect legacy metrics
        legacy_response = requests.get(f"{API_BASE}/metrics/legacy", timeout=10)
        legacy_response.raise_for_status()
        legacy_data = legacy_response.json()

        # Collect standardized metrics
        standard_response = requests.get(f"{API_BASE}/metrics/standard", timeout=10)
        standard_response.raise_for_status()
        standard_data = standard_response.json()

        # Write legacy metrics to JSONL
        legacy_entry = {
            "timestamp": timestamp,
            "format_type": "legacy",
            "metric_data": legacy_data.get("metrics", []),
            "collection_metadata": {
                "collection_time": timestamp,
                "response_time_ms": int(legacy_response.elapsed.total_seconds() * 1000),
                "endpoint": "/metrics/legacy",
                "status_code": legacy_response.status_code
            }
        }

        # Write standardized metrics to JSONL
        standard_entry = {
            "timestamp": timestamp,
            "format_type": "standardized",
            "metric_data": standard_data.get("metrics", []),
            "collection_metadata": {
                "collection_time": timestamp,
                "response_time_ms": int(standard_response.elapsed.total_seconds() * 1000),
                "endpoint": "/metrics/standard",
                "status_code": standard_response.status_code
            }
        }

        # Write to JSONL files
        today = datetime.now().strftime('%Y%m%d')
        legacy_file = OUTPUT_DIR / f"legacy_metrics_{today}.jsonl"
        standard_file = OUTPUT_DIR / f"standard_metrics_{today}.jsonl"

        with open(legacy_file, 'a') as f:
            f.write(json.dumps(legacy_entry) + '\n')

        with open(standard_file, 'a') as f:
            f.write(json.dumps(standard_entry) + '\n')

        # Perform basic comparison
        comparison = compare_metrics(legacy_data.get("metrics", []), standard_data.get("metrics", []))

        comparison_entry = {
            "timestamp": timestamp,
            "comparison_results": comparison,
            "summary": {
                "total_legacy_metrics": len(legacy_data.get("metrics", [])),
                "total_standard_metrics": len(standard_data.get("metrics", [])),
                "matches": len([r for r in comparison if r["status"] == "match"]),
                "mismatches": len([r for r in comparison if r["status"] == "mismatch"])
            }
        }

        comparison_file = OUTPUT_DIR / f"metric_comparison_{today}.jsonl"
        with open(comparison_file, 'a') as f:
            f.write(json.dumps(comparison_entry) + '\n')

        print(f"[{timestamp}] Collection successful: {len(legacy_data.get('metrics', []))} legacy, {len(standard_data.get('metrics', []))} standard")

        return True

    except Exception as e:
        error_entry = {
            "timestamp": timestamp,
            "error": str(e),
            "error_type": type(e).__name__
        }

        error_file = OUTPUT_DIR / f"collection_errors_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(error_file, 'a') as f:
            f.write(json.dumps(error_entry) + '\n')

        print(f"[{timestamp}] Collection failed: {e}")
        return False

def compare_metrics(legacy_metrics, standard_metrics):
    """Simple comparison between legacy and standardized metrics"""
    comparisons = []

    # Create mapping for standard metrics
    standard_lookup = {}
    for metric in standard_metrics:
        name = metric.get("name", "").replace("_", ".")
        standard_lookup[name] = metric

    for legacy_metric in legacy_metrics:
        legacy_name = legacy_metric.get("metric_name", "")
        legacy_value = legacy_metric.get("value")

        # Try to find matching standard metric
        if legacy_name in standard_lookup:
            standard_metric = standard_lookup[legacy_name]
            standard_value = standard_metric.get("value")

            # Compare values
            status = "match" if legacy_value == standard_value else "mismatch"
            difference = abs(legacy_value - standard_value) if isinstance(legacy_value, (int, float)) and isinstance(standard_value, (int, float)) else None

            comparisons.append({
                "legacy_name": legacy_name,
                "standard_name": standard_metric.get("name"),
                "legacy_value": legacy_value,
                "standard_value": standard_value,
                "status": status,
                "difference": difference
            })
        else:
            comparisons.append({
                "legacy_name": legacy_name,
                "standard_name": None,
                "legacy_value": legacy_value,
                "standard_value": None,
                "status": "missing_in_standard",
                "difference": None
            })

    return comparisons

def main():
    """Main collection loop"""
    print("Starting dual-write test collector...")
    print(f"API Base: {API_BASE}")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Collection Interval: {COLLECTION_INTERVAL}s")

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    collection_count = 0

    try:
        while collection_count < 3:  # Run 3 collection cycles for demo
            collection_count += 1
            print(f"\n--- Collection Cycle #{collection_count} ---")

            success = collect_and_write_metrics()

            if collection_count < 3:  # Don't sleep after last collection
                print(f"Waiting {COLLECTION_INTERVAL}s for next collection...")
                time.sleep(COLLECTION_INTERVAL)

    except KeyboardInterrupt:
        print("\nCollection interrupted by user")

    print(f"\nCompleted {collection_count} collection cycles")
    print("Check the following files for output:")
    today = datetime.now().strftime('%Y%m%d')
    print(f"  - {OUTPUT_DIR}/legacy_metrics_{today}.jsonl")
    print(f"  - {OUTPUT_DIR}/standard_metrics_{today}.jsonl")
    print(f"  - {OUTPUT_DIR}/metric_comparison_{today}.jsonl")

if __name__ == "__main__":
    main()