# Test Coverage Improvement Plan

## Current Status
- Total coverage: 43.34%
- Target coverage: 80%
- Files needing attention: 50+ files with coverage below 80%

## Priority Files for Coverage Improvement

### Zero Coverage (0%) - Highest Priority
1. `nodupe/core/cache/embedding_cache.py` - 0.00%
2. `nodupe/core/cache/hash_cache.py` - 0.00% 
3. `nodupe/core/cache/query_cache.py` - 0.0%
4. `nodupe/core/parallel.py` - 0.00%
5. `nodupe/core/pools.py` - 0.00%

### Very Low Coverage (10-20%) - High Priority
1. `nodupe/core/database/indexing.py` - 10.67%
2. `nodupe/core/database/embeddings.py` - 16.13%
3. `nodupe/core/backup.py` - 14.19%
4. `nodupe/core/confirmation.py` - 14.29%
5. `nodupe/core/database/transactions.py` - 23.43%

### Low Coverage (20-40%) - Medium Priority
1. `nodupe/core/database/repository_interface.py` - 26.92%
2. `nodupe/core/database/schema.py` - 22.64%
3. `nodupe/core/database/security.py` - 29.47%
4. `nodupe/core/plugin_system/security.py` - 21.62%
5. `nodupe/core/plugin_system/dependencies.py` - 11.56%
6. `nodupe/core/plugin_system/loader.py` - 15.66%
7. `nodupe/core/hash_progressive.py` - 17.21%
8. `nodupe/core/scan/progress.py` - 16.98%
9. `nodupe/core/plugin_system/compatibility.py` - 27.50%
10. `nodupe/core/plugin_system/hot_reload.py` - 36.21%

### Moderate Coverage (40-60%) - Lower Priority
1. `nodupe/core/archive_handler.py` - 41.58%
2. `nodupe/core/database/database.py` - 49.55%
3. `nodupe/core/limits.py` - 59.09%
4. `nodupe/core/plugin_system/discovery.py` - 65.65%

## Implementation Strategy

### Phase 1: Zero Coverage Files
- Create basic unit tests for all cache and parallel processing modules
- Focus on simple functionality tests and error handling
- Target: 60%+ coverage for each file

### Phase 2: Very Low Coverage Files
- Add comprehensive tests for database indexing and embeddings
- Test backup and confirmation workflows
- Focus on core functionality and edge cases

### Phase 3: Low Coverage Files
- Add plugin system tests (security, dependencies, loader, compatibility)
- Test hash progressive functionality
- Add scan progress tests

### Phase 4: Moderate Coverage Files
- Enhance archive handler tests
- Improve database core functionality tests
- Add limits module tests

## Expected Impact
- Phase 1: ~5-8% coverage improvement
- Phase 2: ~10-15% coverage improvement  
- Phase 3: ~15-20% coverage improvement
- Phase 4: ~5-10% coverage improvement
- Total: ~35-53% improvement (43% + 35-53% = 78-96% target)

## Risk Mitigation
- Start with simple unit tests for complex modules
- Focus on testing public APIs first
- Add integration tests after unit test coverage is solid
- Ensure existing functionality isn't broken by new tests
