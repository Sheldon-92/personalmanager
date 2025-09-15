# Plugin Stress Test Design Document

## Overview

This document describes the comprehensive concurrent plugin load/unload stress test for the Personal Manager plugin system. The test is designed to validate performance, resource management, and stability under concurrent load conditions.

## Test Architecture

### Components

1. **PluginStressTest** (Main Orchestrator)
   - Manages test execution flow
   - Coordinates worker threads/processes
   - Collects and aggregates metrics
   - Performs resource leak detection

2. **PluginWorker** (Operation Executor)
   - Executes plugin load/unload operations
   - Captures operation-level metrics
   - Tracks resource usage per operation

3. **StressTestConfig** (Configuration)
   - Defines test parameters
   - Sets performance thresholds
   - Configures resource tracking options

4. **ResourceSnapshot** (Resource Monitor)
   - Captures system resource state
   - Tracks memory, threads, file descriptors, network connections
   - Provides point-in-time resource measurements

### Concurrency Models

#### Threading Mode (Default)
- Uses Python's `asyncio` with `ThreadPoolExecutor`
- Suitable for I/O-bound operations
- Lower overhead, shared memory space
- Better for testing async plugin operations

#### Multiprocessing Mode
- Uses Python's `multiprocessing` with separate processes
- Suitable for CPU-bound operations
- Complete isolation between workers
- Better for testing resource isolation

## Test Methodology

### 1. Baseline Establishment
```python
# Take 5 samples, use median
baseline = capture_baseline(samples=5)
```
- Captures initial resource state
- Forces garbage collection
- Takes multiple samples for accuracy

### 2. Concurrent Operations
```
Round 1: [Worker1: Load A,B → Unload B,A]
         [Worker2: Load A,B → Unload B,A]
         [Worker3: Load A,B → Unload B,A]
         [Worker4: Load A,B → Unload B,A]

Round 2: ...
...
Round 10: ...
```

### 3. Timing Methodology
- **High-precision timing**: `time.perf_counter()`
- **Per-operation tracking**: Start → End timestamps
- **Millisecond precision**: All latencies in ms

### 4. Resource Tracking

#### Memory Tracking
- **RSS (Resident Set Size)**: Physical memory usage
- **VMS (Virtual Memory Size)**: Virtual memory allocation
- **Memory percent**: System memory percentage

#### File Descriptors
- Unix: `process.num_fds()`
- Windows: `len(process.open_files())`
- Tracks open file handles

#### Thread Tracking
- `process.num_threads()`
- Monitors thread creation/destruction

#### Network Connections
- `process.connections()`
- Tracks active network sockets

### 5. Statistical Analysis

#### Percentile Calculations
```python
P50 = np.percentile(times, 50)  # Median
P95 = np.percentile(times, 95)  # 95th percentile
P99 = np.percentile(times, 99)  # 99th percentile
```

#### Leak Detection
```python
leak_detected = abs((final - baseline) / baseline * 100) > tolerance
```
- Tolerance: ±2% by default
- Checks: Memory, FDs, Threads, Connections

## Performance Metrics

### Primary Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Load P95 | ≤300ms | 95% of loads complete within |
| Load P99 | ≤500ms | 99% of loads complete within |
| Unload P95 | ≤150ms | 95% of unloads complete within |
| Unload P99 | ≤200ms | 99% of unloads complete within |
| Success Rate | 100% | All operations succeed |

### Resource Metrics

| Resource | Baseline | Final | Max Delta |
|----------|----------|-------|-----------|
| Memory | X MB | X±2% MB | 2% |
| Threads | N | N±2% | 2% |
| File Descriptors | F | F±2% | 2% |
| Connections | C | C±2% | 2% |

## Test Execution

### Quick Test (Development)
```bash
./run_stress_test.sh --quick
# 3 rounds, 2 workers, ~30 seconds
```

### Standard Test (CI/CD)
```bash
./run_stress_test.sh
# 10 rounds, 4 workers, ~2 minutes
```

### Full Test (Release)
```bash
./run_stress_test.sh --full
# 20 rounds, 8 workers, ~5 minutes
```

### Stress Test (Performance)
```bash
./run_stress_test.sh --stress
# 50 rounds, 16 workers, ~15 minutes
```

