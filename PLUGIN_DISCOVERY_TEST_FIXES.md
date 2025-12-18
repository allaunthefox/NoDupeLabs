# Plugin Discovery Test Fixes

## Overview
Fixed 5 failing tests in `tests/plugins/test_plugin_discovery.py` that were failing due to mock/real object mismatches.

## Root Cause
The tests were failing because:
1. **Mock Scope Issue**: Tests mocked `nodupe.core.plugin_system.discovery.Path` but passed real `Path` objects as parameters
2. **Real Path Behavior**: When real `Path` objects were used, they tried to access actual filesystem paths that don't exist
3. **Mock/Real Mismatch**: The mocked `Path` class didn't affect the real `Path` objects passed as arguments

## Fixed Tests

### 1. `test_discover_plugins_in_directory`
**Issue**: Mock set `iterdir.return_value = []` but expected plugins to be found
**Fix**: Created proper mock directory structure with realistic mock files that have all necessary attributes (`is_file()`, `suffix`, `stem`, `exists()`, `stat()`)

### 2. `test_mass_plugin_discovery`
**Issue**: Performance test with mocking issues
**Fix**: Created 100 mock plugin files with proper attributes and realistic directory structure

### 3. `test_plugin_discovery_performance`
**Issue**: Performance test with mocking issues
**Fix**: Created 1000 mock plugin files with proper attributes and realistic directory structure

### 4. `test_discover_plugins_with_complex_metadata`
**Issue**: Metadata parsing test with mock Path issues
**Fix**: Created mock file with complex metadata content and actual Python code, added `__str__` method to mock file for proper Path handling

### 5. `test_discover_plugins_with_duplicate_names`
**Issue**: Duplicate handling test with mocking issues
**Fix**: Created two mock files with same name but different paths, each with proper `__str__` method

## Key Fix Patterns

### 1. Proper Mock File Structure
```python
mock_file = MagicMock()
mock_file.is_file.return_value = True
mock_file.suffix = '.py'
mock_file.stem = 'plugin_name'
mock_file.exists.return_value = True
mock_file.stat.return_value.st_size = 100
mock_file.__str__ = lambda: "/test/plugin.py"
```

### 2. Proper Mock Directory Structure
```python
mock_dir = MagicMock()
mock_dir.exists.return_value = True
mock_dir.iterdir.return_value = [mock_file1, mock_file2, ...]
```

### 3. Realistic File Content
- Added actual Python code to make files look like real plugins
- Used `__str__` methods on mock files for proper Path handling
- Ensured mock files have all attributes that the discovery code expects

## Testing Approach
- **No Mocking of `_extract_plugin_info`**: Let the actual parsing logic work on mock file content
- **Realistic Mocks**: Mock objects that behave like real filesystem objects
- **Proper Attributes**: All mock files have the attributes that the discovery code checks

## Results
All 5 previously failing tests now pass:
- ✅ `test_discover_plugins_in_directory`
- ✅ `test_mass_plugin_discovery`
- ✅ `test_plugin_discovery_performance`
- ✅ `test_discover_plugins_with_complex_metadata`
- ✅ `test_discover_plugins_with_duplicate_names`

## Lessons Learned
1. When mocking filesystem operations, ensure mock objects have all the attributes that the code expects
2. Use `__str__` methods on mock files for proper Path handling
3. Don't mock the parsing logic itself - let it work on realistic mock content
4. Create mock structures that mirror real filesystem behavior
