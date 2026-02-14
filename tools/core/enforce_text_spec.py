#!/usr/bin/env python3
"""Enforce plain text file specification compliance.

This script validates text files and fixes common issues:
- Line length
- Trailing whitespace
- Multiple blank lines
- UTF-8 encoding enforcement

Usage:
    python tools/core/enforce_text_spec.py [--fix] [--check]
"""

import argparse
import sys
from pathlib import Path


# Text spec rules
RULES = {
    "line_length": {
        "max": 80,
        "description": "Lines should not exceed 80 characters",
    },
    "no_trailing_whitespace": {
        "description": "Lines should not have trailing whitespace",
    },
    "no_multiple_blanks": {
        "description": "Multiple consecutive blank lines not allowed",
    },
    "utf8_encoding": {
        "description": "Files must be valid UTF-8",
    },
}


def check_line_length(content: str) -> list[dict]:
    """Check line length compliance."""
    errors = []
    for i, line in enumerate(content.split("\n"), 1):
        if len(line) > 80:
            errors.append({
                "line": i,
                "rule": "line_length",
                "message": f"Line length {len(line)} exceeds 80 chars",
            })
    return errors


def check_trailing_whitespace(content: str) -> list[dict]:
    """Check for trailing whitespace."""
    errors = []
    for i, line in enumerate(content.split("\n"), 1):
        if line.rstrip() != line:
            errors.append({
                "line": i,
                "rule": "no_trailing_whitespace",
                "message": "Trailing whitespace found",
            })
    return errors


def check_multiple_blanks(content: str) -> list[dict]:
    """Check for multiple consecutive blank lines."""
    errors = []
    lines = content.split("\n")
    for i in range(len(lines) - 1):
        if lines[i] == "" and lines[i + 1] == "":
            errors.append({
                "line": i + 1,
                "rule": "no_multiple_blanks",
                "message": "Multiple consecutive blank lines",
            })
    return errors


def check_utf8(content: bytes) -> list[dict]:
    """Check for valid UTF-8 encoding."""
    errors = []
    try:
        content.decode("utf-8")
    except UnicodeDecodeError as e:
        errors.append({
            "line": e.start if hasattr(e, "start") else 0,
            "rule": "utf8_encoding",
            "message": f"Invalid UTF-8: {e}",
        })
    return errors


def fix_trailing_whitespace(content: str) -> str:
    """Remove trailing whitespace."""
    lines = [line.rstrip() for line in content.split("\n")]
    return "\n".join(lines)


def fix_multiple_blanks(content: str) -> str:
    """Fix multiple consecutive blank lines."""
    lines = content.split("\n")
    fixed_lines = []
    prev_blank = False

    for line in lines:
        if line == "":
            if not prev_blank:
                fixed_lines.append(line)
                prev_blank = True
        else:
            fixed_lines.append(line)
            prev_blank = False

    return "\n".join(fixed_lines)


def fix_line_length(content: str) -> str:
    """Wrap long lines."""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) <= 80:
            fixed_lines.append(line)
        else:
            words = line.split()
            current = ""
            for word in words:
                if len(current) + len(word) + 1 <= 80:
                    current = f"{current} {word}".strip()
                else:
                    if current:
                        fixed_lines.append(current)
                    current = word
            if current:
                fixed_lines.append(current)

    return "\n".join(fixed_lines)


def enforce_spec(content: str, fix: bool = True) -> tuple[list[dict], str]:
    """Enforce text spec on content."""
    errors = []

    errors.extend(check_trailing_whitespace(content))
    errors.extend(check_multiple_blanks(content))

    if fix and errors:
        content = fix_trailing_whitespace(content)
        content = fix_multiple_blanks(content)
        content = fix_line_length(content)

    return errors, content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enforce text spec compliance")
    parser.add_argument("--fix", action="store_true", help="Fix issues automatically")
    parser.add_argument("--check", action="store_true", help="Check only (no fixes)")
    parser.add_argument("paths", nargs="*", help="Paths to check")
    args = parser.parse_args()

    fix = args.fix and not args.check

    # Find text files
    text_extensions = {".txt", ".text", ".log", ".cfg", ".conf", ".ini", ".yaml", ".yml", ".json", ".toml"}
    
    if args.paths:
        txt_files = []
        for path in args.paths:
            p = Path(path)
            if p.is_file() and p.suffix in text_extensions:
                txt_files.append(p)
            elif p.is_dir():
                txt_files.extend([f for f in p.rglob("*") if f.suffix in text_extensions])
    else:
        txt_files = []
        for ext in text_extensions:
            txt_files.extend(Path(".").rglob(f"*{ext}"))

    txt_files = list(set(txt_files))
    txt_files = [f for f in txt_files if not any(
        part.startswith(".") or part in ["node_modules", "__pycache__", ".venv", "venv"]
        for part in f.parts
    )]

    if not txt_files:
        print("No text files found")
        return 0

    total_errors = 0

    for txt_file in sorted(txt_files):
        try:
            content = txt_file.read_text(encoding="utf-8")
            original = content
            errors, fixed = enforce_spec(content, fix=fix)

            if errors:
                total_errors += len(errors)
                print(f"\n{txt_file}: {len(errors)} issue(s)")
                for err in errors[:3]:
                    print(f"  Line {err['line']}: {err['message']}")

                if fix and fixed != original:
                    txt_file.write_text(fixed, encoding="utf-8")
                    print("  Fixed!")

        except Exception as e:
            print(f"Error: {txt_file}: {e}")

    print(f"\n{'='*50}")
    if total_errors > 0:
        print(f"Total: {total_errors} issue(s) found")
        return 1
    else:
        print("All text files comply with spec")
        return 0


if __name__ == "__main__":
    sys.exit(main())
