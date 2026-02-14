# Contributing

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch

## Development Workflow

```bash
# Create branch
git checkout -b feature/my-feature

# Make changes
# ... edit code ...

# Run tests
pytest tests/ -v

# Commit
git add .
git commit -m "feat: add feature"

# Push
git push origin feature/my-feature
```

## Code Standards

- Follow PEP 8
- Add docstrings to all functions
- Use type annotations
- Run pylint before committing

## Testing

- All new code requires tests
- Run `pytest tests/` before submitting
- Aim for 60%+ coverage

## Pull Requests

1. Keep PRs small (<500 lines)
2. Update documentation if needed
3. Reference related issues
4. Wait for CI to pass

## Commit Messages

Use Conventional Commits:

```
feat: add new feature
fix: resolve bug
docs: update documentation
test: add tests
refactor: restructure code
```

## Review Process

1. Automated checks run (CI)
2. Maintainer reviews code
3. Address feedback
4. Merge when approved
