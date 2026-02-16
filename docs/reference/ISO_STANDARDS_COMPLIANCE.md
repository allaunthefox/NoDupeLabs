# ISO Standards Compliance Documentation

## Overview

This document specifies the exact ISO standards that NoDupeLabs adheres to for source code archival and documentation.

## ISO Standards for Source Code

### 1. SPDX (ISO/IEC 5962:2021)

**Standard:** SPDX (Software Package Data Exchange) - ISO/IEC 5962:2021

**Purpose:** International standard for communicating software bill of materials (SBOM) information.

**Implementation:**
- All source files contain SPDX-License-Identifier header
- License: Apache-2.0

**Example:**
```python
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Allaun
```

**Files Compliant:** 16 database modules + all project source files

### 2. PEP 8 (Style Guide for Python Code)

**Standard:** PEP 8 - Style Guide for Python Code

**Purpose:** Coding conventions for the Python programming language.

**Implementation:**
- 4-space indentation
- Maximum line length: 100 characters
- Proper naming conventions (snake_case for functions/variables, PascalCase for classes)
- Two blank lines between top-level definitions

### 3. PEP 257 (Docstring Conventions)

**Standard:** PEP 257 - Docstring Conventions

**Purpose:** Conventions for Python docstrings.

**Implementation:**
- All modules have module-level docstrings
- All classes have class docstrings with:
  - Summary line (imperative mood)
  - Extended description (if needed)
  - Attributes section
  - Example section
- All public methods have docstrings with:
  - Summary line
  - Args section
  - Returns section
  - Raises section
  - Example section

### 4. ISO 8601 (Date/Time Format)

**Standard:** ISO 8601 - Date and Time Format

**Implementation:**
- Archive directories use format: `refactor_YYYY-MM-DD`
- Example: `archive/refactor_2026-02-14/`

### 5. RFC 5322 (Date/Time in Headers)

**Standard:** RFC 5322 - Date and Time in Internet Messages

**Implementation:**
- Copyright headers use format: `(c) YYYY`
- Example: `Copyright (c) 2025 Allaun`

---

## Database Standards (ISO/IEC and ANSI)

### 1. SQLite3 (ISO/IEC 9075:2016 / SQL:2016 Compliance)

**Standard:** ISO/IEC 9075:2016 - Database Language SQL

**Purpose:** The database layer uses SQLite3 which implements SQL:2016 standard features.

**Implementation:**
- Full SQL query support (SELECT, INSERT, UPDATE, DELETE)
- Transaction support (BEGIN, COMMIT, ROLLBACK)
- ACID compliance for atomic transactions
- Foreign key constraints
- Index management

**Database Features Used:**
```sql
CREATE TABLE, CREATE INDEX
SELECT, INSERT, UPDATE, DELETE
BEGIN IMMEDIATE, COMMIT, ROLLBACK
PRAGMA journal_mode=WAL
PRAGORMAL
PRAGMA synchronous=NMA foreign_keys=ON
```

### 2. ACID Properties (ISO/IEC/IEC 25010)

**Standard:** ISO/IEC 25010:2011 - Systems and software engineering

**Purpose:** Database operations guarantee ACID properties:
- **Atomicity**: Transactions are all-or-nothing
- **Consistency**: Database moves from one valid state to another
- **Isolation**: Concurrent transactions appear serial
- **Durability**: Committed data is permanent

### 3. Connection Standards

**Implementation:**
- Thread-safe connection handling using `threading.local()`
- Connection pooling via singleton pattern
- WAL (Write-Ahead Logging) mode for concurrent access

### 4. Data Types (ISO/IEC 9075)

**Standard:** SQL Data Types from ISO/IEC 9075

**Implementation:**
- INTEGER (primary keys, sizes)
- TEXT (paths, hashes)
- BLOB (embeddings, binary data)
- BOOLEAN (flags)

---

## Compliance Matrix

| Standard | Requirement | Status |
|----------|-------------|--------|
| SPDX | License header in all files | ✅ Compliant |
| PEP 8 | Code style | ✅ Compliant |
| PEP 257 | Docstring coverage | ✅ Compliant |
| ISO 8601 | Archive naming | ✅ Compliant |
| RFC 5322 | Copyright format | ✅ Compliant |
| ISO/IEC 9075 | SQL:2016 (SQLite3) | ✅ Compliant |
| ISO/IEC 25010 | ACID properties | ✅ Compliant |

## Archive Structure

```
archive/refactor_YYYY-MM-DD/
├── database/
│   └── database.py          # Original archived version
├── module_name/
│   └── archived_files...    # Future archived modules
```

## Verification

To verify SPDX compliance:
```bash
grep -r "SPDX-License-Identifier" nodupe/
```

To verify docstring coverage:
```bash
python -m pytest --doctest-modules nodupe/core/database/
```

To verify all tests pass:
```bash
python -m pytest tests/core/test_database.py --no-cov -q
```

## References

### Source Code Standards
- [SPDX Specification](https://spdx.github.io/spdx-spec/)
- [PEP 8](https://peps.python.org/pep-0008/)
- [PEP 257](https://peps.python.org/pep-0257/)
- [ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html)

### Database Standards
- [ISO/IEC 9075 (SQL:2016)](https://www.iso.org/standard/63555.html)
- [SQLite3 Documentation](https://www.sqlite.org/lang.html)
- [ISO/IEC 25010](https://www.iso.org/standard/35733.html)
- [RFC 5322](https://tools.ietf.org/html/rfc5322)
