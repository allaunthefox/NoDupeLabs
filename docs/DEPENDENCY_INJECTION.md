# Dependency Injection Guide

**Version:** 1.0
**Last Updated:** 2025-12-05

---

## Table of Contents

1. [Introduction](#introduction)
2. [The ServiceContainer](#the-servicecontainer)
3. [Using the Container](#using-the-container)
4. [Adding New Services](#adding-new-services)
5. [Testing with DI](#testing-with-di)
6. [Best Practices](#best-practices)
7. [Common Patterns](#common-patterns)
8. [Troubleshooting](#troubleshooting)

---

## Introduction

NoDupeLabs uses **Dependency Injection (DI)** to achieve loose coupling and testability. Instead of creating dependencies directly, components receive them through constructor parameters.

### Why Dependency Injection?

#### Without DI (Tightly Coupled)

```python
# ❌ BAD: Hard to test, hard to change
def cmd_scan(args):
    db = DB('nodupe.db')              # Hardcoded
    logger = JsonlLogger('logs/')      # Hardcoded
    backend = ONNXBackend()            # Hardcoded

    # If ONNXBackend is unavailable, this crashes
    # Can't test with mock database
    # Can't swap implementations
```

#### With DI (Loosely Coupled)

```python
# ✅ GOOD: Easy to test, easy to change
def cmd_scan(args, cfg):
    container = get_container()
    orchestrator = container.get_scanner()  # All deps injected!

    # Container handles:
    # - Backend fallback (ONNX → CPU)
    # - Database creation
    # - Logger configuration
    # - Service lifecycle
```

### Benefits

1. **Testability** - Inject mocks/fakes for unit tests
2. **Flexibility** - Swap implementations without changing code
3. **Loose Coupling** - Modules don't know about concrete implementations
4. **Single Responsibility** - Services don't create their own dependencies
5. **Configuration** - Centralized service configuration

---

## The ServiceContainer

### Location

```python
from nodupe.container import ServiceContainer, get_container
```

### Overview

The `ServiceContainer` is a **service locator** that:

- Creates services lazily (on first access)
- Caches instances (singleton pattern)
- Manages service lifecycles
- Allows overrides for testing

### Basic Structure

```python
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

@dataclass
class ServiceContainer:
    """Centralized container for service dependencies."""

    config_path: str = "nodupe.yml"
    _config: Optional[Dict[str, Any]] = field(default=None, repr=False)
    _services: Dict[str, Any] = field(default_factory=dict, repr=False)
    _overrides: Dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def config(self) -> Dict[str, Any]:
        """Lazy-load configuration."""
        if self._config is None:
            self._config = load_config(self.config_path)
        return self._config

    def get_db(self) -> DB:
        """Get database facade."""
        if 'db' in self._overrides:
            return self._overrides['db']

        if 'db' not in self._services:
            db_path = self.config.get('db_path', 'nodupe.db')
            self._services['db'] = DB(db_path)

        return self._services['db']

    # ... other service getters
```

---

## Using the Container

### In Commands

Commands should use the container to get orchestrators or services:

```python
# nodupe/commands/scan.py
from ..container import get_container

def cmd_scan(args, cfg: Dict) -> int:
    """Execute scan command."""

    # Get container (singleton)
    container = get_container()

    # Get fully-configured orchestrator
    orchestrator = container.get_scanner()

    # Execute workflow
    results = orchestrator.scan(
        roots=args.root,
        hash_algo=cfg.get("hash_algo", "sha512"),
        workers=cfg.get("parallelism", 4),
        # ...
    )

    return 0
```

### Getting Services

```python
from nodupe.container import get_container

# Get singleton container
container = get_container()

# Get services
db = container.get_db()
telemetry = container.get_telemetry()
backend = container.get_backend()
pm = container.get_plugin_manager()
classifier = container.get_classifier()

# Get orchestrators (with all deps injected)
scanner = container.get_scanner()
```

### Accessing Configuration

```python
container = get_container()

# Configuration is lazy-loaded
config = container.config

# Access configuration values
db_path = config.get('db_path', 'nodupe.db')
workers = config.get('parallelism', 4)
hash_algo = config.get('hash_algo', 'sha512')
```

---

## Adding New Services

### Step 1: Add Getter Method

Add a new `get_*()` method to the `ServiceContainer` class:

```python
# nodupe/container.py

def get_deduplicator(self) -> Deduplicator:
    """Get deduplicator service.

    Returns:
        Deduplicator instance
    """
    # Check for test override
    if 'deduplicator' in self._overrides:
        return self._overrides['deduplicator']

    # Check cache
    if 'deduplicator' not in self._services:
        # Create service with dependencies
        db = self.get_db()
        telemetry = self.get_telemetry()

        # Configuration
        threshold = self.config.get('dedup_threshold', 0.95)

        # Create and cache
        self._services['deduplicator'] = Deduplicator(
            db=db,
            telemetry=telemetry,
            threshold=threshold
        )

    return self._services['deduplicator']
```

### Step 2: Update Service Class

Ensure the service accepts dependencies via constructor:

```python
# nodupe/deduplicator.py

class Deduplicator:
    """Service for finding and removing duplicates."""

    def __init__(self, db: DB, telemetry: Telemetry, threshold: float):
        """Initialize deduplicator.

        Args:
            db: Database facade (injected)
            telemetry: Logging + metrics (injected)
            threshold: Similarity threshold (configured)
        """
        self.db = db
        self.telemetry = telemetry
        self.threshold = threshold

    def find_duplicates(self, ...):
        """Find duplicate files."""
        # Use injected services
        files = self.db.get_all()
        self.telemetry.log('dedup:start', {'file_count': len(files)})
        # ...
```

### Step 3: Use in Commands

```python
# nodupe/commands/dedup.py

def cmd_dedup(args, cfg):
    container = get_container()
    deduplicator = container.get_deduplicator()  # New service!
    return deduplicator.find_duplicates()
```

---

## Testing with DI

### Unit Testing with Mocks

Dependency injection makes unit testing trivial:

```python
# tests/test_deduplicator.py
from unittest.mock import Mock
import pytest
from nodupe.deduplicator import Deduplicator
from nodupe.db import DB
from nodupe.telemetry import Telemetry

def test_deduplicator_find_duplicates():
    # Create mocks
    mock_db = Mock(spec=DB)
    mock_telemetry = Mock(spec=Telemetry)

    # Configure mock behavior
    mock_db.get_all.return_value = [
        {'path': '/a.txt', 'hash': 'abc123'},
        {'path': '/b.txt', 'hash': 'abc123'},  # Duplicate!
        {'path': '/c.txt', 'hash': 'def456'},
    ]

    # Inject mocks
    deduplicator = Deduplicator(
        db=mock_db,
        telemetry=mock_telemetry,
        threshold=0.95
    )

    # Test in isolation
    duplicates = deduplicator.find_duplicates()

    # Verify behavior
    assert len(duplicates) == 1
    assert duplicates[0] == ['/a.txt', '/b.txt']

    # Verify interactions
    mock_db.get_all.assert_called_once()
    mock_telemetry.log.assert_called()
```

### Integration Testing with Container Overrides

For integration tests, override services in the container:

```python
# tests/test_scan_integration.py
from pathlib import Path
import pytest
from nodupe.container import get_container
from nodupe.db import DB
from nodupe.commands import cmd_scan

def test_scan_integration(tmp_path):
    # Create test database
    test_db_path = tmp_path / "test.db"
    test_db = DB(test_db_path)

    # Get container and override db
    container = get_container()
    container.override('db', test_db)

    # Create test files
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    # Run scan command (uses injected test db)
    args = Mock(root=[str(tmp_path)], progress='none')
    cfg = {'hash_algo': 'sha256', 'parallelism': 1}

    result = cmd_scan(args, cfg)

    # Verify results
    assert result == 0
    assert test_db.count_files() == 1

    # Cleanup: clear overrides for next test
    container.clear_overrides()
```

### Fixture Setup

Create reusable test fixtures:

```python
# tests/conftest.py
import pytest
from nodupe.container import get_container
from nodupe.db import DB

@pytest.fixture
def container(tmp_path):
    """Provide a container with test overrides."""
    container = get_container()

    # Override services with test versions
    test_db = DB(tmp_path / "test.db")
    container.override('db', test_db)

    yield container

    # Cleanup after test
    container.clear_overrides()

# Use in tests
def test_with_container(container):
    db = container.get_db()  # Gets test db
    # ...
```

---

## Best Practices

### 1. Always Use Constructor Injection

```python
# ✅ GOOD: Dependencies injected via constructor
class ScanOrchestrator:
    def __init__(self, db: DB, telemetry: Telemetry, backend: BaseBackend):
        self.db = db
        self.telemetry = telemetry
        self.backend = backend

# ❌ BAD: Dependencies created internally
class ScanOrchestrator:
    def __init__(self):
        self.db = DB('nodupe.db')  # Hard to test!
        self.telemetry = Telemetry()  # Hard to change!
```

### 2. Don't Pass Container to Services

```python
# ❌ BAD: Service depends on container (service locator anti-pattern)
class ScanOrchestrator:
    def __init__(self, container: ServiceContainer):
        self.container = container

    def scan(self):
        db = self.container.get_db()  # Hidden dependency!

# ✅ GOOD: Explicit dependencies
class ScanOrchestrator:
    def __init__(self, db: DB, telemetry: Telemetry):
        self.db = db  # Clear what's needed
        self.telemetry = telemetry
```

### 3. Keep Container in Commands Only

```python
# ✅ GOOD: Container used only in command layer
def cmd_scan(args, cfg):
    container = get_container()  # OK in commands
    orchestrator = container.get_scanner()
    return orchestrator.scan(...)

# ❌ BAD: Container used deep in business logic
class FileProcessor:
    def process(self, path):
        container = get_container()  # Don't do this!
        db = container.get_db()
```

### 4. Use Type Hints

```python
# ✅ GOOD: Type hints make dependencies explicit
def __init__(self, db: DB, telemetry: Telemetry, backend: BaseBackend):
    self.db = db
    self.telemetry = telemetry
    self.backend = backend

# ❌ BAD: No type hints (unclear dependencies)
def __init__(self, db, telemetry, backend):
    pass
```

### 5. Document Service Lifecycle

```python
def get_plugin_manager(self) -> PluginManager:
    """Get plugin manager.

    Note: Plugin manager starts an async event loop.
    Call `pm.shutdown()` when done to cleanup properly.

    Returns:
        PluginManager instance (singleton)
    """
    # ...
```

---

## Common Patterns

### Pattern 1: Lazy Service Creation

Services are created only when first accessed:

```python
def get_db(self) -> DB:
    if 'db' not in self._services:
        # Created on first access
        self._services['db'] = DB(self.config.get('db_path'))
    return self._services['db']
```

### Pattern 2: Singleton Services

Each service is created once and cached:

```python
# First call - creates DB
db1 = container.get_db()

# Second call - returns same instance
db2 = container.get_db()

assert db1 is db2  # Same object
```

### Pattern 3: Service Dependencies

Services can depend on other services:

```python
def get_scanner(self) -> ScanOrchestrator:
    # Get dependencies
    db = self.get_db()              # May create DB
    telemetry = self.get_telemetry()  # May create Telemetry
    backend = self.get_backend()      # May create Backend
    pm = self.get_plugin_manager()    # May create PM

    # Create orchestrator with all deps
    return ScanOrchestrator(db, telemetry, backend, pm)
```

### Pattern 4: Configuration-Based Creation

Services use config values from container:

```python
def get_db(self) -> DB:
    # Get config value with default
    db_path = self.config.get('db_path', 'nodupe.db')
    timeout = self.config.get('db_timeout', 30)

    return DB(db_path, timeout=timeout)
```

### Pattern 5: Fallback Logic

Container can handle optional dependencies:

```python
def get_backend(self) -> Optional[BaseBackend]:
    """Get AI backend with fallback logic."""
    if 'backend' not in self._services:
        try:
            # Try ONNX (fast but requires onnxruntime)
            self._services['backend'] = ONNXBackend()
        except ImportError:
            try:
                # Fall back to CPU (slower but no deps)
                self._services['backend'] = CPUBackend()
            except Exception:
                # AI disabled
                self._services['backend'] = None

    return self._services['backend']
```

---

## Troubleshooting

### Problem: "Service not found in container"

**Symptom:**

```python
AttributeError: 'ServiceContainer' object has no attribute 'get_my_service'
```

**Solution:** Add the getter method to `ServiceContainer`:

```python
def get_my_service(self) -> MyService:
    if 'my_service' not in self._services:
        self._services['my_service'] = MyService(...)
    return self._services['my_service']
```

### Problem: "Circular dependency"

**Symptom:**

```python
RecursionError: maximum recursion depth exceeded
```

**Cause:** Service A depends on Service B, which depends on Service A.

**Solution:** Refactor to break the cycle:

- Extract shared functionality to a third service
- Use events/callbacks instead of direct dependencies
- Restructure modules to follow layered architecture

### Problem: "Service created multiple times"

**Symptom:** Different instances returned on each call.

**Cause:** Not caching in `_services` dict.

**Solution:**

```python
# ❌ BAD: Creates new instance each time
def get_db(self) -> DB:
    return DB(self.config.get('db_path'))

# ✅ GOOD: Cache instance
def get_db(self) -> DB:
    if 'db' not in self._services:
        self._services['db'] = DB(self.config.get('db_path'))
    return self._services['db']
```

### Problem: "Can't test because using real database"

**Symptom:** Tests fail or are slow due to real DB access.

**Solution:** Use `container.override()` in tests:

```python
def test_my_feature():
    container = get_container()
    mock_db = Mock(spec=DB)
    container.override('db', mock_db)

    # Now get_db() returns mock
    # ...

    container.clear_overrides()  # Cleanup
```

### Problem: "Config changes not reflected"

**Symptom:** Changing config doesn't affect services.

**Cause:** Config loaded once and cached.

**Solution:** Reload config or restart container:

```python
# Option 1: Force reload
container._config = None
config = container.config  # Reloads

# Option 2: Create new container
container = ServiceContainer(config_path="new_config.yml")
```

---

## Advanced Topics

### Custom Container Subclass

For complex apps, subclass `ServiceContainer`:

```python
class MyAppContainer(ServiceContainer):
    def get_custom_service(self) -> CustomService:
        # Add app-specific services
        pass

# Use custom container
container = MyAppContainer(config_path="app.yml")
```

### Context Managers

Services can be context managers:

```python
def get_db(self) -> DB:
    if 'db' not in self._services:
        db = DB(self.config.get('db_path'))
        self._services['db'] = db
    return self._services['db']

# Usage
with container.get_db() as db:
    db.upsert_files([...])
# Automatically closed
```

### Async Services

Container can manage async services:

```python
async def get_async_service(self) -> AsyncService:
    if 'async_service' not in self._services:
        service = AsyncService()
        await service.initialize()
        self._services['async_service'] = service
    return self._services['async_service']
```

---

## Summary

**Key Takeaways:**

1. ✅ Use `get_container()` to access the singleton container
2. ✅ Commands get orchestrators from container
3. ✅ Orchestrators receive dependencies via constructor
4. ✅ Services are created lazily and cached
5. ✅ Use `override()` for testing with mocks
6. ✅ Type hint all dependencies
7. ✅ Keep container usage in command layer only
8. ✅ Don't pass container to services

**Benefits of DI in NoDupeLabs:**

- 🎯 **Testable** - Easy to inject mocks
- 🎯 **Flexible** - Swap implementations
- 🎯 **Loose Coupling** - Services don't create deps
- 🎯 **Configuration** - Centralized setup
- 🎯 **Maintainable** - Clear dependency graph

**Next Steps:**

- See [ARCHITECTURE.md](ARCHITECTURE.md) for overall system design
- See [ADDING_COMMANDS.md](ADDING_COMMANDS.md) for using DI in commands
- See [EXTENDING_BACKENDS.md](EXTENDING_BACKENDS.md) for backend patterns

---

**Document Version:** 1.0
**Maintainer:** NoDupeLabs Team
**License:** Apache-2.0
