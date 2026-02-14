#!/usr/bin/env python3
"""Detect deprecated Python APIs.

This script checks for deprecated Python features:
- Deprecated builtins (Python 3.x)
- Deprecated standard library functions
- Version-specific deprecations

Usage:
    python tools/core/detect_deprecated.py [--check] [paths]
"""

import ast
import argparse
import sys
from pathlib import Path
from typing import Any


# Deprecated APIs by Python version
DEPRECATED_BUILTINS = {
    # Python 3.9+
    "platform.linux_distribution": "platform.dist() removed in 3.8, use platform.freedesktop_os_release()",
    "xml.etree.ElementTree.Element.iterchildren": "Removed in 3.9, use list(element)",
    "xml.etree.ElementTree.Element.getchildren": "Removed in 3.2, use list(element)",
    # Python 3.10+
    "collections.abc.AsyncContextManager": "Use contextlib.asynccontextmanager",
    "typing.TypedDict": "Use typing_extensions.TypedDict for older Python",
    # Python 3.11+
    "asyncio.Future.result": "Use await instead",
    # Python 3.12+
    "importlib.metadata": "Some APIs changed in 3.12",
    "hashlib.sha512": "Use shake algorithms for variable output",
}

# Deprecated patterns
DEPRECATED_PATTERNS = [
    # (pattern, suggestion, version)
    (r"getattr\(.*,\s*['\"]__class__['\"]\)", "type(obj)", "3.0"),
    (r"setattr\(.*,\s*['\"]__class__['\"]\)", "obj.__class__ =", "3.0"),
    (r"__import__\(['\"]future['\"]\)", "No need in Python 3", "3.0"),
    (r"apply\(", "Use func(*args)", "3.0"),
    (r"execfile\(", "Use exec(open(f).read())", "3.0"),
    (r"file\(", "Use open()", "3.0"),
    (r"input\.readlines\(", "Use list(input)", "3.0"),
    (r"print\s*\[", "Use print(..., file=sys.stdout)", "3.0"),
    (r"sys\.maxint", "Use sys.maxsize", "3.0"),
    (r"type\(str\)\s*==", "Use isinstance()", "3.0"),
    (r"type\(bytes\)\s*==", "Use isinstance()", "3.0"),
    (r"from\s+urllib\s+import", "Use urllib.request", "3.0"),
    (r"from\s+optparse\s+import", "Use argparse", "3.0"),
    (r"from\s+StringIO\s+import", "Use io.StringIO", "3.0"),
    (r"from\s+cStringIO\s+import", "Use io.BytesIO", "3.0"),
    # asyncio
    (r"asyncio\.coroutine", "Use async def", "3.8"),
    (r"asyncio\.async", "Use asyncio.create_task", "3.10"),
    # datetime
    (r"datetime\.utcnow\(\)", "Use datetime.now(timezone.utc)", "3.12"),
    (r"datetime\.utcfromtimestamp\(\)", "Use datetime.fromtimestamp(tz=timezone.utc)", "3.12"),
    # collections
    (r"collections\.OrderedDict", "Use dict (ordered by default)", "3.7"),
    (r"collections\.Callable", "Use collections.abc.Callable", "3.10"),
    (r"collections\.Mapping", "Use collections.abc.Mapping", "3.10"),
    (r"collections\.Iterable", "Use collections.abc.Iterable", "3.10"),
    # configparser
    (r"ConfigParser\.", "Use configparser.", "3.2"),
    # html
    (r"from\s+html\.parser\s+import\s+HTMLParser", "Use html.parser.HTMLParser", "3.9"),
    # threading
    (r"Thread\.isAlive\(\)", "Use Thread.is_alive()", "3.9"),
    # unittest
    (r"unittest\.TestCase\.assertEquals", "Use assertEqual", "3.2"),
    (r"unittest\.TestCase\.assertNotEquals", "Use assertNotEqual", "3.2"),
    (r"unittest\.TestCase\.assert_\(", "Use assertTrue", "3.2"),
    # warnings
    (r"warnings\.catch_warnings", "Use warnings.catch_warnings(record=True)", "3.11"),
]

# Deprecated module imports
DEPRECATED_IMPORTS = {
    "optparse": "Use argparse",
    "distutils": "Use setuptools",
    "imp": "Use importlib",
    "functools.cmp_to_key": "Use key function directly when possible",
}


class DeprecatedChecker(ast.NodeVisitor):
    """Check for deprecated Python APIs."""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name in DEPRECATED_IMPORTS:
                self.errors.append({
                    "line": node.lineno,
                    "rule": "deprecated-import",
                    "message": f"Deprecated import '{alias.name}': {DEPRECATED_IMPORTS[alias.name]}",
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            if node.module in DEPRECATED_IMPORTS:
                self.errors.append({
                    "line": node.lineno,
                    "rule": "deprecated-import",
                    "message": f"Deprecated import '{node.module}': {DEPRECATED_IMPORTS[node.module]}",
                })

            # Check specific imports
            for alias in node.names:
                full_name = f"{node.module}.{alias.name}"
                if full_name in DEPRECATED_BUILTINS:
                    self.warnings.append({
                        "line": node.lineno,
                        "rule": "deprecated-api",
                        "message": f"Deprecated: {full_name} - {DEPRECATED_BUILTINS[full_name]}",
                    })

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Check for deprecated function calls
        if isinstance(node.func, ast.Attribute):
            # Check method calls
            if isinstance(node.func.value, ast.Name):
                name = f"{node.func.value.id}.{node.func.attr}"
                if name in DEPRECATED_BUILTINS:
                    self.warnings.append({
                        "line": node.lineno,
                        "rule": "deprecated-call",
                        "message": f"Deprecated call: {name} - {DEPRECATED_BUILTINS[name]}",
                    })

        self.generic_visit(node)


def check_file(path: Path) -> list[dict]:
    """Check a Python file for deprecated APIs."""
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
        checker = DeprecatedChecker()
        checker.visit(tree)
        return checker.errors + checker.warnings
    except SyntaxError as e:
        return [{"line": e.lineno or 0, "rule": "syntax", "message": f"Syntax error: {e}"}]
    except Exception as e:
        return [{"line": 0, "rule": "error", "message": str(e)}]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Detect deprecated Python APIs")
    parser.add_argument("--check", action="store_true", help="Check only")
    parser.add_argument("paths", nargs="*", help="Files to check")
    args = parser.parse_args()

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

            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")

    print(f"\n{'='*50}")
    if total_errors > 0:
        print(f"Total: {total_errors} deprecated API(s) found")
        return 1
    else:
        print("No deprecated APIs detected")
        return 0


if __name__ == "__main__":
    sys.exit(main())
