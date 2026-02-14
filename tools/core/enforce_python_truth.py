#!/usr/bin/env python3
"""Enforce Python truthiness best practices.

This script checks for common Python anti-patterns:
- Using `== True` instead of `if x:`
- Using `== False` instead of `if not x:`
- Using `is None` instead of `if x is None:`
- Using `is not None` instead of `if x is not None:`

Usage:
    python tools/core/enforce_python_truth.py [--fix] [--check] [paths]
"""

import argparse
import ast
import sys
from pathlib import Path


class TruthinessChecker(ast.NodeVisitor):
    """Check for truthiness anti-patterns."""

    def __init__(self):
        self.errors = []

    def visit_Compare(self, node: ast.Compare):
        # Check for == True / == False
        if isinstance(node.ops[0], ast.Eq):
            if isinstance(node.left, ast.Constant):
                if node.left.value is True:
                    self.errors.append({
                        "line": node.lineno,
                        "rule": "truthy-comparison",
                        "message": "Use 'if x:' instead of 'if x == True:'",
                    })
                elif node.left.value is False:
                    self.errors.append({
                        "line": node.lineno,
                        "rule": "falsy-comparison",
                        "message": "Use 'if not x:' instead of 'if x == False:'",
                    })

        # Check for `if x == None:` or `if x != None:`
        if isinstance(node.ops[0], (ast.Eq, ast.NotEq)):
            if isinstance(node.left, ast.Constant) and node.left.value is None:
                self.errors.append({
                    "line": node.lineno,
                    "rule": "none-comparison",
                    "message": "Use 'if x is None:' instead of 'if x == None:'",
                })
            elif len(node.comparators) == 1:
                comp = node.comparators[0]
                if isinstance(comp, ast.Constant) and comp.value is None:
                    op = "==" if isinstance(node.ops[0], ast.Eq) else "!="
                    self.errors.append({
                        "line": node.lineno,
                        "rule": "none-comparison",
                        "message": f"Use 'if x is {op.replace('==', 'not')} None:'",
                    })

        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        # Check for `if x == True:`
        if isinstance(node.test, ast.Compare):
            if isinstance(node.test.ops[0], ast.Eq):
                if isinstance(node.test.left, ast.Constant) and node.test.left.value is True:
                    self.errors.append({
                        "line": node.lineno,
                        "rule": "truthy-comparison",
                        "message": "Use 'if x:' instead of 'if x == True:'",
                    })

        self.generic_visit(node)


def check_file(path: Path) -> list[dict]:
    """Check a Python file for truthiness issues."""
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
        checker = TruthinessChecker()
        checker.visit(tree)
        return checker.errors
    except SyntaxError as e:
        return [{"line": e.lineno or 0, "rule": "syntax", "message": f"Syntax error: {e}"}]
    except Exception as e:
        return [{"line": 0, "rule": "error", "message": str(e)}]


def fix_truthiness(content: str) -> str:
    """Fix truthiness anti-patterns."""
    replacements = [
        # == True -> (implicit truthiness)
        (r"\s*==\s*True\b", ""),
        # == False -> not
        (r"\s*==\s*False\b", " not"),
        # != True -> not
        (r"\s*!=\s*True\b", " not"),
        # != False -> (implicit truthiness)
        (r"\s*!=\s*False\b", ""),
        # == None -> is None
        (r"\s*==\s*None\b", " is None"),
        # != None -> is not None
        (r"\s*!=\s*None\b", " is not None"),
    ]

    import re

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    return content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Enforce Python truthiness")
    parser.add_argument("--fix", action="store_true", help="Fix issues automatically")
    parser.add_argument("--check", action="store_true", help="Check only")
    parser.add_argument("paths", nargs="*", help="Files to check")
    args = parser.parse_args()

    fix = args.fix and not args.check

    if args.paths:
        py_files = []
        for path in args.paths:
            p = Path(path)
            if p.is_file() and p.suffix == ".py":
                py_files.append(p)
            elif p.is_dir():
                py_files.extend(p.rglob("*.py"))
    else:
        py_files = list(Path("nodupe").rglob("*.py")) if Path("nodupe").exists() else []

    py_files = list(set(py_files))

    if not py_files:
        print("No Python files found")
        return 0

    total_errors = 0

    for py_file in sorted(py_files):
        errors = check_file(py_file)

        if errors:
            total_errors += len(errors)
            print(f"\n{py_file}: {len(errors)} issue(s)")
            for err in errors[:5]:
                print(f"  Line {err['line']}: {err['message']}")

            if fix:
                original = py_file.read_text(encoding="utf-8")
                fixed = fix_truthiness(original)
                if fixed != original:
                    py_file.write_text(fixed, encoding="utf-8")
                    print("  Fixed!")

    print(f"\n{'='*50}")
    if total_errors > 0:
        print(f"Total: {total_errors} issue(s) found")
        return 1
    else:
        print("All Python files follow truthiness best practices")
        return 0


if __name__ == "__main__":
    sys.exit(main())
