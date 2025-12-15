# NoDupeLabs Parallel Processing Performance Report

Generated on: 2025-12-13 23:58:33

## Test Environment
- Python Version: 3.13.7 (main, Aug 15 2025, 12:34:02) [GCC 15.2.1 20250813]
- Platform: linux
- CPU Count: 12

## Parallel Strategy Results
| Strategy | Avg Duration (s) | Std Dev (s) | Throughput (files/s) | Speedup |
|----------|------------------|-------------|---------------------|---------|
| Sequential |             0.01 |        0.00 |             4188.72 |    1.00x |
| Threading |             0.00 |        0.00 |            15497.59 |    3.70x |
| Processing |             0.01 |        0.00 |             7364.38 |    1.76x |

*Speedup calculated relative to Sequential baseline (0.01s)*

## Performance Analysis
- Process pool speedup: 1.76x
- Threading speedup: 3.70x
- Optimal strategy: Threading