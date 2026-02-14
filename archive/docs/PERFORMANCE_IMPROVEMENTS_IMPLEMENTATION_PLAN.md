# Performance Improvements Implementation Plan

## Overview
This document outlines the implementation plan to address critical performance issues in the NoDupeLabs TimeSync plugin and related components.

## High-Level Issues Identified

### 1. Sequential Network I/O (CRITICAL)
- **Problem**: `query_servers_best()` and `query_ntp_once()` iterate addresses and hosts serially
- **Impact**: Multiplies wall time - 3 hosts × 2 addresses × 2 attempts = many sequential socket waits
- **Solution**: Parallelize network queries using ThreadPoolExecutor

### 2. Fragile Timing Calculations (HIGH)
- **Problem**: Using `time.time()` for RTT measurements is vulnerable to system clock jumps
- **Impact**: Inaccurate delay/offset calculations, potential time sync failures
- **Solution**: Use `time.monotonic()` for elapsed time, map to wall time for packet timestamps

### 3. Repeated Allocations/Parsing (MEDIUM)
- **Problem**: `struct.unpack("!12I", ...)` and format strings re-evaluated each call
- **Impact**: Unnecessary CPU overhead in hot loops
- **Solution**: Precompile struct formats using `struct.Struct`

### 4. Unbounded DNS Resolution (MEDIUM)
- **Problem**: `getaddrinfo` called for each host/attempt without caching
- **Impact**: Repeated DNS lookups slow down multiple attempts
- **Solution**: Cache DNS results for short TTL (30s)

### 5. Slow File System Fallback (HIGH)
- **Problem**: `_get_file_timestamp()` does recursive glob across many paths
- **Impact**: Can block for seconds/minutes on large filesystems
- **Solution**: Use targeted scanner with limited depth and early cutoff

### 6. Code Duplication (MEDIUM)
- **Problem**: Plugin implementation largely duplicates core module code
- **Impact**: Duplicated performance issues, maintenance burden
- **Solution**: Factor common logic into shared modules

## Implementation Plan

### Phase 1: Parallel Network Queries (HIGHEST PRIORITY)

**Objective**: Convert sequential NTP queries to parallel execution

**Tasks**:
- [ ] Create `ParallelNTPClient` class with ThreadPoolExecutor
- [ ] Implement parallel query across hosts/addresses
- [ ] Add timeout handling and cancellation
- [ ] Implement "good enough" result early termination
- [ ] Update `query_servers_best()` to use parallel client
- [ ] Add comprehensive tests for parallel behavior
- [ ] Benchmark wall-time improvements

**Expected Impact**: 70-90% reduction in synchronization time

**Files to Modify**:
- `nodupe/plugins/time_sync/time_sync.py` (major changes)
- `tests/plugins/test_time_sync.py` (new tests)

### Phase 2: Robust Timing Calculations (HIGH PRIORITY)

**Objective**: Replace fragile wall-clock timing with monotonic-based measurements

**Tasks**:
- [ ] Create `MonotonicTimeCalculator` class
- [ ] Implement dual-timestamp capture (wall + monotonic)
- [ ] Add monotonic-based RTT calculation
- [ ] Map monotonic elapsed time to wall time for packet timestamps
- [ ] Update all timing-sensitive methods
- [ ] Add tests for clock jump resilience
- [ ] Validate against system clock changes

**Expected Impact**: Eliminates timing failures due to clock jumps

**Files to Modify**:
- `nodupe/plugins/time_sync/time_sync.py` (timing methods)
- `tests/plugins/test_time_sync.py` (new timing tests)

### Phase 3: Precompiled Struct Formats (MEDIUM PRIORITY)

**Objective**: Eliminate repeated struct format parsing overhead

**Tasks**:
- [ ] Create module-level `struct.Struct` objects
- [ ] Replace `struct.unpack("!12I", ...)` calls
- [ ] Replace `struct.pack_into("!II", ...)` calls
- [ ] Update all struct operations to use precompiled formats
- [ ] Add performance benchmarks
- [ ] Verify correctness with existing tests

**Expected Impact**: 5-15% improvement in CPU-bound operations

**Files to Modify**:
- `nodupe/plugins/time_sync/time_sync.py` (struct operations)
- `tests/plugins/test_time_sync.py` (verify correctness)

### Phase 4: DNS Caching (MEDIUM PRIORITY)

**Objective**: Cache DNS resolution results to avoid repeated lookups

**Tasks**:
- [ ] Create `DNSCache` class with TTL
- [ ] Implement cache with 30-second TTL
- [ ] Add cache invalidation on errors
- [ ] Update `resolve_addresses()` to use cache
- [ ] Add cache statistics and monitoring
- [ ] Test cache behavior under various conditions

**Expected Impact**: 20-40% reduction in DNS lookup time

**Files to Modify**:
- `nodupe/plugins/time_sync/time_sync.py` (DNS resolution)
- `tests/plugins/test_time_sync.py` (cache tests)

### Phase 5: Optimized File System Fallback (HIGH PRIORITY)

**Objective**: Replace slow recursive glob with targeted file scanning

