# NoDupeLabs Feature Roadmap

## Overview

This document provides a comprehensive roadmap showing which legacy features are missing from the modern system, which are planned in the refactoring TODO, and which need to be added to achieve feature parity.

## Feature Status Matrix

### Core Functionality

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **File Scanning** | ✅ | ✅ | ✅ | Complete |
| **Metadata Extraction** | ✅ | ✅ | ✅ | Complete |
| **Content Hashing** | ✅ | ✅ | ✅ | Complete |
| **MIME Detection** | ✅ | ✅ | ✅ | Complete |
| **Incremental Scanning** | ✅ | ❌ | ✅ (Phase 2) | High |
| **Progress Tracking** | ✅ | ✅ | ✅ | Complete |

### Duplicate Detection & Management

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Planner Module** | ✅ | ❌ | ❌ | Critical |
| **Duplicate Detection** | ✅ | ❌ | ❌ | Critical |
| **Action Planning** | ✅ | ❌ | ❌ | Critical |
| **CSV Generation** | ✅ | ❌ | ❌ | Critical |
| **Apply Operations** | ✅ | ✅ | ✅ | Complete |
| **Dry Run Mode** | ✅ | ✅ | ✅ | Complete |

### Safety & Recovery

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Rollback System** | ✅ | ❌ | ✅ (Phase 9) | Critical |
| **Verify Command** | ✅ | ❌ | ❌ | Critical |
| **Checkpoint Validation** | ✅ | ❌ | ❌ | Critical |
| **Transaction Management** | ✅ | ❌ | ✅ (Phase 2) | High |
| **Error Recovery** | ✅ | ✅ | ✅ | Complete |

### Archive Support

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Archive Inspection** | ✅ | ❌ | ❌ | Medium |
| **Archive Extraction** | ✅ | ❌ | ❌ | Medium |
| **Multi-format Support** | ✅ | ❌ | ❌ | Medium |
| **Archive Management** | ✅ | ❌ | ❌ | Medium |

### Virtual Filesystem

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **FUSE Mounting** | ✅ | ❌ | ❌ | Low |
| **Database Browsing** | ✅ | ❌ | ❌ | Low |
| **Read-only Access** | ✅ | ❌ | ❌ | Low |

### Telemetry & Monitoring

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Performance Metrics** | ✅ | ❌ | ✅ (Phase 10) | Medium |
| **Usage Tracking** | ✅ | ❌ | ✅ (Phase 10) | Medium |
| **Error Tracking** | ✅ | ❌ | ✅ (Phase 10) | Medium |
| **Health Checks** | ✅ | ❌ | ✅ (Phase 10) | Medium |
| **Alerting** | ✅ | ❌ | ✅ (Phase 10) | Medium |

### Command System

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **init** | ✅ | ✅ | ✅ | Complete |
| **scan** | ✅ | ✅ | ✅ | Complete |
| **plan** | ✅ | ❌ | ❌ | Critical |
| **apply** | ✅ | ✅ | ✅ | Complete |
| **verify** | ✅ | ❌ | ❌ | Critical |
| **rollback** | ✅ | ❌ | ✅ (Phase 9) | Critical |
| **similarity** | ✅ | ✅ | ✅ | Complete |
| **archive** | ✅ | ❌ | ❌ | Medium |
| **mount** | ✅ | ❌ | ❌ | Low |

### Plugin System

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Basic Plugins** | ✅ | ✅ | ✅ | Complete |
| **NSFW Logger** | ✅ | ❌ | ❌ | Medium |
| **Scan Reporter** | ✅ | ❌ | ❌ | Medium |
| **Startup Logger** | ✅ | ❌ | ❌ | Medium |
| **Plugin Isolation** | ❌ | ✅ | ✅ (Phase 3) | Complete |
| **Plugin Metrics** | ❌ | ❌ | ✅ (Phase 10) | Medium |

### Configuration & Environment

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **YAML Config** | ✅ | ❌ | ✅ | Complete (TOML) |
| **Environment Auto-tuning** | ✅ | ❌ | ❌ | Medium |
| **Preset Configurations** | ✅ | ❌ | ❌ | Medium |
| **TOML Config** | ❌ | ✅ | ✅ | Complete |

### Documentation

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Manual Docs** | ✅ | ❌ | ✅ | Complete |
| **API Documentation** | ❌ | ❌ | ✅ (Phase 2) | Medium |
| **Plugin Guide** | ❌ | ❌ | ✅ (Phase 8) | Medium |
| **Migration Guide** | ❌ | ❌ | ✅ (Phase 8) | Medium |
| **Automated Docs** | ❌ | ✅ | ✅ | Complete |

### Testing & Quality

