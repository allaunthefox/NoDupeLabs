# ADR-001: Command Registry Pattern

**Status:** ✅ Accepted
**Date:** 2025-12-05
**Deciders:** Architecture Team
**Context:** Phase 1 of Modularity Improvement Plan

---

## Context

The CLI entry point originally hardcoded imports for all 13 command functions, creating tight coupling between the CLI dispatcher and individual command implementations. Adding, removing, or renaming commands required modifying the CLI code.

**Before:**
```python
# cli.py (BAD - tightly coupled)
from .commands.init import cmd_init
from .commands.scan import cmd_scan
from .commands.plan import cmd_plan
# ... 10 more imports
```

**Problems:**
- Adding a command required CLI modification
- Removed command imports left dead code
- No dynamic command discovery
- Difficult to extend via plugins
- Violation of Open/Closed Principle

---

## Decision

Implement a **Command Registry Pattern** where commands are registered in a central dictionary and looked up dynamically at runtime.

**Implementation:**

1. Create `commands/__init__.py` with `COMMANDS` registry:
```python
COMMANDS = {
    'scan': cmd_scan,
    'plan': cmd_plan,
    # ...
}
```

2. CLI uses registry for dispatch:
```python
command_func = COMMANDS.get(args.command)
if command_func:
    return command_func(args, cfg)
```

---

## Consequences

### Positive

- ✅ **Loose Coupling** - CLI doesn't depend on individual commands
- ✅ **Easy Extension** - Add commands by updating registry only
- ✅ **Plugin Ready** - External plugins can extend registry
- ✅ **Better Errors** - Can list available commands from registry
- ✅ **Testing** - Easy to mock registry for tests
- ✅ **Discovery** - Commands are self-documenting via registry

### Negative

- ⚠️ **Runtime Errors** - Typos in command names fail at runtime (not import time)
- ⚠️ **One Extra Import** - Commands must be imported in `__init__.py`

### Mitigations

- Use type hints on registry (`Dict[str, Callable]`)
- Add tests to verify all registry entries are callable
- Use consistent naming convention (`cmd_*` functions)

---

## Alternatives Considered

### 1. Plugin System with Auto-Discovery
**Approach:** Use decorators to auto-register commands
**Rejected:** Too complex for current needs, harder to debug

### 2. Subcommand Classes
**Approach:** Each command as a class with `execute()` method
**Rejected:** Overkill for simple function-based commands

### 3. Keep Current Hardcoded Imports
**Approach:** Accept tight coupling
**Rejected:** Violates modularity goals, doesn't scale

---

## Related

- **Pattern:** Registry Pattern, Strategy Pattern
- **References:**
  - [Martin Fowler - Plugin](https://martinfowler.com/articles/injection.html)
  - [POSA: Patterns of Software Architecture](https://en.wikipedia.org/wiki/Pattern-Oriented_Software_Architecture)
- **Related ADRs:**
  - ADR-002: Dependency Injection Container (builds on this)
  - ADR-003: Scan Subsystem Refactoring (uses DI from ADR-002)

---

## Implementation

- **PR:** #7 - Architecture documentation
- **Commits:** Multiple (part of modularity improvements)
- **Files Changed:**
  - `nodupe/commands/__init__.py` - Added `COMMANDS` registry
  - CLI entry point - Changed to use registry lookup
- **Impact:** Modularity score: 7/10 → 8/10

---

## Notes

This pattern is common in plugin architectures and CLI frameworks. It provides the foundation for future plugin system extensions where external packages can register commands dynamically.

The registry approach was chosen over more complex solutions because:
1. Simple to understand and maintain
2. Explicit (all commands visible in one place)
3. Flexible (easy to extend or modify)
4. Performant (dictionary lookup is O(1))

---

**Last Updated:** 2025-12-05
