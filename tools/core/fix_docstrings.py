#!/usr/bin/env python3
"""Fix docstrings using AST - handles ANY indentation."""

import ast
import re
from pathlib import Path

def find_functions_without_docstrings(filepath):
    """Find all functions missing docstrings."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    
    missing = []
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_docstring = (
                node.body and
                isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, ast.Constant) and
                isinstance(node.body[0].value.value, str)
            )
            
            if not has_docstring:
                missing.append((node.lineno, node.name))
    
    return missing

def add_docstring_to_function(content, line_number, func_name):
    """Add a docstring to a function."""
    lines = content.split('\n')
    func_line_idx = line_number - 1
    
    # Find indentation of function body (first line after def)
    if func_line_idx + 1 < len(lines):
        next_line = lines[func_line_idx + 1]
        indent_match = re.match(r'^(\s*)', next_line)
        body_indent = indent_match.group(1) if indent_match else '    '
    else:
        body_indent = '    '
    
    # Insert docstring after the function definition line
    docstring = f'{body_indent}"""Document {func_name}."""'
    lines.insert(func_line_idx + 1, docstring)
    
    return '\n'.join(lines)

def process_file(filepath, dry_run=True):
    """Process a single file."""
    missing = find_functions_without_docstrings(filepath)
    
    if not missing:
        return 0
    
    print(f"{filepath}: {len(missing)} functions")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Sort by line number descending
    missing.sort(reverse=True)
    
    for line_num, func_name in missing:
        content = add_docstring_to_function(content, line_num, func_name)
    
    if not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return len(missing)

def main():
    import sys
    dry_run = '--apply' not in sys.argv
    
    if dry_run:
        print("=== DRY RUN - Use --apply to make changes ===\n")
    
    total = 0
    path = Path('nodupe')
    
    for py_file in sorted(path.rglob('*.py')):
        count = process_file(py_file, dry_run)
        total += count
    
    print(f"\nTotal: {total} functions")
    if dry_run:
        print("\nRun with --apply to make changes")

if __name__ == '__main__':
    main()