| Feature | Legacy | Modern | Planned | Priority |
|---------|--------|--------|---------|----------|
| **Unit Tests** | ✅ | ✅ | ✅ (Phase 7) | Complete |
| **Integration Tests** | ✅ | ❌ | ✅ (Phase 7) | High |
| **E2E Tests** | ✅ | ❌ | ✅ (Phase 7) | High |
| **Type Checking** | ✅ | ✅ | ✅ (Phase 1) | Complete |
| **Linting** | ✅ | ✅ | ✅ | Complete |
| **CI/CD Pipeline** | ✅ | ❌ | ✅ (Phase 1) | High |

## Planned Features from Refactoring TODO

### Phase 2: Core Isolation (Current Focus)
- [ ] Add transaction management
- [ ] Implement basic indexing
- [ ] Create filesystem utilities
- [ ] Implement compression with fallback
- [ ] Add MIME type detection
- [ ] Create error handling utilities
- [ ] Implement logging system

### Phase 3: Plugin System Implementation
- [ ] Design plugin interface and contracts
- [ ] Implement plugin discovery mechanism
- [ ] Create plugin loading system
- [ ] Add event emission framework
- [ ] Implement plugin lifecycle management
- [ ] Add plugin configuration support
- [ ] Implement plugin error handling
- [ ] Add plugin metrics and monitoring
- [ ] Create plugin documentation

### Phase 6: Command System Refactoring
- [ ] Redesign command interface
- [ ] Implement command discovery
- [ ] Add command validation
- [ ] Create command error handling
- [ ] Implement command help system
- [ ] Add command metrics
- [ ] Implement command testing

### Phase 9: Clean Implementation
- [ ] Implement new CLI interface optimized for efficiency
- [ ] Design clean database schema for performance
- [ ] Create streamlined configuration format
- [ ] Focus on resilience and quality
- [ ] Create rollback procedure

### Phase 10: Monitoring and Maintenance
- [ ] Implement plugin monitoring
- [ ] Add error tracking
- [ ] Create performance metrics
- [ ] Add health checks
- [ ] Implement alerting

## Missing Features Not in Current Plan

### Critical Missing Features (Not Planned)
1. **Planner Module** - No plan to restore duplicate detection
2. **Verify Command** - No plan for integrity checking
3. **Archive Support** - No plan for archive handling
4. **Environment Auto-tuning** - No plan for preset configurations

### Secondary Missing Features (Not Planned)
1. **Virtual Filesystem** - No plan for FUSE mounting
2. **Logging Plugins** - No plan to restore legacy loggers
3. **Bootstrap System** - No plan for automated initialization
4. **Runtime Management** - No plan for environment adaptation

## Feature Roadmap Recommendations

### Immediate Priorities (Next 2-4 Weeks)
1. **Complete Phase 2**: Core isolation features
2. **Implement Transaction Management**: Critical for data integrity
3. **Add Incremental Scanning**: Performance improvement
4. **Create Filesystem Utilities**: Foundation for other features

### Short-Term Priorities (1-2 Months)
1. **Complete Phase 3**: Plugin system implementation
2. **Implement Command System**: Restore missing commands
3. **Add Integration Testing**: Ensure system reliability
4. **Setup CI/CD Pipeline**: Automate quality checks

### Medium-Term Priorities (2-3 Months)
1. **Implement Planner Module**: Restore duplicate detection
2. **Add Verify Command**: Implement integrity checking
3. **Create Rollback System**: Enhance safety features
4. **Add Archive Support**: Restore archive handling

### Long-Term Priorities (3+ Months)
1. **Implement Telemetry**: Add performance monitoring
2. **Create Plugin Marketplace**: Ecosystem expansion
3. **Add UI Layer**: Web interface for better UX
4. **Implement Distributed Scanning**: Scalability improvement

## Feature Parity Roadmap

### Critical Path to Feature Parity
1. **Complete Core Isolation** (Phase 2) - Foundation
2. **Implement Plugin System** (Phase 3) - Architecture
3. **Refactor Command System** (Phase 6) - Functionality
4. **Add Missing Commands** (Custom) - plan, verify, archive
5. **Implement Safety Features** (Phase 9) - rollback, verification
6. **Restore Archive Support** (Custom) - archive handling

### Estimated Timeline
- **Core Completion**: 2-3 months (Phases 2-3)
- **Feature Parity**: 4-6 months (Additional development)
- **Full Maturity**: 6-9 months (All planned features)

## Conclusion

The modern NoDupeLabs system has a solid architectural foundation but is missing several critical features from the legacy system. While the refactoring plan addresses some gaps (transaction management, plugin isolation, monitoring), many legacy features are not currently planned for restoration.

To achieve feature parity, additional development work is needed to implement the planner module, verify/rollback systems, archive support, and other missing components. The recommended roadmap provides a clear path to restore these features while maintaining the benefits of the modern architecture.
