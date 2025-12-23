# Test Coverage Improvement Plan

## Current Status
- Current coverage: 10.21%
- Required coverage: 80%
- Target: Improve coverage significantly by adding strategic tests

## Priority Areas for Test Coverage

### High Priority (Core Functionality)
1. **Scan Plugin** - Currently at 54.84% coverage (missing lines: 53, 57, 61, 65-72, 83-84, 91-92, 101-102, 106-110, 117-126, 130-131, 160, 183-188, 199)
2. **Verify Plugin** - Currently at 10.30% coverage (needs major improvement)
3. **FileRepository** - Currently at 47% coverage (core database functionality)
4. **Plugin Registry** - Currently at 47% coverage (plugin management)
5. **File Processor/Walker** - Core scanning functionality

### Medium Priority (System Integration)
6. **Main application entry points**
7. **Configuration and dependency injection**
8. **Error handling and security**

### Low Priority (Utilities)
9. **Cache systems**
10. **Advanced features**

## Specific Tests to Implement

### 1. Scan Plugin Comprehensive Tests
- [ ] Test error handling in execute_scan (permission errors, file not found, etc.)
- [ ] Test different file size filters (min_size, max_size)
- [ ] Test extension filtering
- [ ] Test exclusion patterns
- [ ] Test verbose output scenarios
- [ ] Test database connection failures
- [ ] Test file processing edge cases (empty files, very large files)
- [ ] Test progress tracking functionality

### 2. Verify Plugin Tests
- [ ] Complete implementation of verify plugin tests
- [ ] Test all verification modes (integrity, consistency, checksums)
- [ ] Test repair functionality
- [ ] Test output formatting
- [ ] Test error scenarios and recovery

### 3. Database Layer Tests
- [ ] FileRepository comprehensive CRUD operations
- [ ] Batch operations (batch_add_files, batch_update_files)
- [ ] Query operations (get_duplicates, get_files_by_hash, etc.)
- [ ] Transaction handling
- [ ] Error handling for database operations

### 4. Plugin System Tests
- [ ] Plugin registration/unregistration
- [ ] Plugin lifecycle (initialize, shutdown, teardown)
- [ ] Plugin discovery and loading
- [ ] Plugin dependency management
- [ ] Plugin error handling

### 5. Core System Tests
- [ ] FileWalker edge cases (symlinks, permissions, etc.)
- [ ] FileProcessor comprehensive tests
- [ ] Hash computation and comparison
- [ ] Progress tracking and callbacks

## Implementation Strategy

### Phase 1: Fix Current Failing Tests (Completed)
- [x] Fix TestScanPlugin::test_scan_plugin_execute_scan_success

### Phase 2: Core Plugin Functionality
- [ ] Implement comprehensive scan plugin tests
- [ ] Implement comprehensive verify plugin tests
- [ ] Add database layer tests

### Phase 3: System Integration
- [ ] Add plugin registry tests
- [ ] Add error handling tests
- [ ] Add security tests

### Phase 4: Edge Cases and Performance
- [ ] Add edge case tests
- [ ] Add performance tests (if needed)
- [ ] Add integration tests

## Expected Impact
- Each core plugin test should improve coverage by 15-25%
- Database layer tests should improve coverage by 10-20%
- Plugin system tests should improve coverage by 5-10%
- Target: Reach at least 40-50% coverage after Phase 2, then 60-70% after Phase 3
