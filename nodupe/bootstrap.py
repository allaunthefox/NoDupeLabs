"""Simple lint_tree stub: performs syntax check of .py files under a
directory by attempting to compile them. Used at CLI startup/shutdown.
"""
from pathlib import Path


def lint_tree(module_dir: Path) -> None:
    py_files = list(module_dir.rglob("*.py"))
    for p in py_files:
        source = p.read_text(encoding="utf-8")
        # compile will raise SyntaxError when a file contains a syntax issue
        compile(source, str(p), 'exec')


__all__ = ["lint_tree"]
