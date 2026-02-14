#!/usr/bin/env python3
"""Enforce TOML specification compliance.

This script validates TOML files for spec compliance:
- Valid TOML syntax
- Trailing whitespace

Usage:
    python tools/core/enforce_toml_spec.py [--fix] [--check]
"""

import argparse
import sys
from pathlib import Path


def check_toml_syntax(content: str) -> list[dict]:
    """Check TOML syntax validity."""
    errors = []
    try:
        import tomllib
        tomllib.loads(content)
    except Exception as e:
        errors.append({
            "line": 1,
            "rule": "toml-syntax",
            "message": f"TOML error: {e}",
        })
    return errors


def check_trailing_whitespace(content: str) -> list[dict]:
    """Check for trailing whitespace."""
    errors = []
    for i, line in enumerate(content.split("\n"), 1):
        if line.rstrip() != line:
            errors.append({
                "line": i,
                "rule": "trailing-whitespace",
                "message": "Trailing whitespace found",
            })
    return errors


def check_multiple_blanks(content: str) -> list[dict]:
    """Check for multiple blank lines."""
    errors = []
    lines = content.split("\n")
    for i in range(len(lines) - 1):
        if lines[i] == "" and lines[i + 1] == "":
            errors.append({
                "line": i + 1,
                "rule": "multiple-blanks",
                "message": "Multiple consecutive blank lines",
            })
    return errors


def fix_trailing_whitespace(content: str) -> str:
    """Fix trailing whitespace."""
    return "\n".join(line.rstrip() for line in content.split("\n"))


def fix_multiple_blanks(content: str) -> str:
    """Fix multiple blank lines."""
    lines = content.split("\n")
    fixed = []
    prev_blank = False
    for line in lines:
        if line == "":
            if not prev_blank:
                fixed.append(line)
                prev_blank = True
        else:
            fixed.append(line)
            prev_blank = False
    return "\n".join(fixed)


def enforce_spec(content: str, fix: bool = True) -> tuple[list[dict], str]:
    """Enforce TOML spec."""
    errors = []
    errors.extend(check_toml_syntax(content))
    errors.extend(check_trailing_whitespace(content))
    errors.extend(check_multiple_blanks(content))

    if fix and errors:
        content = fix_trailing_whitespace(content)
        content = fix_multiple_blanks(content)

    return errors, content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enforce TOML spec")
    parser.add_argument("--fix", action="store_true", help="Fix issues")
    parser.add_argument("--check", action="store_true", help="Check only")
    parser.add_argument("paths", nargs="*", help="Files to check")
    args = parser.parse_args()

    fix = args.fix and not args.check

    if args.paths:
        files = []
        for path in args.paths:
            p = Path(path)
            if p.is_file() and p.suffix == ".toml":
                files.append(p)
            elif p.is_dir():
                files.extend(p.rglob("*.toml"))
    else:
        files = list(Path(".").rglob("*.toml"))

    files = list(set([f for f in files if not any(x in f.parts for x in [".venv", "venv", "__pycache__"])]))

    if not files:
        print("No TOML files found")
        return 0

    total_errors = 0

    for f in sorted(files):
        try:
            content = f.read_text(encoding="utf-8")
            original = content
            errors, fixed = enforce_spec(content, fix=fix)

            if errors:
                total_errors += len(errors)
                print(f"\n{f}: {len(errors)} issue(s)")
                for err in errors[:3]:
                    print(f"  Line {err['line']}: {err['message']}")

                if fix and fixed != original:
                    f.write_text(fixed, encoding="utf-8")
                    print("  Fixed!")

        except Exception as e:
            print(f"Error: {f}: {e}")

    print(f"\n{'='*50}")
    if total_errors > 0:
        print(f"Total: {total_errors} issue(s) found")
        return 1
    else:
        print("All TOML files comply with spec")
        return 0


if __name__ == "__main__":
    sys.exit(main())
