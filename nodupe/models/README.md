This folder is intended to hold optional runtime model files used by `nodupe` for ML inference (e.g. ONNX models).

Examples:
- `nsfw_small.onnx` - a compact NSFW classifier model used by `nodupe/ai/backends.py` if present and ONNX Runtime (`onnxruntime`) is available.

Notes:
- Models are optional. The application will automatically fall back to CPU heuristics when models or runtimes are missing.
- Heavy ML models should not be checked in to the repository for size reasons; prefer separate release artifacts or packaging for production deployment.

Compatibility & troubleshooting
-------------------------------
- `nsfw_small.onnx` currently uses ONNX IR version 13 and includes opset imports (opset 25). Older ONNX Runtime builds (for example, 1.23.x) may be unable to load that model and will report errors such as "Unsupported model IR version: 13, max supported IR version: 11".

What to do if you hit compatibility problems
1. Upgrade your `onnxruntime` installation to a build that supports IR 13 / opset 25 (recommended).
2. If you cannot upgrade your runtime, you can provide a converted compatibility model named `nsfw_small_compat.onnx` in this same folder. The runtime backend will try loading `nsfw_small_compat.onnx` if the main model fails to load.

Vendoring a runtime
--------------------
For offline or reproducible deployments, you can vendor an `onnxruntime` wheel into `nodupe/vendor/libs`. This repository includes a helper wheel and documentation for vendoring; see `nodupe/vendor/libs/ONNXRUNTIME_README.md`.
