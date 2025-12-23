# Testing Strategy for NoDupeLabs

## Current Test Infrastructure Issues

### Import Errors Identified
1. **Database Files Test** (`tests/core/test_database_files.py`)
   - Imports `FileRecordManager` which doesn't exist in `nodupe.core.database.files`
   - Actual class: `DatabaseFileOperations` with different API

2. **Hasher Test** (`tests/core/test_hasher.py`)
   - Contains invalid escape sequence: `b'\x0\x01\x02\x03\xFF\xFE'`
   - Need to fix binary content syntax

3. **Progress Tracker Test** (`tests/core/test_progress_tracker.py`)
   - Module `nodupe.core.progress_tracker` doesn't exist
   - Progress tracking functionality appears to be in `nodupe.core.progress`

4. **Leap Year Plugin Test** (`tests/plugins/test_leap_year.py`)
   - Cannot import `PluginBase` from `nodupe.core.plugin_system`
   - Plugin base classes need to be located and imported correctly

## Testing Approach

### 1. Unit Testing Strategy
- **Target:** Individual functions and classes
- **Coverage Goal:** 70%+ per module
- **Focus:** Core functionality, error handling, edge cases

### 2. Integration Testing Strategy
- **Target:** Module interactions and workflows
- **Coverage Goal:** 60%+ for critical paths
- **Focus:** Scan -> Process -> Apply workflows

### 3. Test File Organization
```
tests/
├── core/                 # Core module tests
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_database/
│   │   ├── test_connection.py
│   │   ├── test_files.py
│   │   └── test_operations.py
│   └── test_plugins/
│       ├── test_registry.py
│       ├── test_loader.py
│       └── test_lifecycle.py
├── plugins/             # Plugin-specific tests
│   ├── test_scan.py
│   ├── test_verify.py
│   └── test_time_sync.py
└── integration/         # End-to-end tests
    ├── test_workflows.py
    └── test_cli.py
```

## Phase 1: Fix Test Infrastructure (Week 1)

### Immediate Fixes Required
1. **Fix Database Files Test**
   - Update import to use actual class: `DatabaseFileOperations`
   - Modify test methods to match actual API

2. **Fix Hasher Test**
   - Correct binary content syntax
   - Use proper escape sequences

3. **Fix Progress Tracker Test**
   - Locate actual progress tracking module
   - Update imports and test methods

4. **Fix Plugin Base Import**
   - Find correct plugin base class location
   - Update import paths

### Test Infrastructure Improvements
- Add proper test fixtures and setup/teardown
- Implement parameterized tests for common scenarios
- Add mock objects for external dependencies

## Phase 2: Core Module Testing (Week 2-3)

### High-Priority Modules (0% Coverage)
1. **Cache System**
   - `nodupe/core/cache/embedding_cache.py`
   - `nodupe/core/cache/hash_cache.py`
   - `nodupe/core/cache/query_cache.py`

2. **Parallel Processing**
   - `nodupe/core/parallel.py`
   - `nodupe/core/pools.py`

3. **Command Modules**
   - `nodupe/plugins/commands/archive.py`
   - `nodupe/plugins/commands/mount.py`
   - `nodupe/plugins/commands/plan.py`
   - `nodupe/plugins/commands/rollback.py`

### Testing Strategy for Zero-Coverage Modules
- Create basic unit tests for all public methods
- Test error handling and edge cases
- Verify input validation and type checking
- Test integration with core dependencies

## Phase 3: Database and Plugin Testing (Week 4-5)

### Database Modules
- `nodupe/core/database/indexing.py` (10.67%)
- `nodupe/core/database/embeddings.py` (16.13%)
- `nodupe/core/database/transactions.py` (23.43%)

### Plugin System Modules
- `nodupe/core/plugin_system/security.py` (21.62%)
- `nodupe/core/plugin_system/dependencies.py` (11.56%)
- `nodupe/core/plugin_system/loader.py` (15.6%)

### Database Testing Strategy
- Test all CRUD operations
- Verify transaction handling
- Test connection pooling
- Validate error recovery

### Plugin Testing Strategy
- Test plugin registration and lifecycle
- Verify security validation
- Test dependency resolution
- Validate hot reload functionality

## Phase 4: Command and Integration Testing (Week 6-8)

### Command Module Testing
- `nodupe/plugins/commands/scan.py` (38.71%)
- `nodupe/plugins/commands/verify.py` (11.00%)
- `nodupe/plugins/commands/similarity.py` (46.15%)

### Integration Testing
- End-to-end scan workflows
- CLI command integration
- Cross-module functionality
- Error recovery scenarios

## Quality Assurance Standards

### Test Requirements
1. **Documentation:** Every test must have clear docstrings explaining:
   - What is being tested
   - Why it's important
   - Expected behavior

2. **Naming Convention:** Use descriptive test names following pattern:
   - `test_[functionality]_[scenario]_[expected_result]`
   - Example: `test_scan_empty_directory_returns_empty_list`

3. **Setup/Teardown:** Use pytest fixtures for:
   - Test data preparation
   - Mock object creation
   - Resource cleanup

4. **Parameterized Tests:** Use `@pytest.mark.parametrize` for:
   - Multiple input scenarios
   - Edge cases
   - Error conditions

### Code Quality for Tests
- Follow Google Python Style Guide for test functions
- Use descriptive variable names
- Include type hints where beneficial
- Minimize test dependencies on external resources

## Success Metrics

### Phase 1: Infrastructure (Week 1)
- [ ] All import errors resolved
- [ ] Test suite runs without collection errors
- [ ] 10% of existing tests pass

### Phase 2: Core Modules (Week 3)
- [ ] 50% of zero-coverage modules have basic tests
- [ ] Overall coverage increases to 50%
- [ ] All core functionality has unit tests

### Phase 3: Database/Plugin (Week 5)
- [ ] Database modules reach 40%+ coverage
- [ ] Plugin system reaches 40%+ coverage
- [ ] Overall coverage increases to 60%

### Phase 4: Integration (Week 8)
- [ ] Command modules reach 60%+ coverage
- [ ] Integration tests cover major workflows
- [ ] Overall coverage reaches 75%+

## Risk Mitigation

### Test-First Approach
- Write tests before fixing functionality
- Verify existing behavior before changes
- Maintain backward compatibility

### Incremental Improvements
- Start with simple unit tests
- Gradually add complex integration tests
- Focus on critical paths first

### Continuous Validation
- Run tests frequently during development
- Verify coverage metrics after each phase
- Monitor for regressions in existing functionality
