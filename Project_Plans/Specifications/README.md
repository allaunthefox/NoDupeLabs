# NoDupeLabs Specifications

## Overview

This directory contains detailed technical specifications for NoDupeLabs components, ensuring consistency, compatibility, and proper implementation across all parts of the system.

## Specification Documents

### 📋 Configuration Schema**File** [`TOML_SCHEMA.md`](TOML_SCHEMA.md)**Purpose** Defines the exact schema rules for NoDupeLabs TOML configuration files**Contents**

- Complete TOML configuration structure
- Section-by-section specifications
- Field validation rules
- Type constraints and requirements
- Example complete configuration
- Schema evolution policy**Usage**:

```toml
# All configuration files must adhere to this schema
[nodupe]
version = "1.0.0"

[core]
database_path = "~/.nodupe/database.db"
log_level = "INFO"
```

## 🗃️ Database Schema**File** [`DATABASE_SCHEMA.md`](DATABASE_SCHEMA.md)**Purpose** Defines the exact database schema for NoDupeLabs SQLite database**Contents**

- Core tables (files, embeddings, relationships)
- Plugin tables (plugins, plugin_config)
- Cache tables (hash_cache, query_cache)
- System tables (system_info, migrations)
- Database constraints and indexing
- Transaction management patterns
- Schema validation rules
- Performance optimization techniques**Usage**:

```python
# Database operations must follow this schema
def initialize_database():
```

conn.execute("""
CREATE TABLE IF NOT EXISTS files (

```text
id INTEGER PRIMARY KEY AUTOINCREMENT,
path TEXT NOT NULL UNIQUE,
size INTEGER NOT NULL,
-- ... other fields per specification
```

)
""")

```text
```

## 📄 File Metadata Standards**File** [`FILE_METADATA_STANDARDS.md`](FILE_METADATA_STANDARDS.md)**Purpose** Defines metadata standards for file handling and processing**Contents**

- ISO metadata standards (Dublin Core, EXIF, ID3, ISO BMFF)
- FIPS 180-4 hash algorithms
- CSV (RFC 4180) and TSV (ISO/IEC 27032) support
- File metadata extraction specifications
- Metadata validation and normalization**Usage**:

```python
# Extract metadata following standards
metadata = extract_file_metadata(file_path)
# Returns standardized metadata dict
```

## 🧵 Python Threading Support**File** [`PYTHON_THREADING.md`](PYTHON_THREADING.md)**Purpose** Comprehensive guide to Python's modern threading and parallelism features**Contents**

- Python 3.12-3.14 threading evolution
- Free-threaded mode (PEP 703) - GIL removal
- Per-interpreter GIL (PEP 684)
- Multiple interpreters module (PEP 734)
- Concurrent execution patterns (threading, asyncio, futures)
- Decision matrix for choosing concurrency models
- Thread safety considerations
- Best practices for parallel processing
- NoDupeLabs implementation recommendations**Usage**:

```python
from concurrent.futures import InterpreterPoolExecutor

# Python 3.14+ parallel execution with interpreters
with InterpreterPoolExecutor(max_interpreters=4) as executor:
```

results = executor.map(process_file, files)

```text

# Or use free-threaded Python 3.13+
import sys
if sys.flags.gil == 0:
```

### Running without GIL - true parallel threading

pass

```text
```

## Specification Standards

### Versioning

All specifications follow semantic versioning:

-**Major version**: Breaking changes
-**Minor version**: Backward-compatible additions
-**Patch version**: Clarifications and fixes

### Compliance Requirements

1.**Strict Adherence**: All implementations must follow specifications exactly
1.**Validation**: Implement validation for configuration and data
1.**Error Handling**: Clear error messages for specification violations
1.**Documentation**: Reference specifications in implementation docs

### Change Process

1.**Proposal**: Create specification change proposal
1.**Review**: Team review and feedback
1.**Approval**: Approval by architecture team
1.**Implementation**: Update specification documents
1.**Migration**: Provide migration path if needed
1.**Documentation**: Update all related documentation

## Specification Validation

### Configuration Validation

```python
def validate_config(config):
```

"""Validate configuration against TOML schema"""
required_sections = ['nodupe', 'core']
for section in required_sections:

```text
if section not in config:
```

raise ValidationError(f"Missing required section: {section}")

```text
```

```text

```

# ### Validate core section

core_fields = ['database_path', 'log_level', 'log_file']
for field in core_fields:

```text
if field not in config['core']:
```

raise ValidationError(f"Missing required field: core.{field}")

```text
```

```text

```

# ### Validate field types and constraints

# ... additional validation per schema

```text
```

## Database Validation

```python
def validate_database_schema():
```

"""Validate database schema against specification"""
conn = get_connection()
cursor = conn.cursor()

```text

```

# ### Check required tables exist

required_tables = [

```text
'files', 'embeddings', 'file_relationships',
'plugins', 'plugin_config', 'hash_cache',
'query_cache', 'system_info', 'migrations'
```

]

```text

```

for table in required_tables:

```text
cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
if not cursor.fetchone():
```

raise DatabaseError(f"Missing required table: {table}")

```text
```

```text

```

# ### Check required columns exist

## ... additional validation per schema

```text
```

## Specification Evolution

### Version Compatibility Matrix

| Specification | Version | Compatible With | Status |
| --- | --- | --- | --- | --- |
| TOML Schema | 1.0.0 | 0.9.x | Current |
| Database Schema | 1.0.0 | 0.9.x | Current |

### Deprecation Policy

1.**Notice Period**: 2 major versions
1.**Migration Path**: Clear upgrade instructions
1.**Documentation**: Deprecation notices in specs
1.**Validation**: Warnings for deprecated features

## Usage Guidelines

### For Developers

1.**Reference**: Consult specifications before implementation
1.**Validation**: Implement validation functions
1.**Testing**: Test against specification examples
1.**Documentation**: Reference specifications in code comments

### For Users

1.**Configuration**: Follow TOML schema for config files
1.**Troubleshooting**: Check specification compliance
1.**Upgrades**: Review specification changes
1.**Customization**: Extend within specification bounds

## Future Specifications

### Implemented Interfaces

1.**Plugin Interface**: Implemented in `nodupe.core.plugin_system`
1.**Command Interface**: Implemented in `nodupe.core.commands`

### Planned Specifications

1.**API Schema**: REST API specifications
1.**Event System**: Event emission and handling specifications
1.**Error Codes**: Standardized error code specifications

### Contribution

To contribute to specifications:

1.**Fork**: Fork the repository
1.**Branch**: Create feature branch
1.**Edit**: Update specification documents
1.**Test**: Validate specification changes
1.**PR**: Submit pull request for review

## Maintenance

### Update Frequency

-**Major Updates**: Quarterly (with major releases)
-**Minor Updates**: Monthly (with feature additions)
-**Patch Updates**: As needed (for clarifications)

### Review Process

1.**Technical Review**: Architecture team
1.**Implementation Review**: Development team
1.**Documentation Review**: Technical writers
1.**User Review**: Community feedback period

This specifications directory ensures consistent implementation and compatibility across all NoDupeLabs components.
