# Archive Format Support Research

## Python Standard Library Archive Support

This document provides comprehensive research on archive formats supported by Python's standard library modules.

### ZIP Archive Support (zipfile module)

**Module**: `zipfile`
**Supported Formats**:
- `.zip` - Standard ZIP archive format
- `.zipx` - Extended ZIP format (with additional compression methods)

**Compression Methods**:
- `ZIP_STORED` (0) - No compression
- `ZIP_DEFLATED` (8) - DEFLATE compression (most common)
- `ZIP_BZIP2` (12) - BZIP2 compression (if available)
- `ZIP_LZMA` (14) - LZMA compression (if available)

**Features**:
- Read and write ZIP archives
- Support for PASSWORD_REMOVED-protected ZIP files
- Support for multi-volume ZIP files
- Support for ZIP64 extensions (large files > 4GB)

**File Extensions**: `.zip`, `.zipx`

### TAR Archive Support (tarfile module)

**Module**: `tarfile`
**Supported Formats**:
- `.tar` - Uncompressed TAR archive
- `.tar.gz` - Gzip-compressed TAR archive
- `.tgz` - Alternative extension for gzip-compressed TAR
- `.tar.bz2` - Bzip2-compressed TAR archive
- `.tbz2` - Alternative extension for bzip2-compressed TAR
- `.tar.xz` - XZ-compressed TAR archive
- `.txz` - Alternative extension for XZ-compressed TAR
- `.tar.lzma` - LZMA-compressed TAR archive

**Compression Methods**:
- No compression (standard TAR)
- Gzip compression (`.gz`, `.tgz`)
- Bzip2 compression (`.bz2`, `.tbz2`)
- XZ compression (`.xz`, `.txz`)
- LZMA compression (`.lzma`)

**Features**:
- Read and write TAR archives
- Support for various compression algorithms
- Support for POSIX, GNU, and other TAR formats
- Support for sparse files
- Support for incremental backups
- Support for long filenames and large files

**File Extensions**: `.tar`, `.tar.gz`, `.tgz`, `.tar.bz2`, `.tbz2`, `.tar.xz`, `.txz`, `.tar.lzma`

### Compression Formats Supported by Standard Library

**Gzip Compression**:
- Module: `gzip`
- File extensions: `.gz`, `.tgz`
- Uses DEFLATE algorithm

**Bzip2 Compression**:
- Module: `bz2`
- File extensions: `.bz2`, `.tbz2`
- Uses Burrows-Wheeler transform

**LZMA/XZ Compression**:
- Module: `lzma`
- File extensions: `.xz`, `.txz`, `.lzma`
- Uses Lempel-Ziv-Markov chain algorithm

### Archive Formats NOT Supported by Standard Library

The following popular archive formats are **NOT** supported by Python's standard library and require third-party modules:

- `.rar` - RAR archive format (requires `rarfile` or `patool`)
- `.7z` - 7-Zip archive format (requires `py7zr` or `patool`)
- `.cab` - Cabinet archive format (requires third-party modules)
- `.iso` - ISO disk image format (requires `pycdlib` or similar)
- `.dmg` - Apple Disk Image format (requires third-party modules)
- `.ar` - Unix archive format (requires third-party modules)
- `.cpio` - CPIO archive format (requires third-party modules)

### Summary of Supported Archive Formats

| Format | Module | Compression | Read | Write | Notes |
|--------|--------|-------------|------|-------|-------|
| `.zip` | zipfile | DEFLATE | ✅ | ✅ | Standard ZIP format |
| `.zip` | zipfile | STORED | ✅ | ✅ | Uncompressed ZIP |
| `.zip` | zipfile | BZIP2 | ❌ | ❌ | Requires external support |
| `.zip` | zipfile | LZMA | ❌ | ❌ | Requires external support |
| `.tar` | tarfile | None | ✅ | ✅ | Uncompressed TAR |
| `.tar.gz` | tarfile | Gzip | ✅ | ✅ | Gzip-compressed TAR |
| `.tgz` | tarfile | Gzip | ✅ | ✅ | Alternative extension |
| `.tar.bz2` | tarfile | Bzip2 | ✅ | ✅ | Bzip2-compressed TAR |
| `.tbz2` | tarfile | Bzip2 | ✅ | ✅ | Alternative extension |
| `.tar.xz` | tarfile | XZ | ✅ | ✅ | XZ-compressed TAR |
| `.txz` | tarfile | XZ | ✅ | ✅ | Alternative extension |
| `.tar.lzma` | tarfile | LZMA | ✅ | ✅ | LZMA-compressed TAR |

### Implementation Notes for NoDupeLabs Archive Support

The current NoDupeLabs archive handler supports:

**ZIP Archives**:
- ✅ Standard ZIP files (`.zip`)
- ✅ DEFLATE compression (most common)
- ✅ Uncompressed ZIP files

**TAR Archives**:
- ✅ Uncompressed TAR (`.tar`)
- ✅ Gzip-compressed TAR (`.tar.gz`, `.tgz`)
- ✅ Bzip2-compressed TAR (`.tar.bz2`, `.tbz2`)
- ✅ XZ-compressed TAR (`.tar.xz`, `.txz`)

**Detection Methods**:
- File extension detection
- MIME type detection using magic numbers
- Fallback to manual format detection

**Limitations**:
- No support for PASSWORD_REMOVED-protected archives
- No support for multi-volume archives
- No support for RAR, 7Z, or other proprietary formats
- Limited to standard library capabilities (no external dependencies)

### Recommendations for Future Enhancement

1. **Add RAR Support**: Consider adding `rarfile` module for RAR archive support
2. **Add 7Z Support**: Consider adding `py7zr` module for 7-Zip archive support
3. **Password Protection**: Add support for PASSWORD_REMOVED-protected ZIP archives
4. **Multi-volume Archives**: Add support for split/multi-volume archives
5. **Performance Optimization**: Add caching for frequently accessed archives
6. **Memory Management**: Add streaming support for large archives to reduce memory usage
