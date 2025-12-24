# Implementation Plan: Plugin Management CLI Fixes

## Overview
Comprehensive fix for plugin management CLI issues including enable/disable functionality, database schema enhancements, help text improvements, documentation link fixes, and error handling improvements.

## Types
### New Type Definitions

**Plugin Teardown Interface** (to be added to base.py):
```python
@abstractmethod
def teardown(self) -> None:
    """Graceful teardown/cleanup hook for plugin unloading"""
    pass
```

**Plugin Error Response** (for structured error handling):
```python
@dataclass
class PluginOperationResult:
    ok: bool
    message: str
    plugin_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
```

## Files

### New Files to be Created
1. **nodupe/core/plugin_system/migrations.py** - Database migration utilities for plugin schema changes
2. **nodupe/core/plugin_system/error_handling.py** - Enhanced error handling for plugin operations

### Existing Files to be Modified

#### Core Files
1. **nodupe/core/main.py**
   - Update `_cmd_plugin_enable()` and `_cmd_plugin_disable()` methods
   - Add combined DB + runtime plugin state management
   - Implement graceful teardown/unload pattern
   - Add structured error handling

2. **nodupe/core/plugin_system/base.py**
   - Add `teardown()` abstract method to Plugin base class
   - Add `PluginOperationResult` dataclass

3. **nodupe/core/plugin_system/registry.py**
   - Add `disable_plugin()` and `enable_plugin()` methods
   - Implement plugin state management

4. **nodupe/core/database/schema.py**
   - Add new fields to plugins table: `plugin_path`, `entry_point`, `dependencies`, `description`
   - Add migration logic for existing databases

#### Documentation Files
1. **README.md**
   - Fix broken documentation links
   - Update plugin management examples

2. **nodupe/core/plugin_system/PLUGIN_DEVELOPMENT_GUIDE.md**
   - Add teardown implementation guidelines

### Files to be Deleted or Moved
None

### Configuration File Updates
None required

## Functions

### New Functions

#### nodupe/core/plugin_system/migrations.py
```python
def migrate_plugin_schema(connection: sqlite3.Connection) -> None:
    """Add missing fields to plugins table"""
    pass

def create_plugin_metadata_table(connection: sqlite3.Connection) -> None:
    """Create plugin metadata table if needed"""
    pass
```

#### nodupe/core/plugin_system/error_handling.py
```python
def handle_plugin_error(e: Exception, plugin_id: str, operation: str) -> PluginOperationResult:
    """Handle plugin errors with logging and user-friendly messages"""
    pass
```

### Modified Functions

#### nodupe/core/main.py

**Function: _cmd_plugin_enable()**
- **Current**: Only updates database
- **Change**: Update database AND load plugin into runtime registry
- **Implementation**: Use combined approach with rollback on failure

**Function: _cmd_plugin_disable()**
- **Current**: Only updates database
- **Change**: Update database AND unload plugin from runtime registry
- **Implementation**: Call teardown() if available, then remove from registry

#### nodupe/core/plugin_system/registry.py

**Function: disable_plugin()**
- **New**: Add method to disable and unload plugin
- **Implementation**: Mark as disabled, call teardown, remove from registry

**Function: enable_plugin()**
- **New**: Add method to enable and load plugin
- **Implementation**: Mark as enabled, load plugin, add to registry

## Classes

### Modified Classes

#### nodupe/core/plugin_system/base.py

**Class: Plugin**
- **Add**: `teardown()` abstract method
- **Add**: `PluginOperationResult` dataclass

#### nodupe/core/plugin_system/registry.py

**Class: PluginRegistry**
- **Add**: `disable_plugin()` method
- **Add**: `enable_plugin()` method
- **Modify**: Add plugin state tracking

## Dependencies
No new external dependencies required. All changes use standard library only.

## Testing

### Test File Requirements
1. **tests/core/test_plugin_commands.py** - Test enable/disable functionality
2. **tests/core/test_plugin_registry.py** - Test registry state management
3. **tests/core/test_plugin_lifecycle.py** - Test teardown/unload behavior

### Existing Test Modifications
- Update existing plugin tests to verify new functionality
- Add tests for error handling scenarios

### Validation Strategies
1. Test enable/disable commands with various plugin types
2. Verify database persistence and runtime state consistency
3. Test error handling and rollback scenarios
4. Validate teardown behavior for plugins with resources

