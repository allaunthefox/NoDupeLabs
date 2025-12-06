#!/usr/bin/env python3
"""Lightweight repo docstring auditor.

Scans the package under `nodupe/` and reports public functions and
classes whose docstrings look weak / inconsistent with Google-style
conventions (missing Args/Returns sections, one-line docstrings, etc.).

The script is purposely conservative and only flags things that very
likely need human review (not attempting to be perfect).
"""

import ast
import os
import textwrap
from typing import List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
PKG = os.path.join(ROOT, 'nodupe')


def is_public(name: str) -> bool:
    return not name.startswith('_')


def analyze_docstring(node: ast.AST) -> Tuple[str, List[str]]:
    """Return (docstring_text, list of issues) for the given function/class AST node."""
    doc = ast.get_docstring(node) or ''
    issues = []
    if not doc:
        issues.append('MISSING_DOCSTRING')
        return (doc, issues)

    # Normalize docstring for checks
    lines = [l.rstrip() for l in doc.strip().splitlines()]
    one_liner = len(lines) == 1

    # Check for Args/Returns style (Google-style uses 'Args:' and 'Returns:')
    has_args = any(l.strip().startswith('Args:') for l in lines)
    has_returns = any(l.strip().startswith('Returns:') for l in lines)
    has_raises = any(l.strip().startswith('Raises:') for l in lines)

    if one_liner:
        issues.append('ONE_LINE_DOCSTRING')
    # If the node has arguments and docstring lacks Args, flag
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args_count = len([a for a in node.args.args if a.arg != 'self'])
        if args_count and not has_args:
            issues.append('MISSING_ARGS_SECTION')
    if isinstance(node, ast.FunctionDef):
        # Best-effort: if function contains 'return' and no Returns:, flag
        has_return_stmt = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(node))
        if has_return_stmt and not has_returns:
            issues.append('MISSING_RETURNS_SECTION')

    # Highly-heuristic: check for sections but with lowercase 'args' etc.
    if any(l.strip().startswith('args:') or l.strip().startswith('returns:') for l in lines):
        issues.append('NON_STANDARD_SECTION_CAPITALIZATION')

    # Short docstring but function has many args -> flag for expansion
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        args_count = len([a for a in node.args.args if a.arg != 'self'])
        if one_liner and args_count >= 2:
            issues.append('TOO_SHORT_FOR_SIGNATURE')

    return (doc, issues)


def scan_file(path: str) -> List[Tuple[str, str, int, str, List[str]]]:
    """Return list of findings: (type, name, lineno, short_doc, issues)"""
    text = open(path, 'r', encoding='utf-8').read()
    tree = ast.parse(text, path)
    findings = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not is_public(node.name):
                continue
            # Exclude inner functions (we only care top-level or class methods)
            parent = getattr(node, 'parent', None)
            # we'll check all; but skip nested simple closures to reduce noise
            doc, issues = analyze_docstring(node)
            if issues:
                short = textwrap.shorten(ast.get_docstring(node) or '', width=60)
                findings.append(('function', node.name, node.lineno, short, issues, os.path.relpath(path, ROOT)))
        elif isinstance(node, ast.ClassDef):
            if not is_public(node.name):
                continue
            doc, issues = analyze_docstring(node)
            if issues:
                short = textwrap.shorten(ast.get_docstring(node) or '', width=60)
                findings.append(('class', node.name, node.lineno, short, issues, os.path.relpath(path, ROOT)))
    return findings


# Attach parents for nested detection
def attach_parents(tree):
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            child.parent = node


def main():
    results = []
    for dirpath, dirnames, filenames in os.walk(PKG):
        # skip vendor
        if 'vendor' in dirpath.split(os.sep):
            continue
        for fn in filenames:
            if fn.endswith('.py'):
                path = os.path.join(dirpath, fn)
                try:
                    text = open(path, 'r', encoding='utf-8').read()
                    tree = ast.parse(text, path)
                    attach_parents(tree)
                except Exception as e:
                    print('PARSE_ERROR', path, e)
                    continue
                findings = scan_file(path)
                results.extend(findings)

    # Prioritize results
    priority = {'MISSING_DOCSTRING': 3, 'MISSING_ARGS_SECTION': 2, 'MISSING_RETURNS_SECTION': 2, 'ONE_LINE_DOCSTRING': 1, 'TOO_SHORT_FOR_SIGNATURE': 2, 'NON_STANDARD_SECTION_CAPITALIZATION': 0}

    # aggregate by file
    by_file = {}
    for kind, name, lineno, short, issues, rel in results:
        key = rel
        entry = by_file.setdefault(key, [])
        entry.append((kind, name, lineno, short, issues))

    # print a readable prioritized report
    print('\nDocstring audit results (candidate improvements):\n')
    for file, items in sorted(by_file.items(), key=lambda kv: (-sum(priority.get(s,0) for _k,_n,_l,_s,iss in kv[1] for s in iss), kv[0])):
        print(f'File: {file}')
        items_sorted = sorted(items, key=lambda t: -max(priority.get(i,0) for i in t[4]))
        for kind, name, lineno, short, issues in items_sorted:
            score = max(priority.get(i,0) for i in issues)
            print(f'  - {kind} {name} (line {lineno}): {short!s}')
            print(f'    Issues: {", ".join(issues)}')
        print()

    total = len(results)
    print(f'Scan complete — {total} items flagged for review (conservative detection).')


if __name__ == '__main__':
    main()
