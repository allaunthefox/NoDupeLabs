# CLI Test Plan

## Overview
This document outlines the comprehensive test plan for CLI command testing in Phase 6. The goal is to ensure all CLI commands work correctly, handle errors gracefully, and provide proper user feedback.

## CLI Architecture Analysis

### Main Components:
1. **nodupe/core/main.py** - Main CLI entry point with argparse
2. **nodupe/core/cli/__init__.py** - CLI handler and argument parsing
3. **nodupe/plugins/commands/__init__.py** - Command implementations
4. **nodupe/plugins/commands/*.py** - Individual command implementations

### Key Commands Identified:
- `scan` - File scanning and duplicate detection
- `apply` - Apply actions to duplicates
- `similarity` - Similarity analysis
- `version` - Show version information
- `help` - Show help information

## Test Strategy

### 1. CLI Argument Parsing Tests
- Test valid command invocations
- Test invalid command invocations
- Test help flag functionality
- Test version flag functionality
- Test argument validation

### 2. CLI Command Execution Tests
- Test scan command execution
- Test apply command execution
- Test similarity command execution
- Test command error handling
- Test command output formatting

### 3. CLI Error Handling Tests
- Test invalid arguments
- Test missing required arguments
- Test invalid file paths
- Test permission errors
- Test graceful error messages

### 4. CLI Help and Documentation Tests
- Test help command output
- Test help for specific commands
- Test help formatting
- Test help completeness

### 5. CLI Integration Tests
- Test end-to-end workflows
- Test command chaining
- Test file system interactions
- Test plugin integration

## Test Implementation Plan

### Test File Structure:
```
tests/core/test_cli.py
tests/core/test_cli_commands.py
tests/core/test_cli_errors.py
tests/core/test_cli_integration.py
```

### Test Implementation Steps:

1. **Create test_cli.py** - Basic CLI argument parsing and help tests
2. **Create test_cli_commands.py** - Individual command execution tests
3. **Create test_cli_errors.py** - Error handling and edge case tests
4. **Create test_cli_integration.py** - End-to-end integration tests

### Test Coverage Goals:
- 100% command coverage
- 100% argument validation coverage
- 100% error handling coverage
- 90%+ integration test coverage

## Test Data Requirements

### Test Directories:
- `tests/test_data/cli/` - Test files and directories
- `tests/test_data/cli/valid_files/` - Valid test files
- `tests/test_data/cli/invalid_files/` - Invalid test files
- `tests/test_data/cli/edge_cases/` - Edge case files

### Test File Types:
- Empty files
- Small files
- Large files
- Binary files
- Text files with various encodings
- Files with special characters in names

## Test Execution Plan

1. Implement basic CLI tests
2. Run tests and fix issues
3. Implement command execution tests
4. Run tests and fix issues
5. Implement error handling tests
6. Run tests and fix issues
7. Implement integration tests
8. Run final test suite
9. Update focus chain

## Success Criteria

- All CLI commands work as expected
- All error conditions handled gracefully
- Help system comprehensive and accurate
- 95%+ test coverage for CLI components
- All tests passing
- Focus chain updated with completion status