## Implementation Order

### Step 1: Database Schema Migration
1. Add new fields to plugins table in schema.py
2. Create migration utilities in migrations.py
3. Update existing databases with new schema

### Step 2: Plugin Base Class Enhancements
1. Add `teardown()` abstract method to Plugin class
2. Add `PluginOperationResult` dataclass

### Step 3: Registry State Management
1. Add `disable_plugin()` and `enable_plugin()` methods
2. Implement plugin state tracking

### Step 4: CLI Command Updates
1. Update `_cmd_plugin_enable()` with combined DB + runtime logic
2. Update `_cmd_plugin_disable()` with teardown + unload logic
3. Add structured error handling

### Step 5: Help Text Improvements
1. Update plugin command help text
2. Add detailed examples section

### Step 6: Documentation Fixes
1. Fix broken links in README.md
2. Update plugin development guide

### Step 7: Testing
1. Create comprehensive test suite
2. Test all scenarios including edge cases
3. Verify backward compatibility

### Step 8: Error Handling Enhancements
1. Implement enhanced error logging
2. Add user-friendly error messages
3. Create error recovery mechanisms

## Implementation Details

### Database Schema Changes
```sql
ALTER TABLE plugins ADD COLUMN plugin_path TEXT;
ALTER TABLE plugins ADD COLUMN entry_point TEXT;
ALTER TABLE plugins ADD COLUMN dependencies TEXT; -- JSON string
ALTER TABLE plugins ADD COLUMN description TEXT;
```

### Combined Enable/Disable Logic
```python
def _cmd_plugin_enable(self, db, plugin_identifier: str) -> int:
    """Enable plugin with combined DB + runtime approach"""
    try:
        plugin_id = self._resolve_plugin_identifier(db, plugin_identifier)
        if not plugin_id:
            print(f"Plugin '{plugin_identifier}' not found")
            return 1

        # 1. Update database
        connection = db.get_connection()
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE plugins SET enabled = 1, updated_at = ? WHERE id = ?",
            (int(time.time()), plugin_id)
        )
        connection.commit()

        # 2. Load into runtime registry
        try:
            plugin = self._load_plugin_into_runtime(plugin_id)
            self.loader.plugin_registry.enable_plugin(plugin)
            print(f"Plugin enabled successfully (persisted and loaded)")
        except Exception as e:
            # Rollback if runtime load fails
            cursor.execute(
                "UPDATE plugins SET enabled = 0, updated_at = ? WHERE id = ?",
                (int(time.time()), plugin_id)
            )
            connection.commit()
            print(f"Error: Plugin enabled in DB but failed to load: {e}")
            return 1

        return 0

    except Exception as e:
        print(f"Error enabling plugin: {e}")
        return 1
```

### Graceful Teardown Pattern
```python
def disable_plugin(self, plugin_id: str) -> PluginOperationResult:
    """Disable plugin with graceful teardown"""
    # 1. Update database
    self._update_plugin_state(plugin_id, enabled=False)

    # 2. Attempt graceful teardown
    plugin = self.get_plugin(plugin_id)
    if plugin:
        try:
            if hasattr(plugin, "teardown"):
                plugin.teardown()
            self.unregister(plugin_id)
            return PluginOperationResult(
                ok=True,
                message="Plugin disabled and unloaded",
                plugin_id=plugin_id
            )
        except Exception as e:
            # Keep disabled in DB but log teardown failure
            logger.exception(f"Plugin {plugin_id} teardown failed")
            return PluginOperationResult(
                ok=False,
                message="Plugin disabled but teardown failed",
                plugin_id=plugin_id,
                details={"error": str(e)}
            )

    return PluginOperationResult(
        ok=True,
        message="Plugin disabled",
        plugin_id=plugin_id
    )
```

### Enhanced Error Handling
```python
def handle_plugin_error(e: Exception, plugin_id: str, operation: str) -> PluginOperationResult:
    """Handle plugin errors with structured response"""
    logger.exception(f"Plugin {operation} failed for {plugin_id}")

    # User-friendly message
    user_message = f"Failed to {operation} plugin: {str(e)}"

    # Technical details for logging
    details = {
        "operation": operation,
        "plugin_id": plugin_id,
        "error_type": type(e).__name__,
        "timestamp": time.time()
    }

    return PluginOperationResult(
        ok=False,
        message=user_message,
        plugin_id=plugin_id,
        details=details
    )
```

