# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records documenting significant architectural decisions made in the NoDupeLabs project.

## What is an ADR?

An Architecture Decision Record (ADR) captures an important architectural decision made along with its context and consequences. ADRs help team members and contributors understand:

- **Why** decisions were made
- **What** alternatives were considered
- **What** the tradeoffs are
- **When** the decision was made
- **Who** was involved

## Format

Each ADR follows this structure:

1. **Title** - Short descriptive name
2. **Status** - Proposed, Accepted, Deprecated, Superseded
3. **Context** - The forces at play (technical, political, social)
4. **Decision** - The architectural decision made
5. **Consequences** - Positive and negative outcomes
6. **Alternatives** - Other options considered

## ADR Index

### ADR-001: Command Registry Pattern
**Date:** 2025-12-05
**Status:** ✅ Accepted

Implements a command registry pattern to decouple CLI from command implementations, enabling dynamic command discovery and easier extension.

**Key Decision:** Use dictionary-based registry instead of hardcoded imports

**Impact:** Modularity 7/10 → 8/10

[Read more →](ADR-001-command-registry-pattern.md)

---

### ADR-002: Dependency Injection Container
**Date:** 2025-12-05
**Status:** ✅ Accepted

Introduces a ServiceContainer for dependency injection to achieve loose coupling, testability, and centralized service lifecycle management.

**Key Decision:** Use DI container pattern with constructor injection for services

**Impact:** Modularity 8/10 → 9/10

[Read more →](ADR-002-dependency-injection-container.md)

---

### ADR-003: Scan Subsystem Refactoring
**Date:** 2025-12-05
**Status:** ✅ Accepted

Refactors monolithic scanner.py (1000+ lines) into modular scan/ subsystem with clear separation of concerns using the Orchestrator pattern.

**Key Decision:** Split into specialized modules (walker, hasher, processor, etc.)

**Impact:** Modularity 9/10 → 9/10 (maintained excellent structure)

[Read more →](ADR-003-scan-subsystem-refactoring.md)

---

## Timeline

```
2025-12-05: ADR-001, ADR-002, ADR-003 (Modularity improvements)
```

## Creating New ADRs

When making significant architectural decisions:

1. Copy the template from an existing ADR
2. Number it sequentially (ADR-004, ADR-005, etc.)
3. Fill in all sections thoroughly
4. Update this README with the new entry
5. Link to related ADRs

## Resources

- [Architecture Decision Records - Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub Organization](https://adr.github.io/)
- [Markdown ADR Tools](https://github.com/npryce/adr-tools)

---

**Last Updated:** 2025-12-05