**Tasks**:
- [ ] Create `TargetedFileScanner` class
- [ ] Implement limited-depth directory scanning
- [ ] Add early cutoff for most-recent files
- [ ] Prioritize trusted system files (/etc/adjtime, /etc/localtime)
- [ ] Add configurable scan limits
- [ ] Make file fallback optional and conservative
- [ ] Benchmark filesystem operations

**Expected Impact**: 90%+ reduction in fallback scan time

**Files to Modify**:
- `nodupe/plugins/time_sync/time_sync.py` (file scanning)
- `tests/plugins/test_time_sync.py` (fallback tests)

### Phase 6: Code Deduplication (MEDIUM PRIORITY)

**Objective**: Factor common logic to eliminate duplication

**Tasks**:
- [ ] Identify duplicated code patterns
- [ ] Create shared utility modules
- [ ] Extract common NTP query logic
- [ ] Extract common timing calculation logic
- [ ] Update plugin to import from shared modules
- [ ] Remove duplicate implementations
- [ ] Update all tests to use shared code

**Expected Impact**: Easier maintenance, consistent performance improvements

**Files to Modify**:
- `nodupe/core/time_sync_utils.py` (new shared module)
- `nodupe/plugins/time_sync/time_sync.py` (refactored)
- All test files (updated imports)

### Phase 7: Micro-optimizations (LOW PRIORITY)

**Objective**: Implement additional performance improvements

**Tasks**:
- [ ] Reuse bytearray(48) for NTP packets where safe
- [ ] Use `socket.recv_into()` for preallocated buffers
- [ ] Optimize FastDate64 encoding/decoding
- [ ] Add performance monitoring and metrics
- [ ] Implement connection pooling for repeated queries

**Expected Impact**: 5-10% additional performance gains

**Files to Modify**:
- `nodupe/plugins/time_sync/time_sync.py` (optimizations)
- `nodupe/core/performance_metrics.py` (new metrics module)

### Phase 8: Testing and Validation (ONGOING)

**Objective**: Ensure all changes maintain correctness and improve performance

**Tasks**:
- [ ] Create performance benchmark suite
- [ ] Add regression tests for all optimizations
- [ ] Test under various network conditions
- [ ] Validate timing accuracy
- [ ] Test fallback scenarios
- [ ] Monitor production performance

**Expected Impact**: Confidence in performance improvements

**Files to Modify**:
- `benchmarks/time_sync_benchmarks.py` (new benchmark suite)
- All test files (updated tests)

## Implementation Order Rationale

1. **Phase 1 (Parallel Queries)**: Highest impact, addresses the most critical bottleneck
2. **Phase 2 (Timing)**: Critical for correctness and reliability
3. **Phase 5 (File Fallback)**: Addresses another major performance bottleneck
4. **Phase 3 (Struct)**: Easy wins with immediate benefits
5. **Phase 4 (DNS Cache)**: Moderate impact with good ROI
6. **Phase 6 (Deduplication)**: Improves maintainability and consistency
7. **Phase 7 (Micro-optimizations)**: Polish and fine-tuning

## Success Metrics

### Performance Targets
- **Wall Time**: 70-90% reduction in sync time (Phase 1)
- **CPU Usage**: 10-20% reduction in CPU-bound operations (Phases 3,7)
- **Fallback Time**: 90%+ reduction in file scan time (Phase 5)
- **DNS Lookups**: 20-40% reduction in lookup time (Phase 4)

### Reliability Targets
- **Clock Jump Resilience**: 100% success rate under clock changes (Phase 2)
- **Network Failure Handling**: Graceful degradation with proper logging
- **Fallback Success**: Reliable time sync even with all optimizations

### Code Quality Targets
- **Duplication**: 100% elimination of duplicate logic (Phase 6)
- **Test Coverage**: Maintain or improve existing test coverage
- **Documentation**: Complete documentation for all changes

## Risk Mitigation

### High-Risk Areas
1. **Parallel Queries**: Race conditions, resource management
   - Mitigation: Thorough testing, proper timeout handling, graceful degradation
   
2. **Timing Changes**: Potential accuracy issues
   - Mitigation: Extensive validation against known good time sources
   
3. **File System Changes**: Potential to miss valid time sources
   - Mitigation: Conservative fallback, comprehensive testing

### Rollback Plan
- Each phase is designed to be independently reversible
- Feature flags for major changes
- Gradual rollout with monitoring

## Timeline Estimate

- **Phase 1**: 3-4 days
- **Phase 2**: 2-3 days  
- **Phase 3**: 1-2 days
- **Phase 4**: 2-3 days
- **Phase 5**: 3-4 days
- **Phase 6**: 4-5 days
- **Phase 7**: 2-3 days
- **Phase 8**: Ongoing throughout

**Total Estimated Duration**: 17-24 days

## Resources Required

- **Developer Time**: 1-2 developers full-time
- **Testing Infrastructure**: Access to various network conditions
- **Performance Monitoring**: Tools for measuring improvements
- **Documentation**: Time for comprehensive documentation

## Next Steps

1. Review and approve this implementation plan
2. Set up development environment with necessary tools
3. Begin Phase 1 implementation
4. Establish performance baseline measurements
5. Proceed with phased implementation and testing
