# NoDupeLabs Database Schema Specification

## Overview

This document defines the exact database schema for NoDupeLabs SQLite database. All database operations must adhere to this schema for data integrity and compatibility.

## Database Version**Current Version**: `1.0.0`**Compatibility**: Backward compatible with version `0.9.x`

## Database Structure

### Core Tables

#### `files` - File Metadata Table

```sql
CREATE TABLE files (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
path TEXT NOT NULL UNIQUE,
size INTEGER NOT NULL,
modified_time INTEGER NOT NULL,
created_time INTEGER NOT NULL,
accessed_time INTEGER,
file_type TEXT,
mime_type TEXT,
hash TEXT,
is_duplicate BOOLEAN DEFAULT FALSE,
duplicate_of INTEGER,
status TEXT DEFAULT 'active',
scanned_at INTEGER NOT NULL,
updated_at INTEGER NOT NULL,
FOREIGN KEY (duplicate_of) REFERENCES files(id) ON DELETE SET NULL

```text
);

CREATE INDEX idx_files_path ON files(path);
CREATE INDEX idx_files_size ON files(size);
CREATE INDEX idx_files_hash ON files(hash);
CREATE INDEX idx_files_is_duplicate ON files(is_duplicate);
CREATE INDEX idx_files_duplicate_of ON files(duplicate_of);
CREATE INDEX idx_files_status ON files(status);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `path` | TEXT | ❌ | File path | UNIQUE |
 | `size` | INTEGER | ❌ | File size in bytes | ≥ 0 |
 | `modified_time` | INTEGER | ❌ | Unix timestamp | ≥ 0 |
 | `created_time` | INTEGER | ❌ | Unix timestamp | ≥ 0 |
 | `accessed_time` | INTEGER | ✅ | Unix timestamp | ≥ 0 |
 | `file_type` | TEXT | ✅ | File type | - |
 | `mime_type` | TEXT | ✅ | MIME type | - |
 | `hash` | TEXT | ✅ | File hash | Length ≤ 128 |
 | `is_duplicate` | BOOLEAN | ❌ | Duplicate flag | DEFAULT FALSE |
 | `duplicate_of` | INTEGER | ✅ | Reference to original file | FOREIGN KEY |
 | `status` | TEXT | ❌ | File status | DEFAULT 'active' |
 | `scanned_at` | INTEGER | ❌ | Scan timestamp | ≥ 0 |
 | `updated_at` | INTEGER | ❌ | Update timestamp | ≥ 0 | **Status Values**: `active`, `deleted`, `archived`, `error`

#### `embeddings` - File Embeddings Table

```sql
CREATE TABLE embeddings (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
file_id INTEGER NOT NULL,
embedding BLOB NOT NULL,
model_version TEXT NOT NULL,
created_time INTEGER NOT NULL,
dimensions INTEGER NOT NULL,
FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE

```text
);

CREATE INDEX idx_embeddings_file_id ON embeddings(file_id);
CREATE INDEX idx_embeddings_model_version ON embeddings(model_version);
CREATE INDEX idx_embeddings_created_time ON embeddings(created_time);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `file_id` | INTEGER | ❌ | File reference | FOREIGN KEY |
 | `embedding` | BLOB | ❌ | Embedding vector | - |
 | `model_version` | TEXT | ❌ | Model version | - |
 | `created_time` | INTEGER | ❌ | Creation timestamp | ≥ 0 |
 | `dimensions` | INTEGER | ❌ | Vector dimensions | > 0 |

#### `file_relationships` - File Relationships Table

```sql
CREATE TABLE file_relationships (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
file1_id INTEGER NOT NULL,
file2_id INTEGER NOT NULL,
relationship_type TEXT NOT NULL,
similarity_score REAL,
created_at INTEGER NOT NULL,
UNIQUE(file1_id, file2_id, relationship_type),
FOREIGN KEY (file1_id) REFERENCES files(id) ON DELETE CASCADE,
FOREIGN KEY (file2_id) REFERENCES files(id) ON DELETE CASCADE

```text
);

