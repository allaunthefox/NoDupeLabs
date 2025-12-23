# Coverage Improvement Plan

## Current Status
- Total coverage: 43.32%
- Target coverage: 80%
- Files needing attention: 50+ files with coverage below 80%

## Phase 1: Zero Coverage Files (Highest Priority)
Target: 60%+ coverage for each file

### Cache System Files
- `nodupe/core/cache/embedding_cache.py` - 0.00%
- `nodupe/core/cache/hash_cache.py` - 0.00% 
- `nodupe/core/cache/query_cache.py` - 0.0%

### Parallel Processing Files  
- `nodupe/core/parallel.py` - 0.00%
- `nodupe/core/pools.py` - 0.00%

### Command Files
- `nodupe/plugins/commands/archive.py` - 0.00%
- `nodupe/plugins/commands/mount.py` - 0.00%
- `nodupe/plugins/commands/plan.py` - 0.00%
- `nodupe/plugins/commands/rollback.py` - 0.00%

## Phase 2: Very Low Coverage Files (High Priority)
Target: 40%+ coverage for each file

### Database Files
- `nodupe/core/database/indexing.py` - 10.67%
- `nodupe/core/database/embeddings.py` - 16.13%
- `nodupe/core/database/transactions.py` - 23.43%

### Core Functionality Files
- `nodupe/core/backup.py` - 14.19%
- `nodupe/core/confirmation.py` - 14.29%
- `nodupe/core/hash_progressive.py` - 17.21%
- `nodupe/core/scan/progress.py` - 16.98%

## Phase 3: Low Coverage Files (Medium Priority)
Target: 60%+ coverage for each file

### Plugin System Files
- `nodupe/core/plugin_system/security.py` - 21.62%
- `nodupe/core/plugin_system/dependencies.py` - 11.56%
- `nodupe/core/plugin_system/loader.py` - 15.66%
- `nodupe/core/plugin_system/compatibility.py` - 27.50%
- `nodupe/core/plugin_system/hot_reload.py` - 36.21%

### Database Schema Files
- `nodupe/core/database/repository_interface.py` - 26.92%
- `nodupe/core/database/schema.py` - 22.64%
- `nodupe/core/database/security.py` - 29.47%

### Command Files
- `nodupe/plugins/commands/scan.py` - 38.71%
- `nodupe/plugins/commands/similarity.py` - 46.15%
- `nodupe/plugins/commands/verify.py` - 11.00%

## Phase 4: Moderate Coverage Files (Lower Priority)
Target: 70%+ coverage for each file

- `nodupe/core/archive_handler.py` - 41.58%
- `nodupe/core/database/database.py` - 49.55%
- `nodupe/core/limits.py` - 59.09%
- `nodupe/core/plugin_system/discovery.py` - 65.65%

## Implementation Strategy

### Week 1-2: Phase 1 - Zero Coverage
- Create basic unit tests for all cache and parallel processing modules
- Focus on simple functionality tests and error handling
- Create tests for archive and mount commands
- Expected improvement: ~5-8% total coverage

### Week 3-4: Phase 2 - Very Low Coverage
- Add comprehensive tests for database indexing and embeddings
- Test backup and confirmation workflows
- Test hash progressive functionality
- Expected improvement: ~10-15% total coverage

### Week 5-6: Phase 3 - Low Coverage
- Add plugin system tests (security, dependencies, loader, compatibility)
- Add scan and similarity command tests
- Test verify plugin functionality
- Expected improvement: ~15-20% total coverage

### Week 7-8: Phase 4 - Moderate Coverage
- Enhance archive handler tests
- Improve database core functionality tests
- Add limits module tests
- Expected improvement: ~5-10% total coverage

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

## Success Metrics
- [ ] Week 1: Phase 1 tests created for 50% of zero coverage files
- [ ] Week 2: Phase 1 complete, total coverage > 48%
- [ ] Week 4: Phase 2 complete, total coverage > 58%
- [ ] Week 6: Phase 3 complete, total coverage > 68%
- [ ] Week 8: Phase 4 complete, total coverage > 78%
