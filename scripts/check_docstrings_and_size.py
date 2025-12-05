#!/usr/bin/env python3
"""Check public API docstrings and module size limits.

This script enforces two lightweight rules on the `nodupe/` package:

- Every public function/method (name not starting with `_`) must have a
  docstring.
- Each module (non-vendor) should be smaller than MODULE_LINE_LIMIT lines to
  avoid monolithic files.

Exit code is non-zero when violations are found.
"""
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "nodupe"
MODULE_LINE_LIMIT = 500


def find_missing_docstrings(pkg_root: Path):
    missing = []
    for p in pkg_root.rglob("*.py"):
        if "vendor" in str(p):
            continue
        src = p.read_text(encoding="utf-8")
        try:
            tree = ast.parse(src)
        except Exception as e:
            missing.append((str(p), -1, f"PARSE_ERROR: {e}"))
            continue

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                # skip private functions
                if name.startswith("_"):
                    continue
                doc = ast.get_docstring(node)
                if not doc:
                    missing.append((str(p), node.lineno, name))
    return missing


def find_large_modules(pkg_root: Path, limit: int):
    large = []
    for p in pkg_root.rglob("*.py"):
        if "vendor" in str(p):
            continue
        ln = len(p.read_text(encoding="utf-8").splitlines())
        if ln > limit:
            large.append((str(p), ln))
    return large


def main():
    missing = find_missing_docstrings(PKG)
    large = find_large_modules(PKG, MODULE_LINE_LIMIT)

    ok = True
    if missing:
        ok = False
        print("ERROR: Missing docstrings for public functions/methods:")
        for p, lineno, name in missing:
            print(f"  {p}:{lineno}: {name}")

    if large:
        ok = False
        print(f"ERROR: Modules exceeding {MODULE_LINE_LIMIT} lines:")
        for p, ln in large:
            print(f"  {p}: {ln} lines")

    if not ok:
        print("\nFix the above issues (add docstrings for public APIs, split big modules)\n")
        sys.exit(2)

    print("Docstring & module size checks passed.")


if __name__ == '__main__':
    main()
