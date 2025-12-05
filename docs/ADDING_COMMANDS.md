# Adding Commands Guide

**Version:** 1.0
**Last Updated:** 2025-12-05

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Command Structure](#command-structure)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Using Dependency Injection](#using-dependency-injection)
6. [Argument Parsing](#argument-parsing)
7. [Testing Commands](#testing-commands)
8. [Best Practices](#best-practices)
9. [Examples](#examples)

---

## Introduction

NoDupeLabs uses a **Command Registry Pattern** that makes adding new commands straightforward. Commands are:

- **Thin wrappers** that validate inputs and coordinate dependencies
- **Registered dynamically** in a central registry
- **Independent** - adding a command doesn't modify CLI code
- **Testable** - use dependency injection for easy testing

### Architecture Overview

```text
CLI Entry Point
    ↓
COMMANDS Registry (commands/__init__.py)
    ↓
Command Function (commands/my_command.py)
    ↓
ServiceContainer (container.py)
    ↓
Orchestrator/Service (with injected dependencies)
```

---

## Quick Start

### 5-Minute Command

Here's the minimal steps to add a new command:

1. **Create command file:** `nodupe/commands/my_command.py`
2. **Implement function:** `def cmd_my_command(args, cfg): ...`
3. **Register command:** Add to `COMMANDS` dict in `commands/__init__.py`
4. **Add CLI arguments:** (if needed)

That's it! No CLI modification needed.

---

## Command Structure

### Minimal Command

```python
# nodupe/commands/my_command.py
"""My command implementation."""

def cmd_my_command(args, cfg: dict) -> int:
    """Execute my command.

    Args:
        args: Parsed CLI arguments (Namespace object)
        cfg: Configuration dictionary from nodupe.yml

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    print(f"My command running with args: {args}")
    return 0
```

### Command with DI

```python
# nodupe/commands/my_command.py
"""My command implementation."""
from ..container import get_container

def cmd_my_command(args, cfg: dict) -> int:
    """Execute my command with dependency injection.

    Args:
        args: Parsed CLI arguments
        cfg: Configuration dictionary

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    # Get container
    container = get_container()

    # Get services via DI
    db = container.get_db()
    telemetry = container.get_telemetry()

    # Use services
    telemetry.log('my_command:start', {})
    files = db.get_all()
    telemetry.log('my_command:complete', {'file_count': len(files)})

    return 0
```

### Command with Orchestrator

```python
# nodupe/commands/my_command.py
"""My command implementation with orchestrator."""
from ..container import get_container

def cmd_my_command(args, cfg: dict) -> int:
    """Execute my command using orchestrator pattern.

    Args:
        args: Parsed CLI arguments
        cfg: Configuration dictionary

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    # Get fully-configured orchestrator from container
    container = get_container()
    orchestrator = container.get_my_orchestrator()

    # Execute workflow
    try:
        results = orchestrator.execute(
            param1=args.param1,
            param2=cfg.get('my_setting', 'default'),
        )
        print(f"Success: {results}")
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
```

---

## Step-by-Step Guide

### Step 1: Create Command File

Create a new file in `nodupe/commands/`:

```bash
touch nodupe/commands/my_command.py
```

### Step 2: Implement Command Function

```python
# nodupe/commands/my_command.py
"""My command: does something useful.

This command demonstrates the basic structure of a NoDupeLabs command.
It shows validation, dependency injection, and error handling.
"""
import sys
from typing import Dict
from ..container import get_container

def cmd_my_command(args, cfg: Dict) -> int:
    """Execute my command.

    This is the main entry point for the 'my-command' CLI command.
    It validates inputs, gets dependencies from the container, and
    delegates actual work to an orchestrator or service.

    Args:
        args: Parsed CLI arguments with attributes:
            - args.input: Input file/directory
            - args.output: Output location
            - args.verbose: Verbosity flag
        cfg: Configuration dict from nodupe.yml with keys:
            - 'my_setting': Custom setting
            - 'parallelism': Worker threads

    Returns:
        Exit code:
            - 0: Success
            - 1: General error
            - 2: Validation error

    Example:
        >>> args = Namespace(input='/data', output='/out', verbose=True)
        >>> cfg = {'my_setting': 'value', 'parallelism': 4}
        >>> cmd_my_command(args, cfg)
        0
    """
    # 1. Validate inputs
    if not args.input:
        print("Error: --input required", file=sys.stderr)
        return 2

    # 2. Get dependencies via DI
    container = get_container()
    db = container.get_db()
    telemetry = container.get_telemetry()

    # 3. Log start
    telemetry.log('my_command:start', {
        'input': args.input,
        'output': args.output,
    })

    # 4. Execute business logic
    try:
        # Your logic here
        result = perform_operation(args.input, args.output, db)

        telemetry.log('my_command:success', {'result': result})
        print(f"Success: {result}")
        return 0

    except FileNotFoundError as e:
        telemetry.log('my_command:error', {'error': str(e)})
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1

    except Exception as e:
        telemetry.log('my_command:error', {'error': str(e)})
        print(f"Error: {e}", file=sys.stderr)
        return 1


def perform_operation(input_path, output_path, db):
    """Actual business logic (separate from CLI concerns)."""
    # Implementation here
    pass
```

### Step 3: Register Command

Add your command to the registry in `nodupe/commands/__init__.py`:

```python
# nodupe/commands/__init__.py
from .my_command import cmd_my_command  # Import

COMMANDS: Dict[str, Callable] = {
    "init": cmd_init,
    "scan": cmd_scan,
    # ... existing commands ...
    "my-command": cmd_my_command,  # Add to registry
}

__all__ = [
    "COMMANDS",
    # ... existing exports ...
    "cmd_my_command",  # Export for direct import if needed
]
```

### Step 4: Add CLI Arguments (Optional)

If your command needs arguments, add them to the CLI parser.

**Location:** Wherever argument parsing happens (typically `cli` module or entry point)

```python
# Add subcommand parser
my_command_parser = subparsers.add_parser(
    'my-command',
    help='Do something useful'
)

# Add arguments
my_command_parser.add_argument(
    'input',
    help='Input file or directory'
)

my_command_parser.add_argument(
    '-o', '--output',
    default='output',
    help='Output location (default: output)'
)

my_command_parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='Enable verbose output'
)
```

### Step 5: Test Your Command

```bash
# Run your command
nodupe my-command /path/to/input --output /path/to/output --verbose

# Check exit code
echo $?
```

---

## Using Dependency Injection

### Get Services from Container

```python
from ..container import get_container

def cmd_my_command(args, cfg):
    container = get_container()

    # Get individual services
    db = container.get_db()
    telemetry = container.get_telemetry()
    backend = container.get_backend()
    pm = container.get_plugin_manager()

    # Use services
    db.upsert_files([...])
    telemetry.log('event', {...})
```

### Get Orchestrators

For complex workflows, use an orchestrator:

```python
def cmd_my_command(args, cfg):
    container = get_container()

    # Get orchestrator (all deps injected automatically)
    orchestrator = container.get_scanner()

    # Execute workflow
    return orchestrator.scan(
        roots=args.paths,
        hash_algo=cfg.get('hash_algo'),
        workers=cfg.get('parallelism'),
    )
```

### Create Custom Orchestrator

If your command needs a custom orchestrator:

1. **Create orchestrator class:**

```python
# nodupe/my_orchestrator.py
class MyOrchestrator:
    def __init__(self, db, telemetry, my_service):
        self.db = db
        self.telemetry = telemetry
        self.my_service = my_service

    def execute(self, param1, param2):
        # Workflow logic here
        pass
```

2. **Add to container:**

```python
# nodupe/container.py
def get_my_orchestrator(self) -> MyOrchestrator:
    if 'my_orchestrator' not in self._services:
        self._services['my_orchestrator'] = MyOrchestrator(
            db=self.get_db(),
            telemetry=self.get_telemetry(),
            my_service=self.get_my_service(),
        )
    return self._services['my_orchestrator']
```

3. **Use in command:**

```python
def cmd_my_command(args, cfg):
    container = get_container()
    orchestrator = container.get_my_orchestrator()
    return orchestrator.execute(args.param1, args.param2)
```

---

## Argument Parsing

### Common Argument Patterns

#### Input Paths

```python
parser.add_argument(
    'paths',
    nargs='+',
    help='Paths to process'
)
```

#### Optional Flags

```python
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show what would be done without making changes'
)
```

#### Choices

```python
parser.add_argument(
    '--format',
    choices=['json', 'yaml', 'csv'],
    default='json',
    help='Output format'
)
```

#### Integer Arguments

```python
parser.add_argument(
    '--workers',
    type=int,
    default=4,
    help='Number of worker threads'
)
```

### Accessing Arguments in Command

```python
def cmd_my_command(args, cfg):
    # Access arguments
    paths = args.paths                    # Required positional
    output = args.output                  # Optional with default
    dry_run = args.dry_run               # Boolean flag
    format_type = getattr(args, 'format', 'json')  # With fallback
```

---

## Testing Commands

### Unit Test (with Mocks)

```python
# tests/test_my_command.py
from unittest.mock import Mock, patch
import pytest
from nodupe.commands.my_command import cmd_my_command

def test_my_command_success():
    # Create mock args
    args = Mock(
        input='/test/input',
        output='/test/output',
        verbose=True
    )

    # Create mock config
    cfg = {
        'my_setting': 'test_value',
        'parallelism': 2
    }

    # Mock container
    with patch('nodupe.commands.my_command.get_container') as mock_container:
        mock_db = Mock()
        mock_telemetry = Mock()

        mock_container.return_value.get_db.return_value = mock_db
        mock_container.return_value.get_telemetry.return_value = mock_telemetry

        # Execute command
        result = cmd_my_command(args, cfg)

        # Verify
        assert result == 0
        mock_telemetry.log.assert_called()
        mock_db.get_all.assert_called()

def test_my_command_validation_error():
    # Test with missing required argument
    args = Mock(input=None, output='/out', verbose=False)
    cfg = {}

    result = cmd_my_command(args, cfg)

    assert result == 2  # Validation error code
```

### Integration Test (with Real Container)

```python
# tests/test_my_command_integration.py
from pathlib import Path
import pytest
from nodupe.container import get_container
from nodupe.commands.my_command import cmd_my_command
from nodupe.db import DB

def test_my_command_integration(tmp_path):
    # Setup test environment
    test_input = tmp_path / "input"
    test_input.mkdir()
    (test_input / "file.txt").write_text("test content")

    test_output = tmp_path / "output"
    test_db = tmp_path / "test.db"

    # Override container services
    container = get_container()
    container.override('db', DB(test_db))

    # Create args
    args = Mock(
        input=str(test_input),
        output=str(test_output),
        verbose=False
    )
    cfg = {'my_setting': 'test'}

    # Execute command
    result = cmd_my_command(args, cfg)

    # Verify results
    assert result == 0
    assert test_output.exists()

    # Cleanup
    container.clear_overrides()
```

---

## Best Practices

### 1. Keep Commands Thin

```python
# ✅ GOOD: Command delegates to orchestrator
def cmd_my_command(args, cfg):
    container = get_container()
    orchestrator = container.get_my_orchestrator()
    return orchestrator.execute(args.input)

# ❌ BAD: Command contains business logic
def cmd_my_command(args, cfg):
    db = DB('nodupe.db')
    files = []
    for path in walk_files(args.input):
        hash_val = compute_hash(path)
        files.append({'path': path, 'hash': hash_val})
    db.upsert_files(files)
    # 50 more lines of business logic...
```

### 2. Use Type Hints

```python
# ✅ GOOD: Clear types
def cmd_my_command(args, cfg: Dict[str, Any]) -> int:
    pass

# ❌ BAD: No types
def cmd_my_command(args, cfg):
    pass
```

### 3. Validate Inputs Early

```python
def cmd_my_command(args, cfg):
    # Validate at the start
    if not args.input:
        print("Error: --input required", file=sys.stderr)
        return 2

    if not Path(args.input).exists():
        print(f"Error: Path not found: {args.input}", file=sys.stderr)
        return 1

    # Continue with valid inputs
    # ...
```

### 4. Use Consistent Exit Codes

```python
# Standard exit codes
return 0   # Success
return 1   # General error
return 2   # Validation error
return 130 # Interrupted by user (Ctrl+C)
```

### 5. Log Important Events

```python
def cmd_my_command(args, cfg):
    container = get_container()
    telemetry = container.get_telemetry()

    # Log start
    telemetry.log('my_command:start', {'input': args.input})

    try:
        result = do_work()
        # Log success
        telemetry.log('my_command:success', {'result': result})
        return 0
    except Exception as e:
        # Log error
        telemetry.log('my_command:error', {'error': str(e)})
        return 1
```

### 6. Handle Errors Gracefully

```python
def cmd_my_command(args, cfg):
    try:
        return execute_command(args, cfg)
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
```

### 7. Document Your Command

```python
def cmd_my_command(args, cfg: Dict) -> int:
    """Execute my command.

    Performs X operation on Y to achieve Z. This command
    requires A and optionally uses B for C.

    Args:
        args: CLI arguments with:
            - input (str): Input path
            - output (str): Output path
        cfg: Config dict with:
            - my_setting (str): Custom setting

    Returns:
        Exit code (0=success, 1=error, 2=validation error)

    Example:
        $ nodupe my-command /data --output /results
    """
```

---

## Examples

### Example 1: Simple Query Command

```python
# nodupe/commands/list_duplicates.py
"""List duplicate files."""
from ..container import get_container

def cmd_list_duplicates(args, cfg):
    """List files with duplicate hashes.

    Args:
        args: CLI arguments (none needed)
        cfg: Configuration dict

    Returns:
        Exit code (0=success)
    """
    container = get_container()
    db = container.get_db()

    # Query duplicates
    duplicates = db.find_duplicates()

    # Display results
    if not duplicates:
        print("No duplicates found")
        return 0

    print(f"Found {len(duplicates)} duplicate groups:\n")
    for hash_val, paths in duplicates.items():
        print(f"Hash: {hash_val}")
        for path in paths:
            print(f"  - {path}")
        print()

    return 0
```

### Example 2: Command with Validation

```python
# nodupe/commands/export_metadata.py
"""Export file metadata."""
import sys
from pathlib import Path
from ..container import get_container

def cmd_export_metadata(args, cfg):
    """Export metadata to JSON/YAML.

    Args:
        args: CLI arguments with output_path and format
        cfg: Configuration dict

    Returns:
        Exit code
    """
    # Validate format
    if args.format not in ('json', 'yaml'):
        print(f"Error: Invalid format '{args.format}'", file=sys.stderr)
        print("Supported: json, yaml", file=sys.stderr)
        return 2

    # Validate output path
    output_path = Path(args.output_path)
    if output_path.exists():
        if not args.overwrite:
            print(f"Error: {output_path} exists (use --overwrite)", file=sys.stderr)
            return 1

    # Get dependencies
    container = get_container()
    db = container.get_db()
    telemetry = container.get_telemetry()

    # Export
    try:
        telemetry.log('export:start', {'output': str(output_path)})

        files = db.get_all()
        export_to_file(files, output_path, args.format)

        telemetry.log('export:success', {'file_count': len(files)})
        print(f"Exported {len(files)} files to {output_path}")
        return 0

    except Exception as e:
        telemetry.log('export:error', {'error': str(e)})
        print(f"Export failed: {e}", file=sys.stderr)
        return 1
```

### Example 3: Command with Progress

```python
# nodupe/commands/rebuild_index.py
"""Rebuild similarity index."""
from ..container import get_container

def cmd_rebuild_index(args, cfg):
    """Rebuild similarity search index.

    Args:
        args: CLI arguments with backend selection
        cfg: Configuration dict

    Returns:
        Exit code
    """
    container = get_container()
    db = container.get_db()
    telemetry = container.get_telemetry()

    # Get all files with embeddings
    files = db.get_files_with_embeddings()

    if not files:
        print("No files with embeddings found")
        return 0

    print(f"Rebuilding index for {len(files)} files...")

    telemetry.log('rebuild_index:start', {'file_count': len(files)})

    try:
        # Import here to avoid loading if not needed
        from ..similarity import make_index, save_index_to_file

        # Create index
        index = make_index(backend=args.backend, dim=cfg.get('similarity_dim', 16))

        # Add vectors with progress
        for i, file_record in enumerate(files, 1):
            if i % 100 == 0:
                print(f"Progress: {i}/{len(files)}")

            index.add(
                [file_record['path']],
                [file_record['embedding']]
            )

        # Save index
        index_path = cfg.get('index_path', 'similarity.npz')
        save_index_to_file(index, index_path, format='npz')

        telemetry.log('rebuild_index:success', {
            'file_count': len(files),
            'index_path': index_path
        })

        print(f"Index saved to {index_path}")
        return 0

    except Exception as e:
        telemetry.log('rebuild_index:error', {'error': str(e)})
        print(f"Failed to rebuild index: {e}", file=sys.stderr)
        return 1
```

---

## Summary

**To add a new command:**

1. ✅ Create `nodupe/commands/my_command.py`
2. ✅ Implement `cmd_my_command(args, cfg) -> int`
3. ✅ Register in `COMMANDS` dict
4. ✅ Add CLI arguments (if needed)
5. ✅ Write tests

**Key Principles:**

- Commands are **thin wrappers**
- Use **dependency injection** via container
- **Validate early**, execute, handle errors
- **Log events** for observability
- **Return proper exit codes**

**See Also:**

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [DEPENDENCY_INJECTION.md](DEPENDENCY_INJECTION.md) - DI container guide
- [EXTENDING_BACKENDS.md](EXTENDING_BACKENDS.md) - Backend patterns

---

**Document Version:** 1.0
**Maintainer:** NoDupeLabs Team
**License:** Apache-2.0
