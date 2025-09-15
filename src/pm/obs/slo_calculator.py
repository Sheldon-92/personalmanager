#!/usr/bin/env python3
"""
SLO Calculator for OBS-O3 Health Monitoring

Calculates Service Level Objectives (SLOs) from health probe data with rolling window analysis.
Supports multiple time windows and generates availability percentages for SLO compliance.
"""

import json
import logging
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    import yaml
except ImportError:
    print("PyYAML is required. Install it with: pip install PyYAML")
    sys.exit(1)


class SLOCalculator:
    """Calculate SLO metrics from health probe data with rolling window analysis."""

    def __init__(self, config_path: Optional[str] = None, logs_dir: Optional[str] = None):
        """
        Initialize SLO Calculator.

        Args:
            config_path: Path to health probe configuration file
            logs_dir: Directory containing health probe logs
        """
        self.logger = logging.getLogger(__name__)

        # Set default paths if not provided
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "configs" / "observability" / "health_probe_config.yaml"
        if logs_dir is None:
            logs_dir = Path(__file__).parent.parent.parent.parent / "logs"

        self.config_path = Path(config_path)
        self.logs_dir = Path(logs_dir)

        # Load configuration
        self.config = self._load_config()
        self.slo_target = self.config.get('global', {}).get('slo_target', 99.5)
        self.slo_windows = self.config.get('slo_windows', [])

        self.logger.info(f"SLO Calculator initialized with target: {self.slo_target}%")

    def _load_config(self) -> Dict[str, Any]:
        """Load health probe configuration."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                self.logger.warning(f"Config file not found: {self.config_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def _load_probe_data(self, endpoint: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Load health probe data for a specific endpoint.

        Args:
            endpoint: Endpoint name
            hours: Number of hours to look back

        Returns:
            List of probe data records
        """
        probe_file = self.logs_dir / f"health_probe_{endpoint}.jsonl"

        if not probe_file.exists():
            self.logger.warning(f"Probe file not found: {probe_file}")
            return []

        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        records = []
        try:
            with open(probe_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        record = json.loads(line)

                        # Parse timestamp
                        timestamp_str = record.get('timestamp', '')
                        if timestamp_str:
                            # Handle both ISO format and other formats
                            try:
                                if timestamp_str.endswith('Z'):
                                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    # Convert to UTC naive datetime for comparison
                                    timestamp = timestamp.replace(tzinfo=None)
                                else:
                                    timestamp = datetime.fromisoformat(timestamp_str)
                                    # Ensure naive datetime
                                    if timestamp.tzinfo is not None:
                                        timestamp = timestamp.replace(tzinfo=None)

                                # Only include records within the time window
                                if timestamp >= cutoff_time:
                                    records.append(record)
                            except ValueError:
                                self.logger.debug(f"Failed to parse timestamp: {timestamp_str}")
                                continue

                    except json.JSONDecodeError as e:
                        self.logger.debug(f"Failed to parse JSON line: {e}")
                        continue

        except FileNotFoundError:
            self.logger.warning(f"Probe file not found: {probe_file}")
        except Exception as e:
            self.logger.error(f"Error reading probe file {probe_file}: {e}")

        self.logger.info(f"Loaded {len(records)} probe records for {endpoint}")
        return records

    def calculate_availability(self, records: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate availability metrics from probe records.

        Args:
            records: List of probe data records

        Returns:
            Dictionary containing availability metrics
        """
        if not records:
            return {
                'total_probes': 0,
                'successful_probes': 0,
                'failed_probes': 0,
                'availability_percentage': 0.0,
                'error_rate': 100.0,
                'mean_response_time': 0.0,
                'p95_response_time': 0.0,
                'p99_response_time': 0.0
            }

        total_probes = len(records)
        successful_probes = sum(1 for r in records if r.get('status') == 'healthy')
        failed_probes = total_probes - successful_probes

        availability_percentage = (successful_probes / total_probes) * 100
        error_rate = (failed_probes / total_probes) * 100

        # Calculate response time statistics
        response_times = [r.get('response_time_ms', 0) for r in records if r.get('response_time_ms') is not None]

        if response_times:
            mean_response_time = statistics.mean(response_times)

            # Calculate percentiles
            sorted_times = sorted(response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)

            p95_response_time = sorted_times[min(p95_index, len(sorted_times) - 1)]
            p99_response_time = sorted_times[min(p99_index, len(sorted_times) - 1)]
        else:
            mean_response_time = 0.0
            p95_response_time = 0.0
            p99_response_time = 0.0

        return {
            'total_probes': total_probes,
            'successful_probes': successful_probes,
            'failed_probes': failed_probes,
            'availability_percentage': round(availability_percentage, 3),
            'error_rate': round(error_rate, 3),
            'mean_response_time': round(mean_response_time, 2),
            'p95_response_time': round(p95_response_time, 2),
            'p99_response_time': round(p99_response_time, 2)
        }

    def calculate_rolling_windows(self, endpoint: str) -> Dict[str, Dict[str, float]]:
        """
        Calculate SLO metrics for different rolling time windows.

        Args:
            endpoint: Endpoint name

        Returns:
            Dictionary with metrics for each time window
        """
        results = {}

        # Default windows if not configured
        windows = self.slo_windows if self.slo_windows else [
            {'name': '1hour', 'duration_minutes': 60},
            {'name': '6hour', 'duration_minutes': 360},
            {'name': '24hour', 'duration_minutes': 1440}
        ]

        for window in windows:
            window_name = window['name']
            duration_hours = window['duration_minutes'] / 60

            records = self._load_probe_data(endpoint, hours=duration_hours)
            metrics = self.calculate_availability(records)

            # Add window-specific information
            metrics['window'] = window_name
            metrics['duration_hours'] = duration_hours
            metrics['slo_target'] = self.slo_target
            metrics['slo_compliance'] = metrics['availability_percentage'] >= self.slo_target
            metrics['slo_budget_remaining'] = max(0, metrics['availability_percentage'] - self.slo_target)

            results[window_name] = metrics

        return results

    def calculate_overall_slo(self, endpoints: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Calculate overall SLO across multiple endpoints.

        Args:
            endpoints: List of endpoint names to include (defaults to all configured endpoints)

        Returns:
            Dictionary containing overall SLO metrics
        """
        if endpoints is None:
            # Get endpoints from configuration
            endpoints = [ep['name'] for ep in self.config.get('endpoints', [])]

        if not endpoints:
            self.logger.warning("No endpoints configured for SLO calculation")
            return {}

        overall_results = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'slo_target': self.slo_target,
            'endpoints': {},
            'overall': {}
        }

        # Calculate per-endpoint metrics
        all_endpoint_metrics = {}
        for endpoint in endpoints:
            endpoint_metrics = self.calculate_rolling_windows(endpoint)
            overall_results['endpoints'][endpoint] = endpoint_metrics
            all_endpoint_metrics[endpoint] = endpoint_metrics

        # Calculate overall metrics across all endpoints
        for window_name in ['1hour', '6hour', '24hour']:
            window_metrics = []
            critical_endpoints = []

            for endpoint in endpoints:
                if endpoint in all_endpoint_metrics and window_name in all_endpoint_metrics[endpoint]:
                    metrics = all_endpoint_metrics[endpoint][window_name]
                    window_metrics.append(metrics)

                    # Check if this is a critical endpoint
                    endpoint_config = next((ep for ep in self.config.get('endpoints', []) if ep['name'] == endpoint), {})
                    if endpoint_config.get('critical', False):
                        critical_endpoints.append(metrics)

            if window_metrics:
                # Calculate weighted average availability
                total_probes = sum(m['total_probes'] for m in window_metrics)
                total_successful = sum(m['successful_probes'] for m in window_metrics)

                overall_availability = (total_successful / total_probes * 100) if total_probes > 0 else 0

                # Calculate critical endpoints availability
                if critical_endpoints:
                    critical_total_probes = sum(m['total_probes'] for m in critical_endpoints)
                    critical_successful = sum(m['successful_probes'] for m in critical_endpoints)
                    critical_availability = (critical_successful / critical_total_probes * 100) if critical_total_probes > 0 else 0
                else:
                    critical_availability = overall_availability

                overall_results['overall'][window_name] = {
                    'availability_percentage': round(overall_availability, 3),
                    'critical_availability_percentage': round(critical_availability, 3),
                    'total_probes': total_probes,
                    'successful_probes': total_successful,
                    'failed_probes': total_probes - total_successful,
                    'endpoints_count': len(window_metrics),
                    'critical_endpoints_count': len(critical_endpoints),
                    'slo_compliance': overall_availability >= self.slo_target,
                    'critical_slo_compliance': critical_availability >= self.slo_target,
                    'slo_budget_remaining': max(0, overall_availability - self.slo_target)
                }

        return overall_results

    def generate_slo_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate comprehensive SLO report.

        Args:
            output_file: Output file path (defaults to timestamped file in logs directory)

        Returns:
            Path to generated report file
        """
        if output_file is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            output_file = str(self.logs_dir / f"slo_report_{timestamp}.json")

        # Calculate overall SLO
        slo_data = self.calculate_overall_slo()

        # Add metadata
        slo_data['report_metadata'] = {
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'calculator_version': '1.0.0',
            'config_file': str(self.config_path),
            'logs_directory': str(self.logs_dir)
        }

        # Write report
        try:
            with open(output_file, 'w') as f:
                json.dump(slo_data, f, indent=2)

            self.logger.info(f"SLO report generated: {output_file}")

            # Log summary
            overall_24h = slo_data.get('overall', {}).get('24hour', {})
            availability = overall_24h.get('availability_percentage', 0)
            compliance = overall_24h.get('slo_compliance', False)

            self.logger.info(f"24h Availability: {availability}% (Target: {self.slo_target}% - {'✓' if compliance else '✗'})")

            return output_file

        except Exception as e:
            self.logger.error(f"Failed to write SLO report: {e}")
            raise

    def export_prometheus_metrics(self, output_file: Optional[str] = None) -> str:
        """
        Export SLO metrics in Prometheus format.

        Args:
            output_file: Output file path

        Returns:
            Path to generated metrics file
        """
        if output_file is None:
            output_file = str(self.logs_dir / "slo_metrics.prom")

        slo_data = self.calculate_overall_slo()
        timestamp = int(datetime.utcnow().timestamp() * 1000)

        metrics_lines = [
            "# HELP obs_slo_availability_percentage Availability percentage for each endpoint and window",
            "# TYPE obs_slo_availability_percentage gauge",
            "",
            "# HELP obs_slo_compliance SLO compliance status (1 = compliant, 0 = non-compliant)",
            "# TYPE obs_slo_compliance gauge",
            "",
            "# HELP obs_slo_total_probes Total number of probes",
            "# TYPE obs_slo_total_probes counter",
            ""
        ]

        # Export per-endpoint metrics
        for endpoint, windows in slo_data.get('endpoints', {}).items():
            for window_name, metrics in windows.items():
                availability = metrics.get('availability_percentage', 0)
                compliance = 1 if metrics.get('slo_compliance', False) else 0
                total_probes = metrics.get('total_probes', 0)

                metrics_lines.extend([
                    f'obs_slo_availability_percentage{{endpoint="{endpoint}",window="{window_name}"}} {availability} {timestamp}',
                    f'obs_slo_compliance{{endpoint="{endpoint}",window="{window_name}"}} {compliance} {timestamp}',
                    f'obs_slo_total_probes{{endpoint="{endpoint}",window="{window_name}"}} {total_probes} {timestamp}'
                ])

        # Export overall metrics
        for window_name, metrics in slo_data.get('overall', {}).items():
            availability = metrics.get('availability_percentage', 0)
            compliance = 1 if metrics.get('slo_compliance', False) else 0
            total_probes = metrics.get('total_probes', 0)

            metrics_lines.extend([
                f'obs_slo_availability_percentage{{endpoint="overall",window="{window_name}"}} {availability} {timestamp}',
                f'obs_slo_compliance{{endpoint="overall",window="{window_name}"}} {compliance} {timestamp}',
                f'obs_slo_total_probes{{endpoint="overall",window="{window_name}"}} {total_probes} {timestamp}'
            ])

        try:
            with open(output_file, 'w') as f:
                f.write('\n'.join(metrics_lines) + '\n')

            self.logger.info(f"Prometheus metrics exported: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"Failed to export Prometheus metrics: {e}")
            raise


def main():
    """Command-line interface for SLO Calculator."""
    import argparse

    parser = argparse.ArgumentParser(description="Calculate SLO metrics from health probe data")
    parser.add_argument("--config", help="Path to health probe configuration file")
    parser.add_argument("--logs-dir", help="Directory containing health probe logs")
    parser.add_argument("--output", help="Output file path for report")
    parser.add_argument("--format", choices=["json", "prometheus"], default="json", help="Output format")
    parser.add_argument("--endpoint", help="Calculate metrics for specific endpoint only")
    parser.add_argument("--window", choices=["1hour", "6hour", "24hour"], help="Calculate metrics for specific window only")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # Initialize calculator
        calculator = SLOCalculator(config_path=args.config, logs_dir=args.logs_dir)

        if args.format == "prometheus":
            # Export Prometheus metrics
            output_file = calculator.export_prometheus_metrics(args.output)
            print(f"Prometheus metrics exported to: {output_file}")
        else:
            # Generate JSON report
            if args.endpoint and args.window:
                # Calculate specific endpoint and window
                records = calculator._load_probe_data(args.endpoint, hours=24)
                metrics = calculator.calculate_availability(records)

                result = {
                    'endpoint': args.endpoint,
                    'window': args.window,
                    'metrics': metrics,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"Metrics exported to: {args.output}")
                else:
                    print(json.dumps(result, indent=2))

            elif args.endpoint:
                # Calculate all windows for specific endpoint
                metrics = calculator.calculate_rolling_windows(args.endpoint)

                result = {
                    'endpoint': args.endpoint,
                    'windows': metrics,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"Metrics exported to: {args.output}")
                else:
                    print(json.dumps(result, indent=2))

            else:
                # Generate full SLO report
                output_file = calculator.generate_slo_report(args.output)
                print(f"SLO report generated: {output_file}")

                # Print summary
                slo_data = calculator.calculate_overall_slo()
                overall_24h = slo_data.get('overall', {}).get('24hour', {})
                availability = overall_24h.get('availability_percentage', 0)
                target = calculator.slo_target
                compliance = overall_24h.get('slo_compliance', False)

                print(f"\n24-hour SLO Summary:")
                print(f"  Availability: {availability}%")
                print(f"  Target: {target}%")
                print(f"  Compliance: {'✓ PASS' if compliance else '✗ FAIL'}")
                print(f"  Budget Remaining: {max(0, availability - target):.3f}%")

    except Exception as e:
        logging.error(f"SLO calculation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()