CREATE INDEX idx_file_relationships_file1_id ON file_relationships(file1_id);
CREATE INDEX idx_file_relationships_file2_id ON file_relationships(file2_id);
CREATE INDEX idx_file_relationships_type ON file_relationships(relationship_type);
CREATE INDEX idx_file_relationships_similarity ON file_relationships(similarity_score);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `file1_id` | INTEGER | ❌ | First file reference | FOREIGN KEY |
 | `file2_id` | INTEGER | ❌ | Second file reference | FOREIGN KEY |
 | `relationship_type` | TEXT | ❌ | Relationship type | - |
 | `similarity_score` | REAL | ✅ | Similarity score | 0.0 ≤ score ≤ 1.0 |
 | `created_at` | INTEGER | ❌ | Creation timestamp | ≥ 0 | **Relationship Types**: `duplicate`, `similar`, `related`, `version`

### Plugin Tables

#### `plugins` - Plugin Registry Table

```sql
CREATE TABLE plugins (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT NOT NULL UNIQUE,
version TEXT NOT NULL,
type TEXT NOT NULL,
status TEXT NOT NULL,
load_order INTEGER DEFAULT 0,
enabled BOOLEAN DEFAULT TRUE,
created_at INTEGER NOT NULL,
updated_at INTEGER NOT NULL

```text
);

CREATE INDEX idx_plugins_name ON plugins(name);
CREATE INDEX idx_plugins_type ON plugins(type);
CREATE INDEX idx_plugins_status ON plugins(status);
CREATE INDEX idx_plugins_enabled ON plugins(enabled);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `name` | TEXT | ❌ | Plugin name | UNIQUE |
 | `version` | TEXT | ❌ | Plugin version | - |
 | `type` | TEXT | ❌ | Plugin type | - |
 | `status` | TEXT | ❌ | Plugin status | - |
 | `load_order` | INTEGER | ❌ | Load order | DEFAULT 0 |
 | `enabled` | BOOLEAN | ❌ | Enabled flag | DEFAULT TRUE |
 | `created_at` | INTEGER | ❌ | Creation timestamp | ≥ 0 |
 | `updated_at` | INTEGER | ❌ | Update timestamp | ≥ 0 | **Plugin Types**: `command`, `similarity`, `ml`, `gpu`, `video`, `network`**Status Values**: `loaded`, `failed`, `disabled`, `unloaded`

#### `plugin_config` - Plugin Configuration Table

```sql
CREATE TABLE plugin_config (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
plugin_id INTEGER NOT NULL,
config_key TEXT NOT NULL,
config_value TEXT,
data_type TEXT NOT NULL,
is_required BOOLEAN DEFAULT FALSE,
default_value TEXT,
UNIQUE(plugin_id, config_key),
FOREIGN KEY (plugin_id) REFERENCES plugins(id) ON DELETE CASCADE

```text
);

CREATE INDEX idx_plugin_config_plugin_id ON plugin_config(plugin_id);
CREATE INDEX idx_plugin_config_key ON plugin_config(config_key);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `plugin_id` | INTEGER | ❌ | Plugin reference | FOREIGN KEY |
 | `config_key` | TEXT | ❌ | Configuration key | - |
 | `config_value` | TEXT | ✅ | Configuration value | - |
 | `data_type` | TEXT | ❌ | Data type | - |
 | `is_required` | BOOLEAN | ❌ | Required flag | DEFAULT FALSE |
 | `default_value` | TEXT | ✅ | Default value | - | **Data Types**: `string`, `integer`, `float`, `boolean`, `json`

### Cache Tables

#### `hash_cache` - Hash Cache Table

```sql
CREATE TABLE hash_cache (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
file_path TEXT NOT NULL UNIQUE,
file_size INTEGER NOT NULL,
modified_time INTEGER NOT NULL,
hash_value TEXT NOT NULL,
algorithm TEXT NOT NULL,
created_at INTEGER NOT NULL,
expires_at INTEGER NOT NULL

```text
);

