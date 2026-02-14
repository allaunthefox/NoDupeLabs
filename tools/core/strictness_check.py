#!/usr/bin/env python3
"""Strictness inspection for NoDupeLabs."""
import ast
import sys
from pathlib import Path


class StrictnessChecker(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not node.returns:
            self.issues.append((node.lineno, f"Function '{node.name}' missing return type"))
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if not node.returns:
            self.issues.append((node.lineno, f"Async function '{node.name}' missing return type"))
        self.generic_visit(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.bases and not ast.get_docstring(node):
            self.issues.append((node.lineno, f"Class '{node.name}' missing docstring"))
        self.generic_visit(node)


def check_file(filepath: Path) -> list:
    try:
        content = filepath.read_text()
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return []
    
    checker = StrictnessChecker(str(filepath))
    checker.visit(tree)
    return checker.issues


def main() -> int:
    root = Path('nodupe')
    total = 0
    
    for filepath in root.rglob('*.py'):
        issues = check_file(filepath)
        if issues:
            print(f"\n{filepath}:")
            for line, msg in issues:
                print(f"  Line {line}: {msg}")
                total += 1
    
    print(f"\nTotal strictness issues: {total}")
    return 1 if total > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
