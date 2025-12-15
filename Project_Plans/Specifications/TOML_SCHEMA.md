<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2025 Allaun -->

# NoDupeLabs Configuration Schema - JSON Schema Standard

## Overview

This document defines the configuration schema following the**JSON Schema Draft 7**standard (IETF RFC 8259) for maximum compatibility with industry tools. The schema can be validated using any standard JSON Schema validator.

## Schema Standard Compliance

### TOML Standard (ISO/IEC 21646:2023)**Standard**: ISO/IEC 21646:2023 - Information technology — TOML (Tom's Obvious, Minimal Language)**Official Name**: TOMLStatus: International Standard published by ISO/IEC**Publication Date**: 2023**Reference**: <https://www.iso.org/standard/82444.html>

### JSON Schema Standard**Standard**: JSON Schema Draft 7 (IETF RFC 8259)**Format**: TOML → JSON/JSON-L conversion for validation**Validation Tools**: ajv, jsonschema, python-jsonschema, etc

### Format Standards**JSON**: RFC 8259 (The JavaScript Object Notation (JSON) Data Interchange Format)**JSON-L**: RFC 7464 (JSON Text Sequences)

## JSON Schema Definition

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "NoDupeLabs Configuration Schema",
  "description": "Configuration schema for NoDupeLabs following JSON Schema Draft 7 standard",
  "type": "object",
  "definitions": {
```

"nodupe": {
  "type": "object",
  "properties": {

```text
"version": {
  "type": "string",
  "pattern": "^\\d+\\.\\d+\\.\\d+$",
  "description": "Configuration schema version following semantic versioning"
}
```

  },
  "required": ["version"],
  "additionalProperties": false
},
"core": {
  "type": "object",
  "properties": {

```text
"database_path": {
  "type": "string",
  "minLength": 1,
  "description": "Path to SQLite database file"
},
"database_timeout": {
  "type": "number",
  "minimum": 0,
  "exclusiveMinimum": true,
  "default": 30.0,
  "description": "Database connection timeout in seconds"
},
"database_journal_mode": {
  "type": "string",
  "enum": ["WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"],
  "default": "WAL",
  "description": "SQLite journal mode"
},
"log_level": {
  "type": "string",
  "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
  "description": "Logging level following RFC 5424 syslog levels"
},
"log_file": {
  "type": "string",
  "minLength": 1,
  "description": "Path to log file"
},
"log_max_size": {
  "type": "integer",
  "minimum": 1,
  "default": 10485760,
  "description": "Maximum log file size in bytes"
},
"log_backup_count": {
  "type": "integer",
  "minimum": 0,
  "default": 5,
  "description": "Number of log backups to keep"
},
"max_workers": {
  "type": "integer",
  "minimum": 1,
  "default": 8,
  "description": "Maximum worker threads"
},
"max_memory_mb": {
  "type": "integer",
  "minimum": 1,
  "default": 4096,
  "description": "Maximum memory usage in megabytes"
},
"max_file_handles": {
  "type": "integer",
  "minimum": 1,
  "default": 1024,
  "description": "Maximum open file handles"
},
"allow_symlinks": {
  "type": "boolean",
  "default": false,
  "description": "Allow symbolic links"
},
"validate_paths": {
  "type": "boolean",
  "default": true,
  "description": "Validate file paths"
}
```

  },
  "required": ["database_path", "log_level", "log_file"],
  "additionalProperties": false
},
"database": {
  "type": "object",
  "properties": {

```text
"pool_size": {
  "type": "integer",
  "minimum": 1,
  "default": 5,
  "description": "Connection pool size"
},
"max_connections": {
  "type": "integer",
  "minimum": 1,
  "default": 20,
  "description": "Maximum connections"
},
"connection_timeout": {
  "type": "number",
  "minimum": 0,
  "exclusiveMinimum": true,
  "default": 10.0,
  "description": "Connection timeout in seconds"
},
"synchronous": {
  "type": "string",
  "enum": ["OFF", "NORMAL", "FULL", "EXTRA"],
  "default": "NORMAL",
  "description": "SQLite synchronous mode"
},
"cache_size": {
  "type": "integer",
  "default": -2000,
  "description": "SQLite cache size in KB (negative = MB)"
},
"temp_store": {
  "type": "string",
  "enum": ["DEFAULT", "FILE", "MEMORY"],
  "default": "MEMORY",
  "description": "SQLite temp store"
},
"vacuum_on_startup": {
  "type": "boolean",
  "default": false,
  "description": "Run VACUUM on startup"
},
"optimize_on_startup": {
  "type": "boolean",
  "default": true,
  "description": "Run OPTIMIZE on startup"
}
```

  },
  "additionalProperties": false
},
"scan": {
  "type": "object",
  "properties": {

```text
"include_patterns": {
  "type": "array",
  "items": {
```

"type": "string",
"minLength": 1

```text
  },
  "default": ["**/*"],
  "description": "File patterns to include (glob patterns)"
},
"exclude_patterns": {
  "type": "array",
  "items": {
```

"type": "string",
"minLength": 1

```text
  },
  "default": [".git", ".venv", "node_modules"],
  "description": "File patterns to exclude (glob patterns)"
},
"max_depth": {
  "type": "integer",
  "minimum": 1,
  "default": 10,
  "description": "Maximum directory depth"
},
"follow_symlinks": {
  "type": "boolean",
  "default": false,
  "description": "Follow symbolic links"
},
"hash_algorithm": {
  "type": "string",
  "enum": ["md5", "sha1", "sha256", "sha512"],
  "default": "sha256",
  "description": "Hash algorithm following FIPS 180-4"
},
"buffer_size": {
  "type": "integer",
  "minimum": 1,
  "default": 65536,
  "description": "Read buffer size in bytes (power of 2)"
},
"min_file_size": {
  "type": "integer",
  "minimum": 0,
  "default": 0,
  "description": "Minimum file size in bytes"
},
"max_file_size": {
  "type": "integer",
  "minimum": 0,
  "default": 0,
  "description": "Maximum file size in bytes (0 = no limit)"
},
"workers": {
  "type": "integer",
  "minimum": 1,
  "default": 4,
  "description": "Number of worker threads"
},
"batch_size": {
  "type": "integer",
  "minimum": 1,
  "default": 1000,
  "description": "Batch size for database operations"
},
"use_mmap": {
  "type": "boolean",
  "default": true,
  "description": "Use memory-mapped files for large files"
},
"map_threshold": {
  "type": "integer",
  "minimum": 1,
  "default": 10485760,
  "description": "MMAP threshold in bytes"
}
```

  },
  "additionalProperties": false
},
"plugins": {
  "type": "object",
  "properties": {

```text
"scan_dirs": {
  "type": "array",
  "items": {
```

"type": "string",
"minLength": 1

```text
  },
  "default": ["nodupe/plugins"],
  "description": "Directories to scan for plugins"
},
"auto_load": {
  "type": "boolean",
  "default": true,
  "description": "Auto-load plugins on startup"
},
"load_order": {
  "type": "array",
  "items": {
```

"type": "string",
"enum": ["commands", "similarity", "ml", "gpu", "video", "network"]

```text
  },
  "default": ["commands", "similarity", "ml", "gpu", "video", "network"],
  "description": "Plugin load order"
},
"commands": {
  "$ref": "#/definitions/plugin_config"
},
"similarity": {
  "$ref": "#/definitions/plugin_config"
},
"ml": {
  "$ref": "#/definitions/plugin_config"
},
"gpu": {
  "$ref": "#/definitions/plugin_config"
},
"video": {
  "$ref": "#/definitions/plugin_config"
},
"network": {
  "$ref": "#/definitions/plugin_config"
}
```

  },
  "additionalProperties": false
},
"plugin_config": {
  "type": "object",
  "properties": {

```text
"enabled": {
  "type": "boolean",
  "default": true,
  "description": "Plugin enabled status"
},
"backend": {
  "type": "string",
  "description": "Backend implementation"
},
"model_dir": {
  "type": "string",
  "minLength": 1,
  "description": "Model directory path"
},
"cache_models": {
  "type": "boolean",
  "default": true,
  "description": "Cache models in memory"
},
"device_id": {
  "type": "integer",
  "minimum": 0,
  "default": 0,
  "description": "GPU device ID"
},
"max_memory_mb": {
  "type": "integer",
  "minimum": 1,
  "description": "Maximum memory in megabytes"
},
"frames_per_video": {
  "type": "integer",
  "minimum": 1,
  "default": 10,
  "description": "Frames to extract per video"
},
"hash_algorithm": {
  "type": "string",
  "enum": ["phash", "ahash", "dhash", "whash"],
  "default": "phash",
  "description": "Perceptual hash algorithm"
},
"timeout": {
  "type": "number",
  "minimum": 0,
  "exclusiveMinimum": true,
  "default": 30.0,
  "description": "Network timeout in seconds"
},
"retry_count": {
  "type": "integer",
  "minimum": 0,
  "default": 3,
  "description": "Maximum retry attempts"
}
```

  },
  "additionalProperties": false
},
"cache": {
  "type": "object",
  "properties": {

```text
"enable_hash_cache": {
  "type": "boolean",
  "default": true,
  "description": "Enable hash caching"
},
"enable_query_cache": {
  "type": "boolean",
  "default": true,
  "description": "Enable query caching"
},
"enable_embedding_cache": {
  "type": "boolean",
  "default": true,
  "description": "Enable embedding caching"
},
"max_cache_size_mb": {
  "type": "integer",
  "minimum": 1,
  "default": 1024,
  "description": "Maximum cache size in megabytes"
},
"max_items": {
  "type": "integer",
  "minimum": 1,
  "default": 100000,
  "description": "Maximum number of cached items"
},
"ttl_seconds": {
  "type": "integer",
  "minimum": 1,
  "default": 3600,
  "description": "Time-to-live in seconds"
},
"cache_dir": {
  "type": "string",
  "minLength": 1,
  "default": "~/.nodupe/cache",
  "description": "Cache directory path"
},
"hash_cache_file": {
  "type": "string",
  "default": "hash_cache.db",
  "description": "Hash cache file name"
},
"query_cache_file": {
  "type": "string",
  "default": "query_cache.db",
  "description": "Query cache file name"
},
"embedding_cache_file": {
  "type": "string",
  "default": "embedding_cache.db",
  "description": "Embedding cache file name"
}
```

  },
  "additionalProperties": false
},
"performance": {
  "type": "object",
  "properties": {

```text
"max_workers": {
  "type": "integer",
  "minimum": 1,
  "default": 8,
  "description": "Maximum worker threads"
},
"worker_timeout": {
  "type": "integer",
  "minimum": 1,
  "default": 300,
  "description": "Worker timeout in seconds"
},
"queue_size": {
  "type": "integer",
  "minimum": 1,
  "default": 1000,
  "description": "Task queue size"
},
"large_file_threshold_mb": {
  "type": "integer",
  "minimum": 1,
  "default": 100,
  "description": "Large file threshold in megabytes"
},
"use_mmap_for_large_files": {
  "type": "boolean",
  "default": true,
  "description": "Use MMAP for large files"
},
"max_memory_per_worker_mb": {
  "type": "integer",
  "minimum": 1,
  "default": 512,
  "description": "Max memory per worker in megabytes"
},
"io_buffer_size": {
  "type": "integer",
  "minimum": 1,
  "default": 8192,
  "description": "I/O buffer size in bytes"
},
"max_io_operations": {
  "type": "integer",
  "minimum": 1,
  "default": 100,
  "description": "Max concurrent I/O operations"
},
"io_timeout": {
  "type": "number",
  "minimum": 0,
  "exclusiveMinimum": true,
  "default": 30.0,
  "description": "I/O operation timeout in seconds"
},
"network_timeout": {
  "type": "number",
  "minimum": 0,
  "exclusiveMinimum": true,
  "default": 10.0,
  "description": "Network operation timeout in seconds"
},
"max_retries": {
  "type": "integer",
  "minimum": 0,
  "default": 3,
  "description": "Maximum retry attempts"
},
"retry_delay": {
  "type": "number",
  "minimum": 0,
  "default": 1.0,
  "description": "Retry delay in seconds"
}
```

  },
  "additionalProperties": false
}

```text
  },
  "properties": {
```

"nodupe": {
  "$ref": "#/definitions/nodupe"
},
"core": {
  "$ref": "#/definitions/core"
},
"database": {
  "$ref": "#/definitions/database"
},
"scan": {
  "$ref": "#/definitions/scan"
},
"plugins": {
  "$ref": "#/definitions/plugins"
},
"cache": {
  "$ref": "#/definitions/cache"
},
"performance": {
  "$ref": "#/definitions/performance"
}

```text
  },
  "required": ["nodupe", "core"],
  "additionalProperties": false
}
```

## Standard Compliance

### JSON Schema Draft 7 Features Used

1.**Core Vocabulary**: `type`, `properties`, `required`, `additionalProperties`
1.**Validation Vocabulary**: `minimum`, `maximum`, `pattern`, `enum`
1.**Metadata Vocabulary**: `title`, `description`, `default`
1.**Structure**: `$ref` for references, `definitions` for reusable schemas

### Industry Standards Referenced

1.**Semantic Versioning**: `version` field follows SemVer 2.0.0
1.**Syslog Levels**: `log_level` follows RFC 5424
1.**FIPS 180-4**: Hash algorithms follow NIST standards
1.**SQLite Standards**: Database parameters follow SQLite conventions
1.**Glob Patterns**: File patterns follow POSIX glob standards

### ISO Metadata Standards

For applications requiring standardized metadata formats, the following ISO standards are relevant:

1.**ISO 19115-1:2014**- Geographic information — Metadata

- Standard for describing geographic information and services

- Used for geospatial data metadata

1.**ISO 15836-1:2017**- Information and documentation — The Dublin Core metadata element set

- Dublin Core Metadata Initiative (DCMI) standard

- 15 core metadata elements for resource description

1.**ISO 19139:2007**- Geographic information — Metadata — XML schema implementation

- XML implementation of ISO 19115 for geospatial metadata

1.**ISO 23081-1:2017**- Information and documentation — Records management processes — Metadata for records

- Metadata standards for records management

1.**ISO 16363:2012**- Space data and information transfer systems — Audit and certification of trustworthy digital repositories

- Metadata requirements for digital preservation

1.**ISO 14721:2012**- Space data and information transfer systems — Open archival information system (OAIS) — Reference model

- OAIS reference model for digital archival systems

### Metadata Format Compliance

For applications that need to comply with specific metadata standards:

-**Dublin Core**: Use ISO 15836-1 for basic resource description
-**Geospatial**: Use ISO 19115-1 for geographic information metadata
-**Digital Preservation**: Use ISO 16363 and ISO 14721 for archival systems
-**Records Management**: Use ISO 23081-1 for document management

### Integration Recommendations

When implementing metadata standards:

1.**Use Standard Schemas**: Implement ISO metadata standards for interoperability
1.**Validation Tools**: Use standard-compliant validation tools
1.**Conversion Utilities**: Provide conversion between TOML/JSON and standard metadata formats
1.**Documentation**: Document metadata standard compliance in specifications

For NoDupeLabs, the current TOML/JSON schema provides configuration management, while ISO metadata standards would be relevant for applications requiring specialized metadata formats for specific domains (geospatial, archival, records management, etc.).

## Validation Implementation

### Python Example (using jsonschema)

```python
import json
import jsonschema
import toml

