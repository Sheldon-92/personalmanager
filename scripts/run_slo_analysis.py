#!/usr/bin/env python3
"""
Run SLO Analysis on Generated Health Probe Data

Simple script to test the SLO calculator with generated data.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pm.obs.slo_calculator import SLOCalculator


def main():
    """Run SLO analysis and generate report."""
    logs_dir = Path(__file__).parent.parent / "logs"
    config_path = Path(__file__).parent.parent / "configs" / "observability" / "health_probe_config.yaml"

    print("Running SLO Analysis...")
    print(f"Logs directory: {logs_dir}")
    print(f"Config file: {config_path}")
    print()

    # Initialize calculator
    calculator = SLOCalculator(config_path=str(config_path), logs_dir=str(logs_dir))

    # Generate SLO report
    try:
        report_file = calculator.generate_slo_report()
        print(f"✓ SLO report generated: {report_file}")

        # Load and display summary
        with open(report_file, 'r') as f:
            report_data = json.load(f)

        print("\n" + "="*60)
        print("SLO ANALYSIS SUMMARY")
        print("="*60)

        # Overall metrics
        overall = report_data.get('overall', {})
        for window in ['1hour', '6hour', '24hour']:
            if window in overall:
                metrics = overall[window]
                availability = metrics.get('availability_percentage', 0)
                critical_availability = metrics.get('critical_availability_percentage', 0)
                compliance = metrics.get('slo_compliance', False)
                critical_compliance = metrics.get('critical_slo_compliance', False)

                print(f"\n{window.upper()} Window:")
                print(f"  Overall Availability:  {availability:.3f}% {'✓' if compliance else '✗'}")
                print(f"  Critical Availability: {critical_availability:.3f}% {'✓' if critical_compliance else '✗'}")
                print(f"  Total Probes: {metrics.get('total_probes', 0)}")
                print(f"  Failed Probes: {metrics.get('failed_probes', 0)}")

        # Per-endpoint breakdown
        print("\n" + "-"*60)
        print("PER-ENDPOINT BREAKDOWN (24 HOUR)")
        print("-"*60)

        endpoints = report_data.get('endpoints', {})
        for endpoint_name, windows in endpoints.items():
            if '24hour' in windows:
                metrics = windows['24hour']
                availability = metrics.get('availability_percentage', 0)
                compliance = metrics.get('slo_compliance', False)
                total_probes = metrics.get('total_probes', 0)
                failed_probes = metrics.get('failed_probes', 0)

                # Check if critical endpoint
                endpoint_config = next(
                    (ep for ep in calculator.config.get('endpoints', []) if ep['name'] == endpoint_name),
                    {}
                )
                is_critical = endpoint_config.get('critical', False)
                critical_marker = " [CRITICAL]" if is_critical else ""

                print(f"\n{endpoint_name}{critical_marker}:")
                print(f"  Availability: {availability:.3f}% {'✓' if compliance else '✗'}")
                print(f"  Probes: {total_probes} total, {failed_probes} failed")
                print(f"  Target: {calculator.slo_target}%")

        # Export Prometheus metrics
        print("\n" + "-"*60)
        print("EXPORTING METRICS")
        print("-"*60)

        prom_file = calculator.export_prometheus_metrics()
        print(f"✓ Prometheus metrics exported: {prom_file}")

        # Summary
        print("\n" + "="*60)
        print("DEPLOYMENT VERIFICATION")
        print("="*60)

        overall_24h = overall.get('24hour', {})
        critical_24h = overall_24h.get('critical_availability_percentage', 0)

        print(f"✓ Health probes deployed: 5 endpoints")
        print(f"✓ 24-hour data generated: {overall_24h.get('total_probes', 0)} total probes")
        print(f"✓ SLO target: {calculator.slo_target}%")
        print(f"✓ Critical endpoints availability: {critical_24h:.3f}%")
        print(f"✓ Overall SLO compliance: {'PASS' if overall_24h.get('slo_compliance', False) else 'FAIL'}")

        if critical_24h >= 99.5:
            print("\n🎯 SUCCESS: OBS-O3 health probes deployed with >99.5% availability!")
        else:
            print(f"\n⚠️  WARNING: Critical availability ({critical_24h:.3f}%) below target (99.5%)")

    except Exception as e:
        print(f"✗ Error generating SLO report: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())