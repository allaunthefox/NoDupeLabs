# Development Tools

Project-specific utilities organized by functional area.

## Structure

```
tools/
├── core/           # Core system utilities
├── plugins/        # Plugin development tools
├── scan/           # Scanning utilities
├── analysis/       # Analysis tools
├── security/       # Security tools
└── wiki/           # Wiki management tools
```

## Core Tools

### fix_docstrings.py

Adds docstrings to Python functions.

```bash
python tools/core/fix_docstrings.py nodupe/
python tools/core/fix_docstrings.py --apply nodupe/
```

### api_check.py

Validates API endpoints and decorators.

```bash
python tools/core/api_check.py
```

### check_toml.py

Validates TOML configuration files.

```bash
python tools/core/check_toml.py
```

### verify_idempotence.py

Verifies operations are idempotent.

```bash
python tools/core/verify_idempotence.py
```

### strictness_check.py

Enforces coding standards (type annotations).

```bash
python tools/core/strictness_check.py
```

### compliance_scan.py

Security and best practices scan.

```bash
python tools/core/compliance_scan.py
```

## Analysis Tools

### collision_check.py

Detect hash collisions.

```bash
python tools/analysis/collision_check.py
```

### deep_idempotence.py

Deep idempotence verification.

```bash
python tools/analysis/deep_idempotence.py
```

## Security Tools

### red_team.py

Red team security assessment.

```bash
python tools/security/red_team.py
```

## Plugin Tools

### plugin_scaffold.py

Scaffold new plugins.

```bash
python tools/plugins/plugin_scaffold.py similarity my_plugin
python tools/plugins/plugin_scaffold.py database my_plugin
python tools/plugins/plugin_scaffold.py command my_plugin
```

## Wiki Tools

### enforce_wiki_style.sh

Enforce wiki markdown style.

```bash
bash tools/wiki/enforce_wiki_style.sh
bash tools/wiki/enforce_wiki_style.sh --fix
```