CREATE INDEX idx_hash_cache_path ON hash_cache(file_path);
CREATE INDEX idx_hash_cache_size ON hash_cache(file_size);
CREATE INDEX idx_hash_cache_modified ON hash_cache(modified_time);
CREATE INDEX idx_hash_cache_hash ON hash_cache(hash_value);
CREATE INDEX idx_hash_cache_algorithm ON hash_cache(algorithm);
CREATE INDEX idx_hash_cache_expires ON hash_cache(expires_at);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `file_path` | TEXT | ❌ | File path | UNIQUE |
 | `file_size` | INTEGER | ❌ | File size | ≥ 0 |
 | `modified_time` | INTEGER | ❌ | Modification time | ≥ 0 |
 | `hash_value` | TEXT | ❌ | Hash value | - |
 | `algorithm` | TEXT | ❌ | Hash algorithm | - |
 | `created_at` | INTEGER | ❌ | Creation time | ≥ 0 |
 | `expires_at` | INTEGER | ❌ | Expiration time | ≥ 0 | **Algorithm Values**: `md5`, `sha1`, `sha256`, `sha512`

#### `query_cache` - Query Cache Table

```sql
CREATE TABLE query_cache (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
query_type TEXT NOT NULL,
query_params TEXT NOT NULL,
result_data BLOB NOT NULL,
created_at INTEGER NOT NULL,
expires_at INTEGER NOT NULL,
UNIQUE(query_type, query_params)

```text
);

CREATE INDEX idx_query_cache_type ON query_cache(query_type);
CREATE INDEX idx_query_cache_created ON query_cache(created_at);
CREATE INDEX idx_query_cache_expires ON query_cache(expires_at);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `query_type` | TEXT | ❌ | Query type | - |
 | `query_params` | TEXT | ❌ | Query parameters | - |
 | `result_data` | BLOB | ❌ | Result data | - |
 | `created_at` | INTEGER | ❌ | Creation time | ≥ 0 |
 | `expires_at` | INTEGER | ❌ | Expiration time | ≥ 0 | **Query Types**: `find_duplicates`, `find_similar`, `get_file_info`, `search_files`

### System Tables

#### `system_info` - System Information Table

```sql
CREATE TABLE system_info (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
key TEXT NOT NULL UNIQUE,
value TEXT,
data_type TEXT NOT NULL,
created_at INTEGER NOT NULL,
updated_at INTEGER NOT NULL

```text
);

CREATE INDEX idx_system_info_key ON system_info(key);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `key` | TEXT | ❌ | System key | UNIQUE |
 | `value` | TEXT | ✅ | System value | - |
 | `data_type` | TEXT | ❌ | Data type | - |
 | `created_at` | INTEGER | ❌ | Creation time | ≥ 0 |
 | `updated_at` | INTEGER | ❌ | Update time | ≥ 0 | **Data Types**: `string`, `integer`, `float`, `boolean`, `json`

#### `migrations` - Database Migration Table

```sql
CREATE TABLE migrations (
```

id INTEGER PRIMARY KEY AUTOINCREMENT,
version TEXT NOT NULL UNIQUE,
applied_at INTEGER NOT NULL,
description TEXT,
status TEXT NOT NULL

```text
);

CREATE INDEX idx_migrations_version ON migrations(version);
CREATE INDEX idx_migrations_applied ON migrations(applied_at);
```**Field Specifications**:

 | Field | Type | Nullable | Description | Constraints |
 | --- | --- | --- | --- | --- | --- |
 | `id` | INTEGER | ❌ | Primary key | AUTOINCREMENT |
 | `version` | TEXT | ❌ | Migration version | UNIQUE |
 | `applied_at` | INTEGER | ❌ | Application time | ≥ 0 |
 | `description` | TEXT | ✅ | Migration description | - |
 | `status` | TEXT | ❌ | Migration status | - | **Status Values**: `applied`, `failed`, `rolled_back`

## Database Constraints

### Foreign Key Constraints

1.**Cascading Deletes**: Used for child records that should be deleted when parent is deleted
1.**Set Null**: Used for optional relationships where null is acceptable
1.**Restrict**: Used for critical relationships that should prevent deletion

### Indexing Strategy

1.**Primary Keys**: Always indexed
1.**Foreign Keys**: Always indexed
1.**Unique Constraints**: Always indexed
1.**Frequently Queried Fields**: Indexed based on query patterns
1.**Sort/Filter Fields**: Indexed for performance

