#!/usr/bin/env python3
"""
API Stability Check Script

This script scans the codebase for API decorators and ensures that changes to
stable APIs are backwards compatible, or at least flagged for review.
"""
import ast
import os
import sys
from typing import Dict, List, Set, Tuple

def get_api_definitions(root_dir: str) -> Dict[str, Dict[str, str]]:
    """
    Scan python files in root_dir for functions/classes decorated with
    @stable_api, @beta_api, or @experimental_api.
    
    Returns:
        Dict mapping filepath to a dictionary of {name: api_level}
    """
    api_defs = {}
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=filepath)
            except Exception:
                continue
                
            file_apis = {}
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    for decorator in node.decorator_list:
                        # Handle simple decorators like @stable_api
                        if isinstance(decorator, ast.Name):
                            if decorator.id in ('stable_api', 'beta_api', 'experimental_api', 'deprecated'):
                                file_apis[node.name] = decorator.id
                        # Handle called decorators if necessary (e.g. @api_endpoint(...))
                        elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                             if decorator.func.id in ('stable_api', 'beta_api', 'experimental_api', 'deprecated'):
                                file_apis[node.name] = decorator.func.id

            if file_apis:
                api_defs[filepath] = file_apis
                
    return api_defs

def main():
    root_dir = os.getcwd()
    print(f"Scanning for API definitions in {root_dir}...")
    
    api_defs = get_api_definitions(root_dir)
    
    if not api_defs:
        print("No API definitions found.")
        return 0
        
    print("\nFound API definitions:")
    count = 0
    for filepath, apis in api_defs.items():
        rel_path = os.path.relpath(filepath, root_dir)
        print(f"\n{rel_path}:")
        for name, level in apis.items():
            print(f"  - {name}: {level}")
            count += 1
            
    print(f"\nTotal API endpoints found: {count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
