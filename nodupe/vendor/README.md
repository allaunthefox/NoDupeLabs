# Vendor Libraries

This directory contains pre-packaged Python libraries to ensure basic operation of NoDupeLabs even if the system Python environment is missing dependencies or has version mismatches.

## Contents

- **tqdm**: Progress bars.
- **PyYAML**: YAML configuration parsing.

## Usage

The `nodupe` CLI automatically adds this directory to `sys.path` at runtime if dependencies are missing.

## Updating

To update these libraries, run:

```bash
pip install --target nodupe/vendor/libs --no-binary :all: tqdm PyYAML --upgrade
```

Note: `jsonschema` is not vendored due to binary dependencies (rpds-py/Rust). The application will fall back to basic validation if it is missing.
