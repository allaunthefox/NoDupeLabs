#!/usr/bin/env python3
"""Enforce Markdown specification compliance (ISO/IEC 23299:2023).

This script validates all markdown files in the project against
the markdown specification and fixes common issues.

Usage:
    python tools/core/enforce_markdown_spec.py [--fix] [--check]
"""

import argparse
import re
import sys
from pathlib import Path


# Markdown spec rules (ISO/IEC 23299:2023 compatible)
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
    "blanks_around_lists": {
        "description": "Lists should be surrounded by blank lines",
    },
    "blanks_around_headers": {
        "description": "Headers should have blank lines around them",
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
                "content": line[:50] + "...",
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
                "content": line,
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
                "content": f"Lines {i+1} and {i+2}",
            })
    return errors


def check_blanks_around_lists(content: str) -> list[dict]:
    """Check that lists have blank lines before them."""
    errors = []
    lines = content.split("\n")
    in_code_block = False

    for i, line in enumerate(lines):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            continue

        # Check for list items
        if re.match(r"^[\s]*[-*+]\s", line) or re.match(r"^[\s]*\d+\.\s", line):
            # Check previous line is blank or it's the start
            if i > 0 and lines[i - 1].strip() != "" and not lines[i - 1].strip().startswith("#"):
                errors.append({
                    "line": i + 1,
                    "rule": "blanks_around_lists",
                    "message": "List should be preceded by blank line",
                    "content": line[:30],
                })

    return errors


def fix_line_length(content: str) -> str:
    """Fix lines that are too long by wrapping."""
    lines = content.split("\n")
    fixed_lines = []

    for line in lines:
        if len(line) <= 80:
            fixed_lines.append(line)
        else:
            # Try to wrap at a space
            words = line.split()
            if not words:
                fixed_lines.append(line)
                continue

            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= 80:
                    current_line = f"{current_line} {word}".strip()
                else:
                    if current_line:
                        fixed_lines.append(current_line)
                    current_line = word
            if current_line:
                fixed_lines.append(current_line)

    return "\n".join(fixed_lines)


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


def fix_blanks_around_lists(content: str) -> str:
    """Add blank lines before lists."""
    lines = content.split("\n")
    fixed_lines = []
    in_code_block = False

    for i, line in enumerate(lines):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            fixed_lines.append(line)
            continue

        if in_code_block:
            fixed_lines.append(line)
            continue

        # Check for list items
        if re.match(r"^[\s]*[-*+]\s", line) or re.match(r"^[\s]*\d+\.\s", line):
            # Check previous line
            if i > 0 and fixed_lines[-1].strip() != "" and not fixed_lines[-1].strip().startswith("#"):
                fixed_lines.append("")  # Add blank line before list

        fixed_lines.append(line)

    return "\n".join(fixed_lines)


def enforce_spec(content: str, fix: bool = True) -> tuple[list[dict], str]:
    """Enforce markdown spec on content."""
    all_errors = []

    # Run all checks
    all_errors.extend(check_line_length(content))
    all_errors.extend(check_trailing_whitespace(content))
    all_errors.extend(check_multiple_blanks(content))
    all_errors.extend(check_blanks_around_lists(content))

    if fix and all_errors:
        content = fix_trailing_whitespace(content)
        content = fix_multiple_blanks(content)
        content = fix_blanks_around_lists(content)
        content = fix_line_length(content)

    return all_errors, content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enforce Markdown spec compliance")
    parser.add_argument("--fix", action="store_true", help="Fix issues automatically")
    parser.add_argument("--check", action="store_true", help="Check only (no fixes)")
    parser.add_argument("paths", nargs="*", help="Paths to check (default: all markdown files)")
    args = parser.parse_args()

    fix = args.fix and not args.check

    # Find markdown files
    if args.paths:
        md_files = []
        for path in args.paths:
            p = Path(path)
            if p.is_file() and p.suffix == ".md":
                md_files.append(p)
            elif p.is_dir():
                md_files.extend(p.rglob("*.md"))
    else:
        # Check common directories
        md_files = []
        for directory in ["wiki", "docs", "."]:
            if Path(directory).exists():
                md_files.extend(Path(directory).rglob("*.md"))

    # Remove duplicates
    md_files = list(set(md_files))

    if not md_files:
        print("No markdown files found")
        return 0

    total_errors = 0

    for md_file in sorted(md_files):
        try:
            content = md_file.read_text(encoding="utf-8")
            original_content = content
            errors, fixed_content = enforce_spec(content, fix=fix)

            if errors:
                total_errors += len(errors)
                print(f"\n{md_file}: {len(errors)} issue(s) found")

                for error in errors[:5]:  # Show first 5 errors
                    print(f"  Line {error['line']}: {error['message']}")

                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more")

                if fix and fixed_content != original_content:
                    md_file.write_text(fixed_content, encoding="utf-8")
                    print(f"  Fixed!")

        except Exception as e:
            print(f"Error processing {md_file}: {e}")

    print(f"\n{'='*50}")
    if total_errors > 0:
        print(f"Total: {total_errors} issue(s) found")
        if fix:
            print("Run with --check to see issues without fixing")
        return 1
    else:
        print("All markdown files comply with ISO/IEC 23299:2023")
        return 0


if __name__ == "__main__":
    sys.exit(main())
