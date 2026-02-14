# Development Tools

Project-specific utilities organized by functional area.

## Structure

```
tools/
├── core/       # Core system utilities
├── plugins/     # Plugin development tools
├── scan/        # Scanning utilities
└── analysis/   # Analysis tools
```

## Core Tools

### fix_docstrings.py

Adds docstrings to Python functions.

```bash
python tools/core/fix_docstrings.py nodupe/
python tools/core/fix_docstrings.py --apply nodupe/
```

### api_check.py

Validates API endpoints.
