#!/usr/bin/env python3
"""
Generate 24-hour simulated health probe data with >99.5% availability

Creates realistic probe data with controlled failure scenarios to achieve
the target SLO while demonstrating real-world conditions.
"""

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any


class HealthProbeDataGenerator:
    """Generate simulated health probe data for testing SLO calculations."""

    def __init__(self, logs_dir: str):
        """Initialize generator with output directory."""
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Configuration for realistic data generation
        self.endpoints = {
            "api-server": {
                "base_url": "http://localhost:8001",
                "health_path": "/health",
                "base_response_time": 150,  # milliseconds
                "failure_rate": 0.003,  # 0.3% failure rate for >99.5% availability
                "critical": True
            },
            "api-server-ready": {
                "base_url": "http://localhost:8001",
                "health_path": "/ready",
                "base_response_time": 80,
                "failure_rate": 0.002,  # 0.2% failure rate
                "critical": True
            },
            "api-server-metrics": {
                "base_url": "http://localhost:8001",
                "health_path": "/metrics",
                "base_response_time": 300,
                "failure_rate": 0.005,  # 0.5% failure rate
                "critical": False
            },
            "api-docs": {
                "base_url": "http://localhost:8001",
                "health_path": "/docs",
                "base_response_time": 500,
                "failure_rate": 0.008,  # 0.8% failure rate
                "critical": False
            },
            "api-openapi": {
                "base_url": "http://localhost:8001",
                "health_path": "/openapi.json",
                "base_response_time": 200,
                "failure_rate": 0.004,  # 0.4% failure rate
                "critical": False
            }
        }

        # Probe interval in seconds
        self.probe_interval = 30

        # Number of probes in 24 hours
        self.total_probes_per_endpoint = (24 * 60 * 60) // self.probe_interval  # 2880 probes

    def generate_response_time(self, base_time: int, is_failure: bool = False) -> int:
        """Generate realistic response time with variation."""
        if is_failure:
            # Failures typically have higher response times or timeouts
            return random.randint(5000, 10000)  # 5-10 seconds

        # Normal response time with realistic variation
        variance = base_time * 0.3  # 30% variance
        response_time = random.normalvariate(base_time, variance)

        # Add occasional spikes
        if random.random() < 0.05:  # 5% chance of spike
            response_time *= random.uniform(2, 5)

        return max(10, int(response_time))  # Minimum 10ms

    def generate_failure_scenarios(self, total_probes: int, failure_rate: float) -> List[int]:
        """Generate realistic failure scenarios."""
        failures = []

        # Calculate total failures needed to achieve target failure rate
        target_failures = int(total_probes * failure_rate)

        # Generate scattered individual failures (80% of failures)
        individual_failures = int(target_failures * 0.8)
        for _ in range(individual_failures):
            failures.append(random.randint(0, total_probes - 1))

        # Generate a few failure clusters (20% of failures)
        cluster_failures = target_failures - individual_failures
        while cluster_failures > 0:
            # Start a failure cluster
            cluster_start = random.randint(0, total_probes - 10)
            cluster_size = min(random.randint(2, 5), cluster_failures)

            for i in range(cluster_size):
                if cluster_start + i < total_probes:
                    failures.append(cluster_start + i)

            cluster_failures -= cluster_size

        return sorted(set(failures))

    def generate_probe_data(self, endpoint: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate probe data for a specific endpoint."""
        probe_data = []

        # Generate failure scenarios
        failures = self.generate_failure_scenarios(self.total_probes_per_endpoint, config["failure_rate"])
        failure_set = set(failures)

        # Start time (24 hours ago)
        start_time = datetime.utcnow() - timedelta(hours=24)

        successful_probes = 0

        for probe_id in range(1, self.total_probes_per_endpoint + 1):
            # Calculate timestamp
            timestamp = start_time + timedelta(seconds=(probe_id - 1) * self.probe_interval)

            # Determine if this probe should fail
            is_failure = probe_id in failure_set

            # Generate response time
            response_time_ms = self.generate_response_time(config["base_response_time"], is_failure)

            # Determine status and response code
            if is_failure:
                status = "unhealthy"
                response_codes = [500, 502, 503, 504, 0]  # Various failure types
                response_code = random.choice(response_codes)
                response_body = ""
                error_messages = [
                    "Connection failed",
                    "HTTP 500",
                    "HTTP 502",
                    "HTTP 503",
                    "HTTP 504",
                    "Timeout",
                    "Connection refused"
                ]
                error_message = random.choice(error_messages)
            else:
                status = "healthy"
                response_code = 200
                # Generate realistic response body
                if endpoint == "api-server":
                    response_body = json.dumps({
                        "status": "ok",
                        "timestamp": timestamp.isoformat() + "Z",
                        "version": "1.0.0"
                    })
                elif endpoint == "api-server-ready":
                    response_body = json.dumps({
                        "status": "ready",
                        "dependencies": ["database", "cache"],
                        "timestamp": timestamp.isoformat() + "Z"
                    })
                else:
                    response_body = "OK"

                error_message = ""
                successful_probes += 1

            # Calculate current uptime percentage
            uptime_percentage = (successful_probes / probe_id) * 100
            runtime_seconds = probe_id * self.probe_interval

            # Create probe record
            probe_record = {
                "timestamp": timestamp.isoformat() + "Z",
                "probe_id": probe_id,
                "endpoint": f"{config['base_url']}{config['health_path']}",
                "status": status,
                "response_code": response_code,
                "response_time_ms": response_time_ms,
                "response_body": response_body,
                "error_message": error_message,
                "uptime_percentage": round(uptime_percentage, 3),
                "total_probes": probe_id,
                "successful_probes": successful_probes,
                "runtime_seconds": runtime_seconds
            }

            probe_data.append(probe_record)

        return probe_data

    def generate_metrics_data(self, endpoint: str, probe_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate metrics summary data (every 10 probes)."""
        metrics_data = []

        for i in range(9, len(probe_data), 10):  # Every 10th probe (0-indexed)
            probe = probe_data[i]

            metrics_record = {
                "timestamp": probe["timestamp"],
                "metric_type": "health_summary",
                "total_probes": probe["total_probes"],
                "successful_probes": probe["successful_probes"],
                "failed_probes": probe["total_probes"] - probe["successful_probes"],
                "uptime_percentage": probe["uptime_percentage"],
                "runtime_seconds": probe["runtime_seconds"],
                "average_interval": round(probe["runtime_seconds"] / probe["total_probes"], 2)
            }

            metrics_data.append(metrics_record)

        return metrics_data

    def write_data_files(self, endpoint: str, probe_data: List[Dict[str, Any]], metrics_data: List[Dict[str, Any]]):
        """Write probe and metrics data to JSONL files."""
        # Write probe data
        probe_file = self.logs_dir / f"health_probe_{endpoint}.jsonl"
        with open(probe_file, 'w') as f:
            for record in probe_data:
                f.write(json.dumps(record) + '\n')

        # Write metrics data
        metrics_file = self.logs_dir / f"health_metrics_{endpoint}.jsonl"
        with open(metrics_file, 'w') as f:
            for record in metrics_data:
                f.write(json.dumps(record) + '\n')

        # Calculate final stats
        total_probes = len(probe_data)
        successful_probes = sum(1 for p in probe_data if p["status"] == "healthy")
        final_availability = (successful_probes / total_probes) * 100

        print(f"Generated data for {endpoint}:")
        print(f"  File: {probe_file}")
        print(f"  Metrics: {metrics_file}")
        print(f"  Total probes: {total_probes}")
        print(f"  Successful probes: {successful_probes}")
        print(f"  Availability: {final_availability:.3f}%")
        print(f"  SLO compliance: {'✓' if final_availability >= 99.5 else '✗'}")
        print()

    def generate_consolidated_data(self):
        """Generate consolidated 24hr data file."""
        consolidated_data = []

        for endpoint, config in self.endpoints.items():
            probe_file = self.logs_dir / f"health_probe_{endpoint}.jsonl"

            with open(probe_file, 'r') as f:
                for line in f:
                    record = json.loads(line.strip())
                    record['endpoint_name'] = endpoint
                    record['critical'] = config['critical']
                    consolidated_data.append(record)

        # Sort by timestamp
        consolidated_data.sort(key=lambda x: x['timestamp'])

        # Write consolidated file
        consolidated_file = self.logs_dir / "health_probes_24hr.jsonl"
        with open(consolidated_file, 'w') as f:
            for record in consolidated_data:
                f.write(json.dumps(record) + '\n')

        print(f"Consolidated data written to: {consolidated_file}")
        print(f"Total records: {len(consolidated_data)}")

    def generate_all_data(self):
        """Generate all simulated data."""
        print("Generating 24-hour simulated health probe data...")
        print(f"Target: >99.5% availability across all endpoints")
        print(f"Probe interval: {self.probe_interval} seconds")
        print(f"Total probes per endpoint: {self.total_probes_per_endpoint}")
        print()

        for endpoint, config in self.endpoints.items():
            print(f"Generating data for {endpoint}...")
            probe_data = self.generate_probe_data(endpoint, config)
            metrics_data = self.generate_metrics_data(endpoint, probe_data)
            self.write_data_files(endpoint, probe_data, metrics_data)

        # Generate consolidated file
        self.generate_consolidated_data()

        print("Data generation completed successfully!")
        print("\nTo analyze the data, run:")
        print(f"python3 /Users/sheldonzhao/programs/personal-manager/src/pm/obs/slo_calculator.py --logs-dir {self.logs_dir}")


def main():
    """Main function to generate simulated data."""
    if len(sys.argv) > 1:
        logs_dir = sys.argv[1]
    else:
        # Default to project logs directory
        script_dir = Path(__file__).parent
        logs_dir = script_dir.parent / "logs"

    generator = HealthProbeDataGenerator(str(logs_dir))
    generator.generate_all_data()


if __name__ == "__main__":
    main()