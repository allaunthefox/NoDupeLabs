#!/usr/bin/env python3
"""Vendor required and optional Python wheels into nodupe/vendor/libs.

This script downloads wheels for the project's declared dependencies (from
pyproject.toml) and a small curated set of optional packages we want available
offline (for example `onnxruntime`, `pillow`, `psutil`, `numpy`). It uses
`pip download` to retrieve wheel files compatible with the running interpreter.

By default it will download dependency wheels (transitive) as well so the
vendored directory can be used offline. Use --no-deps to only download the
explicit package wheels.

Examples:
  # vendor required deps + curated optional extras
  python scripts/vendor_requirements.py

  # vendor only explicit packages (no dependencies)
  python scripts/vendor_requirements.py --no-deps
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import tomllib


def read_pyproject_deps(root: Path) -> list[str]:
    py = root / 'pyproject.toml'
    if not py.exists():
        return []
    with py.open('rb') as fh:
        data = tomllib.load(fh)

    deps = []
    proj = data.get('project') or {}
    for key in ('dependencies', 'optional-dependencies'):
        v = proj.get(key)
        if isinstance(v, dict):
            # optional-dependencies is a dict mapping extras -> list
            for sub in v.values():
                if isinstance(sub, list):
                    deps.extend(sub)
        elif isinstance(v, list):
            deps.extend(v)

    # Normalize to simple package names (version specifiers allowed)
    cleaned = []
    for d in deps:
        # remove platform markers after semicolon
        d = d.split(';', 1)[0].strip()
        if not d:
            continue
        cleaned.append(d)

    return sorted(set(cleaned))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--vendor-dir', default='nodupe/vendor/libs', help='Target directory for vendored wheels')
    p.add_argument('--pattern', default=None, help='Optional substring filter for packages to vendor')
    p.add_argument('--no-deps', action='store_true', help='Do not download dependencies (only explicit packages)')
    p.add_argument('--extra', action='append', default=[], help='Additional package names to vendor (can repeat)')
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    vendor_dir = repo_root / args.vendor_dir
    vendor_dir.mkdir(parents=True, exist_ok=True)

    # Packages explicitly declared in pyproject
    declared = read_pyproject_deps(repo_root)

    # Curated optional set recommended for offline usage and tests
    curated_optional = [
        'onnxruntime',
        'pillow',
        'psutil',
        'numpy',
    ]

    packages = set(declared) | set(curated_optional) | set(args.extra)

    # Allow to filter down with pattern
    if args.pattern:
        packages = {p for p in packages if args.pattern.lower() in p.lower()}

    if not packages:
        print('No packages to vendor (empty set)')
        return 0

    print('Vendoring packages into', vendor_dir)
    print('Packages:', ', '.join(sorted(packages)))

    # Build pip download command
    base_cmd = [sys.executable, '-m', 'pip', 'download', '--only-binary', ':all:', '--dest', str(vendor_dir)]
    if args.no_deps:
        base_cmd.append('--no-deps')

    # Download each package; using pip download for each allows more granular logs
    for pkg in sorted(packages):
        cmd = base_cmd + [pkg]
        print('Running:', ' '.join(cmd))
        rc = subprocess.run(cmd).returncode
        if rc != 0:
            print('Failed to download package:', pkg)
            return rc

    # Create a small manifest of vendored files for reproducibility
    try:
        import json
        files = [p.name for p in vendor_dir.iterdir() if p.is_file()]
        manifest = {
            'packages': sorted(list(packages)),
            'files': sorted(files)
        }
        with open(vendor_dir / 'vendor_manifest.json', 'w', encoding='utf-8') as fh:
            json.dump(manifest, fh, indent=2)
        print('Wrote vendor_manifest.json')
    except Exception:
        pass

    print('Vendoring completed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