def validate_config(config_path):
```

"""Validate configuration file against JSON Schema standard"""

## Load schema

with open('config_schema.json', 'r') as f:

```text
schema = json.load(f)
```

```text

```

## Load TOML config and convert to JSON

with open(config_path, 'r') as f:

```text
config = toml.load(f)
```

```text

```

## Validate

try:

```python
jsonschema.validate(instance=config, schema=schema)
return True, "Configuration is valid"
```

except jsonschema.ValidationError as e:

```python
return False, f"Validation error: {e.message}"
```

```text

## Usage
valid, message = validate_config('nodupe.toml')
print(f"Config validation: {message}")
```

## JavaScript Example (using ajv)

```javascript
const fs = require('fs');
const toml = require('toml');
const Ajv = require('ajv');
const ajv = new Ajv();

function validateConfig(configPath) {
```

// Load schema
const schema = JSON.parse(fs.readFileSync('config_schema.json', 'utf8'));

```text

```

// Load TOML config and convert to JSON
const config = toml.parse(fs.readFileSync(configPath, 'utf8'));

```text

```

// Validate
const validate = ajv.compile(schema);
const valid = validate(config);

```text

```

if (!valid) {

```python
console.error('Validation errors:', validate.errors);
return false;
```

}
return true;

```text
}

