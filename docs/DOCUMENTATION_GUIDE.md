# NoDupeLabs Documentation Guide

This guide provides comprehensive, reproducible documentation standards and examples for the NoDupeLabs project.

## Table of Contents

- [Documentation Philosophy](#documentation-philosophy)
- [Documentation Structure](#documentation-structure)
- [Writing Style Guide](#writing-style-guide)
- [Module Documentation](#module-documentation)
- [Function/Method Documentation](#functionmethod-documentation)
- [Class Documentation](#class-documentation)
- [Command Documentation](#command-documentation)
- [Example Documentation](#example-documentation)
- [Documentation Tools](#documentation-tools)
- [Documentation Review Process](#documentation-review-process)

## Documentation Philosophy

**Clear, Reproducible, and Maintainable**

NoDupeLabs documentation follows these principles:

1. **Clarity**: Documentation should be easy to understand for both beginners and experienced users
2. **Reproducibility**: Examples should be complete and work as shown
3. **Completeness**: All public APIs should be fully documented
4. **Consistency**: Follow established patterns and styles
5. **Maintainability**: Keep documentation up-to-date with code changes

## Documentation Structure

```
docs/
├── BEGINNERS_GUIDE.md          # Getting started guide
├── ARCHITECTURE.md             # System architecture
├── CONTRIBUTING.md             # Contribution guidelines
├── DOCUMENTATION_GUIDE.md      # This file
├── DOCUMENTATION_TODO.md       # Documentation roadmap
├── CHANGELOG.md                # Version history
├── SIMILARITY.md               # Similarity features
├── AI_BACKEND.md               # AI backend documentation
├── adr/                        # Architecture Decision Records
└── sphinx/                     # API documentation
```

## Writing Style Guide

### Language and Tone

- **Use clear, concise language**
- **Write in active voice**
- **Use present tense** for documentation
- **Be specific** rather than vague
- **Use code examples** liberally
- **Follow Markdown conventions**

### Formatting Guidelines

- **Headings**: Use consistent heading hierarchy
- **Lists**: Use bullet points for unordered lists, numbers for steps
- **Code blocks**: Use triple backticks with language specification
- **Links**: Use descriptive link text
- **Images**: Include alt text and captions

### Code Examples

```markdown
```python
# Good example - complete and reproducible
def calculate_hash(file_path: str) -> str:
    """Calculate file hash."""
    import hashlib
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()
```

```python
# Bad example - incomplete and not reproducible
def calculate_hash(file_path):
    # Calculate hash...
    pass
```

## Module Documentation

Every module must have a comprehensive docstring at the top:

```python
"""Brief one-line summary (50-70 characters).

Detailed description explaining the module's purpose, key concepts,
and architecture. Use multiple paragraphs if needed.

Key Features:
    - Feature 1: Brief description
    - Feature 2: Brief description
    - Feature 3: Brief description

Dependencies:
    - Required: dependency1, dependency2
    - Optional: dependency3 (falls back to X)

Usage Example:
    >>> from nodupe.module import function
    >>> result = function(arg1, arg2)
    >>> print(result)
"""
```

## Function/Method Documentation

Every public function and method must have complete docstrings:

```python
def process_file(file_path: str, hash_algo: str = "sha512") -> dict:
    """Process a single file and return metadata.

    This function reads the file, calculates its hash, determines its
    MIME type, and returns a dictionary with all metadata. It handles
    various file types and includes error handling for common issues.

    Args:
        file_path: Path to the file to process
        hash_algo: Hashing algorithm to use (default: "sha512")

    Returns:
        Dictionary containing file metadata with keys:
        - path: File path
        - size: File size in bytes
        - hash: File hash
        - mime: MIME type
        - category: File category

    Raises:
        FileNotFoundError: If the file doesn't exist
        PermissionError: If the file can't be read
        ValueError: If the hash algorithm is invalid

    Example:
        >>> metadata = process_file("/path/to/file.txt")
        >>> print(metadata["hash"])
        "a1b2c3d4e5f6..."
    """
```

## Class Documentation

Every class must have comprehensive docstrings:

```python
class FileProcessor:
    """Process files and extract metadata.

    This class handles file processing, including hashing, MIME type
    detection, and metadata extraction. It supports various file types
    and provides methods for batch processing.

    Attributes:
        hash_algo: Hashing algorithm to use
        mime_detector: MIME type detection instance
        processed_count: Number of files processed

    Example:
        >>> processor = FileProcessor("sha512")
        >>> metadata = processor.process("/path/to/file.txt")
    """

    def __init__(self, hash_algo: str = "sha512"):
        """Initialize the file processor.

        Args:
            hash_algo: Hashing algorithm to use (default: "sha512")
        """
        self.hash_algo = hash_algo
        self.mime_detector = MIMEDetector()
        self.processed_count = 0
```

## Command Documentation

Command documentation should include:

1. **Brief description** of what the command does
2. **Usage examples** with common options
3. **Parameter descriptions** in a table format
4. **Output description** and examples
5. **Common use cases**

```markdown
## `scan` Command

Scans directories recursively and populates the database with file metadata.

### Usage

```bash
# Basic scan
nodupe scan --root /path/to/directory

# Scan multiple directories
nodupe scan --root /path/to/photos --root /path/to/documents

# Scan with custom settings
nodupe scan --root /data --parallelism 4 --hash-algo sha256
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--root` | Directory to scan (can be specified multiple times) | Required |
| `--parallelism` | Number of worker threads | Auto-detect |
| `--hash-algo` | Hashing algorithm (sha512, sha256, blake2b) | sha512 |
| `--ignore-patterns` | File patterns to ignore | [".git", "node_modules"] |
| `--verbose` | Enable verbose output | False |

### Output

- Creates or updates `output/index.db` SQLite database
- Generates `meta.json` files in each scanned directory
- Logs progress to `output/logs/scan.log`

### Examples

**Basic scan:**
```bash
nodupe scan --root ~/Documents
```

**Scan with custom hash algorithm:**
```bash
nodupe scan --root /data --hash-algo blake2b
```

**Scan with increased parallelism:**
```bash
nodupe scan --root /large/dataset --parallelism 8
```
```

## Example Documentation

### Good Example

```python
"""File scanning and metadata extraction.

This module provides comprehensive file scanning capabilities,
including recursive directory traversal, content hashing,
MIME type detection, and metadata extraction. It supports
incremental scanning to avoid reprocessing unchanged files.

Key Features:
    - Recursive directory scanning
    - Multiple hash algorithms (SHA-512, SHA-256, BLAKE2b)
    - Incremental scanning with change detection
    - Parallel processing for performance
    - Comprehensive error handling

Dependencies:
    - Required: hashlib, pathlib, threading
    - Optional: xxhash (for BLAKE2b support)

Example:
    >>> from nodupe.scan import Scanner
    >>> scanner = Scanner(hash_algo="sha512")
    >>> results = scanner.scan("/path/to/directory")
    >>> print(f"Processed {len(results)} files")
"""

def scan_directory(root_path: str, hash_algo: str = "sha512") -> list:
    """Scan a directory and return file metadata.

    Recursively scans the directory, processes each file,
    and returns a list of metadata dictionaries.

    Args:
        root_path: Path to the directory to scan
        hash_algo: Hashing algorithm to use

    Returns:
        List of metadata dictionaries

    Raises:
        NotADirectoryError: If root_path is not a directory
        PermissionError: If directory can't be read

    Example:
        >>> metadata = scan_directory("/path/to/photos")
        >>> for file in metadata:
        ...     print(file["path"], file["hash"])
    """
```

### Bad Example

```python
# Bad - no module docstring
# No explanation of purpose or usage

def scan_dir(path):
    # Bad - incomplete docstring
    # scan a directory
    pass
```

## Documentation Tools

### Sphinx

NoDupeLabs uses Sphinx for API documentation:

```bash
# Build HTML documentation
cd docs/sphinx
make html

# View documentation
open _build/html/index.html
```

### Docstring Coverage

Use Interrogate to check docstring coverage:

```bash
# Check coverage
interrogate -vv nodupe/ --fail-under 100

# Generate coverage report
interrogate -vv nodupe/ --html-report docs/coverage
```

### Markdown Linting

Use Markdownlint to check Markdown files:

```bash
# Install markdownlint
npm install -g markdownlint-cli

# Check Markdown files
markdownlint docs/**/*.md
```

## Documentation Review Process

### Self-Review Checklist

Before submitting documentation:

- [ ] Module has comprehensive docstring
- [ ] All public functions/methods have complete docstrings
- [ ] All classes have docstrings
- [ ] Examples are complete and reproducible
- [ ] Code examples follow project style
- [ ] No broken links or references
- [ ] Consistent formatting and style
- [ ] Spelling and grammar checked

### Peer Review Guidelines

When reviewing documentation:

1. **Check completeness**: Are all public APIs documented?
2. **Verify accuracy**: Do examples work as shown?
3. **Assess clarity**: Is the documentation easy to understand?
4. **Test reproducibility**: Can you follow the examples?
5. **Check consistency**: Does it follow established patterns?
6. **Validate style**: Does it follow the style guide?

### Documentation Update Process

1. **Identify changes**: What needs to be documented?
2. **Write draft**: Create initial documentation
3. **Self-review**: Check against the checklist
4. **Test examples**: Ensure they work correctly
5. **Peer review**: Get feedback from others
6. **Finalize**: Incorporate feedback and finalize
7. **Update**: Commit and push changes

## Best Practices

### Keep Documentation Current

- Update documentation when making code changes
- Add documentation for new features
- Remove documentation for deprecated features
- Review documentation regularly

### Write for Different Audiences

- **Beginners**: Provide clear, step-by-step instructions
- **Intermediate users**: Include practical examples
- **Advanced users**: Document advanced features and customization
- **Developers**: Provide API documentation and architecture details

### Use Consistent Terminology

- Use the same terms throughout documentation
- Define terms in a glossary if needed
- Avoid jargon or explain it when used

### Provide Context

- Explain why something works the way it does
- Include background information when helpful
- Link to related documentation

## Documentation Maintenance

### Regular Reviews

- Review documentation quarterly
- Update examples to reflect current best practices
- Remove outdated or incorrect information
- Add missing documentation

### Version-Specific Documentation

- Document breaking changes clearly
- Provide migration guides when needed
- Maintain documentation for major versions

### Community Contributions

- Encourage community documentation contributions
- Provide clear contribution guidelines
- Review and merge documentation improvements
- Credit contributors appropriately

## Resources

- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)
- [Markdown Guide](https://www.markdownguide.org/)
- [Write the Docs](https://www.writethedocs.org/)
- [Diátaxis Documentation Framework](https://diataxis.fr/)

## Conclusion

High-quality documentation is essential for the success and adoption of NoDupeLabs. By following these guidelines and maintaining consistent, clear, and reproducible documentation, we ensure that users can effectively use and contribute to the project.

**Remember**: Documentation is as important as code. Treat it with the same care and attention to quality.
