# CI/CD Pipeline Fix - Step-by-Step Action Guide

## Overview
This guide provides detailed, actionable steps to fix the CI/CD pipeline failures identified in the NoDupeLabs project. The pipeline currently fails due to two critical import errors that prevent test collection and execution.

## Current Issues Identified

### 1. Missing ProgressTracker Module
**Error**: `ModuleNotFoundError: No module named 'nodupe.core.progress_tracker'`
**Location**: `tests/core/test_progress_tracker.py:6`
**Impact**: Prevents test collection and execution
**Root Cause**: Test file exists but the actual module `nodupe.core.progress_tracker` is missing

### 2. Missing PluginBase and PluginMetadata Exports
**Error**: `ImportError: cannot import name 'PluginBase' from 'nodupe.core.plugin_system'`
**Location**: `nodupe/plugins/leap_year/leap_year.py:30`
**Impact**: Breaks plugin system functionality
**Root Cause**: `PluginBase` and `PluginMetadata` are not properly exported from the plugin system module

## Step-by-Step Fix Implementation

### Phase 1: Fix Plugin System Exports (Priority: High)

#### Step 1.1: Identify PluginBase Implementation
1. **Check current implementation**: The `PluginBase` class is actually named `Plugin` in `nodupe/core/plugin_system/base.py`
2. **Verify the class name**: Open `nodupe/core/plugin_system/base.py` and confirm the class is defined as `class Plugin(ABC):`
3. **Check PluginMetadata**: Determine if `PluginMetadata` is defined elsewhere or needs to be created

#### Step 1.2: Update Plugin System __init__.py
1. **Open the file**: `nodupe/core/plugin_system/__init__.py`
2. **Add missing imports**: Update the imports to include `Plugin` (renamed from `PluginBase`) and create `PluginMetadata`
3. **Update __all__ list**: Add `'Plugin'` and `'PluginMetadata'` to the exports

**Implementation Details**:
```python
# Current content of nodupe/core/plugin_system/__init__.py:
from .base import Plugin
from .registry import PluginRegistry
from .loader import PluginLoader
# ... other imports

# Need to add PluginMetadata - check if it exists or create it
# If PluginMetadata doesn't exist, we need to create it in base.py or a new file

__all__ = [
    'Plugin',           # This is actually PluginBase
    'PluginMetadata',   # Need to create this
    'PluginRegistry',
    'PluginLoader',
    # ... existing exports
]
```

#### Step 1.3: Create PluginMetadata Class
1. **Determine location**: Create `PluginMetadata` in `nodupe/core/plugin_system/base.py` or a new file
2. **Define the class**: Based on usage in `leap_year.py`, `PluginMetadata` should have fields: `name`, `version`, `description`, `author`, `license`, `dependencies`, `tags`
3. **Implementation options**:
   - Option A: Create as a dataclass in `base.py`
   - Option B: Create as a NamedTuple
   - Option C: Create as a regular class with __init__

**Recommended implementation** (dataclass in base.py):
```python
from dataclasses import dataclass
from typing import List

@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    description: str
    author: str
    license: str
    dependencies: List[str]
    tags: List[str]
```

#### Step 1.4: Update LeapYear Plugin Import
1. **Open the file**: `nodupe/plugins/leap_year/leap_year.py`
2. **Update import statement**: Change `from nodupe.core.plugin_system import PluginBase, PluginMetadata` to use the correct names
3. **Update class inheritance**: Change `class LeapYearPlugin(PluginBase):` to `class LeapYearPlugin(Plugin):`

**Updated import**:
```python
from nodupe.core.plugin_system import Plugin, PluginMetadata
```

### Phase 2: Create Missing ProgressTracker Module (Priority: Medium)

#### Step 2.1: Analyze Test Requirements
1. **Examine test file**: Review `tests/core/test_progress_tracker.py` to understand required interface
2. **Identify required methods**: Based on tests, `ProgressTracker` needs:
   - `__init__(self, total: int)`
   - `update(self, increment: int = 1)`
   - `get_progress(self) -> float`
   - `get_elapsed_time(self) -> float`
   - `get_eta(self) -> Optional[float]`
   - `get_rate(self) -> float`
   - `reset(self)`

#### Step 2.2: Create ProgressTracker Module
1. **Create file**: `nodupe/core/progress_tracker.py`
2. **Implement class**: Create `ProgressTracker` class with required methods
3. **Add proper typing**: Include type hints for all methods
4. **Add documentation**: Include docstrings for class and methods

**Implementation template**:
```python
"""Progress tracking utilities for long-running operations."""

import time
from typing import Optional

class ProgressTracker:
    """Track progress of long-running operations."""
    
    def __init__(self, total: int, description: str = "Progress"):
        """Initialize progress tracker.
        
        Args:
            total: Total number of items to process
            description: Description of the operation
        """
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment."""
        self.current += increment
        # Clamp to total
        if self.current > self.total:
            self.current = self.total
    
    def get_progress(self) -> float:
        """Get current progress as percentage."""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100.0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return time.time() - self.start_time
    
    def get_eta(self) -> Optional[float]:
        """Get estimated time of arrival in seconds."""
        if self.current == 0:
            return None
        elapsed = self.get_elapsed_time()
        rate = self.current / elapsed
        remaining = self.total - self.current
        return remaining / rate if rate > 0 else None
    
    def get_rate(self) -> float:
        """Get processing rate (items per second)."""
        elapsed = self.get_elapsed_time()
        return self.current / elapsed if elapsed > 0 else 0.0
    
    def reset(self) -> None:
        """Reset progress tracker."""
        self.current = 0
        self.start_time = time.time()
```