// Usage
const isValid = validateConfig('nodupe.toml');
console.log(`Config validation: ${isValid ? 'Valid' : 'Invalid'}`);
```

## Format Support: JSON and JSON-L Standards

### JSON Standard Support (RFC 8259)**Standard**: JSON (JavaScript Object Notation) - RFC 8259**MIME Type**: `application/json`**File Extension**: `.json`

```json
{
  "nodupe": {
```

"version": "1.0.0"

```text
  },
  "core": {
```

"database_path": "~/.nodupe/database.db",
"log_level": "INFO",
"log_file": "~/.nodupe/nodupe.log",
"max_workers": 8,
"allow_symlinks": false

```text
  },
  "database": {
```

"pool_size": 5,
"synchronous": "NORMAL",
"cache_size": -2000

```text
  }
}
```

### JSON-L (JSON Lines) Standard Support (RFC 7464)**Standard**: JSON Lines - RFC 7464**MIME Type**: `application/json-lines`**File Extension**: `.jsonl` or `.ndjson`

```json
{"nodupe": {"version": "1.0.0"}}
{"core": {"database_path": "~/.nodupe/database.db", "log_level": "INFO", "log_file": "~/.nodupe/nodupe.log", "max_workers": 8, "allow_symlinks": false}}
{"database": {"pool_size": 5, "synchronous": "NORMAL", "cache_size": -200}}
```

### TOML to JSON/JSON-L Conversion

Since JSON Schema validates JSON data, TOML configuration files must be converted to either JSON or JSON-L format for validation.

#### TOML to JSON Conversion Rules

1.**TOML Tables**→**JSON Objects**1.**TOML Arrays**→**JSON Arrays**1.**TOML Primitives**→**JSON Primitives**(strings, numbers, booleans)
1.**TOML Dates**→**JSON Strings**(ISO 8601 format)

#### TOML to JSON-L Conversion Rules

1.**Each TOML Table**→**Separate JSON Line**1.**Arrays and Primitives**→**Same as JSON conversion**1.**Nested Tables**→**Separate JSON Lines with dot notation or nested objects**1.**Comments**→**Removed (JSON-L doesn't support comments)**### Conversion Examples

#### Python Conversion Example

```python
import json
import toml

