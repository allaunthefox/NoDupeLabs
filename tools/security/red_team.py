#!/usr/bin/env python3
"""Red Team Security Assessment - NoDupeLabs."""
import ast
import re
import sys
from pathlib import Path
from typing import Any


class RedTeamScanner:
    """Comprehensive red team security scanner."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.vulnerabilities = []
        self.findings = []
    
    def scan(self, tree: ast.AST) -> None:
        """Run all scans."""
        self._check_dangerous_functions(tree)
        self._check_insecure_defaults(tree)
        self._check_weak_crypto(tree)
        self._check_path_traversal(tree)
        self._check_command_injection(tree)
        self._check_unsafe_pickling(tree)
        self._check_memory_issues(tree)
        self._check_race_conditions(tree)
    
    def _check_dangerous_functions(self, tree: ast.AST) -> None:
        """Check for dangerous function usage."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for dangerous builtins
                if isinstance(node.func, ast.Name):
                    dangerous = ['eval', 'exec', '__import__']
                    if node.func.id in dangerous:
                        self.vulnerabilities.append((
                            node.lineno,
                            f"HIGH: Dangerous function '{node.func.id}()' allows code injection"
                        ))
                    # compile is allowed when used with ast.parse for validation
                    if node.func.id == 'compile':
                        self.findings.append((
                            node.lineno,
                            "MEDIUM: Verify compile() is only used for AST validation"
                        ))
                
                # Check for os.system, subprocess
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        # os.system, os.popen
                        if node.func.value.id == 'os' and node.func.attr in ['system', 'popen']:
                            self.vulnerabilities.append((
                                node.lineno,
                                f"HIGH: os.{node.func.attr}() allows command injection"
                            ))
                        # subprocess calls - only flag shell=True as HIGH
                        if node.func.value.id == 'subprocess':
                            shell_true = False
                            for kw in node.keywords:
                                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant):
                                    if kw.value.value is True:
                                        shell_true = True
                            if shell_true:
                                self.vulnerabilities.append((
                                    node.lineno,
                                    f"HIGH: subprocess.{node.func.attr}() with shell=True is dangerous"
                                ))
    
    def _check_insecure_defaults(self, tree: ast.AST) -> None:
        """Check for insecure default values."""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check default arguments
                for default in node.args.defaults:
                    if isinstance(default, ast.Constant):
                        if isinstance(default.value, str):
                            if default.value in ['', 'PASSWORD_REMOVED', 'SECRET_REMOVED', '123456']:
                                self.findings.append((
                                    node.lineno,
                                    f"MEDIUM: Insecure default value in function '{node.name}'"
                                ))
    
    def _check_weak_crypto(self, tree: ast.AST) -> None:
        """Check for weak cryptographic usage."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    # Check for weak hash algorithms
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'hashlib':
                            weak_algos = ['md5', 'sha1']
                            if node.func.attr in weak_algos:
                                self.vulnerabilities.append((
                                    node.lineno,
                                    f"MEDIUM: Weak hash algorithm '{node.func.attr}' - use sha256+"
                                ))
    
    def _check_path_traversal(self, tree: ast.AST) -> None:
        """Check for path traversal vulnerabilities."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for open() with user input
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'open':
                        # Check if there's any sanitization before
                        # This is a simplified check
                        self.findings.append((
                            node.lineno,
                            "LOW: Check for path traversal in open() call"
                        ))
    
    def _check_command_injection(self, tree: ast.AST) -> None:
        """Check for command injection vectors."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # f-strings in subprocess calls
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id in ['subprocess', 'os']:
                            for arg in node.args:
                                if isinstance(arg, ast.JoinedStr):  # f-string
                                    self.vulnerabilities.append((
                                        node.lineno,
                                        f"HIGH: Potential command injection - f-string in {node.func.value.id}.{node.func.attr}()"
                                    ))
    
    def _check_unsafe_pickling(self, tree: ast.AST) -> None:
        """Check for unsafe pickle usage."""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name):
                        if node.func.value.id == 'pickle':
                            if node.func.attr in ['load', 'loads']:
                                self.vulnerabilities.append((
                                    node.lineno,
                                    f"HIGH: pickle.{node.func.attr}() can execute arbitrary code - use JSON instead"
                                ))
    
    def _check_memory_issues(self, tree: ast.AST) -> None:
        """Check for memory management issues."""
        for node in ast.walk(tree):
            # Check for large file reads into memory
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'read':
                        # Check for .read() without size limit
                        if isinstance(node.func.value, ast.Name):
                            self.findings.append((
                                node.lineno,
                                "MEDIUM: Unbounded read() can cause memory exhaustion - use read(size)"
                            ))
            
            # Check for not closing files
            if isinstance(node, ast.With):
                for item in node.items:
                    # Files should be opened with 'with' statement
                    pass
    
    def _check_race_conditions(self, tree: ast.AST) -> None:
        """Check for race condition potential."""
        for node in ast.walk(tree):
            # Check for file operations without locking
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['rename', 'remove', 'unlink']:
                        self.findings.append((
                            node.lineno,
                            "MEDIUM: Check for TOCTOU race condition in file operation"
                        ))


def scan_file(filepath: Path) -> tuple[list, list]:
    """Scan a single file."""
    try:
        content = filepath.read_text()
        tree = ast.parse(content, filename=str(filepath))
    except SyntaxError:
        return [], []
    
    scanner = RedTeamScanner(str(filepath))
    scanner.scan(tree)
    return scanner.vulnerabilities, scanner.findings


def main() -> int:
    """Main entry point."""
    root = Path('nodupe')
    total_vulns = 0
    total_findings = 0
    
    print("=" * 60)
    print("RED TEAM SECURITY ASSESSMENT - NoDupeLabs")
    print("=" * 60)
    
    for filepath in root.rglob('*.py'):
        vulns, findings = scan_file(filepath)
        
        if vulns or findings:
            print(f"\n{filepath}:")
            
            for line, msg in vulns:
                print(f"  [VULN] Line {line}: {msg}")
                total_vulns += 1
            
            for line, msg in findings:
                print(f"  [FINDING] Line {line}: {msg}")
                total_findings += 1
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Vulnerabilities: {total_vulns}")
    print(f"Findings: {total_findings}")
    
    if total_vulns > 0:
        print("\n⚠️  CRITICAL ISSUES FOUND - Review required")
        return 1
    elif total_findings > 0:
        print("\n✓ No critical vulnerabilities, but review findings")
        return 0
    else:
        print("\n✓ No issues found")
        return 0


if __name__ == '__main__':
    sys.exit(main())
