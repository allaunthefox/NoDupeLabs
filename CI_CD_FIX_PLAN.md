# CI/CD Pipeline Fix Plan

## Summary of CI/CD Test Results

I ran the CI/CD pipeline locally and identified **2 critical errors** that prevent the tests from running:

### Errors Found:

1. **ModuleNotFoundError: No module named 'nodupe.core.progress_tracker'**
   - File: `tests/core/test_progress_tracker.py:6`
   - Issue: The `ProgressTracker` module is referenced but doesn't exist

2. **ImportError: cannot import name 'PluginBase' from 'nodupe.core.plugin_system'**
   - File: `nodupe/plugins/leap_year/leap_year.py:30`
   - Issue: `PluginBase` is not exported from the plugin_system module

## Detailed Analysis

### Error 1: Missing ProgressTracker Module
- **Location**: `tests/core/test_progress_tracker.py`
- **Problem**: Test file exists but the actual module `nodupe.core.progress_tracker` is missing
- **Impact**: Prevents test collection and execution
- **Root Cause**: The module was referenced in tests but never implemented

### Error 2: Missing PluginBase Export
- **Location**: `nodupe/plugins/leap_year/leap_year.py`
- **Problem**: `PluginBase` class is imported from `nodupe.core.plugin_system` but not exported
- **Impact**: Breaks plugin system functionality
- **Root Cause**: `PluginBase` exists in the codebase but is not properly exported from the module's `__init__.py`

## Fix Plan

### Priority 1: Fix Plugin System Export (High Priority)
**File**: `nodupe/core/plugin_system/__init__.py`

**Action**: Add `PluginBase` to the module exports
```python
# Add this import and export
from .base import PluginBase  # or wherever PluginBase is defined

__all__ = ['PluginBase', 'PluginRegistry', 'PluginLoader', ...]  # existing exports
```

**Rationale**: This is a critical dependency for the plugin system and affects multiple components.

### Priority 2: Create Missing ProgressTracker Module (Medium Priority)
**File**: `nodupe/core/progress_tracker.py`

**Action**: Create the missing module with basic progress tracking functionality
```python
"""Progress tracking utilities for long-running operations."""

from typing import Optional, Callable
import time

class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, total: int, description: str = "Progress"):
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current += increment
        self._show_progress()
    
    def _show_progress(self) -> None:
        """Display current progress."""
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        print(f"{self.description}: {self.current}/{self.total} ({percent:.1f}%) - {elapsed:.1f}s")
```

**Rationale**: This is needed for test execution but doesn't block core functionality.

## Additional Issues Identified

### Plugin Discovery Issues
- Multiple plugins show: `Failed to load plugin: 'PluginInfo' object has no attribute 'path'`
- This suggests plugin discovery is not working correctly
- May be related to the PluginBase import issue

### Schema Issues (Previously Fixed)
- ✅ **RESOLVED**: Database schema issue with missing `status` column
- The bootstrap now works correctly after our fix

## Implementation Steps

1. **Fix PluginBase Export** (15 minutes)
   - Locate where `PluginBase` is defined
   - Update `nodupe/core/plugin_system/__init__.py` to export it
   - Test the leap year plugin import

2. **Create ProgressTracker Module** (20 minutes)
   - Create the missing module with basic functionality
   - Ensure it matches the test expectations
   - Run tests to verify

3. **Verify Plugin System** (15 minutes)
   - Test plugin loading after fixes
   - Check if plugin discovery issues are resolved

4. **Run Full Test Suite** (30 minutes)
   - Execute all tests to identify any remaining issues
   - Check coverage requirements (80% threshold)

## Expected Outcomes

After implementing these fixes:
- ✅ Test collection will succeed
- ✅ Plugin system will work correctly
- ✅ Core functionality will be testable
- ✅ CI/CD pipeline will pass the test phase

## Risk Assessment

- **Low Risk**: These are straightforward fixes with clear solutions
- **Dependencies**: PluginBase fix must be done before ProgressTracker
- **Testing**: Each fix can be tested independently

## Next Steps

1. Implement Priority 1 fix (PluginBase export)
2. Implement Priority 2 fix (ProgressTracker module)
3. Re-run CI/CD pipeline to verify fixes
4. Address any remaining test failures or coverage issues
