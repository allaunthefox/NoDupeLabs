# NoDupeLabs ContextStream Rules

## Project Overview
NoDupeLabs is a sophisticated file deduplication and similarity detection system built with Python. The system uses a plugin architecture for extensibility and includes advanced features like parallel processing, GPU acceleration, and ML-based similarity detection.

## Language & Runtime
- **Language**: Python 3.13+ (minimum 3.10)
- **Package Manager**: pip with setuptools
- **Testing Framework**: pytest
- **Type Checking**: Use Python type hints throughout the codebase

## Architecture Principles

### Plugin System
- All new features should be implemented as plugins when possible
- Plugins must extend the `PluginBase` class from `nodupe.core.plugin_system.base`
- Follow the plugin lifecycle: initialization → setup → activation → deactivation → cleanup
- Use the plugin registry for discovery and management
- Support hot-reload capabilities for development
- See `nodupe/core/plugin_system/PLUGIN_DEVELOPMENT_GUIDE.md` for detailed guidelines

### Code Organization
- Core functionality in `nodupe/core/`
- Plugin implementations in `nodupe/plugins/`
- Tests mirror the source structure in `tests/`
- Database operations in `nodupe/core/database/`
- Scanning operations in `nodupe/core/scan/`

### Database Management
- Use SQLite for local storage
- All database operations must use transactions
- Follow the repository pattern via `repository_interface.py`
- Schema changes must include migrations
- Use connection pooling and proper resource cleanup

### Security & Validation
- Validate all user input
- Use the security module for path traversal protection
- Implement proper error handling with custom exceptions
- Never expose internal paths or sensitive data in error messages
- Follow principle of least privilege

## Testing Requirements
- Write tests for all new features
- Unit tests for individual components
- Integration tests for multi-component workflows
- Use pytest fixtures from `tests/conftest.py`
- Maintain test coverage above 80%
- Performance tests for critical paths

## Code Style & Standards
- Follow PEP 8 style guidelines
- Use descriptive variable and function names
- Add docstrings for all public methods and classes
- Include type hints for function parameters and return values
- Keep functions focused and single-purpose
- Prefer composition over inheritance

## Performance Considerations
- Use parallel processing for I/O-bound operations
- Implement caching for expensive operations (hash, embedding, query)
- Use memory-mapped files for large file operations
- Optimize database queries with proper indexing
- Profile before optimizing

## Error Handling
- Use custom exceptions from `nodupe.core.errors`
- Provide meaningful error messages
- Log errors appropriately (debug, info, warning, error, critical)
- Implement graceful degradation when possible
- Clean up resources in finally blocks

## Dependencies
- Keep dependencies minimal and well-justified
- Prefer standard library when possible
- Document any new dependencies in requirements or pyproject.toml
- Consider optional dependencies for advanced features (GPU, ML, etc.)

## Git & Version Control
- Write clear, descriptive commit messages
- Keep commits atomic and focused
- Use feature branches for development
- Never commit cache files, build artifacts, or secrets
- Follow conventional commit format when possible

## Documentation
- Update README.md for user-facing changes
- Update PLUGIN_DEVELOPMENT_GUIDE.md for plugin API changes
- Include inline comments for complex logic
- Maintain up-to-date docstrings

## Commands & CLI
- CLI commands are implemented as plugins in `nodupe/plugins/commands/`
- Main commands: `scan`, `verify`, `similarity`, `apply`
- Use click or argparse for CLI argument parsing
- Provide helpful error messages and usage information

## Common Patterns
- **Scanning**: Use `FileWalker` → `FileProcessor` → `FileHasher` pipeline
- **Database**: Use context managers for connections and transactions
- **Plugins**: Register with decorator or explicit registration
- **Caching**: Multi-level caching with invalidation strategies
- **Logging**: Centralized logging configuration from `nodupe.core.logging`

## Development Workflow
1. Create feature branch from main
2. Implement feature with tests
3. Run full test suite
4. Update documentation
5. Create pull request with clear description
6. Address review feedback
7. Merge to main after approval

## Project-Specific Notes
- This is an LLM-assisted project with known complexity
- Prioritize safety and data integrity over performance
- Extensive error handling due to diverse file system scenarios
- Support for various file types and archive formats
- Time synchronization important for accurate duplicate detection
