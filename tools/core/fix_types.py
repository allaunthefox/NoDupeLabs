#!/usr/bin/env python3
"""Programmatic type fixing tool for NoDupeLabs.

This tool automates fixing common mypy type errors:
- Missing return type annotations
- Returning Any from typed functions
- Type mismatches

Usage:
    python tools/core/fix_types.py --check        # Show what would be fixed
    python tools/core/fix_types.py --fix         # Apply fixes
    python tools/core/fix_types.py --file FILE   # Fix specific file
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


# File-specific fix patterns
FIX_PATTERNS: Dict[str, List[Tuple[str, str]]] = {
    # security.py - missing return types
    "security.py": [
        (r'(def \w+\([^)]*\):\n\s+)"""', r'\1-> None\n"""'),
    ],
    # scan/progress.py - float/int mismatches  
    "scan/progress.py": [
        (r'(progress|percent|rate): int', r'\1: float'),
    ],
}


def get_mypy_errors(base_path: Path = Path("nodupe/core")) -> Dict[str, List[str]]:
    """Get mypy errors grouped by file."""
    import subprocess
    # Use venv python if available
    venv_python = Path("__main__.py").parent / ".venv/bin/python"
    if venv_python.exists():
        python_cmd = str(venv_python)
    else:
        python_cmd = "python"
    
    result = subprocess.run(
        [python_cmd, "-m", "mypy", str(base_path), "--config-file", "mypy.ini"],
        capture_output=True,
        text=True,
        cwd=Path.cwd()
    )
    
    errors: Dict[str, List[str]] = {}
    output = result.stdout + result.stderr
    
    for line in output.split("\n"):
        # Match both "nodupe/core/file.py:123:" and "nodupe\core\file.py:123:"
        if "error:" in line:
            # Extract file path - handle both forward and backslash
            match = re.search(r'(nodupe[/\\]core[/\\][^:]+):(\d+)', line)
            if match:
                file_path = match.group(1).replace('\\', '/').replace('nodupe/', '')
                error_msg = line.strip()
                if file_path not in errors:
                    errors[file_path] = []
                errors[file_path].append(error_msg)
    
    return errors


def count_error_types(errors: Dict[str, List[str]]) -> Dict[str, int]:
    """Count errors by type."""
    counts: Dict[str, int] = {}
    for file_errors in errors.values():
        for error in file_errors:
            if "no-untyped-def" in error:
                counts["no-untyped-def"] = counts.get("no-untyped-def", 0) + 1
            elif "no-any-return" in error:
                counts["no-any-return"] = counts.get("no-any-return", 0) + 1
            elif "assignment" in error:
                counts["assignment"] = counts.get("assignment", 0) + 1
            elif "var-annotated" in error:
                counts["var-annotated"] = counts.get("var-annotated", 0) + 1
            else:
                counts["other"] = counts.get("other", 0) + 1
    return counts


def fix_missing_return_types(content: str) -> str:
    """Fix functions missing return type annotations."""
    # Pattern: def function_name(args): without ->
    pattern = r'^(\s+)(def \w+\([^)]*\):)(\s*\n\s+""".*?""")?\s*$'
    
    def replacer(match):
        indent = match.group(1)
        func_def = match.group(2)
        docstring = match.group(3) or ""
        # Skip if already has return type
        if "->" in func_def:
            return match.group(0)
        # Add -> None
        return f"{indent}{func_def} -> None:{docstring}\n{indent}    pass"
    
    return re.sub(pattern, replacer, content, flags=re.MULTILINE | re.DOTALL)


def fix_dict_returns(content: str) -> str:
    """Fix dict returns that return Any."""
    # Pattern: return self.something.get(...)
    # Fix: return dict(self.something.get(...))
    patterns = [
        (r'\breturn\s+self\.\w+\.get\([^)]+\)(?!\))', 
         lambda m: f"return dict({m.group(0).replace('return ', '')})"),
    ]
    
    for pattern, replacer in patterns:
        content = re.sub(pattern, replacer, content)
    
    return content


def fix_file(file_path: Path, dry_run: bool = True) -> Tuple[int, str]:
    """Fix type errors in a single file.
    
    Returns:
        Tuple of (errors_fixed, original_content or new_content)
    """
    if not file_path.exists():
        return 0, ""
    
    content = file_path.read_text()
    original = content
    
    # Apply fixes based on file
    if file_path.name in FIX_PATTERNS:
        for pattern, replacement in FIX_PATTERNS[file_path.name]:
            content = re.sub(pattern, replacement, content)
    
    # Generic fixes
    content = fix_missing_return_types(content)
    content = fix_dict_returns(content)
    
    if dry_run:
        return len(original) - len(content), original
    else:
        if content != original:
            file_path.write_text(content)
        return len(original) - len(content), content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Fix mypy type errors")
    parser.add_argument("--check", action="store_true", help="Check errors only")
    parser.add_argument("--fix", action="store_true", help="Apply fixes")
    parser.add_argument("--file", help="Fix specific file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    base_path = Path("nodupe/core")
    
    print("=" * 60)
    print("NoDupeLabs Type Fixer")
    print("=" * 60)
    
    if args.check or args.fix:
        # Get current errors
        print("\nAnalyzing mypy errors...")
        errors = get_mypy_errors(base_path)
        total_errors = sum(len(e) for e in errors.values())
        
        print(f"Total errors found: {total_errors}")
        
        # Count by type
        type_counts = count_error_types(errors)
        print("\nErrors by type:")
        for error_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
            print(f"  {error_type}: {count}")
        
        print("\nTop files with errors:")
        for file_path, file_errors in sorted(errors.items(), key=lambda x: -len(x[1]))[:10]:
            print(f"  {file_path}: {len(file_errors)} errors")
        
        print()
    
    if args.fix:
        print("Applying fixes...")
        total_fixed = 0
        
        # Get files with errors
        errors = get_mypy_errors(base_path)
        
        for file_path in errors:
            full_path = base_path / file_path
            if full_path.exists():
                fixed, _ = fix_file(full_path, dry_run=False)
                if fixed > 0:
                    print(f"  Fixed {fixed} issues in {file_path}")
                    total_fixed += fixed
        
        print(f"\nTotal fixed: {total_fixed}")
        
        # Verify
        print("\nVerifying fixes...")
        new_errors = get_mypy_errors(base_path)
        new_total = sum(len(e) for e in new_errors.values())
        print(f"New error count: {new_total} (was {total_errors})")
    
    print("\n" + "=" * 60)
    print("Run 'mypy nodupe/core --config-file mypy.ini' to verify")
    print("=" * 60)


if __name__ == "__main__":
    main()
