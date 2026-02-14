#!/usr/bin/env python3
"""Enforce license headers in source files.

This script ensures all source files have proper copyright headers.

Usage:
    python tools/core/enforce_license.py [--fix] [--check]
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path


# Default license template
DEFAULT_LICENSE = """\
# Copyright {year} NoDupeLabs. All rights reserved.
# Licensed under the MIT License.
"""

# File extensions that need license headers
LICENSE_EXTENSIONS = {
    ".py": DEFAULT_LICENSE,
    ".js": "# " + DEFAULT_LICENSE.replace("\n", "\n# "),
    ".ts": "# " + DEFAULT_LICENSE.replace("\n", "\n# "),
    ".java": "/* " + DEFAULT_LICENSE.replace("\n", "\n * ") + "\n */",
    ".c": "/* " + DEFAULT_LICENSE.replace("\n", "\n * ") + "\n */",
    ".cpp": "/* " + DEFAULT_LICENSE.replace("\n", "\n * ") + "\n */",
    ".h": "/* " + DEFAULT_LICENSE.replace("\n", "\n * ") + "\n */",
    ".go": "// " + DEFAULT_LICENSE.replace("\n", "\n// "),
    ".rs": "// " + DEFAULT_LICENSE.replace("\n", "\n// "),
    ".swift": "// " + DEFAULT_LICENSE.replace("\n", "\n// "),
}

# Patterns that indicate a file already has a license
LICENSE_PATTERNS = [
    r"Copyright\s+\d{4}",
    r"SPDX-License-Identifier",
    r"MIT License",
    r"Apache License",
    r"GNU General Public License",
    r"All rights reserved",
]


def has_license(content: str) -> bool:
    """Check if file already has a license header."""
    # Check first 500 chars (license is usually at the top)
    header = content[:500]
    for pattern in LICENSE_PATTERNS:
        if re.search(pattern, header, re.IGNORECASE):
            return True
    return False


def get_license_header(file_type: str) -> str:
    """Get the appropriate license header for file type."""
    year = datetime.now().year
    template = LICENSE_EXTENSIONS.get(file_type, DEFAULT_LICENSE)
    return template.format(year=year)


def check_file(path: Path) -> dict:
    """Check if a file has a proper license header."""
    try:
        content = path.read_text(encoding="utf-8")

        if not has_license(content):
            return {
                "path": path,
                "has_license": False,
                "error": "Missing license header",
            }

        return {"path": path, "has_license": True}

    except Exception as e:
        return {"path": path, "has_license": False, "error": str(e)}


def fix_file(path: Path) -> bool:
    """Add license header to a file."""
    try:
        content = path.read_text(encoding="utf-8")

        if has_license(content):
            return True  # Already has license

        # Get file extension
        ext = path.suffix
        license_header = get_license_header(ext)

        # Add license header
        new_content = license_header + "\n\n" + content
        path.write_text(new_content, encoding="utf-8")
        return True

    except Exception as e:
        print(f"Error fixing {path}: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enforce license headers")
    parser.add_argument("--fix", action="store_true", help="Fix missing licenses")
    parser.add_argument("--check", action="store_true", help="Check only")
    parser.add_argument("paths", nargs="*", help="Files to check")
    args = parser.parse_args()

    fix = args.fix and not args.check

    if args.paths:
        files = []
        for path in args.paths:
            p = Path(path)
            if p.is_file() and p.suffix in LICENSE_EXTENSIONS:
                files.append(p)
            elif p.is_dir():
                files.extend([f for f in p.rglob("*") if f.suffix in LICENSE_EXTENSIONS])
    else:
        # Check common source directories
        files = []
        for directory in ["nodupe", "tests", "tools", "scripts"]:
            if Path(directory).exists():
                files.extend([f for f in Path(directory).rglob("*") if f.suffix in LICENSE_EXTENSIONS])

    files = list(set(files))

    if not files:
        print("No files found that require license headers")
        return 0

    missing = 0

    for file in sorted(files):
        result = check_file(file)

        if not result["has_license"]:
            missing += 1
            print(f"\n{file}: {result.get('error', 'Missing license')}")

            if fix:
                if fix_file(file):
                    print("  Fixed!")

    print(f"\n{'='*50}")
    if missing > 0:
        print(f"Total: {missing} file(s) missing license headers")
        if fix:
            print("Run with --check to see issues without fixing")
        return 1
    else:
        print("All files have proper license headers")
        return 0


if __name__ == "__main__":
    sys.exit(main())