def toml_to_json(toml_content):
```

"""Convert TOML to JSON format"""
config = toml.loads(toml_content)
return json.dumps(config, indent=2)

```python

def toml_to_jsonl(toml_content):
```

"""Convert TOML to JSON-L format"""
config = toml.loads(toml_content)
json_lines = []

```text

```

## Convert each top-level section to a separate line

for section, data in config.items():

```text
line = {section: data}
json_lines.append(json.dumps(line))
```

```text

```

return '\n'.join(json_lines)

```text

## Usage
with open('config.toml', 'r') as f:
```

toml_content = f.read()

```text

json_config = toml_to_json(toml_content)
jsonl_config = toml_to_jsonl(toml_content)
```

### JavaScript Conversion Example

```javascript
const fs = require('fs');
const toml = require('toml');

function tomlToJson(tomlContent) {
```

// Parse TOML to JavaScript object
const config = toml.parse(tomlContent);
// Convert to JSON string
return JSON.stringify(config, null, 2);

```text
}

function tomlToJsonl(tomlContent) {
```

// Parse TOML to JavaScript object
const config = toml.parse(tomlContent);
// Convert each section to separate JSON line
const lines = [];

```text

```

for (const [section, data] of Object.entries(config)) {

```text
const line = JSON.stringify({[section]: data});
lines.push(line);
```

}

```text

```

return lines.join('\n');

```text
}

