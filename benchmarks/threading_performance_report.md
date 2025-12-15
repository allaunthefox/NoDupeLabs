# NoDupeLabs Performance Benchmark Report

Generated on: 2025-12-13 23:58:33

## Test Environment

- Python Version: 3.13.7 (main, Aug 15 2025, 12:34:02) [GCC 15.2.1 20250813]
- Platform: linux
- CPU Count: 12

## Benchmark Results

| Threads | Avg Duration (s) | Std Dev (s) | Throughput (files/s) | Speedup |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.02 | 0.01 | 5505.26 | 1.00x |
| 2 | 0.01 | 0.00 | 8486.64 | 1.54x |
| 4 | 0.01 | 0.00 | 8529.42 | 1.55x |
| 8 | 0.01 | 0.00 | 8507.98 | 1.55x |
| 16 | 0.01 | 0.00 | 8439.55 | 1.53x |

### Speedup calculated relative to 1 thread baseline (0.02s)

## Performance Analysis

- Maximum speedup achieved: 1.00x with 1 threads
- Optimal thread count: 1
- Performance may be limited by I/O or other factors
