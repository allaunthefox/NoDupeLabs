#!/usr/bin/env python3
"""Try to upgrade onnxruntime from PyPI, falling back to vendored wheel on failure.

Behaviour:
 - Detect current installed onnxruntime version (if any).
 - Query PyPI for the latest release version.
 - If a newer release exists, attempt `pip install --upgrade --pre onnxruntime`.
 - If the install or runtime verification fails, install the vendored wheel(s) from
   `nodupe/vendor/libs` (via the helper script) and verify again.

This script is intended for developer/CI usage to ensure a best-effort attempt
to get a newer runtime, but always provide a reproducible vendored fallback.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.request
from pathlib import Path


def current_version() -> str | None:
    try:
        import onnxruntime as ort

        return getattr(ort, "__version__", None)
    except Exception:
        return None


def latest_pypi_version(pkg: str = "onnxruntime") -> str | None:
    url = f"https://pypi.org/pypi/{pkg}/json"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            obj = json.load(r)
            return obj.get("info", {}).get("version")
    except Exception:
        return None


def pip_install(pkg: str, allow_prerelease: bool = True) -> bool:
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade"]
    if allow_prerelease:
        cmd.append("--pre")
    cmd.append(pkg)
    print("Running:", " ".join(cmd))
    rc = subprocess.run(cmd).returncode
    return rc == 0


def install_vendored():
    repo_root = Path(__file__).resolve().parents[1]
    helper = repo_root / "scripts" / "install_vendored_wheels.py"
    if not helper.exists():
        print("Vendored install helper not found; cannot install vendored wheels", file=sys.stderr)
        return False
    cmd = [sys.executable, str(helper), "--pattern", "onnxruntime"]
    print("Installing vendored wheels with:", " ".join(cmd))
    rc = subprocess.run(cmd).returncode
    return rc == 0


def verify_runtime_load(model_path: str | Path) -> bool:
    try:
        import onnxruntime as ort

        # quick import & try to create session
        ort_ver = getattr(ort, "__version__", "?")
        print("Imported onnxruntime version", ort_ver)
        try:
            sess = ort.InferenceSession(str(model_path))
        except Exception as e:
            # If this fails due to an IR mismatch, attempt to look for a
            # compat model alongside the main model (suffix _compat.onnx) and
            # try that — this supports older runtimes that can still run a
            # converted model.
            msg = str(e)
            if 'Unsupported model IR version' in msg or 'Unsupported model IR version' in msg:
                compat = Path(str(model_path)).with_name(Path(str(model_path)).stem + '_compat.onnx')
                if compat.exists():
                    print('Original model failed to load; attempting compat model', compat)
                    sess = ort.InferenceSession(str(compat))
                else:
                    raise
        print("Created session; inputs:", [i.name for i in sess.get_inputs()])
        return True
    except Exception as e:
        print("Runtime/model verification failed:", type(e), e)
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', type=str, default='nodupe/models/nsfw_small.onnx', help='Model path to validate runtime against')
    p.add_argument('--force', action='store_true', help='Try to install a new runtime even if versions appear equal')
    args = p.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    model = repo_root / args.model

    cur = current_version()
    print('Current onnxruntime version:', cur)

    latest = latest_pypi_version()
    print('Latest PyPI version:', latest)

    if latest is None:
        print('Unable to query PyPI — will attempt to install vendored wheel as fallback')
        ok = install_vendored()
        if ok:
            return 0 if verify_runtime_load(model) else 2
        return 1

    try:
        from packaging.version import Version

        should_try = args.force or cur is None or Version(latest) > Version(cur)
    except Exception:
        should_try = args.force or cur is None

    if should_try:
        print('Attempting to install/upgrade onnxruntime from PyPI...')
        ok = pip_install('onnxruntime', allow_prerelease=True)
        if ok and verify_runtime_load(model):
            print('Successfully installed newer onnxruntime from PyPI')
            return 0

        print('Network install failed or runtime verification failed — falling back to vendored wheel')

    else:
        print('No newer PyPI version detected; attempting vendored install if needed')

    # fallback to vendored wheel
    if install_vendored() and verify_runtime_load(model):
        print('Successfully installed vendored onnxruntime')
        return 0

    print('Failed to ensure a working onnxruntime — please check logs')
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