// Usage
const tomlContent = fs.readFileSync('config.toml', 'utf8');
const jsonConfig = tomlToJson(tomlContent);
const jsonlConfig = tomlToJsonl(tomlContent);
```

### Validation with Both Formats

#### JSON Validation

```python
import jsonschema

## Validate standard JSON
with open('config.json', 'r') as f:
```

config = json.load(f)

```text

jsonschema.validate(instance=config, schema=schema)
```

## JSON-L Validation

```python
import jsonschema

## Validate JSON-L (line by line or combined)
with open('config.jsonl', 'r') as f:
```

lines = f.readlines()

```text

## Option 1: Validate each line separately
for line in lines:
```

if line.strip():  # Skip empty lines

```text
config_part = json.loads(line)
## Validate against appropriate sub-schema
jsonschema.validate(instance=config_part, schema=sub_schema)
```

```text

## Option 2: Combine lines and validate as full JSON
full_config = {}
for line in lines:
```

if line.strip():

```text
part = json.loads(line)
full_config.update(part)
```

```text

jsonschema.validate(instance=full_config, schema=schema)
```

## Schema Compatibility

The JSON Schema definition provided supports both JSON and JSON-L formats:

1.**JSON**: Direct validation of the complete configuration object
1.**JSON-L**: Line-by-line validation or combined validation after parsing

### Industry Standard Tools Support

Both formats are supported by industry-standard tools:

#### JSON Tools

-**Python**: `json`, `jsonschema`
-**JavaScript**: `JSON.parse()`, `ajv`
-**Java**: `Jackson`, `Gson`
-**Go**: `encoding/json`
-**Rust**: `serde_json`

#### JSON-L Tools

-**Python**: `jsonlines` package
-**JavaScript**: Line-by-line parsing
-**Command-line**: `jq`, `jsonl-tools`
-**Streaming**: Ideal for large datasets and log processing

### Use Case Recommendations

 | Format | Use Case | Advantages |
 | --- | --- | --- | --- |
 | **JSON** | Single configuration files, API responses | Human-readable, widely supported |
 | **JSON-L** | Log files, large datasets, streaming | Memory-efficient, appendable, line-based processing |

This dual-format support ensures maximum compatibility with industry tools and allows users to choose the format that best suits their use case.

## Schema Evolution

### Versioning Policy

1.**Schema Version**: Follows Semantic Versioning 2.0.0
1.**Backward Compatibility**: Major versions maintain backward compatibility
1.**Deprecation**: Deprecated properties supported for 2 major versions
1.**Validation**: Strict validation with clear error messages

### Migration Path

```json
{
  "version": "2.0.0",
  "migrations": {
```

"1.0": {
  "from": "1.0.0",
  "to": "2.0.0",
  "changes": [

```text
"Added performance.network section",
"Deprecated cache.ttl_seconds in favor of cache.ttl_seconds",
"Added validation for all string formats"
```

  ],
  "migration_script": "migrate_1_to_2.py"
}

```text
  }
}
```

## Industry Standard Tools Integration

### Recommended Validation Tools

1.**Python**: `jsonschema` (PyPI)
1.**JavaScript**: `ajv` (npm)
1.**Java**: `networknt/json-schema-validator` (Maven)
1.**Go**: `xeipuuv/gojsonschema` (GitHub)
1.**Rust**: `jsonschema` (crates.io)

### CI/CD Integration

```yaml
## GitHub Actions example
name: Config Validation
on: [push, pull_request]

jobs:
  validate:
```

runs-on: ubuntu-latest
steps:

- uses: actions/checkout@v4

- name: Set up Python

```text
uses: actions/setup-python@v4
with:
  python-version: '3.9'
```

- name: Install dependencies

```text
run: pip install jsonschema pytoml
```

- name: Validate config

```text
run: python validate_config.py config.example.toml
```

```text
```

This JSON Schema standard compliance ensures that NoDupeLabs configuration can be validated using any industry-standard JSON Schema validator, providing maximum compatibility and eliminating custom validation requirements.
