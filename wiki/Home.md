# NoDupeLabs

A plugin-based deduplication system for finding and managing duplicate files.

## Quick Status

| Metric | Value |
|--------|-------|
| Tests | 1023 |
| Coverage | 16.5% |
| Docstring Coverage | 100% |
| Modules | 78 |
| Classes | 222 |
| Functions | 1182 |

## Features

- **Minimal-Core Architecture**: Aspect-oriented design with swappable plugin aspects
- **Plugin IPC Socket**: Programmatic access to all plugin features via JSON-RPC
- **ISO Standard Registry**: ISO-8000 compliant action codes for all system events
- **Automated Maintenance**: Built-in ZIP compression for historical log files
- **Similarity Detection**: Content-based duplicate finding

## Getting Started

- [Installation & Setup](Getting-Started.md)
- [Configuration](Operations/Configuration.md)

## Development

- [Development Setup](Development/Setup.md)
- [Plugin Development](Development/Plugins.md)
- [Contributing](Development/Contributing.md)

## Reference

- [Architecture](Architecture/Overview.md)
  - [Aspect-Oriented Design](Architecture/Aspect-Oriented-Design.md)
- [API Reference](API/CLI.md)
  - [Socket IPC Interface](API/Socket-IPC.md)
- [Testing Guide](Testing/Guide.md)

## Operations

- [Security](Operations/Security.md)
- [Action Codes (ISO-8000)](Operations/Action-Codes.md)
- [Logging Policy & Maintenance](Operations/Logging-Policy.md)
- [Configuration](Operations/Configuration.md)

## Project

- [Changelog](Changelog.md)