#### Step 2.3: Update Test Compatibility
1. **Verify test compatibility**: Ensure the implementation matches test expectations
2. **Check edge cases**: Handle zero total, negative increments, etc.
3. **Add error handling**: Consider adding validation for invalid inputs

### Phase 3: Verify and Test Fixes

#### Step 3.1: Run Individual Tests
1. **Test ProgressTracker**: Run `pytest tests/core/test_progress_tracker.py -v`
2. **Test LeapYear plugin**: Run `pytest tests/plugins/test_leap_year.py -v`
3. **Check for import errors**: Verify no more `ImportError` or `ModuleNotFoundError`

#### Step 3.2: Run Full Test Suite
1. **Execute all tests**: Run `pytest tests/ --cov=nodupe --cov-report=term-missing`
2. **Check coverage**: Ensure coverage meets 80% threshold
3. **Identify remaining failures**: Note any new test failures that appear

#### Step 3.3: Fix Additional Issues
1. **Plugin discovery issues**: Address `'PluginInfo' object has no attribute 'path'` errors
2. **Schema issues**: Verify database schema creation works correctly
3. **Plugin loading**: Ensure all plugins load without errors

### Phase 4: CI/CD Pipeline Validation

#### Step 4.1: Local CI/CD Simulation
1. **Install dependencies**: `pip install -r output/ci_artifacts/requirements.txt -r output/ci_artifacts/requirements-dev.txt`
2. **Run linting**: Execute `pylint nodupe/` and `markdownlint`
3. **Run security scan**: Test security scanner if available
4. **Build package**: Test `python -m build --sdist --wheel`

#### Step 4.2: GitHub Actions Workflow Check
1. **Review workflow files**: Check `.github/workflows/ci-cd.yml` and `.github/workflows/pr-validation.yml`
2. **Verify dependencies**: Ensure all required dependencies are in `output/ci_artifacts/requirements*.txt`
3. **Check cache configuration**: Verify cache keys are correct
4. **Test deployment steps**: Ensure PyPI deployment configuration is correct

#### Step 4.3: Dangerfile Validation
1. **Review Dangerfile**: Check `Dangerfile` for PR validation rules
2. **Test Danger locally**: Run `danger-python ci` to verify PR checks work
3. **Update rules if needed**: Adjust rules based on project requirements

## Implementation Order

1. **First**: Fix PluginBase/PluginMetadata exports (blocks plugin system)
2. **Second**: Create ProgressTracker module (enables test execution)
3. **Third**: Verify plugin discovery and loading
4. **Fourth**: Run full test suite and fix any remaining issues
5. **Fifth**: Validate CI/CD pipeline locally
6. **Sixth**: Push changes and monitor GitHub Actions execution

## Expected Outcomes

After implementing these fixes:
- ✅ Test collection will succeed (no more import errors)
- ✅ Plugin system will work correctly
- ✅ All tests will execute (coverage may still need improvement)
- ✅ CI/CD pipeline will pass the test phase
- ✅ PR validation will work correctly

## Risk Mitigation

- **Backup before changes**: Create a backup of critical files
- **Incremental testing**: Test each fix individually before proceeding
- **Version control**: Use git to track changes and enable rollback if needed
- **Documentation**: Update documentation to reflect changes

## Troubleshooting

### Common Issues and Solutions

1. **Import still fails after fixes**:
   - Check Python path and module structure
   - Verify `__init__.py` files exist in all packages
   - Clear Python cache (`__pycache__` directories)

2. **Plugin discovery errors persist**:
   - Check `PluginInfo` class definition
   - Verify plugin discovery logic in `nodupe/core/plugin_system/discovery.py`
   - Ensure plugin directories are correctly configured

3. **Test coverage below 80%**:
   - Run tests with coverage report to identify uncovered code
   - Add tests for uncovered modules
   - Consider adjusting coverage threshold if appropriate

4. **CI/CD pipeline still fails**:
   - Check GitHub Actions logs for specific error messages
   - Verify environment variables and secrets are set
   - Test workflow steps locally

## Post-Implementation Tasks

1. **Update documentation**: Update `CI_CD_FIX_PLAN.md` with results
2. **Create test report**: Document test results and coverage
3. **Monitor next PR**: Verify PR validation works correctly
4. **Schedule follow-up**: Plan for additional test coverage improvements

## References

- Original CI/CD Fix Plan: `CI_CD_FIX_PLAN.md`
- Test files: `tests/core/test_progress_tracker.py`, `tests/plugins/test_leap_year.py`
- Plugin system: `nodupe/core/plugin_system/`
- CI/CD configuration: `.github/workflows/ci-cd.yml`
- PR validation: `Dangerfile`
