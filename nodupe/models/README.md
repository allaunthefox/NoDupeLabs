This folder is intended to hold optional runtime model files used by `nodupe` for ML inference (e.g. ONNX models).

Examples:
- `nsfw_small.onnx` - a compact NSFW classifier model used by `nodupe/ai/backends.py` if present and ONNX Runtime (`onnxruntime`) is available.

Notes:
- Models are optional. The application will automatically fall back to CPU heuristics when models or runtimes are missing.
- Heavy ML models should not be checked in to the repository for size reasons; prefer separate release artifacts or packaging for production deployment.
