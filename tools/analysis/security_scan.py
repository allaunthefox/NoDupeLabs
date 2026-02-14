#!/usr/bin/env python3
"""Advanced security scanner for NoDupeLabs."""
import ast
import re
import sys
from pathlib import Path
from typing import Any


class SecurityScanner(ast.NodeVisitor):
    """Advanced security scanner."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
        self.in_try = False
        self.in_except = False
    
    def visit_Try(self, node: ast.Try) -> None:
        self.in_try = True
        self.generic_visit(node)
        self.in_try = False
    
    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        self.in_except = True
        self.generic_visit(node)
        self.in_except = False
    
    def visit_Call(self, node: ast.Call) -> None:
        # Dangerous functions
        dangerous = {
            'eval': 'Use of eval() is dangerous',
            'exec': 'Use of exec() is dangerous',
            'compile': 'Use of compile() requires caution',
            '__import__': 'Dynamic import requires validation',
            'open': 'File open should use safe paths',
        }
        
        if isinstance(node.func, ast.Name):
            if node.func.id in dangerous:
                self.issues.append((
                    node.lineno, 
                    f"CRITICAL: {dangerous[node.func.id]}: {node.func.id}()"
                ))
        
        # Check for os.system, subprocess shell=True
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id == 'os' and node.func.attr == 'system':
                    self.issues.append((node.lineno, "CRITICAL: os.system() is unsafe"))
                if node.func.value.id == 'subprocess':
                    # Check for shell=True
                    for kw in node.keywords:
                        if kw.arg == 'shell' and isinstance(kw.value, ast.Constant):
                            if kw.value.value is True:
                                self.issues.append((
                                    node.lineno, 
                                    "CRITICAL: subprocess with shell=True is dangerous"
                                ))
        
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        # Check for hardcoded secrets
        for target in node.targets:
            if isinstance(target, ast.Name):
                secret_patterns = ['password', 'secret', 'token', 'api_key', 'private']
                if any(p in target.id.lower() for p in secret_patterns):
                    if isinstance(node.value, ast.Constant):
                        if isinstance(node.value.value, str) and node.value.value:
                            self.issues.append((
                                node.lineno, 
                                f"WARNING: Potential hardcoded secret: {target.id}"
                            ))
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Check for SQL injection vulnerabilities
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if child.func.attr in ['execute', 'executemany', 'cursor']:
                        for arg in child.args:
                            if isinstance(arg, ast.JoinedStr):  # f-string
                                self.issues.append((
                                    node.lineno,
                                    f"WARNING: Potential SQL injection in {node.name}"
                                ))
        self.generic_visit(node)


def scan_file(filepath: Path) -> list:
    """Scan a single file for security issues."""
    try:
        content = filepath.read_text()
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return []
    
    scanner = SecurityScanner(str(filepath))
    scanner.visit(tree)
    return scanner.issues


def main() -> int:
    """Run security scan."""
    root = Path('nodupe')
    total = 0
    critical = 0
    
    for filepath in root.rglob('*.py'):
        issues = scan_file(filepath)
        if issues:
            print(f"\n{filepath}:")
            for line, msg in issues:
                prefix = "CRITICAL" if "CRITICAL" in msg else "WARNING"
                print(f"  [{prefix}] Line {line}: {msg}")
                total += 1
                if "CRITICAL" in msg:
                    critical += 1
    
    print(f"\n{'='*50}")
    print(f"Total issues: {total}")
    print(f"Critical: {critical}")
    
    return 1 if critical > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
