#!/usr/bin/env python3
"""Helper: download or copy an ONNX Runtime wheel into `nodupe/vendor/libs`.

Usage:
  - If you already have a wheel in /tmp/onnx_wheel_cache, the script will move it
    into the repo vendor dir.
  - If not, it can attempt to `pip download` a specific version and then copy it.

This script is intended to make it easy to create a vendored wheel for
reproducible/offline installs. It does not automatically install anything.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import shutil
import subprocess
import sys


def find_wheel(cache_dir: Path):
    if not cache_dir.exists():
        return None
    # find any onnxruntime wheel
    for p in sorted(cache_dir.iterdir()):
        if p.name.startswith('onnxruntime') and p.suffix == '.whl':
            return p
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--cache', type=Path, default=Path('/tmp/onnx_wheel_cache'))
    p.add_argument('--version', type=str, default=None, help='Optional version to download with pip')
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    vendor_dir = repo_root / 'nodupe' / 'vendor' / 'libs'
    vendor_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = args.cache
    wheel = find_wheel(cache_dir)
    if wheel is None and args.version:
        print('No wheel in cache — downloading with pip...')
        cmd = [sys.executable, '-m', 'pip', 'download', '--dest', str(cache_dir), 'onnxruntime' + (f'=={args.version}' if args.version else '')]
        subprocess.check_call(cmd)
        wheel = find_wheel(cache_dir)

    if wheel is None:
        print(f'No onnxruntime wheel found in {cache_dir}. Nothing to vendor.')
        return 1

    dest = vendor_dir / wheel.name
    print('Copying', wheel, '->', dest)
    shutil.copy2(wheel, dest)
    print('Done — wheel saved to', dest)


if __name__ == '__main__':
    raise SystemExit(main())
