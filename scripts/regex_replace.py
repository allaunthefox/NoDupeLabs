#!/usr/bin/env python3
import sys, re
from pathlib import Path

def replace_file(path: Path, pattern: str, repl: str, flags=0):
    text = path.read_text(encoding='utf8')
    new_text, n = re.subn(pattern, repl, text, flags=flags)
    if n:
        path.write_text(new_text, encoding='utf8')
        print(f"Replaced {n} occurrences in {path}")
    else:
        print(f"No matches for {pattern} in {path}")

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: regex_replace.py <file> <pattern> <replacement>")
        sys.exit(2)
    replace_file(Path(sys.argv[1]), sys.argv[2].encode('utf8').decode('unicode_escape'), sys.argv[3], flags=re.M)
