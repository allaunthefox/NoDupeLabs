# Project Improvement Plan

This document outlines the roadmap for stabilizing and improving the NoDupeLabs codebase, building upon the architectural principles defined in `PROJECT_MAP.md`.

## Current Status Overview

- **Code Quality**: 10/10 Pylint (Excellent)
- **Test Status**: 45/45 Passing (Stable)
- **Test Coverage**: ~13% (Critically Low)
- **Architecture**: Modular structure in place, but isolation needs verification.

---

## 🚀 Phase 1: Immediate Stability (Next 2 Weeks)

The focus of this phase is to ensure that the verified code is actually robust and covered by tests, and to prevent regression.

### 1. Boost Core Test Coverage (Critical)

**Current:** 13% | **Target:** >60% for Core

- [ ] **Core Database**: Add tests for `FileRepository` CRUD operations (`nodupe/core/database/`).
- [ ] **File Scanner**: Add tests for `FileWalker` and `FileProcessor` with mocked file systems.
- [ ] **Error Handling**: Verify graceful degradation when plugins fail.

### 2. Enforce Type Safety

**Current:** Partial hints | **Target:** `mypy` strict passing

- [ ] Initialize `mypy` configuration.
- [ ] Run type check on `nodupe/core/` first.
- [ ] Fix typing errors in `nodupe/plugins/`.

### 3. CI/CD Pipeline Setup

**Current:** Manual | **Target:** Automated GitHub Actions

- [ ] Create `.github/workflows/test.yml`:
  - Run `pytest`.
  - Run `pylint` (fail if < 10.0).
  - Check coverage (warn if decreasing).

---

## 🏗️ Phase 2: Architectural Maturation (1-2 Months)

This phase focuses on enforcing the modular architecture and strictly isolating plugins.

### 1. Plugin Isolation Enforcement

- [ ] **Refactor Tests**: Move plugin tests to `tests/plugins/` and ensure they do *not* import from other plugins.
- [ ] **Dependency Checks**: Add a script to ensure `nodupe/core` never imports from `nodupe/plugins`.

### 2. Performance Benchmarking

- [ ] Integrate `pytest-benchmark`.
- [ ] Establish baselines for:
  - Scanning 10k files.
  - Vector search with 100k items.
  - Hashing throughput (MB/s).

### 3. Documentation

- [ ] Set up `MkDocs` or `Sphinx`.
- [ ] Generate API documentation from docstrings.
- [ ] Write a "Plugin Developer Guide".

---

## 🔮 Phase 3: Long-Term Goals (3+ Months)

### 1. Ecosystem Expansion

- [ ] **Plugin Marketplace**: Mechanism to install 3rd party plugins.
- [ ] **UI Layer**: Optional web interface (React/Next.js) interacting with the API.

### 2. Advanced Features

- [ ] **Distributed Scanning**: Networked scanning across multiple machines.
- [ ] **Cloud Sync**: S3/Google Drive integration.

---

## Success Metrics

| Metric | Current | Phase 1 Goal | Phase 2 Goal |
| :--- | :--- | :--- | :--- |
| **Pylint Score** | 10.00 | 10.00 | 10.00 |
| **Test Coverage** | 13% | >60% | >80% |
| **Bugs/Month** | N/A | < 5 | < 2 |
| **Setup Time** | ~5 min | < 2 min | < 1 min |