## Plugin Selection

### Default Plugins Tested
Located in `/Users/sheldonzhao/programs/personal-manager/src/pm/plugins/examples/`:

1. **report_exporter.py**
   - File I/O operations
   - JSON/Markdown generation
   - Permission: WRITE_DATA

2. **custom_recommender.py**
   - Algorithm execution
   - Data processing
   - Permission: READ_DATA

### Plugin Load Pattern
```
Worker 1: [report_exporter, custom_recommender]
Worker 2: [report_exporter, custom_recommender]
Worker 3: [report_exporter, custom_recommender]
Worker 4: [report_exporter, custom_recommender]
```

## Output and Reporting

### Console Output
```
============================================
STRESS TEST RESULTS
============================================
Test Duration: 120.45 seconds
Total Operations: 400
Successful: 400
Failed: 0
Success Rate: 100.00%

----------------------------------------
PERFORMANCE METRICS
----------------------------------------
Load Operations:
  P50: 45.23ms
  P95: 287.45ms
  P99: 412.78ms

Unload Operations:
  P50: 23.12ms
  P95: 89.34ms
  P99: 145.67ms

----------------------------------------
RESOURCE USAGE
----------------------------------------
Memory:
  Baseline: 45.23MB
  Final: 45.89MB
  Delta: 0.66MB
  Change: 1.46%

----------------------------------------
LEAK DETECTION
----------------------------------------
Memory Leak: PASS
Thread Leak: PASS
FD Leak: PASS
Connection Leak: PASS

============================================
OVERALL RESULT: PASS ✓
============================================
```

### File Outputs

1. **Summary Report** (`stress_test_summary_YYYYMMDD_HHMMSS.json`)
   - Complete test results
   - Performance metrics
   - Resource usage
   - Leak detection results

2. **Detailed Metrics** (`detailed_metrics_YYYYMMDD_HHMMSS.jsonl`)
   - Per-operation metrics
   - Timing data
   - Resource snapshots

3. **Resource Timeline** (`resource_timeline_YYYYMMDD_HHMMSS.jsonl`)
   - Resource usage over time
   - Per-round snapshots
   - Trend analysis data

## Success Criteria

The stress test passes if ALL of the following conditions are met:

1. ✓ 100% operation success rate
2. ✓ Load P95 ≤ 300ms
3. ✓ Load P99 ≤ 500ms
4. ✓ Unload P95 ≤ 150ms
5. ✓ Unload P99 ≤ 200ms
6. ✓ Memory delta ≤ 2%
7. ✓ Thread delta ≤ 2%
8. ✓ FD delta ≤ 2%
9. ✓ Connection delta ≤ 2%

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run Plugin Stress Test
  run: |
    cd tests/bench
    ./run_stress_test.sh --rounds 10 --workers 4
  timeout-minutes: 5
```

### Jenkins Pipeline Example
```groovy
stage('Stress Test') {
    steps {
        sh 'cd tests/bench && ./run_stress_test.sh --full'
    }
    post {
        always {
            archiveArtifacts artifacts: '/tmp/plugin_stress_test/*.json'
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **High P99 Latency**
   - Check for GC pauses
   - Review plugin initialization code
   - Consider async loading

2. **Memory Leaks**
   - Check plugin cleanup methods
   - Review circular references
   - Force GC in unload

3. **Thread Leaks**
   - Ensure proper thread termination
   - Check for daemon threads
   - Review executor shutdown

4. **FD Leaks**
   - Close files explicitly
   - Use context managers
   - Check temporary files

## Future Enhancements

1. **Chaos Testing**
   - Random plugin failures
   - Resource exhaustion
   - Network interruptions

2. **Load Patterns**
   - Burst loading
   - Gradual ramp-up
   - Sustained load

3. **Plugin Variations**
   - Different plugin sizes
   - Complex dependencies
   - Resource-intensive plugins

4. **Monitoring Integration**
   - Prometheus metrics
   - Grafana dashboards
   - Alert thresholds

## Conclusion

This stress test provides comprehensive validation of the plugin system's performance and resource management under concurrent load. It ensures the system can handle production workloads while maintaining performance targets and preventing resource leaks.