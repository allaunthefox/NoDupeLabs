#!/usr/bin/env python3
"""Install vendored wheels from nodupe/vendor/libs into the current Python environment.

This helper is conservative: it installs only wheels found in the repo's
`nodupe/vendor/libs` directory and will print what it installs. Use it when you
want a reproducible, offline-friendly environment that falls back to vendored
binaries (for example `onnxruntime` in this repo).

Example:
  python scripts/install_vendored_wheels.py --pattern onnxruntime

The script runs `pip install --no-index --find-links` pointing at the vendor
directory so it never tries PyPI. By default it installs all found wheels.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def find_wheels(vendor_dir: Path, pattern: str | None = None):
    if not vendor_dir.exists():
        return []
    wheels = [p for p in vendor_dir.iterdir() if p.suffix == '.whl']
    if pattern:
        wheels = [p for p in wheels if pattern.lower() in p.name.lower()]
    return sorted(wheels)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pattern', type=str, default=None, help='Optional substring to filter wheel filenames')
    p.add_argument('--no-deps', action='store_true', help="Pass --no-deps to pip install")
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    vendor_dir = repo_root / 'nodupe' / 'vendor' / 'libs'

    wheels = find_wheels(vendor_dir, args.pattern)
    if not wheels:
        print('No vendored wheels found matching pattern', args.pattern or '(all)')
        return 1

    for w in wheels:
        print('Installing vendored wheel:', w.name)
        cmd = [sys.executable, '-m', 'pip', 'install', '--no-index', '--find-links', str(vendor_dir), str(w)]
        if args.no_deps:
            cmd.insert(-1, '--no-deps')
        print('Running:', ' '.join(cmd))
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            print('failed to install', w.name)
            return rc

    print('All vendored wheel installations finished successfully')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
