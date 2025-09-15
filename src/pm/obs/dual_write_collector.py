#!/usr/bin/env python3
"""
Dual-Write Metric Collector for OBS
Collects metrics in both legacy and standardized formats
Writes to JSONL files with timestamps and metadata
"""

import json
import time
import logging
import argparse
import signal
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import yaml
import requests
from urllib.parse import urljoin

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root / "src"))


@dataclass
class MetricEntry:
    """Represents a single metric entry"""
    timestamp: str
    format_type: str  # 'legacy' or 'standardized'
    metric_data: Dict[str, Any]
    collection_metadata: Dict[str, Any]


@dataclass
class ComparisonResult:
    """Represents a comparison between legacy and standardized metrics"""
    timestamp: str
    legacy_metric: Dict[str, Any]
    standardized_metric: Dict[str, Any]
    comparison_status: str  # 'match', 'mismatch', 'missing'
    differences: List[str]
    tolerance_applied: float


class DualWriteCollector:
    """Collects metrics in both legacy and standardized formats"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.session = requests.Session()
        self.session.timeout = self.config['collection']['timeout_seconds']

        # Collection state
        self.running = False
        self.collection_count = 0
        self.error_count = 0
        self.last_collection_time = None

        # Output files
        self.output_files = self._setup_output_files()

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Failed to load config from {config_path}: {e}")
            sys.exit(1)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})

        # Create logger
        logger = logging.getLogger('dual_write_collector')
        logger.setLevel(getattr(logging, log_config.get('level', 'INFO')))

        # Create formatter
        if log_config.get('format') == 'json':
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "message": "%(message)s"}'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # File handler
        if 'file' in log_config:
            os.makedirs(os.path.dirname(log_config['file']), exist_ok=True)
            file_handler = logging.FileHandler(log_config['file'])
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _setup_output_files(self) -> Dict[str, str]:
        """Setup output file paths"""
        output_config = self.config['output']
        base_dir = Path(output_config['base_directory'])
        base_dir.mkdir(parents=True, exist_ok=True)

        today = datetime.now().strftime('%Y%m%d')

        files = {}
        for format_type, config in output_config.items():
            if isinstance(config, dict) and config.get('enabled'):
                pattern = config['file_pattern'].replace('{date}', today)
                files[format_type] = str(base_dir / pattern)

        return files

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    def _get_api_url(self, endpoint: str) -> str:
        """Construct API URL from endpoint"""
        api_config = self.config['api_server']
        base_url = f"http://{api_config['host']}:{api_config['port']}"

        if endpoint.startswith('/'):
            return base_url + endpoint
        else:
            return urljoin(base_url + api_config['base_path'] + '/', endpoint)

    def _collect_metrics(self, format_type: str, endpoint: str) -> Optional[Dict[str, Any]]:
        """Collect metrics from a specific endpoint"""
        try:
            url = self._get_api_url(endpoint)
            self.logger.debug(f"Collecting {format_type} metrics from {url}")

            response = self.session.get(url)
            response.raise_for_status()

            data = response.json()

            # Add collection metadata
            collection_metadata = {
                'collection_time': datetime.now(timezone.utc).isoformat(),
                'collection_id': self.collection_count,
                'response_time_ms': int(response.elapsed.total_seconds() * 1000),
                'response_size_bytes': len(response.content),
                'endpoint': endpoint,
                'status_code': response.status_code
            }

            return {
                'metrics': data.get('metrics', []),
                'metadata': collection_metadata
            }

        except requests.RequestException as e:
            self.logger.error(f"Failed to collect {format_type} metrics: {e}")
            self.error_count += 1
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error collecting {format_type} metrics: {e}")
            self.error_count += 1
            return None

    def _write_jsonl(self, file_path: str, data: Dict[str, Any]):
        """Write data to JSONL file"""
        try:
            with open(file_path, 'a') as f:
                f.write(json.dumps(data) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write to {file_path}: {e}")

    def _compare_metrics(self, legacy_data: Dict[str, Any],
                        standard_data: Dict[str, Any]) -> List[ComparisonResult]:
        """Compare legacy and standardized metrics"""
        comparisons = []
        tolerance = self.config['comparison']['tolerance']
        mapping = self.config['comparison']['mapping']['legacy_to_standard']

        legacy_metrics = legacy_data.get('metrics', [])
        standard_metrics = standard_data.get('metrics', [])

        # Create lookup for standard metrics by name
        standard_lookup = {}
        for metric in standard_metrics:
            name = metric.get('name', '')
            standard_lookup[name] = metric

        for legacy_metric in legacy_metrics:
            legacy_name = legacy_metric.get('metric_name', '')

            # Map legacy name to standard name
            standard_name = None
            for legacy_field, standard_field in mapping.items():
                if legacy_field == 'metric_name' and legacy_name:
                    # Convert legacy naming convention
                    standard_name = legacy_name.replace('.', '_')
                    break

            if standard_name and standard_name in standard_lookup:
                standard_metric = standard_lookup[standard_name]

                # Compare values
                differences = []
                legacy_value = legacy_metric.get('value')
                standard_value = standard_metric.get('value')

                if legacy_value is not None and standard_value is not None:
                    if isinstance(legacy_value, (int, float)) and isinstance(standard_value, (int, float)):
                        diff = abs(legacy_value - standard_value)
                        if diff > tolerance:
                            differences.append(f"Value mismatch: {legacy_value} vs {standard_value} (diff: {diff})")
                    elif legacy_value != standard_value:
                        differences.append(f"Value mismatch: {legacy_value} vs {standard_value}")

                # Compare timestamps (convert to same format)
                legacy_ts = legacy_metric.get('timestamp', '')
                standard_ts = standard_metric.get('timestamp', 0)

                if legacy_ts and standard_ts:
                    try:
                        legacy_dt = datetime.fromisoformat(legacy_ts.replace('Z', '+00:00'))
                        standard_dt = datetime.fromtimestamp(standard_ts / 1_000_000_000, tz=timezone.utc)

                        ts_diff = abs((legacy_dt - standard_dt).total_seconds())
                        if ts_diff > 1.0:  # Allow 1 second difference
                            differences.append(f"Timestamp mismatch: {ts_diff}s difference")
                    except Exception as e:
                        differences.append(f"Timestamp comparison failed: {e}")

                status = 'match' if not differences else 'mismatch'

                comparison = ComparisonResult(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    legacy_metric=legacy_metric,
                    standardized_metric=standard_metric,
                    comparison_status=status,
                    differences=differences,
                    tolerance_applied=tolerance
                )
                comparisons.append(comparison)
            else:
                # No matching standard metric found
                comparison = ComparisonResult(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    legacy_metric=legacy_metric,
                    standardized_metric={},
                    comparison_status='missing',
                    differences=[f"No matching standard metric for {legacy_name}"],
                    tolerance_applied=tolerance
                )
                comparisons.append(comparison)

        return comparisons

    def _perform_collection_cycle(self):
        """Perform one complete collection cycle"""
        self.collection_count += 1
        collection_time = datetime.now(timezone.utc)

        self.logger.info(f"Starting collection cycle #{self.collection_count}")

        # Collect from both endpoints
        endpoints = self.config['endpoints']

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit collection tasks
            future_legacy = executor.submit(
                self._collect_metrics, 'legacy', endpoints['legacy_metrics']
            )
            future_standard = executor.submit(
                self._collect_metrics, 'standardized', endpoints['standard_metrics']
            )

            # Wait for results
            legacy_data = None
            standard_data = None

            for future in as_completed([future_legacy, future_standard]):
                if future == future_legacy:
                    legacy_data = future.result()
                elif future == future_standard:
                    standard_data = future.result()

        # Write collected data to JSONL files
        if legacy_data and 'legacy_format' in self.output_files:
            entry = MetricEntry(
                timestamp=collection_time.isoformat(),
                format_type='legacy',
                metric_data=legacy_data['metrics'],
                collection_metadata=legacy_data['metadata']
            )
            self._write_jsonl(self.output_files['legacy_format'], asdict(entry))

        if standard_data and 'standardized_format' in self.output_files:
            entry = MetricEntry(
                timestamp=collection_time.isoformat(),
                format_type='standardized',
                metric_data=standard_data['metrics'],
                collection_metadata=standard_data['metadata']
            )
            self._write_jsonl(self.output_files['standardized_format'], asdict(entry))

        # Perform comparison if both datasets available
        if (legacy_data and standard_data and
            'comparison_output' in self.output_files and
            self.config['comparison']['enabled']):

            comparisons = self._compare_metrics(legacy_data, standard_data)

            for comparison in comparisons:
                self._write_jsonl(
                    self.output_files['comparison_output'],
                    asdict(comparison)
                )

            # Log comparison summary
            match_count = sum(1 for c in comparisons if c.comparison_status == 'match')
            mismatch_count = sum(1 for c in comparisons if c.comparison_status == 'mismatch')
            missing_count = sum(1 for c in comparisons if c.comparison_status == 'missing')

            self.logger.info(
                f"Comparison results: {match_count} matches, "
                f"{mismatch_count} mismatches, {missing_count} missing"
            )

        self.last_collection_time = collection_time

        # Log collection summary
        success = legacy_data is not None and standard_data is not None
        self.logger.info(
            f"Collection cycle #{self.collection_count} "
            f"{'completed successfully' if success else 'completed with errors'}"
        )

    def run(self):
        """Main collection loop"""
        self.logger.info("Starting dual-write metric collector")
        self.logger.info(f"Configuration: {len(self.output_files)} output formats enabled")
        self.logger.info(f"Collection interval: {self.config['collection']['metrics_interval']}s")

        self.running = True
        interval = self.config['collection']['metrics_interval']

        try:
            while self.running:
                cycle_start = time.time()

                try:
                    self._perform_collection_cycle()
                except Exception as e:
                    self.logger.error(f"Collection cycle failed: {e}")
                    self.error_count += 1

                # Calculate sleep time to maintain interval
                cycle_duration = time.time() - cycle_start
                sleep_time = max(0, interval - cycle_duration)

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    self.logger.warning(f"Collection cycle took {cycle_duration:.2f}s, longer than interval {interval}s")

        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.running = False
            self._cleanup()

    def _cleanup(self):
        """Cleanup resources"""
        self.logger.info(
            f"Shutting down. Collected {self.collection_count} cycles "
            f"with {self.error_count} errors"
        )

        # Write final summary
        summary = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'event': 'collector_shutdown',
            'stats': {
                'total_collections': self.collection_count,
                'total_errors': self.error_count,
                'error_rate': self.error_count / max(1, self.collection_count),
                'uptime_seconds': (
                    datetime.now(timezone.utc) -
                    datetime.fromisoformat(self.last_collection_time or datetime.now(timezone.utc).isoformat())
                ).total_seconds() if self.last_collection_time else 0
            }
        }

        for file_path in self.output_files.values():
            self._write_jsonl(file_path, summary)


def main():
    parser = argparse.ArgumentParser(description='Dual-Write Metric Collector')
    parser.add_argument(
        '--config', '-c',
        default='/Users/sheldonzhao/programs/personal-manager/configs/observability/dual_write_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='Run as daemon process'
    )

    args = parser.parse_args()

    # Validate config file exists
    if not os.path.exists(args.config):
        print(f"ERROR: Configuration file not found: {args.config}")
        sys.exit(1)

    # Create and run collector
    try:
        collector = DualWriteCollector(args.config)
        collector.run()
    except Exception as e:
        print(f"FATAL: Failed to start collector: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()