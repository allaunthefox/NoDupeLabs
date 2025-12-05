# ADR-002: Dependency Injection Container

**Status:** ✅ Accepted
**Date:** 2025-12-05
**Deciders:** Architecture Team
**Context:** Phase 3 of Modularity Improvement Plan

---

## Context

Commands originally created their own dependencies directly, leading to:
- Tight coupling between commands and services
- Difficult testing (can't inject mocks)
- Scattered configuration (duplicated across commands)
- No centralized service lifecycle management

**Before:**
```python
def cmd_scan(args):
    db = DB('nodupe.db')              # Hardcoded
    logger = JsonlLogger('logs/')      # Hardcoded
    backend = ONNXBackend()            # Hardcoded, crashes if unavailable
    # Business logic...
```

**Problems:**
- Hard to test (can't inject mocks)
- Configuration scattered across files
- Service initialization duplicated
- No graceful degradation (e.g., ONNX fallback)
- Difficult to swap implementations

---

## Decision

Implement a **Service Container** using the **Dependency Injection** pattern to manage service creation and lifecycle.

**Implementation:**

1. Create `ServiceContainer` class in `container.py`:
```python
@dataclass
class ServiceContainer:
    config_path: str = "nodupe.yml"
    _services: Dict[str, Any] = field(default_factory=dict)
    _overrides: Dict[str, Any] = field(default_factory=dict)

    def get_db(self) -> DB:
        # Lazy creation, caching, graceful fallback
        pass

    def get_scanner(self) -> ScanOrchestrator:
        # Create orchestrator with all dependencies injected
        return ScanOrchestrator(
            db=self.get_db(),
            telemetry=self.get_telemetry(),
            backend=self.get_backend(),
            plugin_manager=self.get_plugin_manager()
        )
```

2. Commands use container:
```python
def cmd_scan(args, cfg):
    container = get_container()
    orchestrator = container.get_scanner()  # All deps injected!
    return orchestrator.scan(...)
```

3. Services receive dependencies via constructor:
```python
class ScanOrchestrator:
    def __init__(self, db: DB, telemetry: Telemetry,
                 backend: BaseBackend, plugin_manager: PluginManager):
        self.db = db              # Injected
        self.telemetry = telemetry # Injected
        # ...
```

---

## Consequences

### Positive

- ✅ **Testability** - Easy to inject mocks for unit tests
- ✅ **Flexibility** - Swap implementations without changing code
- ✅ **Loose Coupling** - Services don't create their dependencies
- ✅ **Single Responsibility** - Services focus on their job
- ✅ **Centralized Config** - One place for service configuration
- ✅ **Lifecycle Management** - Container handles creation/caching
- ✅ **Graceful Degradation** - Backend fallback logic centralized

### Negative

- ⚠️ **Learning Curve** - Developers must understand DI pattern
- ⚠️ **Indirection** - One more layer between command and service
- ⚠️ **Container Complexity** - Container grows as services increase

### Mitigations

- Comprehensive documentation (DEPENDENCY_INJECTION.md)
- Type hints on all container methods
- Clear examples in command development guide
- Keep container methods simple and focused

---

## Alternatives Considered

### 1. Service Locator Pattern
**Approach:** Global registry of services
**Rejected:** Hidden dependencies, harder to test, anti-pattern

### 2. Manual Dependency Passing
**Approach:** Pass all dependencies through function args
**Rejected:** Leads to long parameter lists, hard to maintain

### 3. Singleton Services
**Approach:** Each service is a global singleton
**Rejected:** Hard to test, global state issues

### 4. Factory Functions
**Approach:** Factory function for each service type
**Rejected:** Doesn't solve lifecycle management or configuration

---

## Design Choices

### Container as Service Locator

We chose a hybrid approach:
- **Commands** use container (service locator pattern)
- **Services** receive dependencies via constructor (pure DI)

This balances:
- Commands are thin wrappers (service locator is acceptable)
- Services are testable (pure DI, no container dependency)

### Lazy Initialization

Services are created on first access and cached:
```python
def get_db(self):
    if 'db' not in self._services:
        self._services['db'] = DB(...)  # Create once
    return self._services['db']         # Return cached
```

**Benefits:**
- Faster startup (don't create unused services)
- Lower memory (only loaded services in RAM)
- Configuration can be late-bound

### Override Support

Container supports overriding services for testing:
```python
container.override('db', mock_db)
db = container.get_db()  # Returns mock_db
```

**Benefits:**
- Easy integration testing
- Can test with fake implementations
- Supports test fixtures

---

## Related

- **Pattern:** Dependency Injection, Service Container, Inversion of Control
- **References:**
  - [Martin Fowler - Inversion of Control](https://martinfowler.com/bliki/InversionOfControl.html)
  - [Dependency Injection Principles](https://stackoverflow.com/questions/130794/what-is-dependency-injection)
- **Related ADRs:**
  - ADR-001: Command Registry Pattern (builds on this)
  - ADR-003: Scan Subsystem Refactoring (enabled by this)

---

## Implementation

- **PR:** #7 - Architecture documentation
- **Files Created:**
  - `nodupe/container.py` - ServiceContainer implementation
  - `docs/DEPENDENCY_INJECTION.md` - Usage guide
- **Files Modified:**
  - All command files - Use container instead of direct instantiation
  - `nodupe/scan/orchestrator.py` - Receives dependencies via constructor
- **Impact:** Modularity score: 8/10 → 9/10

---

## Migration Guide

### Before (Tightly Coupled)
```python
def cmd_scan(args):
    db = DB('nodupe.db')
    logger = JsonlLogger('logs/')
    # Business logic mixing creation and usage
```

### After (Dependency Injection)
```python
def cmd_scan(args, cfg):
    container = get_container()
    orchestrator = container.get_scanner()
    return orchestrator.scan(...)  # Clean separation
```

### Testing Before
```python
# Hard to test - DB created internally
def test_scan():
    result = cmd_scan(args)  # Uses real DB!
```

### Testing After
```python
# Easy to test - inject mock
def test_scan():
    container = get_container()
    container.override('db', mock_db)
    result = cmd_scan(args, cfg)  # Uses mock!
```

---

## Notes

Dependency Injection is a fundamental pattern for achieving loose coupling and testability. While it adds a layer of indirection, the benefits far outweigh the complexity.

The container approach was chosen because:
1. **Centralized** - One place for all service creation logic
2. **Flexible** - Easy to add new services
3. **Testable** - Override support makes testing trivial
4. **Standard** - Common pattern in modern frameworks

Future enhancements could include:
- Scope management (request-scoped services)
- Async service initialization
- Service health checks
- Dependency graph visualization

---

**Last Updated:** 2025-12-05