## Backward Compatibility

### Database Migration Strategy
- Add new columns as nullable to maintain compatibility
- Provide migration scripts for existing installations
- Ensure all new functionality works with old schema (with limited features)

### Plugin Interface Compatibility
- Make `teardown()` method optional (provide default no-op implementation)
- Maintain existing plugin loading interfaces
- Add new functionality as extensions rather than breaking changes

## Performance Considerations

### Database Operations
- Batch database updates where possible
- Use transactions for atomic operations
- Add appropriate indexes for new fields

### Plugin Loading/Unloading
- Implement lazy loading for plugins when possible
- Cache plugin metadata to avoid repeated file system access
- Use efficient data structures for plugin registry

## Security Considerations

### Error Handling
- Avoid exposing sensitive information in error messages
- Log detailed errors but show user-friendly messages
- Implement proper exception handling to prevent crashes

### Plugin Management
- Validate plugin paths and identifiers
- Implement proper access control for plugin operations
- Add input validation for all plugin-related commands

## Documentation Updates

### README.md Changes
- Fix broken documentation links
- Update plugin management examples
- Add troubleshooting section for plugin issues

### Plugin Development Guide
- Add teardown implementation guidelines
- Update best practices for plugin lifecycle management
- Add examples of proper error handling

## Monitoring and Observability

### Logging Enhancements
- Add detailed logging for plugin operations
- Include plugin identifiers in all log messages
- Log operation durations for performance monitoring

### Metrics
- Track plugin enable/disable operations
- Monitor plugin loading times
- Count plugin errors and failures

## Rollback Strategy

### Database Changes
- Provide SQL scripts to revert schema changes if needed
- Implement backup/restore functionality for plugin data
- Add versioning to plugin metadata

### Code Changes
- Maintain backward compatibility in all changes
- Provide feature flags for new functionality
- Implement comprehensive testing for rollback scenarios

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Verify error handling and edge cases
- Test database operations with mock connections

### Integration Tests
- Test complete enable/disable workflows
- Verify database and runtime consistency
- Test plugin lifecycle management

### End-to-End Tests
- Test CLI commands with real plugin scenarios
- Verify user experience and error messages
- Test performance with multiple plugins

## Implementation Timeline

### Phase 1: Foundation (1-2 days)
- Database schema updates
- Plugin base class enhancements
- Registry state management

### Phase 2: Core Functionality (2-3 days)
- CLI command updates
- Error handling improvements
- Basic testing

### Phase 3: Polish (1-2 days)
- Help text improvements
- Documentation updates
- Comprehensive testing

### Phase 4: Deployment (1 day)
- Final validation
- Rollout planning
- Monitoring setup

## Success Criteria

### Functional Requirements
- Plugin enable/disable commands work correctly
- Database schema supports all required fields
- Error handling provides useful information
- Help text is clear and comprehensive

### Non-Functional Requirements
- No breaking changes to existing functionality
- Performance impact is minimal
- Documentation is accurate and complete
- All tests pass successfully

## Risk Assessment

### High Risk Items
- Database migration on production systems
- Plugin unloading with active resources
- Backward compatibility issues

### Mitigation Strategies
- Thorough testing of migration scripts
- Graceful degradation for unload failures
- Comprehensive backward compatibility testing

## Contingency Plans

### Database Migration Issues
- Provide manual migration instructions
- Implement fallback to old schema if needed
- Add data validation and repair tools

### Plugin Compatibility Issues
- Maintain old interfaces alongside new ones
- Provide adapter classes for legacy plugins
- Implement plugin compatibility mode

## Post-Implementation Review

### Monitoring
- Track plugin operation success rates
- Monitor error rates and types
- Collect user feedback on new features

### Continuous Improvement
- Address any issues found in production
- Optimize based on performance data
- Enhance documentation based on user feedback

## Implementation Checklist

- [ ] Database schema migration scripts
- [ ] Plugin base class updates
- [ ] Registry state management
- [ ] CLI command enhancements
- [ ] Error handling improvements
- [ ] Help text updates
- [ ] Documentation fixes
- [ ] Comprehensive test suite
- [ ] Backward compatibility verification
- [ ] Performance testing
- [ ] Security review
- [ ] User acceptance testing
- [ ] Deployment planning
- [ ] Monitoring setup
- [ ] Post-implementation review
