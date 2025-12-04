#!/usr/bin/env python3
"""Automated fixer for common flake8 errors in test files."""
import re
import sys
from pathlib import Path


def fix_trailing_whitespace(content):
    """Remove trailing whitespace from lines."""
    lines = content.split('\n')
    return '\n'.join(line.rstrip() for line in lines)


def fix_blank_lines_before_functions(content):
    """Ensure 2 blank lines before top-level functions/classes."""
    lines = content.split('\n')
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this is a function or class definition at module level
        if (line.startswith('def ') or line.startswith('class ')) and i > 0:
            # Count blank lines before this line
            blank_count = 0
            j = i - 1
            while j >= 0 and lines[j].strip() == '':
                blank_count += 1
                j -= 1
            
            # If previous non-blank line is import or another def/class, need 2 blanks
            if j >= 0 and not lines[j].startswith(('import ', 'from ')):
                if blank_count < 2:
                    # Remove existing blanks and add 2
                    while result and result[-1].strip() == '':
                        result.pop()
                    result.append('')
                    result.append('')
        result.append(line)
        i += 1
    return '\n'.join(result)


def fix_inline_comments(content):
    """Ensure at least 2 spaces before inline comments."""
    lines = content.split('\n')
    result = []
    for line in lines:
        if '#' in line and not line.strip().startswith('#'):
            # Find the comment
            before_hash = line[:line.index('#')]
            after_hash = line[line.index('#'):]
            # Ensure at least 2 spaces before #
            before_hash = before_hash.rstrip()
            result.append(before_hash + '  ' + after_hash)
        else:
            result.append(line)
    return '\n'.join(result)


def main():
    tests_dir = Path('tests')
    if not tests_dir.exists():
        print("tests directory not found")
        return 1
    
    for test_file in tests_dir.glob('test_*.py'):
        print(f"Processing {test_file}")
        content = test_file.read_text()
        
        # Apply fixes
        content = fix_trailing_whitespace(content)
        content = fix_inline_comments(content)
        content = fix_blank_lines_before_functions(content)
        
        # Ensure file ends with newline
        if not content.endswith('\n'):
            content += '\n'
        
        test_file.write_text(content)
    
    print("Done!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
