#!/usr/bin/env python3
"""Compliance scan for NoDupeLabs - checks security, best practices."""
import ast
import sys
from pathlib import Path


class ComplianceChecker(ast.NodeVisitor):
    """Check for compliance issues."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
    
    def visit_Call(self, node: ast.Call) -> None:
        # Check for dangerous functions
        if isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec', 'compile']:
                self.issues.append((node.lineno, f"Dangerous function: {node.func.id}"))
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == 'os' or alias.name == 'subprocess':
                self.issues.append((node.lineno, f"Potentially unsafe import: {alias.name}"))
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module in ['os', 'subprocess', 'sys']:
            self.issues.append((node.lineno, f"Potentially unsafe import: {node.module}"))
        self.generic_visit(node)


def check_file(filepath: Path) -> list:
    try:
        content = filepath.read_text()
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return []
    
    checker = ComplianceChecker(str(filepath))
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
    
    print(f"\nTotal compliance issues: {total}")
    return 1 if total > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