### Data Integrity Rules

1.**NOT NULL Constraints**: Enforced for required fields
1.**UNIQUE Constraints**: Enforced for unique identifiers
1.**CHECK Constraints**: Enforced for value ranges
1.**FOREIGN KEY Constraints**: Enforced for relationships
1.**DEFAULT Values**: Provided for optional fields

## Database Operations

### Transaction Management

```python
## Example transaction pattern
def with_transaction(func):
```

def wrapper(*args,**kwargs):

```python
conn = get_connection()
try:
```

conn.execute("BEGIN TRANSACTION")
result = func(*args,**kwargs)
conn.execute("COMMIT")
return result

```text
except Exception as e:
```

conn.execute("ROLLBACK")
raise DatabaseError(f"Transaction failed: {e}")

```python
```

return wrapper

```text
```

## Migration Process

1.**Backup**: Create database backup before migration
1.**Validation**: Validate current schema version
1.**Application**: Apply migration scripts in order
1.**Verification**: Verify schema changes
1.**Cleanup**: Remove temporary migration artifacts

### Schema Validation

```python
def validate_schema():
```

"""Validate database schema against specification"""
conn = get_connection()
cursor = conn.cursor()

```text

```

## Check required tables

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

## Check required columns

required_columns = {

```text
'files': ['id', 'path', 'size', 'hash', 'is_duplicate'],
'embeddings': ['id', 'file_id', 'embedding', 'model_version'],
## ... other tables
```

}

```text

```

for table, columns in required_columns.items():

```text
cursor.execute(f"PRAGMA table_info({table})")
existing_columns = {col[1] for col in cursor.fetchall()}
for col in columns:
```

if col not in existing_columns:
    raise DatabaseError(f"Missing required column: {table}.{col}")

```text
```

```text
```

## Database Performance

### Optimization Techniques

1.**Indexing**: Strategic indexing for query performance
1.**VACUUM**: Regular database vacuuming
1.**ANALYZE**: Database analysis for query planning
1.**WAL Mode**: Write-Ahead Logging for concurrency
1.**Connection Pooling**: Efficient connection management

### Maintenance Operations

```sql
-- Regular maintenance
PRAGMA optimize;
VACUUM;
ANALYZE;

-- Performance monitoring
PRAGMA cache_size = -2000;  -- 2MB cache
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
```

## Schema Evolution Policy

1.**Backward Compatibility**: All schema changes must be backward compatible
1.**Migration Path**: Provide clear migration path for existing data
1.**Deprecation**: Deprecated tables/columns supported for 2 major versions
1.**Validation**: Schema validation on startup
1.**Documentation**: All schema changes must be documented

## Example Database Initialization

```python
def initialize_database():
```

"""Initialize database with required schema"""
conn = get_connection()
cursor = conn.cursor()

```text

```

## Create tables

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (

```text
id INTEGER PRIMARY KEY AUTOINCREMENT,
path TEXT NOT NULL UNIQUE,
size INTEGER NOT NULL,
modified_time INTEGER NOT NULL,
created_time INTEGER NOT NULL,
accessed_time INTEGER,
file_type TEXT,
mime_type TEXT,
hash TEXT,
is_duplicate BOOLEAN DEFAULT FALSE,
duplicate_of INTEGER,
status TEXT DEFAULT 'active',
scanned_at INTEGER NOT NULL,
updated_at INTEGER NOT NULL,
FOREIGN KEY (duplicate_of) REFERENCES files(id) ON DELETE SET NULL
```

)
""")

```text

```

## Create indexes

cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_path ON files(path)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_size ON files(size)")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_hash ON files(hash)")

```text

```

## Initialize system info

cursor.execute("""
INSERT OR IGNORE INTO system_info (key, value, data_type, created_at, updated_at)
VALUES ('schema_version', '1.0.0', 'string', strftime('%s', 'now'), strftime('%s', 'now'))
""")

```text

```

conn.commit()

```text
```

This database schema specification ensures data integrity, performance, and compatibility across all NoDupeLabs installations.
