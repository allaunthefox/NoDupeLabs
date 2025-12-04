This directory contains vendored wheels and libraries used at runtime by `nodupe`.

Onnxruntime vendoring
---------------------
- A local copy of an `onnxruntime` wheel has been placed here for offline or reproducible installs. The included wheel in this repository is a convenience copy and may not match the exact runtime required to load the model in `nodupe/models`.

Compatibility note
------------------
- If `onnxruntime` in the environment cannot load `nodupe/models/nsfw_small.onnx` it will typically raise an error mentioning an unsupported ONNX IR version or opset. In that case either:
  - Install a newer `onnxruntime` build that supports the ONNX IR/opset used by the model, or
  - Provide a compatibility model `nsfw_small_compat.onnx` in `nodupe/models/` (a converted model) which older runtimes may be able to load.

How to use the vendored wheel
----------------------------
You have two comfortable ways to install and use the vendored wheel as a
baseline runtime in a reproducible environment:

1) Install a specific vendored wheel directly with pip (offline-friendly):

```bash
# from the repository root
python -m pip install --no-index --find-links nodupe/vendor/libs onnxruntime
```

2) Use the repo helper to install one or more vendor wheels into the active
Python environment (safe for reproducible CI/workstation setups):

```bash
# install all wheels in the vendor folder
python scripts/install_vendored_wheels.py

# install only onnxruntime from vendor folder
python scripts/install_vendored_wheels.py --pattern onnxruntime
```

Notes:
- The project's dependency manager checks `nodupe/vendor/libs` first and will
  attempt to install a vendored wheel (without hitting PyPI) when a missing
  dependency is requested and `auto_install` is enabled. This makes the vendored
  wheel a safe fallback for deployments without network access.

If you need help producing a compatible model or building a newer `onnxruntime`, see the project docs or open an issue.
