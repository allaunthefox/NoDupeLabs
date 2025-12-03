# Vendor Libraries

This directory contains pre-packaged Python libraries to ensure basic operation of NoDupeLabs even if the system Python environment is missing dependencies or has version mismatches.

## Contents

- **tqdm**: Progress bars.
- **PyYAML**: YAML configuration parsing.

## Usage

The `nodupe` CLI automatically adds this directory to `sys.path` at runtime if dependencies are missing.

This directory also holds larger runtime wheels (for example `onnxruntime`) which can be used as a stable baseline runtime for ML inference. Use the repo helper `scripts/install_vendored_wheels.py` to install vendored wheels into your environment, or install them manually via pip using `--no-index` and `--find-links` for offline installs.

## Vendoring helper

To help keep the vendored set reproducible you can run `scripts/vendor_requirements.py` from the repo root. It will:

- Read declared dependencies from `pyproject.toml`.
- Add a small curated set of optional packages useful for offline/test runs (`onnxruntime`, `pillow`, `psutil`, `numpy`).
- Download wheel files into `nodupe/vendor/libs` and write a `vendor_manifest.json` listing the files.

Example:

```bash
python scripts/vendor_requirements.py --no-deps
```

The project already includes a minimal set of vendored wheels (see `vendor_manifest.json`) that CI and tests can use as a reliable baseline.

## Updating

To update these libraries, run:

```bash
pip install --target nodupe/vendor/libs --no-binary :all: tqdm PyYAML --upgrade
```

Note: `jsonschema` is not vendored due to binary dependencies (rpds-py/Rust). The application will fall back to basic validation if it is missing.
